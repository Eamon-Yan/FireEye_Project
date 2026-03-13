#!/usr/bin/env python3
"""
检查后端启动错误
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🔍 检查后端代码语法")
print("=" * 60)
print()

try:
    print("正在导入 graph.py 模块...")
    from app.api.v1.endpoints import graph
    print("✅ graph.py 导入成功")
    print()
    
    # 检查路由
    print("检查路由定义...")
    router = graph.router
    print(f"✅ 路由器对象: {router}")
    print(f"✅ 路由数量: {len(router.routes)}")
    print()
    
    print("路由列表:")
    for route in router.routes:
        print(f"  - {route.methods} {route.path}")
    
except SyntaxError as e:
    print(f"❌ 语法错误: {e}")
    print(f"   文件: {e.filename}")
    print(f"   行号: {e.lineno}")
    print(f"   内容: {e.text}")
    import traceback
    traceback.print_exc()
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    import traceback
    traceback.print_exc()
    
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
