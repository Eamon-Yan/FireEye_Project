# 火瞳 QQ 插件 - 快速参考

## 🔧 配置信息

| 项目 | 值 |
|------|-----|
| **API URL** | `http://127.0.0.1:8000/api/v1` |
| **API Key** | `smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA` |
| **配置文件** | `astrbot-plugin-fireeye-qq/config.yaml` |
| **状态** | ✅ 正常运行 |

## 📝 QQ 命令

### 查询命令
```
/火瞳查询 <关键词>
/ht查询 <关键词>
```
**示例**: `/火瞳查询 火灾`

### 统计命令
```
/火瞳统计
/ht统计
```

### 帮助命令
```
/火瞳帮助
/ht帮助
```

## ✅ 功能状态

- ✅ 查询功能 - 支持多轮对话
- ✅ 统计功能 - 返回完整数据
- ✅ 帮助功能 - 显示所有命令
- ✅ 会话管理 - 30分钟自动过期
- ✅ 错误处理 - 友好提示
- ✅ 日志记录 - 详细日志

## 🚀 快速部署

```bash
# 1. 复制插件
cp -r astrbot-plugin-fireeye-qq /path/to/astrbot/plugins/

# 2. 安装依赖
pip install -r astrbot-plugin-fireeye-qq/requirements.txt

# 3. 重启 AstrBot
systemctl restart astrbot

# 4. 验证
# 在 QQ 中发送: /火瞳帮助
```

## 🔍 故障排查

### 问题: 查询失败
**解决**: 检查 API Key 是否正确
```bash
# 测试连接
curl -H "X-API-Key: smKlDXGrWLD9AzaT-ouPQjXUmQ9Zpfe3xBrcgwor3YA" \
  http://127.0.0.1:8000/api/v1/chat/health
```

### 问题: 连接超时
**解决**: 确认后端运行在 `127.0.0.1:8000`（不是 `localhost`）

### 问题: 无法找到插件
**解决**: 重启 AstrBot 并检查日志

## 📊 测试结果

| 测试项 | 结果 |
|--------|------|
| 基本查询 | ✅ 通过 |
| 统计功能 | ✅ 通过 |
| 多轮对话 | ✅ 通过 |
| 不同查询 | ✅ 通过 |

## 📁 关键文件

```
astrbot-plugin-fireeye-qq/
├── config.yaml              # ⭐ 配置文件（已修复）
├── main.py                  # 插件主入口
├── api/client.py            # API 客户端
├── session/manager.py       # 会话管理
├── queue/request_queue.py   # 请求队列
├── utils/formatter.py       # 消息格式化
└── README.md                # 文档
```

## 🎯 使用示例

### 查询示例
```
用户: /火瞳查询 火灾
机器人: 🔍 查询: 火灾

找到 3 条结果:

1. [FireEvent] 电气线路老化
   电线老化

2. [FireEvent] 电气短路
   短路打火

3. [FireEvent] 火灾蔓延
   火势蔓延

💬 会话ID: sess_5f2d94abd51b...
```

### 统计示例
```
用户: /火瞳统计
机器人: 📊 火瞳系统统计信息

📈 数据概览:
• 事件总数: 8
• 实体总数: 8
• 关系总数: 7

📊 节点类型:
• FireEvent: 4
• Hazard: 2
• Consequence: 2
```

## 📞 支持

- 📖 完整文档: `QQ_PLUGIN_SETUP_GUIDE.md`
- 🐛 问题修复: `QQ_PLUGIN_FIXED.md`
- 📋 规格说明: `.kiro/specs/astrbot-plugin-fireeye-qq/`

---

**最后更新**: 2026-03-25  
**版本**: 1.0.0  
**状态**: ✅ 生产就绪
