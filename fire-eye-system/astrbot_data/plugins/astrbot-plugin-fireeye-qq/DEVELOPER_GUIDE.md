# 火瞳 QQ 插件开发指南

本指南为开发者提供详细的架构说明和扩展指南。

## 项目架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        QQ 用户                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      AstrBot 框架                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Fire-Eye QQ Plugin (main.py)                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │  Commands   │  │  Components │  │  Handlers   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Core Components                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  APIClient   │  │SessionManager│  │RequestQueue  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐                                          │
│  │MessageFormatter                                         │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Fire-Eye Backend API                           │
│  /api/v1/chat/query                                        │
│  /api/v1/chat/stats                                        │
└─────────────────────────────────────────────────────────────┘
```

### 模块说明

#### main.py - 主入口

- 插件初始化
- 配置加载
- 命令注册
- 事件处理

#### api/client.py - API 客户端

- HTTP 请求管理
- 自动重试机制
- 错误处理
- 日志记录

#### session/manager.py - 会话管理

- 会话创建和管理
- 对话历史记录
- 会话过期处理
- 上下文保存

#### queue/request_queue.py - 请求队列

- 并发控制
- 队列管理
- 负载均衡
- 队列监控

#### utils/formatter.py - 消息格式化

- 查询结果格式化
- 统计信息格式化
- 错误消息处理
- 消息分割

## 代码结构

### 命令处理流程

```python
@filter.command("火瞳查询", alias={"ht查询"})
async def query_command(self, event: AstrMessageEvent):
    # 1. 提取查询文本
    query_text = extract_query_text(event)
    
    # 2. 获取用户 ID
    user_id = get_user_id(event)
    
    # 3. 获取或创建会话
    session_id = session_manager.get_session(user_id)
    if not session_id:
        session_id = session_manager.create_session(user_id, "qq")
    
    # 4. 调用 API
    result = await api_client.query(query_text, session_id)
    
    # 5. 格式化响应
    formatted_message = formatter.format_query_results(result)
    
    # 6. 发送给用户
    event.set_result(MessageEventResult().message(formatted_message))
```

## 扩展指南

### 添加新命令

#### 步骤 1: 在 main.py 中添加命令处理器

```python
@filter.command("新命令", alias={"别名"})
async def new_command(self, event: AstrMessageEvent):
    """新命令处理器"""
    try:
        # 处理逻辑
        result = await self.api_client.new_endpoint()
        
        # 格式化响应
        formatted = self.formatter.format_new_result(result)
        
        # 发送给用户
        event.set_result(MessageEventResult().message(formatted))
        
    except Exception as e:
        logger.error(f"Error: {e}")
        event.set_result(MessageEventResult().message(f"❌ 错误: {str(e)}"))
```

#### 步骤 2: 在 api/client.py 中添加 API 方法

```python
async def new_endpoint(self, param: str) -> Dict[str, Any]:
    """新的 API 端点"""
    logger.info(f"Calling new endpoint: {param}")
    
    response = await self._request_with_retry(
        "POST",
        "/chat/new_endpoint",
        json={"param": param}
    )
    
    return response
```

#### 步骤 3: 在 utils/formatter.py 中添加格式化方法

```python
def format_new_result(self, response: Dict[str, Any]) -> str:
    """格式化新结果"""
    try:
        if response.get("status") != "success":
            return self.format_error(response.get("detail", "未知错误"))
        
        data = response.get("data", {})
        
        # 格式化逻辑
        message = "📋 新结果\n\n"
        message += f"• 数据: {data.get('value')}\n"
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting result: {e}")
        return self.format_error(f"格式化失败: {str(e)}")
```

#### 步骤 4: 更新帮助信息

在 `utils/formatter.py` 的 `format_help()` 方法中添加新命令说明。

### 添加新的 API 端点

#### 步骤 1: 在 api/client.py 中添加方法

```python
async def new_feature(
    self,
    param1: str,
    param2: Optional[str] = None
) -> Dict[str, Any]:
    """新功能 API"""
    payload = {"param1": param1}
    if param2:
        payload["param2"] = param2
    
    logger.info(f"Calling new feature: {param1}")
    
    response = await self._request_with_retry(
        "POST",
        "/chat/new_feature",
        json=payload
    )
    
    return response
```

#### 步骤 2: 在命令处理器中使用

```python
result = await self.api_client.new_feature(param1, param2)
```

### 自定义消息格式

#### 修改 utils/formatter.py

```python
def format_custom_message(self, data: Dict[str, Any]) -> str:
    """自定义消息格式"""
    message = "🎯 自定义格式\n\n"
    
    # 添加自定义格式逻辑
    for item in data.get('items', []):
        message += f"• {item['name']}: {item['value']}\n"
    
    return message
```

## 测试指南

### 单元测试

创建 `tests/test_formatter.py`:

```python
import pytest
from utils.formatter import MessageFormatter

def test_format_query_results():
    formatter = MessageFormatter()
    
    response = {
        "status": "success",
        "data": {
            "results": [
                {
                    "type": "FireEvent",
                    "name": "Test Event",
                    "description": "Test Description"
                }
            ]
        }
    }
    
    result = formatter.format_query_results(response)
    assert "Test Event" in result
    assert "🔍" in result
```

### 集成测试

创建 `tests/test_api_client.py`:

```python
import pytest
import asyncio
from api.client import APIClient

@pytest.mark.asyncio
async def test_query():
    client = APIClient(
        api_url="http://localhost:8000/api/v1",
        api_key="test-key"
    )
    
    result = await client.query("test query")
    assert result.get("status") == "success"
```

## 性能优化

### 缓存优化

在 `api/client.py` 中添加缓存:

```python
from functools import lru_cache

class APIClient:
    def __init__(self, ...):
        self._cache = {}
    
    async def query_with_cache(self, query: str) -> Dict:
        cache_key = f"query:{query}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await self.query(query)
        self._cache[cache_key] = result
        
        return result
```

### 连接池优化

```python
async def _get_session(self) -> aiohttp.ClientSession:
    if self._session is None or self._session.closed:
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30
        )
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={"X-API-Key": self.api_key}
        )
    return self._session
```

## 调试技巧

### 启用调试日志

在 `config.yaml` 中:

```yaml
logging:
  level: "DEBUG"
```

### 查看详细日志

```bash
tail -f logs/fireeye-qq.log | grep DEBUG
```

### 添加调试输出

```python
logger.debug(f"[DEBUG] Variable value: {variable}")
```

## 常见问题

### Q: 如何添加新的会话属性？

**A:** 在 `session/manager.py` 中修改 `SessionData` 结构:

```python
self._sessions[user_id] = {
    'session_id': session_id,
    'user_id': user_id,
    'platform': platform,
    'created_at': time.time(),
    'last_activity': time.time(),
    'conversation_history': [],
    'custom_attribute': 'value'  # 新属性
}
```

### Q: 如何处理异步错误？

**A:** 使用 try-except 和日志:

```python
try:
    result = await async_operation()
except asyncio.TimeoutError:
    logger.error("Operation timeout")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
```

### Q: 如何优化内存使用？

**A:** 

1. 限制会话数量
2. 定期清理过期会话
3. 限制对话历史长度
4. 使用生成器而不是列表

## 贡献指南

### 提交代码

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

### 代码规范

- 使用 PEP 8 风格
- 添加类型提示
- 编写文档字符串
- 添加单元测试

### 提交信息

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
test: 添加测试
refactor: 重构代码
```

## 相关资源

- [AstrBot 文档](https://astrbot.readthedocs.io/)
- [Fire-Eye API 文档](https://fire-eye-docs.example.com/)
- [Python 异步编程](https://docs.python.org/3/library/asyncio.html)

## 许可证

MIT License

---

**需要帮助？** 提交 Issue 或联系开发团队。
