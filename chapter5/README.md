# 第 5 章 · Coding Agent 与代码生成

> 代码是「能创造新工具的工具」，生产级 Coding Agent 全景

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter5.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 5-1 | [code-for-math](code-for-math/) | ✅ | 同模型同题集对比「纯思维链」与「代码辅助」，后者用 sympy/numpy/scipy 在沙箱执行，准确率显著更高 |
| 5-2 | [code-for-logic](code-for-logic/) | ✅ | 把「骑士与无赖」转化为 CSP，用 `python-constraint` 定义约束并求解，对比自然语言推理与代码辅助 |
| 5-3 | [small-model-codified-rules](small-model-codified-rules/) | ✅ | τ-bench 航空客服对照实验：把退款规则从提示词搬进代码/工具后，小模型成功率与一致性大幅提升 |
| 5-4 | [paper-to-ppt](paper-to-ppt/) | ✅ | 把「做 PPT」重构为代码生成：Proposer 写 Slidev，Reviewer 真渲染成 PNG 用 Vision LLM 检查迭代 |
| 5-5 | [paper-to-video](paper-to-video/) | ✅ | 在「论文 → PPT」基础上生成讲解词、TTS 合成、ffmpeg 逐页同步成带旁白的讲解视频 |
| 5-6 | [video-edit](video-edit/) | ✅ | 一段多场景视频 + 一句自然语言需求，两步 Vision 定位剪出片段，Reviewer 抽帧核对不合格则迭代 |
| 5-7 | [adaptive-log-parser](adaptive-log-parser/) | ✅ | 遇到无法解析的新格式时不报错，交给代码 Agent 生成 `parse` 函数，测试通过后热更新进引擎，全程无人介入 |
| 5-8 | [log-diagnosis](log-diagnosis/) | ✅ | 诊断 Agent 读轨迹日志/架构文档/PRD，定位根因、生成回归测试、重放框架真实验证，并（mock）对接 GitHub |
| 5-9 | [dynamic-form](dynamic-form/) | ✅ | 信息不全时动态生成含级联逻辑的 HTML 表单让用户一次性补全，汇总 JSON 交回 Agent |
| 5-10 | [erp-agent](erp-agent/) | ✅ | 中文自然语言转 SQL 由 DB 执行，artifact 模式让 LLM 只生成 SQL 制品不搬运数据，省 token 又防错 |
| 5-11 | [conversational-ui](conversational-ui/) | ✅ | 自然语言提 UI 定制需求（颜色/字体/文案/布局），Agent 改 React 源码借 Vite HMR 即时生效 |
| 5-12 | [agent-creator](agent-creator/) | ✅ | 模板/从零双臂均已通过结构、编译、测试、真实 Kimi K3 任务和语义门禁；[正式对照](agent-creator/runs/exp5-12-kimi-k3-20260730-v1/comparison.json)完整结束。模板质量非劣且创建更高效，但正文预期的“质量与效率同时严格占优”未出现——这是已完成实验的诚实负结果，不是未完成状态 |

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 已有实现，但实验范围或验收证据尚未满足正文全部要求 |
