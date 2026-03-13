#!/usr/bin/env python3
"""
触发错误并获取详细信息
"""

import requests
import json

print("=" * 60)
print("🔍 触发错误并获取详细信息")
print("=" * 60)
print()

url = "http://localhost:8000/api/v1/graph/query"

print(f"请求URL: {url}")
print()

# 尝试不同的参数组合
test_cases = [
    {"limit": 1, "include_relationships": False},
    {"limit": 1, "include_relationships": True},
    {},
]

for i, params in enumerate(test_cases, 1):
    print(f"测试 {i}: 参数 = {params}")
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功: {data.get('message')}")
        else:
            print(f"  ❌ 失败")
            print(f"  响应头: {dict(response.headers)}")
            print(f"  响应内容: {response.text}")
            
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    
    print()

# 尝试访问其他端点看是否正常
print("=" * 60)
print("测试其他端点:")
print("=" * 60)
print()

other_endpoints = [
    "/api/v1/graph/health",
    "/api/v1/graph/statistics",
]

for endpoint in other_endpoints:
    url = f"http://localhost:8000{endpoint}"
    print(f"测试: {endpoint}")
    try:
        response = requests.get(url, timeout=5)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ 成功")
        else:
            print(f"  ❌ 失败: {response.text[:100]}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    print()
