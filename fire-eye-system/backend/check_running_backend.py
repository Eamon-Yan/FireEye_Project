#!/usr/bin/env python3
"""
检查正在运行的后端版本
"""

import requests
import json

print("=" * 60)
print("🔍 检查正在运行的后端")
print("=" * 60)
print()

# 测试健康检查
print("1. 测试后端健康检查...")
try:
    response = requests.get("http://localhost:8000/api/v1/graph/health", timeout=5)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ 后端正在运行")
    print()
except Exception as e:
    print(f"   ❌ 后端未运行: {e}")
    print()
    exit(1)

# 测试查询端点
print("2. 测试查询端点...")
try:
    response = requests.get(
        "http://localhost:8000/api/v1/graph/query",
        params={"limit": 5, "include_relationships": True},
        timeout=10
    )
    
    print(f"   状态码: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    print()
    
    if response.status_code == 200:
        print("   ✅ 查询成功!")
        data = response.json()
        print(f"   状态: {data.get('status')}")
        print(f"   消息: {data.get('message')}")
        
        if data.get('data'):
            nodes = data['data'].get('nodes', [])
            links = data['data'].get('links', [])
            print(f"   节点数: {len(nodes)}")
            print(f"   关系数: {len(links)}")
    else:
        print(f"   ❌ 查询失败!")
        print(f"   响应内容: {response.text[:200]}")
        
except Exception as e:
    print(f"   ❌ 请求异常: {e}")
    import traceback
    traceback.print_exc()

print()

# 检查路由列表
print("3. 检查可用路由...")
try:
    response = requests.get("http://localhost:8000/openapi.json", timeout=5)
    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get('paths', {})
        
        graph_routes = [p for p in paths.keys() if '/graph/' in p]
        print(f"   图数据库路由数量: {len(graph_routes)}")
        
        if '/api/v1/graph/query' in paths:
            print("   ✅ /query 路由存在")
            query_info = paths['/api/v1/graph/query']
            print(f"   支持的方法: {list(query_info.keys())}")
        else:
            print("   ❌ /query 路由不存在")
            
except Exception as e:
    print(f"   ⚠️  无法获取路由信息: {e}")

print()
print("=" * 60)
