# 第 5 章 · Coding Agent 与代码生成

> 代码是「能创造新工具的工具」，生产级 Coding Agent 全景

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter5.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 5-1 | [code-for-math](code-for-math/) | ✅ | 30 道 AIME 2024 同模型真实对照：代码臂全部调用沙箱（含 sympy/numpy/scipy），53.3% vs 纯 CoT 36.7%，但差异未达显著（p=0.125）；正式负结论与原始收据均保留 |
| 5-2 | [code-for-logic](code-for-logic/) | ✅ | 固定版本 K&K 数据集 84 题真实对照：代码臂 100% 调用 `python-constraint`，实测 39.3% vs 纯思考 75.0%，未达到正文预期的 90%；完整负结论如实保留 |
| 5-3 | [small-model-codified-rules](small-model-codified-rules/) | ✅ | 本地 Qwen3-4B 的 60×2 配对 τ-bench 风格活动：代码化规则臂 91.7% vs 控制组 95.0%（p=0.6875），未显著提升；服务端真值、checklist 和完整 120 条轨迹均已验证 |
| 5-4 | [paper-to-ppt](paper-to-ppt/) | ✅ | 固定真实论文 PDF 的 20 页双臂正式对照：三张原图均带页码/裁剪/变换/哈希来源；两组独立 Vision 均以 95 分通过，质量持平，但双 Agent 峰值上下文 24,186 vs 单 Agent 92,601（低 3.83×） |
| 5-5 | [paper-to-video](paper-to-video/) | ✅ | 12 页真实幻灯片逐页经 Kimi K3 生成讲解词、Qwen-VL-Max 对照像素审核、Fish Audio S1 合成；ffmpeg 成片 513.010 秒，最大页漂移 0.024 秒，全部真实收据与失败重试均保留 |
| 5-6 | [video-edit](video-edit/) | ✅ | 一段多场景视频 + 一句自然语言需求，两步 Vision 定位剪出片段，Reviewer 抽帧核对不合格则迭代 |
| 5-7 | [adaptive-log-parser](adaptive-log-parser/) | ✅ | 遇到无法解析的新格式时不报错，交给代码 Agent 生成 `parse` 函数，测试通过后热更新进引擎，全程无人介入 |
| 5-8 | [log-diagnosis](log-diagnosis/) | ✅ | 诊断 Agent 读真实 HTTP 轨迹/架构文档/PRD，定位根因、生成回归测试并在修复前后重放；正式活动通过官方 GitHub MCP 创建了真实 Issue（保留脱敏收据） |
| 5-9 | [dynamic-form](dynamic-form/) | ✅ | 信息不全时动态生成含级联逻辑的 HTML 表单让用户一次性补全，汇总 JSON 交回 Agent |
| 5-10 | [erp-agent](erp-agent/) | ✅ | 中文自然语言转 SQL 由 DB 执行，artifact 模式让 LLM 只生成 SQL 制品不搬运数据，省 token 又防错 |
| 5-11 | [conversational-ui](conversational-ui/) | ✅ | 自然语言提 UI 定制需求（颜色/字体/文案/布局），Agent 改 React 源码借 Vite HMR 即时生效 |
| 5-12 | [permission-embedded-data-objects](permission-embedded-data-objects/) | ✅ | 在 PostgreSQL 之上的权限内嵌对象存储：应用层代码可以动态生成，但每次读写仍由数据层强制执行权限、校验、引用完整性和受控后果反应 |
| 5-13 | [agent-creator](agent-creator/) | ✅ | 模板/从零双臂均已通过结构、编译、测试、真实 Kimi K3 任务和语义门禁；[正式对照](agent-creator/runs/exp5-12-kimi-k3-20260730-v1/comparison.json)完整结束。模板质量非劣且创建更高效，但正文预期的“质量与效率同时严格占优”未出现——这是已完成实验的诚实负结果，不是未完成状态 |

## 正式实验验收

逐项正文契约、正式运行状态、负结果与证据哈希统一记录在
[EXPERIMENT_LEDGER.md](EXPERIMENT_LEDGER.md)。机制演示、离线占位音频和 mock 外部写入
均不能替代正式证据。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 已有实现，但实验范围或验收证据尚未满足正文全部要求 |
