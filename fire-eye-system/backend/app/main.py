"""
火瞳系统 FastAPI 主应用
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.init_db import initialize_database, cleanup_database

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("正在启动火瞳系统...")
    try:
        await initialize_database()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    
    yield
    
    # 关闭时清理资源
    logger.info("正在关闭火瞳系统...")
    try:
        await cleanup_database()
        logger.info("数据库连接已清理")
    except Exception as e:
        logger.error(f"清理数据库连接失败: {e}")


# 创建 FastAPI 应用实例
app = FastAPI(
    title="火瞳系统 API",
    description="基于Neo4j和LLM的火灾事理图谱Web系统",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置受信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# 注册 API 路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "message": "火瞳系统 API 服务运行正常",
        "version": "0.1.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    from app.db.neo4j_client import neo4j_client
    from app.db.redis_client import redis_client
    
    health_status = {
        "status": "healthy",
        "service": "fire-eye-backend",
        "database": {
            "neo4j": "unknown",
            "redis": "unknown"
        }
    }
    
    # 检查 Neo4j 连接
    try:
        if neo4j_client.driver:
            await neo4j_client.verify_connectivity()
            health_status["database"]["neo4j"] = "connected"
        else:
            health_status["database"]["neo4j"] = "disconnected"
    except Exception:
        health_status["database"]["neo4j"] = "error"
    
    # 检查 Redis 连接
    try:
        if redis_client.redis:
            await redis_client.redis.ping()
            health_status["database"]["redis"] = "connected"
        else:
            health_status["database"]["redis"] = "disconnected"
    except Exception:
        health_status["database"]["redis"] = "error"
    
    # 如果任何数据库连接有问题，整体状态为不健康
    if any(status in ["disconnected", "error"] for status in health_status["database"].values()):
        health_status["status"] = "unhealthy"
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )