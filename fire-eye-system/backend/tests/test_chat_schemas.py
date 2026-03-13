"""
Chat Schema 单元测试
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.chat import (
    ConversationTurn,
    SessionData,
    Citation,
    Task,
    TaskResult,
    ChatQueryResponse,
    TaskResponse,
    TaskStatusResponse,
    StatsResponse,
    ChatQueryRequest,
    ChatAnalyzeRequest,
    ChatStatsRequest
)


class TestConversationModels:
    """对话模型测试"""
    
    def test_conversation_turn_valid(self):
        """测试有效的对话轮次"""
        turn = ConversationTurn(
            timestamp=datetime.now(),
            user_message="查询火灾事故",
            bot_response="找到3个结果",
            query_results=[{"id": "1"}]
        )
        assert turn.user_message == "查询火灾事故"
        assert turn.bot_response == "找到3个结果"
    
    def test_session_data_valid(self):
        """测试有效的会话数据"""
        session = SessionData(
            session_id="sess_123",
            user_id="user_456",
            platform="qq",
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        assert session.session_id == "sess_123"
        assert session.platform == "qq"
        assert len(session.conversation_history) == 0
        assert len(session.context) == 0


class TestTaskModels:
    """任务模型测试"""
    
    def test_citation_valid(self):
        """测试有效的引用"""
        citation = Citation(
            source_document="report.pdf",
            page_number=12,
            confidence=0.92,
            text_snippet="电线老化..."
        )
        assert citation.source_document == "report.pdf"
        assert citation.confidence == 0.92
    
    def test_task_valid(self):
        """测试有效的任务"""
        task = Task(
            task_id="task_123",
            task_type="analyze",
            status="pending",
            progress=0,
            created_at=datetime.now()
        )
        assert task.task_id == "task_123"
        assert task.status == "pending"
        assert task.progress == 0
    
    def test_task_progress_validation(self):
        """测试任务进度验证"""
        # 有效进度
        task = Task(
            task_id="task_123",
            task_type="analyze",
            status="processing",
            progress=50,
            created_at=datetime.now()
        )
        assert task.progress == 50
        
        # 无效进度（超过100）
        with pytest.raises(ValidationError):
            Task(
                task_id="task_123",
                task_type="analyze",
                status="processing",
                progress=150,
                created_at=datetime.now()
            )
        
        # 无效进度（负数）
        with pytest.raises(ValidationError):
            Task(
                task_id="task_123",
                task_type="analyze",
                status="processing",
                progress=-10,
                created_at=datetime.now()
            )


class TestResponseModels:
    """响应模型测试"""
    
    def test_chat_query_response_valid(self):
        """测试有效的查询响应"""
        response = ChatQueryResponse(
            status="success",
            message="查询成功",
            data={"results": [], "total_count": 0}
        )
        assert response.status == "success"
        assert response.data["total_count"] == 0
    
    def test_task_response_valid(self):
        """测试有效的任务响应"""
        response = TaskResponse(
            status="success",
            message="任务已创建",
            data={"task_id": "task_123", "status": "pending"}
        )
        assert response.data["task_id"] == "task_123"
    
    def test_task_status_response_valid(self):
        """测试有效的任务状态响应"""
        task = Task(
            task_id="task_123",
            task_type="analyze",
            status="completed",
            progress=100,
            created_at=datetime.now()
        )
        response = TaskStatusResponse(
            status="success",
            data=task
        )
        assert response.data.task_id == "task_123"
        assert response.data.progress == 100
    
    def test_stats_response_valid(self):
        """测试有效的统计响应"""
        response = StatsResponse(
            status="success",
            data={
                "total_fire_events": 156,
                "total_hazards": 89
            }
        )
        assert response.data["total_fire_events"] == 156


class TestRequestModels:
    """请求模型测试"""
    
    def test_chat_query_request_valid(self):
        """测试有效的查询请求"""
        request = ChatQueryRequest(
            query="查询火灾事故",
            session_id="sess_123"
        )
        assert request.query == "查询火灾事故"
        assert request.session_id == "sess_123"
    
    def test_chat_query_request_empty_query(self):
        """测试空查询"""
        with pytest.raises(ValidationError):
            ChatQueryRequest(query="")
    
    def test_chat_analyze_request_valid(self):
        """测试有效的分析请求"""
        request = ChatAnalyzeRequest(
            text="火灾调查报告内容...",
            session_id="sess_123"
        )
        assert request.text == "火灾调查报告内容..."
    
    def test_chat_analyze_request_too_long(self):
        """测试文本过长"""
        long_text = "a" * 50001  # 超过 50000 字符限制
        with pytest.raises(ValidationError):
            ChatAnalyzeRequest(text=long_text)
    
    def test_chat_stats_request_valid(self):
        """测试有效的统计请求"""
        request = ChatStatsRequest(
            stat_type="hazards",
            time_range="30d"
        )
        assert request.stat_type == "hazards"
        assert request.time_range == "30d"
    
    def test_chat_stats_request_optional_fields(self):
        """测试可选字段"""
        request = ChatStatsRequest()
        assert request.stat_type is None
        assert request.time_range is None
