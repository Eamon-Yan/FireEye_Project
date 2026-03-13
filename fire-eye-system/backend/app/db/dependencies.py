"""
数据库依赖注入
"""

from typing import AsyncGenerator
from fastapi import Depends

from app.db.neo4j_client import neo4j_client, Neo4jClient
from app.db.neo4j_manager import neo4j_manager, Neo4jManager
from app.db.redis_client import redis_client, RedisClient
from app.services.graph_service import graph_service, GraphService


async def get_neo4j_client() -> AsyncGenerator[Neo4jClient, None]:
    """获取 Neo4j 客户端依赖（低级接口）"""
    try:
        if not neo4j_client.driver:
            await neo4j_client.connect()
        yield neo4j_client
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Neo4j客户端连接失败: {e}")
        yield neo4j_client


async def get_neo4j_manager() -> AsyncGenerator[Neo4jManager, None]:
    """获取 Neo4j 管理器依赖（高级接口）"""
    try:
        if not neo4j_manager.driver:
            await neo4j_manager.connect()
        yield neo4j_manager
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Neo4j管理器连接失败: {e}")
        yield neo4j_manager


async def get_graph_service() -> AsyncGenerator[GraphService, None]:
    """获取图服务依赖（业务层接口）"""
    try:
        await graph_service.initialize()
        yield graph_service
    except Exception as e:
        # 记录错误但不重新抛出，让调用者处理
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"图服务初始化失败: {e}")
        # 仍然yield服务实例，让端点处理错误
        yield graph_service


async def get_redis_client() -> AsyncGenerator[RedisClient, None]:
    """获取 Redis 客户端依赖"""
    try:
        if not redis_client.redis:
            await redis_client.connect()
        yield redis_client
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Redis客户端连接失败: {e}")
        yield redis_client


# 便捷的依赖注入别名
Neo4jClientDep = Depends(get_neo4j_client)
Neo4jManagerDep = Depends(get_neo4j_manager)
GraphServiceDep = Depends(get_graph_service)
RedisDep = Depends(get_redis_client)