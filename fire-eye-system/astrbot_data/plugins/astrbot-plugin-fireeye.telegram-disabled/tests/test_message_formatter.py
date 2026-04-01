"""
Message Formatter 单元测试
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.formatter import MessageFormatter


class TestMessageFormatter:
    """消息格式化器测试"""
    
    @pytest.fixture
    def formatter(self):
        """创建消息格式化器实例"""
        return MessageFormatter(max_message_length=2000)
    
    def test_init(self, formatter):
        """测试初始化"""
        assert formatter.max_message_length == 2000
    
    def test_format_query_results_empty(self, formatter):
        """测试格式化空查询结果"""
        response = {
            "data": {
                "results": [],
                "total_count": 0
            }
        }
        
        result = formatter.format_query_results(response)
        assert "未找到相关信息" in result
    
    def test_format_query_results_with_data(self, formatter):
        """测试格式化有数据的查询结果"""
        response = {
            "data": {
                "results": [
                    {
                        "type": "FireEvent",
                        "description": "3.21火灾事故",
                        "properties": {
                            "date": "2024-03-21",
                            "location": "某工厂"
                        }
                    },
                    {
                        "type": "FireHazard",
                        "description": "电气线路老化"
                    }
                ],
                "total_count": 2
            }
        }
        
        result = formatter.format_query_results(response)
        assert "查询结果" in result
        assert "共 2 条" in result
        assert "3.21火灾事故" in result
        assert "电气线路老化" in result
    
    def test_format_task_created(self, formatter):
        """测试格式化任务创建响应"""
        response = {
            "data": {
                "task_id": "task-123",
                "estimated_time": 60
            }
        }
        
        result = formatter.format_task_created(response)
        assert "任务已创建" in result
        assert "task-123" in result
        assert "60" in result
    
    def test_format_task_progress(self, formatter):
        """测试格式化任务进度"""
        result = formatter.format_task_progress(50)
        assert "处理进度" in result
        assert "50%" in result
        assert "█" in result
        assert "░" in result
    
    def test_format_task_completed(self, formatter):
        """测试格式化任务完成"""
        task_data = {
            "result": {
                "event_chains": [
                    {"description": "事件链1"},
                    {"description": "事件链2"}
                ],
                "entities_count": 10,
                "relationships_count": 15
            }
        }
        
        result = formatter.format_task_completed(task_data)
        assert "分析完成" in result
        assert "事件链: 2 个" in result
        assert "实体: 10 个" in result
        assert "关系: 15 个" in result
    
    def test_format_statistics(self, formatter):
        """测试格式化统计信息"""
        response = {
            "data": {
                "total_fire_events": 100,
                "total_hazards": 50,
                "total_consequences": 30,
                "hazard_distribution": {
                    "电气火灾": 20,
                    "用火不慎": 15,
                    "吸烟": 10
                }
            }
        }
        
        result = formatter.format_statistics(response)
        assert "统计信息" in result
        assert "火灾事件: 100 起" in result
        assert "火灾隐患: 50 个" in result
        assert "电气火灾: 20" in result
    
    def test_format_error(self, formatter):
        """测试格式化错误消息"""
        result = formatter.format_error("测试错误")
        assert "错误" in result
        assert "测试错误" in result
    
    def test_format_help(self, formatter):
        """测试格式化帮助信息"""
        result = formatter.format_help()
        assert "帮助信息" in result
        assert "/火瞳查询" in result
        assert "/火瞳上传" in result
        assert "/火瞳统计" in result
        assert "/火瞳帮助" in result
    
    def test_truncate_message(self, formatter):
        """测试消息截断"""
        long_message = "A" * 3000
        result = formatter._truncate_message(long_message)
        
        assert len(result) <= 2000
        assert "消息过长，已截断" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
