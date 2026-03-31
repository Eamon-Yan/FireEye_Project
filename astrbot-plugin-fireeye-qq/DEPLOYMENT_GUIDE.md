# 火瞳 QQ 插件部署指南

本指南说明如何在 AstrBot 中部署和配置火瞳 QQ 插件。

## 前置要求

- Python 3.10 或更高版本
- AstrBot 框架已安装
- Fire-Eye 后端服务正在运行
- QQ 机器人账号已配置

## 安装步骤

### 1. 获取插件

从 GitHub 克隆或下载插件:

```bash
git clone https://github.com/your-repo/astrbot-plugin-fireeye-qq.git
```

或直接下载 ZIP 文件并解压。

### 2. 复制到 AstrBot 插件目录

```bash
# 找到 AstrBot 的插件目录
cd /path/to/astrbot

# 复制插件
cp -r /path/to/astrbot-plugin-fireeye-qq ./plugins/
```

### 3. 安装依赖

```bash
# 进入插件目录
cd plugins/astrbot-plugin-fireeye-qq

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置插件

编辑 `config.yaml` 文件:

```yaml
fire_eye:
  api_url: "http://your-fire-eye-backend:8000/api/v1"
  api_key: "your-api-key-here"
  timeout: 30
  retries: 3

session:
  ttl: 1800

request_queue:
  max_concurrent: 5
  max_queue_size: 20

qq:
  max_message_length: 4096
  polling_interval: 3

logging:
  level: "INFO"
  file: "./logs/fireeye-qq.log"
  max_size: 10485760
  backup_count: 5
```

**重要配置项:**

- `api_url`: Fire-Eye 后端 API 地址
- `api_key`: Fire-Eye API 密钥（从后端获取）
- `max_concurrent`: 最大并发请求数（根据系统能力调整）
- `max_queue_size`: 队列最大长度（防止内存溢出）

### 5. 创建日志目录

```bash
mkdir -p logs
```

### 6. 重启 AstrBot

```bash
# 重启 AstrBot 服务
systemctl restart astrbot

# 或者如果使用 Docker
docker restart astrbot
```

### 7. 验证安装

在 QQ 中发送命令验证:

```
/火瞳帮助
```

如果收到帮助信息，说明插件已成功安装。

## 配置详解

### Fire-Eye 后端配置

获取 API Key:

1. 登录 Fire-Eye 后端管理界面
2. 进入 API 管理
3. 创建新的 API Key
4. 复制 Key 到插件配置

### 性能调优

根据系统负载调整以下参数:

```yaml
request_queue:
  max_concurrent: 5      # 增加以支持更多并发
  max_queue_size: 20     # 增加以支持更长的队列
```

**建议值:**

- 小型部署 (< 100 用户): max_concurrent=3, max_queue_size=10
- 中型部署 (100-1000 用户): max_concurrent=5, max_queue_size=20
- 大型部署 (> 1000 用户): max_concurrent=10, max_queue_size=50

### 日志配置

调整日志级别:

```yaml
logging:
  level: "DEBUG"  # 开发环境使用 DEBUG
  level: "INFO"   # 生产环境使用 INFO
```

## Docker 部署

### 使用 Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  astrbot:
    image: astrbot:latest
    ports:
      - "8080:8080"
    volumes:
      - ./plugins/astrbot-plugin-fireeye-qq:/app/plugins/astrbot-plugin-fireeye-qq
      - ./logs:/app/logs
    environment:
      - FIRE_EYE_API_URL=http://fire-eye-backend:8000/api/v1
      - FIRE_EYE_API_KEY=your-api-key
    depends_on:
      - fire-eye-backend

  fire-eye-backend:
    image: fire-eye-backend:latest
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URL=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
    depends_on:
      - neo4j
      - redis

  neo4j:
    image: neo4j:latest
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password

  redis:
    image: redis:latest
    ports:
      - "6379:6379"
```

启动服务:

```bash
docker-compose up -d
```

## 故障排除

### 插件无法加载

检查:
1. 插件目录结构是否正确
2. `main.py` 中的 `Main` 类是否存在
3. 依赖是否已安装
4. Python 版本是否 >= 3.10

查看日志:
```bash
tail -f logs/fireeye-qq.log
```

### 连接失败

检查:
1. Fire-Eye 后端是否运行
2. API URL 是否正确
3. API Key 是否有效
4. 防火墙是否允许连接

测试连接:
```bash
curl -H "X-API-Key: your-api-key" http://your-fire-eye-backend:8000/api/v1/chat/stats
```

### 查询无响应

可能原因:
1. 后端服务过载
2. 数据库连接问题
3. 网络延迟

解决方案:
1. 检查后端日志
2. 减少 `max_concurrent` 值
3. 增加 `timeout` 值

### 内存占用过高

可能原因:
1. 会话数过多
2. 队列堆积

解决方案:
1. 减少 `session.ttl` 值
2. 减少 `max_queue_size` 值
3. 增加 `max_concurrent` 值

## 监控和维护

### 监控指标

监控以下指标:
- 活跃会话数
- 队列长度
- 平均响应时间
- 错误率

### 日志分析

查看最近的错误:
```bash
grep ERROR logs/fireeye-qq.log | tail -20
```

查看性能指标:
```bash
grep "Request" logs/fireeye-qq.log | tail -20
```

### 定期维护

1. **清理过期会话**: 每小时自动执行
2. **日志轮转**: 每天自动执行
3. **性能优化**: 每周检查一次

## 升级指南

### 升级插件

1. 备份当前配置:
```bash
cp config.yaml config.yaml.backup
```

2. 下载新版本:
```bash
git pull origin main
```

3. 安装新依赖:
```bash
pip install -r requirements.txt
```

4. 重启 AstrBot:
```bash
systemctl restart astrbot
```

### 回滚

如果升级出现问题:

1. 恢复备份:
```bash
cp config.yaml.backup config.yaml
```

2. 恢复旧版本:
```bash
git checkout <old-version>
```

3. 重启 AstrBot:
```bash
systemctl restart astrbot
```

## 安全建议

1. **API Key 管理**:
   - 定期更换 API Key
   - 不要在代码中硬编码 API Key
   - 使用环境变量存储敏感信息

2. **访问控制**:
   - 限制 QQ 群组中的命令使用
   - 实现用户权限检查

3. **日志安全**:
   - 定期清理日志
   - 不要在日志中记录敏感信息

4. **网络安全**:
   - 使用 HTTPS 连接
   - 配置防火墙规则

## 支持和反馈

如有问题或建议:

1. 查看 [README.md](README.md)
2. 查看日志文件
3. 联系系统管理员
4. 提交 Issue 到 GitHub

## 许可证

MIT License
