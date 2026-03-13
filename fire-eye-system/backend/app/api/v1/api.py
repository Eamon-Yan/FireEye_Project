"""
API v1 主路由配置
"""

from fastapi import APIRouter

from app.api.v1.endpoints import graph, documents, chat

# 创建 API 路由器
api_router = APIRouter()

# 注册图数据库路由
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])

# 注册文档管理路由
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# 注册聊天 API 路由（AstrBot 集成）
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# 占位路由
@api_router.get("/")
async def api_root():
    """API 根路径"""
    return {
        "message": "火瞳系统 API v1", 
        "version": "1.0.0",
        "endpoints": {
            "graph": "/graph - 图数据库操作",
            "documents": "/documents - 文档管理和解析",
            "chat": "/chat - 聊天平台集成 API",
            "health": "/graph/health - 图数据库健康检查"
        }
    }

# TODO: 在后续任务中添加以下路由模块
# from app.api.v1.endpoints import extraction, validation, prediction
# 
# api_router.include_router(extraction.router, prefix="/extraction", tags=["extraction"])
# api_router.include_router(validation.router, prefix="/validation", tags=["validation"])
# api_router.include_router(prediction.router, prefix="/prediction", tags=["prediction"])