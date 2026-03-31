# 火瞳 QQ 插件 - 故障排查指南

## 问题描述

所有 QQ 插件命令都失败：
- `/火瞳查询 火` → ❌ 查询失败，请稍后重试
- `/ht查询 火` → ❌ 查询失败，请稍后重试
- `/火瞳统计` → ❌ 获取统计信息失败，请稍后重试
- `/火瞳帮助` → ❌ 帮助命令执行失败

## 可能的原因

### 1. 插件未正确加载 ⚠️ **最可能**

**症状**：
- 命令无法识别
- 所有命令都失败
- AstrBot 日志中没有插件初始化信息

**解决方案**：

a) **检查 `__init__.py` 是否正确导出 Main 类**
```python
# astrbot-plugin-fireeye-qq/__init__.py
from .main import Main
__all__ = ["Main"]
```

b) **检查插件目录结构**
```
astrbot-plugin-fireeye-qq/
├── __init__.py              # ✅ 必须存在且导出 Main
├── main.py                  # ✅ 包含 Main 类
├── config.yaml              # ✅ 配置文件
├── metadata.yaml            # ✅ 元数据
├── api/
│   ├── __init__.py
│   └── client.py
├── session/
│   ├── __init__.py
│   └── manager.py
├── queue/
│   ├── __init__.py
│   └── request_queue.py
└── utils/
    ├── __init__.py
    └── formatter.py
```

c) **重启 AstrBot**
```bash
systemctl restart astrbot
# 或
docker-compose restart astrbot
```

d) **检查 AstrBot 日志**
```bash
# 查看 AstrBot 日志
tail -f /path/to/astrbot/logs/astrbot.log

# 查找插件加载信息
grep -i "fire-eye" /path/to/astrbot/logs/astrbot.log
```

### 2. 命令过滤器配置错误

**症状**：
- 帮助命令可能工作，但查询命令不工作
- 命令前缀识别有问题

**解决方案**：

a) **检查命令装饰器**
```python
# 正确的方式
@filter.command("火瞳帮助", alias={"ht帮助"})
async def help_command(self, event: AstrMessageEvent):
    pass

@filter.command("火瞳查询", alias={"ht查询"})
async def query_command(self, event: AstrMessageEvent):
    pass
```

b) **使用调试版本**
```bash
# 将 main_debug.py 复制为 main.py
cp astrbot-plugin-fireeye-qq/main_debug.py astrbot-plugin-fireeye-qq/main.py

# 重启 AstrBot
systemctl restart astrbot

# 查看详细日志
tail -f /path/to/astrbot/logs/astrbot.log | grep "Fire-Eye QQ DEBUG"
```

### 3. 后端连接问题

**症状**：
- 命令被识别但返回错误
- 日志中显示 API 连接失败

**解决方案**：

a) **验证后端运行**
```bash
curl -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" \
  http://127.0.0.1:8000/api/v1/chat/health
```

b) **检查配置文件**
```yaml
# astrbot-plugin-fireeye-qq/config.yaml
fire_eye:
  api_url: "http://127.0.0.1:8000/api/v1"  # ✅ 使用 127.0.0.1，不是 localhost
  api_key: "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
```

c) **检查网络连接**
```bash
# 从 AstrBot 容器/服务器测试连接
ping 127.0.0.1
curl http://127.0.0.1:8000/api/v1/chat/health
```

### 4. 依赖缺失

**症状**：
- 导入错误
- 模块未找到

**解决方案**：

a) **安装依赖**
```bash
pip install -r astrbot-plugin-fireeye-qq/requirements.txt
```

b) **检查依赖**
```bash
pip list | grep -E "aiohttp|pyyaml|loguru"
```

### 5. AstrBot 版本不兼容

**症状**：
- 导入 `astrbot.api` 失败
- 事件处理不工作

**解决方案**：

a) **检查 AstrBot 版本**
```bash
pip show astrbot
```

b) **更新 AstrBot**
```bash
pip install --upgrade astrbot
```

## 调试步骤

### 步骤 1: 启用调试日志

编辑 `config.yaml`：
```yaml
logging:
  level: "DEBUG"  # 改为 DEBUG
  file: "./logs/fireeye-qq.log"
```

### 步骤 2: 使用调试版本

```bash
# 备份原始文件
cp astrbot-plugin-fireeye-qq/main.py astrbot-plugin-fireeye-qq/main_backup.py

# 使用调试版本
cp astrbot-plugin-fireeye-qq/main_debug.py astrbot-plugin-fireeye-qq/main.py

# 重启 AstrBot
systemctl restart astrbot
```

### 步骤 3: 查看日志

```bash
# 查看实时日志
tail -f ./logs/fireeye-qq.log

# 或查看 AstrBot 日志
tail -f /path/to/astrbot/logs/astrbot.log | grep "Fire-Eye"
```

### 步骤 4: 测试命令

在 QQ 中发送：
```
/火瞳帮助
```

查看日志中是否有：
```
[Fire-Eye QQ DEBUG] Help command triggered
```

## 常见错误信息

### 错误 1: "查询失败，请稍后重试"

**原因**：
- API 连接失败
- API Key 不正确
- 后端未运行

**解决**：
1. 检查后端是否运行
2. 验证 API Key
3. 检查网络连接

### 错误 2: "查询命令执行失败"

**原因**：
- 命令处理器异常
- 配置加载失败
- 组件初始化失败

**解决**：
1. 查看详细日志
2. 检查配置文件
3. 验证所有依赖

### 错误 3: "获取统计信息失败"

**原因**：
- 同查询失败的原因
- 后端统计端点问题

**解决**：
1. 测试后端统计端点
2. 检查数据库连接

## 快速诊断脚本

创建 `diagnose_qq_plugin.py`：

```python
#!/usr/bin/env python3
import asyncio
import aiohttp

async def diagnose():
    api_url = "http://127.0.0.1:8000/api/v1"
    api_key = "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
    
    print("🔍 诊断火瞳 QQ 插件...")
    
    # 1. 检查后端连接
    print("\n1. 检查后端连接...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_url}/chat/health",
                headers={"X-API-Key": api_key}
            ) as resp:
                if resp.status == 200:
                    print("   ✅ 后端连接正常")
                else:
                    print(f"   ❌ 后端返回错误: {resp.status}")
    except Exception as e:
        print(f"   ❌ 后端连接失败: {e}")
    
    # 2. 检查查询功能
    print("\n2. 检查查询功能...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{api_url}/chat/query",
                json={"query": "火灾"},
                headers={"X-API-Key": api_key}
            ) as resp:
                if resp.status == 200:
                    print("   ✅ 查询功能正常")
                else:
                    print(f"   ❌ 查询失败: {resp.status}")
    except Exception as e:
        print(f"   ❌ 查询异常: {e}")
    
    # 3. 检查统计功能
    print("\n3. 检查统计功能...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_url}/chat/stats",
                headers={"X-API-Key": api_key}
            ) as resp:
                if resp.status == 200:
                    print("   ✅ 统计功能正常")
                else:
                    print(f"   ❌ 统计失败: {resp.status}")
    except Exception as e:
        print(f"   ❌ 统计异常: {e}")
    
    print("\n✅ 诊断完成")

if __name__ == "__main__":
    asyncio.run(diagnose())
```

运行：
```bash
python diagnose_qq_plugin.py
```

## 获取帮助

如果问题仍未解决，请提供：

1. **AstrBot 日志**
   ```bash
   tail -n 100 /path/to/astrbot/logs/astrbot.log
   ```

2. **插件日志**
   ```bash
   cat ./logs/fireeye-qq.log
   ```

3. **配置文件**
   ```bash
   cat astrbot-plugin-fireeye-qq/config.yaml
   ```

4. **系统信息**
   ```bash
   python --version
   pip list | grep -E "astrbot|aiohttp|pyyaml"
   ```

---

**最后更新**: 2026-03-25  
**版本**: 1.0.0
