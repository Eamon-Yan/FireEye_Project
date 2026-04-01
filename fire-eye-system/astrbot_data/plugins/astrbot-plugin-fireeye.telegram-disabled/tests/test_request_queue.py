"""
Request Queue 单元测试
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from request_queue_module import RequestQueue, QueueFullError


class TestRequestQueue:
    """请求队列测试"""
    
    @pytest.fixture
    def queue(self):
        """创建请求队列实例"""
        return RequestQueue(max_concurrent=2, max_queue_size=5)
    
    def test_init(self, queue):
        """测试初始化"""
        assert queue.max_concurrent == 2
        assert queue.max_queue_size == 5
        assert queue.active_requests == 0
        assert len(queue.queue) == 0
    
    @pytest.mark.asyncio
    async def test_enqueue_immediate_execution(self, queue):
        """测试立即执行"""
        async def test_func():
            await asyncio.sleep(0.1)
            return "result"
        
        result = await queue.enqueue(test_func)
        assert result == "result"
    
    @pytest.mark.asyncio
    async def test_concurrent_limit(self, queue):
        """测试并发限制"""
        results = []
        
        async def slow_func(value):
            await asyncio.sleep(0.2)
            return value
        
        # 启动3个请求，但只有2个能并发执行
        tasks = [
            queue.enqueue(slow_func, i)
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        assert results == [0, 1, 2]
    
    @pytest.mark.asyncio
    async def test_queue_full_error(self, queue):
        """测试队列满错误"""
        async def slow_func():
            await asyncio.sleep(1)
            return "done"
        
        # 填满队列
        tasks = []
        for i in range(7):  # 2个并发 + 5个队列
            tasks.append(queue.enqueue(slow_func))
        
        # 第8个应该抛出异常
        with pytest.raises(QueueFullError):
            await queue.enqueue(slow_func)
        
        # 取消所有任务
        for task in tasks:
            task.cancel()
    
    @pytest.mark.asyncio
    async def test_queue_processing(self, queue):
        """测试队列处理"""
        execution_order = []
        
        async def track_func(value):
            execution_order.append(value)
            await asyncio.sleep(0.1)
            return value
        
        # 启动5个请求
        tasks = [
            queue.enqueue(track_func, i)
            for i in range(5)
        ]
        
        await asyncio.gather(*tasks)
        
        # 验证所有请求都被执行
        assert len(execution_order) == 5
        assert set(execution_order) == {0, 1, 2, 3, 4}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
