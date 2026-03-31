# QQ 插件装饰器修复

## 问题

之前的错误：
```
TypeError: Main.stats_command() missing 1 required positional argument: 'event'
TypeError: Main.query_command() missing 1 required positional argument: 'event'
```

## 根本原因

使用了错误的装饰器语法。AstrBot 的命令装饰器有两种方式：

### ❌ 错误方式（之前使用的）
```python
@filter.command("火瞳帮助", alias={"ht帮助"})
async def help_command(self, event: AstrMessageEvent):
    pass
```

### ✅ 正确方式（现在使用的）
```python
@filter.command_group("火瞳帮助")
@filter.command_group("ht帮助")
async def help_command(self, event: AstrMessageEvent):
    pass
```

## 已修复的文件

### 1. AstrBot 插件目录
```
fire-eye-system/astrbot_data/plugins/astrbot-plugin-fireeye-qq/main.py
```

### 2. 项目根目录
```
astrbot-plugin-fireeye-qq/main.py
```

## 修复内容

### 帮助命令
```python
@filter.command_group("火瞳帮助")
@filter.command_group("ht帮助")
async def help_command(self, event: AstrMessageEvent):
    """帮助命令"""
```

### 查询命令
```python
@filter.command_group("火瞳查询")
@filter.command_group("ht查询")
async def query_command(self, event: AstrMessageEvent):
    """查询命令"""
```

### 统计命令
```python
@filter.command_group("火瞳统计")
@filter.command_group("ht统计")
async def stats_command(self, event: AstrMessageEvent):
    """统计命令"""
```

## 已执行的操作

1. ✅ 修复了 AstrBot 插件目录中的 main.py
2. ✅ 修复了项目根目录中的 main.py
3. ✅ 重启了 AstrBot 容器

## 现在测试

等待 10-15 秒让 AstrBot 完全启动，然后在 QQ 中测试：

### 1. 帮助命令
```
发送: /火瞳帮助
预期: 显示帮助信息
```

### 2. 查询命令
```
发送: /火瞳查询 火灾
预期: 显示查询结果
```

### 3. 统计命令
```
发送: /火瞳统计
预期: 显示统计信息
```

### 4. 别名测试
```
发送: /ht帮助
预期: 显示帮助信息
```

## 如果仍然不工作

查看 AstrBot 日志：
```bash
cd fire-eye-system
docker-compose logs -f astrbot | grep "Fire-Eye QQ"
```

应该看到：
```
[Fire-Eye QQ] Plugin initialized
[Fire-Eye QQ] API URL: http://127.0.0.1:8000/api/v1
[Fire-Eye QQ] Help command triggered
```

## 预期结果

所有命令现在应该正常工作，不再出现 "missing 1 required positional argument" 错误。

---

**修复日期**: 2026-03-25  
**状态**: ✅ 已修复  
**下一步**: 在 QQ 中测试所有命令

