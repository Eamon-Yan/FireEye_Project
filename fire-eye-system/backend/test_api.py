#!/usr/bin/env python3
"""
测试后端API是否正常工作
"""

import requests
import json

print("=" * 60)
print("🧪 测试后端API")
print("=" * 60)
print()

base_url = "http://localhost:8000"

# 测试1: 健康检查
print("📡 测试 1: 后端健康检查...")
try:
    response = requests.get(f"{base_url}/health", timeout=5)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ 后端服务正常")
    else:
        print(f"   ❌ 后端服务异常: {response.text}")
except Exception as e:
    print(f"   ❌ 无法连接到后端: {e}")
    print("   请确保后端服务正在运行！")
    exit(1)

print()

# 测试2: 图数据库健康检查
print("📊 测试 2: 图数据库健康检查...")
try:
    response = requests.get(f"{base_url}/api/v1/graph/health", timeout=5)
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        if data.get('data', {}).get('healthy'):
            print("   ✅ 图数据库连接正常")
        else:
            print("   ❌ 图数据库连接异常")
    else:
        print(f"   ❌ 请求失败: {response.text}")
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

print()

# 测试3: 查询图数据
print("🔍 测试 3: 查询图数据...")
try:
    response = requests.get(
        f"{base_url}/api/v1/graph/query",
        params={"limit": 10, "include_relationships": True},
        timeout=10
    )
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   状态: {data.get('status')}")
        print(f"   消息: {data.get('message')}")
        
        graph_data = data.get('data', {})
        nodes = graph_data.get('nodes', [])
        links = graph_data.get('links', [])
        
        print(f"   节点数: {len(nodes)}")
        print(f"   关系数: {len(links)}")
        
        if len(nodes) > 0:
            print("   ✅ 成功获取图数据")
            print(f"\n   前3个节点:")
            for i, node in enumerate(nodes[:3]):
                print(f"      {i+1}. [{node.get('type')}] {node.get('description', '')[:50]}...")
        else:
            print("   ⚠️  数据库中没有数据")
            print("   这可能是因为:")
            print("      1. 数据库被清空了")
            print("      2. 文档上传失败")
            print("      3. 数据没有正确保存")
    else:
        print(f"   ❌ 请求失败: {response.text}")
        
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

print()

# 测试4: 获取统计信息
print("📈 测试 4: 获取统计信息...")
try:
    response = requests.get(f"{base_url}/api/v1/graph/statistics", timeout=5)
    print(f"   状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        stats = data.get('data', {})
        
        print(f"   节点总数: {stats.get('node_count', 0)}")
        print(f"   关系总数: {stats.get('relationship_count', 0)}")
        
        node_dist = stats.get('node_type_distribution', {})
        if node_dist:
            print(f"   节点类型分布:")
            for node_type, count in node_dist.items():
                print(f"      {node_type}: {count}")
        
        if stats.get('node_count', 0) > 0:
            print("   ✅ 数据库中有数据")
        else:
            print("   ⚠️  数据库为空")
    else:
        print(f"   ❌ 请求失败: {response.text}")
        
except Exception as e:
    print(f"   ❌ 请求失败: {e}")

print()
print("=" * 60)
print("📋 测试总结:")
print("=" * 60)
print()
print("如果所有测试都通过但前端仍然显示空白，请:")
print("1. 清除浏览器缓存（Ctrl+Shift+Delete）")
print("2. 使用无痕模式访问")
print("3. 检查浏览器控制台的Network标签页")
print("4. 确认前端正在访问正确的API地址")
print()
