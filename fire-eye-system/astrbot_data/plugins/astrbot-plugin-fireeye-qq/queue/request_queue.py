"""
请求队列
管理并发请求和队列
"""

import asyncio
from collections import deque
from typing import Callable, Any
from loguru import logger


class QueueFullError(Exception):
    """队列满异常"""
    pass


class RequestQueue:
    """请求队列"""
    
    def __init__(self, max_concurrent: int = 5, max_queue_size: int = 20):
        """
        初始化请求队列
        
        Args:
            max_concurrent: 最大并发请求数
            max_queue_size: 队列最大长度
        """
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.active_requests = 0
        self.queue = deque()
        self.lock = asyncio.Lock()
        
        logger.info(f"[Fire-Eye QQ] RequestQueue initialized: max_concurrent={max_concurrent}, max_queue={max_queue_size}")
    
    async def enqueue(self, request_func: Callable, *args, **kwargs) -> Any:
        """
        将请求加入队列
        
        Args:
            request_func: 请求函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            请求结果
            
        Raises:
            QueueFullError: 队列已满
        """
        async with self.lock:
            # 检查是否可以立即执行
            if self.active_requests < self.max_concurrent:
                self.active_requests += 1
                try:
                    logger.debug(f"[Fire-Eye QQ] Executing request immediately (active: {self.active_requests})")
                    result = await request_func(*args, **kwargs)
                    return result
                finally:
                    self.active_requests -= 1
                    await self._process_queue()
            
            # 检查队列容量
            if len(self.queue) >= self.max_queue_size:
                logger.warning(f"[Fire-Eye QQ] Queue full (size: {len(self.queue)})")
                raise QueueFullError("系统繁忙，请稍后重试")
            
            # 添加到队列
            future = asyncio.Future()
            self.queue.append((request_func, args, kwargs, future))
            
            # 估计等待时间
            estimated_wait = len(self.queue) * 5  # 粗略估计：每个请求5秒
            logger.info(f"[Fire-Eye QQ] Request queued. Position: {len(self.queue)}, Estimated wait: {estimated_wait}s")
        
        # 等待结果
        return await future
    
    async def _process_queue(self):
        """处理队列中的下一个请求"""
        async with self.lock:
            if self.queue and self.active_requests < self.max_concurrent:
                request_func, args, kwargs, future = self.queue.popleft()
                self.active_requests += 1
                
                logger.debug(f"[Fire-Eye QQ] Processing queued request (active: {self.active_requests}, queue: {len(self.queue)})")
                
                # 在后台执行
                asyncio.create_task(self._execute_request(
                    request_func, args, kwargs, future
                ))
    
    async def _execute_request(self, request_func, args, kwargs, future):
        """执行队列中的请求"""
        try:
            result = await request_func(*args, **kwargs)
            future.set_result(result)
        except Exception as e:
            logger.error(f"[Fire-Eye QQ] Queued request error: {e}")
            future.set_exception(e)
        finally:
            self.active_requests -= 1
            await self._process_queue()
    
    def get_queue_status(self) -> dict:
        """获取队列状态"""
        return {
            'active_requests': self.active_requests,
            'queue_size': len(self.queue),
            'max_concurrent': self.max_concurrent,
            'max_queue_size': self.max_queue_size
        }
