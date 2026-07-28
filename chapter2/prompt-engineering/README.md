# Prompt Engineering Ablation (τ-bench) / 提示工程消融实验

> Companion material for *AI Agents in Depth*, Chapter 2 — **Experiment 2-4 ★★: Ablation study in prompt engineering**.  
> 配套《深入理解 AI Agent》第 2 章 **实验 2-4 ★★：提示工程的消融实验**。

← [Chapter 2 index / 返回第 2 章目录](../README.md)

---

## English

### Overview

Extends the [τ-bench](https://arxiv.org/abs/2406.12045) framework with three ablation axes to show why **prompt engineering treats an Agent like a smart new hire**. Experiments quantify how tone, instruction organization, and tool descriptions affect task success.

### Ablation options

#### 1. Tone style

- **default** — professional baseline  
- **trump** — exaggerated, repetitive, confident phrasing  
- **casual** — emoji/slang, informal  

**Rationale:** Tone affects professionalism and task quality. Over-casual or exaggerated tone can reduce trust, increase misunderstanding, and hurt execution accuracy.

#### 2. Wiki rule randomization

Uses a pre-generated chaotic `wiki.md`:

- Strip section headings/structure  
- Prefix each rule with operation context (e.g. “When booking flights”)  
- Fully shuffle into a flat list  
- Break logical relationships between rules  

**Rationale:** Well-organized instructions are like a training manual. Extreme randomization destroys hierarchy, blurs rule boundaries, and raises misuse/omission risk.

#### 3. Tool description removal

- Empty tool and parameter descriptions  
- Tests the value of explicit documentation  

**Rationale:** Clear tool docs are the “how to use the tools” handbook. Without them the Agent misuses tools more often and completion rates drop.

### Installation

```bash
cd chapter2/prompt-engineering
pip install -r requirements.txt
```

(Older docs may mention `projects/week2/prompt-engineering`; use this repo path.)

### Usage

All entry scripts have Chinese `--help`: `python run_ablation.py --help`, `python analyze_results.py --help`.

#### One-shot full ablation + comparison table (recommended)

`--all` runs baseline + each single-axis ablation + all combined in one process, prints a success-rate table, and writes summary stats to `--output` (default `log-dir/ablation_summary_<timestamp>.json`). Best way to reproduce book 实验 2-4:

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --end-index 10 \
    --all
# Default: OpenAI direct (provider=openai) → set OPENAI_API_KEY.
# OpenRouter: use a slashed model id (e.g. openai/gpt-5) → openrouter + OPENROUTER_API_KEY.
# Fallback: bare id (e.g. gpt-4o-mini) with no OPENAI_API_KEY but OPENROUTER_API_KEY set
#           is rewritten to openai/gpt-4o-mini and routed via openrouter.
```

Example **real smoke** table (`--model gpt-4o --env airline --end-index 4`, only 4 tasks/group—illustrates table shape, not stable science):

```
Experiment                        Success Rate      Tasks        Relative
----------------------------------------------------------------------
wiki_random                      50.0%         2/  4      200.0%
baseline                         25.0%         1/  4      100.0%  ⭐
tone_trump                       25.0%         1/  4      100.0%
tone_casual                      25.0%         1/  4      100.0%
no_tool_desc                      0.0%         0/  4        0.0%
all_ablations                     0.0%         0/  4        0.0%
```

> ⚠️ n=4 per arm is very noisy—e.g. `wiki_random` above baseline is chance, not a real finding. Directional signals (no tool desc → 0%, full stack → 0%, tone little effect on success) match 实验 2-4; for stable numbers use `--end-index` ≥ 10 and multiple `--seed`. Use **your** full runs, not these smoke digits.

#### Baseline (single config)

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --task-split test \
    --start-index 0 \
    --end-index 10
# bare ids → OpenAI direct; ids with '/' → openrouter
```

#### Tone ablations

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --tone-style trump \
    --ablation-name trump_tone

python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --tone-style casual \
    --ablation-name casual_tone
```

#### Wiki randomization

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --randomize-wiki \
    --ablation-name wiki_random
```

#### Remove tool descriptions

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --remove-tool-descriptions \
    --ablation-name no_tool_desc
```

#### Combined ablations

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --tone-style casual \
    --randomize-wiki \
    --remove-tool-descriptions \
    --ablation-name full_ablation
```

### Experiment scripts

Two equivalent ways to run the full suite:

1. **Python one-shot (recommended):** `python run_ablation.py --env airline --end-index 10 --all`  
2. **Bash orchestration:** `run_full_ablation.sh` calls `run_ablation.py` then `analyze_results.py`:

```bash
./run_full_ablation.sh --model gpt-5.6-luna --env airline --num-tasks 10
./run_full_ablation.sh --quick   # 3 tasks/arm smoke
```

### Result analysis

Raw trajectories land in `results_ablation/` with:

- **task_id**, **reward** (0/1), **info**, **traj**, **ablation_config**

```bash
python analyze_results.py
python analyze_results.py --results-dir results_ablation --output summary.json
```

> `--all` already prints the comparison table; `analyze_results.py` is for re-aggregating historical/manual runs. Bundled `results_ablation/*.json` are small debug samples (1–6 tasks)—**not** enough for statistical claims; use full runs (`--end-index` ≥ 10).

### Expected ranking

1. **Baseline** — best  
2. **Tone variants** — usually little success-rate impact  
3. **Wiki randomization** — hurts instruction following  
4. **No tool descriptions** — many bad tool args / wrong ops  
5. **Combined** — worst  

### Key insights

Treat the Agent as a smart new employee:

1. **Clear instructions matter** — structure, task description, tool how-to  
2. **Context organization matters** — logical order, group related rules, explicit priority  
3. **Tool docs are required** — purpose, parameters, examples  

### Parameters

| Parameter | Description | Options |
|------|------|------|
| `--tone-style` | Axis 1: tone on system prompt | default, trump, casual |
| `--randomize-wiki` | Axis 2: scramble wiki structure | flag |
| `--remove-tool-descriptions` | Axis 3: strip tool docs | flag |
| `--all` | Full ablation suite + comparison table | flag |
| `--output` | Summary JSON path (`--all` only) | string |
| `--ablation-name` | Run label | string |
| `--env` | Environment | airline, retail |
| `--model` | Model id | e.g. gpt-4o-mini, gpt-4o |
| `--model-provider` | Provider (optional) | auto: bare → openai, `/` → openrouter |
| `--task-split` | Split | train, test, dev |
| `--start-index` / `--end-index` | Task range | integers |
| `--log-dir` | Results directory | string |

### Troubleshooting

1. **ImportError** — correct cwd + install deps  
2. **API errors** — keys and quota  
3. **Memory** — lower `--max-concurrency`  

Debug:

```bash
export LITELLM_LOG=DEBUG
python run_ablation.py ...
```

### Summary

Ablations quantify prompt quality: poor structure/docs can cost **30–80%** performance. Structure and clarity dominate; professionalism and consistency support effective Agents. Good prompt engineering ≈ good employee training.

### Upstream τ-bench (bundled)

This tree vendors τ-bench (tool-agent-user interaction benchmark). Upstream news: [τ²-bench](https://github.com/sierra-research/tau2-bench) adds fixes + a `telecom` domain.

**Papers:** [τ-bench](https://arxiv.org/abs/2406.12045), [τ²-Bench](https://arxiv.org/abs/2506.07982)

**Vanilla τ-bench run** (non-ablation path):

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o \
  --model-provider openai --user-model gpt-4o --user-model-provider openai \
  --user-strategy llm --max-concurrency 10
# optional: --task-ids 2 4 6
```

User strategies include `llm`, `react`, `verify`, `reflection`. See original τ-bench docs for leaderboards, auto error identification, and historical trajectories. License: `./LICENSE`.

---

## 中文

### 概述

扩展 [τ-bench](https://arxiv.org/abs/2406.12045) 框架，增加三个关键消融维度，演示**提示工程：把 Agent 看成聪明的新员工**的重要性，并量化语气、指令组织、工具描述对任务成功率的影响。

### 消融研究选项

#### 1. 语气风格

- **default**：标准专业语气（基线）  
- **trump**：夸张、重复强调、自信表述  
- **casual**：表情符号、俚语、轻松口吻  

**原理：** 语气影响专业性与任务质量；过于随意或夸张可能降低信任、增加误解、损害执行准确度。

#### 2. Wiki 规则随机化

使用预生成的极度混乱版 wiki：

- 移除章节标题与结构  
- 每条规则加操作上下文前缀（如 “When booking flights”）  
- 打乱成平面列表  
- 破坏规则间逻辑关系  

**原理：** 组织良好的指令像培训手册；极度随机化破坏层级、混淆规则边界、抬高误用与遗漏风险。

#### 3. 工具描述移除

- 工具与参数描述置空  
- 检验「写清楚怎么用」的重要性  

**原理：** 清晰工具说明像操作手册；去掉后误用上升、完成率下降。

### 安装

```bash
cd chapter2/prompt-engineering
pip install -r requirements.txt
```

（旧文档可能写 `projects/week2/prompt-engineering`；请使用本仓库路径。）

### 使用方法

入口脚本均提供中文 `--help`：`python run_ablation.py --help`、`python analyze_results.py --help`。

#### 一键完整消融并输出对比表（推荐）

`--all` 在同一进程内依次跑基线 + 三个维度单独消融 + 全部叠加，打印成功率对比表，汇总写入 `--output`（默认 `log-dir/ablation_summary_<时间戳>.json`）。复现书中实验 2-4 最直接：

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --end-index 10 \
    --all
# 默认 OpenAI 直连（provider=openai），需 OPENAI_API_KEY。
# 走 OpenRouter：模型写成带斜杠 id（如 openai/gpt-5），需 OPENROUTER_API_KEY。
# 通用回退：裸 id（如 gpt-4o-mini）且未设 OPENAI_API_KEY、已设 OPENROUTER_API_KEY 时，
#           自动前缀为 openai/gpt-4o-mini 并切到 openrouter。
```

**真实冒烟**表示例（`--model gpt-4o --env airline --end-index 4`，每组仅 4 任务，只用于展示表格形态）：

```
Experiment                        Success Rate      Tasks        Relative
----------------------------------------------------------------------
wiki_random                      50.0%         2/  4      200.0%
baseline                         25.0%         1/  4      100.0%  ⭐
tone_trump                       25.0%         1/  4      100.0%
tone_casual                      25.0%         1/  4      100.0%
no_tool_desc                      0.0%         0/  4        0.0%
all_ablations                     0.0%         0/  4        0.0%
```

> ⚠️ 每组 4 任务噪声极大——例如 `wiki_random` 偶然高于 baseline 不是真实结论。方向性信号（去掉工具描述 → 0%、全部叠加 → 0%、语气对成功率影响小）与实验 2-4 一致；要稳定量化请把 `--end-index` 提到 10 以上并多跑 `--seed`。以你自己的完整运行为准。

#### 基线（单配置）

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --task-split test \
    --start-index 0 \
    --end-index 10
# 裸 id → OpenAI 直连；带 / 的 id → openrouter
```

#### 语气消融

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --tone-style trump \
    --ablation-name trump_tone

python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --tone-style casual \
    --ablation-name casual_tone
```

#### Wiki 随机化

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --randomize-wiki \
    --ablation-name wiki_random
```

#### 移除工具描述

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --remove-tool-descriptions \
    --ablation-name no_tool_desc
```

#### 组合消融

```bash
python run_ablation.py \
    --model gpt-5.6-luna \
    --env airline \
    --tone-style casual \
    --randomize-wiki \
    --remove-tool-descriptions \
    --ablation-name full_ablation
```

### 实验脚本

完整套消融有两种等价方式：

1. **Python 一键（推荐）：** `python run_ablation.py --env airline --end-index 10 --all`  
2. **Bash 编排：** `run_full_ablation.sh` 逐个调用 `run_ablation.py` 再 `analyze_results.py`：

```bash
./run_full_ablation.sh --model gpt-5.6-luna --env airline --num-tasks 10
./run_full_ablation.sh --quick   # 每组 3 任务冒烟
```

### 结果分析

原始轨迹在 `results_ablation/`，含 **task_id**、**reward**（0/1）、**info**、**traj**、**ablation_config**。

```bash
python analyze_results.py
python analyze_results.py --results-dir results_ablation --output summary.json
```

> `--all` 结束时已打印对比表；`analyze_results.py` 用于事后重汇总。仓库内 `results_ablation/*.json` 为少量调试样本（1–6 任务），**不足以做统计结论**；请用完整运行（`--end-index` ≥ 10）。

### 预期排序

1. **Baseline** — 最佳  
2. **语气变化** — 通常对成功率影响不大  
3. **Wiki 随机化** — 严重损害指令遵循  
4. **无工具描述** — 大量参数错误 / 错误操作  
5. **组合消融** — 最差  

### 关键洞察

把 Agent 看成聪明的新员工：

1. **清晰指令至关重要** — 结构化信息、任务描述、工具用法  
2. **上下文组织影响理解** — 逻辑排序、相关规则归并、优先级明确  
3. **工具文档不可或缺** — 用途、参数、示例  

### 参数说明

| 参数 | 说明 | 选项 |
|------|------|------|
| `--tone-style` | 维度一·语气风格 | default, trump, casual |
| `--randomize-wiki` | 维度二·随机化 wiki 结构 | flag |
| `--remove-tool-descriptions` | 维度三·移除工具描述 | flag |
| `--all` | 一键完整消融并打印对比表 | flag |
| `--output` | （仅 --all）汇总 JSON 路径 | string |
| `--ablation-name` | 实验名称标识 | string |
| `--env` | 环境 | airline, retail |
| `--model` | 模型 | 如 gpt-4o-mini, gpt-4o |
| `--model-provider` | 提供商（可选） | 自动：裸 id → openai，带 / → openrouter |
| `--task-split` | 任务集 | train, test, dev |
| `--start-index` / `--end-index` | 任务区间 | 整数 |
| `--log-dir` | 结果目录 | string |

### 故障排除

1. **ImportError**：确认目录与依赖  
2. **API 错误**：密钥与配额  
3. **内存**：降低 `--max-concurrency`  

```bash
export LITELLM_LOG=DEBUG
python run_ablation.py ...
```

### 总结

消融框架量化展示：提示工程不当时可出现 **30–80%** 的性能下滑；**结构与清晰度**最关键；专业性与一致性支撑有效 Agent 系统。记住：优秀的提示工程就是优秀的员工培训。

### 上游 τ-bench（内嵌）

本目录内嵌 τ-bench（工具-Agent-用户交互基准）。上游进展：[τ²-bench](https://github.com/sierra-research/tau2-bench) 含修复与 `telecom` 域。

**论文：** [τ-bench](https://arxiv.org/abs/2406.12045)、[τ²-Bench](https://arxiv.org/abs/2506.07982)

**原版（非消融）运行：**

```bash
python run.py --agent-strategy tool-calling --env retail --model gpt-4o \
  --model-provider openai --user-model gpt-4o --user-model-provider openai \
  --user-strategy llm --max-concurrency 10
# 可选：--task-ids 2 4 6
```

用户模拟策略含 `llm`、`react`、`verify`、`reflection`。排行榜、自动错误识别、历史轨迹等见原版 τ-bench 文档。许可：`./LICENSE`。

---

## Notes / 说明

- Book experiment path is `run_ablation.py`; vanilla `run.py` is the upstream τ-bench entry.  
- 书中实验主路径是 `run_ablation.py`；`run.py` 为上游 τ-bench 原版入口。  
- Smoke tables in this README are not publishable success rates.  
- 文中冒烟表不可当作可发表的成功率数字。
