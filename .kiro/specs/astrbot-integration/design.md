# Design Document: AstrBot Integration for Fire-Eye System

## Document Information

- **Version:** 1.0
- **Date:** 2026-02-17
- **Status:** Design Phase
- **Related Requirements:** [requirements.md](./requirements.md)

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Component Design](#component-design)
3. [API Specifications](#api-specifications)
4. [Data Models](#data-models)
5. [Sequence Diagrams](#sequence-diagrams)
6. [Security Design](#security-design)
7. [Performance Considerations](#performance-considerations)
8. [Deployment Architecture](#deployment-architecture)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Layer                                │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐             │
│  │  QQ  │  │Telegram│ │WeChat│ │DingTalk│ │Feishu│             │
│  └──┬───┘  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘             │
└─────┼──────────┼─────────┼─────────┼─────────┼────────────────┘
      │          │         │         │         │
      └──────────┴─────────┴─────────┴─────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AstrBot Core Platform                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Fire-Eye Plugin (火瞳插件)                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │   Command    │  │  API Client  │  │   Message    │    │ │
│  │  │   Handler    │  │  + Polling   │  │  Formatter   │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │   Session    │  │    Config    │  │   Request    │    │ │
│  │  │   Manager    │  │   Manager    │  │    Queue     │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                         │
                         │ HTTPS + API Key
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Fire-Eye Backend (Chat API Layer)                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Chat API Endpoints                        │ │
│  │  /api/v1/chat/query    /api/v1/chat/analyze               │ │
│  │  /api/v1/chat/upload   /api/v1/chat/status/{task_id}      │ │
│  │  /api/v1/chat/stats                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Business Logic Layer                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │   Session    │  │     Task     │  │   Context    │    │ │
│  │  │   Service    │  │   Manager    │  │   Manager    │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Existing Services (Reused)                     │ │
│  │  ExtractionService  GraphService  ValidationService        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    Neo4j     │  │    Redis     │  │  File System │         │
│  │  (Graph DB)  │  │   (Cache)    │  │   (Temp)     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Architecture Principles

1. **Minimal Intrusion**: Fire-Eye backend remains independent, accessed only via REST API
2. **Async-First**: All long-running operations use task-based async processing
3. **Stateful Conversations**: Session management enables context-aware multi-turn dialogue
4. **Security by Default**: API key authentication, audit logging, privacy protection
5. **Graceful Degradation**: Request queuing and rate limiting prevent system overload

### 1.3 Technology Stack

#### Fire-Eye Backend (Chat API Layer)
- **Framework**: FastAPI (Python 3.10+)
- **Async Runtime**: asyncio
- **Task Queue**: In-memory task manager (Redis-backed for production)
- **Session Store**: Redis (30-minute TTL)
- **Authentication**: API Key in HTTP headers

#### AstrBot Plugin
- **Language**: Python 3.10+
- **Framework**: AstrBot Plugin SDK
- **HTTP Client**: aiohttp (async)
- **Configuration**: YAML + environment variables
- **Logging**: Python logging module

---

## 2. Component Design

### 2.1 Fire-Eye Backend Components

#### 2.1.1 Chat API Layer (`app/api/v1/endpoints/chat.py`)

**Purpose**: Provide chat-optimized REST API endpoints

**Responsibilities**:
- Handle incoming chat requests with authentication
- Validate request parameters
- Delegate to business logic services
- Format responses for chat platforms
- Manage async task lifecycle

**Key Methods**:

```python
@router.post("/query")
async def query_graph(
    query: str,
    session_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> ChatResponse

@router.post("/analyze")
async def analyze_document(
    text: str,
    session_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> TaskResponse

@router.post("/upload")
async def upload_document(
    file: UploadFile,
    session_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> TaskResponse

@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
) -> TaskStatusResponse

@router.get("/stats")
async def get_statistics(
    stat_type: Optional[str] = None,
    time_range: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> StatsResponse
```

#### 2.1.2 Session Service (`app/services/session_service.py`)

**Purpose**: Manage conversation context and history

**Data Structure**:
```python
class SessionData:
    session_id: str
    user_id: str
    platform: str
    created_at: datetime
    last_activity: datetime
    conversation_history: List[ConversationTurn]
    context: Dict[str, Any]

class ConversationTurn:
    timestamp: datetime
    user_message: str
    bot_response: str
    query_results: Optional[List[Dict]]
```

**Key Methods**:
```python
async def create_session(user_id: str, platform: str) -> str
async def get_session(session_id: str) -> Optional[SessionData]
async def update_session(session_id: str, turn: ConversationTurn)
async def resolve_context_reference(session_id: str, query: str) -> str
async def cleanup_expired_sessions()
```

**Redis Storage Schema**:
```
Key: session:{session_id}
Value: JSON-serialized SessionData
TTL: 1800 seconds (30 minutes)
```

#### 2.1.3 Task Manager (`app/services/task_manager.py`)

**Purpose**: Manage async task lifecycle and status tracking

**Data Structure**:
```python
class Task:
    task_id: str
    task_type: str  # "analyze" | "upload"
    status: str  # "pending" | "processing" | "completed" | "failed" | "timeout"
    progress: int  # 0-100
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_time_remaining: Optional[int]  # seconds
    result: Optional[Dict]
    error: Optional[str]
    session_id: Optional[str]

class TaskResult:
    event_chains: List[EventChain]
    node_count: int
    relationship_count: int
    document_metadata: Optional[Dict]
```

**Key Methods**:
```python
async def create_task(task_type: str, session_id: Optional[str]) -> str
async def get_task_status(task_id: str) -> Task
async def update_task_progress(task_id: str, progress: int, estimated_time: int)
async def complete_task(task_id: str, result: TaskResult)
async def fail_task(task_id: str, error: str)
async def cleanup_old_tasks()
```

**Background Worker**:
```python
async def process_analyze_task(task_id: str, text: str):
    # Update status to "processing"
    await task_manager.update_task_progress(task_id, 10, 50)
    
    # Extract event chains using existing ExtractionService
    event_chains = await extraction_service.extract_event_chains(text)
    await task_manager.update_task_progress(task_id, 50, 25)
    
    # Create graph nodes and relationships
    result = await graph_service.batch_create_event_chains(event_chains)
    await task_manager.update_task_progress(task_id, 90, 5)
    
    # Complete task
    await task_manager.complete_task(task_id, TaskResult(...))
```

#### 2.1.4 Context Manager (`app/services/context_manager.py`)

**Purpose**: Resolve context references in multi-turn conversations

**Key Methods**:
```python
async def resolve_reference(session_id: str, query: str) -> str:
    """
    Resolve references like "主要原因" to actual entities from conversation history
    
    Example:
    - Previous: "查询3.21火灾事故" → Results: [Event A, Event B, ...]
    - Current: "主要原因是什么？"
    - Resolved: "3.21火灾事故的主要原因是什么？"
    """
    session = await session_service.get_session(session_id)
    if not session:
        return query
    
    # Extract entities from last query results
    last_results = session.conversation_history[-1].query_results
    
    # Use LLM to resolve reference
    resolved_query = await llm_service.resolve_context_reference(
        query=query,
        context=last_results
    )
    
    return resolved_query
```

#### 2.1.5 Authentication Middleware (`app/api/auth.py`)

**Purpose**: Validate API keys and log authentication attempts

**Implementation**:
```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required"
        )
    
    # Load valid API keys from config
    valid_keys = settings.ASTRBOT_API_KEYS  # List of valid keys
    
    if api_key not in valid_keys:
        # Log failed attempt
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    # Log successful authentication
    logger.info(f"API key authenticated: {api_key[:8]}...")
    return api_key
```

### 2.2 AstrBot Plugin Components

#### 2.2.1 Plugin Structure

```
astrbot-plugin-fireeye/
├── __init__.py
├── main.py                 # Plugin entry point
├── config.yaml             # Configuration file
├── commands/
│   ├── __init__.py
│   ├── query_handler.py    # /火瞳查询 command
│   ├── upload_handler.py   # /火瞳上传 command
│   ├── stats_handler.py    # /火瞳统计 command
│   └── help_handler.py     # /火瞳帮助 command
├── api/
│   ├── __init__.py
│   ├── client.py           # HTTP client with retry logic
│   └── polling.py          # Background polling coroutine
├── session/
│   ├── __init__.py
│   └── manager.py          # Session ID management
├── queue/
│   ├── __init__.py
│   └── request_queue.py    # Request queue and rate limiting
├── utils/
│   ├── __init__.py
│   ├── formatter.py        # Message formatting
│   └── file_handler.py     # File download and upload
└── README.md
```

#### 2.2.2 Plugin Main Entry (`main.py`)

```python
from astrbot.api import AstrBotPlugin, CommandHandler, register_command

class FireEyePlugin(AstrBotPlugin):
    def __init__(self):
        super().__init__()
        self.name = "fire-eye"
        self.version = "1.0.0"
        self.author = "Fire-Eye Team"
        self.description = "火瞳火灾调查知识图谱系统集成插件"
        
        # Initialize components
        self.api_client = APIClient(config)
        self.session_manager = SessionManager()
        self.request_queue = RequestQueue(max_concurrent=10, max_queue=50)
        self.message_formatter = MessageFormatter()
        
    async def on_load(self):
        """Plugin initialization"""
        logger.info("Fire-Eye plugin loaded")
        
        # Register commands
        self.register_command("/火瞳查询", self.handle_query)
        self.register_command("/火瞳上传", self.handle_upload)
        self.register_command("/火瞳统计", self.handle_stats)
        self.register_command("/火瞳帮助", self.handle_help)
        
        # Register aliases
        self.register_command("/ht查询", self.handle_query)
        self.register_command("/ht上传", self.handle_upload)
        
        # Optional: Register intent detection
        if config.enable_intent_detection:
            self.register_intent_handler(self.handle_intent)
    
    async def handle_query(self, context):
        """Handle /火瞳查询 command"""
        # Implementation in query_handler.py
        pass
```

#### 2.2.3 API Client (`api/client.py`)

```python
import aiohttp
import asyncio
from typing import Optional, Dict, Any

class APIClient:
    def __init__(self, config):
        self.base_url = config.fire_eye_api_url
        self.api_key = config.api_key
        self.timeout = aiohttp.ClientTimeout(total=config.timeout)
        self.max_retries = config.max_retries
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers={"X-API-Key": self.api_key}
            )
        return self.session
    
    async def query(self, query: str, session_id: str) -> Dict[str, Any]:
        """Send query request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                async with session.post(
                    f"{self.base_url}/api/v1/chat/query",
                    json={"query": query, "session_id": session_id}
                ) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    raise
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
    
    async def analyze(self, text: str, session_id: str) -> str:
        """Start document analysis task"""
        session = await self._get_session()
        async with session.post(
            f"{self.base_url}/api/v1/chat/analyze",
            json={"text": text, "session_id": session_id}
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data["task_id"]
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        session = await self._get_session()
        async with session.get(
            f"{self.base_url}/api/v1/chat/status/{task_id}"
        ) as response:
            response.raise_for_status()
            return await response.json()
    
    async def close(self):
        if self.session:
            await self.session.close()
```

#### 2.2.4 Polling Coroutine (`api/polling.py`)

```python
import asyncio
from typing import Callable

class TaskPoller:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.polling_interval = 3  # seconds
        self.max_polling_time = 300  # 5 minutes
    
    async def poll_task(
        self,
        task_id: str,
        on_complete: Callable,
        on_failed: Callable,
        on_progress: Optional[Callable] = None
    ):
        """
        Poll task status until completion or timeout
        
        Args:
            task_id: Task ID to poll
            on_complete: Callback when task completes successfully
            on_failed: Callback when task fails
            on_progress: Optional callback for progress updates
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # Check timeout
            if elapsed > self.max_polling_time:
                await on_failed(
                    "任务处理超时（5分钟），请使用任务ID手动查询状态"
                )
                return
            
            # Get task status
            try:
                status_data = await self.api_client.get_task_status(task_id)
                status = status_data["status"]
                
                if status == "completed":
                    await on_complete(status_data["result"])
                    return
                elif status == "failed":
                    await on_failed(status_data.get("error", "未知错误"))
                    return
                elif status in ["pending", "processing"]:
                    # Optional progress callback
                    if on_progress:
                        await on_progress(
                            status_data.get("progress", 0),
                            status_data.get("estimated_time_remaining")
                        )
                
            except Exception as e:
                logger.error(f"Polling error: {e}")
            
            # Wait before next poll
            await asyncio.sleep(self.polling_interval)
```

#### 2.2.5 Request Queue (`queue/request_queue.py`)

```python
import asyncio
from collections import deque
from typing import Callable, Any

class RequestQueue:
    def __init__(self, max_concurrent: int = 10, max_queue: int = 50):
        self.max_concurrent = max_concurrent
        self.max_queue = max_queue
        self.active_requests = 0
        self.queue = deque()
        self.lock = asyncio.Lock()
    
    async def enqueue(self, request_func: Callable, *args, **kwargs) -> Any:
        """
        Enqueue a request for execution
        
        Returns:
            Result of request_func or raises QueueFullError
        """
        async with self.lock:
            # Check if we can execute immediately
            if self.active_requests < self.max_concurrent:
                self.active_requests += 1
                try:
                    result = await request_func(*args, **kwargs)
                    return result
                finally:
                    self.active_requests -= 1
                    await self._process_queue()
            
            # Check queue capacity
            if len(self.queue) >= self.max_queue:
                raise QueueFullError("系统繁忙，请稍后重试")
            
            # Add to queue
            future = asyncio.Future()
            self.queue.append((request_func, args, kwargs, future))
            
            # Estimate wait time
            estimated_wait = len(self.queue) * 5  # Rough estimate: 5s per request
            logger.info(f"Request queued. Position: {len(self.queue)}, "
                       f"Estimated wait: {estimated_wait}s")
        
        # Wait for result
        return await future
    
    async def _process_queue(self):
        """Process next item in queue"""
        async with self.lock:
            if self.queue and self.active_requests < self.max_concurrent:
                request_func, args, kwargs, future = self.queue.popleft()
                self.active_requests += 1
                
                # Execute in background
                asyncio.create_task(self._execute_request(
                    request_func, args, kwargs, future
                ))
    
    async def _execute_request(self, request_func, args, kwargs, future):
        """Execute queued request"""
        try:
            result = await request_func(*args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            self.active_requests -= 1
            await self._process_queue()

class QueueFullError(Exception):
    pass
```

---

## 3. API Specifications

### 3.1 Chat API Endpoints

#### 3.1.1 POST /api/v1/chat/query

**Purpose**: Query knowledge graph using natural language

**Request**:
```json
{
  "query": "查询3.21火灾事故",
  "session_id": "sess_abc123"  // Optional
}
```

**Response**:
```json
{
  "status": "success",
  "message": "查询成功，返回3个结果",
  "data": {
    "results": [
      {
        "node_id": "node_123",
        "type": "FireEvent",
        "description": "3.21某商场火灾事故",
        "properties": {
          "date": "2023-03-21",
          "location": "某市某区某商场",
          "severity_level": 8
        },
        "related_nodes": [
          {
            "node_id": "node_456",
            "type": "Hazard",
            "description": "电线老化",
            "relation": "CAUSES",
            "confidence": 0.92
          }
        ]
      }
    ],
    "total_count": 3,
    "session_id": "sess_abc123"
  }
}
```

#### 3.1.2 POST /api/v1/chat/analyze

**Purpose**: Analyze document text and extract event chains

**Request**:
```json
{
  "text": "2023年3月21日，某商场发生火灾...",
  "session_id": "sess_abc123"  // Optional
}
```

**Response**:
```json
{
  "status": "success",
  "message": "分析任务已创建",
  "data": {
    "task_id": "task_xyz789",
    "status": "pending",
    "estimated_time": 45  // seconds
  }
}
```

#### 3.1.3 POST /api/v1/chat/upload

**Purpose**: Upload document file for analysis

**Request**: `multipart/form-data`
```
file: <binary file data>
session_id: sess_abc123  // Optional
```

**Response**:
```json
{
  "status": "success",
  "message": "文件上传成功",
  "data": {
    "task_id": "task_xyz789",
    "document_id": "doc_abc123",
    "filename": "火灾调查报告.pdf",
    "status": "pending"
  }
}
```

#### 3.1.4 GET /api/v1/chat/status/{task_id}

**Purpose**: Get async task status

**Response**:
```json
{
  "status": "success",
  "data": {
    "task_id": "task_xyz789",
    "status": "processing",  // pending | processing | completed | failed | timeout
    "progress": 65,  // 0-100
    "estimated_time_remaining": 15,  // seconds
    "result": null,  // Available when status is "completed"
    "error": null    // Available when status is "failed"
  }
}
```

**When completed**:
```json
{
  "status": "success",
  "data": {
    "task_id": "task_xyz789",
    "status": "completed",
    "progress": 100,
    "result": {
      "event_chains": [
        {
          "source": "电线老化",
          "relation": "导致",
          "target": "短路",
          "confidence": 0.92
        }
      ],
      "node_count": 15,
      "relationship_count": 12,
      "document_metadata": {
        "filename": "火灾调查报告.pdf",
        "upload_time": "2026-02-17T10:30:00Z"
      }
    }
  }
}
```

#### 3.1.5 GET /api/v1/chat/stats

**Purpose**: Get fire case statistics

**Request Parameters**:
- `stat_type`: Optional, one of "total" | "hazards" | "consequences" | "chains"
- `time_range`: Optional, e.g., "7d" | "30d" | "1y"

**Response**:
```json
{
  "status": "success",
  "data": {
    "total_fire_events": 156,
    "total_hazards": 89,
    "total_consequences": 67,
    "hazard_distribution": {
      "电气隐患": 45,
      "消防设施缺陷": 23,
      "违规操作": 21
    },
    "time_range": "30d",
    "generated_at": "2026-02-17T10:30:00Z"
  }
}
```

### 3.2 Authentication

All API requests must include API key in header:

```
X-API-Key: your-api-key-here
```

**Error Response** (401 Unauthorized):
```json
{
  "status": "error",
  "message": "Invalid API Key",
  "code": "AUTH_FAILED"
}
```

---

## 4. Data Models

### 4.1 Backend Data Models

#### 4.1.1 Session Model

```python
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional

class ConversationTurn(BaseModel):
    timestamp: datetime
    user_message: str
    bot_response: str
    query_results: Optional[List[Dict[str, Any]]] = None

class SessionData(BaseModel):
    session_id: str
    user_id: str
    platform: str  # "qq" | "telegram" | "wechat" | "dingtalk" | "feishu"
    created_at: datetime
    last_activity: datetime
    conversation_history: List[ConversationTurn] = []
    context: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

#### 4.1.2 Task Model

```python
class Task(BaseModel):
    task_id: str
    task_type: str  # "analyze" | "upload"
    status: str  # "pending" | "processing" | "completed" | "failed" | "timeout"
    progress: int = 0  # 0-100
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_time_remaining: Optional[int] = None  # seconds
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    session_id: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None

class TaskResult(BaseModel):
    event_chains: List[EventChain]
    node_count: int
    relationship_count: int
    document_metadata: Optional[Dict[str, Any]] = None
    citations: List[Citation] = []

class Citation(BaseModel):
    source_document: str
    page_number: Optional[int] = None
    confidence: float
    text_snippet: Optional[str] = None
```

#### 4.1.3 Chat Response Models

```python
class ChatQueryResponse(BaseModel):
    status: str = "success"
    message: str
    data: Dict[str, Any]

class TaskResponse(BaseModel):
    status: str = "success"
    message: str
    data: Dict[str, Any]  # Contains task_id, status, etc.

class TaskStatusResponse(BaseModel):
    status: str = "success"
    data: Task

class StatsResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]
```

### 4.2 Plugin Configuration Model

```yaml
# config.yaml
fire_eye:
  api_url: "http://localhost:8000"
  api_key: "${FIRE_EYE_API_KEY}"  # From environment variable
  timeout: 30  # seconds
  max_retries: 3
  
session:
  ttl: 1800  # 30 minutes
  
request_queue:
  max_concurrent: 10
  max_queue_size: 50
  
intent_detection:
  enabled: false  # Set to true to enable LLM intent detection
  
file_upload:
  retain_files_on_server: false  # Delete files after extraction
  temp_dir: "/tmp/fire-eye"
  max_file_size: 10485760  # 10MB
  
logging:
  level: "INFO"
  file: "fire-eye-plugin.log"
  max_size: 10485760  # 10MB
  backup_count: 5
```

---

## 5. Sequence Diagrams

### 5.1 Query Flow (Synchronous)

```
User          Plugin         API Client      Fire-Eye Backend      Neo4j
 │              │                │                  │                 │
 │─/火瞳查询 3.21事故─>│                │                  │                 │
 │              │                │                  │                 │
 │              │─Get/Create─────>│                  │                 │
 │              │  session_id    │                  │                 │
 │              │<───────────────│                  │                 │
 │              │                │                  │                 │
 │              │─Enqueue────────>│                  │                 │
 │              │  Request       │                  │                 │
 │              │                │                  │                 │
 │              │                │─POST /chat/query─>│                 │
 │              │                │  + session_id    │                 │
 │              │                │  + API Key       │                 │
 │              │                │                  │                 │
 │              │                │                  │─Resolve Context─>│
 │              │                │                  │<────────────────│
 │              │                │                  │                 │
 │              │                │                  │─Query Graph─────>│
 │              │                │                  │<────────────────│
 │              │                │                  │                 │
 │              │                │<─Response────────│                 │
 │              │                │  (results)       │                 │
 │              │<───────────────│                  │                 │
 │              │                │                  │                 │
 │              │─Format─────────>│                  │                 │
 │              │  Message       │                  │                 │
 │<─结果消息────│                │                  │                 │
 │              │                │                  │                 │
```

### 5.2 Document Analysis Flow (Asynchronous)

```
User          Plugin         Poller         Fire-Eye Backend      Worker
 │              │              │                  │                 │
 │─/火瞳分析 <text>─>│              │                  │                 │
 │              │              │                  │                 │
 │              │──POST /chat/analyze─>│                  │                 │
 │              │              │                  │                 │
 │              │<─task_id─────│                  │                 │
 │<─"分析中..."──│              │                  │                 │
 │              │              │                  │                 │
 │              │─Start Polling─>│                  │                 │
 │              │              │                  │                 │
 │              │              │─GET /status/{id}─>│                 │
 │              │              │<─pending─────────│                 │
 │              │              │                  │                 │
 │              │              │  (wait 3s)       │                 │
 │              │              │                  │                 │
 │              │              │─GET /status/{id}─>│                 │
 │              │              │<─processing 50%──│                 │
 │              │              │                  │                 │
 │              │              │  (wait 3s)       │                 │
 │              │              │                  │─Extract─────────>│
 │              │              │                  │  Event Chains   │
 │              │              │                  │<────────────────│
 │              │              │                  │                 │
 │              │              │─GET /status/{id}─>│                 │
 │              │              │<─completed───────│                 │
 │              │<─Result──────│  + event_chains  │                 │
 │              │              │                  │                 │
 │<─"分析完成!"──│              │                  │                 │
 │  + 结果详情   │              │                  │                 │
```

### 5.3 File Upload Flow

```
User          Plugin         File Handler    Fire-Eye Backend      Worker
 │              │                │                  │                 │
 │─Upload File──>│                │                  │                 │
 │  (via IM)    │                │                  │                 │
 │              │                │                  │                 │
 │              │─Download───────>│                  │                 │
 │              │  from IM       │                  │                 │
 │              │  Platform      │                  │                 │
 │              │<───────────────│                  │                 │
 │              │  /tmp/file.pdf │                  │                 │
 │              │                │                  │                 │
 │              │─Validate───────>│                  │                 │
 │              │  File Type     │                  │                 │
 │              │<───────────────│                  │                 │
 │              │                │                  │                 │
 │              │──POST /chat/upload (multipart)───>│                 │
 │              │                │                  │                 │
 │              │<─task_id───────│                  │                 │
 │<─"上传成功"───│                │                  │                 │
 │              │                │                  │                 │
 │              │─Delete Temp────>│                  │                 │
 │              │  File          │                  │                 │
 │              │                │                  │                 │
 │              │─Start Polling──>│                  │                 │
 │              │                │                  │                 │
 │              │                │                  │─Process─────────>│
 │              │                │                  │  Document       │
 │              │                │                  │<────────────────│
 │              │                │                  │                 │
 │              │                │                  │─Delete File─────>│
 │              │                │                  │  (if configured)│
 │              │                │                  │                 │
 │              │<─Result────────│                  │                 │
 │<─"处理完成!"──│                │                  │                 │
```

### 5.4 Context-Aware Multi-Turn Conversation

```
User          Plugin         Session Mgr     Fire-Eye Backend      Context Mgr
 │              │                │                  │                 │
 │─"查询3.21事故"─>│                │                  │                 │
 │              │─Get Session────>│                  │                 │
 │              │<─sess_abc123───│                  │                 │
 │              │                │                  │                 │
 │              │──POST /chat/query (sess_abc123)──>│                 │
 │              │<─Results───────│                  │                 │
 │<─[Event A, B]─│                │                  │                 │
 │              │                │                  │                 │
 │              │─Save Turn──────>│                  │                 │
 │              │  + Results     │                  │                 │
 │              │                │                  │                 │
 │─"主要原因?"───>│                │                  │                 │
 │              │─Get Session────>│                  │                 │
 │              │<─sess_abc123───│                  │                 │
 │              │  + History     │                  │                 │
 │              │                │                  │                 │
 │              │──POST /chat/query (sess_abc123)──>│                 │
 │              │  "主要原因?"    │                  │                 │
 │              │                │                  │                 │
 │              │                │                  │─Resolve─────────>│
 │              │                │                  │  Reference      │
 │              │                │                  │  (3.21事故)     │
 │              │                │                  │<────────────────│
 │              │                │                  │                 │
 │              │<─Results───────│                  │                 │
 │<─[Hazard X]───│                │                  │                 │
```

---

## 6. Security Design

### 6.1 Authentication

**API Key Authentication**:
- All requests must include `X-API-Key` header
- Keys stored in environment variables (not in code)
- Support multiple keys for different platforms
- Failed authentication attempts logged for security audit

**Implementation**:
```python
# Backend: .env
ASTRBOT_API_KEYS=key1,key2,key3

# Plugin: config.yaml
fire_eye:
  api_key: "${FIRE_EYE_API_KEY}"  # From environment
```

### 6.2 Data Privacy

**File Retention Policy**:
- Default: Delete uploaded files immediately after extraction
- Configurable via `retain_files_on_server` setting
- When retention enabled: implement access controls and audit logging

**Sensitive Data Handling**:
- No PII stored in logs (mask user IDs, file names)
- Session data expires after 30 minutes
- Temporary files cleaned up after 1 hour maximum

**Implementation**:
```python
# After extraction completes
if not config.retain_files_on_server:
    await file_manager.delete_file(file_path)
    logger.info(f"File deleted: {file_id} (privacy protection)")
```

### 6.3 Audit Logging

**Events to Log**:
- Authentication attempts (success/failure)
- API requests (endpoint, user, timestamp)
- File uploads/deletions
- Task creation/completion
- Errors and exceptions

**Log Format**:
```json
{
  "timestamp": "2026-02-17T10:30:00Z",
  "event_type": "api_request",
  "user_id": "user_***",  // Masked
  "platform": "qq",
  "endpoint": "/api/v1/chat/query",
  "status": "success",
  "duration_ms": 245
}
```

### 6.4 Rate Limiting

**Request Queue**:
- Max 10 concurrent requests per plugin instance
- Queue up to 50 requests
- Reject with "System Busy" when queue full

**Purpose**:
- Protect backend from overload
- Ensure fair resource allocation
- Prevent abuse

---

## 7. Performance Considerations

### 7.1 Caching Strategy

**Statistics Caching**:
- Cache frequently requested statistics for 5 minutes
- Use Redis for distributed caching
- Invalidate cache on data updates

**Session Caching**:
- Store session data in Redis with 30-minute TTL
- Automatic cleanup of expired sessions

### 7.2 Connection Pooling

**HTTP Client**:
- Reuse aiohttp ClientSession
- Connection pool size: 20
- Keep-alive timeout: 60 seconds

**Database Connections**:
- Neo4j connection pool: 50 connections
- Redis connection pool: 10 connections

### 7.3 Async Processing

**Task Processing**:
- All long-running operations (>5s) use async tasks
- Background workers process tasks independently
- Status polling prevents blocking

**Benefits**:
- No timeout issues with IM platforms
- Better user experience
- Scalable architecture

---

## 8. Deployment Architecture

### 8.1 Development Environment

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Machine                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   AstrBot    │  │  Fire-Eye    │  │    Neo4j     │     │
│  │   + Plugin   │  │   Backend    │  │   + Redis    │     │
│  │  (Port N/A)  │  │  (Port 8000) │  │ (7687/6379)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                  │                  │             │
│         └──────────────────┴──────────────────┘             │
│                    localhost                                │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Production Environment

```
┌─────────────────────────────────────────────────────────────┐
│                    IM Platforms                              │
│         QQ  Telegram  WeChat  DingTalk  Feishu             │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  AstrBot Server                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  AstrBot Core + Fire-Eye Plugin                        │ │
│  │  - Session Manager (in-memory)                         │ │
│  │  - Request Queue (in-memory)                           │ │
│  │  - API Client (connection pool)                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ HTTPS + API Key
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Fire-Eye Backend Server                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  FastAPI Application                                   │ │
│  │  - Chat API Layer                                      │ │
│  │  - Task Manager (Redis-backed)                         │ │
│  │  - Session Service (Redis-backed)                      │ │
│  │  - Background Workers                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Neo4j     │  │    Redis     │  │  File System │     │
│  │  (Cluster)   │  │  (Cluster)   │  │   (Shared)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Deployment Checklist

#### Backend Deployment

- [ ] Install Python 3.10+ and dependencies
- [ ] Configure environment variables (.env file)
- [ ] Set up Neo4j database connection
- [ ] Set up Redis connection
- [ ] Configure API keys for AstrBot
- [ ] Set up file storage directory with proper permissions
- [ ] Configure logging (file rotation, level)
- [ ] Start FastAPI application (uvicorn)
- [ ] Verify health check endpoint
- [ ] Set up monitoring and alerting

#### Plugin Deployment

- [ ] Install AstrBot platform
- [ ] Install Fire-Eye plugin
- [ ] Configure plugin (config.yaml)
- [ ] Set Fire-Eye API URL and key
- [ ] Configure IM platform connections
- [ ] Test command handlers
- [ ] Verify file upload functionality
- [ ] Monitor plugin logs
- [ ] Set up error alerting

### 8.4 Configuration Management

**Backend Configuration** (`.env`):
```bash
# API Keys
ASTRBOT_API_KEYS=key1,key2,key3

# Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
REDIS_HOST=localhost
REDIS_PORT=6379

# File Storage
UPLOAD_DIR=/var/fire-eye/uploads
RETAIN_FILES_ON_SERVER=false

# Session
SESSION_TTL=1800

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/fire-eye/api.log
```

**Plugin Configuration** (`config.yaml`):
```yaml
fire_eye:
  api_url: "https://fire-eye-api.example.com"
  api_key: "${FIRE_EYE_API_KEY}"
  timeout: 30
  max_retries: 3

request_queue:
  max_concurrent: 10
  max_queue_size: 50

file_upload:
  retain_files_on_server: false
  temp_dir: "/tmp/fire-eye"
  max_file_size: 10485760

logging:
  level: "INFO"
  file: "/var/log/astrbot/fire-eye-plugin.log"
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Backend Components**:
- Session Service: Create, retrieve, update, expire sessions
- Task Manager: Create, update, complete, fail tasks
- Context Manager: Resolve references in queries
- Authentication: Validate API keys, handle invalid keys

**Plugin Components**:
- API Client: Request/response handling, retry logic
- Request Queue: Enqueue, process, reject when full
- Message Formatter: Format different response types
- File Handler: Download, validate, upload, cleanup

### 9.2 Integration Tests

**API Endpoints**:
- POST /api/v1/chat/query: Query with/without session
- POST /api/v1/chat/analyze: Create task, check status
- POST /api/v1/chat/upload: Upload file, process document
- GET /api/v1/chat/status/{task_id}: Poll task status
- GET /api/v1/chat/stats: Retrieve statistics

**End-to-End Flows**:
- Complete query flow: User → Plugin → Backend → Neo4j → Response
- Async analysis flow: Submit → Poll → Complete
- Multi-turn conversation: Query → Follow-up with context
- File upload flow: Upload → Process → Extract → Respond

### 9.3 Performance Tests

**Load Testing**:
- Concurrent requests: 10, 50, 100 users
- Request queue behavior under load
- Task processing throughput
- Session management scalability

**Stress Testing**:
- Maximum queue size (50 requests)
- Timeout handling (5-minute limit)
- Memory usage with many sessions
- File upload with large files (10MB)

### 9.4 Security Tests

**Authentication**:
- Valid API key: Should succeed
- Invalid API key: Should return 401
- Missing API key: Should return 401
- Multiple API keys: Should all work

**Privacy**:
- File deletion after extraction
- Session data expiration
- Log masking of sensitive data
- Audit trail completeness

---

## 10. Monitoring and Observability

### 10.1 Metrics to Track

**Backend Metrics**:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate (4xx, 5xx)
- Active sessions count
- Task queue length
- Task completion time
- Cache hit rate

**Plugin Metrics**:
- Command usage frequency
- Request queue size
- Polling coroutine count
- File upload success rate
- Error rate by type

### 10.2 Logging

**Log Levels**:
- DEBUG: Detailed execution flow
- INFO: Normal operations (requests, tasks)
- WARNING: Recoverable errors (retries, queue full)
- ERROR: Failures requiring attention

**Log Aggregation**:
- Centralized logging (e.g., ELK stack)
- Structured JSON logs
- Correlation IDs for request tracing

### 10.3 Alerting

**Critical Alerts**:
- Backend service down
- Database connection failure
- High error rate (>5%)
- Queue consistently full

**Warning Alerts**:
- High response time (>5s)
- Low cache hit rate (<50%)
- Many task timeouts
- Disk space low (file storage)

---

## 11. Future Enhancements

### 11.1 Phase 2 Features

**Intent Detection**:
- Enable LLM-based intent detection
- Auto-trigger commands without `/火瞳` prefix
- Fine-tune intent classification model

**Advanced Analytics**:
- Fire pattern recognition
- Predictive risk analysis
- Trend visualization in chat

**Multi-Language Support**:
- English interface
- Automatic language detection
- Translated responses

### 11.2 Phase 3 Features

**Voice Integration**:
- Voice command support
- Text-to-speech responses
- Voice file upload

**Mobile App**:
- Dedicated mobile application
- Push notifications
- Offline mode

**Collaborative Features**:
- Team workspaces
- Shared investigation sessions
- Real-time collaboration

---

## 12. Summary

This design document provides a comprehensive architecture for integrating the Fire-Eye fire investigation knowledge graph system with AstrBot chatbot platform.

### Key Design Decisions

1. **Minimal Intrusion**: Fire-Eye backend remains independent, accessed only via REST API
2. **Async-First**: Task-based processing prevents timeout issues
3. **Context-Aware**: Session management enables natural multi-turn conversations
4. **Security by Default**: API key authentication, privacy protection, audit logging
5. **Graceful Degradation**: Request queuing and rate limiting prevent overload

### Implementation Phases

**Phase 1: Core Infrastructure** (Week 1-2)
- Chat API Layer with authentication
- Session and task management
- Basic command handlers

**Phase 2: Advanced Features** (Week 2-3)
- File upload with privacy protection
- Request queue and rate limiting
- Citation and provenance tracking

**Phase 3: Optimization** (Week 3-4)
- Performance tuning
- Monitoring and alerting
- Documentation and training

### Success Criteria

- ✅ All 16 requirements implemented
- ✅ Response time <3s for queries
- ✅ Task completion time <60s for analysis
- ✅ Zero data loss or corruption
- ✅ 99.9% uptime
- ✅ Comprehensive audit trail

---

## Appendix

### A. Technology References

- **FastAPI**: https://fastapi.tiangolo.com/
- **AstrBot**: https://github.com/Soulter/AstrBot
- **Neo4j Python Driver**: https://neo4j.com/docs/python-manual/
- **aiohttp**: https://docs.aiohttp.org/
- **Redis**: https://redis.io/docs/

### B. Related Documents

- [Requirements Document](./requirements.md)
- [Revision Notes](./REVISION_NOTES.md)
- [Tasks Document](./tasks.md) (to be created)

### C. Glossary

See Requirements Document Section: Glossary

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-17  
**Status**: Ready for Implementation
