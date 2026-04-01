"""
会话管理器
管理用户会话和上下文
"""

import uuid
from typing import Dict, Optional
from datetime import datetime, timedelta
from astrbot.core import logger


class SessionManager:
    """会话管理器"""
    
    def __init__(self, session_ttl: int = 1800):
        """
        初始化会话管理器
        
        Args:
            session_ttl: 会话超时时间（秒），默认30分钟
        """
        self.session_ttl = session_ttl
        self.sessions: Dict[str, dict] = {}
        
        logger.info(f"[SessionManager] Initialized with TTL={session_ttl}s")
    
    def get_or_create_session(self, user_id: str) -> str:
        """
        获取或创建会话
        
        Args:
            user_id: 用户 ID
            
        Returns:
            会话 ID
        """
        # 检查是否已有会话
        if user_id in self.sessions:
            session = self.sessions[user_id]
            
            # 检查是否过期
            if datetime.now() < session["expires_at"]:
                # 更新过期时间
                session["expires_at"] = datetime.now() + timedelta(seconds=self.session_ttl)
                logger.debug(f"[SessionManager] Reusing session for user {user_id}")
                return session["session_id"]
            else:
                # 会话已过期，删除
                logger.info(f"[SessionManager] Session expired for user {user_id}")
                del self.sessions[user_id]
        
        # 创建新会话
        session_id = str(uuid.uuid4())
        self.sessions[user_id] = {
            "session_id": session_id,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(seconds=self.session_ttl),
            "context": {}
        }
        
        logger.info(f"[SessionManager] Created new session for user {user_id}: {session_id}")
        return session_id
    
    def get_session(self, user_id: str) -> Optional[str]:
        """
        获取会话 ID（不创建新会话）
        
        Args:
            user_id: 用户 ID
            
        Returns:
            会话 ID 或 None
        """
        if user_id in self.sessions:
            session = self.sessions[user_id]
            if datetime.now() < session["expires_at"]:
                return session["session_id"]
            else:
                del self.sessions[user_id]
        return None
    
    def update_context(self, user_id: str, key: str, value: any):
        """
        更新会话上下文
        
        Args:
            user_id: 用户 ID
            key: 上下文键
            value: 上下文值
        """
        if user_id in self.sessions:
            self.sessions[user_id]["context"][key] = value
            logger.debug(f"[SessionManager] Updated context for user {user_id}: {key}")
    
    def get_context(self, user_id: str, key: str, default=None):
        """
        获取会话上下文
        
        Args:
            user_id: 用户 ID
            key: 上下文键
            default: 默认值
            
        Returns:
            上下文值
        """
        if user_id in self.sessions:
            return self.sessions[user_id]["context"].get(key, default)
        return default
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        expired_users = [
            user_id for user_id, session in self.sessions.items()
            if now >= session["expires_at"]
        ]
        
        for user_id in expired_users:
            del self.sessions[user_id]
            logger.info(f"[SessionManager] Cleaned up expired session for user {user_id}")
        
        if expired_users:
            logger.info(f"[SessionManager] Cleaned up {len(expired_users)} expired sessions")
