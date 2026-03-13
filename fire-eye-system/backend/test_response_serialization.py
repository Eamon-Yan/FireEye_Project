#!/usr/bin/env python3
"""
测试响应序列化
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🔍 测试响应序列化")
print("=" * 60)
print()

try:
    print("1. 导入模块...")
    from app.schemas import BaseResponse, ResponseStatus
    print("✅ 导入成功")
    print()
    
    print("2. 创建简单响应...")
    response1 = BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="测试消息",
        data={"test": "data"}
    )
    print("✅ 创建成功")
    print(f"   {response1}")
    print()
    
    print("3. 序列化为JSON...")
    json_data = response1.model_dump()
    print("✅ 序列化成功")
    print(f"   {json_data}")
    print()
    
    print("4. 创建复杂响应（模拟查询结果）...")
    response2 = BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="查询成功，返回 2 个节点，1 个关系",
        data={
            "nodes": [
                {
                    "id": "node1",
                    "type": "FireEvent",
                    "description": "测试节点1",
                    "properties": {"key": "value"}
                },
                {
                    "id": "node2",
                    "type": "Hazard",
                    "description": "测试节点2",
                    "properties": {"key": "value"}
                }
            ],
            "links": [
                {
                    "source": "node1",
                    "target": "node2",
                    "relation": "CAUSES",
                    "confidence": 0.9
                }
            ]
        }
    )
    print("✅ 创建成功")
    print()
    
    print("5. 序列化复杂响应...")
    json_data2 = response2.model_dump()
    print("✅ 序列化成功")
    print(f"   节点数: {len(json_data2['data']['nodes'])}")
    print(f"   关系数: {len(json_data2['data']['links'])}")
    print()
    
    print("6. 转换为JSON字符串...")
    import json
    json_str = json.dumps(json_data2, ensure_ascii=False, default=str)
    print("✅ 转换成功")
    print(f"   长度: {len(json_str)} 字符")
    print()
    
    print("=" * 60)
    print("✅ 所有序列化测试通过！")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
