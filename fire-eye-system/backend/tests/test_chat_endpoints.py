"""
聊天 API 端点集成测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.api.v1.endpoints.chat import (
    query_knowledge_graph,
    analyze_text,
    get_task_status,
    get_statistics
)
from app.schemas.chat import ChatQueryRequest, ChatAnalyzeRequest
from app.services.task_manager import TaskType, TaskStatus


@pytest.mark.asyncio
async def test_query_knowledge_graph_new_session():
    """测试查询端点 - 新会话"""
    # 准备
    request = ChatQueryRequest(query="查询火灾事故")
    
    # Mock 依赖
    with patch('app.api.v1.endpoints.chat.session_service') as mock_session_service, \
         patch('app.api.v1.endpoints.chat.context_manager') as mock_context_manager, \
         patch('app.api.v1.endpoints.chat.graph_service') as mock_graph_service:
        
        # 配置 mock
        mock_session = MagicMock()
        mock_session.session_id = "test-session-123"
        mock_session_service.create_session = AsyncMock(return_value=mock_session)
        mock_context_manager.resolve_reference = AsyncMock(return_value="查询火灾事故")
        mock_graph_service.query_graph = AsyncMock(return_value=[{"id": "1", "type": "event"}])
        mock_session_service.update_session = AsyncMock()
        
        # 执行
        response = await query_knowledge_graph(request, api_key="test-key")
        
        # 验证
        assert response.session_id == "test-session-123"
        assert response.query == "查询火灾事故"
        assert response.result_count == 1
        assert len(response.results) == 1


@pytest.mark.asyncio
async def test_query_knowledge_graph_existing_session():
    """测试查询端点 - 已存在会话"""
    # 准备
    request = ChatQueryRequest(query="主要原因是什么", session_id="existing-session")
    
    # Mock 依赖
    with patch('app.api.v1.endpoints.chat.session_service') as mock_session_service, \
         patch('app.api.v1.endpoints.chat.context_manager') as mock_context_manager, \
         patch('app.api.v1.endpoints.chat.graph_service') as mock_graph_service:
        
        # 配置 mock
        mock_session = MagicMock()
        mock_session.session_id = "existing-session"
        mock_session_service.get_session = AsyncMock(return_value=mock_session)
        mock_context_manager.resolve_reference = AsyncMock(return_value="火灾事故的主要原因是什么")
        mock_graph_service.query_graph = AsyncMock(return_value=[{"id": "1", "cause": "电气故障"}])
        mock_session_service.update_session = AsyncMock()
        
        # 执行
        response = await query_knowledge_graph(request, api_key="test-key")
        
        # 验证
        assert response.session_id == "existing-session"
        assert response.resolved_query == "火灾事故的主要原因是什么"
        assert response.result_count == 1


@pytest.mark.asyncio
async def test_analyze_text_success():
    """测试文本分析端点 - 成功"""
    # 准备
    request = ChatAnalyzeRequest(text="这是一段测试文本" * 100)
    
    # Mock 依赖
    with patch('app.api.v1.endpoints.chat.task_manager') as mock_task_manager, \
         patch('app.api.v1.endpoints.chat.start_analyze_task') as mock_start_task:
        
        # 配置 mock
        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.status = TaskStatus.PENDING
        mock_task.estimated_time = 60
        mock_task_manager.create_task = AsyncMock(return_value=mock_task)
        
        # 执行
        response = await analyze_text(request, api_key="test-key")
        
        # 验证
        assert response.task_id == "task-123"
        assert response.status == TaskStatus.PENDING
        assert response.estimated_time == 60
        mock_start_task.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_text_too_long():
    """测试文本分析端点 - 文本过长"""
    # 准备
    request = ChatAnalyzeRequest(text="x" * 60000)  # 超过 50,000 字符
    
    # 执行并验证
    with pytest.raises(HTTPException) as exc_info:
        await analyze_text(request, api_key="test-key")
    
    assert exc_info.value.status_code == 400
    assert "过长" in exc_info.value.detail


@pytest.mark.asyncio
async def test_analyze_text_empty():
    """测试文本分析端点 - 空文本"""
    # 准备
    request = ChatAnalyzeRequest(text="   ")
    
    # 执行并验证
    with pytest.raises(HTTPException) as exc_info:
        await analyze_text(request, api_key="test-key")
    
    assert exc_info.value.status_code == 400
    assert "不能为空" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_task_status_success():
    """测试获取任务状态 - 成功"""
    # Mock 依赖
    with patch('app.api.v1.endpoints.chat.task_manager') as mock_task_manager:
        # 配置 mock
        mock_task = MagicMock()
        mock_task.task_id = "task-123"
        mock_task.status = TaskStatus.COMPLETED
        mock_task.progress = 100
        mock_task.estimated_time = 60
        mock_task.result = None
        mock_task.error = None
        mock_task.created_at = None
        mock_task.updated_at = None
        mock_task_manager.get_task_status = AsyncMock(return_value=mock_task)
        
        # 执行
        response = await get_task_status("task-123", api_key="test-key")
        
        # 验证
        assert response.task_id == "task-123"
        assert response.status == TaskStatus.COMPLETED
        assert response.progress == 100


@pytest.mark.asyncio
async def test_get_task_status_not_found():
    """测试获取任务状态 - 任务不存在"""
    # Mock 依赖
    with patch('app.api.v1.endpoints.chat.task_manager') as mock_task_manager:
        mock_task_manager.get_task_status = AsyncMock(return_value=None)
        
        # 执行并验证
        with pytest.raises(HTTPException) as exc_info:
            await get_task_status("nonexistent", api_key="test-key")
        
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_statistics():
    """测试获取统计信息"""
    # Mock 依赖
    with patch('app.api.v1.endpoints.chat.graph_service') as mock_graph_service:
        # 配置 mock
        mock_stats = {
            "total_events": 100,
            "total_entities": 500,
            "total_relationships": 300,
            "total_documents": 50
        }
        mock_graph_service.get_statistics = AsyncMock(return_value=mock_stats)
        
        # 执行
        response = await get_statistics(api_key="test-key")
        
        # 验证
        assert response.total_events == 100
        assert response.total_entities == 500
        assert response.total_relationships == 300
        assert response.total_documents == 50
