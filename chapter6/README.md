# 第 6 章 · Agent 的评估

> 把表现变成可比较信号：评估环境、指标、统计显著性、评估驱动选型

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter6.md)

逐实验的正文要求、直接证据与未完成边界见 [验收台账](EXPERIMENT_LEDGER.md)。

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 6-1 | [tau2-bench-eval](tau2-bench-eval/) | ✅ | 已在固定上游提交上完成 5 个 telecom 双控任务：4/5 通过；保存原始轨迹、成本、内容哈希及错选线路导致漏做流量加油的失败分析 |
| 6-2 | `tau2-bench/` | 📖 | 人工完成 τ²-bench 的分级任务并记录轨迹；它只是 6-2 要抽样的六类基准之一 |
| 6-2 | `terminal-bench/` | 📖 | 测试 Agent 在真实终端环境的端到端能力（编译/训练/部署），约 100 任务 + 执行框架 |
| 6-2 | `SWE-bench/` | 📖 | 评估 LLM 解决真实 GitHub 问题的能力，含 SWE-bench/Lite/Verified/Multimodal 多个版本 |
| 6-2 | `GAIA/` | 📖 | 评估下一代 LLM 的工具/搜索/自主能力，450+ 个答案明确的非平凡问题，分 3 级难度 |
| 6-2 | `OSWorld/` | 📖 | 评估 Agent 在完整 OS 环境执行复杂任务的能力：文件管理、应用操作、系统配置 |
| 6-2, 6-11 | `android_world/` | 📖 | 评估 Agent 在 Android 环境的应用导航、UI 交互与任务完成能力（外部基准仓库） |
| 6-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | 四档多维 Rubric 已在 60 用例 × 3 系统的 180/180 条真实评判记录上完整执行；[独立验收索引](user-memory-system-evaluation/results/full_6_3_structured_rubric_evidence.json)验证逐维理由/证据或边界案例及幻觉一票否决，状态为 `complete` |
| 6-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | 60 用例 × 3 系统共 180/180 条真实轨迹，零错误且原生币种定价完整；[验收结果](user-memory-system-evaluation/results/full_6_4_60_cases_costed.json)状态为 `complete` |
| 6-10 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | [全矩阵验收](user-memory-system-evaluation/results/full_6_9_60_case_matrix.json)完成 60 用例 × 24 单元（4 嵌入 × 3 reranker × 2 主模型）共 1,440/1,440 条真实轨迹，零错误、零未定价用量，检索/任务指标与交互分析完整；[独立验证器](user-memory-system-evaluation/validation/verify_full_matrix_20260731.py)复核通过（ALL CHECKS PASSED），后端替代方案如实记录于 [readiness 证据](user-memory-system-evaluation/results/full_matrix_backend_readiness_20260731.json) |
| 6-5 | [tts-quality-eval](tts-quality-eval/) | ✅ | [真实验收](tts-quality-eval/validation/mistral_multimodal_20260730/manifest.json)完成 OpenAI/Fish 两 provider × 四类语料的 8/8 双音频 Voxtral 四维评审；候选/参考音频逐项哈希，早期 Gemini/OpenRouter 失败证据仍保留 |
| 6-6 | [elo-leaderboard](elo-leaderboard/) | ✅ | [正式全量验收](elo-leaderboard/validation/runs/exp6-6-arena-20260731-v1/manifest.json)处理 1,799,991 条公开 Arena 记录（1,670,250 条盲选票、129 个模型），在线 Elo 与 Bradley-Terry 排名 Spearman 0.787、Top-20 重合 12/20；胜率矩阵、17 个月度快照、三张图与 D3 动画均由同一 manifest 哈希绑定并复核通过 |
| 6-7 | [model-action-threshold](model-action-threshold/) | ✅ | 同一中性 Coding Harness 下完成 GPT-5.6-sol / Claude Sonnet 5 × 三任务 × 三次重复的 18/18 单元实测；[manifest](model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json)零 API 错误并绑定完整轨迹与汇总哈希 |
| 6-8 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | 多轮 Agent 任务（客服退款）全链路成本拆解 + KV-cache 友好设计/上下文压缩的 A/B 节省量化 |
| 6-9 | [model-benchmark](model-benchmark/) | 🚧 | 完整 8K/32K/128K × 512/2048、限流爬坡、Agent 成本与 168 小时可用性 campaign 已实现；现有[验收清单](model-benchmark/results/manifest.json)只有真实 smoke/readiness，不能替代完整长期实验 |
| 6-11 | [android-world](android-world/) | 📖 | 本书对 T3A Agent 在 AndroidWorld 上的评估报告与失败分析笔记（实验 6-11 起点；非基准源码） |
| 6-12 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | 🚧 | 固定 OpenVLA + RoboTwin2 配置、上游版本与预检/证据门禁；完成需要真实 checkpoint、RoboTwin2 环境和 8-GPU 仿真评估 |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | 基于合成 DHIS2 风格汇总数据，客观评估公共卫生报告 Agent 的工具调用、计算准确性、证据引用与无依据声明 |

> 📖 表中带反引号的外部基准需自行克隆。[`android-world/`](android-world/)（连字符）是本仓库内的 **T3A 评估分析笔记**（见该目录 [README](android-world/README.md)），与外部 `android_world/` 基准源码不是同一路径。

## 实验 6-1 / 6-2 外部复现锚点

以下映射以[正文](../book/chapter6.md)为准。SHA 来自对应 checkout 的 `origin` 与 `HEAD`。其中 6-1 已保留五任务正式运行的[验收证据](tau2-bench-eval/validation/runs/exp6-1-openrouter-gpt41mini-telecom-20260802-v1/manifest.json)；其余行仍只核验来源、路径和入口，不代表相应实验完成。

| 实验 | 上游与本地路径 | 固定提交 | 正文对应入口 |
| :--: | --- | --- | --- |
| 6-1；6-2 的 τ²-bench 样本 | [`sierra-research/tau2-bench`](https://github.com/sierra-research/tau2-bench) → `chapter6/tau2-bench` | `8d005b0e5b9e4af0bc055886fa7f95fc86d1710e` | 正文要求重点观察新增的双控 telecom 领域：`tau2 run --domain telecom --agent-llm <model> --user-llm <model> --num-trials 1 --num-tasks 5` |
| 6-1 原始 τ-bench 对照（仅溯源） | [论文](https://arxiv.org/abs/2406.12045) · [`sierra-research/tau-bench`](https://github.com/sierra-research/tau-bench/tree/59a200c6d575d595120f1cb70fea53cef0632f6b)；**不承诺本地 checkout** | `59a200c6d575d595120f1cb70fea53cef0632f6b` | 该历史版本入口：`python run.py --agent-strategy tool-calling --env retail --model gpt-4o --model-provider openai --user-model gpt-4o --user-model-provider openai --user-strategy llm --max-concurrency 10` |
| 6-2 GAIA | [`gaia-benchmark/GAIA`](https://huggingface.co/datasets/gaia-benchmark/GAIA) → `chapter6/GAIA` | `682dd723ee1e1697e00360edccf2366dc8418dd9` | 从 `2023/validation/metadata.level1.parquet`、`metadata.level2.parquet`、`metadata.level3.parquet` 各选一题人工完成并核对答案 |
| 6-2 AndroidWorld | [`google-research/android_world`](https://github.com/google-research/android_world) → `chapter6/android_world` | `0e95d641e244504c22087cc29b013f3b2428a261` | `python minimal_task_runner.py --task=ContactsAddContact`（先按上游 README 配置 emulator） |
| 6-2 SWE-Bench Verified | [`SWE-bench/SWE-bench`](https://github.com/SWE-bench/SWE-bench) → `chapter6/SWE-bench` | `5cd4be9fb23971679cbbafe5a0ecade27cef99be` | 安装后先用 `python -m swebench.harness.run_evaluation --predictions_path gold --max_workers 1 --instance_ids sympy__sympy-20590 --run_id validate-gold` 验证 harness，再人工处理选定 Verified issue |
| 6-2 Terminal-Bench | [`laude-institute/terminal-bench`](https://github.com/laude-institute/terminal-bench) → `chapter6/terminal-bench` | `8384a179b1b8688f6ea5233a4d9d51218df1ac96` | 任务定义在 `tasks/`；若要核对 harness 参数，运行 `tb run --help` |
| 6-2 OSWorld-Verified | [`xlang-ai/OSWorld`](https://github.com/xlang-ai/OSWorld) → `chapter6/OSWorld` | `8365edc975efd0477a0d62444a5beed562ab5a7b` | `python quickstart.py --provider_name vmware --path_to_vm "path/to/your/vm.vmx"`；再从 Verified 任务中抽样人工完成 |

从仓库根目录取得同一版本：

```bash
git clone https://github.com/sierra-research/tau2-bench.git chapter6/tau2-bench && git -C chapter6/tau2-bench checkout --detach 8d005b0e5b9e4af0bc055886fa7f95fc86d1710e
git clone https://huggingface.co/datasets/gaia-benchmark/GAIA chapter6/GAIA && git -C chapter6/GAIA checkout --detach 682dd723ee1e1697e00360edccf2366dc8418dd9
git clone https://github.com/google-research/android_world.git chapter6/android_world && git -C chapter6/android_world checkout --detach 0e95d641e244504c22087cc29b013f3b2428a261
git clone https://github.com/SWE-bench/SWE-bench.git chapter6/SWE-bench && git -C chapter6/SWE-bench checkout --detach 5cd4be9fb23971679cbbafe5a0ecade27cef99be
git clone https://github.com/laude-institute/terminal-bench.git chapter6/terminal-bench && git -C chapter6/terminal-bench checkout --detach 8384a179b1b8688f6ea5233a4d9d51218df1ac96
git clone https://github.com/xlang-ai/OSWorld.git chapter6/OSWorld && git -C chapter6/OSWorld checkout --detach 8365edc975efd0477a0d62444a5beed562ab5a7b
```

原始 τ-bench 行只用于复核 6-1 的历史设计差异，不在本仓库的 checkout 清单中。其当前 README 已明确警告：该仓库的 airline/retail 任务版本过时，应使用后续的 [`tau2-bench`](https://github.com/sierra-research/tau2-bench)（现已继续演进为 τ³-bench）获取修订任务与新领域。因此，不应把历史 τ-bench 的 retail 命令当成当前 τ²/τ³-bench 的推荐运行入口。

实验 6-2 是**读者亲自执行并记录轨迹**，不是把六套 Agent harness 全跑一遍。各基准应分别挑选简单、中等、困难任务；记录任务 ID、环境版本、人工步骤、最终答案/状态与标准验证结果，不能把仓库能安装或 quickstart 能启动写成 6-2 已完成。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 已有实现，但实验范围或验收证据尚未满足正文全部要求 |
