# 火瞳插件集成指南

## 前提条件检查 ✅

在开始之前，请确认以下条件已满足：

- [x] AstrBot 已通过 Docker 部署并运行
- [x] Telegram Bot 已配置并连接
- [x] 火瞳后端系统正在运行
- [x] 可以访问火瞳后端 API

---

## 步骤 1: 准备插件文件

### 1.1 将插件复制到 AstrBot 插件目录

```bash
# 找到 AstrBot 的插件目录
# 通常在 Docker 容器中是 /app/plugins 或 /astrbot/plugins

# 方法 1: 如果使用 Docker volume 挂载
cp -r astrbot-plugin-fireeye /path/to/astrbot/plugins/

# 方法 2: 如果需要复制到容器内
docker cp astrbot-plugin-fireeye <astrbot-container-name>:/app/plugins/
```

### 1.2 验证文件结构

```bash
# 进入 AstrBot 容器
docker exec -it <astrbot-container-name> bash

# 检查插件目录
ls -la /app/plugins/astrbot-plugin-fireeye/

# 应该看到以下文件：
# - main.py
# - config.yaml
# - requirements.txt
# - api/
# - commands/
# - utils/
# 等等
```

---

## 步骤 2: 配置插件

### 2.1 编辑配置文件

```bash
# 在容器内或挂载的目录中编辑配置
nano /app/plugins/astrbot-plugin-fireeye/config.yaml
```

### 2.2 配置示例

```yaml
# 火瞳后端配置
fire_eye:
  # 如果火瞳后端也在 Docker 中，使用容器名称或服务名
  api_url: "http://fireeye-backend:8000"  # 或 "http://localhost:8000"
  api_key: "your-api-key-here"  # 从火瞳后端管理员获取
  timeout: 30
  retries: 3

# 会话配置
session:
  ttl: 1800  # 30分钟

# 请求队列配置
request_queue:
  max_concurrent: 5
  max_queue_size: 20

# 意图检测（暂时禁用）
intent_detection:
  enabled: false

# 文件上传配置
file_upload:
  retain_files_on_server: false
  temp_dir: "/tmp/fireeye"
  max_file_size: 10485760  # 10MB

# 日志配置
logging:
  level: "INFO"
  file: "/app/logs/fireeye.log"
  max_size: "10 MB"
  backup_count: 5
```

### 2.3 获取 API 密钥

```bash
# 方法 1: 从火瞳后端环境变量获取
docker exec <fireeye-backend-container> printenv | grep API_KEY

# 方法 2: 查看火瞳后端配置
docker exec <fireeye-backend-container> cat /app/.env | grep ASTRBOT_API_KEYS

# 方法 3: 如果没有配置，需要在火瞳后端添加
# 编辑 fire-eye-system/backend/.env
# 添加: ASTRBOT_API_KEYS=your-generated-key-here
```

---

## 步骤 3: 安装插件依赖

### 3.1 在 AstrBot 容器中安装依赖

```bash
# 进入容器
docker exec -it <astrbot-container-name> bash

# 进入插件目录
cd /app/plugins/astrbot-plugin-fireeye

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import aiohttp, yaml, loguru; print('Dependencies OK')"
```

### 3.2 如果使用 Docker Compose（推荐）

修改 AstrBot 的 Dockerfile 或 docker-compose.yml：

```dockerfile
# 在 Dockerfile 中添加
COPY astrbot-plugin-fireeye/requirements.txt /tmp/fireeye-requirements.txt
RUN pip install -r /tmp/fireeye-requirements.txt
```

或在 docker-compose.yml 中：

```yaml
services:
  astrbot:
    # ... 其他配置
    volumes:
      - ./astrbot-plugin-fireeye:/app/plugins/astrbot-plugin-fireeye:ro
    command: sh -c "pip install -r /app/plugins/astrbot-plugin-fireeye/requirements.txt && python -m astrbot"
```

---

## 步骤 4: 配置网络连接

### 4.1 确保容器可以互相通信

如果使用 Docker Compose，确保所有服务在同一网络中：

```yaml
# docker-compose.yml
version: '3.8'

services:
  astrbot:
    image: astrbot:latest
    container_name: astrbot
    networks:
      - fireeye-network
    volumes:
      - ./astrbot-plugin-fireeye:/app/plugins/astrbot-plugin-fireeye
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}

  fireeye-backend:
    image: fireeye-backend:latest
    container_name: fireeye-backend
    networks:
      - fireeye-network
    ports:
      - "8000:8000"

networks:
  fireeye-network:
    driver: bridge
```

### 4.2 测试网络连接

```bash
# 从 AstrBot 容器测试火瞳后端连接
docker exec <astrbot-container-name> curl http://fireeye-backend:8000/health

# 应该返回健康检查响应
```

---

## 步骤 5: 注册插件到 AstrBot

### 5.1 检查 AstrBot 插件加载机制

AstrBot 通常会自动加载 `plugins/` 目录下的插件。检查 AstrBot 的配置：

```bash
# 查看 AstrBot 配置
docker exec <astrbot-container-name> cat /app/config.yaml

# 或
docker exec <astrbot-container-name> cat /app/config.json
```

### 5.2 如果需要手动注册

某些 AstrBot 版本可能需要在配置文件中明确启用插件：

```yaml
# AstrBot config.yaml
plugins:
  enabled:
    - astrbot-plugin-fireeye
  
  # 或者
  load_path:
    - /app/plugins/astrbot-plugin-fireeye
```

---

## 步骤 6: 重启 AstrBot

### 6.1 重启容器

```bash
# 方法 1: 重启容器
docker restart <astrbot-container-name>

# 方法 2: 使用 docker-compose
docker-compose restart astrbot

# 方法 3: 完全重新创建
docker-compose down
docker-compose up -d
```

### 6.2 查看启动日志

```bash
# 查看 AstrBot 日志
docker logs -f <astrbot-container-name>

# 查找插件加载信息
docker logs <astrbot-container-name> 2>&1 | grep -i "fire-eye\|fireeye"

# 应该看到类似：
# [INFO] Loading plugin: Fire-Eye
# [INFO] Fire-Eye plugin loaded successfully
```

---

## 步骤 7: 验证插件功能

### 7.1 在 Telegram 中测试

打开你的 Telegram Bot，发送以下命令：

```
/火瞳帮助
```

或

```
/ht帮助
```

**预期响应**：
```
🔥 火瞳系统 - 帮助信息

📖 可用命令:

1️⃣ 查询命令
   /火瞳查询 <查询内容>
   /ht查询 <查询内容>
   ...
```

### 7.2 测试查询功能

```
/火瞳查询 测试
```

**预期响应**：
- 如果有数据：显示查询结果
- 如果没有数据：显示"未找到相关信息"
- 如果出错：显示错误信息

### 7.3 测试统计功能

```
/火瞳统计
```

**预期响应**：显示系统统计信息

---

## 步骤 8: 故障排除

### 8.1 插件未加载

**症状**：发送命令没有响应

**检查步骤**：

```bash
# 1. 检查插件文件是否存在
docker exec <astrbot-container-name> ls -la /app/plugins/astrbot-plugin-fireeye/

# 2. 检查 Python 导入
docker exec <astrbot-container-name> python -c "import sys; sys.path.insert(0, '/app/plugins/astrbot-plugin-fireeye'); import main; print('OK')"

# 3. 检查 AstrBot 日志
docker logs <astrbot-container-name> 2>&1 | grep -i error

# 4. 检查插件日志
docker exec <astrbot-container-name> cat /app/logs/fireeye.log
```

### 8.2 无法连接后端

**症状**：命令返回"连接失败"

**检查步骤**：

```bash
# 1. 测试网络连接
docker exec <astrbot-container-name> ping fireeye-backend

# 2. 测试 HTTP 连接
docker exec <astrbot-container-name> curl -v http://fireeye-backend:8000/health

# 3. 检查配置
docker exec <astrbot-container-name> cat /app/plugins/astrbot-plugin-fireeye/config.yaml | grep api_url

# 4. 检查火瞳后端是否运行
docker ps | grep fireeye-backend
```

### 8.3 API 密钥错误

**症状**：返回"认证失败"

**解决方案**：

```bash
# 1. 检查配置的 API 密钥
docker exec <astrbot-container-name> cat /app/plugins/astrbot-plugin-fireeye/config.yaml | grep api_key

# 2. 检查后端配置的密钥
docker exec <fireeye-backend-container> cat /app/.env | grep ASTRBOT_API_KEYS

# 3. 确保密钥匹配
# 如果不匹配，更新插件配置或后端配置

# 4. 重启服务
docker restart <astrbot-container-name>
```

### 8.4 依赖缺失

**症状**：启动时报 ImportError

**解决方案**：

```bash
# 重新安装依赖
docker exec <astrbot-container-name> pip install -r /app/plugins/astrbot-plugin-fireeye/requirements.txt

# 重启容器
docker restart <astrbot-container-name>
```

---

## 步骤 9: 生产环境优化

### 9.1 配置持久化日志

```yaml
# docker-compose.yml
services:
  astrbot:
    volumes:
      - ./logs:/app/logs  # 持久化日志
      - ./astrbot-plugin-fireeye:/app/plugins/astrbot-plugin-fireeye
```

### 9.2 配置环境变量

```yaml
# docker-compose.yml
services:
  astrbot:
    environment:
      - FIREEYE_API_KEY=${FIREEYE_API_KEY}
      - FIREEYE_API_URL=http://fireeye-backend:8000
```

然后在 config.yaml 中使用环境变量：

```yaml
fire_eye:
  api_url: "${FIREEYE_API_URL}"
  api_key: "${FIREEYE_API_KEY}"
```

### 9.3 配置健康检查

```yaml
# docker-compose.yml
services:
  astrbot:
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 步骤 10: 监控和维护

### 10.1 查看日志

```bash
# 实时查看 AstrBot 日志
docker logs -f <astrbot-container-name>

# 查看插件日志
docker exec <astrbot-container-name> tail -f /app/logs/fireeye.log

# 查看最近的错误
docker logs <astrbot-container-name> 2>&1 | grep ERROR
```

### 10.2 监控资源使用

```bash
# 查看容器资源使用
docker stats <astrbot-container-name>

# 查看磁盘使用
docker exec <astrbot-container-name> df -h
```

### 10.3 定期清理

```bash
# 清理临时文件
docker exec <astrbot-container-name> find /tmp/fireeye -type f -mtime +1 -delete

# 清理旧日志
docker exec <astrbot-container-name> find /app/logs -name "*.log.*" -mtime +7 -delete
```

---

## 完整的 Docker Compose 示例

```yaml
version: '3.8'

services:
  # 火瞳后端
  fireeye-backend:
    image: fireeye-backend:latest
    container_name: fireeye-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_HOST=redis
      - ASTRBOT_API_KEYS=your-secret-key-here
    networks:
      - fireeye-network
    depends_on:
      - neo4j
      - redis

  # Neo4j 数据库
  neo4j:
    image: neo4j:latest
    container_name: neo4j
    restart: unless-stopped
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes:
      - neo4j-data:/data
    networks:
      - fireeye-network

  # Redis
  redis:
    image: redis:alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    networks:
      - fireeye-network

  # AstrBot
  astrbot:
    image: astrbot:latest
    container_name: astrbot
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - FIREEYE_API_KEY=your-secret-key-here
      - FIREEYE_API_URL=http://fireeye-backend:8000
    volumes:
      - ./astrbot-plugin-fireeye:/app/plugins/astrbot-plugin-fireeye:ro
      - ./logs:/app/logs
    networks:
      - fireeye-network
    depends_on:
      - fireeye-backend
    command: >
      sh -c "pip install -r /app/plugins/astrbot-plugin-fireeye/requirements.txt &&
             python -m astrbot"

networks:
  fireeye-network:
    driver: bridge

volumes:
  neo4j-data:
```

---

## 快速启动命令

```bash
# 1. 创建 .env 文件
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
FIREEYE_API_KEY=your-secret-key
EOF

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f astrbot

# 4. 测试
# 在 Telegram 中发送: /火瞳帮助
```

---

## 验证清单

完成集成后，请验证以下项目：

- [ ] AstrBot 容器正常运行
- [ ] 插件文件已复制到正确位置
- [ ] 配置文件已正确设置
- [ ] 依赖已安装
- [ ] 网络连接正常
- [ ] API 密钥正确
- [ ] 插件已加载（查看日志）
- [ ] `/火瞳帮助` 命令有响应
- [ ] `/火瞳查询` 命令可以执行
- [ ] `/火瞳统计` 命令可以执行
- [ ] 日志正常记录
- [ ] 没有错误信息

---

## 下一步

集成完成后，你可以：

1. **测试所有功能**
   - 查询命令
   - 文件上传
   - 统计查看

2. **配置监控**
   - 设置日志监控
   - 配置告警

3. **用户培训**
   - 分享用户指南
   - 演示功能

4. **收集反馈**
   - 记录使用问题
   - 优化配置

---

**需要帮助？**

如果遇到问题，请：
1. 查看日志文件
2. 参考故障排除部分
3. 查看 `docs/USER_GUIDE.md`
4. 查看 `docs/DEPLOYMENT_GUIDE.md`

---

**最后更新**: 2026-02-17
