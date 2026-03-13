"""
API 认证中间件
用于验证 AstrBot 插件的 API Key
"""

import logging
from typing import List
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

logger = logging.getLogger(__name__)

# API Key 认证头
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    验证 API Key
    
    Args:
        api_key: 从请求头中提取的 API Key
        
    Returns:
        验证通过的 API Key
        
    Raises:
        HTTPException: 当 API Key 无效或缺失时
    """
    # 检查是否提供了 API Key
    if not api_key:
        logger.warning("API request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required. Please provide X-API-Key header."
        )
    
    # 获取有效的 API Keys 列表
    valid_keys: List[str] = getattr(settings, 'ASTRBOT_API_KEYS', [])
    
    # 如果没有配置 API Keys，记录警告但允许通过（开发环境）
    if not valid_keys:
        logger.warning("No API keys configured. Authentication bypassed (development mode).")
        return api_key
    
    # 验证 API Key
    if api_key not in valid_keys:
        # 记录失败的认证尝试（只记录前8个字符以保护隐私）
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    # 记录成功的认证
    logger.info(f"API key authenticated: {api_key[:8]}...")
    return api_key
