# 第 1 章 · Agent 基础知识

> **Agent = LLM + 上下文 + 工具**；Harness 工程才是竞争力

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter1.md)

逐项正文验收、真实 API 状态与证据路径见
[EXPERIMENT_LEDGER.md](EXPERIMENT_LEDGER.md)。其中实验 1-1 的五臂正式运行已完成，
但“去掉 reasoning 必然退化”没有在该次运行中复现；实验 1-3 已按作者批准的多提供商
政策验收：官方 OpenAI 路径保留但仍受配额阻塞，阿里云百炼 qwen3.7-plus 的
Responses API（hosted web_search + code_interpreter）实测通过全部验收门。

## 如何阅读实验

正文用短 skeleton 解释控制流；实验目录承载完整 SDK 适配、日志和验收。无需逐行读完每个文件，建议按三层推进：

- **Starter**：先读目标、最小命令和验收条件，推荐从 [context](context/) 开始；
- **Builder**：沿 main.py 的入口追踪上下文、工具调用和消融变量，再看 [web-search-agent](web-search-agent/) 的多轮循环；
- **Maintainer**：最后阅读 tests/、证据 manifest、失败回退和 provider adapter。

首次阅读可跳过凭据加载、展示层和 provider 兼容代码；当你要复现实验数字时，再回到 [验收台账](EXPERIMENT_LEDGER.md)。

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | 系统性消融实验展示 Agent 上下文各组件的重要性；支持阿里云百炼直连 Qwen、SiliconFlow Qwen、字节 Doubao、月之暗面 Kimi 等多提供商 |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Kimi K3 模型即 Agent，具备基础深度搜索能力，能进行多轮搜索和信息整合 |
| 1-3 | [search-codegen](search-codegen/) | ✅ | 模型自主多轮搜索 + 服务端代码执行的 Deep Research 闭环，先澄清意图再执行；官方 GPT-5.6 路径保留，阿里云百炼 qwen3.7-plus（hosted web_search + code_interpreter）实测通过东盟首都距离与比特币技术分析全部验收门 |
| 1-4 | [image-gen-workflow](image-gen-workflow/) | ✅ | 具体/宽泛两类需求 × 工作流（kimi-k3 改写 + 通义万相）与原生（Gemini / GPT-Image 2）双路线真实对照：具体需求下原生更忠实（海报文案被改写节点丢进负面词），宽泛需求下改写的场景具象化带来想象力，但 GPT-Image 2 自己就能补观点——适配层被模型内化的实证 |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | 10,000 局 Q-learning + 100 局评估与官方 Kimi K3 第一局双臂实测已验收；[证据](learning-from-experience/validation/20260730_011704/evidence.json)记录 Kimi 17 步成功、零 fallback 及历史点估计差异 |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
