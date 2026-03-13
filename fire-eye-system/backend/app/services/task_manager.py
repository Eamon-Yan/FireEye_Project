"""任务管理服务 - 用于管理异步任务的生命周期"""
import json
import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from app.db.redis_client import redis_client

logger = logging.getLogger(__name__)
TASK_TTL = 3600


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TaskType(str, Enum):
    """任务类型"""
    ANALYZE = "analyze"
    UPLOAD = "upload"


class TaskResult(BaseModel):
    """任务结果"""
    event_chains: List[Dict[str, Any]] = Field(default_factory=list)
    entities_count: int = Field(default=0)
    relationships_count: int = Field(default=0)
    document_id: Optional[str] = Field(default=None)
    message: Optional[str] = Field(default=None)


class Task(BaseModel):
    """任务模型"""
    task_id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_time: Optional[int] = None
    result: Optional[TaskResult] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

from app.db.redis_client import redis_client
from app.schemas.chat import SessionData, ConversationTurn

logger = logging.getLogger(__name__)

# 会话 TTL (30 分钟)
SESSION_TTL = 1800


class SessionService:
    """会话管理服务"""
    
    def __init__(self):
        self.redis = redis_client
        self.key_prefix = "session:"
    
    def _get_key(self, session_id: str) -> str:
        """获取 Redis key"""
        return f"{self.key_prefix}{session_id}"
    
    async def create_session(
        self,
        user_id: str,
        platform: str = "unknown"
    ) -> str:
        """
        创建新会话
        
        Args:
            user_id: 用户 ID
            platform: 平台类型
            
        Returns:
            会话 ID
        """
        try:
            # 生成会话 ID
            session_id = f"sess_{uuid.uuid4().hex[:12]}"
            
            # 创建会话数据
            now = datetime.now()
            session_data = SessionData(
                session_id=session_id,
                user_id=user_id,
                platform=platform,
                created_at=now,
                last_activity=now
            )
            
            # 存储到 Redis（直接使用 redis 实例）
            key = self._get_key(session_id)
            await self.redis.redis.setex(
                key,
                SESSION_TTL,
                session_data.model_dump_json()
            )
            
            logger.info(f"Created session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        获取会话数据
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话数据，如果不存在则返回 None
        """
        try:
            key = self._get_key(session_id)
            data = await self.redis.redis.get(key)
            
            if not data:
                logger.debug(f"Session {session_id} not found")
                return None
            
            # 解析 JSON 数据
            session_data = SessionData.model_validate_json(data)
            
            # 更新最后活动时间
            session_data.last_activity = datetime.now()
            
            # 刷新 TTL
            await self.redis.redis.expire(key, SESSION_TTL)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update_session(
        self,
        session_id: str,
        turn: ConversationTurn
    ) -> bool:
        """
        更新会话（添加对话轮次）
        
        Args:
            session_id: 会话 ID
            turn: 对话轮次
            
        Returns:
            是否更新成功
        """
        try:
            # 获取现有会话
            session_data = await self.get_session(session_id)
            if not session_data:
                logger.warning(f"Cannot update non-existent session {session_id}")
                return False
            
            # 添加对话轮次
            session_data.conversation_history.append(turn)
            session_data.last_activity = datetime.now()
            
            # 限制历史记录长度（保留最近 10 轮）
            if len(session_data.conversation_history) > 10:
                session_data.conversation_history = session_data.conversation_history[-10:]
            
            # 保存到 Redis
            key = self._get_key(session_id)
            await self.redis.redis.setex(
                key,
                SESSION_TTL,
                session_data.model_dump_json()
            )
            
            logger.debug(f"Updated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            是否删除成功
        """
        try:
            key = self._get_key(session_id)
            result = await self.redis.redis.delete(key)
            
            if result:
                logger.info(f"Deleted session {session_id}")
            else:
                logger.debug(f"Session {session_id} not found for deletion")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """
        清理过期会话（Redis 自动处理 TTL，此方法用于手动清理）
        
        Returns:
            清理的会话数量
        """
        try:
            # Redis 会自动清理过期的 key，这里只是记录日志
            logger.info("Session cleanup triggered (Redis handles TTL automatically)")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
            return 0


# 创建全局实例
session_service = SessionService()


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.redis = redis_client
    
    def _get_task_key(self, task_id: str) -> str:
        return f"task:{task_id}"
    
    async def create_task(self, task_type: TaskType, metadata: Optional[Dict[str, Any]] = None,
                         estimated_time: Optional[int] = None) -> Task:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        task = Task(task_id=task_id, task_type=task_type, status=TaskStatus.PENDING,
                   progress=0, estimated_time=estimated_time, metadata=metadata or {})
        await self._save_task(task)
        logger.info(f"Created task {task_id} of type {task_type}")
        return task
    
    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        task_key = self._get_task_key(task_id)
        task_data = await self.redis.get(task_key)
        if not task_data:
            logger.warning(f"Task {task_id} not found")
            return None
        # RedisClient.get() already returns a dict, no need to parse JSON
        if isinstance(task_data, str):
            task_dict = json.loads(task_data)
        else:
            task_dict = task_data
            task_dict = task_data
        return Task(**task_dict)
    
    async def update_task_progress(self, task_id: str, progress: int,
                                  status: Optional[TaskStatus] = None) -> bool:
        """更新任务进度"""
        task = await self.get_task_status(task_id)
        if not task:
            logger.error(f"Cannot update progress: task {task_id} not found")
            return False
        task.progress = max(0, min(100, progress))
        task.updated_at = datetime.utcnow()
        if status:
            task.status = status
        await self._save_task(task)
        logger.debug(f"Updated task {task_id} progress to {progress}%")
        return True
    
    async def complete_task(self, task_id: str, result: TaskResult) -> bool:
        """完成任务"""
        task = await self.get_task_status(task_id)
        if not task:
            logger.error(f"Cannot complete: task {task_id} not found")
            return False
        task.status = TaskStatus.COMPLETED
        task.progress = 100
        task.result = result
        task.updated_at = datetime.utcnow()
        await self._save_task(task)
        logger.info(f"Task {task_id} completed successfully")
        return True
    
    async def fail_task(self, task_id: str, error: str) -> bool:
        """标记任务失败"""
        task = await self.get_task_status(task_id)
        if not task:
            logger.error(f"Cannot fail: task {task_id} not found")
            return False
        task.status = TaskStatus.FAILED
        task.error = error
        task.updated_at = datetime.utcnow()
        await self._save_task(task)
        logger.error(f"Task {task_id} failed: {error}")
        return True
    
    async def _save_task(self, task: Task) -> None:
        """保存任务到 Redis"""
        task_key = self._get_task_key(task.task_id)
        task_dict = task.model_dump(mode='json')
        task_data = json.dumps(task_dict, default=str)
        await self.redis.set(task_key, task_data, expire=TASK_TTL)
    
    async def cleanup_expired_tasks(self) -> int:
        """清理过期任务"""
        logger.info("Task cleanup triggered (Redis handles TTL automatically)")
        return 0


task_manager = TaskManager()
