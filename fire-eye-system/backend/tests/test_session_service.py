"""
Session Service 单元测试
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.session_service import SessionService, SESSION_TTL
from app.schemas.chat import SessionData, ConversationTurn


@pytest.fixture
def mock_redis():
    """Mock Redis 客户端"""
    redis_mock = AsyncMock()
    redis_mock.redis = AsyncMock()  # 添加 redis 属性
    return redis_mock


@pytest.fixture
def session_service(mock_redis):
    """创建 SessionService 实例"""
    service = SessionService()
    service.redis = mock_redis
    return service


class TestSessionService:
    """Session Service 测试类"""
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_service, mock_redis):
        """测试创建会话"""
        # 配置 mock
        mock_redis.redis.setex = AsyncMock(return_value=True)
        
        # 创建会话
        session_id = await session_service.create_session(
            user_id="user_123",
            platform="qq"
        )
        
        # 验证
        assert session_id.startswith("sess_")
        assert len(session_id) == 17  # "sess_" + 12 字符
        
        # 验证 Redis 调用
        mock_redis.redis.setex.assert_called_once()
        call_args = mock_redis.redis.setex.call_args
        assert call_args[0][0] == f"session:{session_id}"
        assert call_args[0][1] == SESSION_TTL
    
    @pytest.mark.asyncio
    async def test_get_session_exists(self, session_service, mock_redis):
        """测试获取存在的会话"""
        # 准备测试数据
        session_data = SessionData(
            session_id="sess_test123",
            user_id="user_456",
            platform="telegram",
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        # 配置 mock
        mock_redis.redis.get = AsyncMock(return_value=session_data.model_dump_json())
        mock_redis.redis.expire = AsyncMock(return_value=True)
        
        # 获取会话
        result = await session_service.get_session("sess_test123")
        
        # 验证
        assert result is not None
        assert result.session_id == "sess_test123"
        assert result.user_id == "user_456"
        assert result.platform == "telegram"
        
        # 验证 Redis 调用
        mock_redis.redis.get.assert_called_once_with("session:sess_test123")
        mock_redis.redis.expire.assert_called_once_with("session:sess_test123", SESSION_TTL)
    
    @pytest.mark.asyncio
    async def test_get_session_not_exists(self, session_service, mock_redis):
        """测试获取不存在的会话"""
        # 配置 mock
        mock_redis.redis.get = AsyncMock(return_value=None)
        
        # 获取会话
        result = await session_service.get_session("sess_nonexistent")
        
        # 验证
        assert result is None
        mock_redis.redis.get.assert_called_once_with("session:sess_nonexistent")
    
    @pytest.mark.asyncio
    async def test_update_session(self, session_service, mock_redis):
        """测试更新会话"""
        # 准备测试数据
        session_data = SessionData(
            session_id="sess_test123",
            user_id="user_456",
            platform="qq",
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        # 配置 mock
        mock_redis.redis.get = AsyncMock(return_value=session_data.model_dump_json())
        mock_redis.redis.expire = AsyncMock(return_value=True)
        mock_redis.redis.setex = AsyncMock(return_value=True)
        
        # 创建对话轮次
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_message="查询火灾事故",
            bot_response="找到3个结果"
        )
        
        # 更新会话
        result = await session_service.update_session("sess_test123", turn)
        
        # 验证
        assert result is True
        mock_redis.redis.setex.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_session_not_exists(self, session_service, mock_redis):
        """测试更新不存在的会话"""
        # 配置 mock
        mock_redis.redis.get = AsyncMock(return_value=None)
        
        # 创建对话轮次
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_message="查询火灾事故",
            bot_response="找到3个结果"
        )
        
        # 更新会话
        result = await session_service.update_session("sess_nonexistent", turn)
        
        # 验证
        assert result is False
    
    @pytest.mark.asyncio
    async def test_update_session_history_limit(self, session_service, mock_redis):
        """测试会话历史记录限制（最多保留10轮）"""
        # 准备测试数据 - 已有10轮对话
        session_data = SessionData(
            session_id="sess_test123",
            user_id="user_456",
            platform="qq",
            created_at=datetime.now(),
            last_activity=datetime.now(),
            conversation_history=[
                ConversationTurn(
                    timestamp=datetime.now(),
                    user_message=f"消息{i}",
                    bot_response=f"响应{i}"
                ) for i in range(10)
            ]
        )
        
        # 配置 mock
        mock_redis.redis.get = AsyncMock(return_value=session_data.model_dump_json())
        mock_redis.redis.expire = AsyncMock(return_value=True)
        mock_redis.redis.setex = AsyncMock(return_value=True)
        
        # 添加第11轮对话
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_message="新消息",
            bot_response="新响应"
        )
        
        # 更新会话
        result = await session_service.update_session("sess_test123", turn)
        
        # 验证
        assert result is True
        
        # 验证保存的数据中历史记录被限制为10轮
        call_args = mock_redis.redis.setex.call_args
        saved_json = call_args[0][2]
        saved_data = SessionData.model_validate_json(saved_json)
        assert len(saved_data.conversation_history) == 10
        assert saved_data.conversation_history[-1].user_message == "新消息"
    
    @pytest.mark.asyncio
    async def test_delete_session(self, session_service, mock_redis):
        """测试删除会话"""
        # 配置 mock
        mock_redis.redis.delete = AsyncMock(return_value=1)
        
        # 删除会话
        result = await session_service.delete_session("sess_test123")
        
        # 验证
        assert result is True
        mock_redis.redis.delete.assert_called_once_with("session:sess_test123")
    
    @pytest.mark.asyncio
    async def test_delete_session_not_exists(self, session_service, mock_redis):
        """测试删除不存在的会话"""
        # 配置 mock
        mock_redis.redis.delete = AsyncMock(return_value=0)
        
        # 删除会话
        result = await session_service.delete_session("sess_nonexistent")
        
        # 验证
        assert result is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_service):
        """测试清理过期会话"""
        # 清理会话（Redis 自动处理 TTL）
        result = await session_service.cleanup_expired_sessions()
        
        # 验证
        assert result == 0  # 返回0因为 Redis 自动处理
    
    @pytest.mark.asyncio
    async def test_get_key(self, session_service):
        """测试 Redis key 生成"""
        key = session_service._get_key("sess_test123")
        assert key == "session:sess_test123"
