"""
智能抽取服务相关模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, model_validator
from enum import Enum

from .base import BaseSchema, TimestampMixin
from .event_chain import EventChain, EventChainCreate, RelationType


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """文档类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"


class SectionType(str, Enum):
    """章节类型枚举"""
    ACCIDENT_PROCESS = "事故经过"
    CAUSE_ANALYSIS = "原因分析"
    INVESTIGATION_RESULT = "调查结果"
    PREVENTION_MEASURES = "预防措施"
    OTHER = "其他"


class ExtractedNodeType(str, Enum):
    """分层抽取节点类型"""
    HAZARD = "Hazard"
    FIRE_EVENT = "FireEvent"
    CONSEQUENCE = "Consequence"


class ExtractedRelationType(str, Enum):
    """分层抽取关系类型"""
    LEADS_TO = "LEADS_TO"
    CAUSES = "CAUSES"
    RESULTS_IN = "RESULTS_IN"


class DocumentSections(BaseSchema):
    """文档章节"""
    sections: Dict[str, str] = Field(description="章节内容映射")
    
    @field_validator("sections")
    @classmethod
    def validate_sections(cls, v):
        """验证章节内容"""
        if not v:
            raise ValueError("章节内容不能为空")
        
        has_content = False
        for _, content in v.items():
            if content and content.strip():
                has_content = True
                break
        
        if not has_content:
            raise ValueError("所有章节内容都为空")
        
        return v


class ExtractedNode(BaseSchema):
    """LLM 抽取出的分层节点"""
    node_type: ExtractedNodeType = Field(description="节点类型")
    description: str = Field(description="节点描述", min_length=2, max_length=1000)
    standard_term: str = Field(description="标准术语", min_length=2, max_length=200)
    context: str = Field(default="", description="上下文信息", max_length=1000)

    @field_validator("description", "standard_term", mode="before")
    @classmethod
    def validate_text_fields(cls, v):
        if not v or not str(v).strip():
            raise ValueError("文本字段不能为空")
        return str(v).strip()

    @field_validator("context", mode="before")
    @classmethod
    def validate_context(cls, v):
        return str(v).strip() if v else ""


class ExtractedEdge(BaseSchema):
    """LLM 抽取出的分层关系"""
    source: str = Field(description="源节点标准术语", min_length=2, max_length=200)
    source_type: ExtractedNodeType = Field(description="源节点类型")
    target: str = Field(description="目标节点标准术语", min_length=2, max_length=200)
    target_type: ExtractedNodeType = Field(description="目标节点类型")
    relation: ExtractedRelationType = Field(description="关系类型")
    confidence: float = Field(description="置信度", ge=0.0, le=1.0)
    context: str = Field(default="", description="上下文信息", max_length=1000)

    @field_validator("source", "target", mode="before")
    @classmethod
    def validate_endpoints(cls, v):
        if not v or not str(v).strip():
            raise ValueError("关系端点不能为空")
        return str(v).strip()

    @field_validator("context", mode="before")
    @classmethod
    def validate_context(cls, v):
        return str(v).strip() if v else ""

    @model_validator(mode="after")
    def validate_relation_semantics(self):
        allowed = {
            (ExtractedNodeType.HAZARD, ExtractedRelationType.LEADS_TO, ExtractedNodeType.FIRE_EVENT),
            (ExtractedNodeType.HAZARD, ExtractedRelationType.CAUSES, ExtractedNodeType.HAZARD),
            (ExtractedNodeType.HAZARD, ExtractedRelationType.CAUSES, ExtractedNodeType.FIRE_EVENT),
            (ExtractedNodeType.HAZARD, ExtractedRelationType.RESULTS_IN, ExtractedNodeType.CONSEQUENCE),
            (ExtractedNodeType.FIRE_EVENT, ExtractedRelationType.CAUSES, ExtractedNodeType.FIRE_EVENT),
            (ExtractedNodeType.FIRE_EVENT, ExtractedRelationType.RESULTS_IN, ExtractedNodeType.CONSEQUENCE),
            (ExtractedNodeType.FIRE_EVENT, ExtractedRelationType.CAUSES, ExtractedNodeType.CONSEQUENCE),
        }
        triple = (self.source_type, self.relation, self.target_type)
        if triple not in allowed:
            raise ValueError(
                f"不支持的分层关系: {self.source_type} -[{self.relation}]-> {self.target_type}"
            )
        return self


class LayeredExtractionResult(BaseSchema):
    """分层抽取结果"""
    nodes: List[ExtractedNode] = Field(default_factory=list, description="抽取出的节点")
    edges: List[ExtractedEdge] = Field(default_factory=list, description="抽取出的关系")

    @field_validator("nodes")
    @classmethod
    def validate_nodes(cls, v):
        if not v:
            raise ValueError("抽取节点不能为空")
        return v

    @field_validator("edges")
    @classmethod
    def validate_edges(cls, v):
        if not v:
            raise ValueError("抽取关系不能为空")
        return v

    def to_event_chains(self) -> List[EventChainCreate]:
        relation_mapping = {
            ExtractedRelationType.LEADS_TO: RelationType.TRIGGERS,
            ExtractedRelationType.CAUSES: RelationType.CAUSES,
            ExtractedRelationType.RESULTS_IN: RelationType.CAUSES,
        }
        return [
            EventChainCreate(
                source=edge.source,
                relation=relation_mapping[edge.relation],
                target=edge.target,
                confidence=edge.confidence,
                context=edge.context,
            )
            for edge in self.edges
        ]


class ExtractionResult(BaseSchema, TimestampMixin):
    """抽取结果"""
    document_id: str = Field(description="文档ID")
    event_chains: List[EventChain] = Field(description="抽取的事件链")
    quality_score: float = Field(description="质量评分", ge=0.0, le=1.0)
    processing_time: float = Field(description="处理时间(秒)", ge=0.0)
    errors: List[str] = Field(default_factory=list, description="错误信息")
    layered_result: Optional[LayeredExtractionResult] = Field(default=None, description="分层抽取结果")
    
    @field_validator("event_chains")
    @classmethod
    def validate_event_chains(cls, v):
        if not v:
            raise ValueError("事件链不能为空")
        return v


class QualityScore(BaseSchema):
    """质量评分"""
    overall_score: float = Field(description="总体评分", ge=0.0, le=1.0)
    completeness: float = Field(description="完整性评分", ge=0.0, le=1.0)
    consistency: float = Field(description="一致性评分", ge=0.0, le=1.0)
    relevance: float = Field(description="相关性评分", ge=0.0, le=1.0)
    confidence: float = Field(description="置信度评分", ge=0.0, le=1.0)
    details: Dict[str, Any] = Field(default_factory=dict, description="详细评分信息")


class ExtractionTask(BaseSchema, TimestampMixin):
    """抽取任务"""
    task_id: str = Field(description="任务ID")
    document_id: str = Field(description="文档ID")
    status: ProcessingStatus = Field(description="处理状态")
    progress: float = Field(default=0.0, description="进度百分比", ge=0.0, le=100.0)
    result: Optional[ExtractionResult] = Field(default=None, description="抽取结果")
    error_message: Optional[str] = Field(default=None, description="错误消息")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class ExtractionRequest(BaseSchema):
    """抽取请求"""
    document_id: str = Field(description="文档ID")
    extraction_options: Dict[str, Any] = Field(default_factory=dict, description="抽取选项")
    priority: int = Field(default=5, description="优先级", ge=1, le=10)
    
    @field_validator("document_id")
    @classmethod
    def validate_document_id(cls, v):
        if not v or v.isspace():
            raise ValueError("文档ID不能为空")
        return v.strip()


class ExtractionConfig(BaseSchema):
    """抽取配置"""
    llm_model: str = Field(default="gpt-3.5-turbo", description="LLM模型")
    temperature: float = Field(default=0.1, description="温度参数", ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, description="最大令牌数", ge=100, le=8000)
    few_shot_examples: List[Dict[str, Any]] = Field(default_factory=list, description="Few-Shot示例")
    extraction_prompt: str = Field(description="抽取提示词")
    quality_threshold: float = Field(default=0.7, description="质量阈值", ge=0.0, le=1.0)


class LLMResponse(BaseSchema):
    """LLM响应"""
    content: str = Field(description="响应内容")
    usage: Dict[str, Any] = Field(description="使用统计")
    model: str = Field(description="使用的模型")
    finish_reason: str = Field(description="完成原因")
    response_time: float = Field(description="响应时间(秒)")


class ExtractionMetrics(BaseSchema):
    """抽取指标"""
    total_documents: int = Field(description="总文档数")
    successful_extractions: int = Field(description="成功抽取数")
    failed_extractions: int = Field(description="失败抽取数")
    avg_processing_time: float = Field(description="平均处理时间")
    avg_quality_score: float = Field(description="平均质量评分")
    total_event_chains: int = Field(description="总事件链数")
    success_rate: float = Field(description="成功率", ge=0.0, le=1.0)


class ExtractionHistory(BaseSchema):
    """抽取历史"""
    task_id: str = Field(description="任务ID")
    document_id: str = Field(description="文档ID")
    status: ProcessingStatus = Field(description="状态")
    quality_score: Optional[float] = Field(description="质量评分")
    event_chain_count: int = Field(description="事件链数量")
    processing_time: float = Field(description="处理时间")
    created_at: datetime = Field(description="创建时间")
    completed_at: Optional[datetime] = Field(description="完成时间")


class BatchExtractionRequest(BaseSchema):
    """批量抽取请求"""
    document_ids: List[str] = Field(description="文档ID列表", min_length=1, max_length=50)
    extraction_options: Dict[str, Any] = Field(default_factory=dict, description="抽取选项")
    priority: int = Field(default=5, description="优先级", ge=1, le=10)
    
    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, v):
        if not v:
            raise ValueError("文档ID列表不能为空")
        if len(v) != len(set(v)):
            raise ValueError("文档ID列表包含重复项")
        return v


class BatchExtractionResult(BaseSchema):
    """批量抽取结果"""
    batch_id: str = Field(description="批次ID")
    total_documents: int = Field(description="总文档数")
    completed_documents: int = Field(description="已完成文档数")
    failed_documents: int = Field(description="失败文档数")
    results: List[ExtractionResult] = Field(description="抽取结果列表")
    overall_quality_score: float = Field(description="整体质量评分")
    total_processing_time: float = Field(description="总处理时间")


class ExtractionProgress(BaseSchema):
    """抽取进度"""
    task_id: str = Field(description="任务ID")
    status: ProcessingStatus = Field(description="状态")
    progress: float = Field(description="进度百分比", ge=0.0, le=100.0)
    current_step: str = Field(description="当前步骤")
    estimated_remaining_time: Optional[float] = Field(description="预计剩余时间(秒)")
    message: str = Field(description="状态消息")
