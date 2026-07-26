# 第 6 章 · Agent 的评估

> 把表现变成可比较信号：评估环境、指标、统计显著性、评估驱动选型

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter6.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 6-1, 6-2 | `tau2-bench/` | 📖 | 专注评估 Agent 使用工具进行复杂推理（计算、搜索、数据处理）的能力 |
| 6-2 | `terminal-bench/` | 📖 | 测试 Agent 在真实终端环境的端到端能力（编译/训练/部署），约 100 任务 + 执行框架 |
| 6-2 | `SWE-bench/` | 📖 | 评估 LLM 解决真实 GitHub 问题的能力，含 SWE-bench/Lite/Verified/Multimodal 多个版本 |
| 6-2 | `GAIA/` | 📖 | 评估下一代 LLM 的工具/搜索/自主能力，450+ 个答案明确的非平凡问题，分 3 级难度 |
| 6-2 | `OSWorld/` | 📖 | 评估 Agent 在完整 OS 环境执行复杂任务的能力：文件管理、应用操作、系统配置 |
| 6-2, 6-10 | `android_world/` | 📖 | 评估 Agent 在 Android 环境的应用导航、UI 交互与任务完成能力（外部基准仓库） |
| 6-5 | [tts-quality-eval](tts-quality-eval/) | ✅ | 多种 TTS 配置合成挑战文本，LLM-as-a-Judge 按 Rubric 逐维度打分，输出可复现对比表 |
| 6-6 | [elo-leaderboard](elo-leaderboard/) | ✅ | 基于 ELO 评分的 Agent 性能排行榜，通过对战比较相对能力 |
| 6-7 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | 多轮 Agent 任务（客服退款）全链路成本拆解 + KV-cache 友好设计/上下文压缩的 A/B 节省量化 |
| 6-8 | [model-benchmark](model-benchmark/) | ✅ | 对多家 OpenAI 兼容 API 横向压测 TTFT、p50/p95 延迟、吞吐与成功率，一条命令出对比表 |
| 6-10 | [android-world](android-world/) | 📖 | 本书对 T3A Agent 在 AndroidWorld 上的评估报告与失败分析笔记（实验 6-10 起点；非基准源码） |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | 基于合成 DHIS2 风格汇总数据，客观评估公共卫生报告 Agent 的工具调用、计算准确性、证据引用与无依据声明 |

> 📖 表中带反引号的外部基准需自行克隆。[`android-world/`](android-world/)（连字符）是本仓库内的 **T3A 评估分析笔记**（见该目录 [README](android-world/README.md)），与外部 `android_world/` 基准源码不是同一路径。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
