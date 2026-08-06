# 第 4 章 · 工具

> 工具是 Agent 的双手：MCP 协议、感知/执行/协作三类工具、事件驱动异步 Agent

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter4.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | 感知工具 MCP：网络搜索、多模态理解、文件系统、公共数据源（DuckDuckGo/Open-Meteo/Yahoo/OpenStreetMap），大多无需 API Key |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | 对比原生多模态、提取为文本、工具化分析三种策略在保真度、成本和灵活性上的权衡 |
| 4-3 | [execution-tools](execution-tools/) | ✅ | 执行工具 MCP：20 次正式调用已通过 13/15 门禁，含 GitHub PR、Xvfb 桌面 Computer Use 与 KVM Android 实机操作；仅真实日历/邮件授权仍阻塞 |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | 协作工具 MCP：浏览器自动化、HITL、Email/Telegram/Slack/Discord 通知、定时器，支持管理员审批 |
| 4-5 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | FastAPI 事件驱动 Agent，原生异步集成前三组 MCP 工具，通过 HTTP API 接收 Web/IM/GitHub/定时器事件 |
| 4-6 | [async-agent](async-agent/) | ✅ | asyncio 单线程事件驱动框架 Flux：事件队列按紧急度分派、异步工具并行、运行中打断、长任务取消与状态查询 |
| 4-7 | [active-tool-discovery](active-tool-discovery/) | ✅ | Qwen3-4B 真实对照中两组均 3/3 完成、准确率均 100%（未证明准确率提升）；主动发现的 schema 暴露和实测用时显著更低，但轨迹仍含无关调用与过早结束 |
| — | [active-tool-selection](active-tool-selection/) | ✅ | 让 Agent 根据任务需求主动选择最合适的工具组合，而非被动接受预定义工具集 |

> 此外，[`chapter4/docker-compose.yml`](docker-compose.yml) 与 [`chapter4/DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md) 提供了将上述 MCP 工具服务器容器化部署的参考方案。

## 正式实验验收

真实运行、原始收据、哈希、逐项门禁与外部凭据阻塞项统一记录在 [EXPERIMENT_LEDGER.md](EXPERIMENT_LEDGER.md)。代码“可独立运行”不等于本机当前凭据已满足论文实验：4-1 至 4-5 的可执行核心均已通过真实运行，但授权私有数据、外部通知或真实邮箱门禁仍按证据诚实标为 blocked；不会用 mock 结果代替。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
