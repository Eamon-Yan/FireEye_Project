"""
API Client 单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientSession, ClientError
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.client import APIClient


class TestAPIClient:
    """API 客户端测试"""
    
    @pytest.fixture
    def api_client(self):
        """创建 API 客户端实例"""
        return APIClient(
            api_url="http://localhost:8000",
            api_key="test-key",
            timeout=30,
            retries=3
        )
    
    def test_init(self, api_client):
        """测试初始化"""
        assert api_client.api_url == "http://localhost:8000"
        assert api_client.api_key == "test-key"
        assert api_client.timeout == 30
        assert api_client.retries == 3
    
    @pytest.mark.asyncio
    async def test_query_success(self, api_client):
        """测试查询成功"""
        mock_response = {
            "success": True,
            "data": {
                "results": [{"type": "FireEvent", "description": "测试事件"}],
                "total_count": 1
            }
        }
        
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await api_client.query("测试查询", "session-123")
            
            assert result["success"] is True
            assert result["data"]["total_count"] == 1
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_success(self, api_client):
        """测试分析成功"""
        mock_response = {
            "success": True,
            "data": {
                "task_id": "task-123",
                "estimated_time": 60
            }
        }
        
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await api_client.analyze("测试文本")
            
            assert result["data"]["task_id"] == "task-123"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_task_status_success(self, api_client):
        """测试获取任务状态成功"""
        mock_response = {
            "success": True,
            "data": {
                "task_id": "task-123",
                "status": "completed",
                "progress": 100
            }
        }
        
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await api_client.get_task_status("task-123")
            
            assert result["data"]["status"] == "completed"
            assert result["data"]["progress"] == 100
    
    @pytest.mark.asyncio
    async def test_get_stats_success(self, api_client):
        """测试获取统计信息成功"""
        mock_response = {
            "success": True,
            "data": {
                "total_fire_events": 100,
                "total_hazards": 50
            }
        }
        
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            
            result = await api_client.get_stats()
            
            assert result["data"]["total_fire_events"] == 100
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self, api_client):
        """测试失败重试"""
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            # 前两次失败，第三次成功
            mock_request.side_effect = [
                Exception("Network error"),
                Exception("Network error"),
                {"success": True, "data": {}}
            ]
            
            result = await api_client.query("测试")
            
            assert result["success"] is True
            assert mock_request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_close(self, api_client):
        """测试关闭连接"""
        api_client.session = AsyncMock()
        await api_client.close()
        api_client.session.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
