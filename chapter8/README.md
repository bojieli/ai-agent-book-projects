# 第 8 章 · Agent 的持续进化

> 从运行轨迹中获得可靠信号，把经验转化为可验证、可回滚的能力更新

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter8.md)

## 配套实验

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | 实验 8-1：28 条真实客服调用、8 次 Judge 调用与 8 条专家标注样本已通过验收；[证据](trajectory-verifier/validation/real_20260729T165247Z/evidence.json)同时记录关键违规稳定性主张未复现 |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | 实验 8-2：真实 GAIA 三组轨迹与知识文档对照已验收；[证据](gaia-experience/validation/real_20260729T164012Z/evidence.json)记录知识文档组仅 25%、两控制组均 50% 的负结果 |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | 实验 8-3：真实任务 Agent、LLM Judge 与 Coding Agent 跑完初始/自动/人工三组完整保留集和边界集；原始回执与发布门槛已保存 |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | 实验 8-4：真实 ARK Agent + Chromium 在可重置本地消息站完成探索、独立验证、参数化回放、假成功对照与页面变化失效 |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | 实验 8-5：真实 Coding Agent 从重复故障生成补丁，并与确定性候选、故意过宽的反例通过同一回归/灰度/回滚发布门；[证据](self-modifying-agent/validation/latest.json)保留接受与拒绝历史 |
| 8-6 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | 把整本书和源码交给 Hermes；它读完后选择一项改进，亲手修改自己，并把每次 Reviewer 的退回变成下一轮学习，直到通过 |
| 8-7 | [self-evolution-eval](self-evolution-eval/) | ✅ | 实验 8-7：static、append-only、evolving 三臂 × 3 seeds × 14 任务共 126 次真实调用；[证据](self-evolution-eval/validation/latest.json)保留迁移、规则替换、保持与配对统计 |
| 8-8 | [harness-safety-gate](harness-safety-gate/) | ✅ | 实验 8-8：用户纠正/点踩/事后审计触发"高风险调用确认门禁"候选，经 AST 静态检查、未完成任务回放和正常操作回放；确定性候选通过，真实 `gpt-4o-mini` 候选因检查失败被安全拒绝，整体验收通过 |
| 8-9 | [ai-style-skill](ai-style-skill/) | ✅ | 实验 8-9：20 条"AI 味"纠正反馈提炼为 8 条可检查写作规则并生成 Skill；真实 `gpt-4o-mini` 只能提交候选，模型外筛选与确定性回退后，未完成任务集检出 8/8、正常文本保留集误伤 0/8，21 条候选合并为 8 条；正文同时承接第 7 章弯引号 Skill→合成数据→参数化案例 |

以上实验都保留无需 API Key 的离线入口和单元测试用于预检；表中 ✅ 来自各目录保存的真实模型、真实轨迹或真实浏览器规范证据，不由离线机制演示代替。历史数值或定性主张未复现时，证据按负结果如实记录。

证据完整性边界：8-5、8-7 的 canonical evidence 与 `latest.json` 都有独立
SHA-256 sidecar，当前复算一致；8-4 对三个关键浏览器产物保存并核对了 hash。
8-1、8-2、8-3 的 `latest.json` 虽与各自真实 run 的 `evidence.json` 字节一致，
但没有顶层 evidence/source hash manifest，因此可审计强度低于 8-5、8-7，
不能把提交时存在的 JSON 等同于运行时源码已被固定。

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
| 🚧 | **进行中** | 已有实现，但真实数据、真实环境或纵向验收证据尚未完整 |
