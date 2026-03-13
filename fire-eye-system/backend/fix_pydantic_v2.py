#!/usr/bin/env python3
"""
快速修复 Pydantic v2 兼容性
"""

import os
import re

# 需要修复的文件列表
files_to_fix = [
    "app/schemas/graph.py",
    "app/schemas/validation.py", 
    "app/schemas/extraction.py",
    "app/schemas/prediction.py",
    "app/schemas/document.py",
    "app/schemas/user.py"
]

def fix_file(filepath):
    """修复单个文件"""
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. 更新 import
    content = re.sub(r'from pydantic import ([^,\n]*,\s*)?validator', 
                    r'from pydantic import \1field_validator', content)
    
    # 2. 更新简单的 @validator
    content = re.sub(r'@validator\(', r'@field_validator(', content)
    
    # 3. 更新 pre=True 为 mode="before"
    content = re.sub(r'@field_validator\(([^)]+),\s*pre=True\)', 
                    r'@field_validator(\1, mode="before")', content)
    
    # 4. 添加 @classmethod 装饰器
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '@field_validator' in line:
            new_lines.append(line)
            # 查找下一个 def 行
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('def '):
                new_lines.append(lines[i])
                i += 1
            if i < len(lines):
                def_line = lines[i]
                # 添加 @classmethod
                indent = len(def_line) - len(def_line.lstrip())
                new_lines.append(' ' * indent + '@classmethod')
                new_lines.append(def_line)
        else:
            new_lines.append(line)
        i += 1
    
    content = '\n'.join(new_lines)
    
    # 5. 更新方法参数 values -> info
    content = re.sub(r'def\s+(\w+)\(cls,\s*v,\s*values\)', 
                    r'def \1(cls, v, info)', content)
    
    # 6. 更新 values.get -> info.data.get
    content = re.sub(r'values\.get\(', r'info.data.get(', content)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ 修复完成: {filepath}")
    else:
        print(f"- 无需修复: {filepath}")

def main():
    """主函数"""
    print("开始修复 Pydantic v2 兼容性...")
    
    for filepath in files_to_fix:
        fix_file(filepath)
    
    print("\n修复完成！")

if __name__ == "__main__":
    main()