# 文件上传功能状态 / File Upload Feature Status

## 更新时间 / Update Time
2026-02-18 05:48 UTC

## 当前状态 / Current Status

### ✅ 已完成 / Completed
1. **上传命令已添加** - `/火瞳上传` 命令显示在帮助信息中
2. **组件已初始化** - API客户端、文件处理器、会话管理器、任务轮询器
3. **插件正常加载** - 无错误，所有命令可用

### ⚠️ 技术限制 / Technical Limitations

由于 AstrBot API 的限制，`@filter.message()` 装饰器在当前版本中不可用。这意味着：

- ❌ 无法监听所有消息来检测文件
- ❌ 命令过滤器只能处理文本命令，无法访问文件附件
- ❌ Telegram 发送文件时，文件和命令在不同的事件中

**错误信息：**
```
AttributeError: module 'astrbot.api.event.filter' has no attribute 'message'
```

## 推荐解决方案 / Recommended Solutions

### 方案 1: 使用 Web 界面（推荐）✅

**最简单、最可靠的方式**

**地址：** http://localhost:3000/upload

**优点：**
- ✅ 已完全实现并测试
- ✅ 支持所有文件类型
- ✅ 实时进度显示
- ✅ 完整的错误处理
- ✅ 任务状态轮询
- ✅ 分析结果展示

**使用步骤：**
1. 打开浏览器访问 http://localhost:3000/upload
2. 点击"选择文件"或拖拽文件
3. 点击"上传"按钮
4. 等待分析完成（30-60秒）
5. 查看分析结果
6. 使用 `/火瞳查询` 命令查询提取的信息

### 方案 2: 两步上传流程（需要开发）

**实现思路：**
1. 用户发送 `/火瞳上传` 命令
2. 系统设置"等待文件"状态（使用会话管理器）
3. 用户直接发送文件（不带命令）
4. 系统检测到该用户有"等待文件"状态
5. 处理文件上传

**需要实现：**
- 会话状态管理（已有 SessionManager）
- 文件事件监听器（需要找到正确的 API）
- 状态超时处理（30秒后自动清除状态）

**挑战：**
- 需要找到监听文件事件的正确方法
- 可能需要升级 AstrBot 版本
- 或者使用 AstrBot 的其他 API

### 方案 3: 直接 API 调用（高级用户）

用户可以直接使用 curl 或其他工具调用后端 API：

```bash
# 上传文件
curl -X POST http://localhost:8000/api/v1/chat/upload \
  -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" \
  -F "file=@/path/to/file.txt" \
  -F "session_id=user123"

# 查询任务状态
curl -X GET http://localhost:8000/api/v1/chat/task/{task_id} \
  -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA"
```

## 当前可用功能 / Currently Available Features

### Telegram 命令 / Telegram Commands

1. **帮助命令** ✅
   ```
   /火瞳帮助 或 /ht帮助
   ```
   显示所有可用命令和使用说明

2. **查询命令** ✅
   ```
   /火瞳查询 <内容> 或 /ht查询 <内容>
   ```
   查询火灾事故信息

3. **统计命令** ✅
   ```
   /火瞳统计 或 /ht统计
   ```
   查看系统统计信息

4. **上传命令** ✅
   ```
   /火瞳上传 或 /ht上传
   ```
   显示上传说明和 Web 界面链接

### Web 界面功能 / Web UI Features

1. **文件上传** ✅
   - 支持 PDF、TXT、DOCX
   - 最大 10MB
   - 拖拽上传
   - 进度显示

2. **任务管理** ✅
   - 任务状态查询
   - 实时进度更新
   - 错误处理

3. **结果展示** ✅
   - 事件链列表
   - 节点和关系统计
   - 置信度显示

## 测试步骤 / Testing Steps

### 测试 Telegram 命令 / Test Telegram Commands

1. **测试帮助命令**
   ```
   /火瞳帮助
   ```
   应该看到 4 个命令，包括上传命令

2. **测试上传命令**
   ```
   /火瞳上传
   ```
   应该看到上传说明和 Web 界面链接

3. **测试查询命令**
   ```
   /火瞳查询 火灾
   ```
   应该返回查询结果

4. **测试统计命令**
   ```
   /火瞳统计
   ```
   应该显示系统统计信息

### 测试 Web 上传 / Test Web Upload

1. 打开浏览器访问: http://localhost:3000/upload
2. 选择测试文件: `fire-eye-system/测试文档-火灾调查报告示例.txt`
3. 点击上传
4. 等待分析完成
5. 查看结果
6. 在 Telegram 中使用 `/火瞳查询` 查询提取的信息

## 技术细节 / Technical Details

### 组件架构 / Component Architecture

```
Main (star.Star)
├── API Client (APIClient)
│   ├── api_url: http://fire-eye-backend:8000/api/v1
│   ├── api_key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA
│   └── timeout: 30s
├── File Handler (FileHandler)
│   ├── temp_dir: /tmp/fire-eye
│   ├── max_file_size: 10MB
│   └── supported_types: [.pdf, .txt, .docx]
├── Session Manager (SessionManager)
│   └── session_ttl: 1800s (30分钟)
└── Task Poller (TaskPoller)
    ├── poll_interval: 2s
    └── max_attempts: 60
```

### 文件上传流程 / File Upload Flow

```
1. 用户选择文件
   ↓
2. 验证文件类型和大小
   ↓
3. 下载文件到临时目录
   ↓
4. 上传到后端 API
   ↓
5. 获取任务 ID
   ↓
6. 轮询任务状态
   ↓
7. 显示分析结果
   ↓
8. 清理临时文件
```

### API 端点 / API Endpoints

1. **上传文件**
   ```
   POST /api/v1/chat/upload
   Headers: X-API-Key
   Body: multipart/form-data
     - file: 文件
     - session_id: 会话ID
   ```

2. **查询任务状态**
   ```
   GET /api/v1/chat/task/{task_id}
   Headers: X-API-Key
   ```

3. **查询信息**
   ```
   POST /api/v1/chat/query
   Headers: X-API-Key
   Body: {"query": "查询内容"}
   ```

4. **获取统计**
   ```
   GET /api/v1/chat/stats
   Headers: X-API-Key
   ```

## 未来改进 / Future Improvements

### 短期 / Short Term
1. ✅ 添加上传命令到帮助信息 - 已完成
2. ✅ 显示 Web 界面链接 - 已完成
3. 📝 优化上传说明文本
4. 📝 添加更多使用示例

### 中期 / Medium Term
1. 研究 AstrBot 的文件事件 API
2. 实现两步上传流程
3. 添加文件预览功能
4. 支持批量上传

### 长期 / Long Term
1. 升级到支持 `@filter.message()` 的 AstrBot 版本
2. 实现完全自动的文件检测
3. 添加文件类型自动识别
4. 支持更多文件格式（图片、视频等）

## 故障排除 / Troubleshooting

### 问题 1: 插件未加载
**症状：** 命令不响应
**解决：**
```bash
docker restart astrbot
docker logs astrbot | grep "Fire-Eye"
```

### 问题 2: Web 界面无法访问
**症状：** http://localhost:3000 无法打开
**解决：**
```bash
cd fire-eye-system
docker-compose ps
docker-compose up -d frontend
```

### 问题 3: 后端 API 错误
**症状：** 上传失败，返回 500 错误
**解决：**
```bash
docker logs fire-eye-backend --tail 50
docker restart fire-eye-backend
```

### 问题 4: 文件分析超时
**症状：** 任务一直显示"处理中"
**解决：**
- 检查文件大小（最大 10MB）
- 检查文件格式（PDF/TXT/DOCX）
- 查看后端日志
- 重新上传文件

## 文件位置 / File Locations

### 插件文件 / Plugin Files
- `astrbot-plugin-fireeye/main.py` - 主插件文件
- `astrbot-plugin-fireeye/api/client.py` - API 客户端
- `astrbot-plugin-fireeye/utils/file_handler.py` - 文件处理器
- `astrbot-plugin-fireeye/session/manager.py` - 会话管理器
- `astrbot-plugin-fireeye/api/polling.py` - 任务轮询器

### 容器内位置 / Container Locations
- `/AstrBot/data/plugins/astrbot-plugin-fireeye/` - 插件目录
- `/tmp/fire-eye/` - 临时文件目录

### Web 界面 / Web UI
- `fire-eye-system/frontend/src/app/upload/page.tsx` - 上传页面
- `fire-eye-system/frontend/src/components/FileUpload.tsx` - 上传组件

## 联系支持 / Contact Support

如果遇到问题，请：
1. 查看日志文件
2. 检查 Docker 容器状态
3. 尝试重启服务
4. 查看本文档的故障排除部分

---

**创建时间 / Created**: 2026-02-18 05:50 UTC
**状态 / Status**: ✅ 基本功能完成，Web 上传可用
**推荐方式 / Recommended**: 使用 Web 界面上传文件
