# 第 1 章 · Agent 基础知识

> **Agent = LLM + 上下文 + 工具**；Harness 工程才是竞争力

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter1.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | 系统性消融实验展示 Agent 上下文各组件的重要性；支持 SiliconFlow Qwen、字节 Doubao、月之暗面 Kimi 等多提供商 |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Kimi K3 模型即 Agent，具备基础深度搜索能力，能进行多轮搜索和信息整合 |
| 1-3 | [search-codegen](search-codegen/) | ✅ | GPT-5 原生工具集成，综合利用网络搜索与代码沙盒实现复杂分析 |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | 对比 Q-learning 与基于 LLM 的上下文学习，复现 Shunyu Yao 的 "The Second Half"：LLM 以 250–400 倍样本效率超越传统 RL |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
