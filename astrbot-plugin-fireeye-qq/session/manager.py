"""
会话管理器
管理用户会话和对话上下文
"""

import uuid
import time
from typing import Dict, Optional
from loguru import logger


class SessionManager:
    """会话管理器"""
    
    def __init__(self, session_ttl: int = 1800):
        """
        初始化会话管理器
        
        Args:
            session_ttl: 会话过期时间（秒），默认30分钟
        """
        self.session_ttl = session_ttl
        self._sessions: Dict[str, Dict] = {}  # user_id -> session_data
        
        logger.info(f"[Fire-Eye QQ] SessionManager initialized with TTL={session_ttl}s")
    
    def create_session(self, user_id: str, platform: str = "qq") -> str:
        """
        为用户创建新会话
        
        Args:
            user_id: 用户 ID
            platform: 平台类型
            
        Returns:
            会话 ID
        """
        session_id = str(uuid.uuid4())
        
        self._sessions[user_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'platform': platform,
            'created_at': time.time(),
            'last_activity': time.time(),
            'conversation_history': []
        }
        
        logger.info(f"[Fire-Eye QQ] Created session for user {user_id}: {session_id}")
        
        return session_id
    
    def get_session(self, user_id: str) -> Optional[str]:
        """
        获取用户的会话 ID
        
        Args:
            user_id: 用户 ID
            
        Returns:
            会话 ID，如果会话已过期或不存在则返回 None
        """
        if user_id not in self._sessions:
            return None
        
        session_data = self._sessions[user_id]
        
        # 检查会话是否过期
        current_time = time.time()
        if current_time - session_data['last_activity'] > self.session_ttl:
            logger.info(f"[Fire-Eye QQ] Session expired for user {user_id}")
            del self._sessions[user_id]
            return None
        
        return session_data['session_id']
    
    def update_activity(self, user_id: str):
        """
        更新用户会话的活动时间
        
        Args:
            user_id: 用户 ID
        """
        if user_id in self._sessions:
            self._sessions[user_id]['last_activity'] = time.time()
            logger.debug(f"[Fire-Eye QQ] Updated activity for user {user_id}")
    
    def add_conversation_turn(
        self,
        user_id: str,
        user_message: str,
        bot_response: str,
        query_results: Optional[Dict] = None
    ):
        """
        添加对话记录
        
        Args:
            user_id: 用户 ID
            user_message: 用户消息
            bot_response: 机器人响应
            query_results: 查询结果（可选）
        """
        if user_id not in self._sessions:
            return
        
        turn = {
            'timestamp': time.time(),
            'user_message': user_message,
            'bot_response': bot_response,
            'query_results': query_results
        }
        
        self._sessions[user_id]['conversation_history'].append(turn)
        
        # 只保留最近的 10 条对话
        if len(self._sessions[user_id]['conversation_history']) > 10:
            self._sessions[user_id]['conversation_history'] = \
                self._sessions[user_id]['conversation_history'][-10:]
        
        logger.debug(f"[Fire-Eye QQ] Added conversation turn for user {user_id}")
    
    def get_conversation_history(self, user_id: str) -> list:
        """
        获取用户的对话历史
        
        Args:
            user_id: 用户 ID
            
        Returns:
            对话历史列表
        """
        if user_id not in self._sessions:
            return []
        
        return self._sessions[user_id]['conversation_history']
    
    def clear_session(self, user_id: str):
        """
        清除用户会话
        
        Args:
            user_id: 用户 ID
        """
        if user_id in self._sessions:
            del self._sessions[user_id]
            logger.info(f"[Fire-Eye QQ] Cleared session for user {user_id}")
    
    def cleanup_expired_sessions(self):
        """清理过期的会话"""
        current_time = time.time()
        expired_users = []
        
        for user_id, session_data in self._sessions.items():
            if current_time - session_data['last_activity'] > self.session_ttl:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self._sessions[user_id]
            logger.info(f"[Fire-Eye QQ] Cleaned up expired session for user {user_id}")
        
        if expired_users:
            logger.info(f"[Fire-Eye QQ] Cleaned up {len(expired_users)} expired sessions")
