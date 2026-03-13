"""
Chat API 响应模型
用于 AstrBot 集成的聊天接口数据模型
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.schemas.event_chain import EventChain


# ==================== Session Models ====================

class ConversationTurn(BaseModel):
    """对话轮次模型"""
    timestamp: datetime = Field(..., description="对话时间戳")
    user_message: str = Field(..., description="用户消息")
    bot_response: str = Field(..., description="机器人响应")
    query_results: Optional[List[Dict[str, Any]]] = Field(
        None, 
        description="查询结果数据"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "timestamp": "2026-02-17T10:30:00Z",
                "user_message": "查询3.21火灾事故",
                "bot_response": "找到3个相关事故...",
                "query_results": [{"node_id": "node_123", "type": "FireEvent"}]
            }
        }
    }


class SessionData(BaseModel):
    """会话数据模型"""
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    platform: str = Field(
        ..., 
        description="平台类型: qq, telegram, wechat, dingtalk, feishu"
    )
    created_at: datetime = Field(..., description="创建时间")
    last_activity: datetime = Field(..., description="最后活动时间")
    conversation_history: List[ConversationTurn] = Field(
        default_factory=list,
        description="对话历史"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="上下文数据"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "sess_abc123",
                "user_id": "user_456",
                "platform": "qq",
                "created_at": "2026-02-17T10:00:00Z",
                "last_activity": "2026-02-17T10:30:00Z",
                "conversation_history": [],
                "context": {}
            }
        }
    }


# ==================== Task Models ====================

class Citation(BaseModel):
    """引用来源模型"""
    source_document: str = Field(..., description="源文档名称")
    page_number: Optional[int] = Field(None, description="页码")
    confidence: float = Field(..., description="置信度 (0-1)")
    text_snippet: Optional[str] = Field(None, description="文本片段")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "source_document": "调查报告-2023.pdf",
                "page_number": 12,
                "confidence": 0.92,
                "text_snippet": "电线老化导致短路..."
            }
        }
    }


class TaskResult(BaseModel):
    """任务结果模型"""
    event_chains: List[EventChain] = Field(
        default_factory=list,
        description="提取的事件链"
    )
    node_count: int = Field(..., description="节点数量")
    relationship_count: int = Field(..., description="关系数量")
    document_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="文档元数据"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="引用来源列表"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "event_chains": [],
                "node_count": 15,
                "relationship_count": 12,
                "document_metadata": {
                    "filename": "火灾调查报告.pdf",
                    "upload_time": "2026-02-17T10:30:00Z"
                },
                "citations": []
            }
        }
    }


class Task(BaseModel):
    """任务模型"""
    task_id: str = Field(..., description="任务ID")
    task_type: str = Field(
        ..., 
        description="任务类型: analyze, upload"
    )
    status: str = Field(
        ...,
        description="任务状态: pending, processing, completed, failed, timeout"
    )
    progress: int = Field(
        default=0,
        ge=0,
        le=100,
        description="进度百分比 (0-100)"
    )
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    estimated_time_remaining: Optional[int] = Field(
        None,
        description="预计剩余时间（秒）"
    )
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    session_id: Optional[str] = Field(None, description="关联的会话ID")
    document_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="文档元数据"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "task_id": "task_xyz789",
                "task_type": "analyze",
                "status": "processing",
                "progress": 65,
                "created_at": "2026-02-17T10:30:00Z",
                "started_at": "2026-02-17T10:30:05Z",
                "completed_at": None,
                "estimated_time_remaining": 15,
                "result": None,
                "error": None,
                "session_id": "sess_abc123",
                "document_metadata": None
            }
        }
    }


# ==================== Response Models ====================

class ChatQueryResponse(BaseModel):
    """查询响应模型"""
    status: str = Field(default="success", description="响应状态")
    message: str = Field(..., description="响应消息")
    data: Dict[str, Any] = Field(..., description="响应数据")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "查询成功，返回3个结果",
                "data": {
                    "results": [],
                    "total_count": 3,
                    "session_id": "sess_abc123"
                }
            }
        }
    }


class TaskResponse(BaseModel):
    """任务响应模型"""
    status: str = Field(default="success", description="响应状态")
    message: str = Field(..., description="响应消息")
    data: Dict[str, Any] = Field(
        ...,
        description="响应数据，包含 task_id, status 等"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "分析任务已创建",
                "data": {
                    "task_id": "task_xyz789",
                    "status": "pending",
                    "estimated_time": 45
                }
            }
        }
    }


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    status: str = Field(default="success", description="响应状态")
    data: Task = Field(..., description="任务数据")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "data": {
                    "task_id": "task_xyz789",
                    "task_type": "analyze",
                    "status": "completed",
                    "progress": 100,
                    "created_at": "2026-02-17T10:30:00Z",
                    "result": {}
                }
            }
        }
    }


class StatsResponse(BaseModel):
    """统计响应模型"""
    status: str = Field(default="success", description="响应状态")
    data: Dict[str, Any] = Field(..., description="统计数据")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "data": {
                    "total_fire_events": 156,
                    "total_hazards": 89,
                    "total_consequences": 67,
                    "hazard_distribution": {
                        "电气隐患": 45,
                        "消防设施缺陷": 23,
                        "违规操作": 21
                    },
                    "time_range": "30d",
                    "generated_at": "2026-02-17T10:30:00Z"
                }
            }
        }
    }


# ==================== Request Models ====================

class ChatQueryRequest(BaseModel):
    """查询请求模型"""
    query: str = Field(..., description="查询文本", min_length=1)
    session_id: Optional[str] = Field(None, description="会话ID（可选）")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "查询3.21火灾事故",
                "session_id": "sess_abc123"
            }
        }
    }


class ChatAnalyzeRequest(BaseModel):
    """文档分析请求模型"""
    text: str = Field(
        ...,
        description="文档文本内容",
        min_length=1,
        max_length=50000
    )
    session_id: Optional[str] = Field(None, description="会话ID（可选）")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "2023年3月21日，某商场发生火灾...",
                "session_id": "sess_abc123"
            }
        }
    }


class ChatStatsRequest(BaseModel):
    """统计查询请求模型"""
    stat_type: Optional[str] = Field(
        None,
        description="统计类型: total, hazards, consequences, chains"
    )
    time_range: Optional[str] = Field(
        None,
        description="时间范围: 7d, 30d, 1y"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "stat_type": "hazards",
                "time_range": "30d"
            }
        }
    }
