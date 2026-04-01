# 使用官方 Node.js 18 镜像
FROM node:18-alpine

# 设置工作目录
WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制应用代码
COPY . .

# 构建应用
RUN npm run build
RUN cp -r .next/static .next/standalone/.next/static

# 切换到 standalone 运行目录
WORKDIR /app/.next/standalone

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1:3000 || exit 1

# standalone 模式必须直接运行生成的 server.js
CMD ["node", "server.js"]
