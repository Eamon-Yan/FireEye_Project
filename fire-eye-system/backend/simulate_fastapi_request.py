#!/usr/bin/env python3
"""
模拟FastAPI完整请求处理流程
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🔍 模拟FastAPI请求处理")
print("=" * 60)
print()

async def simulate_request():
    try:
        print("1. 导入所有必要模块...")
        from app.api.v1.endpoints.graph import query_graph_data, router
        from app.services.graph_service import graph_service
        from app.schemas import BaseResponse, ResponseStatus
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        print("✅ 导入成功")
        print()
        
        print("2. 创建测试应用...")
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/graph")
        print("✅ 应用创建成功")
        print()
        
        print("3. 创建测试客户端...")
        client = TestClient(app)
        print("✅ 客户端创建成功")
        print()
        
        print("4. 发送测试请求...")
        response = client.get("/api/v1/graph/query", params={"limit": 5})
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ 请求成功!")
            data = response.json()
            print(f"   状态: {data.get('status')}")
            print(f"   消息: {data.get('message')}")
            
            if data.get('data'):
                nodes = data['data'].get('nodes', [])
                links = data['data'].get('links', [])
                print(f"   节点数: {len(nodes)}")
                print(f"   关系数: {len(links)}")
        else:
            print(f"   ❌ 请求失败!")
            print(f"   响应: {response.text}")
            print(f"   响应头: {dict(response.headers)}")
        
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 模拟失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simulate_request())
