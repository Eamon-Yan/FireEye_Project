"""
Task Poller 单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.polling import TaskPoller


class TestTaskPoller:
    """任务轮询器测试"""
    
    @pytest.fixture
    def poller(self):
        """创建任务轮询器实例"""
        api_client = MagicMock()
        return TaskPoller(api_client=api_client)
    
    def test_init(self, poller):
        """测试初始化"""
        assert poller.polling_interval == 3
        assert poller.max_polling_time == 300
    
    @pytest.mark.asyncio
    async def test_poll_task_completed(self, poller):
        """测试轮询完成的任务"""
        # 模拟任务立即完成
        poller.api_client.get_task_status = AsyncMock(return_value={
            "success": True,
            "data": {
                "status": "completed",
                "progress": 100,
                "result": {"entities_count": 10}
            }
        })
        
        on_complete = AsyncMock()
        on_failed = AsyncMock()
        
        await poller.poll_task(
            task_id="task-123",
            on_complete=on_complete,
            on_failed=on_failed
        )
        
        on_complete.assert_called_once()
        on_failed.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_poll_task_failed(self, poller):
        """测试轮询失败的任务"""
        poller.api_client.get_task_status = AsyncMock(return_value={
            "success": True,
            "data": {
                "status": "failed",
                "error": "处理失败"
            }
        })
        
        on_complete = AsyncMock()
        on_failed = AsyncMock()
        
        await poller.poll_task(
            task_id="task-123",
            on_complete=on_complete,
            on_failed=on_failed
        )
        
        on_complete.assert_not_called()
        on_failed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_poll_task_progress(self, poller):
        """测试轮询进度更新"""
        # 模拟进度更新
        call_count = 0
        
        async def mock_status(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return {
                    "success": True,
                    "data": {
                        "status": "processing",
                        "progress": call_count * 30
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "status": "completed",
                        "progress": 100
                    }
                }
        
        poller.api_client.get_task_status = mock_status
        poller.polling_interval = 0.1  # 加快测试速度
        
        on_progress = AsyncMock()
        on_complete = AsyncMock()
        
        await poller.poll_task(
            task_id="task-123",
            on_progress=on_progress,
            on_complete=on_complete
        )
        
        assert on_progress.call_count >= 2
        on_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_poll_task_timeout(self, poller):
        """测试轮询超时"""
        # 模拟任务一直处理中
        poller.api_client.get_task_status = AsyncMock(return_value={
            "success": True,
            "data": {
                "status": "processing",
                "progress": 50
            }
        })
        
        poller.polling_interval = 0.1
        poller.max_polling_time = 0.5  # 设置很短的超时时间
        
        on_timeout = AsyncMock()
        on_complete = AsyncMock()
        
        await poller.poll_task(
            task_id="task-123",
            on_timeout=on_timeout,
            on_complete=on_complete
        )
        
        on_timeout.assert_called_once()
        on_complete.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
