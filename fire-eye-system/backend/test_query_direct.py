#!/usr/bin/env python3
"""
直接测试查询逻辑（不通过HTTP）
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🔍 直接测试查询逻辑")
print("=" * 60)
print()

async def test_query():
    try:
        print("1. 导入模块...")
        from app.db.neo4j_manager import neo4j_manager
        print("✅ 导入成功")
        print()
        
        print("2. 连接数据库...")
        await neo4j_manager.connect()
        print("✅ 连接成功")
        print()
        
        print("3. 执行查询...")
        node_query = """
            MATCH (n)
            RETURN n, labels(n) as node_labels
            LIMIT 10
        """
        
        node_records = await neo4j_manager.execute_query(node_query, {"limit": 10})
        print(f"✅ 查询成功，返回 {len(node_records)} 条记录")
        print()
        
        print("4. 处理节点数据...")
        nodes = []
        for i, record in enumerate(node_records):
            try:
                node_data = record.get("n", {})
                node_labels = record.get("node_labels", [])
                
                node_id = node_data.get("id", "unknown")
                node_type = node_labels[0] if node_labels else "Unknown"
                description = node_data.get("description", node_data.get("standard_term", node_id))
                
                print(f"   节点 {i+1}: {node_type} - {description[:50]}...")
                
                nodes.append({
                    "id": node_id,
                    "type": node_type,
                    "description": description
                })
                
            except Exception as e:
                print(f"   ❌ 处理节点 {i+1} 失败: {e}")
                continue
        
        print()
        print(f"✅ 成功处理 {len(nodes)} 个节点")
        print()
        
        print("5. 查询关系...")
        if nodes:
            node_ids = [n["id"] for n in nodes]
            rel_query = """
                MATCH (a)-[r]->(b)
                WHERE a.id IN $node_ids AND b.id IN $node_ids
                RETURN type(r) as rel_type, a.id as source_id, b.id as target_id
                LIMIT 20
            """
            
            rel_records = await neo4j_manager.execute_query(rel_query, {"node_ids": node_ids})
            print(f"✅ 查询成功，返回 {len(rel_records)} 个关系")
            
            for i, record in enumerate(rel_records[:5]):
                rel_type = record.get("rel_type", "UNKNOWN")
                source = record.get("source_id", "?")[:20]
                target = record.get("target_id", "?")[:20]
                print(f"   关系 {i+1}: {source}... -> {target}... ({rel_type})")
        
        print()
        print("=" * 60)
        print("✅ 所有测试通过！查询逻辑正常")
        print("=" * 60)
        
        await neo4j_manager.disconnect()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query())
