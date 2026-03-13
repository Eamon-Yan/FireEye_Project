# 火瞳系统手动测试指南

## 测试日期
2026-02-18

## 测试目标
验证火瞳后端 API 和 AstrBot 插件的集成是否正常工作

---

## 测试前准备

### 1. 确认所有容器正在运行
```bash
docker ps
```

应该看到以下容器：
- `astrbot` - 运行中
- `fire-eye-backend` - 运行中
- `fire-eye-redis` - 运行中
- `fire-eye-neo4j` - 运行中

### 2. 确认 API 密钥
API 密钥: `smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA`

---

## 第一部分：后端 API 测试

### 测试 1.1: 健康检查
```bash
docker exec astrbot curl -s http://fire-eye-backend:8000/health
```

**预期结果**: 返回 JSON，包含 `{"status": "healthy"}` 或类似信息

---

### 测试 1.2: 统计接口测试
```bash
docker exec astrbot curl -s http://fire-eye-backend:8000/api/v1/chat/stats \
  -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
```

**预期结果**: 返回 JSON，包含统计数据
```json
{
  "status": "success",
  "data": {
    "total_events": 数字,
    "total_entities": 数字,
    "total_relationships": 数字,
    ...
  }
}
```

---

### 测试 1.3: 查询接口测试
```bash
docker exec astrbot curl -s -X POST http://fire-eye-backend:8000/api/v1/chat/query \
  -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" \
  -H "Content-Type: application/json" \
  -d '{"query": "火灾"}'
```

**预期结果**: 返回查询结果或空结果
```json
{
  "status": "success",
  "data": {
    "results": [...],
    "session_id": "uuid-string"
  }
}
```

---

### 测试 1.4: 认证失败测试
```bash
docker exec astrbot curl -s http://fire-eye-backend:8000/api/v1/chat/stats \
  -H "X-API-Key: wrong-key"
```

**预期结果**: 返回 401 错误
```json
{
  "detail": "Invalid API key"
}
```

---

## 第二部分：插件状态检查

### 测试 2.1: 查看插件加载状态
```bash
docker logs astrbot 2>&1 | grep -i "fire-eye"
```

**预期结果**: 应该看到类似以下内容
```
[Fire-Eye] Plugin initialized v1.0.0
```

---

### 测试 2.2: 查看插件日志
```bash
docker exec astrbot cat /AstrBot/data/logs/fireeye.log
```

**预期结果**: 
- 如果文件不存在，说明插件还没有执行日志记录操作（正常）
- 如果文件存在，查看是否有错误信息

---

### 测试 2.3: 检查插件文件完整性
```bash
docker exec astrbot ls -la /AstrBot/data/plugins/astrbot-plugin-fireeye/
```

**预期结果**: 应该看到所有插件文件
```
main.py
config.yaml
api/
commands/
utils/
session/
request_queue_module/
...
```

---

## 第三部分：Telegram Bot 测试

### 测试 3.1: 检查 Telegram Bot 状态
```bash
docker logs astrbot 2>&1 | grep -i "telegram"
```

**预期结果**: 应该看到
```
Telegram Platform Adapter is running.
```

---

### 测试 3.2: 在 Telegram 中测试基础命令

由于当前插件是简化版本，还没有实现命令处理器，所以 Telegram 命令暂时无法使用。

**当前状态**: 
- ❌ `/火瞳帮助` - 未实现
- ❌ `/火瞳查询` - 未实现
- ❌ `/火瞳统计` - 未实现
- ❌ `/火瞳上传` - 未实现

**下一步**: 需要实现完整的命令处理器

---

## 第四部分：网络连通性测试

### 测试 4.1: AstrBot 到后端的连接
```bash
docker exec astrbot ping -c 3 fire-eye-backend
```

**预期结果**: 成功 ping 通

---

### 测试 4.2: 后端到 Redis 的连接
```bash
docker exec fire-eye-backend ping -c 3 fire-eye-redis
```

**预期结果**: 成功 ping 通

---

### 测试 4.3: 后端到 Neo4j 的连接
```bash
docker exec fire-eye-backend ping -c 3 fire-eye-neo4j
```

**预期结果**: 成功 ping 通

---

## 第五部分：数据库状态检查

### 测试 5.1: 检查 Neo4j 数据
```bash
docker exec fire-eye-neo4j cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n) as node_count"
```

**预期结果**: 返回节点数量

---

### 测试 5.2: 检查 Redis 连接
```bash
docker exec fire-eye-redis redis-cli ping
```

**预期结果**: 返回 `PONG`

---

## 测试结果记录表

| 测试项 | 状态 | 备注 |
|--------|------|------|
| 1.1 健康检查 | ⬜ 待测试 | |
| 1.2 统计接口 | ⬜ 待测试 | |
| 1.3 查询接口 | ⬜ 待测试 | |
| 1.4 认证测试 | ⬜ 待测试 | |
| 2.1 插件加载 | ✅ 已通过 | 插件已成功加载 |
| 2.2 插件日志 | ⬜ 待测试 | |
| 2.3 文件完整性 | ✅ 已通过 | 文件已复制 |
| 3.1 Telegram 状态 | ⬜ 待测试 | |
| 3.2 Telegram 命令 | ❌ 未实现 | 需要实现命令处理器 |
| 4.1 网络连通性 | ⬜ 待测试 | |
| 4.2 Redis 连接 | ⬜ 待测试 | |
| 4.3 Neo4j 连接 | ⬜ 待测试 | |
| 5.1 Neo4j 数据 | ⬜ 待测试 | |
| 5.2 Redis 状态 | ⬜ 待测试 | |

---

## 快速测试脚本

我为你创建了一个自动化测试脚本，可以一次性运行所有测试：

```bash
# 保存为 run_manual_tests.sh
#!/bin/bash

echo "=========================================="
echo "火瞳系统手动测试"
echo "=========================================="
echo ""

echo "测试 1.1: 健康检查"
docker exec astrbot curl -s http://fire-eye-backend:8000/health
echo -e "\n"

echo "测试 1.2: 统计接口"
docker exec astrbot curl -s http://fire-eye-backend:8000/api/v1/chat/stats \
  -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
echo -e "\n"

echo "测试 1.3: 查询接口"
docker exec astrbot curl -s -X POST http://fire-eye-backend:8000/api/v1/chat/query \
  -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" \
  -H "Content-Type: application/json" \
  -d '{"query": "火灾"}'
echo -e "\n"

echo "测试 2.1: 插件加载状态"
docker logs astrbot 2>&1 | grep -i "fire-eye"
echo -e "\n"

echo "测试 3.1: Telegram 状态"
docker logs astrbot 2>&1 | grep -i "telegram" | tail -5
echo -e "\n"

echo "测试 4.1: 网络连通性 (AstrBot -> Backend)"
docker exec astrbot ping -c 3 fire-eye-backend
echo -e "\n"

echo "测试 5.2: Redis 状态"
docker exec fire-eye-redis redis-cli ping
echo -e "\n"

echo "=========================================="
echo "测试完成"
echo "=========================================="
```

---

## Windows PowerShell 测试脚本

如果你在 Windows 上，使用这个 PowerShell 脚本：

```powershell
# 保存为 run_manual_tests.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "火瞳系统手动测试" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "测试 1.1: 健康检查" -ForegroundColor Yellow
docker exec astrbot curl -s http://fire-eye-backend:8000/health
Write-Host ""

Write-Host "测试 1.2: 统计接口" -ForegroundColor Yellow
docker exec astrbot curl -s http://fire-eye-backend:8000/api/v1/chat/stats -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
Write-Host ""

Write-Host "测试 1.3: 查询接口" -ForegroundColor Yellow
docker exec astrbot curl -s -X POST http://fire-eye-backend:8000/api/v1/chat/query -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" -H "Content-Type: application/json" -d '{\"query\": \"火灾\"}'
Write-Host ""

Write-Host "测试 2.1: 插件加载状态" -ForegroundColor Yellow
docker logs astrbot 2>&1 | Select-String -Pattern "fire-eye"
Write-Host ""

Write-Host "测试 3.1: Telegram 状态" -ForegroundColor Yellow
docker logs astrbot 2>&1 | Select-String -Pattern "telegram" | Select-Object -Last 5
Write-Host ""

Write-Host "测试 5.2: Redis 状态" -ForegroundColor Yellow
docker exec fire-eye-redis redis-cli ping
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "测试完成" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
```

---

## 下一步行动

根据测试结果，你可以：

### 如果所有后端测试通过 ✅
说明后端 API 工作正常，可以继续实现插件的命令处理器功能。

**下一步**: 实现完整的插件功能
- 实现查询命令处理器
- 实现统计命令处理器
- 实现帮助命令处理器
- 实现上传命令处理器

### 如果后端测试失败 ❌
需要先修复后端问题：
1. 检查后端日志: `docker logs fire-eye-backend`
2. 检查环境变量配置
3. 检查数据库连接
4. 重启后端服务

### 如果网络测试失败 ❌
需要检查 Docker 网络配置：
1. 确认容器在同一网络
2. 检查防火墙设置
3. 重新连接网络

---

## 故障排除

### 问题 1: curl 命令不存在
**解决方案**: 在容器中安装 curl
```bash
docker exec astrbot apk add curl
# 或
docker exec astrbot apt-get update && apt-get install -y curl
```

### 问题 2: 后端返回 500 错误
**解决方案**: 查看后端日志
```bash
docker logs fire-eye-backend --tail 100
```

### 问题 3: 插件未加载
**解决方案**: 
1. 检查插件文件是否存在
2. 检查 main.py 语法错误
3. 重启 AstrBot 容器

---

## 联系支持

如果遇到问题，请提供：
1. 测试结果截图
2. 错误日志
3. Docker 容器状态 (`docker ps`)
4. 网络配置 (`docker network ls`)

---

**创建时间**: 2026-02-18
**版本**: 1.0
**状态**: 准备就绪
