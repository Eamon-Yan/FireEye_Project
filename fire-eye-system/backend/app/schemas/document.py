"""
文档管理相关模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from enum import Enum

from .base import BaseSchema, TimestampMixin


class DocumentStatus(str, Enum):
    """文档状态枚举"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


class FileType(str, Enum):
    """文件类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"


class Document(BaseSchema, TimestampMixin):
    """文档模型"""
    document_id: str = Field(description="文档ID")
    title: str = Field(description="文档标题", max_length=500)
    file_path: str = Field(description="文件路径")
    file_type: FileType = Field(description="文件类型")
    file_size: int = Field(description="文件大小(字节)", ge=0)
    upload_time: datetime = Field(description="上传时间")
    processing_status: DocumentStatus = Field(description="处理状态")
    extracted_chains: int = Field(default=0, description="抽取的事件链数量", ge=0)
    quality_score: Optional[float] = Field(default=None, description="质量评分", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """验证文档标题"""
        if not v or v.isspace():
            raise ValueError("文档标题不能为空")
        return v.strip()
    
    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v):
        """验证文件路径"""
        if not v or v.isspace():
            raise ValueError("文件路径不能为空")
        return v.strip()


class DocumentCreate(BaseSchema):
    """创建文档请求"""
    title: str = Field(description="文档标题", max_length=500)
    file_type: FileType = Field(description="文件类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """验证文档标题"""
        if not v or v.isspace():
            raise ValueError("文档标题不能为空")
        return v.strip()


class DocumentUpdate(BaseSchema):
    """更新文档请求"""
    title: Optional[str] = Field(default=None, description="文档标题", max_length=500)
    processing_status: Optional[DocumentStatus] = Field(default=None, description="处理状态")
    extracted_chains: Optional[int] = Field(default=None, description="抽取的事件链数量", ge=0)
    quality_score: Optional[float] = Field(default=None, description="质量评分", ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="文档元数据")


class DocumentResponse(BaseSchema):
    """文档响应"""
    document_id: str = Field(description="文档ID")
    title: str = Field(description="文档标题")
    file_type: FileType = Field(description="文件类型")
    file_size: int = Field(description="文件大小(字节)")
    upload_time: datetime = Field(description="上传时间")
    processing_status: DocumentStatus = Field(description="处理状态")
    extracted_chains: int = Field(description="抽取的事件链数量")
    quality_score: Optional[float] = Field(description="质量评分")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class DocumentQuery(BaseSchema):
    """文档查询参数"""
    title: Optional[str] = Field(default=None, description="标题关键词")
    file_type: Optional[FileType] = Field(default=None, description="文件类型")
    status: Optional[DocumentStatus] = Field(default=None, description="处理状态")
    min_quality_score: Optional[float] = Field(default=None, description="最小质量评分", ge=0.0, le=1.0)
    max_quality_score: Optional[float] = Field(default=None, description="最大质量评分", ge=0.0, le=1.0)
    upload_start: Optional[datetime] = Field(default=None, description="上传开始时间")
    upload_end: Optional[datetime] = Field(default=None, description="上传结束时间")
    
    @field_validator("max_quality_score")
    @classmethod
    def validate_quality_range(cls, v, info):
        """验证质量评分范围"""
        min_score = info.data.get("min_quality_score")
        if min_score is not None and v is not None and v < min_score:
            raise ValueError("最大质量评分不能小于最小质量评分")
        return v
    
    @field_validator("upload_end")
    @classmethod
    def validate_time_range(cls, v, info):
        """验证时间范围"""
        start_time = info.data.get("upload_start")
        if start_time is not None and v is not None and v < start_time:
            raise ValueError("结束时间不能早于开始时间")
        return v


class DocumentStatistics(BaseSchema):
    """文档统计信息"""
    total_documents: int = Field(description="总文档数量")
    status_distribution: Dict[str, int] = Field(description="状态分布")
    file_type_distribution: Dict[str, int] = Field(description="文件类型分布")
    avg_quality_score: Optional[float] = Field(description="平均质量评分")
    total_file_size: int = Field(description="总文件大小(字节)")
    total_extracted_chains: int = Field(description="总抽取事件链数量")
    processing_success_rate: float = Field(description="处理成功率", ge=0.0, le=1.0)


class FileUpload(BaseSchema):
    """文件上传信息"""
    filename: str = Field(description="文件名")
    content_type: str = Field(description="内容类型")
    file_size: int = Field(description="文件大小(字节)", ge=0)
    
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v):
        """验证文件名"""
        if not v or v.isspace():
            raise ValueError("文件名不能为空")
        
        # 检查文件扩展名
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f"不支持的文件类型，支持的类型: {', '.join(allowed_extensions)}")
        
        return v.strip()


class DocumentContent(BaseSchema):
    """文档内容"""
    document_id: str = Field(description="文档ID")
    raw_content: str = Field(description="原始内容")
    structured_content: Dict[str, str] = Field(description="结构化内容")
    extracted_sections: Dict[str, str] = Field(description="提取的章节")
    content_length: int = Field(description="内容长度", ge=0)
    extraction_time: datetime = Field(description="提取时间")


class DocumentProcessingLog(BaseSchema, TimestampMixin):
    """文档处理日志"""
    log_id: str = Field(description="日志ID")
    document_id: str = Field(description="文档ID")
    operation: str = Field(description="操作类型")
    status: str = Field(description="操作状态")
    message: str = Field(description="日志消息")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细信息")
    processing_time: Optional[float] = Field(default=None, description="处理时间(秒)")


class DocumentBatch(BaseSchema):
    """批量文档操作"""
    document_ids: List[str] = Field(description="文档ID列表", min_length=1, max_length=100)
    operation: str = Field(description="操作类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")
    
    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, v):
        """验证文档ID列表"""
        if not v:
            raise ValueError("文档ID列表不能为空")
        
        # 检查重复
        if len(v) != len(set(v)):
            raise ValueError("文档ID列表包含重复项")
        
        return v


class DocumentVersion(BaseSchema, TimestampMixin):
    """文档版本"""
    version_id: str = Field(description="版本ID")
    document_id: str = Field(description="文档ID")
    version_number: int = Field(description="版本号", ge=1)
    changes: List[str] = Field(description="变更记录")
    file_path: str = Field(description="文件路径")
    file_size: int = Field(description="文件大小(字节)", ge=0)
    created_by: str = Field(description="创建者")


class DocumentMetadata(BaseSchema):
    """文档元数据"""
    author: Optional[str] = Field(default=None, description="作者")
    creation_date: Optional[datetime] = Field(default=None, description="创建日期")
    modification_date: Optional[datetime] = Field(default=None, description="修改日期")
    subject: Optional[str] = Field(default=None, description="主题")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    language: Optional[str] = Field(default=None, description="语言")
    page_count: Optional[int] = Field(default=None, description="页数", ge=0)
    word_count: Optional[int] = Field(default=None, description="字数", ge=0)
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")


class DocumentSearchResult(BaseSchema):
    """文档搜索结果"""
    document: DocumentResponse = Field(description="文档信息")
    relevance_score: float = Field(description="相关性评分", ge=0.0, le=1.0)
    matched_content: List[str] = Field(description="匹配的内容片段")
    highlight_positions: List[Dict[str, int]] = Field(description="高亮位置")


class DocumentExport(BaseSchema):
    """文档导出配置"""
    document_ids: List[str] = Field(description="文档ID列表", min_length=1)
    export_format: str = Field(description="导出格式", pattern="^(json|csv|xlsx|pdf)$")
    include_content: bool = Field(default=False, description="是否包含内容")
    include_metadata: bool = Field(default=True, description="是否包含元数据")
    include_processing_logs: bool = Field(default=False, description="是否包含处理日志")