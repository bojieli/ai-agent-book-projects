# 第 2 章 · 上下文工程

> 上下文决定能力上限：KV Cache、提示工程、Agent Skills、上下文压缩

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter2.md)

逐项正文验收条件、真实运行状态及规范证据路径见
[EXPERIMENT_LEDGER.md](EXPERIMENT_LEDGER.md)。项目“可运行”不代表历史数值已复现，
也不代表外部凭证阻塞的正式路径可以由本地 proxy 替代。

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 2-1 | [local_llm_serving](local_llm_serving/) | ✅ | 跨平台本地 LLM 部署，自动选 vLLM/Ollama 后端，展示 0.6B 小模型也能有出色工具调用 |
| 2-2, 2-7 | [attention_visualization](attention_visualization/) | ✅ | 可视化 LLM 完整 token 序列与注意力权重分布，理解模型如何处理上下文、推理与调用工具 |
| 2-3 | [kv-cache](kv-cache/) | ✅ | 探索不同上下文管理模式对 KV Cache 的影响，演示错误模式如何破坏缓存效率 |
| 2-4 | [prompt-engineering](prompt-engineering/) | ✅ | 扩展 Tau-Bench，量化语气风格、指令组织、工具描述等因素对任务完成率的影响 |
| 2-5 | [prompt-injection](prompt-injection/) | ✅ | 3 种攻击场景 × 4 种防御配置的对照实验，直观展示逐层叠加防御后注入成功率下降 |
| 2-6 | [agent-skills-ppt](agent-skills-ppt/) | ✅ | 固定 Anthropic 官方 PPTX Skill + 真实论文 PDF，运行时可为 Claude Code 或等价的 Kimi Code CLI（已实测通过：13 页演示文稿、4 张论文原图、完整渐进式披露轨迹），旧 python-pptx 同构 demo 不作为正文验收 |
| 2-8 | [system-hint](system-hint/) | ✅ | 研究系统提示对 Agent 行为的影响，探索如何通过优化系统提示提升性能 |
| 2-9 | [context-compression](context-compression/) | ✅ | 实现并对比摘要、关键信息提取、语义压缩等多种策略，保持能力的同时减少 token |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
