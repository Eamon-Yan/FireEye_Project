"""
任务管理器单元测试
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.task_manager import (
    TaskManager,
    Task,
    TaskResult,
    TaskStatus,
    TaskType,
    TASK_TTL
)


@pytest.fixture
def mock_redis():
    """模拟 Redis 客户端"""
    redis = AsyncMock()
    return redis


@pytest.fixture
def task_manager(mock_redis):
    """创建任务管理器实例"""
    manager = TaskManager()
    manager.redis = mock_redis
    return manager


@pytest.mark.asyncio
async def test_create_task(task_manager, mock_redis):
    """测试创建任务"""
    # 执行
    task = await task_manager.create_task(
        task_type=TaskType.ANALYZE,
        metadata={"text": "test content"},
        estimated_time=60
    )
    
    # 验证
    assert task.task_id is not None
    assert task.task_type == TaskType.ANALYZE
    assert task.status == TaskStatus.PENDING
    assert task.progress == 0
    assert task.estimated_time == 60
    assert task.metadata == {"text": "test content"}
    
    # 验证 Redis 调用
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == f"task:{task.task_id}"
    assert call_args[0][1] == TASK_TTL


@pytest.mark.asyncio
async def test_get_task_status_success(task_manager, mock_redis):
    """测试获取任务状态 - 成功"""
    # 准备
    task_id = "test-task-123"
    task_data = {
        "task_id": task_id,
        "task_type": "analyze",
        "status": "processing",
        "progress": 50,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "estimated_time": 60,
        "result": None,
        "error": None,
        "metadata": {}
    }
    mock_redis.get.return_value = json.dumps(task_data)
    
    # 执行
    task = await task_manager.get_task_status(task_id)
    
    # 验证
    assert task is not None
    assert task.task_id == task_id
    assert task.status == TaskStatus.PROCESSING
    assert task.progress == 50
    
    mock_redis.get.assert_called_once_with(f"task:{task_id}")


@pytest.mark.asyncio
async def test_get_task_status_not_found(task_manager, mock_redis):
    """测试获取任务状态 - 不存在"""
    # 准备
    mock_redis.get.return_value = None
    
    # 执行
    task = await task_manager.get_task_status("nonexistent")
    
    # 验证
    assert task is None


@pytest.mark.asyncio
async def test_update_task_progress(task_manager, mock_redis):
    """测试更新任务进度"""
    # 准备
    task_id = "test-task-123"
    existing_task = Task(
        task_id=task_id,
        task_type=TaskType.ANALYZE,
        status=TaskStatus.PROCESSING,
        progress=30
    )
    
    # 模拟 get_task_status
    with patch.object(task_manager, 'get_task_status', return_value=existing_task):
        # 执行
        success = await task_manager.update_task_progress(
            task_id=task_id,
            progress=60,
            status=TaskStatus.PROCESSING
        )
        
        # 验证
        assert success is True
        assert existing_task.progress == 60
        assert existing_task.status == TaskStatus.PROCESSING
        
        # 验证 Redis 保存
        mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_update_task_progress_clamps_values(task_manager, mock_redis):
    """测试更新任务进度 - 边界值处理"""
    # 准备
    task_id = "test-task-123"
    existing_task = Task(
        task_id=task_id,
        task_type=TaskType.ANALYZE,
        status=TaskStatus.PROCESSING,
        progress=50
    )
    
    # 测试超过 100
    with patch.object(task_manager, 'get_task_status', return_value=existing_task):
        await task_manager.update_task_progress(task_id, 150)
        assert existing_task.progress == 100
    
    # 测试小于 0
    with patch.object(task_manager, 'get_task_status', return_value=existing_task):
        await task_manager.update_task_progress(task_id, -10)
        assert existing_task.progress == 0


@pytest.mark.asyncio
async def test_update_task_progress_not_found(task_manager, mock_redis):
    """测试更新任务进度 - 任务不存在"""
    # 准备
    with patch.object(task_manager, 'get_task_status', return_value=None):
        # 执行
        success = await task_manager.update_task_progress("nonexistent", 50)
        
        # 验证
        assert success is False


@pytest.mark.asyncio
async def test_complete_task(task_manager, mock_redis):
    """测试完成任务"""
    # 准备
    task_id = "test-task-123"
    existing_task = Task(
        task_id=task_id,
        task_type=TaskType.ANALYZE,
        status=TaskStatus.PROCESSING,
        progress=90
    )
    
    result = TaskResult(
        event_chains=[{"id": "chain1"}],
        entities_count=10,
        relationships_count=15,
        message="Analysis completed"
    )
    
    # 执行
    with patch.object(task_manager, 'get_task_status', return_value=existing_task):
        success = await task_manager.complete_task(task_id, result)
        
        # 验证
        assert success is True
        assert existing_task.status == TaskStatus.COMPLETED
        assert existing_task.progress == 100
        assert existing_task.result == result
        
        # 验证 Redis 保存
        mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_complete_task_not_found(task_manager, mock_redis):
    """测试完成任务 - 任务不存在"""
    # 准备
    result = TaskResult(message="Test")
    
    with patch.object(task_manager, 'get_task_status', return_value=None):
        # 执行
        success = await task_manager.complete_task("nonexistent", result)
        
        # 验证
        assert success is False


@pytest.mark.asyncio
async def test_fail_task(task_manager, mock_redis):
    """测试标记任务失败"""
    # 准备
    task_id = "test-task-123"
    existing_task = Task(
        task_id=task_id,
        task_type=TaskType.ANALYZE,
        status=TaskStatus.PROCESSING,
        progress=50
    )
    
    error_message = "Analysis failed due to invalid input"
    
    # 执行
    with patch.object(task_manager, 'get_task_status', return_value=existing_task):
        success = await task_manager.fail_task(task_id, error_message)
        
        # 验证
        assert success is True
        assert existing_task.status == TaskStatus.FAILED
        assert existing_task.error == error_message
        
        # 验证 Redis 保存
        mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_fail_task_not_found(task_manager, mock_redis):
    """测试标记任务失败 - 任务不存在"""
    with patch.object(task_manager, 'get_task_status', return_value=None):
        # 执行
        success = await task_manager.fail_task("nonexistent", "error")
        
        # 验证
        assert success is False


@pytest.mark.asyncio
async def test_task_key_format(task_manager):
    """测试任务键格式"""
    task_id = "abc-123"
    key = task_manager._get_task_key(task_id)
    assert key == "task:abc-123"


@pytest.mark.asyncio
async def test_cleanup_expired_tasks(task_manager):
    """测试清理过期任务"""
    # 执行
    count = await task_manager.cleanup_expired_tasks()
    
    # 验证（Redis 自动处理 TTL，所以返回 0）
    assert count == 0


def test_task_model():
    """测试 Task 模型"""
    task = Task(
        task_id="test-123",
        task_type=TaskType.UPLOAD,
        status=TaskStatus.PENDING,
        progress=0
    )
    
    assert task.task_id == "test-123"
    assert task.task_type == TaskType.UPLOAD
    assert task.status == TaskStatus.PENDING
    assert task.progress == 0
    assert task.result is None
    assert task.error is None
    assert task.metadata == {}


def test_task_result_model():
    """测试 TaskResult 模型"""
    result = TaskResult(
        event_chains=[{"id": "1"}],
        entities_count=5,
        relationships_count=10,
        document_id="doc-123",
        message="Success"
    )
    
    assert len(result.event_chains) == 1
    assert result.entities_count == 5
    assert result.relationships_count == 10
    assert result.document_id == "doc-123"
    assert result.message == "Success"


def test_task_status_enum():
    """测试 TaskStatus 枚举"""
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.PROCESSING == "processing"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED == "failed"
    assert TaskStatus.TIMEOUT == "timeout"


def test_task_type_enum():
    """测试 TaskType 枚举"""
    assert TaskType.ANALYZE == "analyze"
    assert TaskType.UPLOAD == "upload"
