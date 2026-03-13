#!/usr/bin/env python3
"""
测试修复后的查询接口
"""

import requests
import json

# 配置
API_URL = "http://localhost:8000/api/v1/chat/query"
API_KEY = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"

# 测试数据
test_queries = [
    {"query": "火灾"},
    {"query": "test"},
    {"query": "火灾事故"},
]

print("=" * 50)
print("测试查询接口")
print("=" * 50)
print()

for i, data in enumerate(test_queries, 1):
    print(f"测试 {i}: {data['query']}")
    print("-" * 50)
    
    try:
        response = requests.post(
            API_URL,
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json"
            },
            json=data,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 成功")
            print(f"会话ID: {result.get('data', {}).get('session_id', 'N/A')}")
            print(f"结果数量: {len(result.get('data', {}).get('results', []))}")
        else:
            print("❌ 失败")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print()

print("=" * 50)
print("测试完成")
print("=" * 50)
