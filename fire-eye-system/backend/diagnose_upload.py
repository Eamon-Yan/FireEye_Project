#!/usr/bin/env python3
"""
诊断文档上传和数据保存流程
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from app.db.neo4j_manager import neo4j_manager
from app.services.graph_service import graph_service


async def diagnose():
    """诊断数据库状态"""
    print("=" * 60)
    print("🔍 FireEye 数据库诊断工具")
    print("=" * 60)
    print()
    
    try:
        # 1. 连接数据库
        print("📡 步骤 1: 连接数据库...")
        await neo4j_manager.connect()
        print("✅ 数据库连接成功")
        print()
        
        # 2. 检查数据库状态
        print("📊 步骤 2: 检查数据库状态...")
        stats = await neo4j_manager.get_graph_statistics()
        
        print(f"   节点总数: {stats.node_count}")
        print(f"   关系总数: {stats.relationship_count}")
        print(f"   平均度数: {stats.avg_degree:.2f}")
        print()
        
        # 3. 检查节点类型分布
        print("📈 步骤 3: 节点类型分布...")
        if stats.node_type_distribution:
            for node_type, count in stats.node_type_distribution.items():
                print(f"   {node_type}: {count} 个")
        else:
            print("   ⚠️  没有节点数据")
        print()
        
        # 4. 检查关系类型分布
        print("🔗 步骤 4: 关系类型分布...")
        if stats.relationship_type_distribution:
            for rel_type, count in stats.relationship_type_distribution.items():
                print(f"   {rel_type}: {count} 个")
        else:
            print("   ⚠️  没有关系数据")
        print()
        
        # 5. 检查最近创建的节点
        print("🆕 步骤 5: 最近创建的节点（前5个）...")
        recent_nodes_query = """
        MATCH (n)
        RETURN n.id as id, labels(n) as labels, n.description as description, n.created_at as created_at
        ORDER BY n.created_at DESC
        LIMIT 5
        """
        recent_nodes = await neo4j_manager.execute_query(recent_nodes_query)
        
        if recent_nodes:
            for node in recent_nodes:
                labels = node['labels'][0] if node['labels'] else 'Unknown'
                desc = node['description'][:50] if node['description'] else 'N/A'
                print(f"   [{labels}] {desc}...")
        else:
            print("   ⚠️  没有节点")
        print()
        
        # 6. 检查最近创建的关系
        print("🔗 步骤 6: 最近创建的关系（前5个）...")
        recent_rels_query = """
        MATCH (a)-[r]->(b)
        RETURN a.description as source, type(r) as relation, b.description as target, r.created_at as created_at
        ORDER BY r.created_at DESC
        LIMIT 5
        """
        recent_rels = await neo4j_manager.execute_query(recent_rels_query)
        
        if recent_rels:
            for rel in recent_rels:
                source = rel['source'][:30] if rel['source'] else 'N/A'
                target = rel['target'][:30] if rel['target'] else 'N/A'
                relation = rel['relation']
                print(f"   {source}... -> [{relation}] -> {target}...")
        else:
            print("   ⚠️  没有关系")
        print()
        
        # 7. 诊断结果
        print("=" * 60)
        print("📋 诊断结果:")
        print("=" * 60)
        
        if stats.node_count == 0:
            print("❌ 问题: 数据库中没有节点数据")
            print()
            print("可能的原因:")
            print("1. 文档上传后没有成功保存到数据库")
            print("2. 后端服务在处理时出错")
            print("3. Neo4j数据库连接问题")
            print()
            print("建议操作:")
            print("1. 检查后端日志，查看是否有错误信息")
            print("2. 确认后端服务正在运行")
            print("3. 重新上传测试文档")
            print("4. 查看浏览器控制台是否有错误")
        else:
            print("✅ 数据库中有数据")
            print()
            print(f"   总节点数: {stats.node_count}")
            print(f"   总关系数: {stats.relationship_count}")
            print()
            
            # 检查节点类型分布是否合理
            if stats.node_type_distribution:
                fire_event_count = stats.node_type_distribution.get('FireEvent', 0)
                hazard_count = stats.node_type_distribution.get('Hazard', 0)
                consequence_count = stats.node_type_distribution.get('Consequence', 0)
                
                total = fire_event_count + hazard_count + consequence_count
                
                if total == stats.node_count:
                    print("✅ 节点分类正常")
                    print(f"   🔴 FireEvent: {fire_event_count} ({fire_event_count/total*100:.1f}%)")
                    print(f"   🟠 Hazard: {hazard_count} ({hazard_count/total*100:.1f}%)")
                    print(f"   🟣 Consequence: {consequence_count} ({consequence_count/total*100:.1f}%)")
                    
                    if fire_event_count == stats.node_count:
                        print()
                        print("⚠️  警告: 所有节点都是 FireEvent 类型")
                        print("   这可能意味着节点分类逻辑没有生效")
                        print("   建议: 清空数据库并重启后端服务后重新上传")
                else:
                    print("⚠️  发现其他类型的节点")
        
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await neo4j_manager.disconnect()
        print("🔌 数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(diagnose())
