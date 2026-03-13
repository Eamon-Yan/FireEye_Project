# Requirements Document: AstrBot Integration for Fire-Eye System

## Introduction

This document specifies the requirements for integrating the Fire-Eye (火瞳) fire investigation knowledge graph system with AstrBot, an open-source chatbot platform. The integration will enable firefighters and investigators to interact with the Fire-Eye system through popular messaging platforms (QQ, Telegram, WeChat, DingTalk, Feishu) using natural language commands.

The integration follows a minimal intrusion principle: the Fire-Eye system remains independent and is accessed via REST API, while AstrBot acts as a conversational interface layer.

## Architecture Decisions

### Trigger Strategy

The plugin supports two interaction modes:

1. **Command Mode (Primary)**: Users explicitly invoke Fire-Eye functions using slash commands (e.g., `/火瞳查询 <query>`). This is the default and recommended mode for production environments to prevent unintended activations.

2. **Intent Detection Mode (Optional)**: When enabled, AstrBot's LLM analyzes user messages and automatically triggers Fire-Eye functions when fire investigation intent is detected. This provides a more natural conversation experience but requires careful tuning to avoid false positives.

**Recommendation**: Start with Command Mode for stability, then optionally enable Intent Detection after observing usage patterns.

### Async Processing Strategy

Document analysis and file upload operations are inherently slow (30-60 seconds) due to LLM inference and graph construction. To prevent chat platform timeouts:

- Backend immediately returns a `task_id` when processing starts
- Plugin polls task status in background every 3 seconds
- Results are pushed to user proactively when processing completes
- Users can continue other conversations while processing happens

This ensures responsive user experience even with long-running operations.

## Glossary

- **Fire-Eye System**: The existing fire investigation knowledge graph system with Neo4j database and REST API
- **AstrBot**: Open-source chatbot platform supporting multiple messaging platforms
- **Chat_API_Layer**: New REST API endpoints in Fire-Eye backend specifically designed for chat interactions
- **Fire-Eye_Plugin**: AstrBot plugin that handles commands and communicates with Fire-Eye backend
- **Command_Handler**: Component in Fire-Eye_Plugin that processes user commands
- **API_Client**: Component in Fire-Eye_Plugin that communicates with Fire-Eye backend
- **Message_Formatter**: Component that formats Fire-Eye responses for chat display
- **FireEvent**: Red node type in knowledge graph representing fire events
- **Hazard**: Orange node type representing hazards/causes
- **Consequence**: Purple node type representing consequences/outcomes
- **Event_Chain**: Sequence of connected nodes showing fire progression
- **Natural_Language_Query**: User query in conversational language (not structured commands)
- **Task_ID**: Unique identifier for asynchronous processing tasks (document analysis, file upload)
- **Session_ID**: Unique identifier for conversation context tracking across multiple queries
- **Polling_Coroutine**: Background async task that periodically checks task status
- **Citation**: Reference to source document that supports a graph inference
- **Provenance**: Traceability information showing the origin and evidence for knowledge graph data

## Requirements

### Requirement 1: Chat API Layer in Fire-Eye Backend

**User Story:** As a Fire-Eye system administrator, I want a dedicated chat API layer in the backend, so that external chat platforms can interact with the system without affecting existing web APIs.

#### Acceptance Criteria

1. WHEN the Fire-Eye backend starts, THE Chat_API_Layer SHALL register routes under `/api/v1/chat/` prefix
2. WHEN an API request is received without valid authentication, THE Chat_API_Layer SHALL reject it with 401 status code
3. WHEN an API request is received with valid API key, THE Chat_API_Layer SHALL process the request and return appropriate response
4. THE Chat_API_Layer SHALL maintain separation from existing web API endpoints
5. WHEN the Chat_API_Layer processes requests, THE existing Fire-Eye web interface SHALL continue functioning without interruption

### Requirement 2: Natural Language Query Endpoint (Context-Aware)

**User Story:** As a firefighter, I want to query fire cases using natural language in chat, so that I can quickly find relevant information without learning complex query syntax.

#### Acceptance Criteria

1. WHEN a natural language query is sent to `/api/v1/chat/query`, THE Chat_API_Layer SHALL accept optional `session_id` parameter for context tracking
2. WHEN `session_id` is provided, THE Chat_API_Layer SHALL retrieve conversation history to understand context
3. WHEN the query intent is identified, THE Chat_API_Layer SHALL convert it to appropriate Neo4j graph queries
4. WHEN graph data is retrieved, THE Chat_API_Layer SHALL format results in chat-friendly format (concise, readable)
5. WHEN no results are found, THE Chat_API_Layer SHALL return a helpful message suggesting query refinements
6. WHEN query processing fails, THE Chat_API_Layer SHALL return error message without exposing internal system details
7. THE Chat_API_Layer SHALL support queries about fire events, hazards, consequences, and event chains
8. WHEN multiple results are found, THE Chat_API_Layer SHALL limit response to top 10 most relevant results
9. THE Chat_API_Layer SHALL maintain conversation context for up to 30 minutes per session
10. WHEN context includes previous query results, THE Chat_API_Layer SHALL resolve references (e.g., "主要原因" refers to previously mentioned event)

### Requirement 3: Document Analysis Endpoint (Async Processing)

**User Story:** As a fire investigator, I want to submit fire investigation documents through chat, so that I can analyze cases while communicating with my team.

#### Acceptance Criteria

1. WHEN document text is sent to `/api/v1/chat/analyze`, THE Chat_API_Layer SHALL validate the text content
2. **[MODIFIED]** WHEN text content is valid, THE Chat_API_Layer SHALL create an analysis task and return a `task_id` immediately with status `pending`, instead of waiting for full completion
3. THE Chat_API_Layer SHALL NOT block the HTTP response waiting for extraction to complete (to avoid IM platform timeouts)
4. WHEN extraction completes, THE Chat_API_Layer SHALL update task status to `completed` and store results
5. WHEN extraction fails, THE Chat_API_Layer SHALL update task status to `failed` with error details
6. THE Chat_API_Layer SHALL support text content up to 50,000 characters
7. **[NEW]** THE Chat_API_Layer SHALL provide `/api/v1/chat/status/{task_id}` endpoint to check progress
8. **[NEW]** WHEN task status is queried, THE Chat_API_Layer SHALL return: status (`pending`/`processing`/`completed`/`failed`), progress percentage (0-100), estimated time remaining, and results if completed
9. **[NEW]** THE Plugin SHALL poll the status endpoint every 3 seconds and push the final Event_Chain result to the user when status becomes `completed`
10. **[NEW]** WHEN task processing exceeds 5 minutes, THE Chat_API_Layer SHALL mark it as `timeout` and allow manual status check

### Requirement 4: Document Upload Endpoint (Async Processing)

**User Story:** As a fire investigator, I want to upload document files through chat interfaces, so that I can process investigation reports without switching to web interface.

#### Acceptance Criteria

1. WHEN a file is uploaded to `/api/v1/chat/upload`, THE Chat_API_Layer SHALL accept `multipart/form-data` format with file stream
2. WHEN file validation passes, THE Chat_API_Layer SHALL save the file and return a `task_id` immediately with status `pending`
3. THE Chat_API_Layer SHALL NOT wait for full document processing before responding to avoid timeout
4. WHEN file validation fails, THE Chat_API_Layer SHALL return error message specifying validation failure reason
5. THE Chat_API_Layer SHALL support PDF, TXT, and DOCX file formats
6. THE Chat_API_Layer SHALL enforce maximum file size of 10MB
7. WHEN upload is successful, THE Chat_API_Layer SHALL return a `task_id` and `document_id` for future reference
8. THE Chat_API_Layer SHALL process uploaded documents asynchronously in background
9. WHEN processing completes, THE task status SHALL be updated to `completed` with extracted event chains

### Requirement 5: Statistics Query Endpoint

**User Story:** As a fire department manager, I want to query fire case statistics through chat, so that I can quickly access insights during meetings and discussions.

#### Acceptance Criteria

1. WHEN a statistics request is sent to `/api/v1/chat/stats`, THE Chat_API_Layer SHALL retrieve aggregated statistics from Neo4j
2. WHEN statistics type is specified, THE Chat_API_Layer SHALL return relevant metrics (total cases, event types, hazard distribution)
3. WHEN time range is specified, THE Chat_API_Layer SHALL filter statistics by the specified period
4. WHEN statistics are retrieved, THE Chat_API_Layer SHALL format them in chat-friendly format with clear labels
5. THE Chat_API_Layer SHALL support statistics for: total fire events, hazard types, consequence types, event chain patterns
6. WHEN no data exists for the requested period, THE Chat_API_Layer SHALL return message indicating no data available

### Requirement 6: API Authentication and Security

**User Story:** As a system administrator, I want API access to be secured with authentication, so that only authorized chat platforms can access Fire-Eye data.

#### Acceptance Criteria

1. WHEN the Fire-Eye backend initializes, THE Chat_API_Layer SHALL load API keys from secure configuration
2. WHEN an API request includes an API key in header, THE Chat_API_Layer SHALL validate the key against stored keys
3. WHEN API key validation fails, THE Chat_API_Layer SHALL reject the request with 401 Unauthorized status
4. WHEN API key validation succeeds, THE Chat_API_Layer SHALL allow the request to proceed
5. THE Chat_API_Layer SHALL support multiple API keys for different chat platforms
6. WHEN API keys are stored, THE Chat_API_Layer SHALL use secure storage mechanism (environment variables or encrypted config)
7. THE Chat_API_Layer SHALL log all authentication attempts for security auditing

### Requirement 7: AstrBot Plugin Core Structure

**User Story:** As a developer, I want the AstrBot plugin to have clear structure and organization, so that it is easy to maintain and extend.

#### Acceptance Criteria

1. WHEN the Fire-Eye_Plugin is loaded by AstrBot, THE plugin SHALL register all command handlers
2. THE Fire-Eye_Plugin SHALL maintain separate modules for: command handling, API communication, message formatting, configuration
3. WHEN the plugin initializes, THE Fire-Eye_Plugin SHALL load configuration from plugin config file
4. WHEN configuration is missing or invalid, THE Fire-Eye_Plugin SHALL log error and fail gracefully
5. THE Fire-Eye_Plugin SHALL follow AstrBot plugin development standards and conventions
6. THE Fire-Eye_Plugin SHALL include metadata file with plugin information (name, version, author, description)

### Requirement 8: Command Handlers and Intent Detection

**User Story:** As a firefighter, I want to use simple commands in chat to interact with Fire-Eye system, so that I can access features without remembering complex syntax.

#### Acceptance Criteria

1. WHEN user sends `/火瞳查询 <query>`, THE Command_Handler SHALL extract the query text and send it to query endpoint
2. WHEN user sends `/火瞳上传`, THE Command_Handler SHALL provide instructions for document upload
3. WHEN user sends `/火瞳统计 [type]`, THE Command_Handler SHALL request statistics of specified type
4. WHEN user sends `/火瞳帮助`, THE Command_Handler SHALL return help message listing all available commands
5. WHEN command syntax is invalid, THE Command_Handler SHALL return error message with correct syntax example
6. THE Command_Handler SHALL support command aliases for convenience (e.g., `/ht查询` as alias for `/火瞳查询`)
7. WHEN command processing fails, THE Command_Handler SHALL return user-friendly error message
8. **[NEW] (Optional - Intent Detection Mode) WHEN user sends natural language without slash command AND Intent Detection is enabled, THE Fire-Eye_Plugin SHALL use AstrBot's LLM Function Calling to detect fire investigation intent**
9. **[NEW] (Optional - Intent Detection Mode) WHEN intent is detected as fire case query (e.g., "帮我看下这个隐患"), THE Fire-Eye_Plugin SHALL automatically trigger the `analyze_fire_case` function without requiring explicit `/火瞳` command**
10. **[NEW] (Optional - Intent Detection Mode) THE Fire-Eye_Plugin SHALL provide configuration option `enable_intent_detection` (default: false) to control this behavior**
11. THE Command_Handler SHALL maintain `session_id` for each conversation to enable context-aware queries
12. **[NEW]** WHEN a new conversation starts, THE Command_Handler SHALL generate a unique `session_id` and associate it with the user's chat ID
13. **[NEW]** THE Command_Handler SHALL include `session_id` in all API requests to enable backend context tracking

### Requirement 9: API Client Communication and Async Task Polling

**User Story:** As a developer, I want the plugin to reliably communicate with Fire-Eye backend, so that users receive consistent responses.

#### Acceptance Criteria

1. WHEN API_Client sends request to Fire-Eye backend, THE API_Client SHALL include API key in request header
2. WHEN API request times out, THE API_Client SHALL retry up to 3 times with exponential backoff
3. WHEN all retries fail, THE API_Client SHALL return timeout error message to user
4. WHEN API returns error response, THE API_Client SHALL parse error details and return meaningful message
5. THE API_Client SHALL validate API responses against expected schema before processing
6. WHEN network connection fails, THE API_Client SHALL return connection error message
7. THE API_Client SHALL log all API requests and responses for debugging purposes
8. **WHEN async task is created (analyze/upload), THE API_Client SHALL start background polling coroutine**
9. **THE polling coroutine SHALL check task status every 3 seconds via `/api/v1/chat/status/{task_id}`**
10. **WHEN task status becomes `completed`, THE API_Client SHALL push final results to user proactively**
11. **WHEN task status becomes `failed`, THE API_Client SHALL notify user with error details**
12. **THE API_Client SHALL timeout polling after 5 minutes and notify user to check status manually**

### Requirement 10: Message Formatting for Chat Platforms

**User Story:** As a chat user, I want Fire-Eye responses to be well-formatted and readable in my chat application, so that I can easily understand the information.

#### Acceptance Criteria

1. WHEN query results are received, THE Message_Formatter SHALL format them with clear structure (headers, bullet points, numbering)
2. WHEN event chains are displayed, THE Message_Formatter SHALL show them in sequential order with relationship indicators
3. WHEN statistics are displayed, THE Message_Formatter SHALL use tables or structured lists for clarity
4. WHEN response exceeds platform message length limit, THE Message_Formatter SHALL split into multiple messages
5. THE Message_Formatter SHALL adapt formatting based on target platform capabilities (QQ, Telegram, etc.)
6. WHEN error messages are formatted, THE Message_Formatter SHALL use clear, non-technical language
7. WHEN formatting includes special characters, THE Message_Formatter SHALL escape them appropriately for the platform

### Requirement 11: Configuration Management

**User Story:** As a system administrator, I want to configure the plugin through configuration files, so that I can adjust settings without modifying code.

#### Acceptance Criteria

1. WHEN plugin starts, THE Fire-Eye_Plugin SHALL read configuration from `config.yaml` file
2. THE configuration file SHALL include: Fire-Eye backend URL, API key, timeout settings, retry settings
3. WHEN configuration value is missing, THE Fire-Eye_Plugin SHALL use sensible default value
4. WHEN configuration file is invalid YAML, THE Fire-Eye_Plugin SHALL log error with specific parsing issue
5. THE Fire-Eye_Plugin SHALL support environment variable overrides for sensitive values (API keys)
6. WHEN configuration is updated, THE Fire-Eye_Plugin SHALL support reload without full restart
7. THE configuration file SHALL include comments explaining each setting

### Requirement 12: Error Handling and User Feedback

**User Story:** As a chat user, I want to receive clear feedback when something goes wrong, so that I know what to do next.

#### Acceptance Criteria

1. WHEN API request fails, THE Fire-Eye_Plugin SHALL return error message indicating the problem category (network, authentication, server error)
2. WHEN user input is invalid, THE Fire-Eye_Plugin SHALL return message explaining what was wrong and how to fix it
3. WHEN processing takes longer than 5 seconds, THE Fire-Eye_Plugin SHALL send "processing" indicator to user
4. WHEN unexpected error occurs, THE Fire-Eye_Plugin SHALL log full error details and return generic error message to user
5. THE Fire-Eye_Plugin SHALL never expose internal system details (stack traces, database queries) to users
6. WHEN service is temporarily unavailable, THE Fire-Eye_Plugin SHALL return message suggesting to try again later

### Requirement 13: Logging and Monitoring

**User Story:** As a system administrator, I want comprehensive logging of plugin operations, so that I can troubleshoot issues and monitor usage.

#### Acceptance Criteria

1. WHEN plugin processes a command, THE Fire-Eye_Plugin SHALL log: timestamp, user ID, command type, execution time
2. WHEN API call is made, THE Fire-Eye_Plugin SHALL log: endpoint, request parameters (excluding sensitive data), response status
3. WHEN error occurs, THE Fire-Eye_Plugin SHALL log: error type, error message, stack trace, context information
4. THE Fire-Eye_Plugin SHALL support configurable log levels (DEBUG, INFO, WARNING, ERROR)
5. WHEN log file reaches size limit, THE Fire-Eye_Plugin SHALL rotate logs automatically
6. THE Fire-Eye_Plugin SHALL log to both file and console (configurable)
7. WHEN logging sensitive data, THE Fire-Eye_Plugin SHALL mask or redact it

### Requirement 14: Multi-Platform File Upload Support

**User Story:** As a user on different messaging platforms, I want consistent Fire-Eye functionality regardless of which platform I use, so that I have the same experience everywhere.

#### Acceptance Criteria

1. THE Fire-Eye_Plugin SHALL support QQ, Telegram, WeChat, DingTalk, and Feishu platforms
2. WHEN plugin runs on different platforms, THE core functionality SHALL remain identical
3. WHEN platform has specific limitations, THE Fire-Eye_Plugin SHALL adapt gracefully (message length, formatting)
4. **[MODIFIED]** WHEN file upload is supported by platform, THE Fire-Eye_Plugin SHALL first download the file from the IM platform's server to a local temporary directory
5. **[MODIFIED]** WHEN file is downloaded successfully, THE Fire-Eye_Plugin SHALL POST the file stream to Fire-Eye backend at `/api/v1/chat/upload` using `multipart/form-data` format (not just file path)
6. WHEN platform does not support file upload, THE Fire-Eye_Plugin SHALL provide alternative text-based document submission
7. THE Fire-Eye_Plugin SHALL detect platform type automatically through AstrBot context
8. **[NEW]** WHEN file download from IM platform fails, THE Fire-Eye_Plugin SHALL notify user with specific error and suggest alternative upload methods (e.g., paste text directly)
9. **[NEW]** THE Fire-Eye_Plugin SHALL clean up temporary files after successful upload or after 1 hour, whichever comes first
10. **[NEW]** WHEN file size exceeds platform limit during download, THE Fire-Eye_Plugin SHALL notify user before attempting download
11. **[NEW]** THE Fire-Eye_Plugin SHALL validate file type (PDF/TXT/DOCX) before uploading to backend to provide early feedback
12. **[NEW]** THE Fire-Eye_Plugin SHALL support configuration option `retain_files_on_server` (default: false). WHEN false, THE backend API SHALL verify that uploaded files are deleted from local storage immediately after graph extraction is complete to protect sensitive investigation data
13. **[NEW]** WHEN `retain_files_on_server` is true, THE backend SHALL store files securely with access controls and audit logging
14. **[NEW]** THE Chat_API_Layer SHALL log file deletion events for compliance and audit purposes

### Requirement 15: Performance and Scalability

**User Story:** As a system administrator, I want the integration to handle multiple concurrent users efficiently, so that response times remain acceptable under load.

#### Acceptance Criteria

1. WHEN multiple users send commands simultaneously, THE Fire-Eye_Plugin SHALL process them concurrently
2. WHEN API response time exceeds 10 seconds, THE Fire-Eye_Plugin SHALL timeout and return error message
3. THE Fire-Eye_Plugin SHALL implement connection pooling for API requests
4. WHEN processing large result sets, THE Chat_API_Layer SHALL implement pagination
5. THE Chat_API_Layer SHALL cache frequently requested statistics for 5 minutes
6. WHEN cache is available, THE Chat_API_Layer SHALL return cached results instead of querying database
7. **[MODIFIED]** THE Fire-Eye_Plugin SHALL implement a request queue. WHEN concurrent requests exceed 10, new requests SHALL be queued
8. **[NEW]** WHEN the queue size exceeds 50 (configurable via `max_queue_size`), new requests SHALL be rejected with "System Busy, please try again later" message to protect the backend
9. **[NEW]** WHEN a request is queued, THE Fire-Eye_Plugin SHALL notify the user with estimated wait time
10. **[NEW]** THE Fire-Eye_Plugin SHALL log queue metrics (current size, average wait time) for monitoring

### Requirement 16: Citation and Evidence Traceability

**User Story:** As a fire investigator, I need to know the source of each inference in the knowledge graph, so that I can trust the results and trace back to original documents.

#### Acceptance Criteria

1. WHEN providing a causal inference (e.g., "A 导致 B"), THE Chat_API_Layer SHALL include source document information if available
2. WHEN source document is available, THE response SHALL include: document name, page number (if applicable), confidence score
3. WHEN multiple sources support the same inference, THE Chat_API_Layer SHALL list all supporting sources
4. THE Message_Formatter SHALL display citations as footnotes (e.g., `[来源: 调查报告-2023.pdf, 第12页]`)
5. WHEN displaying event chains, THE Message_Formatter SHALL annotate each relationship with its confidence score
6. WHEN no source document is available, THE response SHALL indicate the inference is based on pattern matching or system rules
7. WHEN user queries about a specific relationship, THE Chat_API_Layer SHALL provide detailed provenance information
8. THE Chat_API_Layer SHALL store document metadata (filename, upload time, uploader) in graph nodes for traceability