# 火瞳系统 (Fire Eye System)

基于Neo4j和大语言模型(LLM)的火灾事理图谱Web系统

## 项目概述

火瞳系统通过智能抽取火灾调查报告中的因果关系，构建高质量的事理图谱，并提供场景演化预测功能，支持火灾预防和应急决策。

## 技术栈

- **后端**: Python 3.11 + FastAPI + Pydantic
- **前端**: React 18 + Next.js 14 + TypeScript + Tailwind CSS
- **数据库**: Neo4j 5.x + Redis 7.x
- **可视化**: ECharts + react-force-graph
- **部署**: Docker + Docker Compose

## 项目结构

```
fire-eye-system/
├── backend/                 # Python FastAPI 后端
├── frontend/               # React Next.js 前端
├── docker-compose.yml      # 服务编排
├── .env.example           # 环境变量模板
└── README.md              # 项目说明
```

## 快速开始

1. 克隆项目并安装依赖
2. 配置环境变量
3. 启动服务：`docker-compose up -d`
4. 访问前端：http://localhost:3000

## 核心功能

- 🔍 智能抽取层：LLM驱动的文档解析和事件链抽取
- ✅ 校验对齐层：术语归一化和逻辑校验
- 🗄️ 图谱存储：Neo4j高性能图数据库
- 🎯 场景预测：路径游走和剧本生成