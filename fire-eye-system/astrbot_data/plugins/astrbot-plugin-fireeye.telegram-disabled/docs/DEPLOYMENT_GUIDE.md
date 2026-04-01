# 火瞳系统 AstrBot 插件 - 部署指南

## 目录
- [部署前准备](#部署前准备)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [监控和维护](#监控和维护)
- [故障恢复](#故障恢复)

---

## 部署前准备

### 系统要求

#### 硬件要求
- CPU: 2核心以上
- 内存: 2GB 以上
- 磁盘: 10GB 可用空间

#### 软件要求
- 操作系统: Linux (推荐 Ubuntu 20.04+) / Windows Server
- Python: 3.8+
- AstrBot: 最新稳定版
- 网络: 能够访问火瞳后端系统

### 依赖服务

1. **火瞳后端系统**
   - 确保后端 API 可访问
   - 获取有效的 API 密钥
   - 测试网络连通性

2. **AstrBot 框架**
   - 已安装并配置
   - 已连接到聊天平台

---

## 生产环境部署

### 步骤 1: 准备部署目录

```bash
# 创建部署目录
sudo mkdir -p /opt/astrbot/plugins
cd /opt/astrbot/plugins

# 克隆或复制插件
git clone <repository-url> astrbot-plugin-fireeye
# 或
cp -r /path/to/astrbot-plugin-fireeye .

cd astrbot-plugin-fireeye
```

### 步骤 2: 安装依赖

```bash
# 使用虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import aiohttp, yaml, loguru; print('Dependencies OK')"
```

### 步骤 3: 配置插件

```bash
# 复制配置模板
cp config.yaml.example config.yaml

# 编辑配置文件
nano config.yaml
```

**生产环境配置示例**:
```yaml
fire_eye:
  api_url: "https://fireeye-api.example.com"
  api_key: "${FIREEYE_API_KEY}"  # 从环境变量读取
  timeout: 30
  retries: 3

session:
  ttl: 1800

request_queue:
  max_concurrent: 10  # 生产环境可以增加
  max_queue_size: 50

file_upload:
  retain_files_on_server: false
  temp_dir: "/var/tmp/fireeye"
  max_file_size: 10485760

logging:
  level: "INFO"  # 生产环境使用 INFO
  file: "/var/log/fireeye/plugin.log"
  max_size: "50 MB"
  backup_count: 10
```

### 步骤 4: 设置环境变量

```bash
# 创建环境变量文件
cat > .env << EOF
FIREEYE_API_KEY=your-production-api-key-here
EOF

# 设置权限
chmod 600 .env

# 加载环境变量
source .env
```

### 步骤 5: 创建必要的目录

```bash
# 创建日志目录
sudo mkdir -p /var/log/fireeye
sudo chown $USER:$USER /var/log/fireeye

# 创建临时文件目录
sudo mkdir -p /var/tmp/fireeye
sudo chown $USER:$USER /var/tmp/fireeye
```

### 步骤 6: 配置日志轮转

```bash
# 创建 logrotate 配置
sudo nano /etc/logrotate.d/fireeye-plugin

# 添加以下内容:
/var/log/fireeye/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 astrbot astrbot
    sharedscripts
    postrotate
        systemctl reload astrbot
    endscript
}
```

### 步骤 7: 配置 Systemd 服务（如果独立运行）

```bash
# 创建服务文件
sudo nano /etc/systemd/system/astrbot.service

# 添加以下内容:
[Unit]
Description=AstrBot with Fire-Eye Plugin
After=network.target

[Service]
Type=simple
User=astrbot
WorkingDirectory=/opt/astrbot
Environment="PATH=/opt/astrbot/venv/bin"
EnvironmentFile=/opt/astrbot/plugins/astrbot-plugin-fireeye/.env
ExecStart=/opt/astrbot/venv/bin/python -m astrbot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start astrbot

# 设置开机自启
sudo systemctl enable astrbot

# 查看状态
sudo systemctl status astrbot
```

### 步骤 8: 验证部署

```bash
# 检查日志
tail -f /var/log/fireeye/plugin.log

# 测试插件
# 在聊天平台发送: /火瞳帮助

# 检查进程
ps aux | grep astrbot
```

---

## Docker 部署

### Dockerfile

```dockerfile
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制插件代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/logs /app/temp

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 暴露端口（如果需要）
# EXPOSE 8080

# 启动命令
CMD ["python", "-m", "astrbot"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  astrbot-fireeye:
    build: .
    container_name: astrbot-fireeye
    restart: unless-stopped
    environment:
      - FIREEYE_API_KEY=${FIREEYE_API_KEY}
      - FIREEYE_API_URL=${FIREEYE_API_URL}
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./logs:/app/logs
      - ./temp:/app/temp
    networks:
      - astrbot-network
    depends_on:
      - fireeye-backend

  fireeye-backend:
    image: fireeye-backend:latest
    container_name: fireeye-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    networks:
      - astrbot-network

networks:
  astrbot-network:
    driver: bridge
```

### 部署步骤

```bash
# 1. 创建 .env 文件
cat > .env << EOF
FIREEYE_API_KEY=your-api-key
FIREEYE_API_URL=http://fireeye-backend:8000
EOF

# 2. 构建镜像
docker-compose build

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f astrbot-fireeye

# 5. 停止服务
docker-compose down
```

---

## 监控和维护

### 日志监控

#### 实时查看日志
```bash
# 查看最新日志
tail -f /var/log/fireeye/plugin.log

# 查看错误日志
grep ERROR /var/log/fireeye/plugin.log

# 查看最近100行
tail -n 100 /var/log/fireeye/plugin.log
```

#### 日志分析
```bash
# 统计错误数量
grep -c ERROR /var/log/fireeye/plugin.log

# 查找特定错误
grep "ConnectionError" /var/log/fireeye/plugin.log

# 按时间过滤
grep "2026-02-17" /var/log/fireeye/plugin.log
```

### 性能监控

#### 系统资源监控
```bash
# CPU 和内存使用
top -p $(pgrep -f astrbot)

# 详细资源信息
ps aux | grep astrbot

# 磁盘使用
df -h /var/log/fireeye
df -h /var/tmp/fireeye
```

#### 应用监控指标

监控以下指标：
- 请求响应时间
- 错误率
- 活跃会话数
- 队列长度
- 文件上传成功率

### 健康检查

```bash
# 创建健康检查脚本
cat > /opt/astrbot/health_check.sh << 'EOF'
#!/bin/bash

# 检查进程
if ! pgrep -f astrbot > /dev/null; then
    echo "ERROR: AstrBot process not running"
    exit 1
fi

# 检查日志中的错误
ERROR_COUNT=$(grep -c "CRITICAL\|FATAL" /var/log/fireeye/plugin.log | tail -n 100)
if [ $ERROR_COUNT -gt 10 ]; then
    echo "WARNING: High error count: $ERROR_COUNT"
    exit 1
fi

# 检查磁盘空间
DISK_USAGE=$(df -h /var/log/fireeye | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "WARNING: Disk usage high: ${DISK_USAGE}%"
    exit 1
fi

echo "OK: All checks passed"
exit 0
EOF

chmod +x /opt/astrbot/health_check.sh

# 添加到 crontab
crontab -e
# 添加: */5 * * * * /opt/astrbot/health_check.sh >> /var/log/fireeye/health.log 2>&1
```

### 定期维护任务

#### 清理临时文件
```bash
# 创建清理脚本
cat > /opt/astrbot/cleanup.sh << 'EOF'
#!/bin/bash

# 清理超过1小时的临时文件
find /var/tmp/fireeye -type f -mmin +60 -delete

# 清理旧日志
find /var/log/fireeye -name "*.log.*" -mtime +30 -delete

echo "Cleanup completed at $(date)"
EOF

chmod +x /opt/astrbot/cleanup.sh

# 添加到 crontab（每小时执行）
# 0 * * * * /opt/astrbot/cleanup.sh >> /var/log/fireeye/cleanup.log 2>&1
```

#### 数据库备份（如果有本地数据）
```bash
# 备份会话数据（如果持久化）
# 根据实际情况调整
```

---

## 故障恢复

### 常见故障处理

#### 1. 插件无法启动

**症状**: AstrBot 启动失败或插件未加载

**诊断**:
```bash
# 查看启动日志
journalctl -u astrbot -n 100

# 检查配置文件
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# 检查依赖
pip list | grep -E "aiohttp|yaml|loguru"
```

**解决**:
```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 检查配置文件语法
yamllint config.yaml

# 重启服务
sudo systemctl restart astrbot
```

#### 2. 无法连接后端

**症状**: 查询时提示连接失败

**诊断**:
```bash
# 测试网络连接
curl -v http://fireeye-backend:8000/health

# 检查 DNS 解析
nslookup fireeye-backend

# 检查防火墙
sudo iptables -L | grep 8000
```

**解决**:
```bash
# 更新后端地址
nano config.yaml

# 检查 API 密钥
echo $FIREEYE_API_KEY

# 重启服务
sudo systemctl restart astrbot
```

#### 3. 内存泄漏

**症状**: 内存使用持续增长

**诊断**:
```bash
# 监控内存使用
watch -n 5 'ps aux | grep astrbot'

# 查看会话数量
# 需要添加监控端点
```

**解决**:
```bash
# 重启服务
sudo systemctl restart astrbot

# 调整会话 TTL
# 在 config.yaml 中减少 session.ttl

# 启用会话清理
# 确保 cleanup_expired_sessions 正常运行
```

#### 4. 磁盘空间不足

**症状**: 无法写入日志或临时文件

**诊断**:
```bash
# 检查磁盘使用
df -h

# 查找大文件
du -sh /var/log/fireeye/*
du -sh /var/tmp/fireeye/*
```

**解决**:
```bash
# 清理旧日志
find /var/log/fireeye -name "*.log.*" -mtime +7 -delete

# 清理临时文件
rm -rf /var/tmp/fireeye/*

# 配置日志轮转
sudo logrotate -f /etc/logrotate.d/fireeye-plugin
```

### 紧急恢复流程

#### 完全重启
```bash
# 1. 停止服务
sudo systemctl stop astrbot

# 2. 清理临时数据
rm -rf /var/tmp/fireeye/*

# 3. 检查配置
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"

# 4. 启动服务
sudo systemctl start astrbot

# 5. 验证
tail -f /var/log/fireeye/plugin.log
```

#### 回滚到上一版本
```bash
# 1. 停止服务
sudo systemctl stop astrbot

# 2. 备份当前版本
cp -r /opt/astrbot/plugins/astrbot-plugin-fireeye /opt/astrbot/plugins/astrbot-plugin-fireeye.backup

# 3. 恢复上一版本
git checkout <previous-version-tag>
# 或
cp -r /opt/astrbot/plugins/astrbot-plugin-fireeye.old /opt/astrbot/plugins/astrbot-plugin-fireeye

# 4. 重新安装依赖
pip install -r requirements.txt

# 5. 启动服务
sudo systemctl start astrbot
```

### 数据恢复

#### 恢复会话数据
```bash
# 如果会话数据持久化到文件
# 从备份恢复
cp /backup/sessions.json /opt/astrbot/plugins/astrbot-plugin-fireeye/data/
```

#### 恢复配置
```bash
# 从备份恢复配置
cp /backup/config.yaml /opt/astrbot/plugins/astrbot-plugin-fireeye/
```

---

## 安全建议

### 1. API 密钥管理
- 使用环境变量存储密钥
- 定期轮换密钥
- 不要将密钥提交到版本控制

### 2. 文件权限
```bash
# 设置适当的文件权限
chmod 600 config.yaml
chmod 600 .env
chmod 755 /opt/astrbot/plugins/astrbot-plugin-fireeye
```

### 3. 网络安全
- 使用 HTTPS 连接后端
- 配置防火墙规则
- 限制访问 IP

### 4. 日志安全
- 不要记录敏感信息
- 定期清理旧日志
- 限制日志文件访问权限

---

## 性能优化建议

### 1. 并发配置
```yaml
request_queue:
  max_concurrent: 20  # 根据服务器性能调整
  max_queue_size: 100
```

### 2. 连接池
- 配置适当的连接池大小
- 启用连接复用

### 3. 缓存策略
- 启用统计信息缓存
- 配置适当的 TTL

### 4. 资源限制
```bash
# 使用 systemd 限制资源
[Service]
MemoryLimit=2G
CPUQuota=200%
```

---

## 升级指南

### 升级步骤

```bash
# 1. 备份当前版本
cp -r /opt/astrbot/plugins/astrbot-plugin-fireeye /backup/astrbot-plugin-fireeye-$(date +%Y%m%d)

# 2. 停止服务
sudo systemctl stop astrbot

# 3. 拉取新版本
cd /opt/astrbot/plugins/astrbot-plugin-fireeye
git pull origin main

# 4. 更新依赖
pip install -r requirements.txt --upgrade

# 5. 检查配置变更
diff config.yaml config.yaml.example

# 6. 运行迁移脚本（如果有）
# python migrate.py

# 7. 启动服务
sudo systemctl start astrbot

# 8. 验证
tail -f /var/log/fireeye/plugin.log
```

---

## 联系支持

如果遇到无法解决的问题：

1. 收集以下信息：
   - 错误日志
   - 配置文件（隐藏敏感信息）
   - 系统信息
   - 复现步骤

2. 联系技术支持：
   - Email: support@example.com
   - Issue Tracker: https://github.com/.../issues

---

**最后更新**: 2026-02-17
