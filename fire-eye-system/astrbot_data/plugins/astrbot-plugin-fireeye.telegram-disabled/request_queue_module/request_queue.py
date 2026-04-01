"""
请求队列
限制并发请求数量，防止后端过载
"""

import asyncio
from collections import deque
from typing import Callable, Any, Awaitable
from loguru import logger


class QueueFullError(Exception):
    """队列已满异常"""
    pass


class RequestQueue:
    """请求队列管理器"""
    
    def __init__(
        self,
        max_concurrent: int = 5,
        max_queue_size: int = 20
    ):
        """
        初始化请求队列
        
        Args:
            max_concurrent: 最大并发请求数
            max_queue_size: 队列最大长度
        """
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        
        self.queue = deque()
        self.active_count = 0
        self.lock = asyncio.Lock()
        
        logger.info(
            f"RequestQueue initialized: "
            f"max_concurrent={max_concurrent}, "
            f"max_queue_size={max_queue_size}"
        )
    
    async def enqueue(
        self,
        request_func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        将请求加入队列并执行
        
        Args:
            request_func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            请求函数的返回值
            
        Raises:
            QueueFullError: 队列已满
        """
        async with self.lock:
            # 检查是否可以立即执行
            if self.active_count < self.max_concurrent:
                self.active_count += 1
                logger.debug(
                    f"Executing request immediately "
                    f"(active: {self.active_count}/{self.max_concurrent})"
                )
                
                try:
                    result = await self._execute_request(
                        request_func, *args, **kwargs
                    )
                    return result
                finally:
                    async with self.lock:
                        self.active_count -= 1
                        # 处理队列中的下一个请求
                        await self._process_queue()
            
            # 需要排队
            if len(self.queue) >= self.max_queue_size:
                logger.warning("Request queue is full")
                raise QueueFullError(
                    f"请求队列已满（最大 {self.max_queue_size} 个请求）"
                )
            
            # 创建 Future 用于等待结果
            future = asyncio.Future()
            self.queue.append((request_func, args, kwargs, future))
            
            logger.info(
                f"Request queued "
                f"(queue size: {len(self.queue)}, "
                f"active: {self.active_count})"
            )
        
        # 等待请求被处理
        return await future
    
    async def _process_queue(self):
        """处理队列中的下一个请求"""
        if not self.queue or self.active_count >= self.max_concurrent:
            return
        
        # 从队列中取出请求
        request_func, args, kwargs, future = self.queue.popleft()
        self.active_count += 1
        
        logger.debug(
            f"Processing queued request "
            f"(queue size: {len(self.queue)}, "
            f"active: {self.active_count})"
        )
        
        # 异步执行请求
        asyncio.create_task(
            self._execute_and_complete(
                request_func, args, kwargs, future
            )
        )
    
    async def _execute_and_complete(
        self,
        request_func: Callable,
        args: tuple,
        kwargs: dict,
        future: asyncio.Future
    ):
        """执行请求并设置 Future 结果"""
        try:
            result = await self._execute_request(request_func, *args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            async with self.lock:
                self.active_count -= 1
                # 继续处理队列
                await self._process_queue()
    
    async def _execute_request(
        self,
        request_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行请求函数
        
        Args:
            request_func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数返回值
        """
        try:
            logger.debug(f"Executing request: {request_func.__name__}")
            result = await request_func(*args, **kwargs)
            logger.debug(f"Request completed: {request_func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Request failed: {request_func.__name__}: {e}")
            raise
    
    def get_status(self) -> dict:
        """
        获取队列状态
        
        Returns:
            队列状态信息
        """
        return {
            "active_count": self.active_count,
            "queue_size": len(self.queue),
            "max_concurrent": self.max_concurrent,
            "max_queue_size": self.max_queue_size
        }
