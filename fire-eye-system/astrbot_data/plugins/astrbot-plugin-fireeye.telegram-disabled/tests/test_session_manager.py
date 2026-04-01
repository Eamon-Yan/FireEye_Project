"""
Session Manager 单元测试
"""

import pytest
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from session.manager import SessionManager


class TestSessionManager:
    """会话管理器测试"""
    
    @pytest.fixture
    def manager(self):
        """创建会话管理器实例"""
        return SessionManager(ttl=1800)
    
    def test_init(self, manager):
        """测试初始化"""
        assert manager.ttl == 1800
        assert len(manager.sessions) == 0
    
    def test_create_session(self, manager):
        """测试创建会话"""
        session_id = manager.create_session("user-123", "qq")
        
        assert session_id is not None
        assert len(session_id) > 0
        assert "user-123" in manager.user_sessions
        assert manager.user_sessions["user-123"] == session_id
    
    def test_get_session(self, manager):
        """测试获取会话"""
        # 创建会话
        session_id = manager.create_session("user-123", "qq")
        
        # 获取会话
        retrieved_id = manager.get_session("user-123")
        assert retrieved_id == session_id
    
    def test_get_nonexistent_session(self, manager):
        """测试获取不存在的会话"""
        session_id = manager.get_session("nonexistent-user")
        assert session_id is None
    
    def test_update_activity(self, manager):
        """测试更新活动时间"""
        session_id = manager.create_session("user-123", "qq")
        
        # 获取初始时间
        initial_time = manager.sessions[session_id]["last_activity"]
        
        # 等待一小段时间
        time.sleep(0.1)
        
        # 更新活动时间
        manager.update_activity("user-123")
        
        # 验证时间已更新
        updated_time = manager.sessions[session_id]["last_activity"]
        assert updated_time > initial_time
    
    def test_session_expiration(self, manager):
        """测试会话过期"""
        # 创建一个TTL很短的管理器
        short_ttl_manager = SessionManager(ttl=1)
        
        session_id = short_ttl_manager.create_session("user-123", "qq")
        
        # 等待会话过期
        time.sleep(2)
        
        # 清理过期会话
        short_ttl_manager.cleanup_expired_sessions()
        
        # 验证会话已被删除
        assert "user-123" not in short_ttl_manager.user_sessions
        assert session_id not in short_ttl_manager.sessions
    
    def test_multiple_users(self, manager):
        """测试多用户会话"""
        session1 = manager.create_session("user-1", "qq")
        session2 = manager.create_session("user-2", "telegram")
        session3 = manager.create_session("user-3", "qq")
        
        assert session1 != session2 != session3
        assert manager.get_session("user-1") == session1
        assert manager.get_session("user-2") == session2
        assert manager.get_session("user-3") == session3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
