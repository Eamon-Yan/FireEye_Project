#!/usr/bin/env python3
"""Fix task_manager.py directly in the container"""

import subprocess

# Read the file from container
result = subprocess.run(
    ['docker', 'exec', 'fire-eye-backend', 'cat', '/app/app/services/task_manager.py'],
    capture_output=True,
    text=True
)

content = result.stdout

# Replace the problematic line
old_code = "        task_dict = json.loads(task_data)"
new_code = """        # RedisClient.get() already returns a dict, no need to parse JSON
        if isinstance(task_data, str):
            task_dict = json.loads(task_data)
        else:
            task_dict = task_data"""

content = content.replace(old_code, new_code)

# Write back to container
with open('temp_task_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Copy to container
subprocess.run(['docker', 'cp', 'temp_task_manager.py', 'fire-eye-backend:/app/app/services/task_manager.py'])

# Restart
subprocess.run(['docker', 'restart', 'fire-eye-backend'])

print("Fixed and restarted!")
