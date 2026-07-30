# 第 1 章 · Agent 基础知识

> **Agent = LLM + 上下文 + 工具**；Harness 工程才是竞争力

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter1.md)

逐项正文验收、真实 API 状态与证据路径见
[EXPERIMENT_LEDGER.md](EXPERIMENT_LEDGER.md)。其中实验 1-1 的五臂正式运行已完成，
但“去掉 reasoning 必然退化”没有在该次运行中复现；实验 1-3 则在推理前受官方配额阻塞。

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | 系统性消融实验展示 Agent 上下文各组件的重要性；支持 SiliconFlow Qwen、字节 Doubao、月之暗面 Kimi 等多提供商 |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Kimi K3 模型即 Agent，具备基础深度搜索能力，能进行多轮搜索和信息整合 |
| 1-3 | [search-codegen](search-codegen/) | 🚧 | GPT-5 官方 Responses API 的 hosted search + code interpreter 路径已完整实现，但两次官方实测均因 `insufficient_quota` 返回 429；OpenRouter 仅作接口诊断，不能替代正文验收 |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | 10,000 局 Q-learning + 100 局评估与官方 Kimi K3 第一局双臂实测已验收；[证据](learning-from-experience/validation/20260730_011704/evidence.json)记录 Kimi 17 步成功、零 fallback 及历史点估计差异 |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
