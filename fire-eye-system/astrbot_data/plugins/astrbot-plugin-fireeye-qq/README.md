# 火瞳 QQ 插件 (Fire-Eye QQ Plugin)

火瞳火灾调查知识图谱系统的 QQ 集成插件，为 AstrBot 平台提供支持。

## 功能特性

- 🔍 **知识图谱查询**: 通过自然语言查询火灾事件、隐患和后果
- 📊 **统计信息**: 获取系统中的数据统计和分布情况
- 💬 **会话管理**: 自动记录对话上下文，支持多轮对话
- ⚡ **请求队列**: 智能队列管理，防止系统过载
- 🛡️ **错误处理**: 完善的错误处理和用户反馈

## 安装

### 前置要求

- Python 3.10+
- AstrBot 框架
- Fire-Eye 后端服务

### 安装步骤

1. 将插件目录复制到 AstrBot 的插件目录:
```bash
cp -r astrbot-plugin-fireeye-qq /path/to/astrbot/plugins/
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 配置插件 (编辑 `config.yaml`):
```yaml
fire_eye:
  api_url: "http://your-fire-eye-backend:8000/api/v1"
  api_key: "your-api-key"
```

4. 重启 AstrBot

## 使用方法

### 查询命令

查询知识图谱中的火灾事件、隐患等信息:

```
/火瞳查询 <查询内容>
/ht查询 <查询内容>
```

示例:
```
/火瞳查询 3.21火灾事故
/ht查询 电气隐患
```

### 统计命令

获取系统统计信息:

```
/火瞳统计
/ht统计
```

### 帮助命令

显示帮助信息:

```
/火瞳帮助
/ht帮助
```

## 配置说明

### config.yaml

```yaml
# Fire-Eye 后端 API 配置
fire_eye:
  api_url: "http://localhost:8000/api/v1"  # API 地址
  api_key: "your-api-key"                   # API 密钥
  timeout: 30                               # 请求超时（秒）
  retries: 3                                # 失败重试次数

# 会话管理配置
session:
  ttl: 1800  # 会话过期时间（秒），30分钟

# 请求队列配置
request_queue:
  max_concurrent: 5   # 最大并发请求数
  max_queue_size: 20  # 队列最大长度

# QQ 特定配置
qq:
  max_message_length: 4096  # QQ 消息最大长度
  polling_interval: 3       # 任务轮询间隔（秒）

# 日志配置
logging:
  level: "INFO"                  # 日志级别
  file: "./logs/fireeye-qq.log"  # 日志文件
  max_size: 10485760             # 日志文件最大大小
  backup_count: 5                # 保留日志文件数
```

## 项目结构

```
astrbot-plugin-fireeye-qq/
├── __init__.py              # 包初始化
├── main.py                  # 插件主入口
├── config.yaml              # 配置文件
├── README.md                # 本文件
├── api/
│   ├── __init__.py
│   └── client.py            # API 客户端
├── session/
│   ├── __init__.py
│   └── manager.py           # 会话管理器
├── queue/
│   ├── __init__.py
│   └── request_queue.py     # 请求队列
└── utils/
    ├── __init__.py
    └── formatter.py         # 消息格式化器
```

## 核心组件

### APIClient (api/client.py)

处理与 Fire-Eye 后端的所有 HTTP 通信:
- 自动重试机制
- 指数退避策略
- 请求日志记录

### SessionManager (session/manager.py)

管理用户会话和对话上下文:
- 自动会话创建和过期
- 对话历史记录
- 上下文保存

### RequestQueue (queue/request_queue.py)

智能请求队列管理:
- 并发控制
- 队列管理
- 负载均衡

### MessageFormatter (utils/formatter.py)

将 API 响应格式化为 QQ 消息:
- 查询结果格式化
- 统计信息格式化
- 错误消息处理
- 消息分割

## 命令处理流程

```
用户输入
   ↓
命令解析
   ↓
会话管理 (获取或创建会话)
   ↓
请求队列 (加入队列)
   ↓
API 调用 (查询后端)
   ↓
消息格式化 (格式化响应)
   ↓
发送给用户
```

## 错误处理

插件包含完善的错误处理机制:

- **网络错误**: 自动重试，最多3次
- **API 错误**: 返回友好的错误提示
- **队列满**: 提示用户稍后重试
- **会话过期**: 自动创建新会话

## 日志

日志文件位置: `./logs/fireeye-qq.log`

日志级别:
- DEBUG: 详细的调试信息
- INFO: 一般信息
- WARNING: 警告信息
- ERROR: 错误信息

## 性能指标

- 查询响应时间: < 3 秒 (p95)
- 最大并发请求: 5
- 队列最大长度: 20
- 会话过期时间: 30 分钟

## 故障排除

### 连接失败

检查:
1. Fire-Eye 后端是否运行
2. API URL 是否正确
3. API Key 是否有效
4. 网络连接是否正常

### 查询无结果

可能原因:
1. 知识图谱中没有相关数据
2. 查询关键词不匹配
3. 后端服务异常

### 消息格式错误

检查:
1. QQ 消息长度是否超过限制
2. 特殊字符是否正确转义
3. 消息格式化器配置是否正确

## 开发指南

### 添加新命令

1. 在 `main.py` 中添加新的命令处理器:

```python
@filter.command("新命令", alias={"别名"})
async def new_command(self, event: AstrMessageEvent):
    # 处理逻辑
    pass
```

2. 在 `utils/formatter.py` 中添加格式化方法

3. 更新帮助信息

### 扩展功能

- 添加新的 API 端点调用
- 实现新的消息格式化方式
- 增强会话管理功能

## 许可证

MIT License

## 联系方式

如有问题或建议，请联系系统管理员。

## 更新日志

### v1.0.0 (2026-02-17)

- 初始版本发布
- 支持查询、统计、帮助命令
- 完整的会话管理
- 请求队列管理
- 错误处理和日志记录
