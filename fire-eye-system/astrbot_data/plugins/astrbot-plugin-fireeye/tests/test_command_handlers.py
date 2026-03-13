"""
Command Handlers 单元测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from commands.query_handler import QueryHandler
from commands.stats_handler import StatsHandler
from commands.help_handler import HelpHandler


class TestQueryHandler:
    """查询命令处理器测试"""
    
    @pytest.fixture
    def handler(self):
        """创建查询处理器实例"""
        api_client = MagicMock()
        session_manager = MagicMock()
        request_queue = MagicMock()
        formatter = MagicMock()
        
        return QueryHandler(
            api_client=api_client,
            session_manager=session_manager,
            request_queue=request_queue,
            formatter=formatter
        )
    
    def test_extract_query_text_string(self, handler):
        """测试从字符串提取查询文本"""
        message = "/火瞳查询 3.21火灾事故"
        result = handler._extract_query_text(message)
        assert result == "3.21火灾事故"
    
    def test_extract_query_text_alias(self, handler):
        """测试从别名提取查询文本"""
        message = "/ht查询 测试查询"
        result = handler._extract_query_text(message)
        assert result == "测试查询"
    
    @pytest.mark.asyncio
    async def test_handle_empty_query(self, handler):
        """测试处理空查询"""
        result = await handler.handle("/火瞳查询", "user-123")
        assert "请提供查询内容" in result


class TestStatsHandler:
    """统计命令处理器测试"""
    
    @pytest.fixture
    def handler(self):
        """创建统计处理器实例"""
        api_client = MagicMock()
        api_client.get_stats = AsyncMock(return_value={
            "success": True,
            "data": {"total_fire_events": 100}
        })
        
        formatter = MagicMock()
        formatter.format_statistics = MagicMock(return_value="统计信息")
        
        return StatsHandler(
            api_client=api_client,
            formatter=formatter
        )
    
    def test_extract_stat_type_default(self, handler):
        """测试提取默认统计类型"""
        message = "/火瞳统计"
        result = handler._extract_stat_type(message)
        assert result == "all"
    
    def test_extract_stat_type_hazard(self, handler):
        """测试提取隐患统计类型"""
        message = "/火瞳统计 隐患"
        result = handler._extract_stat_type(message)
        assert result == "hazard"
    
    def test_extract_stat_type_consequence(self, handler):
        """测试提取后果统计类型"""
        message = "/ht统计 后果"
        result = handler._extract_stat_type(message)
        assert result == "consequence"
    
    @pytest.mark.asyncio
    async def test_handle_success(self, handler):
        """测试处理成功"""
        result = await handler.handle("/火瞳统计", "user-123")
        assert result == "统计信息"
        handler.api_client.get_stats.assert_called_once()


class TestHelpHandler:
    """帮助命令处理器测试"""
    
    @pytest.fixture
    def handler(self):
        """创建帮助处理器实例"""
        formatter = MagicMock()
        formatter.format_help = MagicMock(return_value="帮助信息")
        
        return HelpHandler(formatter=formatter)
    
    @pytest.mark.asyncio
    async def test_handle(self, handler):
        """测试处理帮助命令"""
        result = await handler.handle("/火瞳帮助", "user-123")
        assert result == "帮助信息"
        handler.formatter.format_help.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
