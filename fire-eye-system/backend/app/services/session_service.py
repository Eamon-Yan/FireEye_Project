"""
会话管理服务
用于管理 AstrBot 用户的对话上下文和历史记录
"""

import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime

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
            
            # 存储到 Redis
            key = self._get_key(session_id)
            await self.redis.set(
                key,
                session_data.model_dump_json(),
                expire=SESSION_TTL
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
            data = await self.redis.get(key)
            
            if not data:
                logger.debug(f"Session {session_id} not found")
                return None
            
            # Parse JSON data - data is already a dict from RedisClient.get()
            if isinstance(data, str):
                session_data = SessionData.model_validate_json(data)
            else:
                session_data = SessionData.model_validate(data)
            
            # 更新最后活动时间
            session_data.last_activity = datetime.now()
            
            # 刷新 TTL
            await self.redis.expire(key, SESSION_TTL)
            
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
            await self.redis.set(
                key,
                session_data.model_dump_json(),
                expire=SESSION_TTL
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
            result = await self.redis.delete(key)
            
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
