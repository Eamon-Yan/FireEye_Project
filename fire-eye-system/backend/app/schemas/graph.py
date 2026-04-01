"""
图数据相关模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import Field, field_validator
from enum import Enum

from .base import BaseSchema, TimestampMixin


class NodeType(str, Enum):
    """节点类型枚举"""
    FIRE_EVENT = "FireEvent"
    HAZARD = "Hazard"
    CONSEQUENCE = "Consequence"
    DOCUMENT = "Document"


class EventType(str, Enum):
    """火灾事件类型枚举"""
    CAUSE = "原因"
    PROCESS = "过程"
    RESULT = "结果"


class RiskLevel(str, Enum):
    """风险等级枚举"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    CRITICAL = "极高"


class ImpactLevel(str, Enum):
    """影响程度枚举"""
    MINOR = "轻微"
    MODERATE = "中等"
    MAJOR = "重大"
    SEVERE = "严重"
    CATASTROPHIC = "灾难性"


class Node(BaseSchema, TimestampMixin):
    """图节点模型"""
    id: str = Field(description="节点唯一标识符")
    labels: List[str] = Field(description="节点标签", min_length=1)
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")
    
    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        """验证节点ID"""
        if not v or v.isspace():
            raise ValueError("节点ID不能为空")
        return v.strip()
    
    @field_validator("labels")
    @classmethod
    def validate_labels(cls, v):
        """验证节点标签"""
        if not v:
            raise ValueError("节点标签不能为空")
        return [label.strip() for label in v if label.strip()]


class FireEventNode(BaseSchema, TimestampMixin):
    """火灾事件节点"""
    id: str = Field(description="事件ID")
    event_type: EventType = Field(description="事件类型")
    description: str = Field(description="事件描述", max_length=1000)
    standard_term: str = Field(description="标准术语", max_length=200)
    category: str = Field(description="事件分类", max_length=100)
    severity_level: int = Field(description="严重程度", ge=1, le=10)
    frequency: int = Field(description="发生频率", ge=0)
    
    @field_validator("description", "standard_term")
    @classmethod
    def validate_text_fields(cls, v):
        """验证文本字段"""
        if not v or v.isspace():
            raise ValueError("文本字段不能为空")
        return v.strip()


class HazardNode(BaseSchema, TimestampMixin):
    """隐患节点"""
    id: str = Field(description="隐患ID")
    description: str = Field(description="隐患描述", max_length=1000)
    standard_term: str = Field(description="标准术语", max_length=200)
    risk_level: RiskLevel = Field(description="风险等级")
    location: str = Field(description="位置信息", max_length=200)
    
    @field_validator("description", "standard_term", "location")
    @classmethod
    def validate_text_fields(cls, v):
        """验证文本字段"""
        if not v or v.isspace():
            raise ValueError("文本字段不能为空")
        return v.strip()


class ConsequenceNode(BaseSchema, TimestampMixin):
    """后果节点"""
    id: str = Field(description="后果ID")
    description: str = Field(description="后果描述", max_length=1000)
    standard_term: str = Field(description="标准术语", max_length=200)
    impact_level: ImpactLevel = Field(description="影响程度")
    affected_area: str = Field(description="影响区域", max_length=200)
    
    @field_validator("description", "standard_term", "affected_area")
    @classmethod
    def validate_text_fields(cls, v):
        """验证文本字段"""
        if not v or v.isspace():
            raise ValueError("文本字段不能为空")
        return v.strip()


class RelationshipType(str, Enum):
    """关系类型枚举"""
    CAUSES = "CAUSES"
    LEADS_TO = "LEADS_TO"
    RESULTS_IN = "RESULTS_IN"


class Relationship(BaseSchema, TimestampMixin):
    """图关系模型"""
    id: str = Field(description="关系唯一标识符")
    type: RelationshipType = Field(description="关系类型")
    start_node: str = Field(description="起始节点ID")
    end_node: str = Field(description="结束节点ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系属性")
    weight: float = Field(default=1.0, description="关系权重", ge=0.0)
    
    @field_validator("id", "start_node", "end_node")
    @classmethod
    def validate_ids(cls, v):
        """验证ID字段"""
        if not v or v.isspace():
            raise ValueError("ID字段不能为空")
        return v.strip()


class CausalRelation(BaseSchema, TimestampMixin):
    """因果关系"""
    id: str = Field(description="关系ID")
    relation_type: str = Field(description="关系类型", max_length=50)
    source_event: str = Field(description="源事件ID")
    target_event: str = Field(description="目标事件ID")
    confidence: float = Field(description="置信度", ge=0.0, le=1.0)
    time_delay: Optional[int] = Field(default=None, description="时间延迟(秒)")
    conditions: List[str] = Field(default_factory=list, description="触发条件")


class Path(BaseSchema):
    """图路径模型"""
    nodes: List[Node] = Field(description="路径节点")
    relationships: List[Relationship] = Field(description="路径关系")
    length: int = Field(description="路径长度", ge=0)
    total_weight: float = Field(description="总权重", ge=0.0)
    
    @field_validator("length")
    @classmethod
    def validate_length(cls, v, info):
        """验证路径长度"""
        nodes = info.data.get("nodes", [])
        relationships = info.data.get("relationships", [])
        expected_length = len(relationships)
        if v != expected_length:
            raise ValueError(f"路径长度不匹配: 期望 {expected_length}, 实际 {v}")
        return v


class GraphQuery(BaseSchema):
    """图查询参数"""
    cypher_query: str = Field(description="Cypher查询语句", min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="查询参数")
    limit: Optional[int] = Field(default=100, description="结果限制", ge=1, le=1000)
    
    @field_validator("cypher_query")
    @classmethod
    def validate_cypher(cls, v):
        """验证Cypher查询"""
        if not v or v.isspace():
            raise ValueError("Cypher查询不能为空")
        # 基本安全检查
        dangerous_keywords = ["DELETE", "DROP", "CREATE CONSTRAINT", "DROP CONSTRAINT"]
        upper_query = v.upper()
        for keyword in dangerous_keywords:
            if keyword in upper_query:
                raise ValueError(f"查询包含危险关键词: {keyword}")
        return v.strip()


class QueryResult(BaseSchema):
    """查询结果"""
    records: List[Dict[str, Any]] = Field(description="查询记录")
    summary: Dict[str, Any] = Field(default_factory=dict, description="查询摘要")
    execution_time: float = Field(description="执行时间(毫秒)")
    record_count: int = Field(description="记录数量")


class PathFindingQuery(BaseSchema):
    """路径查找查询"""
    start_node: str = Field(description="起始节点ID")
    end_node: Optional[str] = Field(default=None, description="结束节点ID")
    max_depth: int = Field(default=5, description="最大深度", ge=1, le=10)
    relationship_types: Optional[List[str]] = Field(default=None, description="关系类型过滤")
    direction: str = Field(default="OUTGOING", description="方向", pattern="^(OUTGOING|INCOMING|BOTH)$")


class GraphStatistics(BaseSchema):
    """图统计信息"""
    node_count: int = Field(description="节点总数")
    relationship_count: int = Field(description="关系总数")
    node_type_distribution: Dict[str, int] = Field(description="节点类型分布")
    relationship_type_distribution: Dict[str, int] = Field(description="关系类型分布")
    avg_degree: float = Field(description="平均度数")
    max_depth: int = Field(description="最大深度")


class NodeCreate(BaseSchema):
    """创建节点请求"""
    labels: List[str] = Field(description="节点标签", min_length=1)
    properties: Dict[str, Any] = Field(description="节点属性")


class NodeUpdate(BaseSchema):
    """更新节点请求"""
    properties: Dict[str, Any] = Field(description="要更新的属性")


class RelationshipCreate(BaseSchema):
    """创建关系请求"""
    type: str = Field(description="关系类型")
    start_node: str = Field(description="起始节点ID")
    end_node: str = Field(description="结束节点ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系属性")


class RelationshipUpdate(BaseSchema):
    """更新关系请求"""
    properties: Dict[str, Any] = Field(description="要更新的属性")