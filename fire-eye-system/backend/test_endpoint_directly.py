#!/usr/bin/env python3
"""
直接测试端点函数（模拟HTTP请求）
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🔍 直接测试端点函数")
print("=" * 60)
print()

async def test_endpoint():
    try:
        print("1. 导入模块...")
        from app.api.v1.endpoints.graph import query_graph_data
        from app.services.graph_service import graph_service
        print("✅ 导入成功")
        print()
        
        print("2. 初始化服务...")
        await graph_service.initialize()
        print("✅ 初始化成功")
        print()
        
        print("3. 调用查询端点...")
        result = await query_graph_data(
            node_types=None,
            search_text=None,
            limit=10,
            include_relationships=True,
            graph_service=graph_service
        )
        
        print("✅ 端点调用成功")
        print()
        
        print("4. 检查返回结果...")
        print(f"   状态: {result.status}")
        print(f"   消息: {result.message}")
        
        if result.data:
            nodes = result.data.get("nodes", [])
            links = result.data.get("links", [])
            print(f"   节点数: {len(nodes)}")
            print(f"   关系数: {len(links)}")
            
            if nodes:
                print()
                print("   前3个节点:")
                for i, node in enumerate(nodes[:3]):
                    print(f"     {i+1}. {node.get('type')} - {node.get('description', '')[:50]}...")
        
        print()
        print("=" * 60)
        print("✅ 端点测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
