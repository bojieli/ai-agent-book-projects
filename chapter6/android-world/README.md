# AndroidWorld T3A Evaluation Notes / AndroidWorld T3A 评估分析笔记

> Companion material for *AI Agents in Depth*, Chapter 6 — **Experiment 6-10: Evaluate and improve on AndroidWorld**.  
> 配套《深入理解 AI Agent》第 6 章 **实验 6-10 ★★★：AndroidWorld 的评估和改进**。

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

### How to use this material (Experiment 6-10)

Follow the book’s five-step loop:

1. **Diagnose** — Cross the per-task table with the capability matrix; map surface failures to capability gaps.
2. **Hypothesize** — Layered ideas (surface → mid → deep), e.g. settings navigation hints, fix multimodal input pipe, add UI tree + screenshot, stronger vision model, conditional thinking for count tasks.
3. **Experiment** — Cheap ablations first; measure success **and** latency/cost side effects.
4. **Decide** — Deploy high ROI fixes; reject global “always think” if only a small tag set benefits.
5. **Iterate** — Re-run the suite; new residual failures become the next report.

### Executed controlled loop (2026-07-29)

The companion runner now makes the book's loop executable while leaving the adjacent upstream checkout unmodified. It records the real AndroidWorld evaluator reward, explicit agent termination, actions, steps, wall time, LLM calls, and token use after every episode. A bounded final analysis is requested from the same real configured LLM; the JSON evidence, not that prose, remains authoritative.

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

The completed H5C paired run preserved `4/4` successes in both arms. Compact UIAutomator used `70,557.5` mean tokens versus `139,439.5` for raw UIAutomator (`0.506×`) and `99.18s` versus `101.20s` mean latency (`0.980×`). It therefore passes the stricter H5C subset gate and is eligible only for a full-suite candidate rerun. It is **not** deployment approval and does not complete Experiment 6-10's 116-task × five-seed requirement. See the [H5C evidence](validation/paired_h5c_compact_api35_20260729/evidence.json) and [report](validation/paired_h5c_compact_api35_20260729/report.md).

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

The current environment is a real Pixel 9 Pro API-35 AVD, not AndroidWorld's tested Pixel 6 API-33 reference. It lacks the complete third-party app bundle, and its non-root shell rejects AndroidWorld's per-task `date` command. The current evidence is consequently limited to four system Settings tasks; `--skip-device-time` is safe only for these time-independent Wi-Fi evaluators. These constraints prevent a valid full-suite run here and are recorded in every artifact.

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
3. Install the companion requirements in that environment, set the selected provider credential (the default is `ARK_API_KEY`), and run one of the commands above.
4. Provision the exact upstream Pixel 6 / API-33 apps before attempting `--full-suite`; do not use the API-35 Wi-Fi-only deviations for the full benchmark.

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

本目录**不是** [AndroidWorld](https://github.com/google-research/android_world) 基准的源码拷贝。它既包含 **T3A** 类移动 Agent 的**评估产物与分析笔记**，也包含一个连接独立、未修改上游 checkout 的配套 runner，用于真实执行书中的完整闭环：**诊断 → 假设 → 实验 → 决策 → 迭代**（对应**实验 6-10**）。

| 路径 | 作用 |
| --- | --- |
| [`t3a_summary.md`](t3a_summary.md) | 总览：逐任务结果 + 能力标签 × 难度矩阵、优势与短板 |
| [`t3a_failed_analysis.md`](t3a_failed_analysis.md) | 失败分类与根因（转录、复杂 UI、数学/计数等） |
| [`t3a.md`](t3a.md) | 完整逐步轨迹（含成功案例）：每步记录 `Action` / `Reason` / `Summary` |
| [`t3a_failed.md`](t3a_failed.md) | 失败任务轨迹（适合回放根因） |
| [`experiment_core.py`](experiment_core.py) | 证据聚合、成功/成本决策、严格完成门槛与五阶段报告渲染 |
| [`run_controlled_experiment.py`](run_controlled_experiment.py) | 真实 AndroidWorld 对照/处理与候选重跑 runner；没有 mock fallback |
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

### 如何使用（实验 6-10）

按书中五步闭环：

1. **诊断** — 交叉逐任务表与能力矩阵，把表面失败映射到能力缺陷。  
2. **假设** — 表层 → 中层 → 深层（如设置导航提示、修复多模态输入管道、截图+UI 树、更强视觉模型、仅对计数任务开思考）。  
3. **实验** — 先做低成本对照；同时量成功率与时延/成本副作用。  
4. **决策** — 优先部署高 ROI；拒绝为少数标签让全局任务承担数倍延迟/成本。  
5. **迭代** — 重跑全集，新失败模式成为下一轮起点。

### 已执行的对照闭环（2026-07-29）

配套 runner 会逐 episode 记录真实 AndroidWorld evaluator reward、Agent 是否显式结束、动作、步数、耗时、LLM 调用与 token。运行结束后，同一个真实配置模型会对聚合证据做受约束分析；JSON 证据始终是权威来源，LLM 文本不能覆盖它。

第一阶段测试低成本表层假设 **H1**：对照组使用原始 T3A prompt，处理组只增加 Wi-Fi 导航和最终状态确认指南。四个配对任务全部正常结束；两组均只成功 `1/4`，平均 evaluator reward 都是 `0.50`。处理组平均延迟由 `233.47s` 降至 `156.98s`，输入+输出 token 由 `442,619` 降至 `210,039`，但**没有配对成功增益**，因此不晋级。证据见 [phase-1 evidence](validation/paired_wifi_api35_20260729/evidence.json) 与 [report](validation/paired_wifi_api35_20260729/report.md)。

残余轨迹暴露了 API 35 观察兼容问题：打开 Internet 面板后，gRPC 无障碍树经常只剩状态栏元素，而独立 UIAutomator dump 能看到完整的真实 Settings 层级。因此第二阶段中层假设 **H5** 对比 gRPC forwarder 与 AndroidWorld 上游已有的 `A11yMethod.UIAUTOMATOR`，两组保持相同原始 T3A prompt、参数、seed、模型和 evaluator。H5 将该四任务切片从对照组 `1/4` 成功提升到 UIAutomator 的 `4/4`，但平均 token 比达到 `2.498×`，超过 `1.5×` 门槛，因此没有晋级。

随后执行的成本优化假设 **H5C** 对比原始 UIAutomator 与过滤非语义容器节点的紧凑 UIAutomator。两组都保持 `4/4` 成功；紧凑组平均 token 从 `139,439.5` 降至 `70,557.5`（`0.506×`），平均延迟从 `101.20s` 降至 `99.18s`（`0.980×`）。该结果通过了 H5C 的四任务候选门槛，但仅表示可以在完整参考环境中进行候选重跑，不是部署批准，也不是完整实验完成。证据见 [H5C JSON](validation/paired_h5c_compact_api35_20260729/evidence.json) 与 [报告](validation/paired_h5c_compact_api35_20260729/report.md)；英文部分列出了精确复现命令。

H1/H5 决策门槛要求至少四个完整 pair、净成功增益为正、零配对退化，且平均延迟与 token 都不超过对照的 `1.5×`。H5C 则要求四个紧凑处理组全部成功、零退化、延迟不超过 `1.5×`、token 不超过原始 UIAutomator 的 `0.75×`。通过门槛只允许进入**候选重跑**，绝不等于部署。候选重跑必须提供真实晋级 pair 的 evidence 文件；仅提供 run ID 不够。实验完成还必须有 580 条直接候选记录，即 116 个任务 × 五个不同 trial seed，且没有 episode error。

当前真实环境是 Pixel 9 Pro API-35 AVD，并非上游验证的 Pixel 6 API 33；它没有完整第三方 App bundle，非 root shell 也拒绝 AndroidWorld 的逐任务 `date` 命令。因此当前证据只能覆盖四个与时间无关的系统 Wi-Fi 任务；`--skip-device-time` 不能用于完整 benchmark。这些边界均写入 artifact，当前环境无法产生有效的全套完成结论。

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
3. 在对应环境中安装配套依赖，设置所选 provider 凭证（默认 `ARK_API_KEY`），运行英文部分给出的命令。
4. 只有在完整配置上游 Pixel 6 / API-33 App 后才能尝试 `--full-suite`；不要把 API-35 的 Wi-Fi 专用偏差用于完整 benchmark。

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
