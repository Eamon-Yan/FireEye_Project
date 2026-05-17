<img width="260" height="88" alt="image" src="https://github.com/user-attachments/assets/daadaf22-c03a-40ad-af6d-35fca83bbc9b" /># 火瞳 (FireEye) —— 基于 LLM 与 neo4j 知识图谱的火灾智能分析系统

> **2026中国大学生计算机设计大赛（人工智能赛道）项目**
>
> 本项目采用 **SDD（Specification-Driven Development，规范驱动开发）** 模式，基于 **Kiro Spec** 规范与 **Vibe Coding** 工作流进行全栈高效率开发。

---

## 🚀 系统核心架构

本项目打破了传统消防系统孤立、滞后的信息弊端，通过“前沿大模型 + 结构化图谱 + 智能化 Agent”实现了火灾场景下的秒级研判与多端协同。

### 1. 核心技术栈
* **智能推理/图谱：** LLM (Large Language Models) + Neo4j 拓扑知识图谱
* **多端交互：** AstrBot (Agentic AI 助手生态)
* **开发方法论：** SDD (规范驱动开发) & Kiro Spec 业务逻辑抽象
* **基础设施：** Docker 容器化集群 + Linux 生产环境运维

### 2. 业务链路
数据采集输入 ➔ LLM 实体抽取与关系沉淀 ➔ 事件链校验 ➔ 术语归一化 ➔ Neo4j 图数据库存储 ➔ 导出复用 + AstrBot Agent 多端实时监控与自然语言交互。

---

## 🛠 规范驱动开发 (SDD) 实践

本项目深度践行了 AI 时代的全新开发范式：
* **架构先行：** 不盲目对 AI 灌输 Prompt，而是优先使用 **Kiro Spec** 定义严谨的业务边界、数据结构与底层契约。
* **精准规训：** 将编写好的静态 Spec 规范作为核心 Context 喂给 AI（如 Claude Code / DeepSeek），在受限的“规范沙盒”内进行高质量代码生成，大幅降低了 AI 幻觉，使复杂功能的编译一次通过率显著提升。

---

## 📦 部署与运维规范

项目目前已实现全链路容器化，具备工业级环境适应能力：

### 1. 容器化设计
项目基于 **Docker** 及 Docker Compose 进行微服务编排。为确保大模型组件与 Neo4j 在有限硬件资源下的高可用性，设计了严谨的存储卷（Volume）持久化挂载方案。

### 2. 生产环境调优
**内存优化：** 针对密集计算导致的 OOM 风险，在 Linux（Ubuntu/CentOS）宿主机上通过合理分配**虚拟内存（Swap 交换分区）**，结合 Xshell 实时监控，实现了低配服务器的平稳运行。
