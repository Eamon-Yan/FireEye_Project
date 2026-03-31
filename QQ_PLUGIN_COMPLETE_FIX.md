# 火瞳 QQ 插件 - 完整修复指南

## 问题现象

所有 QQ 插件命令都返回错误：
```
❌ 查询失败，请稍后重试
❌ 获取统计信息失败，请稍后重试
❌ 帮助命令执行失败
```

## 根本原因分析

经过诊断，问题可能是以下几个方面之一：

1. **插件未正确加载** - `__init__.py` 没有导出 `Main` 类
2. **命令处理器未正确注册** - 装饰器配置问题
3. **后端连接失败** - API Key 或 URL 配置错误
4. **依赖缺失** - 必要的 Python 包未安装

## 修复步骤

### 步骤 1: 修复 `__init__.py`

**文件**: `astrbot-plugin-fireeye-qq/__init__.py`

```python
"""
Fire-Eye QQ Plugin
火瞳 QQ 插件
"""

from .main import Main

__version__ = "1.0.0"
__author__ = "Fire-Eye Team"
__description__ = "火瞳火灾调查知识图谱系统 QQ 集成插件"

__all__ = ["Main"]
```

✅ **已完成** - 文件已更新

### 步骤 2: 验证配置文件

**文件**: `astrbot-plugin-fireeye-qq/config.yaml`

```yaml
# Fire-Eye 后端 API 配置
fire_eye:
  api_url: "http://127.0.0.1:8000/api/v1"  # ✅ 使用 127.0.0.1
  api_key: "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"  # ✅ 正确的 API Key
  timeout: 30
  retries: 3

# 会话管理配置
session:
  ttl: 1800

# 请求队列配置
request_queue:
  max_concurrent: 5
  max_queue_size: 20

# QQ 特定配置
qq:
  max_message_length: 4096
  polling_interval: 3

# 日志配置
logging:
  level: "INFO"
  file: "./logs/fireeye-qq.log"
  max_size: 10485760
  backup_count: 5
```

✅ **已完成** - 配置已更新

### 步骤 3: 测试基本功能

使用最小化版本测试命令处理是否工作：

```bash
# 1. 备份原始文件
cp astrbot-plugin-fireeye-qq/main.py astrbot-plugin-fireeye-qq/main_backup.py

# 2. 使用最小化版本测试
cp astrbot-plugin-fireeye-qq/main_minimal.py astrbot-plugin-fireeye-qq/main.py

# 3. 重启 AstrBot
systemctl restart astrbot

# 4. 在 QQ 中测试
# 发送: /火瞳帮助
# 预期: ✅ 帮助命令工作正常！
```

如果最小化版本工作，说明问题在于完整版本的代码。

### 步骤 4: 恢复完整版本并调试

```bash
# 1. 恢复完整版本
cp astrbot-plugin-fireeye-qq/main_backup.py astrbot-plugin-fireeye-qq/main.py

# 2. 使用调试版本
cp astrbot-plugin-fireeye-qq/main_debug.py astrbot-plugin-fireeye-qq/main.py

# 3. 重启 AstrBot
systemctl restart astrbot

# 4. 查看详细日志
tail -f ./logs/fireeye-qq.log | grep "Fire-Eye QQ DEBUG"

# 5. 在 QQ 中测试
# 发送: /火瞳查询 火灾
# 查看日志输出
```

### 步骤 5: 验证后端连接

```bash
# 运行诊断脚本
python test_qq_plugin_complete.py

# 预期输出:
# ✅ 基本查询: 通过
# ✅ 统计功能: 通过
# ✅ 多轮对话: 通过
# ✅ 不同查询: 通过
```

### 步骤 6: 安装依赖

```bash
# 安装所有依赖
pip install -r astrbot-plugin-fireeye-qq/requirements.txt

# 验证安装
pip list | grep -E "aiohttp|pyyaml|loguru"
```

### 步骤 7: 重启 AstrBot

```bash
# 恢复原始版本
cp astrbot-plugin-fireeye-qq/main_backup.py astrbot-plugin-fireeye-qq/main.py

# 重启 AstrBot
systemctl restart astrbot

# 或使用 Docker
docker-compose restart astrbot
```

## 验证修复

### 测试 1: 帮助命令
```
发送: /火瞳帮助
预期: 显示帮助信息
```

### 测试 2: 查询命令
```
发送: /火瞳查询 火灾
预期: 显示查询结果
```

### 测试 3: 统计命令
```
发送: /火瞳统计
预期: 显示统计信息
```

### 测试 4: 别名命令
```
发送: /ht查询 电气
预期: 显示查询结果
```

## 如果仍然不工作

### 检查清单

- [ ] `__init__.py` 已更新并导出 `Main` 类
- [ ] `config.yaml` 中的 API Key 正确
- [ ] `config.yaml` 中的 API URL 使用 `127.0.0.1`
- [ ] 后端服务运行在 `http://127.0.0.1:8000`
- [ ] 所有依赖已安装
- [ ] AstrBot 已重启
- [ ] 查看了 AstrBot 日志
- [ ] 查看了插件日志

### 获取日志

```bash
# AstrBot 日志
tail -n 200 /path/to/astrbot/logs/astrbot.log > astrbot_log.txt

# 插件日志
cat ./logs/fireeye-qq.log > plugin_log.txt

# 系统信息
python --version > system_info.txt
pip list >> system_info.txt
```

### 测试后端连接

```bash
# 测试健康检查
curl -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" \
  http://127.0.0.1:8000/api/v1/chat/health

# 测试查询
curl -X POST \
  -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" \
  -H "Content-Type: application/json" \
  -d '{"query": "火灾"}' \
  http://127.0.0.1:8000/api/v1/chat/query
```

## 文件清单

### 已修复的文件
- ✅ `astrbot-plugin-fireeye-qq/__init__.py` - 导出 Main 类
- ✅ `astrbot-plugin-fireeye-qq/config.yaml` - 正确的 API Key 和 URL

### 调试工具
- 📝 `astrbot-plugin-fireeye-qq/main_minimal.py` - 最小化版本
- 📝 `astrbot-plugin-fireeye-qq/main_debug.py` - 调试版本
- 📝 `test_qq_plugin_complete.py` - 完整测试脚本

### 文档
- 📖 `QQ_PLUGIN_TROUBLESHOOTING.md` - 故障排查指南
- 📖 `QQ_PLUGIN_SETUP_GUIDE.md` - 配置指南
- 📖 `QQ_PLUGIN_QUICK_REFERENCE.md` - 快速参考

## 快速修复命令

```bash
# 1. 更新 __init__.py
cat > astrbot-plugin-fireeye-qq/__init__.py << 'EOF'
"""
Fire-Eye QQ Plugin
火瞳 QQ 插件
"""

from .main import Main

__version__ = "1.0.0"
__author__ = "Fire-Eye Team"
__description__ = "火瞳火灾调查知识图谱系统 QQ 集成插件"

__all__ = ["Main"]
EOF

# 2. 安装依赖
pip install -r astrbot-plugin-fireeye-qq/requirements.txt

# 3. 重启 AstrBot
systemctl restart astrbot

# 4. 测试
python test_qq_plugin_complete.py
```

## 预期结果

修复完成后，所有命令应该正常工作：

```
用户: /火瞳帮助
机器人: 🔥 火瞳系统 - 帮助信息
        📖 可用命令:
        1️⃣ 查询命令
           /火瞳查询 <查询内容>
        ...

用户: /火瞳查询 火灾
机器人: 🔍 查询: 火灾
        找到 3 条结果:
        1. [FireEvent] 电气线路老化
           电线老化
        ...

用户: /火瞳统计
机器人: 📊 火瞳系统统计信息
        📈 数据概览:
        • 事件总数: 8
        • 实体总数: 8
        ...
```

---

**修复日期**: 2026-03-25  
**版本**: 1.0.0  
**状态**: 修复指南完成
