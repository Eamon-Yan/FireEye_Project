# 前端节点显示问题 - 已修复 / Frontend Node Display Issue - FIXED

## 问题 / Problem

**症状：**
- ✅ 数据库中有节点
- ✅ 前端地址可以访问 (http://localhost:8080 或 5000)
- ❌ 但图表页面不显示任何节点

## 根本原因 / Root Cause

**GraphViewer.tsx 中硬编码了 API 地址！**

```typescript
// 错误的代码
const response = await fetch(
  `http://localhost:8000/api/v1/graph/query?...`  // ❌ 硬编码
)
```

当前端运行在 `http://localhost:8080` 或 `http://localhost:5000` 时，这个硬编码的地址不会改变，导致无法获取数据。

## 修复 / Fix

已修改 `fire-eye-system/frontend/src/components/GraphViewer.tsx`：

```typescript
// 修复后的代码
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const response = await fetch(
  `${apiUrl}/api/v1/graph/query?...`  // ✅ 使用环境变量
)
```

现在会使用 `.env.local` 中配置的 `NEXT_PUBLIC_API_URL`。

## 立即应用修复 / Apply Fix Now

### 步骤 1: 确保前端配置正确

编辑 `fire-eye-system/frontend/.env.local`：

```bash
# 如果前端在 8080
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > fire-eye-system/frontend/.env.local
echo "PORT=3001" >> fire-eye-system/frontend/.env.local

# 或者如果前端在 5000
echo "NEXT_PUBLIC_API_URL=http://localhost:5000" > fire-eye-system/frontend/.env.local
echo "PORT=3001" >> fire-eye-system/frontend/.env.local
```

### 步骤 2: 重启前端

```bash
# 如果用 Docker
docker restart fire-eye-frontend

# 如果手动启动
cd fire-eye-system/frontend
npm run dev
```

### 步骤 3: 清除浏览器缓存

- F12 打开开发者工具
- 右键点击刷新按钮
- 选择"清空缓存并硬性重新加载"

### 步骤 4: 访问图表页面

```
http://localhost:8080/graph
或
http://localhost:5000/graph
```

**现在应该能看到节点了！** 🎉

## 验证修复 / Verify Fix

### 检查 1: 浏览器控制台

1. F12 打开开发者工具
2. 切换到 "Console" 标签
3. 应该看不到错误信息
4. 应该看到数据被正确加载

### 检查 2: 网络请求

1. F12 打开开发者工具
2. 切换到 "Network" 标签
3. 刷新页面
4. 查看 `/api/v1/graph/query` 请求
5. 应该看到 200 状态码和数据

### 检查 3: 图表显示

访问图表页面，应该看到：
- ✓ 节点显示
- ✓ 关系显示
- ✓ 节点数 > 0
- ✓ 关系数 > 0

## 修改的文件 / Modified Files

- `fire-eye-system/frontend/src/components/GraphViewer.tsx` - 第 59-76 行

## 修改内容 / Changes

```diff
- const response = await fetch(
-   `http://localhost:8000/api/v1/graph/query?limit=100&include_relationships=true${
+ const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
+ const response = await fetch(
+   `${apiUrl}/api/v1/graph/query?limit=100&include_relationships=true${
```

## 为什么会这样？/ Why This Happened?

前端代码中硬编码了 API 地址，没有使用环境变量。这在开发时可能没问题，但当前端运行在不同的端口时就会出现问题。

## 最佳实践 / Best Practice

✅ **应该这样做：**
```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
```

❌ **不应该这样做：**
```typescript
const apiUrl = 'http://localhost:8000'  // 硬编码
```

## 相关配置 / Related Configuration

### 前端环境变量 (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8080
PORT=3001
```

### 后端环境变量 (.env)
```
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

## 总结 / Summary

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 看不到节点 | API 地址硬编码 | 使用环境变量 |
| 数据为空 | 前端无法连接后端 | 配置正确的 API 地址 |
| 刷新后还是看不到 | 浏览器缓存 | 清除缓存并硬性重新加载 |

---

**问题已修复！** ✅
**现在就重启前端并查看图表吧！** 🚀

