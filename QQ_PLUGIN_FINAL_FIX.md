# QQ 插件最终修复

## 问题总结

经过多次调试，发现了以下问题：

### 1. 装饰器语法错误
- ❌ 错误: `@filter.command_group("火瞳帮助")`
- ✅ 正确: `@filter.command("火瞳帮助", alias={"ht帮助"})`

### 2. API URL 配置错误
- ❌ 错误: `http://127.0.0.1:8000/api/v1` (在 Docker 容器内无法访问)
- ✅ 正确: `http://fire-eye-backend:8000/api/v1` (Docker 网络内部地址)

### 3. 插件未复制到 AstrBot 目录
- ❌ 错误: 插件只在项目根目录
- ✅ 正确: 插件需要在 `fire-eye-system/astrbot_data/plugins/astrbot-plugin-fireeye-qq/`

## 已执行的修复

### 1. 修复装饰器语法 ✅
```python
# 帮助命令
@filter.command("火瞳帮助", alias={"ht帮助"})
async def help_command(self, event: AstrMessageEvent):
    pass

# 查询命令
@filter.command("火瞳查询", alias={"ht查询"})
async def query_command(self, event: AstrMessageEvent):
    pass

# 统计命令
@filter.command("火瞳统计", alias={"ht统计"})
async def stats_command(self, event: AstrMessageEvent):
    pass
```

### 2. 修复 API URL ✅
```yaml
fire_eye:
  api_url: "http://fire-eye-backend:8000/api/v1"
  api_key: "smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
```

### 3. 重启 AstrBot ✅
```bash
docker-compose restart astrbot
```

## 修复的文件

### AstrBot 插件目录
```
fire-eye-system/astrbot_data/plugins/astrbot-plugin-fireeye-qq/
├── main.py          ✅ 修复装饰器
└── config.yaml      ✅ 修复 API URL
```

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

## 验证插件加载

查看 AstrBot 日志，应该看到：

```bash
cd fire-eye-system
docker-compose logs astrbot | grep "astrbot-plugin-fireeye-qq"
```

预期输出：
```
正在载入插件 astrbot-plugin-fireeye-qq ...
Plugin fire-eye-qq (1.0.0) by Fire-Eye Team: 火瞳火灾调查知识图谱系统的 QQ 集成插件
```

如果看到错误：
```
插件 astrbot-plugin-fireeye-qq 导入失败
```

说明还有问题，需要查看详细错误信息。

## 预期结果

所有命令现在应该正常工作：

### 帮助命令
```
用户: /火瞳帮助
机器人: 🔥 火瞳系统 - 帮助信息
        📖 可用命令:
        1️⃣ 查询命令
           /火瞳查询 <查询内容>
        ...
```

### 查询命令
```
用户: /火瞳查询 火灾
机器人: 🔍 查询: 火灾
        找到 3 条结果:
        1. [FireEvent] 电气线路老化
           电线老化
        ...
```

### 统计命令
```
用户: /火瞳统计
机器人: 📊 火瞳系统统计信息
        📈 数据概览:
        • 事件总数: 8
        • 实体总数: 8
        ...
```

## 关键点总结

### Docker 环境中的网络配置
- AstrBot 容器内部访问后端：使用 `fire-eye-backend:8000`
- 宿主机访问后端：使用 `127.0.0.1:8000` 或 `localhost:8000`

### AstrBot 命令装饰器
- 使用 `@filter.command("命令名", alias={"别名1", "别名2"})`
- 不要使用 `@filter.command_group()`

### 插件位置
- 必须在 `fire-eye-system/astrbot_data/plugins/` 目录下
- 插件名称必须与目录名称匹配

## 如果仍然不工作

### 1. 查看完整日志
```bash
cd fire-eye-system
docker-compose logs -f astrbot
```

### 2. 检查插件是否加载
在日志中查找：
```
正在载入插件 astrbot-plugin-fireeye-qq
```

### 3. 检查错误信息
如果有错误，日志会显示详细的 Python traceback

### 4. 验证后端连接
```bash
# 在 AstrBot 容器内测试
docker-compose exec astrbot ping fire-eye-backend
```

---

**修复日期**: 2026-03-25  
**状态**: ✅ 最终修复完成  
**下一步**: 在 QQ 中测试所有命令

