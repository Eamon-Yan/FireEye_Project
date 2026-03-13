#!/usr/bin/env python3
"""
快速清空Neo4j数据库脚本
用于测试新的节点分类逻辑
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.db.neo4j_manager import neo4j_manager


async def clear_all_data():
    """清空所有Neo4j数据"""
    print("🔥 开始清空Neo4j数据库...")
    
    try:
        # 连接数据库
        await neo4j_manager.connect()
        print("✅ 数据库连接成功")
        
        # 获取清空前的统计信息
        stats_before = await neo4j_manager.get_graph_statistics()
        print(f"\n📊 清空前统计:")
        print(f"   节点数: {stats_before.node_count}")
        print(f"   关系数: {stats_before.relationship_count}")
        print(f"   节点类型分布: {stats_before.node_type_distribution}")
        
        # 清空所有数据
        print("\n🗑️  正在删除所有节点和关系...")
        await neo4j_manager.execute_query("MATCH (n) DETACH DELETE n")
        
        # 获取清空后的统计信息
        stats_after = await neo4j_manager.get_graph_statistics()
        print(f"\n✅ 数据库已清空!")
        print(f"   当前节点数: {stats_after.node_count}")
        print(f"   当前关系数: {stats_after.relationship_count}")
        
        print("\n💡 提示: 现在可以重新上传测试文档来验证新的节点分类逻辑")
        
    except Exception as e:
        print(f"\n❌ 清空数据库失败: {e}")
        raise
    finally:
        await neo4j_manager.disconnect()
        print("\n🔌 数据库连接已关闭")


if __name__ == "__main__":
    print("=" * 60)
    print("🔥 FireEye 数据库清空工具")
    print("=" * 60)
    
    confirm = input("\n⚠️  确定要清空所有数据吗？此操作不可恢复！(输入 yes 确认): ")
    
    if confirm.lower() == 'yes':
        asyncio.run(clear_all_data())
    else:
        print("\n❌ 操作已取消")
