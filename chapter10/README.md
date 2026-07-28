# 第 10 章 · 多 Agent 协作

> 群体智能高于个体：协作框架、上下文共享/隔离、涌现的「Agent 社会」

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter10.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | 同一 Coding Agent 在需求澄清/实现/审查三阶段加载不同提示词与工具集，对话历史跨阶段共享，审查不通过可回退 |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | 共享上下文下的链式 handoff：多角色各有独立提示词与工具，通过 `transfer_to_agent` 自主切换 |
| 10-3 | [book-translation](book-translation/) | ✅ | 管理者模式拆分翻译给术语表/翻译/审校专职 Agent，Manager 只存索引、译文全落盘，上下文基本恒定 |
| 10-4 | `use-computer-while-calling/` | 📖 | 电话 Agent（Node.js）与浏览器 Agent（Python）经 WebSocket 直接通信无协调器并行协作；代码已独立为 [TalkAct](https://github.com/19PINE-AI/TalkAct)，本仓库不内置该目录（克隆命令见主 README 附录） |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | N 个同构子 Agent 并行搜索，命中即级联终止；消息总线/并行派发/实时监控/竞态处理均真实实现 |
| 10-7 | `generative_agents/` | 📖 | 斯坦福「AI 小镇」生成式智能体（实验 10-7 配套）；外部仓库 `joonspk-research/generative_agents`，需自行克隆（见主 README 附录） |
| 10-8 | [voice-werewolf](voice-werewolf/) | ✅ | 用多 Agent 狼人杀演示「上下文不共享」的信息权限：玩家私有上下文严格隔离，确定性法官投递信息并审计 |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
