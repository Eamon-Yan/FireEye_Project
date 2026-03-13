# 图表可视化问题 - 快速解决方案 / Graph Visualization Issue - Quick Solution

## 问题 / Problem

**用户报告：** 前端界面能正常打开，但是没有任何节点信息

**Translation:** Frontend opens normally but shows no node data

---

## 原因 / Root Cause

**数据库为空** - 系统是新安装的，还没有上传任何文档

**Translation:** Database is empty - system is newly installed with no documents uploaded yet

---

## 解决方案 / Solution

### 只需 3 步！/ Just 3 Steps!

#### 步骤 1️⃣ : 打开上传页面 / Open Upload Page

```
http://localhost:3000/upload
```

#### 步骤 2️⃣ : 上传测试文件 / Upload Test File

选择这个文件：
```
fire-eye-system/测试文档-火灾调查报告示例.txt
```

或者任何 PDF/TXT/DOCX 文件

#### 步骤 3️⃣ : 查看图表 / View Graph

等待分析完成后（30-60 秒），访问：
```
http://localhost:3000/graph
```

应该看到节点和关系！

---

## 验证 / Verification

在 Telegram 中测试：
```
/火瞳查询 火灾
```

应该返回查询结果。

---

## 如果还是不行 / If Still Not Working

### 运行诊断脚本 / Run Diagnostic Script

```bash
python diagnose_graph_issue.py
```

这会检查：
- ✓ Docker 容器状态
- ✓ Neo4j 连接
- ✓ 后端健康状态
- ✓ 数据库数据
- ✓ 前端配置

### 查看详细指南 / See Detailed Guide

- 诊断文档: `GRAPH_VISUALIZATION_ISSUE_DIAGNOSIS.md`
- 解决方案: `GRAPH_VISUALIZATION_SOLUTION_GUIDE.md`
- 系统状态: `CURRENT_SYSTEM_STATUS.md`

---

## 常见问题 / FAQ

**Q: 上传需要多长时间？**
A: 通常 30-60 秒

**Q: 支持哪些文件格式？**
A: PDF、TXT、DOCX，最大 50MB

**Q: 为什么没有数据？**
A: 需要先上传文件

**Q: 如何在 Telegram 中上传？**
A: 目前需要使用 Web 界面

---

## 快速链接 / Quick Links

| 功能 | 链接 |
|------|------|
| 上传文件 | http://localhost:3000/upload |
| 查看图表 | http://localhost:3000/graph |
| 后端 API | http://localhost:8000 |
| 诊断脚本 | `python diagnose_graph_issue.py` |

---

**就这么简单！** / **That's it!**

上传文件 → 等待分析 → 查看图表

Upload file → Wait for analysis → View graph

