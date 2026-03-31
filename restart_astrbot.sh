#!/bin/bash
# 重启 AstrBot 容器以加载 QQ 插件

echo "🔄 正在重启 AstrBot 容器..."
echo ""

cd fire-eye-system

# 重启 AstrBot 容器
docker-compose restart astrbot

echo ""
echo "✅ AstrBot 已重启"
echo ""
echo "📝 后续步骤:"
echo "1. 等待 10-15 秒让 AstrBot 完全启动"
echo "2. 在 QQ 中发送: /火瞳帮助"
echo "3. 应该会看到帮助信息"
echo ""
echo "🔍 如果仍然不工作，查看日志:"
echo "   docker-compose logs -f astrbot"
