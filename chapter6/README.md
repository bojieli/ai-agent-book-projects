# 第 6 章 · Agent 的评估

> 把表现变成可比较信号：评估环境、指标、统计显著性、评估驱动选型

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter6.md)

逐实验的正文要求、直接证据与未完成边界见 [验收台账](EXPERIMENT_LEDGER.md)。

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 6-1 | [tau2-bench-eval](tau2-bench-eval/) | ✅ | 已在固定上游提交上完成 5 个 telecom 双控任务：4/5 通过；保存原始轨迹、成本、内容哈希及错选线路导致漏做流量加油的失败分析 |
| 6-2 | [experiment-6-2-human-benchmark](experiment-6-2-human-benchmark/) | ✅ | Codex 作为人工操作员，预注册并完成 GAIA、AndroidWorld、SWE-bench Verified、τ²-bench、Terminal-Bench、OSWorld-Verified 各简单/中等/困难一题，共 18/18 个首轮正式结果：13 通过、5 失败；逐题保留任务、轨迹、官方评估及成败解释 |
| 6-2 | `terminal-bench/` | 📖 | Terminal-Bench 外部任务与执行框架；6-2 的三档人工操作结果与失败分析已收录于上行案例集 |
| 6-2 | `SWE-bench/` | 📖 | SWE-bench Verified 外部代码修复基准；6-2 的三档补丁轨迹与官方 harness 结果已收录于上行案例集 |
| 6-2 | `GAIA/` | 📖 | GAIA 外部数据集；6-2 的 Level 1/2/3 作答、核验与舍入失败边界已收录于上行案例集 |
| 6-2 | `OSWorld/` | 📖 | OSWorld-Verified 外部桌面环境；6-2 的三档 GUI 操作轨迹与官方结果已收录于上行案例集 |
| 6-2, 6-12 | `android_world/` | 📖 | 评估 Agent 在 Android 环境的应用导航、UI 交互与任务完成能力（外部基准仓库；6-2 的实际结果见上行） |
| 6-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | 四档多维 Rubric 已在 60 用例 × 3 系统的 180/180 条真实评判记录上完整执行；[独立验收索引](user-memory-system-evaluation/results/full_6_3_structured_rubric_evidence.json)验证逐维理由/证据或边界案例及幻觉一票否决，状态为 `complete` |
| 6-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | 60 用例 × 3 系统共 180/180 条真实轨迹，零错误且原生币种定价完整；[验收结果](user-memory-system-evaluation/results/full_6_4_60_cases_costed.json)状态为 `complete` |
| 6-5 | [user-memory-policy-eval](user-memory-policy-eval/) | ✅ | 已用真实 `openai/gpt-5.6-sol` 经 OpenRouter 完成 11 个 trajectory-prefix bad case × JSON/Markdown/Python-like 三种表示，共 33/33 个 API 单元、0 个 API 错误；三种表示均为 6/11 通过，结果和哈希保存在 `results/policy_prefix_live.json` 与 `results/manifest.json` |
| 6-6 | [tts-quality-eval](tts-quality-eval/) | ✅ | [真实验收](tts-quality-eval/validation/mistral_multimodal_20260730/manifest.json)完成 OpenAI/Fish 两 provider × 四类语料的 8/8 双音频 Voxtral 四维评审；候选/参考音频逐项哈希，早期 Gemini/OpenRouter 失败证据仍保留 |
| 6-7 | [elo-leaderboard](elo-leaderboard/) | ✅ | [正式全量验收](elo-leaderboard/validation/runs/exp6-6-arena-20260731-v1/manifest.json)处理 1,799,991 条公开 Arena 记录（1,670,250 条盲选票、129 个模型），在线 Elo 与 Bradley-Terry 排名 Spearman 0.787、Top-20 重合 12/20；胜率矩阵、17 个月度快照、三张图与 D3 动画均由同一 manifest 哈希绑定并复核通过 |
| 6-8 | [model-action-threshold](model-action-threshold/) | ✅ | 同一中性 Coding Harness 下完成 GPT-5.6-sol / Claude Sonnet 5 × 三任务 × 三次重复的 18/18 单元实测；[manifest](model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json)零 API 错误并绑定完整轨迹与汇总哈希 |
| 6-9 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | 多轮 Agent 任务（客服退款）全链路成本拆解 + KV-cache 友好设计/上下文压缩的 A/B 节省量化 |
| 6-10 | [model-benchmark](model-benchmark/) | 🚧 | 完整 8K/32K/128K × 512/2048、限流爬坡、Agent 成本与 168 小时可用性 campaign 已实现；现有[验收清单](model-benchmark/results/manifest.json)只有真实 smoke/readiness，不能替代完整长期实验 |
| 6-11 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | [全矩阵验收](user-memory-system-evaluation/results/full_6_11_60_case_matrix.json)完成 60 用例 × 24 单元（4 嵌入 × 3 reranker × 2 主模型）共 1,440/1,440 条真实轨迹，零错误、零未定价用量，检索/任务指标与交互分析完整；[独立验证器](user-memory-system-evaluation/validation/verify_full_matrix_20260731.py)复核通过（ALL CHECKS PASSED），后端替代方案如实记录于 [readiness 证据](user-memory-system-evaluation/results/full_matrix_backend_readiness_20260731.json) |
| 6-12 | [android-world](android-world/) | ✅ | [完整候选实验证据](android-world/validation/candidate_h5c_api33_local_qwen_20260804/evidence.json)保留 116 任务 × 5 轮的 580/580 条唯一 episode（包括评估失败），运行时错误为零：严格 T3A 成功 26 条（4.4828%），平均 evaluator reward 0.133621，由 77 条满分状态与 1 条 `0.5` 部分 reward 组成。实验在完成官方初始化且配齐 24/24 应用的 Pixel 6/API-33 上执行，本地 Qwen2.5-7B（revision `a09a35458c702b33eeacc393d103063234e8bc28`）通过 vLLM 0.19.0 运行于 RTX PRO 6000 Blackwell 96 GB。执行与证据已完成，但未批准部署；候选 Qwen 与配对源 Doubao 不同，因而不支持同模型提升或非劣性结论 |
| 6-13 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | ✅ | [正式单卡运行](openvla-robotwin2-eval/validation/runs/exp6-12-localgpu-20260803-v1/manifest.json)完成 chunk 1/25 各 128 IID + 128 OOD episodes，严格门禁及 512 个 rollout hash 全通过；chunk 1 为 0/256、chunk 25 为 26/256，低绝对成功率作为真实结果保留 |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | 基于合成 DHIS2 风格汇总数据，客观评估公共卫生报告 Agent 的工具调用、计算准确性、证据引用与无依据声明 |

> 📖 表中带反引号的外部基准需自行克隆。[`android-world/`](android-world/)（连字符）是本仓库内的 **T3A 评估分析笔记**（见该目录 [README](android-world/README.md)），与外部 `android_world/` 基准源码不是同一路径。

## 跨章 Bad Case 回归协议

正文新增的两类作用域/保真度 Bad Case 评估不把训练代码重复复制到第六章：第六章负责记录首个错误、片段作用域、逐层字符串哈希和轨迹前缀回归；第七章的 [`curly-quote-sft`](../chapter7/curly-quote-sft/) 与 [`exact-copy-sft`](../chapter7/exact-copy-sft/) 复用这些标签生成训练数据，并在独立边界集和保留集上回归。前者按中文自然语言、英文原文、代码和 JSON 作用域评分，后者按 byte/code-point/token exactness 和真实工具参数匹配评分。

## 实验 6-1 / 6-2 外部复现锚点

以下映射以[正文](../book/chapter6.md)为准。SHA 来自对应 checkout 的 `origin` 与 `HEAD`。6-1 已保留五任务正式运行的[验收证据](tau2-bench-eval/validation/runs/exp6-1-openrouter-gpt41mini-telecom-20260802-v1/manifest.json)；6-2 的 18 个分级人工操作案例、正式结果与兼容边界见[独立报告](experiment-6-2-human-benchmark/README.md)。下表继续保留复现来源、路径和入口。

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

实验 6-2 是**操作员亲自执行并记录轨迹**，不是把六套 Agent harness 全跑一遍。本仓库的[已完成案例集](experiment-6-2-human-benchmark/)由 Codex 明确署名为人工操作员，并分别记录每个基准的简单、中等、困难任务 ID、环境版本、步骤、最终答案/状态与标准验证结果；失败案例未在评估后修改或重跑。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 已有实现，但实验范围或验收证据尚未满足正文全部要求 |
