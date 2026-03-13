"""
认证中间件单元测试
"""

import pytest
from fastapi import HTTPException, status
from unittest.mock import patch, MagicMock

from app.api.auth import verify_api_key


class TestAuthMiddleware:
    """认证中间件测试类"""
    
    @pytest.mark.asyncio
    async def test_verify_api_key_missing(self):
        """测试缺少 API Key 的情况"""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(api_key=None)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "API Key required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        """测试无效 API Key 的情况"""
        with patch('app.api.auth.settings') as mock_settings:
            mock_settings.ASTRBOT_API_KEYS = ["valid-key-1", "valid-key-2"]
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(api_key="invalid-key")
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid API Key" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self):
        """测试有效 API Key 的情况"""
        with patch('app.api.auth.settings') as mock_settings:
            mock_settings.ASTRBOT_API_KEYS = ["valid-key-1", "valid-key-2"]
            
            result = await verify_api_key(api_key="valid-key-1")
            assert result == "valid-key-1"
    
    @pytest.mark.asyncio
    async def test_verify_api_key_no_config(self):
        """测试未配置 API Keys 的情况（开发模式）"""
        with patch('app.api.auth.settings') as mock_settings:
            mock_settings.ASTRBOT_API_KEYS = []
            
            # 开发模式下应该允许通过
            result = await verify_api_key(api_key="any-key")
            assert result == "any-key"
    
    @pytest.mark.asyncio
    async def test_verify_api_key_multiple_valid_keys(self):
        """测试多个有效 API Keys"""
        with patch('app.api.auth.settings') as mock_settings:
            mock_settings.ASTRBOT_API_KEYS = ["key1", "key2", "key3"]
            
            # 测试第一个 key
            result1 = await verify_api_key(api_key="key1")
            assert result1 == "key1"
            
            # 测试第二个 key
            result2 = await verify_api_key(api_key="key2")
            assert result2 == "key2"
            
            # 测试第三个 key
            result3 = await verify_api_key(api_key="key3")
            assert result3 == "key3"
