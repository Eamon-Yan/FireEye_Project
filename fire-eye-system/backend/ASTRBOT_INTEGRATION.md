# AstrBot 集成配置指南

## API 认证配置

Fire-Eye 系统为 AstrBot 插件提供了基于 API Key 的认证机制。

### 配置 API Keys

在 `.env` 文件中配置 `ASTRBOT_API_KEYS`：

```bash
# 单个 API Key
ASTRBOT_API_KEYS=your-secret-key-here

# 多个 API Keys（逗号分隔）
ASTRBOT_API_KEYS=key1,key2,key3
```

### 生成安全的 API Key

建议使用强随机字符串作为 API Key。可以使用以下方法生成：

**Python:**
```python
import secrets
api_key = secrets.token_urlsafe(32)
print(api_key)
```

**PowerShell:**
```powershell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

### 使用 API Key

在请求 Chat API 端点时，需要在 HTTP 头中包含 API Key：

```bash
curl -X GET "http://localhost:8000/api/v1/chat/health" \
  -H "X-API-Key: your-secret-key-here"
```

### 认证流程

1. **请求验证**: 所有 `/api/v1/chat/*` 端点都需要 API Key 认证
2. **Key 验证**: 系统会验证提供的 API Key 是否在配置的有效 Keys 列表中
3. **日志记录**: 所有认证尝试（成功/失败）都会被记录到日志中
4. **错误响应**: 无效或缺失的 API Key 会返回 401 Unauthorized 错误

### 开发模式

如果未配置 `ASTRBOT_API_KEYS`（空列表），系统会进入开发模式：
- 所有 API Key 都会被接受
- 会记录警告日志
- **仅用于开发环境，生产环境必须配置有效的 API Keys**

### 安全建议

1. ✅ 使用强随机字符串作为 API Key（至少 32 字符）
2. ✅ 为不同的 AstrBot 实例使用不同的 API Key
3. ✅ 定期轮换 API Keys
4. ✅ 不要在代码中硬编码 API Keys
5. ✅ 不要将 `.env` 文件提交到版本控制系统
6. ❌ 不要在生产环境使用示例 Keys（如 `dev-key-12345`）

### 故障排查

**问题: 收到 "API Key required" 错误**
- 确认请求头中包含 `X-API-Key`
- 检查 Key 的拼写和格式

**问题: 收到 "Invalid API Key" 错误**
- 确认 API Key 在 `.env` 文件的 `ASTRBOT_API_KEYS` 列表中
- 检查是否有多余的空格或特殊字符
- 重启后端服务以加载新的配置

**问题: 认证总是通过（开发模式）**
- 检查 `.env` 文件中是否配置了 `ASTRBOT_API_KEYS`
- 确认配置不是空字符串

### 测试认证

运行单元测试验证认证功能：

```bash
pytest tests/test_auth.py -v
```

### 相关文件

- 认证中间件: `app/api/auth.py`
- 配置文件: `app/core/config.py`
- 环境变量: `.env`
- 单元测试: `tests/test_auth.py`
