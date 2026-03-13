"""
事件链相关数据模型
"""

from datetime import datetime
from typing import List, Optional
from pydantic import Field, field_validator
from enum import Enum

from .base import BaseSchema, TimestampMixin


class RelationType(str, Enum):
    """关系类型枚举"""
    CAUSES = "导致"
    PROMOTES = "促进"
    PREVENTS = "阻止"
    TRIGGERS = "触发"
    ACCELERATES = "加速"


class EventChain(BaseSchema, TimestampMixin):
    """事件链模型"""
    source: str = Field(description="源事件", min_length=1, max_length=500)
    relation: RelationType = Field(description="关系类型")
    target: str = Field(description="目标事件", min_length=1, max_length=500)
    confidence: float = Field(description="置信度", ge=0.0, le=1.0)
    timestamp: Optional[datetime] = Field(default=None, description="事件时间戳")
    context: str = Field(description="上下文信息", max_length=1000)
    
    @field_validator("source", "target")
    @classmethod
    def validate_event_text(cls, v):
        """验证事件文本"""
        if not v or v.isspace():
            raise ValueError("事件描述不能为空")
        return v.strip()
    
    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        """验证上下文"""
        return v.strip() if v else ""


class EventChainCreate(BaseSchema):
    """创建事件链请求"""
    source: str = Field(description="源事件", min_length=1, max_length=500)
    relation: RelationType = Field(description="关系类型")
    target: str = Field(description="目标事件", min_length=1, max_length=500)
    confidence: float = Field(description="置信度", ge=0.0, le=1.0)
    timestamp: Optional[datetime] = Field(default=None, description="事件时间戳")
    context: Optional[str] = Field(default="", description="上下文信息", max_length=1000)


class EventChainUpdate(BaseSchema):
    """更新事件链请求"""
    source: Optional[str] = Field(default=None, description="源事件", min_length=1, max_length=500)
    relation: Optional[RelationType] = Field(default=None, description="关系类型")
    target: Optional[str] = Field(default=None, description="目标事件", min_length=1, max_length=500)
    confidence: Optional[float] = Field(default=None, description="置信度", ge=0.0, le=1.0)
    timestamp: Optional[datetime] = Field(default=None, description="事件时间戳")
    context: Optional[str] = Field(default=None, description="上下文信息", max_length=1000)


class EventChainResponse(BaseSchema):
    """事件链响应"""
    id: str = Field(description="事件链ID")
    source: str = Field(description="源事件")
    relation: RelationType = Field(description="关系类型")
    target: str = Field(description="目标事件")
    confidence: float = Field(description="置信度")
    timestamp: Optional[datetime] = Field(description="事件时间戳")
    context: str = Field(description="上下文信息")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class EventChainBatch(BaseSchema):
    """批量事件链"""
    chains: List[EventChainCreate] = Field(description="事件链列表", min_length=1, max_length=100)
    
    @field_validator("chains")
    @classmethod
    def validate_chains(cls, v):
        """验证事件链列表"""
        if not v:
            raise ValueError("事件链列表不能为空")
        return v


class EventChainQuery(BaseSchema):
    """事件链查询参数"""
    source: Optional[str] = Field(default=None, description="源事件关键词")
    target: Optional[str] = Field(default=None, description="目标事件关键词")
    relation: Optional[RelationType] = Field(default=None, description="关系类型")
    min_confidence: Optional[float] = Field(default=None, description="最小置信度", ge=0.0, le=1.0)
    max_confidence: Optional[float] = Field(default=None, description="最大置信度", ge=0.0, le=1.0)
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")
    
    @field_validator("max_confidence")
    @classmethod
    def validate_confidence_range(cls, v, info):
        """验证置信度范围"""
        if info.data:
            min_conf = info.data.get("min_confidence")
            if min_conf is not None and v is not None and v < min_conf:
                raise ValueError("最大置信度不能小于最小置信度")
        return v
    
    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v, info):
        """验证时间范围"""
        if info.data:
            start_time = info.data.get("start_time")
            if start_time is not None and v is not None and v < start_time:
                raise ValueError("结束时间不能早于开始时间")
        return v


class EventChainStatistics(BaseSchema):
    """事件链统计信息"""
    total_chains: int = Field(description="总事件链数量")
    relation_counts: dict = Field(description="关系类型统计")
    avg_confidence: float = Field(description="平均置信度")
    confidence_distribution: dict = Field(description="置信度分布")
    time_range: dict = Field(description="时间范围")


class EventChainValidation(BaseSchema):
    """事件链验证结果"""
    is_valid: bool = Field(description="是否有效")
    validation_errors: List[str] = Field(default_factory=list, description="验证错误")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    confidence_score: float = Field(description="验证置信度", ge=0.0, le=1.0)