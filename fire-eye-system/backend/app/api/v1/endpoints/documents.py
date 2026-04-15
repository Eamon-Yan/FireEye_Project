"""
文档管理API端点
集成完整的文档处理工作流：解析 -> 提取 -> 验证 -> 存储
"""

import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.schemas.base import BaseResponse, ResponseStatus
from app.db.redis_client import redis_client
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


async def _set_task_status(document_id: str, payload: Dict[str, Any], expire: int = 3600) -> None:
    await redis_client.set(f"task:{document_id}", payload, expire=expire)


@router.post("/process", response_model=BaseResponse)
async def process_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="上传的文档文件"),
    apply_validation: bool = True,
    save_to_graph: bool = True,
    graph_service: GraphService = GraphServiceDep
):
    """
    统一文档处理端点 (异步任务版)
    
    完整工作流程：
    1. 立即返回 document_id 和状态
    2. 后台执行：解析 -> 提取 -> 验证 -> 存储
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
        
        document_id = str(uuid.uuid4())
        
        # 初始化任务状态
        task_status = {
            "document_id": document_id,
            "filename": file.filename,
            "status": ProcessingStatus.PROCESSING.value,
            "stage": "parsing",
            "message": "正在解析文档内容...",
            "progress": 10,
            "start_time": datetime.now().isoformat(),
            "result": None
        }
        await _set_task_status(document_id, task_status)
        
        # 预读取文件内容到内存或临时文件，因为 UploadFile 在后台任务中可能会关闭
        file_content = await file.read()
        
        async def run_extraction_task():
            current_status = dict(task_status)

            async def update_status(**updates: Any) -> None:
                nonlocal current_status
                current_status = {**current_status, **updates}
                await _set_task_status(document_id, current_status)

            try:
                # 重新包装文件对象
                from io import BytesIO
                wrapped_file = UploadFile(
                    file=BytesIO(file_content),
                    filename=file.filename,
                    headers=file.headers
                )
                
                # 更新状态：提取中
                await update_status(
                    stage="extracting",
                    message="正在提取事件链...",
                    progress=30
                )
                
                doc_id, document_sections, event_chains, processing_stats, layered_result = await extraction_service.process_document_with_extraction(
                    wrapped_file,
                    apply_validation=apply_validation,
                    document_id=document_id # 传入固定的 ID
                )

                await update_status(
                    stage="extracted",
                    message="事件链提取完成，正在整理结果...",
                    progress=60
                )
                
                # 更新状态：存储中
                if save_to_graph and event_chains:
                    await update_status(
                        stage="storing",
                        message="正在保存到图数据库...",
                        progress=80
                    )
                else:
                    await update_status(
                        stage="finalizing",
                        message="正在整理处理结果...",
                        progress=85
                    )
                
                graph_results = None
                if save_to_graph and event_chains:
                    try:
                        graph_results = await graph_service.batch_create_event_chains(event_chains)
                    except Exception as e:
                        logger.error(f"任务 {document_id} 存储失败: {e}")
                        graph_results = {"error": str(e)}
                
                final_result = {
                    "document_id": document_id,
                    "filename": file.filename,
                    "file_type": file_extension[1:],
                    "processing_status": ProcessingStatus.COMPLETED.value,
                    "document_sections": {
                        "section_count": len(document_sections.sections)
                    },
                    "processing_statistics": processing_stats,
                    "event_chains": {
                        "count": len(event_chains),
                        "chains": [
                            {
                                "source": chain.source,
                                "relation": chain.relation.value if hasattr(chain.relation, 'value') else str(chain.relation),
                                "target": chain.target,
                                "confidence": chain.confidence,
                                "context": chain.context
                            } for chain in event_chains
                        ]
                    },
                    "graph_results": graph_results,
                    "layered_extraction": {
                        "node_count": len(layered_result.nodes) if layered_result else 0,
                        "edge_count": len(layered_result.edges) if layered_result else 0
                    }
                }
                
                # 更新状态：已完成
                await update_status(
                    status=ProcessingStatus.COMPLETED.value,
                    stage="completed",
                    message="文档处理完成",
                    progress=100,
                    result=final_result,
                    end_time=datetime.now().isoformat()
                )
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"后台任务 {document_id} 失败: {error_msg}")
                await update_status(
                    status=ProcessingStatus.FAILED.value,
                    stage="failed",
                    message=_classify_error(error_msg),
                    error=error_msg,
                    end_time=datetime.now().isoformat()
                )

        background_tasks.add_task(run_extraction_task)
        
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="文件已上传，后台正在处理",
            data={"document_id": document_id, "status": "processing"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发起处理任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"无法发起处理任务: {str(e)}"
        )

@router.get("/status/{document_id}", response_model=BaseResponse)
async def get_task_status(document_id: str):
    """获取文档处理任务状态"""
    task_status = await redis_client.get(f"task:{document_id}")
    if not task_status:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="查询成功",
        data=task_status
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
