# 第 4 章 · 工具

> 工具是 Agent 的双手：MCP 协议、感知/执行/协作三类工具、事件驱动异步 Agent

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter4.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | 感知工具 MCP：网络搜索、多模态理解、文件系统、公共数据源（DuckDuckGo/Open-Meteo/Yahoo/OpenStreetMap），大多无需 API Key |
| 4-2 | [execution-tools](execution-tools/) | ✅ | 执行工具 MCP：文件操作、代码解释器、虚拟终端、外部系统集成，LLM 二次审批防误操作 |
| 4-3 | [collaboration-tools](collaboration-tools/) | ✅ | 协作工具 MCP：浏览器自动化、HITL、Email/Telegram/Slack/Discord 通知、定时器，支持管理员审批 |
| 4-4 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | FastAPI 事件驱动 Agent，原生异步集成前三组 MCP 工具，通过 HTTP API 接收 Web/IM/GitHub/定时器事件 |
| 4-5 | [async-agent](async-agent/) | ✅ | asyncio 单线程事件驱动框架 Flux：事件队列按紧急度分派、异步工具并行、运行中打断、长任务取消与状态查询 |
| 4-6 | [active-tool-discovery](active-tool-discovery/) | ✅ | 对比「全量注入 120+ 工具 schema」与「少量基础工具 + discover_tools 元工具按需检索」，省 token 防错选 |
| — | [active-tool-selection](active-tool-selection/) | ✅ | 让 Agent 根据任务需求主动选择最合适的工具组合，而非被动接受预定义工具集 |

> 此外，[`chapter4/docker-compose.yml`](docker-compose.yml) 与 [`chapter4/DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md) 提供了将上述 MCP 工具服务器容器化部署的参考方案。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
