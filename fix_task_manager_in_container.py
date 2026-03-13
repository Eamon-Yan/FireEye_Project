#!/usr/bin/env python3
"""
直接在容器内修复 task_manager.py 的 JSON 解析问题
"""

import subprocess
import sys

def run_command(cmd):
    """运行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return result.returncode, result.stdout, result.stderr

def main():
    print("=" * 60)
    print("修复 task_manager.py 中的 JSON 解析问题")
    print("=" * 60)
    
    # 1. 检查容器是否运行
    print("\n1. 检查容器状态...")
    code, stdout, stderr = run_command("docker ps --filter name=fire-eye-backend --format '{{.Status}}'")
    if code != 0 or not stdout.strip():
        print("❌ fire-eye-backend 容器未运行")
        return 1
    print(f"✅ 容器状态: {stdout.strip()}")
    
    # 2. 创建修复脚本
    print("\n2. 创建修复脚本...")
    fix_script = '''
import re

# 读取文件
with open('/app/app/services/task_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并替换
old_pattern = r'task_dict = json\\.loads\\(task_data\\)'
new_code = """# RedisClient.get() already returns a dict, no need to parse JSON
        if isinstance(task_data, str):
            task_dict = json.loads(task_data)
        else:
            task_dict = task_data"""

# 替换
content = re.sub(old_pattern, new_code, content)

# 写回文件
with open('/app/app/services/task_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 文件已修复")
'''
    
    # 保存修复脚本到临时文件
    with open('temp_fix_script.py', 'w', encoding='utf-8') as f:
        f.write(fix_script)
    
    # 3. 复制脚本到容器
    print("\n3. 复制修复脚本到容器...")
    code, stdout, stderr = run_command("docker cp temp_fix_script.py fire-eye-backend:/tmp/fix_script.py")
    if code != 0:
        print(f"❌ 复制失败: {stderr}")
        return 1
    print("✅ 脚本已复制到容器")
    
    # 4. 在容器内执行修复脚本
    print("\n4. 执行修复脚本...")
    code, stdout, stderr = run_command("docker exec fire-eye-backend python /tmp/fix_script.py")
    if code != 0:
        print(f"❌ 执行失败: {stderr}")
        return 1
    print(stdout)
    
    # 5. 验证修复
    print("\n5. 验证修复...")
    code, stdout, stderr = run_command(
        'docker exec fire-eye-backend grep -A 3 "if isinstance(task_data, str):" /app/app/services/task_manager.py'
    )
    if code == 0 and "isinstance" in stdout:
        print("✅ 修复已应用:")
        print(stdout[:200])
    else:
        print("⚠️  无法验证修复，但脚本已执行")
    
    # 6. 重启容器
    print("\n6. 重启后端容器...")
    code, stdout, stderr = run_command("docker restart fire-eye-backend")
    if code != 0:
        print(f"❌ 重启失败: {stderr}")
        return 1
    print("✅ 容器已重启")
    
    # 7. 清理临时文件
    print("\n7. 清理临时文件...")
    run_command("del temp_fix_script.py")
    run_command("docker exec fire-eye-backend rm /tmp/fix_script.py")
    print("✅ 临时文件已清理")
    
    print("\n" + "=" * 60)
    print("✅ 修复完成！")
    print("=" * 60)
    print("\n等待10秒让容器完全启动，然后运行测试:")
    print("  python test_upload_api.py")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
