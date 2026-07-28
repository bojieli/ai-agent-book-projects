# AndroidWorld T3A Evaluation Notes / AndroidWorld T3A 评估分析笔记

> Companion material for *AI Agents in Depth*, Chapter 6 — **Experiment 6-10: Evaluate and improve on AndroidWorld**.  
> 配套《深入理解 AI Agent》第 6 章 **实验 6-10 ★★★：AndroidWorld 的评估和改进**。

← [Chapter 6 index / 返回第 6 章目录](../README.md) · 📖 [Read the chapter / 读本章正文](../../book/chapter6.md)（[EN](../../book-en/chapter6.md)）

---

## English

### What this directory is

This folder is **not** a copy of the [AndroidWorld](https://github.com/google-research/android_world) benchmark codebase. It is a set of **evaluation artifacts and analysis notes** for a **T3A** (Text-only / accessibility-tree style mobile agent) run on AndroidWorld—used in the book as the starting point for a full **diagnose → hypothesize → experiment → decide → iterate** evaluation loop.

| Path | Role |
| --- | --- |
| [`t3a_summary.md`](t3a_summary.md) | High-level report: per-task outcomes + capability-tag × difficulty matrix, strengths/weaknesses |
| [`t3a_failed_analysis.md`](t3a_failed_analysis.md) | Failure taxonomy with root-cause write-ups (transcription, complex UI, math/counting, etc.) |
| [`t3a.md`](t3a.md) | Full step traces for runs (including successes): per-step `Action` / `Reason` / `Summary` records |
| [`t3a_failed.md`](t3a_failed.md) | Step traces focused on failed tasks (useful for root-cause replay) |

If you need to **run** the benchmark yourself, clone and follow the upstream project (see [Reproduce the benchmark](#reproduce-the-benchmark-optional) below). This directory is primarily for **reading and analysis**.

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
├── t3a_summary.md            # Aggregated metrics + capability matrix
├── t3a_failed_analysis.md    # Failure taxonomy & root causes
├── t3a.md                    # Full (large) run logs
└── t3a_failed.md             # Failed-task run logs
```

### Reproduce the benchmark (optional)

This repo does **not** vendor AndroidWorld. To re-run evaluation upstream:

1. Clone [google-research/android_world](https://github.com/google-research/android_world) (or the fork your course materials specify).
2. Provide an Android emulator / device environment as required by that project.
3. Point your agent implementation (T3A or other) at the task suite and export traces comparable to `t3a*.md`.

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

本目录**不是** [AndroidWorld](https://github.com/google-research/android_world) 基准的源码拷贝，而是一份 **T3A** 类移动 Agent 在 AndroidWorld 上的**评估产物与分析笔记**。书中用它作为完整闭环的起点：**诊断 → 假设 → 实验 → 决策 → 迭代**（对应**实验 6-10**）。

| 路径 | 作用 |
| --- | --- |
| [`t3a_summary.md`](t3a_summary.md) | 总览：逐任务结果 + 能力标签 × 难度矩阵、优势与短板 |
| [`t3a_failed_analysis.md`](t3a_failed_analysis.md) | 失败分类与根因（转录、复杂 UI、数学/计数等） |
| [`t3a.md`](t3a.md) | 完整逐步轨迹（含成功案例）：每步记录 `Action` / `Reason` / `Summary` |
| [`t3a_failed.md`](t3a_failed.md) | 失败任务轨迹（适合回放根因） |

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
├── t3a_summary.md            # 汇总指标与能力矩阵
├── t3a_failed_analysis.md    # 失败分类与根因
├── t3a.md                    # 完整运行日志（体积大）
└── t3a_failed.md             # 失败任务日志
```

### 复现基准（可选）

本仓库**不**内嵌 AndroidWorld。自行重跑请：

1. 克隆 [google-research/android_world](https://github.com/google-research/android_world)（或课程指定 fork）。  
2. 按上游文档准备模拟器/真机环境。  
3. 接入你的 Agent（T3A 或其他），导出与 `t3a*.md` 类似的轨迹。

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
- Project type in the chapter index: **📖 reading / analysis notes** (not a standalone runnable lab in this folder).  
- 在章节目录中归类为 **📖 阅读/分析材料**（本目录内无可独立运行的评测代码）。
