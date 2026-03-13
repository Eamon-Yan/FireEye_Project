#!/usr/bin/env python3
"""
清理并正确修复 task_manager.py
"""

import subprocess
import sys

def run_command(cmd):
    """运行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return result.returncode, result.stdout, result.stderr

def main():
    print("=" * 60)
    print("清理并修复 task_manager.py")
    print("=" * 60)
    
    # 1. 从宿主机复制原始文件到容器
    print("\n1. 恢复原始文件...")
    code, stdout, stderr = run_command(
        "docker cp fire-eye-system/backend/app/services/task_manager.py fire-eye-backend:/app/app/services/task_manager.py"
    )
    if code != 0:
        print(f"❌ 复制失败: {stderr}")
        return 1
    print("✅ 原始文件已恢复")
    
    # 2. 创建简单的 sed 命令来修复
    print("\n2. 应用修复...")
    
    # 使用 sed 直接在容器内修复
    sed_cmd = r"""docker exec fire-eye-backend bash -c "sed -i '266s/.*/        # RedisClient.get() already returns a dict, no need to parse JSON\n        if isinstance(task_data, str):\n            task_dict = json.loads(task_data)\n        else:\n            task_dict = task_data/' /app/app/services/task_manager.py" """
    
    # 更简单的方法：使用 Python 在容器内直接修复
    fix_script = '''
import json

# 读取文件
with open('/app/app/services/task_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换目标行
old_line = "        task_dict = json.loads(task_data)"
new_code = """        # RedisClient.get() already returns a dict, no need to parse JSON
        if isinstance(task_data, str):
            task_dict = json.loads(task_data)
        else:
            task_dict = task_data"""

# 只替换 get_task_status 方法中的那一行
# 找到 get_task_status 方法
lines = content.split('\\n')
new_lines = []
in_get_task_status = False
replaced = False

for i, line in enumerate(lines):
    if 'async def get_task_status' in line:
        in_get_task_status = True
        new_lines.append(line)
    elif in_get_task_status and not replaced and 'task_dict = json.loads(task_data)' in line:
        # 替换这一行
        new_lines.append(new_code)
        replaced = True
    elif in_get_task_status and line.strip().startswith('async def '):
        # 进入下一个方法
        in_get_task_status = False
        new_lines.append(line)
    else:
        new_lines.append(line)

# 写回文件
with open('/app/app/services/task_manager.py', 'w', encoding='utf-8') as f:
    f.write('\\n'.join(new_lines))

print("✅ 修复完成")
'''
    
    # 保存并执行
    with open('temp_clean_fix.py', 'w', encoding='utf-8') as f:
        f.write(fix_script)
    
    code, stdout, stderr = run_command("docker cp temp_clean_fix.py fire-eye-backend:/tmp/fix.py")
    if code != 0:
        print(f"❌ 复制脚本失败: {stderr}")
        return 1
    
    code, stdout, stderr = run_command("docker exec fire-eye-backend python /tmp/fix.py")
    if code != 0:
        print(f"❌ 执行失败: {stderr}")
        return 1
    print(stdout)
    
    # 3. 验证
    print("\n3. 验证修复...")
    code, stdout, stderr = run_command(
        'docker exec fire-eye-backend sed -n "260,275p" /app/app/services/task_manager.py'
    )
    if code == 0:
        print("修复后的代码:")
        print(stdout)
    
    # 4. 重启
    print("\n4. 重启容器...")
    code, stdout, stderr = run_command("docker restart fire-eye-backend")
    if code != 0:
        print(f"❌ 重启失败: {stderr}")
        return 1
    print("✅ 容器已重启")
    
    # 5. 清理
    run_command("del temp_clean_fix.py")
    run_command("docker exec fire-eye-backend rm /tmp/fix.py")
    
    print("\n" + "=" * 60)
    print("✅ 完成！等待15秒后测试")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
