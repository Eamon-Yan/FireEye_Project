"""
Chat API Layer for AstrBot Integration
为聊天平台提供优化的API端点
"""

import logging
import uuid
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.api.auth import verify_api_key
from app.core.config import settings
from app.schemas.base import BaseResponse, ResponseStatus
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChatAnalyzeRequest,
    TaskResponse,
    TaskStatusResponse,
    ChatStatsRequest,
    StatsResponse
)
from app.services.session_service import session_service
from app.services.context_manager import context_manager
from app.services.graph_service import graph_service
from app.services.task_manager import task_manager, TaskType
from app.workers.analysis_worker import start_analyze_task
from app.workers.upload_worker import start_upload_task

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=BaseResponse)
async def health_check():
    """
    健康检查端点
    用于测试Chat API Layer是否正常运行
    """
    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Chat API Layer is running",
        data={
            "service": "fire-eye-chat-api",
            "version": "1.0.0",
            "status": "healthy"
        }
    )


@router.post("/query", response_model=ChatQueryResponse)
async def query_knowledge_graph(
    request: ChatQueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    查询知识图谱
    支持上下文感知的多轮对话
    
    Args:
        request: 查询请求（包含查询文本和可选的会话ID）
        api_key: API密钥（通过依赖注入验证）
        
    Returns:
        ChatQueryResponse: 查询结果
    """
    try:
        logger.info(f"Received query: '{request.query}' with session_id: {request.session_id}")
        
        # 获取或创建会话
        # 使用 API key 作为 user_id（或者可以从请求中获取）
        user_id = api_key[:8]  # 使用 API key 的前8个字符作为用户标识
        
        if request.session_id:
            session = await session_service.get_session(request.session_id)
            if not session:
                # 会话不存在，创建新会话
                new_session_id = await session_service.create_session(user_id=user_id)
                session = await session_service.get_session(new_session_id)
                logger.info(f"Session {request.session_id} not found, created new session {new_session_id}")
        else:
            # 创建新会话
            new_session_id = await session_service.create_session(user_id=user_id)
            session = await session_service.get_session(new_session_id)
            logger.info(f"Created new session {new_session_id}")
        
        # 解析上下文引用
        resolved_query = await context_manager.resolve_reference(
            session_id=session.session_id,
            query=request.query
        )
        
        if resolved_query != request.query:
            logger.info(f"Query resolved: '{request.query}' -> '{resolved_query}'")
        
        # 查询图数据库
        query_results = await graph_service.query_graph(resolved_query)
        
        # 更新会话
        from app.services.session_service import ConversationTurn
        from datetime import datetime
        turn = ConversationTurn(
            timestamp=datetime.utcnow(),
            user_message=request.query,
            bot_response=f"找到 {len(query_results)} 条结果",
            query_results=query_results
        )
        await session_service.update_session(
            session_id=session.session_id,
            turn=turn
        )
        
        # 构建响应
        response_data = {
            "session_id": session.session_id,
            "query": request.query,
            "resolved_query": resolved_query if resolved_query != request.query else None,
            "results": query_results,
            "total_count": len(query_results),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Query completed: {len(query_results)} results found")
        
        return ChatQueryResponse(
            status="success",
            message=f"查询成功，返回 {len(query_results)} 个结果",
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Query failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )



@router.post("/analyze", response_model=TaskResponse)
async def analyze_text(
    request: ChatAnalyzeRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    分析文本内容
    异步处理，立即返回任务ID
    
    Args:
        request: 分析请求（包含文本内容）
        api_key: API密钥
        
    Returns:
        TaskResponse: 任务信息
    """
    try:
        # 验证文本长度
        if len(request.text) > 50000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文本内容过长，最大支持50,000字符"
            )
        
        if len(request.text.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文本内容不能为空"
            )
        
        logger.info(f"Received analyze request: {len(request.text)} characters")
        
        # 创建任务
        task = await task_manager.create_task(
            task_type=TaskType.ANALYZE,
            metadata={
                "text_length": len(request.text),
                "session_id": request.session_id
            },
            estimated_time=60
        )
        
        # 启动后台工作器
        start_analyze_task(
            task_id=task.task_id,
            text=request.text,
            metadata={"session_id": request.session_id}
        )
        
        logger.info(f"Analysis task {task.task_id} created and started")
        
        return TaskResponse(
            status="success",
            message="分析任务已创建，正在处理中",
            data={
                "task_id": task.task_id,
                "status": task.status.value,
                "estimated_time": task.estimated_time
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create analysis task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建分析任务失败: {str(e)}"
        )


@router.post("/upload", response_model=TaskResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    api_key: str = Depends(verify_api_key)
):
    """
    上传文件进行分析
    支持 PDF、TXT、DOCX 格式
    
    Args:
        file: 上传的文件
        session_id: 可选的会话ID
        api_key: API密钥
        
    Returns:
        TaskResponse: 任务信息
    """
    try:
        # 验证文件类型
        allowed_extensions = ['.pdf', '.txt', '.docx', '.doc']
        file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型。支持的格式: {', '.join(allowed_extensions)}"
            )
        
        # 验证文件大小（10MB）
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小超过限制（最大10MB）"
            )
        
        logger.info(f"Received file upload: {file.filename} ({len(file_content)} bytes)")
        
        # 生成文档ID和保存路径
        document_id = str(uuid.uuid4())
        upload_dir = settings.UPLOAD_DIR
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{document_id}{file_ext}"
        
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"File saved to {file_path}")
        
        # 创建任务
        task = await task_manager.create_task(
            task_type=TaskType.UPLOAD,
            metadata={
                "filename": file.filename,
                "file_size": len(file_content),
                "document_id": document_id,
                "session_id": session_id
            },
            estimated_time=90
        )
        
        # 启动后台工作器
        start_upload_task(
            task_id=task.task_id,
            file_path=str(file_path),
            document_id=document_id,
            metadata={"session_id": session_id},
            delete_after_processing=True
        )
        
        logger.info(f"Upload task {task.task_id} created for document {document_id}")
        
        return TaskResponse(
            status="success",
            message=f"文件 {file.filename} 上传成功，正在处理中",
            data={
                "task_id": task.task_id,
                "status": task.status,
                "document_id": document_id,
                "filename": file.filename,
                "estimated_time": task.estimated_time
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    查询任务状态
    
    Args:
        task_id: 任务ID
        api_key: API密钥
        
    Returns:
        TaskStatusResponse: 任务状态信息
    """
    try:
        task = await task_manager.get_task_status(task_id)
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务 {task_id} 不存在"
            )
        
        # Convert Task to dict for response
        task_dict = {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "progress": task.progress,
            "created_at": task.created_at,
            "started_at": None,
            "completed_at": task.updated_at if task.status.value == "completed" else None,
            "estimated_time_remaining": task.estimated_time,
            "result": task.result.model_dump() if task.result else None,
            "error": task.error,
            "session_id": task.metadata.get("session_id"),
            "document_metadata": task.metadata.get("document_metadata")
        }
        
        return TaskStatusResponse(
            status="success",
            data=task_dict
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询任务状态失败: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(
    stat_type: Optional[str] = None,
    time_range: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    获取统计信息
    支持缓存（5分钟TTL）
    
    Args:
        stat_type: 统计类型（可选）
        time_range: 时间范围（可选）
        api_key: API密钥
        
    Returns:
        StatsResponse: 统计信息
    """
    try:
        logger.info(f"Fetching statistics: type={stat_type}, range={time_range}")
        
        # 查询图数据库获取统计信息
        # Note: GraphService.get_statistics() doesn't accept parameters yet
        # TODO: Implement filtering by stat_type and time_range
        stats_obj = await graph_service.get_statistics()
        
        # Convert GraphStatistics object to dict
        stats = {
            "total_events": stats_obj.node_count,
            "total_entities": stats_obj.node_count,
            "total_relationships": stats_obj.relationship_count,
            "total_documents": 0,  # Not tracked yet
            "node_types": stats_obj.node_type_distribution,
            "relationship_types": stats_obj.relationship_type_distribution,
            "avg_degree": stats_obj.avg_degree,
            "max_depth": stats_obj.max_depth
        }
        
        return StatsResponse(
            status="success",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )
