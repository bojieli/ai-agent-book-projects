# AndroidWorld T3A Evaluation Notes / AndroidWorld T3A 评估分析笔记

> Companion material for *AI Agents in Depth*, Chapter 6 — **Experiment 6-11: Evaluate and improve on AndroidWorld**.
> 配套《深入理解 AI Agent》第 6 章 **实验 6-11 ★★★：AndroidWorld 的评估和改进**。

← [Chapter 6 index / 返回第 6 章目录](../README.md) · 📖 [Read the chapter / 读本章正文](../../book/chapter6.md)（[EN](../../book-en/chapter6.md)）

---

## English

### What this directory is

This folder is **not** a copy of the [AndroidWorld](https://github.com/google-research/android_world) benchmark codebase. It contains **evaluation artifacts and analysis notes** for a **T3A** (Text-only / accessibility-tree style mobile agent) run plus a companion runner that executes the book's full **diagnose → hypothesize → experiment → decide → iterate** loop against a separate, unmodified upstream checkout.

| Path | Role |
| --- | --- |
| [`t3a_summary.md`](t3a_summary.md) | High-level report: per-task outcomes + capability-tag × difficulty matrix, strengths/weaknesses |
| [`t3a_failed_analysis.md`](t3a_failed_analysis.md) | Failure taxonomy with root-cause write-ups (transcription, complex UI, math/counting, etc.) |
| [`t3a.md`](t3a.md) | Full step traces for runs (including successes): per-step `Action` / `Reason` / `Summary` records |
| [`t3a_failed.md`](t3a_failed.md) | Step traces focused on failed tasks (useful for root-cause replay) |
| [`experiment_core.py`](experiment_core.py) | Evidence aggregation, success/cost decisions, strict completion gates, and five-stage report rendering |
| [`run_controlled_experiment.py`](run_controlled_experiment.py) | Real AndroidWorld control/treatment and candidate-rerun runner; no mock fallback |
| [`merge_candidate_shards.py`](merge_candidate_shards.py) | Strict merger for independent trial shards; rejects overlap, provenance drift, missing reference setup, and duplicate episodes |
| [`test_experiment.py`](test_experiment.py) | Offline checks for redaction, cost decisions, and non-overclaiming gates |
| [`requirements.txt`](requirements.txt) | Installs the adjacent upstream checkout plus the OpenAI-compatible API client |
| `validation/` | Machine-readable real-run evidence and the reports generated from it |

To execute the controlled loop, first clone and configure upstream AndroidWorld (see [Reproduce the benchmark](#reproduce-the-benchmark-optional) below). The large `t3a*.md` files remain reading/analysis inputs; the runner and `validation/` artifacts are the executable evidence layer.

### Background: AndroidWorld + T3A

- **AndroidWorld** evaluates agents that complete real tasks on Android apps (navigation, UI interaction, multi-app flows). Tasks are often **parameterized templates** (anti-contamination, diverse instances) and are scored by **final UI / environment state**, not by matching a fixed action sequence.
- The notes here analyze a **T3A** agent run (logged as `t3a_claude4_sonnet` in the summary tables): the agent plans from UI state (accessibility tree / similar structured observations) and issues discrete actions (`open_app`, `click`, `status`, …).

### Snapshot results (from the included report)

Numbers below come from [`t3a_summary.md`](t3a_summary.md) (116 tasks, one trial each; agent `t3a_claude4_sonnet`, run on 2025-07-02):

| Metric | Value (approx.) |
| --- | --- |
| Overall success rate | **~88%** |
| Fail rate | **~12%** |
| Mean episode length (successful) | **~13.5** steps |

**Where it succeeds:** structured, linear flows—camera/clock/contacts, file ops, Markor notes, many system toggles, multi-app and short-term memorization on easier tags.

**Where it fails (clustered):** SMS reply edge cases, Wi-Fi / combined connectivity, Tasks app queries, VLC playlists, and tasks needing **transcription**, **math/counting**, **complex UI understanding**, **information retrieval**, or **requires_setup**.

### Capability portrait

From the tag × difficulty matrix in the summary:

| Strengths | Critical weaknesses |
| --- | --- |
| `multi_app`, `memorization` (easy ~1.0) | `transcription` (~0.0) |
| Decent `search` on medium | `math_counting` (easy ~0.0) |
| Reliable on standard UI flows | `complex_ui_understanding`, `information_retrieval` (very low) |
| | `requires_setup` (easy ~0.0) |

**One-line portrait:** a strong “operator” on standard linear tasks; weak as a “thinker” when deep vision, counting, non-standard UI, or fragile multi-step state is required.

### Failure categories (see detailed analysis)

Condensed from [`t3a_failed_analysis.md`](t3a_failed_analysis.md):

1. **Transcription** — Navigates gallery/VLC correctly but cannot OCR image/video text; may invent plausible data and “fake success.”
2. **Complex UI** — Sees widgets but lacks a mental model of control logic (e.g. timer digit entry loops after detecting invalid `63s`).
3. **App first-run overhead** — Tutorials / permission wizards burn step budget before the real goal.
4. **Math / counting** — Can scroll and “see” list items but fails to filter + count or sum durations under step limits.
5. **Retrieval + planning** — Dense UIs (calendar grid), multi-delete with state tracking; inefficient recovery (day-by-day instead of reselecting).

Many failures surface as **max steps** (`Agent did not indicate task is done. Reached max number of steps.`)—symptom of loops, inefficient recovery, or missing perception, not merely “too few steps.”

### How to use this material (Experiment 6-11)

Follow the book’s five-step loop:

1. **Diagnose** — Cross the per-task table with the capability matrix; map surface failures to capability gaps.
2. **Hypothesize** — Layered ideas (surface → mid → deep), e.g. settings navigation hints, fix multimodal input pipe, add UI tree + screenshot, stronger vision model, conditional thinking for count tasks.
3. **Experiment** — Cheap ablations first; measure success **and** latency/cost side effects.
4. **Decide** — Deploy high ROI fixes; reject global “always think” if only a small tag set benefits.
5. **Iterate** — Re-run the suite; new residual failures become the next report.

### Executed controlled loop (2026-07-29 to 2026-08-04)

The companion runner now makes the book's loop executable while leaving the adjacent upstream checkout unmodified. It records the real AndroidWorld evaluator reward, explicit agent termination, actions, steps, wall time, LLM calls, token use, estimated token cost, exact model/runtime provenance, and the installed version of every required app after every episode. A bounded final analysis is requested from the same real configured LLM; the JSON evidence, not that prose, remains authoritative.

The first low-cost phase tested **H1**, a Wi-Fi navigation/state-verification guideline, against the untouched upstream T3A prompt. Its four matched task pairs completed with no runtime errors:

| Phase 1 result | Control | H1 treatment |
| --- | ---: | ---: |
| Successful episodes | 1 / 4 | 1 / 4 |
| Mean evaluator reward | 0.50 | 0.50 |
| Mean latency | 233.47 s | 156.98 s |
| Input + output tokens | 442,619 | 210,039 |

H1 reduced observed latency and token use but produced **no paired success gain**, so it was not promoted. See [phase-1 evidence](validation/paired_wifi_api35_20260729/evidence.json) and its [report](validation/paired_wifi_api35_20260729/report.md).

The residual traces exposed an API-35 observation issue: AndroidWorld's gRPC accessibility feed often returned only status-bar elements after opening the Internet panel, while an independent UIAutomator dump showed the full real Settings hierarchy. **H5** therefore tests a middle-layer input-pipeline change: upstream's `A11yMethod.UIAUTOMATOR` versus the gRPC forwarder, with the same base T3A prompt in both arms. This is an AndroidWorld-supported observation path selected from the companion runner, not an edit to upstream source.

H5 recovered the four-task slice from `1/4` control successes to `4/4` UIAutomator successes with no paired regression and a `0.788×` latency ratio. It was still restricted because its `2.498×` mean-token ratio exceeded the `1.5×` guardrail. The resulting cost-refinement hypothesis **H5C** keeps real UIAutomator observations/actions/evaluators but filters non-semantic container elements before T3A formats the prompt.

The completed H5C paired run preserved `4/4` successes in both arms. Compact UIAutomator used `70,557.5` mean tokens versus `139,439.5` for raw UIAutomator (`0.506×`) and `99.18s` versus `101.20s` mean latency (`0.980×`). It therefore passed the stricter H5C subset gate and became eligible only for a full-suite candidate rerun. At that stage it was **not** deployment approval and did not complete Experiment 6-11's 116-task × five-seed requirement. See the [H5C evidence](validation/paired_h5c_compact_api35_20260729/evidence.json) and [report](validation/paired_h5c_compact_api35_20260729/report.md).

The final reference-environment campaign subsequently completed all five gates: 580/580 unique episodes, 116 tasks × trials 1–5, zero runtime errors, official setup completed, and the same 24/24 required package versions on every Pixel 6/API-33 shard. The canonical [merged evidence](validation/candidate_h5c_api33_local_qwen_20260804/evidence.json) and [generated report](validation/candidate_h5c_api33_local_qwen_20260804/report.md) record:

| Full candidate result | Value |
| --- | ---: |
| Strict T3A successes | 26 / 580 (`4.4828%`) |
| Evaluator rewards | 77 full (`1.0`) + 1 partial (`0.5`) |
| Mean evaluator reward | `0.133621` |
| Mean steps / LLM calls | `9.672414` / `18.998276` |
| Mean latency | `109.860845s` |
| Mean tokens | `169,069.563793` |
| Total input / output tokens | `97,384,410` / `675,937` |
| Estimated API cost | `$0.00` (local inference) |

Strict success follows the upstream minimal-runner rule: the final evaluator state must equal `1.0` **and** the agent must explicitly declare completion. This is why the 26 strict successes are fewer than the 77 full-reward final states; one additional episode received partial reward `0.5`. Evaluator failures were retained as experimental outcomes; they were not rerun. The merged evidence sets `scope.direct_episode_gate_completed`, `scope.full_suite_completed`, `scope.manuscript_five_seed_gate_completed`, and `experiment_complete` to `true`, but `decision.deployment_approved` remains `false` because the observed result is poor and there is no valid full-suite control comparison.

The candidate used local `qwen2.5-7b-instruct-local` revision `a09a35458c702b33eeacc393d103063234e8bc28`, served by vLLM 0.19.0 on an NVIDIA RTX PRO 6000 Blackwell 96 GB. The H5C paired source used `doubao-seed-1-6-250615`. Consequently, this campaign completes the direct execution/evidence requirement for the promoted observation treatment, but it is **not** a same-model extension and establishes neither comparative uplift nor noninferiority.

The following compatibility treatments are explicitly part of the result boundary:

1. `ContactsNewContactDraft`: UIAutomator does not populate `state.forest`, so `state.ui_elements` is passed to the unchanged official contact predicate.
2. Clipper foreground race: the unchanged clipboard get/set operation is retried once after one second only for the exact documented foreground-access error.
3. `SimpleSmsReplyMostRecent`: the inbox is polled for five additional seconds; if emulator-console injection still leaves it empty, the exact last injected address/body is inserted into the same SMS SQLite database that upstream already clears, then the unchanged evaluator query runs.
4. `RetroPlayingQueue`: only the exact missing `playing_queue` table error from the pinned APK maps to an empty observed queue; the unchanged exact-queue predicate then records evaluator failure.
5. Native 32,768-token context overflow: only after a real provider context error, a deterministic retry retains at most 12,000 characters from the ends of the action-selection UI description or 6,000 from each before/after summary UI description. The goal, history, action, reason, guidance, output format, original retained UI indices, and per-episode truncation/removal counters remain intact. There were 63 such truncations, removing 7,390,498 UI-description characters in total.
6. Runtime-error retries reuse the exact parameters saved in the failed checkpoint, preventing upstream generator drift from changing the task. Completed checkpoints remain canonical when later parameter regeneration drifts, and resume on the same live emulator preserves the completed setup state rather than rerunning setup.

Phase 1 command (shown for reproducibility):

```bash
PYTHONDONTWRITEBYTECODE=1 GRPC_VERBOSITY=ERROR \
python run_controlled_experiment.py \
  --mode paired --hypothesis H1 \
  --tasks SystemWifiTurnOff,SystemWifiTurnOffVerify,SystemWifiTurnOn,SystemWifiTurnOnVerify \
  --trials 1 --seed 42 --model-seed 42 --max-steps 10 \
  --transition-pause 0.5 --skip-device-time \
  --output-dir validation/paired_wifi_api35_20260729
```

Phase 2 command:

```bash
PYTHONDONTWRITEBYTECODE=1 GRPC_VERBOSITY=ERROR \
python run_controlled_experiment.py \
  --mode paired --hypothesis H5 \
  --source-phase1-evidence validation/paired_wifi_api35_20260729/evidence.json \
  --tasks SystemWifiTurnOff,SystemWifiTurnOffVerify,SystemWifiTurnOn,SystemWifiTurnOnVerify \
  --trials 1 --seed 42 --model-seed 42 --max-steps 10 \
  --transition-pause 0.5 --skip-device-time \
  --output-dir validation/paired_h5_a11y_api35_20260729
```

Cost-refinement command:

```bash
PYTHONDONTWRITEBYTECODE=1 GRPC_VERBOSITY=ERROR \
python run_controlled_experiment.py \
  --mode paired --hypothesis H5C \
  --source-phase1-evidence validation/paired_wifi_api35_20260729/evidence.json \
  --source-phase2-evidence validation/paired_h5_a11y_api35_20260729/evidence.json \
  --tasks SystemWifiTurnOff,SystemWifiTurnOffVerify,SystemWifiTurnOn,SystemWifiTurnOnVerify \
  --trials 1 --seed 42 --model-seed 42 --max-steps 10 \
  --transition-pause 0.5 --skip-device-time \
  --output-dir validation/paired_h5c_compact_api35_REPRODUCE
```

The H1/H5 decision gate requires at least four complete pairs, a positive net success delta, no paired regression, and no more than `1.5×` mean latency or token use. H5C instead requires all four compact-treatment pairs to succeed, no regression, at most `1.5×` latency, and at most `0.75×` raw-UIAutomator tokens. Passing either gate permits only a **candidate rerun**, never deployment. Candidate reruns must supply the actual promoted paired-evidence file; a run ID string alone is insufficient. Full experiment completion additionally requires 580 direct candidate records: all 116 tasks × five distinct trial seeds, with no episode error.

For parallel reference-environment execution, keep `--trials 5` and assign one or more 1-based trials with `--trial-indices`; use a distinct `--execution-shard` label for every emulator. Each shard remains incomplete by itself. `merge_candidate_shards.py` accepts completion only when the shard union contains trials 1–5 exactly once for every task, with the same model, source decision, API-33 environment, completed upstream app setup, and identical required-app versions. Evaluator failures are direct results and are retained; only runtime-error records are eligible for `--resume --retry-errors`.

The historical paired slices used a Pixel 9 Pro API-35 AVD without the complete third-party app bundle; `--skip-device-time` was restricted to those time-independent Wi-Fi evaluators. The full candidate campaign instead uses five isolated Pixel 6/API-33 emulators, the completed upstream setup procedure, and the same 24 required app packages and versions on every shard. The evidence keeps those two environments separate rather than treating the reference-environment candidate run as a same-environment extension of the API-35 slice.

Concrete example trajectories for root-cause practice:

| Example task | File | Lesson |
| --- | --- | --- |
| `ExpenseAddMultipleFromGallery` | failed analysis + `t3a_failed.md` | OCR / multimodal gap; fabricated expenses |
| `ClockTimerEntry` | same | No durable UI model; repeats bad digit sequence |
| `MarkorTranscribeVideo` | same | Video navigation OK, content blind |
| `SportsTracker*Count*` / duration | same | Perception without arithmetic |
| Successful short flows (`CameraTakeVideo`, stopwatch) | `t3a.md` | What “good” step traces look like |

### Directory layout

```text
chapter6/android-world/
├── README.md                 # This file
├── experiment_core.py        # Evidence, decisions, completion gates, report renderer
├── run_controlled_experiment.py # Real AndroidWorld paired/candidate runner
├── merge_candidate_shards.py # Validates and merges parallel trial shards
├── test_experiment.py        # Focused offline integrity tests
├── requirements.txt          # Adjacent upstream + API client dependency
├── t3a_summary.md            # Aggregated metrics + capability matrix
├── t3a_failed_analysis.md    # Failure taxonomy & root causes
├── t3a.md                    # Full (large) run logs
├── t3a_failed.md             # Failed-task run logs
└── validation/               # Real evidence.json + generated report.md artifacts
```

### Reproduce the benchmark (optional)

The controlled runner expects a separate adjacent AndroidWorld checkout (the current workspace uses `chapter6/android_world`) plus its configured emulator and model credential. For a clean reproduction:

1. Clone [google-research/android_world](https://github.com/google-research/android_world) (or the fork your course materials specify).
2. Provide an Android emulator / device environment as required by that project.
3. Install the companion requirements in that environment, set the selected provider credential (the default is `ARK_API_KEY`), and run one of the commands above. For the retained local run, the OpenAI-compatible endpoint was `http://127.0.0.1:18111/v1` on the host (`http://host.docker.internal:18111/v1` from the emulator containers). Set `LOCAL_API_KEY` only in the launching process environment; the runner records only its variable name and never persists its value.
4. Provision the exact upstream Pixel 6 / API-33 apps before attempting `--full-suite`; do not use the API-35 Wi-Fi-only deviations for the full benchmark.

Run one trial per isolated emulator, changing `<N>`, ports, and output directory for shards 1–5:

```bash
python run_controlled_experiment.py \
  --android-world-checkout /workspace/android_world \
  --mode candidate-rerun --hypothesis H5C \
  --source-paired-evidence validation/paired_h5c_compact_api35_20260729/evidence.json \
  --full-suite --trials 5 --trial-indices <N> --execution-shard shard-<N>-of-5 \
  --seed 42 --model-seed 42 --max-steps 10 --transition-pause 0.5 \
  --provider local-vllm --model qwen2.5-7b-instruct-local \
  --base-url http://host.docker.internal:18111/v1 --api-key-env LOCAL_API_KEY \
  --max-model-tokens 1024 --model-timeout-s 90 --model-retries 2 \
  --model-source local_gpu \
  --model-revision a09a35458c702b33eeacc393d103063234e8bc28 \
  --model-runtime vllm-0.19.0 \
  --accelerator NVIDIA_RTX_PRO_6000_Blackwell_96GB \
  --perform-emulator-setup \
  --output-dir validation/candidate_h5c_api33_local_shard<N>
```

Merge only after all five shards have completed. The merger rejects overlap, missing trials, provenance/setup/app-version drift, runtime errors, and duplicate task/trial keys:

```bash
python merge_candidate_shards.py \
  validation/candidate_h5c_api33_local_shard{1,2,3,4,5}/evidence.json \
  --source-paired-evidence validation/paired_h5c_compact_api35_20260729/evidence.json \
  --output-dir validation/candidate_h5c_api33_local_qwen_20260804
```

Reading order if you only study the notes: **`t3a_summary.md` → `t3a_failed_analysis.md` → sample episodes in `t3a_failed.md` / `t3a.md`**.

### Related chapter projects

| Project | Relation |
| --- | --- |
| Upstream `android_world` (external) | Runnable benchmark environment |
| [model-benchmark](../model-benchmark/) | API latency / reliability dimensions of “evaluation” |
| [elo-leaderboard](../elo-leaderboard/) | Pairwise ranking instead of absolute task success |
| [public-health-reporting-eval](../public-health-reporting-eval/) | Another structured eval harness in-repo |

---

## 中文

### 本目录是什么

本目录**不是** [AndroidWorld](https://github.com/google-research/android_world) 基准的源码拷贝。它既包含 **T3A** 类移动 Agent 的**评估产物与分析笔记**，也包含一个连接独立、未修改上游 checkout 的配套 runner，用于真实执行书中的完整闭环：**诊断 → 假设 → 实验 → 决策 → 迭代**（对应**实验 6-11**）。

| 路径 | 作用 |
| --- | --- |
| [`t3a_summary.md`](t3a_summary.md) | 总览：逐任务结果 + 能力标签 × 难度矩阵、优势与短板 |
| [`t3a_failed_analysis.md`](t3a_failed_analysis.md) | 失败分类与根因（转录、复杂 UI、数学/计数等） |
| [`t3a.md`](t3a.md) | 完整逐步轨迹（含成功案例）：每步记录 `Action` / `Reason` / `Summary` |
| [`t3a_failed.md`](t3a_failed.md) | 失败任务轨迹（适合回放根因） |
| [`experiment_core.py`](experiment_core.py) | 证据聚合、成功/成本决策、严格完成门槛与五阶段报告渲染 |
| [`run_controlled_experiment.py`](run_controlled_experiment.py) | 真实 AndroidWorld 对照/处理与候选重跑 runner；没有 mock fallback |
| [`merge_candidate_shards.py`](merge_candidate_shards.py) | 严格合并独立 trial 分片，并拒绝重叠、来源漂移、缺少参考环境 setup 或重复 episode |
| [`test_experiment.py`](test_experiment.py) | 脱机检查脱敏、成本决策与防止夸大结论的门槛 |
| [`requirements.txt`](requirements.txt) | 安装相邻上游 checkout 与 OpenAI 兼容 API 客户端 |
| `validation/` | 真实运行的机器可读证据及据此生成的报告 |

若要**自己跑**基准，请按上游仓库克隆与配置（见下文[复现基准](#复现基准可选)）。本目录以**阅读与分析**为主。

### 背景：AndroidWorld 与 T3A

- **AndroidWorld**：在真实 Android 应用上评测 Agent 的导航、UI 交互与多应用任务。任务多为**参数化模板**（降低泄漏、增加多样性），按**最终 UI / 环境状态**判分，而不是比对固定操作序列。
- 笔记分析的是一次 **T3A** 运行（摘要表中记为 `t3a_claude4_sonnet`）：主要依据 UI 状态（无障碍树等结构化观察）规划，并输出离散动作（`open_app`、`click`、`status` 等）。

### 结果快照（来自随附报告）

数据摘自 [`t3a_summary.md`](t3a_summary.md)（116 个任务，每任务 1 次 trial；Agent 为 `t3a_claude4_sonnet`，运行于 2025-07-02）：

| 指标 | 约值 |
| --- | --- |
| 总体成功率 | **~88%** |
| 失败率 | **~12%** |
| 成功任务平均步数 | **~13.5** |

**擅长：** 结构化、线性流程——相机/时钟/联系人、文件操作、Markor 笔记、多数系统开关；在较简单标签上，跨应用与短时记忆表现好。

**短板（失败扎堆）：** 短信回复边缘、Wi-Fi/组合连接、Tasks 查询、VLC 播放列表，以及需要**转录**、**数学/计数**、**复杂 UI 理解**、**信息检索**、**requires_setup** 的任务。

### 能力画像

| 优势 | 关键短板 |
| --- | --- |
| `multi_app`、`memorization`（easy ~1.0） | `transcription`（~0.0） |
| `search` 在 medium 上较好 | `math_counting`（easy ~0.0） |
| 标准 UI 流程稳定 | `complex_ui_understanding`、`information_retrieval` 很低 |
| | `requires_setup`（easy ~0.0） |

**一句话：** 在标准线性任务上是高效的「操作手」；在深度视觉、计数、非标 UI、脆弱多步状态维护上，「思考者」能力明显不足。

### 失败类别（详见分析文）

浓缩自 [`t3a_failed_analysis.md`](t3a_failed_analysis.md)：

1. **转录失败** — 图库/VLC 导航正确，但无法 OCR 图/视频文字；可能捏造合理数据「假装成功」。
2. **复杂 UI** — 看得见控件，却没有控件逻辑的心智模型（如计时器输入，发现 `63s` 非法后仍重复错误序列）。
3. **应用首次启动开销** — 教程/权限向导吃掉步数预算。
4. **数学/计数** — 能滚动「看见」列表，却完不成筛选+计数或时长求和。
5. **检索与规划** — 密集日历格、去重删除的状态维护；恢复策略低效（逐天点而不是回月视图重选）。

大量失败以**步数耗尽**呈现（`Reached max number of steps`）——根因往往是循环、低效恢复或感知缺失，而不仅是「上限太小」。

### 如何使用（实验 6-11）

按书中五步闭环：

1. **诊断** — 交叉逐任务表与能力矩阵，把表面失败映射到能力缺陷。  
2. **假设** — 表层 → 中层 → 深层（如设置导航提示、修复多模态输入管道、截图+UI 树、更强视觉模型、仅对计数任务开思考）。  
3. **实验** — 先做低成本对照；同时量成功率与时延/成本副作用。  
4. **决策** — 优先部署高 ROI；拒绝为少数标签让全局任务承担数倍延迟/成本。  
5. **迭代** — 重跑全集，新失败模式成为下一轮起点。

### 已执行的对照闭环（2026-07-29 至 2026-08-04）

配套 runner 会逐 episode 记录真实 AndroidWorld evaluator reward、Agent 是否显式结束、动作、步数、耗时、LLM 调用、token、估算 token 成本、模型/运行时来源，以及每个必需 App 的安装版本。运行结束后，同一个真实配置模型会对聚合证据做受约束分析；JSON 证据始终是权威来源，LLM 文本不能覆盖它。

第一阶段测试低成本表层假设 **H1**：对照组使用原始 T3A prompt，处理组只增加 Wi-Fi 导航和最终状态确认指南。四个配对任务全部正常结束；两组均只成功 `1/4`，平均 evaluator reward 都是 `0.50`。处理组平均延迟由 `233.47s` 降至 `156.98s`，输入+输出 token 由 `442,619` 降至 `210,039`，但**没有配对成功增益**，因此不晋级。证据见 [phase-1 evidence](validation/paired_wifi_api35_20260729/evidence.json) 与 [report](validation/paired_wifi_api35_20260729/report.md)。

残余轨迹暴露了 API 35 观察兼容问题：打开 Internet 面板后，gRPC 无障碍树经常只剩状态栏元素，而独立 UIAutomator dump 能看到完整的真实 Settings 层级。因此第二阶段中层假设 **H5** 对比 gRPC forwarder 与 AndroidWorld 上游已有的 `A11yMethod.UIAUTOMATOR`，两组保持相同原始 T3A prompt、参数、seed、模型和 evaluator。H5 将该四任务切片从对照组 `1/4` 成功提升到 UIAutomator 的 `4/4`，但平均 token 比达到 `2.498×`，超过 `1.5×` 门槛，因此没有晋级。

随后执行的成本优化假设 **H5C** 对比原始 UIAutomator 与过滤非语义容器节点的紧凑 UIAutomator。两组都保持 `4/4` 成功；紧凑组平均 token 从 `139,439.5` 降至 `70,557.5`（`0.506×`），平均延迟从 `101.20s` 降至 `99.18s`（`0.980×`）。该结果通过了 H5C 的四任务候选门槛；在当时它仅表示可以在完整参考环境中进行候选重跑，尚不是部署批准，也尚未完成 116 任务 × 5 轮要求。证据见 [H5C JSON](validation/paired_h5c_compact_api35_20260729/evidence.json) 与 [报告](validation/paired_h5c_compact_api35_20260729/report.md)；英文部分列出了精确复现命令。

最终参考环境 campaign 已完成全部五项执行门槛：580/580 条唯一 episode（116 任务 × 1–5 轮）、零运行时错误、官方 setup 完成，且五个 Pixel 6/API-33 分片均安装相同版本的 24/24 个必需应用。权威结果见[合并 evidence](validation/candidate_h5c_api33_local_qwen_20260804/evidence.json)与[生成报告](validation/candidate_h5c_api33_local_qwen_20260804/report.md)：

| 完整候选结果 | 数值 |
| --- | ---: |
| 严格 T3A 成功 | 26 / 580（`4.4828%`） |
| Evaluator reward | 77 条满分（`1.0`）+ 1 条部分分（`0.5`） |
| 平均 evaluator reward | `0.133621` |
| 平均步数 / LLM 调用 | `9.672414` / `18.998276` |
| 平均延迟 | `109.860845s` |
| 平均 token | `169,069.563793` |
| 总输入 / 输出 token | `97,384,410` / `675,937` |
| 估算 API 成本 | `$0.00`（本地推理） |

严格成功遵循上游 minimal runner 规则：最终 evaluator 必须为 `1.0`，并且 Agent 必须显式宣告完成。因此 26 条严格成功少于 77 条 evaluator 满分的最终状态；另有 1 条部分 reward `0.5`。Evaluator 失败作为实验结果被完整保留，没有重跑。合并证据中 `scope.direct_episode_gate_completed`、`scope.full_suite_completed`、`scope.manuscript_five_seed_gate_completed` 与 `experiment_complete` 均为 `true`；但由于观测成绩很低，且没有有效的全集对照，`decision.deployment_approved` 仍为 `false`。

候选运行使用本地 `qwen2.5-7b-instruct-local`（revision `a09a35458c702b33eeacc393d103063234e8bc28`），由 NVIDIA RTX PRO 6000 Blackwell 96 GB 上的 vLLM 0.19.0 提供服务；H5C 配对源则使用 `doubao-seed-1-6-250615`。因此本 campaign 完成了已晋级观察方案的直接执行/证据要求，但**不是**同模型延续，不能证明比较提升或非劣性。

本结果包含以下明示的兼容处理边界：

1. `ContactsNewContactDraft`：UIAutomator 不填充 `state.forest`，因此把 `state.ui_elements` 传给未改动的官方联系人 predicate。
2. Clipper 前台竞态：仅对文档中精确的前台访问错误，在一秒后重试一次未改动的剪贴板读/写操作。
3. `SimpleSmsReplyMostRecent`：多轮询收件箱五秒；若 emulator console 注入后仍为空，将最后一次注入的精确地址/正文写入上游本就直接清理的同一 SMS SQLite 数据库，然后运行未改动的 evaluator query。
4. `RetroPlayingQueue`：仅将固定 APK 缺失 `playing_queue` 表的精确错误映射为空观察队列，再由未改动的精确队列 predicate 记录 evaluator 失败。
5. 原生 32,768-token 上下文溢出：仅在真实 provider context error 之后，确定性重试最多保留 action-selection UI 描述两端共 12,000 个字符，或 before/after summary UI 描述各 6,000 个字符；goal、history、action、reason、guidance、输出格式、保留 UI 的原索引与逐 episode 计数都保留。共发生 63 次截断，移除 7,390,498 个 UI 描述字符。
6. 运行时错误重试复用失败 checkpoint 中保存的精确参数，避免上游生成器漂移改变任务；若后续重生成参数发生漂移，已完成 checkpoint 仍为权威记录。同一存活 emulator 上 resume 时保留已完成的 setup 状态，不重复 setup。

H1/H5 决策门槛要求至少四个完整 pair、净成功增益为正、零配对退化，且平均延迟与 token 都不超过对照的 `1.5×`。H5C 则要求四个紧凑处理组全部成功、零退化、延迟不超过 `1.5×`、token 不超过原始 UIAutomator 的 `0.75×`。通过门槛只允许进入**候选重跑**，绝不等于部署。候选重跑必须提供真实晋级 pair 的 evidence 文件；仅提供 run ID 不够。实验完成还必须有 580 条直接候选记录，即 116 个任务 × 五个不同 trial seed，且没有 episode error。

若要在多个参考环境上并行执行，请保留 `--trials 5`，用 `--trial-indices` 分配一个或多个从 1 开始的 trial，并为每个 emulator 设置不同的 `--execution-shard`。单个分片本身永远不算完成。`merge_candidate_shards.py` 只有在 1–5 号 trial 对每个任务恰好出现一次，并且模型、晋级来源、API-33 环境、上游 App setup 完成状态与必需 App 版本一致时才接受合并。Evaluator 失败属于直接实验结果，必须保留；只有运行时 error 才可通过 `--resume --retry-errors` 重试。

历史配对切片运行在 Pixel 9 Pro API-35 AVD 上，缺少完整第三方 App bundle；`--skip-device-time` 仅用于这些与时间无关的 Wi-Fi evaluator。完整候选 campaign 则改用五个相互隔离的 Pixel 6/API-33 emulator，执行完整上游 setup，并在所有分片上保持相同的 24 个必需 App 包及版本。证据将两种环境明确分开，不把参考环境候选运行描述成 API-35 切片的同环境延伸。

适合精读的轨迹示例：

| 任务 | 材料 | 启示 |
| --- | --- | --- |
| `ExpenseAddMultipleFromGallery` | 失败分析 + `t3a_failed.md` | OCR/多模态缺口；伪造开销条目 |
| `ClockTimerEntry` | 同上 | 无稳定 UI 模型；重复错误输入 |
| `MarkorTranscribeVideo` | 同上 | 会播视频但「看不见」内容 |
| `SportsTracker*` 计数/时长 | 同上 | 有感知无算术 |
| 成功短流程（摄像、秒表等） | `t3a.md` | 对照「正常」轨迹长什么样 |

### 目录结构

```text
chapter6/android-world/
├── README.md                 # 本文件
├── experiment_core.py        # 证据、决策、完成门槛、报告渲染
├── run_controlled_experiment.py # 真实 AndroidWorld 配对/候选 runner
├── merge_candidate_shards.py # 校验并合并并行 trial 分片
├── test_experiment.py        # 聚焦的脱机完整性测试
├── requirements.txt          # 相邻上游 + API 客户端依赖
├── t3a_summary.md            # 汇总指标与能力矩阵
├── t3a_failed_analysis.md    # 失败分类与根因
├── t3a.md                    # 完整运行日志（体积大）
├── t3a_failed.md             # 失败任务日志
└── validation/               # 真实 evidence.json + 生成的 report.md
```

### 复现基准（可选）

配套 runner 需要一个独立的相邻 AndroidWorld checkout（当前工作区使用 `chapter6/android_world`）、已配置模拟器以及真实模型凭证。自行重跑请：

1. 克隆 [google-research/android_world](https://github.com/google-research/android_world)（或课程指定 fork）。  
2. 按上游文档准备模拟器/真机环境。  
3. 在对应环境中安装配套依赖，设置所选 provider 凭证（默认 `ARK_API_KEY`），运行英文部分给出的命令。本地保留运行在 host 使用 `http://127.0.0.1:18111/v1`，container 内使用 `http://host.docker.internal:18111/v1`；`LOCAL_API_KEY` 只设在启动进程环境中，runner 只记录变量名，不保存其值。
4. 只有在完整配置上游 Pixel 6 / API-33 App 后才能尝试 `--full-suite`；不要把 API-35 的 Wi-Fi 专用偏差用于完整 benchmark。

五分片的本地 GPU 命令与严格合并流程见英文复现节；每个隔离 emulator 运行一个 `--trial-indices`，全部完成后再调用 `merge_candidate_shards.py`。

仅做笔记研读的推荐顺序：**`t3a_summary.md` → `t3a_failed_analysis.md` → 抽读 `t3a_failed.md` / `t3a.md` 中的若干 episode**。

### 相关项目

| 项目 | 关系 |
| --- | --- |
| 上游 `android_world`（外部） | 可运行的评测环境 |
| [model-benchmark](../model-benchmark/) | API 时延/可用性维度的评测 |
| [elo-leaderboard](../elo-leaderboard/) | 成对比较式排行，而非绝对任务成功率 |
| [public-health-reporting-eval](../public-health-reporting-eval/) | 仓库内另一套结构化评测脚手架 |

---

## Notes / 说明

- Log files can be **very large** (`t3a.md` ~1MB+). Prefer summary + failed analysis first.  
- 日志文件体积很大，建议先读摘要与失败分析。  
- Project type: historical **reading / analysis notes** plus a runnable companion that requires a separately provisioned upstream AndroidWorld environment.
- 项目类型：历史**阅读/分析材料** + 可运行配套工具；后者依赖另行配置的上游 AndroidWorld 环境。
