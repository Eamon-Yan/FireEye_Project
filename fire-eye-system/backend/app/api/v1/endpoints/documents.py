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
    2. 使用LLM提取分层事件图并映射事件链 (LLMService)
    3. 验证和归一化事件链 (ValidationService)
    4. 保存到Neo4j图数据库 (GraphService)
    """
    try:
        content_length = file.headers.get("content-length") if file.headers else None
        if content_length and int(content_length) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE} bytes)"
            )
        
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
        document_id, document_sections, event_chains, processing_stats, layered_result = await extraction_service.process_document_with_extraction(
            file,
            apply_validation=apply_validation
        )
        
        logger.info(f"文档处理完成: {document_id}, 提取到 {len(event_chains)} 个有效事件链")
        
        graph_results = None
        if save_to_graph and event_chains:
            try:
                logger.info("开始保存事件链到图数据库...")
                graph_results = await graph_service.batch_create_event_chains(event_chains)
                logger.info(f"成功保存 {len(graph_results)} 个事件链到图数据库")
            except Exception as e:
                logger.error(f"保存到图数据库失败: {e}")
                graph_results = {"error": str(e)}
        
        response_data = {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_extension[1:],
            "processing_status": ProcessingStatus.COMPLETED.value,
            "document_sections": {
                "sections": document_sections.sections,
                "section_count": len(document_sections.sections)
            },
            "layered_extraction": {
                "nodes": [
                    {
                        "node_type": node.node_type.value if hasattr(node.node_type, 'value') else str(node.node_type),
                        "description": node.description,
                        "standard_term": node.standard_term,
                        "context": node.context,
                    }
                    for node in (layered_result.nodes if layered_result else [])
                ],
                "edges": [
                    {
                        "source": edge.source,
                        "source_type": edge.source_type.value if hasattr(edge.source_type, 'value') else str(edge.source_type),
                        "target": edge.target,
                        "target_type": edge.target_type.value if hasattr(edge.target_type, 'value') else str(edge.target_type),
                        "relation": edge.relation.value if hasattr(edge.relation, 'value') else str(edge.relation),
                        "confidence": edge.confidence,
                        "context": edge.context,
                    }
                    for edge in (layered_result.edges if layered_result else [])
                ],
                "node_count": len(layered_result.nodes) if layered_result else 0,
                "edge_count": len(layered_result.edges) if layered_result else 0,
            },
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
            "processing_statistics": processing_stats,
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
        error_msg = str(e)
        logger.error(f"文档处理失败: {error_msg}")
        user_friendly_detail = _classify_error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=user_friendly_detail
        )


def _classify_error(error_msg: str) -> str:
    error_msg_lower = error_msg.lower()

    if any(x in error_msg_lower for x in [
        'json decode', 'json解析', 'json.decoder', 'json.decodererror'
    ]):
        return (
            '文档内容解析失败：LLM返回的响应格式异常。'
            '这通常是模型输出不稳定导致的，建议稍后重试上传同一文档，'
            '或尝试使用更规范的火灾事故报告文本。'
        )

    if any(x in error_msg_lower for x in [
        'validation error', '格式验证失败', '验证失败', 'extractededge', 'extractednode'
    ]):
        return (
            '事件链结构解析失败：模型返回的图谱结构不符合规范。'
            '系统已尝试自动修复常见错误，如问题持续，请确保文档内容清晰描述了'
            '完整的火灾事故经过、原因和后果。'
        )

    if any(x in error_msg_lower for x in [
        '缺少nodes', '缺少edges', 'nodes或edges', '缺少event_chains', 'event_chains字段'
    ]):
        return (
            '事件链提取失败：未能从文档中识别出足够的事件关系。'
            '请确认文档包含清晰的因果描述，例如：'
            '电气线路老化导致短路，短路引燃可燃物，火势蔓延造成损失。'
        )

    if any(x in error_msg_lower for x in [
        '文档解析失败', 'pdf解析', 'docx解析', 'txt解析', 'pdf文件解析', 'docx文件解析', 'txt文件解析'
    ]):
        return (
            '文档内容解析失败：无法提取文档中的文本内容。'
            '请确保上传的是文本型PDF（不是扫描图片）、标准DOCX格式或UTF-8编码的TXT文件。'
        )

    if any(x in error_msg_lower for x in [
        '文档内容过短', '内容为空', '内容过短', '有效内容'
    ]):
        return (
            '文档内容不足：提取的文本过短或几乎为空。'
            '请上传包含完整火灾事故描述的文档，建议字数不少于200字。'
        )

    if any(x in error_msg_lower for x in [
        'openai_api_key', 'api_key', 'llm', '模型', 'api错误', 'api调用'
    ]):
        return (
            'AI服务调用失败：LLM服务配置异常或网络问题。'
            '请检查后端服务的OPENAI_API_KEY等LLM配置是否正确。'
        )

    if any(x in error_msg_lower for x in [
        '超时', 'timeout', 'timeouterror', 'timed out'
    ]):
        return (
            '处理超时：文档处理耗时过长。'
            '建议使用更小的文档（不超过1MB），或稍后重试。'
        )

    if any(x in error_msg_lower for x in [
        '图数据库', 'neo4j', 'graph', '保存到图', '图存储'
    ]):
        return (
            '图数据库保存失败：事件链已提取成功，但保存到图数据库时出现问题。'
            '这不影响本次提取结果，可稍后重试或检查Neo4j服务状态。'
        )

    if any(x in error_msg_lower for x in [
        'section', '章节', '章节验证', 'required_sections'
    ]):
        return (
            '文档章节验证失败：未找到必需的章节结构。'
            '建议文档包含事故经过、原因分析等标准章节标题。'
        )

    return f'文档处理失败：{error_msg}'


@router.post("/upload", response_model=BaseResponse)
async def upload_document(
    file: UploadFile = File(..., description="上传的文档文件")
):
    """简单文档上传和解析（不包含事件链提取）"""
    try:
        content_length = file.headers.get("content-length") if file.headers else None
        if content_length and int(content_length) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE} bytes)"
            )
        
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
        document_id, document_sections = await extraction_service.process_document(file)
        
        response_data = {
            "document_id": document_id,
            "filename": file.filename,
            "file_type": file_extension[1:],
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
