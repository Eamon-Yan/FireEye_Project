"""
异步任务轮询器
用于轮询长时间运行的任务状态
"""

import asyncio
from typing import Callable, Optional
from astrbot.core import logger


class TaskPoller:
    """任务轮询器"""
    
    def __init__(self, api_client):
        """
        初始化轮询器
        
        Args:
            api_client: API 客户端实例
        """
        self.api_client = api_client
        self.polling_interval = 3  # 轮询间隔（秒）
        self.max_polling_time = 300  # 最大轮询时间（5分钟）
    
    async def poll_task(
        self,
        task_id: str,
        on_complete: Callable,
        on_failed: Callable,
        on_progress: Optional[Callable] = None
    ):
        """
        轮询任务状态直到完成或超时
        
        Args:
            task_id: 任务 ID
            on_complete: 完成时的回调函数
            on_failed: 失败时的回调函数
            on_progress: 进度更新的回调函数（可选）
        """
        logger.info(f"[TaskPoller] Starting to poll task: {task_id}")
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # 检查超时
            if elapsed > self.max_polling_time:
                logger.warning(f"[TaskPoller] Task {task_id} timeout after {elapsed:.1f}s")
                await on_failed(
                    f"任务处理超时（5分钟）\n任务ID: {task_id}\n请稍后使用任务ID手动查询状态"
                )
                return
            
            # 获取任务状态
            try:
                status_data = await self.api_client.get_task_status(task_id)
                
                if not status_data:
                    logger.error(f"[TaskPoller] Failed to get status for task {task_id}")
                    await asyncio.sleep(self.polling_interval)
                    continue
                
                data = status_data.get("data", {})
                status = data.get("status", "unknown")
                
                logger.debug(f"[TaskPoller] Task {task_id} status: {status}")
                
                if status == "completed":
                    logger.info(f"[TaskPoller] Task {task_id} completed")
                    result = data.get("result", {})
                    await on_complete(result)
                    return
                    
                elif status == "failed":
                    logger.error(f"[TaskPoller] Task {task_id} failed")
                    error = data.get("error", "未知错误")
                    await on_failed(f"任务处理失败: {error}")
                    return
                    
                elif status in ["pending", "processing"]:
                    # 可选的进度回调
                    if on_progress:
                        progress = data.get("progress", 0)
                        estimated_time = data.get("estimated_time_remaining")
                        await on_progress(progress, estimated_time)
                
            except Exception as e:
                logger.error(f"[TaskPoller] Polling error: {e}")
            
            # 等待下次轮询
            await asyncio.sleep(self.polling_interval)
