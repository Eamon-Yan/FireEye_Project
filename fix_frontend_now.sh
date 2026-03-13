#!/bin/bash
# 快速修复前端节点显示问题

echo "🔧 修复前端节点显示问题..."
echo ""

# 检查前端地址
read -p "前端运行在哪个端口? (8080/5000): " port
port=${port:-8080}

# 更新配置
echo "NEXT_PUBLIC_API_URL=http://localhost:$port" > fire-eye-system/frontend/.env.local
echo "PORT=3001" >> fire-eye-system/frontend/.env.local

echo "✓ 配置已更新"
echo ""
echo "重启前端:"
echo "  docker restart fire-eye-frontend"
echo ""
echo "然后清除浏览器缓存并访问:"
echo "  http://localhost:$port/graph"
