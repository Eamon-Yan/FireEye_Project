# AstrBot Fire-Eye Plugin

火瞳系统的 AstrBot 集成插件，为聊天平台提供火灾调查知识图谱查询能力。

## 功能特性

- 🔍 **知识图谱查询**: 通过自然语言查询火灾事故信息
- 📄 **文档分析**: 上传火灾调查报告进行自动分析
- 📊 **统计信息**: 查看火灾事故统计数据
- 💬 **多轮对话**: 支持上下文感知的连续对话
- 🔄 **异步处理**: 大文件和复杂分析任务异步处理

## 支持的平台

- QQ
- Telegram
- 微信
- 钉钉
- 飞书

## 安装

1. 将插件目录复制到 AstrBot 的 plugins 目录
2. 配置 `config.yaml` 文件
3. 重启 AstrBot

## 配置

编辑 `config.yaml`:

```yaml
fire_eye:
  api_url: "http://localhost:8000/api/v1"
  api_key: "your-api-key-here"
  timeout: 30
  retries: 3

session:
  ttl: 1800  # 30 minutes

request_queue:
  max_concurrent: 5
  max_queue_size: 20

file_upload:
  retain_files_on_server: false
  temp_dir: "./temp"
  max_file_size: 10485760  # 10MB

logging:
  level: "INFO"
  file: "./logs/fireeye.log"
```

## 使用方法

### 查询命令

```
/火瞳查询 3.21火灾事故
/ht查询 电气火灾原因
```

### 上传文档

```
/火瞳上传
然后发送文件（支持 PDF、DOCX、TXT）
```

### 查看统计

```
/火瞳统计
/火瞳统计 隐患
```

### 帮助信息

```
/火瞳帮助
```

## 开发

### 目录结构

```
astrbot-plugin-fireeye/
├── __init__.py
├── main.py              # 插件入口
├── config.yaml          # 配置文件
├── requirements.txt     # 依赖
├── api/                 # API 客户端
│   ├── client.py
│   └── polling.py
├── commands/            # 命令处理器
│   ├── query_handler.py
│   ├── upload_handler.py
│   ├── stats_handler.py
│   └── help_handler.py
├── session/             # 会话管理
│   └── manager.py
├── queue/               # 请求队列
│   └── request_queue.py
└── utils/               # 工具类
    ├── formatter.py
    └── file_handler.py
```

### 依赖

- aiohttp
- pyyaml
- python-magic (可选，用于文件类型检测)

## 许可证

MIT License

## 联系方式

- 项目主页: https://github.com/your-org/fire-eye-system
- 问题反馈: https://github.com/your-org/fire-eye-system/issues
