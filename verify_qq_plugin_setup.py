#!/usr/bin/env python3
"""
火瞳 QQ 插件 - 快速验证脚本
验证所有配置和依赖是否正确
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_check(status, text):
    """打印检查结果"""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {text}")


def check_file_exists(path, description):
    """检查文件是否存在"""
    exists = Path(path).exists()
    print_check(exists, f"{description}: {path}")
    return exists


def check_directory_exists(path, description):
    """检查目录是否存在"""
    exists = Path(path).is_dir()
    print_check(exists, f"{description}: {path}")
    return exists


def check_python_package(package_name):
    """检查 Python 包是否安装"""
    try:
        __import__(package_name)
        print_check(True, f"Python 包已安装: {package_name}")
        return True
    except ImportError:
        print_check(False, f"Python 包未安装: {package_name}")
        return False


def check_config_content(path, key, expected_value=None):
    """检查配置文件内容"""
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 导航到嵌套键
        keys = key.split('.')
        value = config
        for k in keys:
            value = value.get(k, {})
        
        if expected_value:
            matches = str(value) == str(expected_value)
            print_check(matches, f"配置 {key}: {value}")
            return matches
        else:
            print_check(value is not None, f"配置 {key}: {value}")
            return value is not None
    except Exception as e:
        print_check(False, f"读取配置失败: {e}")
        return False


def main():
    """主函数"""
    print_header("🔥 火瞳 QQ 插件 - 快速验证")
    
    all_passed = True
    
    # 1. 检查文件结构
    print_header("1️⃣ 检查文件结构")
    
    files_to_check = [
        ("astrbot-plugin-fireeye-qq/__init__.py", "插件入口"),
        ("astrbot-plugin-fireeye-qq/main.py", "主插件代码"),
        ("astrbot-plugin-fireeye-qq/config.yaml", "配置文件"),
        ("astrbot-plugin-fireeye-qq/metadata.yaml", "元数据"),
        ("astrbot-plugin-fireeye-qq/requirements.txt", "依赖列表"),
    ]
    
    for file_path, description in files_to_check:
        if not check_file_exists(file_path, description):
            all_passed = False
    
    # 2. 检查目录结构
    print_header("2️⃣ 检查目录结构")
    
    dirs_to_check = [
        ("astrbot-plugin-fireeye-qq/api", "API 模块"),
        ("astrbot-plugin-fireeye-qq/session", "会话模块"),
        ("astrbot-plugin-fireeye-qq/queue", "队列模块"),
        ("astrbot-plugin-fireeye-qq/utils", "工具模块"),
    ]
    
    for dir_path, description in dirs_to_check:
        if not check_directory_exists(dir_path, description):
            all_passed = False
    
    # 3. 检查 Python 依赖
    print_header("3️⃣ 检查 Python 依赖")
    
    packages = ["aiohttp", "yaml", "loguru"]
    for package in packages:
        if not check_python_package(package):
            all_passed = False
    
    # 4. 检查配置内容
    print_header("4️⃣ 检查配置内容")
    
    config_checks = [
        ("astrbot-plugin-fireeye-qq/config.yaml", "fire_eye.api_url"),
        ("astrbot-plugin-fireeye-qq/config.yaml", "fire_eye.api_key"),
        ("astrbot-plugin-fireeye-qq/config.yaml", "session.ttl"),
        ("astrbot-plugin-fireeye-qq/config.yaml", "request_queue.max_concurrent"),
    ]
    
    for config_path, key in config_checks:
        if not check_config_content(config_path, key):
            all_passed = False
    
    # 5. 检查 __init__.py 导出
    print_header("5️⃣ 检查 __init__.py 导出")
    
    try:
        with open("astrbot-plugin-fireeye-qq/__init__.py", 'r', encoding='utf-8') as f:
            init_content = f.read()
        
        has_import = "from .main import Main" in init_content
        has_export = '__all__ = ["Main"]' in init_content or "__all__ = ['Main']" in init_content
        
        print_check(has_import, "__init__.py 导入 Main 类")
        print_check(has_export, "__init__.py 导出 Main 类")
        
        if not (has_import and has_export):
            all_passed = False
    except Exception as e:
        print_check(False, f"检查 __init__.py 失败: {e}")
        all_passed = False
    
    # 6. 检查后端连接
    print_header("6️⃣ 检查后端连接")
    
    try:
        import asyncio
        import aiohttp
        
        async def test_backend():
            """测试后端连接"""
            api_url = "http://127.0.0.1:8000/api/v1"
            api_key = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
            
            try:
                async with aiohttp.ClientSession() as session:
                    headers = {"X-API-Key": api_key}
                    async with session.get(f"{api_url}/chat/health", headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            print_check(True, "后端连接正常")
                            return True
                        else:
                            print_check(False, f"后端返回状态码: {resp.status}")
                            return False
            except Exception as e:
                print_check(False, f"后端连接失败: {e}")
                return False
        
        # 运行异步测试
        result = asyncio.run(test_backend())
        if not result:
            all_passed = False
    except Exception as e:
        print_check(False, f"测试后端连接失败: {e}")
        all_passed = False
    
    # 7. 总结
    print_header("📋 验证总结")
    
    if all_passed:
        print("✅ 所有检查通过！")
        print("\n🎉 QQ 插件已准备就绪！")
        print("\n后续步骤:")
        print("1. 确保 AstrBot 已安装所有依赖")
        print("2. 重启 AstrBot 服务")
        print("3. 在 QQ 中测试命令:")
        print("   • /火瞳帮助")
        print("   • /火瞳查询 火灾")
        print("   • /火瞳统计")
        return 0
    else:
        print("❌ 某些检查未通过")
        print("\n请修复上述问题后重试")
        print("\n常见问题:")
        print("1. 依赖未安装: pip install -r astrbot-plugin-fireeye-qq/requirements.txt")
        print("2. 配置错误: 检查 astrbot-plugin-fireeye-qq/config.yaml")
        print("3. 后端未运行: 确保 fire-eye-system 后端已启动")
        return 1


if __name__ == "__main__":
    sys.exit(main())
