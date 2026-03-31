# 使用官方 Node.js 18 镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制应用代码
COPY . .

# 构建应用
RUN npm run build
RUN cp -r .next/static .next/standalone/.next/static
RUN cp -r public .next/standalone/public

# 暴露端口
EXPOSE 3000

# 修复启动命令（不要用 npm start）
WORKDIR /app/.next/standalone
CMD ["node", "server.js"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# 启动命令
//CMD ["npm", "start"]
CMD ["node", ".next/standalone/server.js"]