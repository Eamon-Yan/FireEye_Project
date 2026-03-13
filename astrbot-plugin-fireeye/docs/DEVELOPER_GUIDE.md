# 火瞳系统 AstrBot 插件 - 开发者指南

## 目录
- [架构概览](#架构概览)
- [组件说明](#组件说明)
- [开发环境设置](#开发环境设置)
- [代码结构](#代码结构)
- [扩展指南](#扩展指南)
- [测试指南](#测试指南)
- [贡献指南](#贡献指南)

---

## 架构概览

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    聊天平台 (QQ/Telegram)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    AstrBot 框架                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Fire-Eye Plugin (本插件)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Command Handlers (命令处理器)                    │  │
│  │  - QueryHandler                                   │  │
│  │  - UploadHandler                                  │  │
│  │  - StatsHandler                                   │  │
│  │  - HelpHandler                                    │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Core Components (核心组件)                       │  │
│  │  - APIClient (API 客户端)                        │  │
│  │  - SessionManager (会话管理)                     │  │
│  │  - RequestQueue (请求队列)                       │  │
│  │  - TaskPoller (任务轮询)                         │  │
│  │  - MessageFormatter (消息格式化)                 │  │
│  │  - FileHandler (文件处理)                        │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/REST API
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Fire-Eye Backend (后端系统)                 │
│  - Chat API                                             │
│  - Knowledge Graph (Neo4j)                              │
│  - Task Management (Redis)                              │
└─────────────────────────────────────────────────────────┘
```

### 数据流

#### 查询流程
```
用户输入 → QueryHandler → RequestQueue → APIClient 
→ Backend API → Neo4j → Response → MessageFormatter → 用户
```

#### 上传流程
```
用户文件 → UploadHandler → FileHandler → APIClient 
→ Backend API → Task Created → TaskPoller (轮询)
→ Task Complete → MessageFormatter → 用户
```

---

## 组件说明

### 1. Command Handlers (命令处理器)

#### QueryHandler
**职责**: 处理查询命令

**关键方法**:
```python
async def handle(self, message, user_id: str, platform: str)
    """处理查询命令"""
    
def _extract_query_text(self, message) -> str
    """提取查询文本"""
```

**依赖**:
- APIClient: 调用后端 API
- SessionManager: 管理用户会话
- RequestQueue: 控制并发
- MessageFormatter: 格式化响应

#### UploadHandler
**职责**: 处理文件上传命令

**关键方法**:
```python
async def handle(self, message, user_id: str, platform: str)
    """处理上传命令"""
    
async def _handle_file_upload(self, file, user_id: str)
    """处理文件上传"""
```

**依赖**:
- APIClient: 上传文件到后端
- FileHandler: 文件验证和处理
- TaskPoller: 轮询任务状态
- MessageFormatter: 格式化响应

#### StatsHandler
**职责**: 处理统计命令

**关键方法**:
```python
async def handle(self, message, user_id: str, platform: str)
    """处理统计命令"""
    
def _extract_stat_type(self, message) -> str
    """提取统计类型"""
```

#### HelpHandler
**职责**: 处理帮助命令

**关键方法**:
```python
async def handle(self, message, user_id: str, platform: str)
    """处理帮助命令"""
```

### 2. Core Components (核心组件)

#### APIClient
**职责**: 与后端 API 通信

**关键方法**:
```python
async def query(self, query: str, session_id: str = None)
    """查询知识图谱"""
    
async def analyze(self, text: str, session_id: str = None)
    """分析文本"""
    
async def upload(self, file_path: str, filename: str)
    """上传文件"""
    
async def get_task_status(self, task_id: str)
    """获取任务状态"""
    
async def get_stats(self, stat_type: str = "all", time_range: str = "all")
    """获取统计信息"""
```

**特性**:
- 自动重试（指数退避）
- 连接池管理
- 超时控制

#### SessionManager
**职责**: 管理用户会话

**关键方法**:
```python
def create_session(self, user_id: str, platform: str) -> str
    """创建会话"""
    
def get_session(self, user_id: str) -> str
    """获取会话ID"""
    
def update_activity(self, user_id: str)
    """更新活动时间"""
    
def cleanup_expired_sessions(self)
    """清理过期会话"""
```

**特性**:
- 内存存储
- 自动过期（30分钟）
- 用户ID到会话ID映射

#### RequestQueue
**职责**: 控制并发请求

**关键方法**:
```python
async def enqueue(self, request_func, *args, **kwargs)
    """将请求加入队列"""
    
def get_status(self) -> dict
    """获取队列状态"""
```

**特性**:
- 并发限制（默认5个）
- 队列缓冲（默认20个）
- 自动处理队列

#### TaskPoller
**职责**: 轮询异步任务状态

**关键方法**:
```python
async def poll_task(
    self,
    task_id: str,
    on_complete: Callable = None,
    on_failed: Callable = None,
    on_progress: Callable = None,
    on_timeout: Callable = None
)
    """轮询任务状态"""
```

**特性**:
- 3秒轮询间隔
- 5分钟超时
- 回调机制

#### MessageFormatter
**职责**: 格式化消息

**关键方法**:
```python
def format_query_results(self, response: Dict) -> str
    """格式化查询结果"""
    
def format_task_progress(self, progress: int) -> str
    """格式化任务进度"""
    
def format_task_completed(self, task_data: Dict) -> str
    """格式化任务完成"""
    
def format_statistics(self, response: Dict) -> str
    """格式化统计信息"""
    
def format_error(self, error_message: str) -> str
    """格式化错误消息"""
    
def format_help(self) -> str
    """格式化帮助信息"""
```

**特性**:
- 自动截断长消息
- Emoji 图标
- 清晰的层次结构

#### FileHandler
**职责**: 处理文件操作

**关键方法**:
```python
def validate_file_type(self, filename: str) -> bool
    """验证文件类型"""
    
def validate_file_size(self, file_path: str) -> bool
    """验证文件大小"""
    
def cleanup_temp_file(self, file_path: str)
    """清理临时文件"""
```

**特性**:
- 文件类型验证（PDF/DOCX/TXT）
- 文件大小限制（10MB）
- 自动清理

---

## 开发环境设置

### 1. 克隆项目
```bash
git clone <repository-url>
cd astrbot-plugin-fireeye
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

### 4. 配置开发环境
```bash
cp config.yaml.example config.yaml
# 编辑 config.yaml 配置开发环境参数
```

### 5. 运行测试
```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_message_formatter.py -v

# 运行手动测试
python manual_test.py
```

---

## 代码结构

```
astrbot-plugin-fireeye/
├── api/                      # API 客户端
│   ├── __init__.py
│   ├── client.py            # API 客户端实现
│   └── polling.py           # 任务轮询器
├── commands/                 # 命令处理器
│   ├── __init__.py
│   ├── query_handler.py     # 查询命令
│   ├── upload_handler.py    # 上传命令
│   ├── stats_handler.py     # 统计命令
│   └── help_handler.py      # 帮助命令
├── request_queue_module/     # 请求队列
│   ├── __init__.py
│   └── request_queue.py
├── session/                  # 会话管理
│   ├── __init__.py
│   └── manager.py
├── utils/                    # 工具类
│   ├── __init__.py
│   ├── formatter.py         # 消息格式化
│   └── file_handler.py      # 文件处理
├── tests/                    # 测试文件
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_command_handlers.py
│   ├── test_file_handler.py
│   ├── test_message_formatter.py
│   ├── test_polling.py
│   ├── test_request_queue.py
│   └── test_session_manager.py
├── docs/                     # 文档
│   ├── USER_GUIDE.md
│   └── DEVELOPER_GUIDE.md
├── config.yaml              # 配置文件
├── main.py                  # 插件入口
├── requirements.txt         # 依赖列表
├── README.md               # 项目说明
└── manual_test.py          # 手动测试脚本
```

---

## 扩展指南

### 添加新命令

#### 1. 创建命令处理器
```python
# commands/my_command_handler.py

from loguru import logger
from api.client import APIClient
from utils.formatter import MessageFormatter


class MyCommandHandler:
    """我的命令处理器"""
    
    def __init__(
        self,
        api_client: APIClient,
        formatter: MessageFormatter
    ):
        self.api_client = api_client
        self.formatter = formatter
        logger.info("MyCommandHandler initialized")
    
    async def handle(self, message, user_id: str, platform: str = "unknown"):
        """处理命令"""
        try:
            # 1. 提取参数
            params = self._extract_params(message)
            
            # 2. 调用 API
            response = await self.api_client.my_api_method(params)
            
            # 3. 格式化响应
            formatted = self.formatter.format_my_response(response)
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return self.formatter.format_error(str(e))
    
    def _extract_params(self, message):
        """提取参数"""
        # 实现参数提取逻辑
        pass
```

#### 2. 注册命令
```python
# main.py

def _register_commands(self):
    from commands.my_command_handler import MyCommandHandler
    
    my_handler = MyCommandHandler(
        api_client=self.api_client,
        formatter=self.message_formatter
    )
    
    commands = [
        # ... 现有命令
        ("/我的命令", my_handler.handle, "命令描述"),
    ]
```

#### 3. 添加测试
```python
# tests/test_my_command_handler.py

import pytest
from commands.my_command_handler import MyCommandHandler


class TestMyCommandHandler:
    @pytest.fixture
    def handler(self):
        # 创建处理器实例
        pass
    
    @pytest.mark.asyncio
    async def test_handle(self, handler):
        # 测试命令处理
        pass
```

### 添加新的消息格式

```python
# utils/formatter.py

def format_my_response(self, response: Dict[str, Any]) -> str:
    """格式化我的响应"""
    try:
        data = response.get('data', {})
        
        message = "📋 我的响应\n\n"
        # 添加格式化逻辑
        
        return self._truncate_message(message)
        
    except Exception as e:
        logger.error(f"Error formatting response: {e}")
        return "❌ 格式化响应时出错"
```

### 扩展 API 客户端

```python
# api/client.py

async def my_api_method(self, param1: str, param2: int):
    """我的 API 方法"""
    endpoint = f"{self.api_url}/api/v1/my-endpoint"
    
    payload = {
        "param1": param1,
        "param2": param2
    }
    
    response = await self._make_request(
        method="POST",
        url=endpoint,
        json=payload
    )
    
    return response
```

---

## 测试指南

### 单元测试

#### 编写测试
```python
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestMyComponent:
    @pytest.fixture
    def component(self):
        """创建组件实例"""
        return MyComponent()
    
    def test_sync_method(self, component):
        """测试同步方法"""
        result = component.sync_method()
        assert result == expected_value
    
    @pytest.mark.asyncio
    async def test_async_method(self, component):
        """测试异步方法"""
        result = await component.async_method()
        assert result == expected_value
```

#### 运行测试
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定文件
pytest tests/test_my_component.py -v

# 运行特定测试
pytest tests/test_my_component.py::TestMyComponent::test_method -v

# 查看覆盖率
pytest tests/ --cov=. --cov-report=html
```

### 集成测试

```python
# tests/integration/test_end_to_end.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_flow():
    """测试完整查询流程"""
    # 1. 创建插件实例
    plugin = FireEyePlugin()
    plugin.on_load()
    
    # 2. 模拟用户查询
    response = await plugin.handle_message(
        "/火瞳查询 测试查询",
        user_id="test-user"
    )
    
    # 3. 验证响应
    assert "查询结果" in response
```

### 手动测试

```bash
# 运行手动测试脚本
python manual_test.py
```

---

## 贡献指南

### 代码规范

#### Python 风格
- 遵循 PEP 8
- 使用类型提示
- 添加文档字符串

```python
def my_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    函数说明
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        
    Returns:
        返回值说明
        
    Raises:
        ValueError: 错误说明
    """
    pass
```

#### 命名规范
- 类名: `PascalCase`
- 函数/方法: `snake_case`
- 常量: `UPPER_CASE`
- 私有方法: `_leading_underscore`

#### 日志规范
```python
from loguru import logger

# 使用适当的日志级别
logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 提交流程

#### 1. Fork 项目
```bash
# 在 GitHub 上 Fork 项目
# 克隆你的 Fork
git clone <your-fork-url>
```

#### 2. 创建分支
```bash
git checkout -b feature/my-feature
# 或
git checkout -b fix/my-bugfix
```

#### 3. 开发和测试
```bash
# 编写代码
# 运行测试
pytest tests/ -v

# 检查代码风格
flake8 .
black .
```

#### 4. 提交更改
```bash
git add .
git commit -m "feat: 添加新功能"
# 或
git commit -m "fix: 修复bug"
```

**提交消息格式**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

#### 5. 推送和创建 PR
```bash
git push origin feature/my-feature
# 在 GitHub 上创建 Pull Request
```

### Pull Request 检查清单

- [ ] 代码遵循项目规范
- [ ] 添加了必要的测试
- [ ] 所有测试通过
- [ ] 更新了相关文档
- [ ] 提交消息清晰明确
- [ ] 没有合并冲突

---

## API 参考

### Backend API Endpoints

#### POST /api/v1/chat/query
查询知识图谱

**请求**:
```json
{
  "query": "查询文本",
  "session_id": "可选的会话ID"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "results": [...],
    "total_count": 10,
    "session_id": "session-id"
  }
}
```

#### POST /api/v1/chat/analyze
分析文本

**请求**:
```json
{
  "text": "要分析的文本",
  "session_id": "可选的会话ID"
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task-id",
    "estimated_time": 60
  }
}
```

#### POST /api/v1/chat/upload
上传文件

**请求**: multipart/form-data
- `file`: 文件内容

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task-id",
    "document_id": "doc-id",
    "estimated_time": 60
  }
}
```

#### GET /api/v1/chat/status/{task_id}
查询任务状态

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "task-id",
    "status": "completed",
    "progress": 100,
    "result": {...}
  }
}
```

#### GET /api/v1/chat/stats
获取统计信息

**参数**:
- `stat_type`: 统计类型（可选）
- `time_range`: 时间范围（可选）

**响应**:
```json
{
  "success": true,
  "data": {
    "total_fire_events": 100,
    "total_hazards": 50,
    ...
  }
}
```

---

## 常见开发问题

### Q: 如何调试插件？
**A**: 
```python
# 1. 启用调试日志
logging:
  level: "DEBUG"

# 2. 使用 Python 调试器
import pdb; pdb.set_trace()

# 3. 查看日志文件
tail -f logs/fireeye.log
```

### Q: 如何模拟 AstrBot 环境？
**A**: 使用手动测试脚本或创建模拟对象

### Q: 如何处理异步代码？
**A**: 使用 `async/await` 和 `asyncio`

---

**最后更新**: 2026-02-17
