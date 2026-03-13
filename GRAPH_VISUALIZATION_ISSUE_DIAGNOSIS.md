# 图表可视化问题诊断与解决方案 / Graph Visualization Issue Diagnosis & Solution

## 问题描述 / Problem Description

**用户报告：** 前端界面能正常打开，但是没有任何节点信息
**Frontend opens but no node data is displayed**

## 根本原因分析 / Root Cause Analysis

### 1. 最可能的原因：数据库为空 / Most Likely: Empty Database

**症状：**
- 图表页面加载成功
- 显示 "Nodes: 0, Links: 0"
- 没有任何节点或关系显示

**原因：**
- Neo4j 数据库中没有任何数据
- 还没有上传和分析任何文档
- 系统是新安装的，需要初始化数据

**验证方法：**
```bash
# 进入 Neo4j 容器
docker exec -it fire-eye-neo4j cypher-shell -u neo4j -p password

# 执行查询
MATCH (n) RETURN count(n) as node_count;
MATCH ()-[r]->() RETURN count(r) as rel_count;

# 如果都返回 0，说明数据库为空
```

### 2. 其他可能的原因 / Other Possible Causes

#### 原因 2: 后端 API 连接问题
- Neo4j 连接失败
- 查询端点返回错误
- 数据格式转换失败

#### 原因 3: 前端请求问题
- API URL 配置错误
- CORS 问题
- 网络连接问题

#### 原因 4: 数据库初始化失败
- Neo4j 容器未正确启动
- 初始化脚本未执行
- 权限问题

## 完整诊断步骤 / Complete Diagnostic Steps

### 步骤 1: 检查 Neo4j 容器状态

```bash
# 检查容器是否运行
docker ps | grep neo4j

# 查看容器日志
docker logs fire-eye-neo4j --tail 50

# 检查容器健康状态
docker inspect fire-eye-neo4j | grep -A 5 "Health"
```

**预期输出：**
```
CONTAINER ID   IMAGE              STATUS
xxx            neo4j:5.15-community   Up X minutes (healthy)
```

### 步骤 2: 检查 Neo4j 连接

```bash
# 进入 Neo4j 容器
docker exec -it fire-eye-neo4j cypher-shell -u neo4j -p password

# 执行测试查询
RETURN "Neo4j is working" as message;

# 检查数据库中的数据
MATCH (n) RETURN labels(n) as node_type, count(n) as count;
MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count;
```

### 步骤 3: 检查后端 API

```bash
# 测试后端健康检查
curl -X GET http://localhost:8000/api/v1/graph/health

# 测试图表查询端点
curl -X GET "http://localhost:8000/api/v1/graph/query?limit=100&include_relationships=true"

# 查看返回的数据结构
# 应该返回类似：
# {
#   "status": "success",
#   "message": "查询成功，返回 0 个节点，0 个关系",
#   "data": {
#     "nodes": [],
#     "links": []
#   }
# }
```

### 步骤 4: 检查前端配置

```bash
# 检查前端环境变量
cat fire-eye-system/frontend/.env.local

# 应该包含：
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 步骤 5: 检查浏览器控制台

1. 打开浏览器开发者工具 (F12)
2. 切换到 "Console" 标签
3. 查看是否有错误信息
4. 切换到 "Network" 标签
5. 刷新页面
6. 查看 `/api/v1/graph/query` 请求
7. 检查响应状态和数据

## 解决方案 / Solutions

### 解决方案 1: 上传文档以填充数据库（推荐）✅

**这是最直接的解决方案**

#### 步骤 1: 打开上传页面
```
http://localhost:3000/upload
```

#### 步骤 2: 选择测试文件
使用提供的测试文件：
```
fire-eye-system/测试文档-火灾调查报告示例.txt
```

#### 步骤 3: 上传文件
1. 点击"选择文件"或拖拽文件
2. 点击"上传"按钮
3. 等待分析完成（30-60秒）

#### 步骤 4: 验证数据
1. 上传完成后，返回图表页面
2. 刷新页面 (F5)
3. 应该看到节点和关系显示

#### 步骤 5: 在 Telegram 中验证
```
/火瞳查询 火灾
```

### 解决方案 2: 直接导入测试数据

如果上传功能有问题，可以直接导入测试数据：

```bash
# 进入 Neo4j 容器
docker exec -it fire-eye-neo4j cypher-shell -u neo4j -p password

# 创建测试节点
CREATE (event:FireEvent {
  id: 'test-event-1',
  description: '电气火灾',
  standard_term: '电气火灾',
  event_type: '电气火灾',
  category: '电气',
  severity_level: 8,
  frequency: 1,
  created_at: datetime(),
  updated_at: datetime()
});

CREATE (hazard:Hazard {
  id: 'test-hazard-1',
  description: '电线老化',
  standard_term: '电线老化',
  risk_level: '高',
  location: '建筑物内',
  created_at: datetime(),
  updated_at: datetime()
});

CREATE (consequence:Consequence {
  id: 'test-consequence-1',
  description: '造成人员伤亡',
  standard_term: '人员伤亡',
  impact_level: '严重',
  affected_area: '整个建筑',
  created_at: datetime(),
  updated_at: datetime()
});

# 创建关系
MATCH (h:Hazard {id: 'test-hazard-1'})
MATCH (e:FireEvent {id: 'test-event-1'})
CREATE (h)-[r:CAUSES {
  id: 'test-rel-1',
  relation_type: '导致',
  confidence: 0.95,
  created_at: datetime()
}]->(e);

MATCH (e:FireEvent {id: 'test-event-1'})
MATCH (c:Consequence {id: 'test-consequence-1'})
CREATE (e)-[r:RESULTS_IN {
  id: 'test-rel-2',
  relation_type: '造成',
  confidence: 0.9,
  created_at: datetime()
}]->(c);

# 验证数据
MATCH (n) RETURN count(n) as node_count;
MATCH ()-[r]->() RETURN count(r) as rel_count;
```

### 解决方案 3: 检查并修复后端连接

如果后端无法连接到 Neo4j：

```bash
# 检查后端日志
docker logs fire-eye-backend --tail 100

# 查看是否有连接错误
# 如果看到 "ServiceUnavailable" 或 "AuthError"，说明连接有问题

# 重启后端服务
docker restart fire-eye-backend

# 等待 30 秒后再测试
sleep 30
curl -X GET http://localhost:8000/api/v1/graph/health
```

### 解决方案 4: 重置整个系统

如果以上方案都不行，可以重置系统：

```bash
# 停止所有容器
docker-compose down

# 删除数据卷（警告：这会删除所有数据）
docker volume rm fire-eye-system_neo4j_data
docker volume rm fire-eye-system_redis_data

# 重新启动
docker-compose up -d

# 等待容器启动（约 30 秒）
sleep 30

# 验证
docker ps
curl -X GET http://localhost:8000/api/v1/graph/health
```

## 完整工作流程 / Complete Workflow

### 第一次使用 / First Time Setup

```
1. 启动系统
   docker-compose up -d

2. 等待容器启动
   sleep 30

3. 验证后端
   curl http://localhost:8000/api/v1/graph/health

4. 打开上传页面
   http://localhost:3000/upload

5. 上传测试文件
   fire-eye-system/测试文档-火灾调查报告示例.txt

6. 等待分析完成
   约 30-60 秒

7. 打开图表页面
   http://localhost:3000/graph

8. 应该看到节点和关系
```

### 日常使用 / Daily Usage

```
1. 打开上传页面
   http://localhost:3000/upload

2. 上传新文件

3. 查看图表
   http://localhost:3000/graph

4. 在 Telegram 中查询
   /火瞳查询 <内容>
```

## 常见问题排查 / Troubleshooting

### 问题 1: 上传后仍然没有数据

**检查步骤：**
1. 查看后端日志
   ```bash
   docker logs fire-eye-backend --tail 50 | grep -i "error\|exception"
   ```

2. 检查任务状态
   ```bash
   # 从上传页面获取任务 ID，然后查询
   curl -X GET http://localhost:8000/api/v1/chat/task/{task_id} \
     -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
   ```

3. 检查 Neo4j 日志
   ```bash
   docker logs fire-eye-neo4j --tail 50
   ```

### 问题 2: 后端返回 500 错误

**可能原因：**
- Neo4j 连接失败
- LLM API 调用失败
- 文件处理错误

**解决方法：**
```bash
# 查看详细错误
docker logs fire-eye-backend --tail 100

# 重启后端
docker restart fire-eye-backend

# 检查环境变量
docker exec fire-eye-backend env | grep -E "NEO4J|REDIS|OPENAI"
```

### 问题 3: 前端无法连接后端

**检查步骤：**
1. 验证后端运行
   ```bash
   docker ps | grep backend
   ```

2. 测试后端连接
   ```bash
   curl -X GET http://localhost:8000/api/v1/graph/health
   ```

3. 检查前端环境变量
   ```bash
   cat fire-eye-system/frontend/.env.local
   ```

4. 检查浏览器控制台错误
   - F12 打开开发者工具
   - 查看 Console 标签中的错误

## 数据流图 / Data Flow Diagram

```
用户上传文件
    ↓
前端 (FileUpload.tsx)
    ↓
后端 API (/api/v1/chat/upload)
    ↓
文件处理 (upload_worker.py)
    ↓
LLM 分析 (analysis_worker.py)
    ↓
提取信息 (extraction_service.py)
    ↓
创建节点和关系 (neo4j_manager.py)
    ↓
Neo4j 数据库
    ↓
前端查询 (/api/v1/graph/query)
    ↓
图表显示 (GraphViewer.tsx)
```

## 验证清单 / Verification Checklist

- [ ] Neo4j 容器运行中
- [ ] Redis 容器运行中
- [ ] 后端容器运行中
- [ ] 前端容器运行中
- [ ] 后端健康检查通过
- [ ] 前端可以访问
- [ ] 上传页面可以访问
- [ ] 图表页面可以访问
- [ ] 文件已上传
- [ ] 任务已完成
- [ ] Neo4j 中有数据
- [ ] 图表显示节点

## 下一步 / Next Steps

1. **立即行动：** 上传测试文件
   ```
   http://localhost:3000/upload
   ```

2. **验证数据：** 检查 Neo4j
   ```bash
   docker exec -it fire-eye-neo4j cypher-shell -u neo4j -p password
   MATCH (n) RETURN count(n);
   ```

3. **查看图表：** 刷新图表页面
   ```
   http://localhost:3000/graph
   ```

4. **在 Telegram 中测试：**
   ```
   /火瞳查询 火灾
   ```

---

**创建时间 / Created**: 2026-03-12
**状态 / Status**: 诊断完成，等待用户上传数据
**推荐行动 / Recommended Action**: 上传测试文件以填充数据库

