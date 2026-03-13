"""
场景预测服务相关模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from enum import Enum

from .base import BaseSchema, TimestampMixin
from .graph import Node, Relationship, Path


class PredictionStatus(str, Enum):
    """预测状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """风险等级枚举"""
    VERY_LOW = "极低"
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    VERY_HIGH = "极高"
    CRITICAL = "危急"


class ScenarioType(str, Enum):
    """场景类型枚举"""
    FIRE_EVOLUTION = "火灾演化"
    EVACUATION = "疏散逃生"
    RESCUE_OPERATION = "救援行动"
    DAMAGE_ASSESSMENT = "损失评估"


class EvolutionPath(BaseSchema, TimestampMixin):
    """演化路径"""
    path_id: str = Field(description="路径ID")
    nodes: List[Node] = Field(description="路径节点")
    relationships: List[Relationship] = Field(description="路径关系")
    probability: float = Field(description="发生概率", ge=0.0, le=1.0)
    risk_level: RiskLevel = Field(description="风险等级")
    estimated_time: int = Field(description="预计时间(秒)", ge=0)
    
    @field_validator("nodes")
    @classmethod
    def validate_nodes(cls, v):
        """验证节点列表"""
        if not v:
            raise ValueError("路径节点不能为空")
        return v


class Scene(BaseSchema):
    """场景片段"""
    scene_id: str = Field(description="场景ID")
    title: str = Field(description="场景标题", max_length=200)
    description: str = Field(description="场景描述", max_length=2000)
    duration: int = Field(description="持续时间(秒)", ge=0)
    visual_elements: List[str] = Field(description="视觉元素")
    audio_elements: List[str] = Field(description="音频元素")
    risk_indicators: List[str] = Field(default_factory=list, description="风险指标")
    
    @field_validator("title", "description")
    @classmethod
    def validate_text_fields(cls, v):
        """验证文本字段"""
        if not v or v.isspace():
            raise ValueError("文本字段不能为空")
        return v.strip()


class ScenarioScript(BaseSchema, TimestampMixin):
    """场景剧本"""
    script_id: str = Field(description="剧本ID")
    title: str = Field(description="剧本标题", max_length=200)
    scenario_type: ScenarioType = Field(description="场景类型")
    scenes: List[Scene] = Field(description="场景列表", min_length=1)
    total_duration: int = Field(description="总时长(秒)", ge=0)
    risk_assessment: str = Field(description="风险评估", max_length=1000)
    prevention_measures: List[str] = Field(default_factory=list, description="预防措施")
    
    @field_validator("scenes")
    @classmethod
    def validate_scenes(cls, v):
        """验证场景列表"""
        if not v:
            raise ValueError("场景列表不能为空")
        return v
    
    @field_validator("total_duration")
    @classmethod
    def calculate_total_duration(cls, v, info):
        """计算总时长"""
        scenes = info.data.get("scenes", [])
        calculated_duration = sum(scene.duration for scene in scenes)
        if v != calculated_duration:
            # 自动修正总时长
            return calculated_duration
        return v


class PredictionRequest(BaseSchema):
    """预测请求"""
    hazard_description: str = Field(description="隐患描述", max_length=1000)
    prediction_type: ScenarioType = Field(default=ScenarioType.FIRE_EVOLUTION, description="预测类型")
    max_paths: int = Field(default=10, description="最大路径数", ge=1, le=50)
    max_depth: int = Field(default=5, description="最大深度", ge=1, le=10)
    time_horizon: int = Field(default=3600, description="时间范围(秒)", ge=60, le=86400)
    include_script: bool = Field(default=True, description="是否生成剧本")
    
    @field_validator("hazard_description")
    @classmethod
    def validate_hazard_description(cls, v):
        """验证隐患描述"""
        if not v or v.isspace():
            raise ValueError("隐患描述不能为空")
        return v.strip()


class PredictionResult(BaseSchema, TimestampMixin):
    """预测结果"""
    prediction_id: str = Field(description="预测ID")
    hazard_description: str = Field(description="隐患描述")
    matched_nodes: List[Node] = Field(description="匹配的起始节点")
    evolution_paths: List[EvolutionPath] = Field(description="演化路径")
    scenario_scripts: List[ScenarioScript] = Field(description="场景剧本")
    overall_risk_level: RiskLevel = Field(description="整体风险等级")
    confidence_score: float = Field(description="预测置信度", ge=0.0, le=1.0)
    processing_time: float = Field(description="处理时间(秒)", ge=0.0)


class RankedPath(BaseSchema):
    """排序路径"""
    path: EvolutionPath = Field(description="演化路径")
    rank: int = Field(description="排名", ge=1)
    risk_score: float = Field(description="风险评分", ge=0.0, le=1.0)
    impact_score: float = Field(description="影响评分", ge=0.0, le=1.0)
    likelihood_score: float = Field(description="可能性评分", ge=0.0, le=1.0)
    combined_score: float = Field(description="综合评分", ge=0.0, le=1.0)


class NodeMatchingResult(BaseSchema):
    """节点匹配结果"""
    query_text: str = Field(description="查询文本")
    matched_nodes: List[Node] = Field(description="匹配的节点")
    similarity_scores: List[float] = Field(description="相似度评分")
    matching_method: str = Field(description="匹配方法")
    confidence: float = Field(description="匹配置信度", ge=0.0, le=1.0)


class PathFindingConfig(BaseSchema):
    """路径查找配置"""
    algorithm: str = Field(default="dijkstra", description="算法类型")
    max_depth: int = Field(default=5, description="最大深度", ge=1, le=10)
    max_paths: int = Field(default=10, description="最大路径数", ge=1, le=50)
    weight_threshold: float = Field(default=0.1, description="权重阈值", ge=0.0, le=1.0)
    include_cycles: bool = Field(default=False, description="是否包含环路")
    relationship_filters: List[str] = Field(default_factory=list, description="关系过滤器")


class RiskAssessment(BaseSchema):
    """风险评估"""
    risk_level: RiskLevel = Field(description="风险等级")
    probability: float = Field(description="发生概率", ge=0.0, le=1.0)
    impact_severity: int = Field(description="影响严重程度", ge=1, le=10)
    time_to_impact: int = Field(description="影响时间(秒)", ge=0)
    affected_areas: List[str] = Field(description="影响区域")
    potential_casualties: int = Field(description="潜在伤亡", ge=0)
    economic_loss: float = Field(description="经济损失", ge=0.0)
    mitigation_measures: List[str] = Field(description="缓解措施")


class ScenarioGeneration(BaseSchema):
    """场景生成配置"""
    include_visual_effects: bool = Field(default=True, description="包含视觉效果")
    include_audio_effects: bool = Field(default=True, description="包含音频效果")
    detail_level: str = Field(default="medium", description="详细程度", pattern="^(low|medium|high)$")
    target_audience: str = Field(default="general", description="目标受众")
    language: str = Field(default="zh-CN", description="语言")
    duration_preference: str = Field(default="auto", description="时长偏好")


class PredictionTask(BaseSchema, TimestampMixin):
    """预测任务"""
    task_id: str = Field(description="任务ID")
    status: PredictionStatus = Field(description="预测状态")
    request: PredictionRequest = Field(description="预测请求")
    progress: float = Field(default=0.0, description="进度百分比", ge=0.0, le=100.0)
    result: Optional[PredictionResult] = Field(default=None, description="预测结果")
    error_message: Optional[str] = Field(default=None, description="错误消息")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class PredictionMetrics(BaseSchema):
    """预测指标"""
    total_predictions: int = Field(description="总预测次数")
    successful_predictions: int = Field(description="成功预测次数")
    failed_predictions: int = Field(description="失败预测次数")
    avg_processing_time: float = Field(description="平均处理时间")
    avg_confidence_score: float = Field(description="平均置信度")
    avg_paths_per_prediction: float = Field(description="平均路径数")
    success_rate: float = Field(description="成功率", ge=0.0, le=1.0)


class ScenarioComparison(BaseSchema):
    """场景对比"""
    scenario_a: ScenarioScript = Field(description="场景A")
    scenario_b: ScenarioScript = Field(description="场景B")
    similarity_score: float = Field(description="相似度评分", ge=0.0, le=1.0)
    key_differences: List[str] = Field(description="关键差异")
    risk_comparison: Dict[str, Any] = Field(description="风险对比")
    recommendations: List[str] = Field(description="建议")


class PredictionHistory(BaseSchema):
    """预测历史"""
    prediction_id: str = Field(description="预测ID")
    hazard_description: str = Field(description="隐患描述")
    risk_level: RiskLevel = Field(description="风险等级")
    path_count: int = Field(description="路径数量")
    confidence_score: float = Field(description="置信度")
    processing_time: float = Field(description="处理时间")
    created_at: datetime = Field(description="创建时间")
    user_feedback: Optional[str] = Field(default=None, description="用户反馈")


class BatchPredictionRequest(BaseSchema):
    """批量预测请求"""
    hazard_descriptions: List[str] = Field(description="隐患描述列表", min_length=1, max_length=20)
    prediction_config: Optional[PredictionRequest] = Field(default=None, description="预测配置")
    
    @field_validator("hazard_descriptions")
    @classmethod
    def validate_hazard_descriptions(cls, v):
        """验证隐患描述列表"""
        if not v:
            raise ValueError("隐患描述列表不能为空")
        return [desc.strip() for desc in v if desc.strip()]