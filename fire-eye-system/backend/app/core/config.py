"""
应用配置设置
"""

from typing import List, Optional, Union
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """应用配置类"""
    
    # API 配置
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "火瞳系统"
    
    # 服务器配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # CORS 配置
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    # 受信任主机
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Neo4j 数据库配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"
    
    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # LLM API 配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.deepseek.com"
    OPENAI_API_BASE: Optional[str] = None  # Alternative base URL field
    OPENAI_MODEL: str = "deepseek-chat"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: Path = Path("uploads")
    ALLOWED_FILE_TYPES: List[str] = [".pdf", ".docx", ".txt"]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 前端配置
    NEXT_PUBLIC_API_URL: Optional[str] = None
    NEXT_PUBLIC_APP_NAME: Optional[str] = None
    
    # AstrBot 集成配置
    ASTRBOT_API_KEYS: Union[List[str], str] = []
    
    # 开发环境配置
    DEBUG: bool = True
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle JSON array string format
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Fallback to comma-separated parsing
                    v = v.strip("[]").replace('"', '').replace("'", "")
                    return [i.strip() for i in v.split(",") if i.strip()]
            else:
                # Handle comma-separated string format
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []
    
    @field_validator("ASTRBOT_API_KEYS", mode="before")
    @classmethod
    def assemble_api_keys(cls, v):
        """解析 API Keys 配置"""
        if isinstance(v, str):
            # Handle JSON array string format
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Fallback to comma-separated parsing
                    v = v.strip("[]").replace('"', '').replace("'", "")
                    return [i.strip() for i in v.split(",") if i.strip()]
            else:
                # Handle comma-separated string format
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# 创建全局配置实例
settings = Settings()
