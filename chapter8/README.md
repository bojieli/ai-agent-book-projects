# 第 8 章 · Agent 的持续进化

> 从运行轨迹中获得可靠信号，把经验转化为可验证、可回滚的能力更新

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter8.md)

## 配套实验

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | 实验 8-1：用环境结果、过程规则和语言 Rubric 形成带证据的客服轨迹诊断 |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | 实验 8-2：比较成功、部分成功与失败轨迹，生成跨轨迹 Markdown 经验文档 |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | 实验 8-3：从失败轨迹生成最小 Prompt 补丁，并以边界集和保留集控制发布 |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | 实验 8-4：把浏览器轨迹编译为带状态谓词、经重置回放验证的工作流 |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | 实验 8-5：由重复故障触发重试/熔断代码补丁、回归、灰度与回滚 |
| 8-6 | [self-evolution-eval](self-evolution-eval/) | ✅ | 实验 8-6：用学习、迁移、规则变化和保持四阶段评估长期进化 |

以上实验都提供无需 API Key 的离线入口和单元测试；需要真实模型或浏览器的扩展路径在各项目 README 中另行说明。

## 补充案例

| 编号 | 项目 | 关系 |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | Prompt 蒸馏与参数化学习的跨章项目；训练方法归入第七章 |
| — | [self-evolving-tools](self-evolving-tools/) | Alita 式工具发现、封装与复用，是“将经验写成程序”的补充案例 |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **设计文档** | 仅包含架构与实现方案，可运行代码仍在完善中 |
