#!/usr/bin/env python3
"""
测试 QQ 插件的连接和功能
"""

import asyncio
import aiohttp
import json
from loguru import logger

logger.add("test_qq_plugin.log", level="DEBUG")


async def test_backend_connection():
    """测试后端连接"""
    print("\n=== 测试后端连接 ===")
    
    api_url = "http://127.0.0.1:8000/api/v1"
    api_key = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试健康检查
            print(f"\n1. 测试健康检查: GET {api_url}/chat/health")
            async with session.get(
                f"{api_url}/chat/health",
                headers={"X-API-Key": api_key}
            ) as resp:
                print(f"   状态码: {resp.status}")
                data = await resp.json()
                print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if resp.status == 200:
                    print("   ✅ 健康检查成功")
                else:
                    print("   ❌ 健康检查失败")
                    
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False
    
    return True


async def test_query():
    """测试查询功能"""
    print("\n=== 测试查询功能 ===")
    
    api_url = "http://127.0.0.1:8000/api/v1"
    api_key = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试查询
            print(f"\n2. 测试查询: POST {api_url}/chat/query")
            
            payload = {
                "query": "火灾",
                "session_id": None
            }
            
            print(f"   请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            async with session.post(
                f"{api_url}/chat/query",
                json=payload,
                headers={
                    "X-API-Key": api_key,
                    "Content-Type": "application/json"
                }
            ) as resp:
                print(f"   状态码: {resp.status}")
                data = await resp.json()
                print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if resp.status == 200:
                    print("   ✅ 查询成功")
                    return True
                else:
                    print("   ❌ 查询失败")
                    return False
                    
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
        return False


async def test_stats():
    """测试统计功能"""
    print("\n=== 测试统计功能 ===")
    
    api_url = "http://127.0.0.1:8000/api/v1"
    api_key = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
    
    try:
        async with aiohttp.ClientSession() as session:
            # 测试统计
            print(f"\n3. 测试统计: GET {api_url}/chat/stats")
            
            async with session.get(
                f"{api_url}/chat/stats",
                headers={"X-API-Key": api_key}
            ) as resp:
                print(f"   状态码: {resp.status}")
                data = await resp.json()
                print(f"   响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if resp.status == 200:
                    print("   ✅ 统计成功")
                    return True
                else:
                    print("   ❌ 统计失败")
                    return False
                    
    except Exception as e:
        print(f"   ❌ 统计失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("=" * 50)
    print("火瞳 QQ 插件诊断工具")
    print("=" * 50)
    
    # 测试后端连接
    connected = await test_backend_connection()
    
    if not connected:
        print("\n❌ 后端连接失败，请检查:")
        print("   1. 后端是否正在运行")
        print("   2. 后端地址是否正确 (http://127.0.0.1:8000)")
        print("   3. API Key 是否正确")
        return
    
    # 测试查询
    query_ok = await test_query()
    
    # 测试统计
    stats_ok = await test_stats()
    
    print("\n" + "=" * 50)
    print("诊断结果:")
    print(f"  后端连接: ✅")
    print(f"  查询功能: {'✅' if query_ok else '❌'}")
    print(f"  统计功能: {'✅' if stats_ok else '❌'}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
