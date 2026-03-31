# Design Document: AstrBot Fire-Eye QQ Plugin

## Overview

The Fire-Eye QQ Plugin is a comprehensive AstrBot plugin that extends Fire-Eye fire investigation knowledge graph functionality to the QQ messaging platform. The design follows a modular architecture with clear separation of concerns, enabling maintainability, testability, and extensibility.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AstrBot Framework                         │
│  (Event handling, message routing, plugin lifecycle)         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │  Fire-Eye QQ Plugin     │
        │  (main.py)             │
        │                        │
        │ • Command Handlers     │
        │ • Event Routing        │
        │ • Response Delivery    │
        └────────────┬───────────┘
                     │
        ┌────────────┴────────────────────────────────────┐
        │                                                 │
   ┌────▼──────┐  ┌──────────┐  ┌──────────┐  ┌────────▼────┐
   │   API     │  │ Session  │  │ Request  │  │  Message    │
   │  Client   │  │ Manager  │  │  Queue   │  │ Formatter   │
   │           │  │          │  │          │  │             │
   │ • HTTP    │  │ • Track  │  │ • Limit  │  │ • Format    │
   │ • Retry   │  │ • History│  │ • Queue  │  │ • Split     │
   │ • Error   │  │ • Expire │  │ • Manage │  │ • Escape    │
   │   Handle  │  │          │  │          │  │             │
   └────┬──────┘  └──────────┘  └──────────┘  └─────────────┘
        │
        └────────────┬─────────────────────────────────────┐
                     │                                     │
            ┌────────▼────────┐              ┌─────────────▼──┐
            │ Fire-Eye Backend │              │  QQ Platform   │
            │  Chat API        │              │  (via AstrBot) │
            │                  │              │                │
            │ • /query         │              │ • Messages     │
            │ • /upload        │              │ • Events       │
            │ • /stats         │              │ • Files        │
            │ • /status        │              │                │
            └───────────────────┘             └────────────────┘
```

### Component Architecture

#### 1. Main Plugin (main.py)

**Responsibilities:**
- Register command handlers with AstrBot
- Route incoming QQ messages to appropriate handlers
- Manage plugin lifecycle (initialization, shutdown)
- Coordinate between components

**Key Classes:**
- `FireEyeQQPlugin`: Main plugin class
- `QueryHandler`: Handles `/火瞳查询` commands
- `StatsHandler`: Handles `/火瞳统计` commands
- `HelpHandler`: Handles `/火瞳帮助` commands

**Design Patterns:**
- Command pattern for command handling
- Dependency injection for component initialization
- Async/await for non-blocking operations

#### 2. API Client (api/client.py)

**Responsibilities:**
- Communicate with Fire-Eye backend
- Handle HTTP requests and responses
- Implement retry logic with exponential backoff
- Parse and validate API responses

**Key Classes:**
- `APIClient`: Main API communication class
- `APIError`: Custom exception for API errors
- `RetryConfig`: Configuration for retry behavior

**Design Patterns:**
- Singleton pattern for API client instance
- Retry pattern with exponential backoff
- Error handling with custom exceptions

**Key Methods:**
- `query(query_text, session_id)`: Send query to backend
- `get_stats(stat_type, session_id)`: Get statistics
- `get_status(task_id)`: Check async task status
- `upload_file(file_path, session_id)`: Upload file for analysis

#### 3. Session Manager (session/manager.py)

**Responsibilities:**
- Create and manage user sessions
- Track conversation history
- Handle session expiration
- Provide session context for multi-turn conversations

**Key Classes:**
- `SessionManager`: Main session management class
- `Session`: Session data model
- `ConversationHistory`: Stores conversation context

**Design Patterns:**
- Repository pattern for session storage
- TTL (Time-To-Live) pattern for session expiration
- Context manager pattern for session lifecycle

**Key Methods:**
- `get_or_create_session(user_id)`: Get existing or create new session
- `add_to_history(session_id, message, response)`: Add to conversation history
- `get_history(session_id)`: Retrieve conversation history
- `expire_session(session_id)`: Mark session as expired

#### 4. Request Queue (queue/request_queue.py)

**Responsibilities:**
- Manage concurrent request processing
- Queue requests when at capacity
- Implement backpressure mechanism
- Track queue metrics

**Key Classes:**
- `RequestQueue`: Main queue management class
- `QueuedRequest`: Request wrapper with metadata
- `QueueMetrics`: Metrics tracking

**Design Patterns:**
- Producer-consumer pattern
- Backpressure pattern for load management
- Metrics collection pattern

**Key Methods:**
- `enqueue(request)`: Add request to queue
- `dequeue()`: Get next request to process
- `is_at_capacity()`: Check if queue is full
- `get_metrics()`: Get queue statistics

#### 5. Message Formatter (utils/formatter.py)

**Responsibilities:**
- Format Fire-Eye responses for QQ display
- Handle message length limits
- Escape special characters
- Support QQ-specific formatting

**Key Classes:**
- `MessageFormatter`: Main formatting class
- `FormattedMessage`: Formatted message wrapper
- `MessageSplitter`: Handles message splitting

**Design Patterns:**
- Builder pattern for message construction
- Strategy pattern for different formatting types
- Template method pattern for formatting pipeline

**Key Methods:**
- `format_query_results(results)`: Format query results
- `format_stats(stats)`: Format statistics
- `format_error(error)`: Format error messages
- `split_message(message)`: Split long messages

## Data Flow

### Query Command Flow

```
User sends: /火瞳查询 <query>
    │
    ▼
[main.py] Parse command
    │
    ▼
[session/manager.py] Get/create session
    │
    ▼
[queue/request_queue.py] Enqueue request
    │
    ▼
[api/client.py] Send to backend
    │
    ▼
[Fire-Eye Backend] Process query
    │
    ▼
[api/client.py] Receive results
    │
    ▼
[utils/formatter.py] Format for QQ
    │
    ▼
[main.py] Send to user
    │
    ▼
User receives formatted response
```

### Async Upload Flow

```
User sends: /火瞳上传 + file
    │
    ▼
[main.py] Receive file event
    │
    ▼
[api/client.py] Download from QQ
    │
    ▼
[api/client.py] Validate file
    │
    ▼
[api/client.py] Upload to backend
    │
    ▼
Backend returns task_id
    │
    ▼
[api/client.py] Start polling
    │
    ▼
Poll every 3 seconds: /api/v1/chat/status/{task_id}
    │
    ├─ If pending/processing: continue polling
    │
    ├─ If completed: 
    │   ▼
    │   [api/client.py] Get results
    │   ▼
    │   [utils/formatter.py] Format results
    │   ▼
    │   [main.py] Send to user
    │
    └─ If failed/timeout: notify user
```

## Configuration

### config.yaml Structure

```yaml
fire_eye:
  api_url: "http://localhost:8000/api/v1"
  api_key: "your-api-key"
  timeout: 30
  retries: 3

session:
  ttl: 1800  # 30 minutes

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

## Error Handling Strategy

### Error Categories

1. **Network Errors**: Connection failures, timeouts
   - Strategy: Retry with exponential backoff
   - User Message: "Network error, retrying..."

2. **API Errors**: Invalid requests, authentication failures
   - Strategy: Log and return meaningful error
   - User Message: "API error: [specific reason]"

3. **Validation Errors**: Invalid input, file type mismatch
   - Strategy: Return validation error immediately
   - User Message: "Invalid input: [specific reason]"

4. **System Errors**: Unexpected exceptions
   - Strategy: Log full error, return generic message
   - User Message: "System error, please try again later"

### Retry Strategy

- **Max Retries**: 3
- **Backoff Strategy**: Exponential (1s, 2s, 4s)
- **Timeout**: 30 seconds per request
- **Jitter**: Random 0-1s added to prevent thundering herd

## Performance Considerations

### Optimization Strategies

1. **Connection Pooling**: Reuse HTTP connections
2. **Async Processing**: Non-blocking I/O for all operations
3. **Message Caching**: Cache frequently accessed data
4. **Lazy Loading**: Load data only when needed
5. **Batch Processing**: Process multiple requests efficiently

### Performance Targets

- Command response time: < 2 seconds (excluding backend)
- File download: < 30 seconds
- File upload: < 60 seconds
- Message formatting: < 500ms
- Session lookup: < 100ms

## Security Considerations

### Data Protection

1. **API Key Management**: Store in environment variables
2. **HTTPS Communication**: All backend communication over HTTPS
3. **Input Validation**: Sanitize all user input
4. **Temporary Files**: Secure storage with restricted permissions
5. **Logging**: Never log sensitive data (API keys, user IDs)

### Access Control

1. **Session Isolation**: Each user has isolated session
2. **Rate Limiting**: Enforce queue limits to prevent abuse
3. **File Validation**: Verify file type and size before processing
4. **Error Messages**: Never expose internal system details

## Extensibility

### Adding New Commands

1. Create handler method in main.py
2. Register with @filter.command decorator
3. Implement command logic
4. Add to help message

### Adding New API Endpoints

1. Add method to APIClient class
2. Implement request/response handling
3. Add error handling
4. Update documentation

### Custom Message Formatting

1. Add formatter method to MessageFormatter class
2. Implement formatting logic
3. Handle message splitting if needed
4. Add to format_* methods

## Testing Strategy

### Unit Tests

- Test each component in isolation
- Mock external dependencies
- Test error conditions
- Achieve 80%+ code coverage

### Integration Tests

- Test component interactions
- Test with mock backend API
- Test end-to-end flows
- Test error scenarios

### Test Fixtures

- Mock API responses
- Sample user data
- Test configuration
- Error response samples

## Deployment Architecture

### Development Environment

```
Local Machine
├── AstrBot (dev)
├── Fire-Eye Backend (dev)
└── QQ Plugin (dev)
```

### Production Environment

```
Server
├── AstrBot (production)
├── Fire-Eye Backend (production)
└── QQ Plugin (production)
```

### Configuration Management

- Environment-specific config files
- Environment variable overrides
- Secure credential storage
- Configuration validation on startup

## Monitoring and Logging

### Logging Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures

### Metrics Collection

- Command execution count
- Average response time
- Error rate
- Queue size and wait time
- File upload statistics

### Log Rotation

- Max file size: 10MB
- Backup count: 5
- Automatic rotation on size limit

## Versioning and Compatibility

### Version Strategy

- Semantic versioning (MAJOR.MINOR.PATCH)
- Backward compatibility maintained
- Breaking changes documented

### API Compatibility

- Support multiple backend API versions
- Graceful degradation for missing features
- Version detection and adaptation

## Future Enhancements

1. **File Upload Support**: When QQ AstrBot supports file uploads
2. **Advanced Analytics**: More detailed statistics and insights
3. **Custom Workflows**: User-defined command sequences
4. **Integration with Other Platforms**: Support for WeChat, DingTalk, etc.
5. **Machine Learning**: Intelligent query suggestions
6. **Real-time Notifications**: Push notifications for important events

## Conclusion

The Fire-Eye QQ Plugin is designed with modularity, reliability, and extensibility in mind. The architecture supports current requirements while providing a foundation for future enhancements. Clear separation of concerns enables independent testing and maintenance of each component.
