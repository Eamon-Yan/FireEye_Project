"""
基础 Pydantic 模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class BaseSchema(BaseModel):
    """基础模型类"""
    
    model_config = {
        # 允许使用 ORM 模式
        "from_attributes": True,
        # 使用枚举值而不是枚举名称
        "use_enum_values": True,
        # 验证赋值
        "validate_assignment": True,
        # 禁止额外字段
        "extra": "forbid"
    }


class TimestampMixin(BaseModel):
    """时间戳混入类"""
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, description="更新时间")


class ResponseStatus(str, Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class BaseResponse(BaseSchema):
    """基础响应模型"""
    status: ResponseStatus = Field(description="响应状态")
    message: str = Field(description="响应消息")
    data: Optional[Any] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class PaginationParams(BaseSchema):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")
    
    @property
    def offset(self) -> int:
        """计算偏移量"""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseResponse):
    """分页响应模型"""
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页大小")
    pages: int = Field(description="总页数")
    
    @field_validator("pages", mode="before")
    @classmethod
    def calculate_pages(cls, v, info):
        """计算总页数"""
        if info.data:
            total = info.data.get("total", 0)
            size = info.data.get("size", 20)
            return (total + size - 1) // size if total > 0 else 0
        return v


class ErrorDetail(BaseSchema):
    """错误详情"""
    error_code: str = Field(description="错误代码")
    error_message: str = Field(description="错误消息")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
    suggestions: List[str] = Field(default_factory=list, description="建议解决方案")


class ValidationError(BaseSchema):
    """验证错误"""
    field: str = Field(description="字段名")
    message: str = Field(description="错误消息")
    value: Optional[Any] = Field(default=None, description="错误值")


class HealthStatus(BaseSchema):
    """健康状态"""
    status: str = Field(description="服务状态")
    service: str = Field(description="服务名称")
    database: Dict[str, str] = Field(description="数据库状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")