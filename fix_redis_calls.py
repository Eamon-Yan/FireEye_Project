#!/usr/bin/env python3
"""Fix Redis setex calls in the backend"""

import re

# Fix task_manager.py
with open('fire-eye-system/backend/app/services/task_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace setex with set
content = re.sub(
    r'await self\.redis\.setex\(task_key, TASK_TTL, task_data\)',
    'await self.redis.set(task_key, task_data, expire=TASK_TTL)',
    content
)

with open('fire-eye-system/backend/app/services/task_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed task_manager.py")

# Fix session_service.py
with open('fire-eye-system/backend/app/services/session_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace redis.redis.setex with redis.set and fix parameters
content = re.sub(
    r'await self\.redis\.redis\.setex\(\s*key,\s*SESSION_TTL,\s*session_data\.model_dump_json\(\)\s*\)',
    'await self.redis.set(key, session_data.model_dump_json(), expire=SESSION_TTL)',
    content,
    flags=re.MULTILINE | re.DOTALL
)

# Fix redis.redis.get to redis.get
content = re.sub(
    r'await self\.redis\.redis\.get\(key\)',
    'await self.redis.get(key)',
    content
)

# Fix redis.redis.expire to redis.expire
content = re.sub(
    r'await self\.redis\.redis\.expire\(key, SESSION_TTL\)',
    'await self.redis.expire(key, SESSION_TTL)',
    content
)

# Fix redis.redis.delete to redis.delete
content = re.sub(
    r'await self\.redis\.redis\.delete\(key\)',
    'await self.redis.delete(key)',
    content
)

with open('fire-eye-system/backend/app/services/session_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed session_service.py")
