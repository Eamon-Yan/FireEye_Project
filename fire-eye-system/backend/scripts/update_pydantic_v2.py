#!/usr/bin/env python3
"""
更新 Pydantic v2 兼容性脚本
"""

import os
import re
from pathlib import Path

def update_validators_in_file(file_path):
    """更新文件中的 validator 为 field_validator"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 更新 import 语句
    content = re.sub(
        r'from pydantic import ([^,\n]*,\s*)?validator([,\s][^,\n]*)?',
        lambda m: f'from pydantic import {m.group(1) or ""}field_validator{m.group(2) or ""}',
        content
    )
    
    # 更新 @validator 装饰器
    # 处理简单的 validator
    content = re.sub(
        r'@validator\("([^"]+)"\)',
        r'@field_validator("\1")',
        content
    )
    
    # 处理带 pre=True 的 validator
    content = re.sub(
        r'@validator\("([^"]+)",\s*pre=True\)',
        r'@field_validator("\1", mode="before")',
        content
    )
    
    # 处理多个字段的 validator
    content = re.sub(
        r'@validator\("([^"]+)",\s*"([^"]+)"\)',
        r'@field_validator("\1", "\2")',
        content
    )
    
    # 更新方法签名，添加 @classmethod
    content = re.sub(
        r'(@field_validator[^\n]*\n\s*)def\s+(\w+)\(cls,',
        r'\1@classmethod\n    def \2(cls,',
        content
    )
    
    # 更新 values 参数为 info.data
    content = re.sub(
        r'def\s+\w+\(cls,\s*v,\s*values\)',
        r'def \g<0>(cls, v, info)',
        content
    )
    content = re.sub(
        r'values\.get\(',
        r'info.data.get(',
        content
    )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")
        return True
    
    return False

def main():
    """主函数"""
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    
    # 需要更新的文件模式
    patterns = [
        "app/schemas/*.py",
        "app/core/*.py"
    ]
    
    updated_files = []
    
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            if file_path.is_file() and file_path.suffix == '.py':
                if update_validators_in_file(file_path):
                    updated_files.append(str(file_path))
    
    print(f"\n更新完成！共更新了 {len(updated_files)} 个文件:")
    for file_path in updated_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main()