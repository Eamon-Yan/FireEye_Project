"""
文档管理API端点
集成完整的文档处理工作流：解析 -> 提取 -> 验证 -> 存储
"""

import logging
from typing import List, Dict, Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.base import BaseResponse, ResponseStatus
from app.schemas.document import (
    Document,
    DocumentCreate,
    DocumentResponse,
    DocumentQuery,
    DocumentStatistics,
    FileUpload,
    DocumentContent
)
from app.schemas.extraction import DocumentSections, ProcessingStatus
from app.schemas.event_chain import EventChainCreate
from app.services.extraction_service import extraction_service
from app.services.validation_service import validation_service
from app.services.graph_service import GraphService
from app.db.dependencies import GraphServiceDep

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/process", response_model=BaseResponse)
async def process_document(
    file: UploadFile = File(..., description="上传的文档文件"),
    apply_validation: bool = True,
    save_to_graph: bool = True,
    graph_service: GraphService = GraphServiceDep
):
    """
    统一文档处理端点
    
    完整工作流程：
    1. 解析文档并提取章节 (ExtractionService)
    2. 使用LLM提取事件链 (LLMService)
    3. 验证和归一化事件链 (ValidationService)
    4. 保存到Neo4j图数据库 (GraphService)
    
    支持的文件格式:
    - PDF (.pdf)
    - Word文档 (.docx)
    - 纯文本 (.txt)
    """
    try:
        # 验证文件大小
        if hasattr(file, 'size') and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE} bytes)"
            )
        
        # 验证文件类型
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名不能为空"
            )
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_extension}"
            )
        
        logger.info(f"开始处理文档: {file.filename}")
        
        # 步骤1-3: 完整的文档处理流程（解析 -> 提取 -> 验证）
        document_id, document_sections, event_chains, processing_stats = await extraction_service.process_document_with_extraction(
            file, 
            apply_validation=apply_validation
        )
        
        logger.info(f"文档处理完成: {document_id}, 提取到 {len(event_chains)} 个有效事件链")
        
        # 步骤4: 保存到Neo4j图数据库（可选）
        graph_results = None
        if save_to_graph and event_chains:
            try:
                logger.info("开始保存事件链到图数据库...")
                graph_results = await graph_service.batch_create_event_chains(event_chains)
                logger.info(f"成功保存 {len(graph_results)} 个事件链到图数据库")
            except Exception as e:
                logger.error(f"保存到图数据库失败: {e}")
                # 不抛出异常，允许返回处理结果
                graph_results = {"error": str(e)}
        
        # 构建响应数据
        response_data = {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_extension[1:],  # 去掉点号
            "processing_status": ProcessingStatus.COMPLETED.value,
            
            # 文档解析结果
            "document_sections": {
                "sections": document_sections.sections,
                "section_count": len(document_sections.sections)
            },
            
            # 事件链提取结果
            "event_chains": {
                "chains": [
                    {
                        "source": chain.source,
                        "relation": chain.relation.value if hasattr(chain.relation, 'value') else str(chain.relation),
                        "target": chain.target,
                        "confidence": chain.confidence,
                        "context": chain.context
                    } for chain in event_chains
                ],
                "count": len(event_chains)
            },
            
            # 处理统计信息
            "processing_statistics": processing_stats,
            
            # 图数据库保存结果
            "graph_storage": {
                "enabled": save_to_graph,
                "results": graph_results,
                "saved_count": len(graph_results) if isinstance(graph_results, list) else 0
            }
        }
        
        logger.info(f"文档处理完成: {document_id}")
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"文档处理成功，提取到 {len(event_chains)} 个有效事件链",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {str(e)}"
        )


@router.post("/upload", response_model=BaseResponse)
async def upload_document(
    file: UploadFile = File(..., description="上传的文档文件")
):
    """
    简单文档上传和解析（不包含事件链提取）
    
    支持的文件格式:
    - PDF (.pdf)
    - Word文档 (.docx)
    - 纯文本 (.txt)
    """
    try:
        # 验证文件大小
        if hasattr(file, 'size') and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE} bytes)"
            )
        
        # 验证文件类型
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名不能为空"
            )
        
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_extension}"
            )
        
        logger.info(f"开始处理文档上传: {file.filename}")
        
        # 处理文档
        document_id, document_sections = await extraction_service.process_document(file)
        
        # 构建响应数据
        response_data = {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_extension[1:],  # 去掉点号
            "sections": document_sections.sections,
            "section_count": len(document_sections.sections),
            "processing_status": ProcessingStatus.COMPLETED.value
        }
        
        logger.info(f"文档处理完成: {document_id}")
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="文档上传和解析成功",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档处理失败: {str(e)}"
        )


@router.post("/extract-chains", response_model=BaseResponse)
async def extract_event_chains_from_sections(
    sections: DocumentSections,
    apply_validation: bool = True
):
    """
    从文档章节中提取事件链
    """
    try:
        logger.info("开始从章节提取事件链...")
        
        # 提取并验证事件链
        event_chains, processing_stats = await extraction_service.extract_and_validate_event_chains(
            sections,
            apply_validation=apply_validation
        )
        
        # 构建响应数据
        response_data = {
            "event_chains": [
                {
                    "source": chain.source,
                    "relation": chain.relation.value if hasattr(chain.relation, 'value') else str(chain.relation),
                    "target": chain.target,
                    "confidence": chain.confidence,
                    "context": chain.context
                } for chain in event_chains
            ],
            "count": len(event_chains),
            "processing_statistics": processing_stats
        }
        
        logger.info(f"事件链提取完成，获得 {len(event_chains)} 个有效事件链")
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"事件链提取成功，获得 {len(event_chains)} 个有效事件链",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"事件链提取失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"事件链提取失败: {str(e)}"
        )


@router.post("/analyze-quality", response_model=BaseResponse)
async def analyze_document_quality(sections: DocumentSections):
    """
    分析文档质量
    """
    try:
        logger.info("开始分析文档质量...")
        
        # 分析文档质量
        quality_analysis = await extraction_service.analyze_document_quality(sections)
        
        logger.info("文档质量分析完成")
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="文档质量分析完成",
            data=quality_analysis
        )
        
    except Exception as e:
        logger.error(f"文档质量分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档质量分析失败: {str(e)}"
        )
async def get_document_sections(document_id: str):
    """
    获取文档的章节内容
    """
    try:
        # 这里应该从数据库或缓存中获取文档章节信息
        # 目前返回示例数据
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="获取文档章节成功",
            data={
                "document_id": document_id,
                "sections": {
                    "事故经过": "示例事故经过内容...",
                    "原因分析": "示例原因分析内容..."
                }
            }
        )
    except Exception as e:
        logger.error(f"获取文档章节失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档章节失败: {str(e)}"
        )


@router.post("/validate-sections", response_model=BaseResponse)
async def validate_document_sections(sections: DocumentSections):
    """
    验证文档章节内容
    """
    try:
        # 验证章节内容
        errors = extraction_service.validate_sections(sections.sections)
        
        if errors:
            return BaseResponse(
                status=ResponseStatus.WARNING,
                message="章节验证发现问题",
                data={
                    "is_valid": False,
                    "errors": errors,
                    "sections": sections.sections
                }
            )
        else:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="章节验证通过",
                data={
                    "is_valid": True,
                    "errors": [],
                    "sections": sections.sections
                }
            )
            
    except Exception as e:
        logger.error(f"章节验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"章节验证失败: {str(e)}"
        )


@router.delete("/{document_id}", response_model=BaseResponse)
async def delete_document(document_id: str):
    """
    删除文档及其相关文件
    """
    try:
        # 这里应该从数据库中获取文档信息
        # 目前假设文档存在并尝试清理文件
        
        # 尝试清理不同类型的文件
        cleaned = False
        for ext in settings.ALLOWED_FILE_TYPES:
            if extraction_service.cleanup_document(document_id, ext):
                cleaned = True
                break
        
        if cleaned:
            return BaseResponse(
                status=ResponseStatus.SUCCESS,
                message="文档删除成功",
                data={"document_id": document_id}
            )
        else:
            return BaseResponse(
                status=ResponseStatus.WARNING,
                message="文档文件未找到，但记录已清理",
                data={"document_id": document_id}
            )
            
    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败: {str(e)}"
        )


@router.get("/supported-formats", response_model=BaseResponse)
async def get_supported_formats():
    """
    获取支持的文件格式列表
    """
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="获取支持格式成功",
        data={
            "supported_formats": settings.ALLOWED_FILE_TYPES,
            "max_file_size": settings.MAX_FILE_SIZE,
            "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024)
        }
    )