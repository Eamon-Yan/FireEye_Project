"""
手动测试脚本 - 验证 Phase 2 核心功能
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from utils.formatter import MessageFormatter
from session.manager import SessionManager
from commands.help_handler import HelpHandler


def test_message_formatter():
    """测试消息格式化器"""
    print("\n=== 测试消息格式化器 ===")
    
    formatter = MessageFormatter()
    
    # 测试查询结果格式化
    response = {
        "data": {
            "results": [
                {
                    "type": "FireEvent",
                    "description": "3.21火灾事故",
                    "properties": {
                        "date": "2024-03-21",
                        "location": "某工厂"
                    }
                }
            ],
            "total_count": 1
        }
    }
    
    result = formatter.format_query_results(response)
    print(f"✅ 查询结果格式化:\n{result}\n")
    
    # 测试任务进度格式化
    progress = formatter.format_task_progress(50)
    print(f"✅ 任务进度格式化:\n{progress}\n")
    
    # 测试帮助信息格式化
    help_text = formatter.format_help()
    print(f"✅ 帮助信息格式化:\n{help_text[:200]}...\n")
    
    return True


def test_session_manager():
    """测试会话管理器"""
    print("\n=== 测试会话管理器 ===")
    
    manager = SessionManager(ttl=1800)
    
    # 创建会话
    session_id = manager.create_session("user-123", "qq")
    print(f"✅ 创建会话: {session_id}")
    
    # 获取会话
    retrieved_id = manager.get_session("user-123")
    assert retrieved_id == session_id
    print(f"✅ 获取会话: {retrieved_id}")
    
    # 更新活动时间
    manager.update_activity("user-123")
    print(f"✅ 更新活动时间")
    
    # 创建多个会话
    session2 = manager.create_session("user-456", "telegram")
    print(f"✅ 创建第二个会话: {session2}")
    
    return True


async def test_help_handler():
    """测试帮助命令处理器"""
    print("\n=== 测试帮助命令处理器 ===")
    
    formatter = MessageFormatter()
    handler = HelpHandler(formatter=formatter)
    
    result = await handler.handle("/火瞳帮助", "user-123")
    print(f"✅ 帮助命令响应:\n{result[:200]}...\n")
    
    return True


def test_file_validation():
    """测试文件验证"""
    print("\n=== 测试文件验证 ===")
    
    from utils.file_handler import FileHandler
    import tempfile
    
    handler = FileHandler(temp_dir=tempfile.mkdtemp(), max_file_size=10485760)
    
    # 测试文件类型验证
    assert handler.validate_file_type("report.pdf") is True
    print("✅ PDF 文件类型验证通过")
    
    assert handler.validate_file_type("document.docx") is True
    print("✅ DOCX 文件类型验证通过")
    
    assert handler.validate_file_type("data.txt") is True
    print("✅ TXT 文件类型验证通过")
    
    assert handler.validate_file_type("image.jpg") is False
    print("✅ 无效文件类型正确拒绝")
    
    return True


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("Phase 2 插件核心功能手动测试")
    print("=" * 60)
    
    tests = [
        ("消息格式化器", test_message_formatter),
        ("会话管理器", test_session_manager),
        ("帮助命令处理器", test_help_handler),
        ("文件验证", test_file_validation),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {name} 测试通过")
            else:
                failed += 1
                print(f"❌ {name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"❌ {name} 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有核心功能测试通过！")
        return 0
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，需要修复")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
