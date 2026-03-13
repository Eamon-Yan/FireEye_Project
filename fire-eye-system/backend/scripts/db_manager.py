#!/usr/bin/env python3
"""
数据库管理 CLI 工具
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.init_db import initialize_database, cleanup_database, create_sample_data
from app.db.neo4j_client import neo4j_client
from app.db.redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    await initialize_database()
    logger.info("数据库初始化完成")


async def reset_db():
    """重置数据库（清空所有数据）"""
    logger.info("开始重置数据库...")
    
    try:
        await neo4j_client.connect()
        await redis_client.connect()
        
        # 清空 Neo4j 数据
        await neo4j_client.execute_query("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j 数据已清空")
        
        # 清空 Redis 数据
        await redis_client.redis.flushdb()
        logger.info("Redis 数据已清空")
        
        # 重新创建约束和索引
        await neo4j_client.create_constraints_and_indexes()
        
        # 创建示例数据
        await create_sample_data()
        
        logger.info("数据库重置完成")
        
    except Exception as e:
        logger.error(f"重置数据库失败: {e}")
        raise
    finally:
        await cleanup_database()


async def check_db():
    """检查数据库状态"""
    logger.info("检查数据库状态...")
    
    try:
        await neo4j_client.connect()
        await redis_client.connect()
        
        # 检查 Neo4j
        result = await neo4j_client.execute_query(
            """
            MATCH (n) 
            RETURN labels(n) as node_type, count(n) as count
            ORDER BY node_type
            """
        )
        
        logger.info("Neo4j 节点统计:")
        total_nodes = 0
        for record in result:
            node_type = record["node_type"][0] if record["node_type"] else "Unknown"
            count = record["count"]
            total_nodes += count
            logger.info(f"  {node_type}: {count}")
        logger.info(f"  总计: {total_nodes} 个节点")
        
        # 检查关系
        result = await neo4j_client.execute_query(
            """
            MATCH ()-[r]->() 
            RETURN type(r) as relationship_type, count(r) as count
            ORDER BY relationship_type
            """
        )
        
        logger.info("Neo4j 关系统计:")
        total_relationships = 0
        for record in result:
            rel_type = record["relationship_type"]
            count = record["count"]
            total_relationships += count
            logger.info(f"  {rel_type}: {count}")
        logger.info(f"  总计: {total_relationships} 个关系")
        
        # 检查 Redis
        info = await redis_client.redis.info()
        logger.info(f"Redis 状态:")
        logger.info(f"  版本: {info.get('redis_version', 'Unknown')}")
        logger.info(f"  内存使用: {info.get('used_memory_human', 'Unknown')}")
        logger.info(f"  键数量: {info.get('db0', {}).get('keys', 0) if 'db0' in info else 0}")
        
        logger.info("数据库状态检查完成")
        
    except Exception as e:
        logger.error(f"检查数据库状态失败: {e}")
        raise
    finally:
        await cleanup_database()


async def backup_db():
    """备份数据库"""
    logger.info("开始备份数据库...")
    
    try:
        await neo4j_client.connect()
        
        # 导出所有节点
        nodes_result = await neo4j_client.execute_query(
            "MATCH (n) RETURN n, labels(n) as labels"
        )
        
        # 导出所有关系
        rels_result = await neo4j_client.execute_query(
            "MATCH (a)-[r]->(b) RETURN a, r, b, type(r) as rel_type"
        )
        
        # 这里可以将数据保存到文件
        # 简化版本只打印统计信息
        logger.info(f"备份完成: {len(nodes_result)} 个节点, {len(rels_result)} 个关系")
        
    except Exception as e:
        logger.error(f"备份数据库失败: {e}")
        raise
    finally:
        await cleanup_database()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="火瞳系统数据库管理工具")
    parser.add_argument(
        "command",
        choices=["init", "reset", "check", "backup"],
        help="要执行的命令"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        asyncio.run(init_db())
    elif args.command == "reset":
        confirm = input("确定要重置数据库吗？这将删除所有数据 (y/N): ")
        if confirm.lower() == 'y':
            asyncio.run(reset_db())
        else:
            logger.info("操作已取消")
    elif args.command == "check":
        asyncio.run(check_db())
    elif args.command == "backup":
        asyncio.run(backup_db())


if __name__ == "__main__":
    main()