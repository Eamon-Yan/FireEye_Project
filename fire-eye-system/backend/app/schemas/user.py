"""
用户管理相关模型
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, EmailStr
from enum import Enum

from .base import BaseSchema, TimestampMixin


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    GUEST = "guest"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(BaseSchema, TimestampMixin):
    """用户模型"""
    user_id: str = Field(description="用户ID")
    username: str = Field(description="用户名", min_length=3, max_length=50)
    email: EmailStr = Field(description="邮箱地址")
    full_name: str = Field(description="全名", max_length=100)
    role: UserRole = Field(description="用户角色")
    status: UserStatus = Field(description="用户状态")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")
    login_count: int = Field(default=0, description="登录次数", ge=0)
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好")
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """验证用户名"""
        if not v or v.isspace():
            raise ValueError("用户名不能为空")
        
        # 检查用户名格式
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        
        return v.strip().lower()
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        """验证全名"""
        if not v or v.isspace():
            raise ValueError("全名不能为空")
        return v.strip()


class UserCreate(BaseSchema):
    """创建用户请求"""
    username: str = Field(description="用户名", min_length=3, max_length=50)
    email: EmailStr = Field(description="邮箱地址")
    password: str = Field(description="密码", min_length=8, max_length=128)
    full_name: str = Field(description="全名", max_length=100)
    role: UserRole = Field(default=UserRole.VIEWER, description="用户角色")
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        
        # 检查密码复杂度
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("密码必须包含大写字母、小写字母和数字")
        
        return v


class UserUpdate(BaseSchema):
    """更新用户请求"""
    email: Optional[EmailStr] = Field(default=None, description="邮箱地址")
    full_name: Optional[str] = Field(default=None, description="全名", max_length=100)
    role: Optional[UserRole] = Field(default=None, description="用户角色")
    status: Optional[UserStatus] = Field(default=None, description="用户状态")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="用户偏好")


class UserResponse(BaseSchema):
    """用户响应"""
    user_id: str = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: EmailStr = Field(description="邮箱地址")
    full_name: str = Field(description="全名")
    role: UserRole = Field(description="用户角色")
    status: UserStatus = Field(description="用户状态")
    last_login: Optional[datetime] = Field(description="最后登录时间")
    login_count: int = Field(description="登录次数")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class UserLogin(BaseSchema):
    """用户登录请求"""
    username: str = Field(description="用户名或邮箱")
    password: str = Field(description="密码")
    remember_me: bool = Field(default=False, description="记住我")
    
    @field_validator("username", "password")
    @classmethod
    def validate_required_fields(cls, v):
        """验证必需字段"""
        if not v or v.isspace():
            raise ValueError("字段不能为空")
        return v.strip()


class UserSession(BaseSchema, TimestampMixin):
    """用户会话"""
    session_id: str = Field(description="会话ID")
    user_id: str = Field(description="用户ID")
    last_activity: datetime = Field(description="最后活动时间")
    query_history: List[str] = Field(default_factory=list, description="查询历史")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="会话偏好")
    ip_address: Optional[str] = Field(default=None, description="IP地址")
    user_agent: Optional[str] = Field(default=None, description="用户代理")


class Token(BaseSchema):
    """访问令牌"""
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间(秒)")
    refresh_token: Optional[str] = Field(default=None, description="刷新令牌")


class TokenData(BaseSchema):
    """令牌数据"""
    user_id: str = Field(description="用户ID")
    username: str = Field(description="用户名")
    role: UserRole = Field(description="用户角色")
    exp: datetime = Field(description="过期时间")


class PasswordChange(BaseSchema):
    """密码修改请求"""
    current_password: str = Field(description="当前密码")
    new_password: str = Field(description="新密码", min_length=8, max_length=128)
    confirm_password: str = Field(description="确认密码")
    
    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v, info):
        """验证密码匹配"""
        new_password = info.data.get("new_password")
        if new_password and v != new_password:
            raise ValueError("确认密码与新密码不匹配")
        return v


class PasswordReset(BaseSchema):
    """密码重置请求"""
    email: EmailStr = Field(description="邮箱地址")


class PasswordResetConfirm(BaseSchema):
    """密码重置确认"""
    token: str = Field(description="重置令牌")
    new_password: str = Field(description="新密码", min_length=8, max_length=128)
    confirm_password: str = Field(description="确认密码")
    
    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v, info):
        """验证密码匹配"""
        new_password = info.data.get("new_password")
        if new_password and v != new_password:
            raise ValueError("确认密码与新密码不匹配")
        return v


class UserActivity(BaseSchema, TimestampMixin):
    """用户活动记录"""
    activity_id: str = Field(description="活动ID")
    user_id: str = Field(description="用户ID")
    action: str = Field(description="操作类型")
    resource: str = Field(description="资源类型")
    resource_id: Optional[str] = Field(default=None, description="资源ID")
    details: Dict[str, Any] = Field(default_factory=dict, description="操作详情")
    ip_address: Optional[str] = Field(default=None, description="IP地址")
    user_agent: Optional[str] = Field(default=None, description="用户代理")


class UserPreferences(BaseSchema):
    """用户偏好设置"""
    language: str = Field(default="zh-CN", description="界面语言")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    theme: str = Field(default="light", description="主题", pattern="^(light|dark|auto)$")
    notifications: Dict[str, bool] = Field(default_factory=dict, description="通知设置")
    dashboard_layout: Dict[str, Any] = Field(default_factory=dict, description="仪表板布局")
    default_page_size: int = Field(default=20, description="默认页面大小", ge=10, le=100)


class UserStatistics(BaseSchema):
    """用户统计信息"""
    total_users: int = Field(description="总用户数")
    active_users: int = Field(description="活跃用户数")
    role_distribution: Dict[str, int] = Field(description="角色分布")
    status_distribution: Dict[str, int] = Field(description="状态分布")
    recent_registrations: int = Field(description="近期注册数")
    avg_login_frequency: float = Field(description="平均登录频率")


class UserQuery(BaseSchema):
    """用户查询参数"""
    username: Optional[str] = Field(default=None, description="用户名关键词")
    email: Optional[str] = Field(default=None, description="邮箱关键词")
    full_name: Optional[str] = Field(default=None, description="全名关键词")
    role: Optional[UserRole] = Field(default=None, description="用户角色")
    status: Optional[UserStatus] = Field(default=None, description="用户状态")
    created_start: Optional[datetime] = Field(default=None, description="创建开始时间")
    created_end: Optional[datetime] = Field(default=None, description="创建结束时间")
    last_login_start: Optional[datetime] = Field(default=None, description="最后登录开始时间")
    last_login_end: Optional[datetime] = Field(default=None, description="最后登录结束时间")


class Permission(BaseSchema):
    """权限模型"""
    permission_id: str = Field(description="权限ID")
    name: str = Field(description="权限名称")
    description: str = Field(description="权限描述")
    resource: str = Field(description="资源类型")
    action: str = Field(description="操作类型")


class RolePermission(BaseSchema):
    """角色权限关联"""
    role: UserRole = Field(description="用户角色")
    permissions: List[Permission] = Field(description="权限列表")


class UserProfile(BaseSchema):
    """用户档案"""
    user: UserResponse = Field(description="用户信息")
    permissions: List[Permission] = Field(description="用户权限")
    recent_activities: List[UserActivity] = Field(description="最近活动")
    statistics: Dict[str, Any] = Field(description="用户统计")