"""
校验对齐服务相关模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from enum import Enum

from .base import BaseSchema, TimestampMixin
from .event_chain import EventChain


class ValidationStatus(str, Enum):
    """验证状态枚举"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    NEEDS_REVIEW = "needs_review"


class RuleType(str, Enum):
    """规则类型枚举"""
    TEMPORAL_LOGIC = "temporal_logic"
    TERMINOLOGY = "terminology"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    DOMAIN_SPECIFIC = "domain_specific"


class TermCategory(str, Enum):
    """术语分类枚举"""
    FIRE_EVENT = "火灾事件"
    EQUIPMENT = "设备设施"
    MATERIAL = "材料物质"
    LOCATION = "位置场所"
    PERSON = "人员"
    PROCESS = "过程"
    CONDITION = "条件"


class TermMapping(BaseSchema, TimestampMixin):
    """术语映射"""
    original_term: str = Field(description="原始术语", max_length=200)
    standard_term: str = Field(description="标准术语", max_length=200)
    confidence: float = Field(description="映射置信度", ge=0.0, le=1.0)
    category: TermCategory = Field(description="术语分类")
    source: str = Field(default="manual", description="映射来源", max_length=100)
    
    @field_validator("original_term", "standard_term")
    @classmethod
    def validate_terms(cls, v):
        """验证术语"""
        if not v or v.isspace():
            raise ValueError("术语不能为空")
        return v.strip()


class ValidationRule(BaseSchema, TimestampMixin):
    """验证规则"""
    rule_id: str = Field(description="规则ID")
    rule_type: RuleType = Field(description="规则类型")
    name: str = Field(description="规则名称", max_length=200)
    description: str = Field(description="规则描述", max_length=1000)
    condition: str = Field(description="规则条件")
    action: str = Field(description="规则动作")
    priority: int = Field(description="优先级", ge=1, le=10)
    is_active: bool = Field(default=True, description="是否激活")
    
    @field_validator("rule_id", "name")
    @classmethod
    def validate_required_fields(cls, v):
        """验证必需字段"""
        if not v or v.isspace():
            raise ValueError("字段不能为空")
        return v.strip()


class ValidationResult(BaseSchema, TimestampMixin):
    """验证结果"""
    validated_chains: List[EventChain] = Field(description="验证通过的事件链")
    rejected_chains: List[EventChain] = Field(description="被拒绝的事件链")
    applied_mappings: List[TermMapping] = Field(description="应用的术语映射")
    rule_violations: List[str] = Field(description="规则违反信息")
    validation_score: float = Field(description="验证评分", ge=0.0, le=1.0)
    processing_time: float = Field(description="处理时间(秒)", ge=0.0)


class ValidationReport(BaseSchema, TimestampMixin):
    """验证报告"""
    report_id: str = Field(description="报告ID")
    input_chain_count: int = Field(description="输入事件链数量", ge=0)
    valid_chain_count: int = Field(description="有效事件链数量", ge=0)
    invalid_chain_count: int = Field(description="无效事件链数量", ge=0)
    warning_chain_count: int = Field(description="警告事件链数量", ge=0)
    applied_mapping_count: int = Field(description="应用映射数量", ge=0)
    rule_violation_count: int = Field(description="规则违反数量", ge=0)
    overall_quality_score: float = Field(description="整体质量评分", ge=0.0, le=1.0)
    recommendations: List[str] = Field(description="改进建议")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")


class TermNormalizationRequest(BaseSchema):
    """术语归一化请求"""
    terms: List[str] = Field(description="待归一化术语列表", min_length=1)
    category_filter: Optional[TermCategory] = Field(default=None, description="分类过滤")
    confidence_threshold: float = Field(default=0.8, description="置信度阈值", ge=0.0, le=1.0)
    
    @field_validator("terms")
    @classmethod
    def validate_terms(cls, v):
        """验证术语列表"""
        if not v:
            raise ValueError("术语列表不能为空")
        return [term.strip() for term in v if term.strip()]


class TermNormalizationResult(BaseSchema):
    """术语归一化结果"""
    original_term: str = Field(description="原始术语")
    normalized_term: str = Field(description="归一化术语")
    confidence: float = Field(description="置信度")
    category: TermCategory = Field(description="术语分类")
    alternatives: List[str] = Field(default_factory=list, description="备选术语")


class LogicalConsistencyCheck(BaseSchema):
    """逻辑一致性检查"""
    chain_id: str = Field(description="事件链ID")
    check_type: str = Field(description="检查类型")
    is_consistent: bool = Field(description="是否一致")
    violation_details: Optional[str] = Field(default=None, description="违反详情")
    suggested_fix: Optional[str] = Field(default=None, description="建议修复")


class TemporalValidation(BaseSchema):
    """时间逻辑验证"""
    source_event: str = Field(description="源事件")
    target_event: str = Field(description="目标事件")
    source_timestamp: Optional[datetime] = Field(description="源事件时间")
    target_timestamp: Optional[datetime] = Field(description="目标事件时间")
    is_valid: bool = Field(description="时间逻辑是否有效")
    time_gap: Optional[float] = Field(description="时间间隔(秒)")
    violation_reason: Optional[str] = Field(description="违反原因")


class ValidationMetrics(BaseSchema):
    """验证指标"""
    total_validations: int = Field(description="总验证次数")
    success_rate: float = Field(description="成功率", ge=0.0, le=1.0)
    avg_processing_time: float = Field(description="平均处理时间")
    avg_quality_score: float = Field(description="平均质量评分")
    rule_usage_stats: Dict[str, int] = Field(description="规则使用统计")
    mapping_usage_stats: Dict[str, int] = Field(description="映射使用统计")


class ValidationConfig(BaseSchema):
    """验证配置"""
    enable_terminology_check: bool = Field(default=True, description="启用术语检查")
    enable_temporal_check: bool = Field(default=True, description="启用时间检查")
    enable_consistency_check: bool = Field(default=True, description="启用一致性检查")
    confidence_threshold: float = Field(default=0.7, description="置信度阈值", ge=0.0, le=1.0)
    max_time_gap: int = Field(default=86400, description="最大时间间隔(秒)")
    strict_mode: bool = Field(default=False, description="严格模式")


class BatchValidationRequest(BaseSchema):
    """批量验证请求"""
    event_chains: List[EventChain] = Field(description="事件链列表", min_length=1, max_length=100)
    validation_config: Optional[ValidationConfig] = Field(default=None, description="验证配置")
    
    @field_validator("event_chains")
    @classmethod
    def validate_event_chains(cls, v):
        """验证事件链列表"""
        if not v:
            raise ValueError("事件链列表不能为空")
        return v


class ValidationTask(BaseSchema, TimestampMixin):
    """验证任务"""
    task_id: str = Field(description="任务ID")
    status: ValidationStatus = Field(description="验证状态")
    input_count: int = Field(description="输入数量")
    processed_count: int = Field(description="已处理数量")
    result: Optional[ValidationResult] = Field(default=None, description="验证结果")
    error_message: Optional[str] = Field(default=None, description="错误消息")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class RuleViolation(BaseSchema):
    """规则违反"""
    rule_id: str = Field(description="规则ID")
    rule_name: str = Field(description="规则名称")
    violation_type: str = Field(description="违反类型")
    description: str = Field(description="违反描述")
    severity: str = Field(description="严重程度")
    affected_chain: EventChain = Field(description="受影响的事件链")
    suggested_action: str = Field(description="建议操作")


class QualityAssessment(BaseSchema):
    """质量评估"""
    completeness_score: float = Field(description="完整性评分", ge=0.0, le=1.0)
    consistency_score: float = Field(description="一致性评分", ge=0.0, le=1.0)
    accuracy_score: float = Field(description="准确性评分", ge=0.0, le=1.0)
    relevance_score: float = Field(description="相关性评分", ge=0.0, le=1.0)
    overall_score: float = Field(description="总体评分", ge=0.0, le=1.0)
    improvement_suggestions: List[str] = Field(description="改进建议")