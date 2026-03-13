# 图表可视化问题解决指南 / Graph Visualization Solution Guide

## 快速诊断 / Quick Diagnosis

### 第一步：运行诊断脚本

```bash
python diagnose_graph_issue.py
```

这个脚本会检查：
- ✓ Docker 容器状态
- ✓ Neo4j 连接
- ✓ 数据库中的数据
- ✓ 后端健康状态
- ✓ 图表查询端点
- ✓ 前端配置

### 第二步：根据诊断结果采取行动

---

## 场景 1: 数据库为空（最常见）

**症状：**
- 诊断脚本显示 "节点数: 0"
- 图表页面显示 "Nodes: 0, Links: 0"

**解决方案：上传测试文件**

### 步骤 1: 打开上传页面

```
http://localhost:3000/upload
```

### 步骤 2: 选择测试文件

使用提供的测试文件：
```
fire-eye-system/测试文档-火灾调查报告示例.txt
```

### 步骤 3: 上传文件

1. 点击"选择文件"或拖拽文件到上传区域
2. 点击"上传"按钮
3. 等待上传完成

### 步骤 4: 等待分析

- 上传后，系统会自动开始分析
- 进度条会显示处理进度
- 通常需要 30-60 秒

### 步骤 5: 查看结果

- 分析完成后，会显示提取的信息
- 点击"查看图表"按钮或直接访问 http://localhost:3000/graph
- 应该看到节点和关系

### 步骤 6: 验证

在 Telegram 中测试：
```
/火瞳查询 火灾
```

应该返回查询结果。

---

## 场景 2: 后端连接失败

**症状：**
- 诊断脚本显示 "后端健康检查失败"
- 上传页面无法加载
- 图表页面显示加载错误

**解决方案：重启后端**

### 步骤 1: 重启后端容器

```bash
docker restart fire-eye-backend
```

### 步骤 2: 等待启动

```bash
sleep 30
```

### 步骤 3: 验证

```bash
curl -X GET http://localhost:8000/api/v1/graph/health
```

应该返回：
```json
{
  "status": "success",
  "message": "图数据库连接正常",
  "data": {"healthy": true}
}
```

### 步骤 4: 重新尝试

- 刷新浏览器页面
- 重新上传文件或查看图表

---

## 场景 3: Neo4j 连接失败

**症状：**
- 诊断脚本显示 "Neo4j 连接失败"
- 后端日志显示 "ServiceUnavailable" 或 "AuthError"

**解决方案：重启 Neo4j**

### 步骤 1: 重启 Neo4j 容器

```bash
docker restart fire-eye-neo4j
```

### 步骤 2: 等待启动

```bash
sleep 30
```

### 步骤 3: 验证连接

```bash
docker exec -it fire-eye-neo4j cypher-shell -u neo4j -p password "RETURN 'Connected' as status;"
```

### 步骤 4: 重启后端

```bash
docker restart fire-eye-backend
```

### 步骤 5: 重新尝试

- 刷新浏览器页面
- 重新上传文件

---

## 场景 4: 前端无法连接后端

**症状：**
- 浏览器控制台显示 CORS 错误
- 网络请求显示 "Failed to fetch"
- 图表页面显示加载错误

**解决方案：检查前端配置**

### 步骤 1: 检查前端环境变量

```bash
cat fire-eye-system/frontend/.env.local
```

应该包含：
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 步骤 2: 如果配置不正确，更新它

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > fire-eye-system/frontend/.env.local
```

### 步骤 3: 重启前端

```bash
docker restart fire-eye-frontend
```

### 步骤 4: 等待启动

```bash
sleep 15
```

### 步骤 5: 清除浏览器缓存

- 打开浏览器开发者工具 (F12)
- 右键点击刷新按钮
- 选择"清空缓存并硬性重新加载"

### 步骤 6: 重新访问

```
http://localhost:3000/graph
```

---

## 场景 5: 上传失败

**症状：**
- 上传页面显示错误
- 任务状态显示"失败"
- 后端日志显示错误

**解决方案：检查文件和后端**

### 步骤 1: 检查文件

- 文件大小不超过 50MB
- 文件格式为 PDF、TXT 或 DOCX
- 文件不为空

### 步骤 2: 查看后端日志

```bash
docker logs fire-eye-backend --tail 50 | grep -i "error\|exception"
```

### 步骤 3: 检查 LLM API

```bash
# 验证 API 密钥
docker exec fire-eye-backend env | grep OPENAI_API_KEY

# 测试 LLM 连接
curl -X POST https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-chat", "messages": [{"role": "user", "content": "test"}]}'
```

### 步骤 4: 重试上传

- 使用较小的文件
- 使用 TXT 格式
- 检查文件内容是否有效

---

## 场景 6: 完全重置系统

**警告：这会删除所有数据**

如果以上方案都不行，可以完全重置系统：

### 步骤 1: 停止所有容器

```bash
docker-compose down
```

### 步骤 2: 删除数据卷

```bash
docker volume rm fire-eye-system_neo4j_data
docker volume rm fire-eye-system_redis_data
docker volume rm fire-eye-system_backend_uploads
```

### 步骤 3: 重新启动

```bash
cd fire-eye-system
docker-compose up -d
```

### 步骤 4: 等待启动

```bash
sleep 60
```

### 步骤 5: 验证

```bash
python diagnose_graph_issue.py
```

### 步骤 6: 上传测试文件

```
http://localhost:3000/upload
```

---

## 手动测试步骤 / Manual Testing Steps

### 测试 1: 检查 Neo4j 数据

```bash
# 进入 Neo4j 容器
docker exec -it fire-eye-neo4j cypher-shell -u neo4j -p password

# 执行查询
MATCH (n) RETURN count(n) as node_count;
MATCH ()-[r]->() RETURN count(r) as rel_count;
MATCH (n) RETURN labels(n) as node_type, count(n) as count;
```

### 测试 2: 测试后端 API

```bash
# 健康检查
curl -X GET http://localhost:8000/api/v1/graph/health

# 查询图表数据
curl -X GET "http://localhost:8000/api/v1/graph/query?limit=100&include_relationships=true"

# 查询统计信息
curl -X GET http://localhost:8000/api/v1/graph/statistics
```

### 测试 3: 测试前端连接

```bash
# 检查前端是否运行
curl -X GET http://localhost:3000

# 检查 API 连接
curl -X GET http://localhost:3000/api/v1/graph/query
```

### 测试 4: 在浏览器中测试

1. 打开浏览器开发者工具 (F12)
2. 切换到 "Network" 标签
3. 访问 http://localhost:3000/graph
4. 查看网络请求
5. 找到 `/api/v1/graph/query` 请求
6. 检查响应状态和数据

---

## 常见错误信息及解决方案

### 错误 1: "CORS error"

**原因：** 前端无法连接后端

**解决：**
```bash
# 检查后端是否运行
docker ps | grep backend

# 检查后端日志
docker logs fire-eye-backend --tail 20

# 重启后端
docker restart fire-eye-backend
```

### 错误 2: "Failed to fetch"

**原因：** 网络连接问题或后端未响应

**解决：**
```bash
# 测试后端连接
curl -X GET http://localhost:8000/api/v1/graph/health

# 检查防火墙
# 确保端口 8000 未被阻止
```

### 错误 3: "Neo4j connection failed"

**原因：** Neo4j 容器未运行或连接失败

**解决：**
```bash
# 检查 Neo4j 容器
docker ps | grep neo4j

# 查看 Neo4j 日志
docker logs fire-eye-neo4j --tail 50

# 重启 Neo4j
docker restart fire-eye-neo4j
```

### 错误 4: "Task failed"

**原因：** 文件处理或 LLM 分析失败

**解决：**
```bash
# 查看后端日志
docker logs fire-eye-backend --tail 100 | grep -i "error"

# 检查文件大小和格式
# 尝试使用不同的文件

# 检查 LLM API 密钥
docker exec fire-eye-backend env | grep OPENAI_API_KEY
```

---

## 性能优化建议

### 如果图表加载缓慢

1. **减少查询数据量**
   ```
   http://localhost:3000/graph?limit=50
   ```

2. **检查 Neo4j 性能**
   ```bash
   docker exec -it fire-eye-neo4j cypher-shell -u neo4j -p password
   PROFILE MATCH (n) RETURN n LIMIT 100;
   ```

3. **增加 Neo4j 内存**
   编辑 `docker-compose.yml`：
   ```yaml
   environment:
     - NEO4J_dbms_memory_heap_max__size=4G
   ```

### 如果上传缓慢

1. **检查文件大小**
   - 最大 50MB
   - 建议 < 10MB

2. **检查 LLM API 响应**
   ```bash
   docker logs fire-eye-backend --tail 50 | grep -i "deepseek\|openai"
   ```

3. **增加后端资源**
   编辑 `docker-compose.yml`：
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

---

## 获取帮助 / Getting Help

### 收集诊断信息

```bash
# 运行诊断脚本
python diagnose_graph_issue.py > diagnostic_report.txt

# 收集容器日志
docker logs fire-eye-backend > backend.log
docker logs fire-eye-neo4j > neo4j.log
docker logs fire-eye-frontend > frontend.log

# 收集系统信息
docker ps > containers.txt
docker volume ls > volumes.txt
```

### 检查清单

- [ ] 所有容器都在运行
- [ ] Neo4j 连接正常
- [ ] 后端健康检查通过
- [ ] 前端可以访问
- [ ] 已上传测试文件
- [ ] 任务已完成
- [ ] Neo4j 中有数据
- [ ] 图表显示节点

---

## 总结 / Summary

| 问题 | 症状 | 解决方案 |
|------|------|--------|
| 数据库为空 | 节点数: 0 | 上传测试文件 |
| 后端连接失败 | 健康检查失败 | 重启后端 |
| Neo4j 连接失败 | 连接错误 | 重启 Neo4j |
| 前端无法连接 | CORS 错误 | 检查配置，重启前端 |
| 上传失败 | 任务失败 | 检查文件，查看日志 |
| 其他问题 | 不确定 | 运行诊断脚本 |

---

**最后更新 / Last Updated**: 2026-03-12
**版本 / Version**: 1.0
**状态 / Status**: 完成 / Complete

