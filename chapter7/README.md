# 第 7 章 · 模型后训练

> 预训练/SFT/RL 三阶段：何时选 SFT、何时选 RL，工具调用内化、样本效率

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter7.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 7-3, 7-4 | [MiniMind-pretrain](MiniMind-pretrain/) | 📖 | 从零预训练小型 LLM/VLM，理解完整预训练流程与关键技术 |
| 7-5 | [continued-pretraining](continued-pretraining/) | ✅ | 在特定领域数据上持续预训练，提升目标领域表现 |
| 7-6 | [sesame](sesame/) | ✅ | Sesame CSM 语音 SFT：LoRA 微调 1B TTS 模型，用 `<laugh>`、`<sigh>` 等副语言标记控制表达 |
| 7-6 | [orpheus](orpheus/) | ✅ | Orpheus 3B 语音 SFT：LoRA 微调 TTS 模型，拼接参考音频实现跨句音色一致的声音复刻 |
| 7-7 | [MultilingualReasoning](MultilingualReasoning/) | ✅ | 训练模型在多语言环境下的推理能力，提升跨语言任务表现 |
| 7-9 | [cot-distillation](cot-distillation/) | ✅ | 经 OpenRouter 调用 Claude 等前沿模型蒸馏 CoT 轨迹，规则验证器过滤后生成 SFT 数据（实验 7-9 配套） |
| 7-10 | [AdaptThink](AdaptThink/) | 📖 | 让推理模型按问题难度自适应选 Thinking/NoThinking，约束优化 + 重要性采样降成本 45–69% 同时提准确率 |
| 7-11 | `SFTvsRL/` | 📖 | 系统性对比监督微调与强化学习在不同任务上的效果与适用场景 |
| 7-12 | [SpatialReasoning](SpatialReasoning/) | 📖 | 训练模型的空间推理能力，处理位置、方向、距离等空间关系 |
| 7-13 | [SimpleVLA-RL](SimpleVLA-RL/) | 📖 | 视觉-语言-动作 RL，让模型理解视觉输入并执行相应动作 |
| 7-14 | [RLVP](RLVP/) | 📖 | 奖励结果、惩罚路径（RLVP）后训练研究（实验 7-14 配套）；完整训练/评估代码在独立论文仓库 `19PINE-AI/rlvp`，需自行克隆 |
| 7-15 | [retool](retool/) | 📖 | 多轮对话 + 代码沙箱提升数学推理，SFT→RL 两阶段；Qwen2.5-32B + AIME 2024 + DAPO + SandboxFusion |
| 7-16 | `AWorld/` · [AWorld-train](AWorld-train/) | 📖 | 基于 AWorld 框架训练具身 Agent，在虚拟环境中执行任务并从经验中学习 |
| — | `verl/` | 📖 | 为 LLM RLHF 设计的高效 RL 框架，支持 PPO/GRPO/DAPO 等 |
| — | [Intuitor](Intuitor/) | ✅ | 训练模型的直觉推理，快速做出合理判断而不依赖详细思考链 |
| — | `tinker-cookbook/` | 📖 | 收集各种模型训练的实用技巧与最佳实践 |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
