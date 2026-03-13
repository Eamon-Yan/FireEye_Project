#!/usr/bin/env python3
"""
详细测试查询API并显示错误信息
"""

import requests
import json

print("=" * 60)
print("🔍 详细测试查询API")
print("=" * 60)
print()

url = "http://localhost:8000/api/v1/graph/query"
params = {"limit": 10, "include_relationships": True}

print(f"请求URL: {url}")
print(f"参数: {params}")
print()

try:
    response = requests.get(url, params=params, timeout=10)
    
    print(f"状态码: {response.status_code}")
    print()
    
    if response.status_code == 200:
        print("✅ 请求成功!")
        data = response.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print("❌ 请求失败!")
        print(f"响应头: {dict(response.headers)}")
        print()
        print(f"响应内容:")
        print(response.text)
        
except Exception as e:
    print(f"❌ 请求异常: {e}")
    import traceback
    traceback.print_exc()
