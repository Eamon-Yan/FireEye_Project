#!/usr/bin/env python3
"""
完整的 QQ 插件功能测试
"""

import asyncio
import aiohttp
import json
from loguru import logger

logger.add("test_qq_plugin_complete.log", level="DEBUG")


class QQPluginTester:
    def __init__(self):
        self.api_url = "http://127.0.0.1:8000/api/v1"
        self.api_key = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
        self.session_id = None
        
    async def test_query(self, query_text: str):
        """测试查询功能"""
        print(f"\n📝 测试查询: '{query_text}'")
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "query": query_text,
                    "session_id": self.session_id
                }
                
                async with session.post(
                    f"{self.api_url}/chat/query",
                    json=payload,
                    headers={
                        "X-API-Key": self.api_key,
                        "Content-Type": "application/json"
                    }
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # 保存 session_id
                        if data.get("data", {}).get("session_id"):
                            self.session_id = data["data"]["session_id"]
                        
                        results = data.get("data", {}).get("results", [])
                        print(f"   ✅ 查询成功，找到 {len(results)} 条结果")
                        
                        for i, result in enumerate(results[:3], 1):
                            print(f"      {i}. [{result.get('type')}] {result.get('name')}")
                            if result.get('description'):
                                print(f"         {result.get('description')}")
                        
                        if len(results) > 3:
                            print(f"      ... 还有 {len(results) - 3} 条结果")
                        
                        return True
                    else:
                        data = await resp.json()
                        print(f"   ❌ 查询失败: {data.get('detail', '未知错误')}")
                        return False
                        
        except Exception as e:
            print(f"   ❌ 查询异常: {e}")
            return False
    
    async def test_stats(self):
        """测试统计功能"""
        print(f"\n📊 测试统计功能")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/chat/stats",
                    headers={"X-API-Key": self.api_key}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        stats = data.get("data", {})
                        
                        print(f"   ✅ 统计成功")
                        print(f"      • 事件总数: {stats.get('total_events', 0)}")
                        print(f"      • 实体总数: {stats.get('total_entities', 0)}")
                        print(f"      • 关系总数: {stats.get('total_relationships', 0)}")
                        
                        node_types = stats.get('node_types', {})
                        if node_types:
                            print(f"      • 节点类型:")
                            for node_type, count in node_types.items():
                                print(f"        - {node_type}: {count}")
                        
                        return True
                    else:
                        data = await resp.json()
                        print(f"   ❌ 统计失败: {data.get('detail', '未知错误')}")
                        return False
                        
        except Exception as e:
            print(f"   ❌ 统计异常: {e}")
            return False
    
    async def test_multi_turn_conversation(self):
        """测试多轮对话"""
        print(f"\n💬 测试多轮对话")
        
        # 第一轮
        print(f"\n   第一轮: 查询 '火灾'")
        result1 = await self.test_query("火灾")
        
        if not result1:
            print(f"   ❌ 多轮对话测试失败")
            return False
        
        # 第二轮 - 使用相同的 session_id
        print(f"\n   第二轮: 查询 '电气' (使用相同会话)")
        result2 = await self.test_query("电气")
        
        if result2:
            print(f"   ✅ 多轮对话成功")
            return True
        else:
            print(f"   ❌ 多轮对话失败")
            return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("🔥 火瞳 QQ 插件完整功能测试")
    print("=" * 60)
    
    tester = QQPluginTester()
    
    # 测试 1: 基本查询
    print("\n【测试 1】基本查询功能")
    print("-" * 60)
    test1 = await tester.test_query("火灾")
    
    # 测试 2: 统计功能
    print("\n【测试 2】统计功能")
    print("-" * 60)
    test2 = await tester.test_stats()
    
    # 测试 3: 多轮对话
    print("\n【测试 3】多轮对话")
    print("-" * 60)
    test3 = await tester.test_multi_turn_conversation()
    
    # 测试 4: 不同查询
    print("\n【测试 4】不同查询")
    print("-" * 60)
    test4 = await tester.test_query("电气短路")
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 测试总结")
    print("=" * 60)
    print(f"  基本查询:     {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"  统计功能:     {'✅ 通过' if test2 else '❌ 失败'}")
    print(f"  多轮对话:     {'✅ 通过' if test3 else '❌ 失败'}")
    print(f"  不同查询:     {'✅ 通过' if test4 else '❌ 失败'}")
    
    all_passed = test1 and test2 and test3 and test4
    print(f"\n  总体结果:     {'✅ 全部通过' if all_passed else '❌ 部分失败'}")
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 QQ 插件功能完全正常！")
        print("\n配置说明:")
        print("  • API URL: http://127.0.0.1:8000/api/v1")
        print("  • API Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA")
        print("\n在 QQ 中使用:")
        print("  • /火瞳查询 <关键词>  - 查询知识图谱")
        print("  • /火瞳统计          - 获取统计信息")
        print("  • /火瞳帮助          - 显示帮助信息")
    else:
        print("\n⚠️  QQ 插件存在问题，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())
