# 数据库配置指南

## 概述

火瞳系统使用 Neo4j 作为主要的图数据库存储事理图谱，使用 Redis 作为缓存层提升性能。

## Neo4j 配置

### 数据库模式

#### 节点类型

1. **FireEvent (火灾事件)**
   - `id`: 唯一标识符
   - `event_type`: 事件类型 (原因/过程/结果)
   - `description`: 事件描述
   - `standard_term`: 标准术语
   - `category`: 事件分类
   - `severity_level`: 严重程度 (1-10)
   - `frequency`: 发生频率

2. **Hazard (隐患)**
   - `id`: 唯一标识符
   - `description`: 隐患描述
   - `risk_level`: 风险等级 (低/中/高)
   - `location`: 位置信息

3. **Consequence (后果)**
   - `id`: 唯一标识符
   - `description`: 后果描述
   - `impact_level`: 影响程度
   - `affected_area`: 影响区域

#### 关系类型

1. **CAUSES (导致)**
   - 连接火灾事件之间的因果关系
   - 属性: `confidence`, `time_delay`, `conditions`

2. **LEADS_TO (引发)**
   - 连接隐患到火灾事件
   - 属性: `probability`, `conditions`

3. **RESULTS_IN (导致后果)**
   - 连接火灾事件到后果
   - 属性: `severity`, `likelihood`

### 约束和索引

系统自动创建以下约束和索引：

#### 唯一性约束
- `fire_event_id_unique`: FireEvent.id
- `hazard_id_unique`: Hazard.id  
- `consequence_id_unique`: Consequence.id

#### 性能索引
- `fire_event_type_index`: FireEvent.event_type
- `fire_event_category_index`: FireEvent.category
- `fire_event_severity_index`: FireEvent.severity_level
- `hazard_risk_level_index`: Hazard.risk_level

#### 全文搜索索引
- `fire_event_description_fulltext`: FireEvent 描述和术语
- `hazard_description_fulltext`: Hazard 描述

## Redis 配置

### 缓存结构

Redis 使用以下键命名约定：

```
fire_eye:session:{session_id}        # 用户会话
fire_eye:query_cache:{query_hash}    # 查询结果缓存
fire_eye:extraction_queue            # 文档处理队列
fire_eye:terminology_mapping         # 术语映射表
```

### 缓存策略

1. **查询结果缓存**: 图查询结果缓存 5 分钟
2. **术语映射缓存**: 永久缓存，手动更新
3. **用户会话**: 30 分钟过期
4. **处理队列**: 任务完成后自动清理

## 数据库管理

### 使用 CLI 工具

```bash
# 初始化数据库
make db-init

# 检查数据库状态  
make db-check

# 重置数据库（清空所有数据）
make db-reset

# 备份数据库
make db-backup
```

### 使用 Python 脚本

```bash
cd backend
python scripts/db_manager.py init    # 初始化
python scripts/db_manager.py check   # 检查状态
python scripts/db_manager.py reset   # 重置
python scripts/db_manager.py backup  # 备份
```

## 连接配置

### 环境变量

在 `.env` 文件中配置数据库连接：

```env
# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### Docker 配置

使用 Docker Compose 启动数据库服务：

```bash
# 启动所有服务
docker-compose up -d

# 只启动数据库服务
docker-compose up -d neo4j redis

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs neo4j
docker-compose logs redis
```

## 性能优化

### Neo4j 优化

1. **内存配置**
   - 堆内存: 512MB - 2GB
   - 页面缓存: 根据数据量调整

2. **查询优化**
   - 使用索引加速查询
   - 限制查询深度和结果数量
   - 使用 EXPLAIN 分析查询计划

3. **批量操作**
   - 使用事务批量插入数据
   - 避免大量小事务

### Redis 优化

1. **内存管理**
   - 设置合适的过期时间
   - 使用压缩算法减少内存占用

2. **连接池**
   - 配置连接池大小
   - 启用连接保活

## 监控和维护

### 健康检查

系统提供健康检查端点：

```bash
curl http://localhost:8000/health
```

返回数据库连接状态：

```json
{
  "status": "healthy",
  "service": "fire-eye-backend",
  "database": {
    "neo4j": "connected",
    "redis": "connected"
  }
}
```

### 日志监控

- Neo4j 日志: `docker-compose logs neo4j`
- Redis 日志: `docker-compose logs redis`
- 应用日志: 查看应用输出

### 备份策略

1. **Neo4j 备份**
   - 定期导出数据
   - 使用 Neo4j 官方备份工具

2. **Redis 备份**
   - 启用 AOF 持久化
   - 定期保存 RDB 快照

## 故障排除

### 常见问题

1. **连接失败**
   - 检查服务是否启动
   - 验证网络连接
   - 确认认证信息

2. **性能问题**
   - 检查索引使用情况
   - 分析慢查询
   - 监控内存使用

3. **数据不一致**
   - 检查约束违反
   - 验证事务完整性
   - 重建索引

### 调试命令

```bash
# 检查 Neo4j 连接
docker exec -it fire-eye-neo4j cypher-shell -u neo4j -p password

# 检查 Redis 连接  
docker exec -it fire-eye-redis redis-cli

# 查看容器状态
docker-compose ps

# 重启服务
docker-compose restart neo4j redis
```