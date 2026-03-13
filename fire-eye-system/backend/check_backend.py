#!/usr/bin/env python3
"""
检查后端服务状态
"""

import requests
import sys

print("=" * 60)
print("🔍 检查后端服务状态")
print("=" * 60)
print()

try:
    response = requests.get("http://localhost:8000/api/v1/graph/health", timeout=5)
    
    if response.status_code == 200:
        print("✅ 后端服务正在运行")
        print()
        print("⚠️  代码已修复，但需要重启后端服务才能生效！")
        print()
        print("请按以下步骤操作：")
        print("1. 在运行后端的命令行窗口按 Ctrl+C 停止服务")
        print("2. 重新运行: start-backend.bat")
        print("3. 等待服务启动完成（看到 'Application startup complete'）")
        print("4. 再次运行测试: python test_query_detailed.py")
    else:
        print("⚠️  后端服务响应异常")
        print(f"状态码: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ 后端服务未运行")
    print()
    print("请启动后端服务:")
    print("cd fire-eye-system/backend")
    print("start-backend.bat")
    
except Exception as e:
    print(f"❌ 检查失败: {e}")
    sys.exit(1)

print()
print("=" * 60)
