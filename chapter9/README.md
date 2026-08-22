# 第 9 章 · Agent 的持续进化

> 从运行轨迹中获得可靠信号，把经验转化为可验证、可回滚的能力更新

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter9.md)

## 如何阅读实验

正文用 skeleton 说明验证、载体选择、候选发布/回滚和睡眠学习；项目代码按三层阅读：

- **Starter**：从 [trajectory-verifier](trajectory-verifier/) 运行离线样例，先看三层 verifier 和证据输出；
- **Builder**：再看 [self-modifying-agent](self-modifying-agent/) 的提案—回归—灰度—回滚循环，以及 [prompt-auto-optimization](prompt-auto-optimization/) 的最小 diff；
- **Maintainer**：检查安全可信根、边界/保留/安全集、版本淘汰和 validation/latest.json。首次可跳过 provider 与 UI 适配。

## 配套实验

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 9-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | 实验 9-1：28 条真实客服调用、8 次 Judge 调用与 8 条专家标注样本已通过验收；[证据](trajectory-verifier/validation/real_20260729T165247Z/evidence.json)同时记录关键违规稳定性主张未复现 |
| 9-2 | [gaia-experience](gaia-experience/) | ✅ | 实验 9-2：真实 GAIA 三组轨迹与知识文档对照已验收；[证据](gaia-experience/validation/real_20260729T164012Z/evidence.json)记录知识文档组仅 25%、两控制组均 50% 的负结果 |
| 9-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | 实验 9-3：真实任务 Agent、LLM Judge 与 Coding Agent 跑完初始/自动/人工三组完整保留集和边界集；原始回执与发布门槛已保存 |
| 9-4 | 正文对照实验 | 🚧 | 从用户反馈中进化“需求澄清 + Spec 确认”Skill；正文给出三臂 A/B 设计、指标和发布门槛，配套实现待补充 |
| 9-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | 实验 9-5：真实 ARK Agent + Chromium 在可重置本地消息站完成探索、独立验证、参数化回放、假成功对照与页面变化失效 |
| 9-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | 实验 9-6：真实 Coding Agent 从重复故障生成补丁，并与确定性提案、故意过宽的反例通过同一回归/灰度/回滚发布门；[证据](self-modifying-agent/validation/latest.json)保留接受与拒绝历史 |
| 9-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | 实验 9-7：用户纠正/点踩/事后审计触发“高风险调用确认门禁”提案，经 AST 静态检查、未完成任务回放和正常操作回放；确定性提案通过，真实 `gpt-4o-mini` 提案因检查失败被安全拒绝，整体验收通过 |
| 9-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | 实验 9-8：把整本书和源码交给 Hermes；它读完后选择一项改进，亲手修改自己，并把每次 Reviewer 的退回变成下一轮学习，直到通过 |
| 9-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | 实验 9-9：static、append-only、evolving 三臂 × 3 seeds × 14 任务共 126 次真实调用；[证据](self-evolution-eval/validation/latest.json)保留迁移、规则替换、保持与配对统计 |

带项目链接的实验都保留无需 API Key 的离线入口和单元测试用于预检。

## 补充案例

| 编号 | 项目 | 关系 |
| :--: | --- | --- |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | Prompt 蒸馏与参数化学习的跨章项目；训练方法归入第八章 |
| — | [self-evolving-tools](self-evolving-tools/) | Alita 式工具发现、封装与复用，是“将经验写成程序”的补充案例 |
| — | [ai-style-skill](ai-style-skill/) | 写作型 Skill 的补充实验：把“去 AI 味”反馈提炼为可检查规则；正文示例移至第二章，自动更新管道和验收数据保留在项目 README |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 已有实现，但真实数据、真实环境或纵向验收证据尚未完整 |
