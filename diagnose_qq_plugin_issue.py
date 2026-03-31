#!/usr/bin/env python3
"""
诊断 QQ 插件问题
找出为什么命令在 AstrBot 中失败
"""

import asyncio
import sys
from pathlib import Path

# 添加插件路径到 sys.path
plugin_path = Path(__file__).parent / "astrbot-plugin-fireeye-qq"
sys.path.insert(0, str(plugin_path))


async def test_imports():
    """测试所有导入"""
    print("=" * 60)
    print("测试 1: 检查导入")
    print("=" * 60)
    
    try:
        import yaml
        print("✅ yaml 导入成功")
    except ImportError as e:
        print(f"❌ yaml 导入失败: {e}")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp 导入成功")
    except ImportError as e:
        print(f"❌ aiohttp 导入失败: {e}")
        return False
    
    try:
        from loguru import logger
        print("✅ loguru 导入成功")
    except ImportError as e:
        print(f"❌ loguru 导入失败: {e}")
        return False
    
    return True


async def test_plugin_structure():
    """测试插件结构"""
    print("\n" + "=" * 60)
    print("测试 2: 检查插件结构")
    print("=" * 60)
    
    files_to_check = [
        "astrbot-plugin-fireeye-qq/__init__.py",
        "astrbot-plugin-fireeye-qq/main.py",
        "astrbot-plugin-fireeye-qq/config.yaml",
        "astrbot-plugin-fireeye-qq/api/client.py",
        "astrbot-plugin-fireeye-qq/session/manager.py",
        "astrbot-plugin-fireeye-qq/queue/request_queue.py",
        "astrbot-plugin-fireeye-qq/utils/formatter.py",
    ]
    
    all_exist = True
    for file_path in files_to_check:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"{status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


async def test_api_client():
    """测试 API 客户端"""
    print("\n" + "=" * 60)
    print("测试 3: 测试 API 客户端")
    print("=" * 60)
    
    try:
        from api.client import APIClient
        
        api_url = "http://127.0.0.1:8000/api/v1"
        api_key = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
        
        client = APIClient(api_url=api_url, api_key=api_key, timeout=5)
        print(f"✅ API 客户端创建成功")
        
        # 测试查询
        try:
            result = await client.query("火灾")
            print(f"✅ 查询测试成功")
            print(f"   结果: {result.get('status')}")
        except Exception as e:
            print(f"❌ 查询测试失败: {e}")
            return False
        
        # 测试统计
        try:
            result = await client.get_stats()
            print(f"✅ 统计测试成功")
            print(f"   结果: {result.get('status')}")
        except Exception as e:
            print(f"❌ 统计测试失败: {e}")
            return False
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ API 客户端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_component_imports():
    """测试组件导入"""
    print("\n" + "=" * 60)
    print("测试 4: 测试组件导入")
    print("=" * 60)
    
    try:
        from api.client import APIClient
        print("✅ APIClient 导入成功")
    except Exception as e:
        print(f"❌ APIClient 导入失败: {e}")
        return False
    
    try:
        from session.manager import SessionManager
        print("✅ SessionManager 导入成功")
    except Exception as e:
        print(f"❌ SessionManager 导入失败: {e}")
        return False
    
    try:
        from queue.request_queue import RequestQueue
        print("✅ RequestQueue 导入成功")
    except Exception as e:
        print(f"❌ RequestQueue 导入失败: {e}")
        return False
    
    try:
        from utils.formatter import MessageFormatter
        print("✅ MessageFormatter 导入成功")
    except Exception as e:
        print(f"❌ MessageFormatter 导入失败: {e}")
        return False
    
    return True


async def test_main_class():
    """测试主类"""
    print("\n" + "=" * 60)
    print("测试 5: 测试主类")
    print("=" * 60)
    
    try:
        # 尝试导入 Main 类
        import sys
        import importlib.util
        
        # 加载 main.py
        spec = importlib.util.spec_from_file_location(
            "main", 
            "astrbot-plugin-fireeye-qq/main.py"
        )
        main_module = importlib.util.module_from_spec(spec)
        
        # 检查是否有 Main 类
        print("✅ main.py 可以加载")
        
        # 检查 __init__.py
        with open("astrbot-plugin-fireeye-qq/__init__.py", 'r', encoding='utf-8') as f:
            init_content = f.read()
        
        if "from .main import Main" in init_content:
            print("✅ __init__.py 正确导入 Main")
        else:
            print("❌ __init__.py 未导入 Main")
            return False
        
        if '__all__ = ["Main"]' in init_content or "__all__ = ['Main']" in init_content:
            print("✅ __init__.py 正确导出 Main")
        else:
            print("❌ __init__.py 未导出 Main")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 主类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("\n🔍 开始诊断 QQ 插件问题...\n")
    
    results = []
    
    # 测试 1: 导入
    results.append(("导入测试", await test_imports()))
    
    # 测试 2: 插件结构
    results.append(("插件结构", await test_plugin_structure()))
    
    # 测试 3: 组件导入
    results.append(("组件导入", await test_component_imports()))
    
    # 测试 4: API 客户端
    results.append(("API 客户端", await test_api_client()))
    
    # 测试 5: 主类
    results.append(("主类测试", await test_main_class()))
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有测试通过！")
        print("\n可能的问题:")
        print("1. AstrBot 可能没有正确加载插件")
        print("2. AstrBot 环境中的网络配置可能不同")
        print("3. 需要检查 AstrBot 的日志")
        print("\n建议:")
        print("1. 检查 AstrBot 日志: tail -n 200 /path/to/astrbot/logs/astrbot.log")
        print("2. 检查插件是否在 AstrBot 的插件列表中")
        print("3. 确认 AstrBot 已重启")
    else:
        print("❌ 某些测试失败")
        print("\n请修复上述失败的测试")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
