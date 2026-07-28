## English

# Experiment 10-1: Staged System Prompt Based on Execution Phase

*Hands-on code accompanying "Understanding AI Agents"*

## Experiment Objective

The same Coding Agent loads **different system prompts + different tool sets** at different **execution phases** of a task,
thereby playing different roles and exhibiting different behavior patterns within the same conversation; while ensuring **conversation history and task state are continuously shared across phases**.

This experiment uses a single "Coding Agent" to chain together three phases:

| Phase | Role | System Prompt Emphasis | Supporting Tool Set | Tool Triggering Next Phase |
| --- | --- | --- | --- | --- |
| 1 Requirements Clarification | Requirements Analyst | Only ask clarifying questions, **do not write code** | `ask_clarifying_question` / `save_requirement` / `complete_requirements_analysis` | `complete_requirements_analysis` → Phase 2 |
| 2 Code Implementation | Software Engineer | Write high-quality Python based on confirmed requirements | `write_file` / `read_file` / `execute_code` / `submit_for_review` | `submit_for_review` → Phase 3 |
| 3 Code Review | Code Reviewer | Critically evaluate quality | `run_linter` / `run_tests` / `analyze_complexity` / `request_revision` / `approve_code` | `request_revision` → **fallback to Phase 2**; `approve_code` → Complete |

## Architecture

```text
demo.py                Entry point: run all three phases with one command (task = "write a Python script to organize the Downloads folder")
agent.py               StagedAgent: phase state machine + tool call loop + cross-phase shared context + execution log
tools.py               Schemas and real implementations for three tool sets (virtual workspace / real code execution / linter / complexity analysis)
simulated_user.py      Simulated user: automatically answers the Agent's questions during requirements clarification (predefined answers), enabling unattended operation
config.py              Read API Key / base_url / model from environment variables
```

Key design points:

- **Shared Context**: `StagedAgent.history` is a message list that persists throughout. When switching phases, **only the system prompt is replaced, only the tools passed to the model are swapped**; the history (requirements, code, review comments) is fully retained. Each request is `[system(current phase)] + history`.
- **Phase transitions triggered by tool calls**: The main loop detects when "signal tools" like `complete_requirements_analysis` / `submit_for_review` / `request_revision` / `approve_code` are called, injects a cross-phase "handover" message, and switches the phase.
- **Fallback mechanism**: When issues are found during the review phase, `request_revision(issues)` is called, sending the issue list back to the implementation phase; a `max_revisions` safety valve prevents infinite loops from burning tokens.
- **Real execution**: `execute_code` / `run_tests` write code to a temporary directory and run it in a real subprocess; `run_linter` / `analyze_complexity` perform real static analysis based on `ast`, not fake returns.

## How to Run

```bash
pip install -r requirements.txt

# Configuration (choose one)
export OPENAI_API_KEY=sk-...           # Option A: direct export
cp env.example .env && vi .env         # Option B: write to .env

python demo.py

# View offline three-phase configuration (roles / system prompts / tool sets / transition signals), no API Key required
python demo.py --list-stages

# View optional parameters (does not affect default behavior)
python demo.py --help
```

Optional command-line arguments (default values are identical to running without arguments):

| Argument | Default Value | Description |
| --- | --- | --- |
| `--task` | Organize Downloads folder task | Override the user task given to the Agent |
| `--start-stage` | `requirements` | Which phase to start from. Choosing `implementation` will pre-populate confirmed requirements equivalent to the output of the requirements clarification phase, starting directly from the implementation phase. Useful for debugging the latter two phases independently (`review` depends on code from the implementation phase and cannot be a starting point) |
| `--interactive` | Off | During the requirements clarification phase, a real person answers the Agent's questions from standard input (default uses the simulated user from `simulated_user.py` for automatic answers, enabling unattended full flow) |
| `--max-revisions` | `3` | Maximum number of fallbacks allowed during the review phase; exceeding this forces the demo to end |
| `--model` | Environment variable `OPENAI_MODEL` | Override the model name used |
| `--list-stages` | — | Print the three-phase configuration offline and exit, without calling any API (suitable for understanding the mechanism without a Key) |

Configurable environment variables (see `env.example`): `OPENAI_API_KEY`, `OPENAI_BASE_URL` (default is official),
`OPENAI_MODEL` (default `gpt-5.6-luna`, currently the affordable flagship), `OPENAI_TEMPERATURE` (default 0.3).
Can also switch to Kimi / Doubao compatible with the OpenAI protocol.

**Universal fallback**: Prefers using `OPENAI_API_KEY` to connect directly to OpenAI; if this variable is not set but `OPENROUTER_API_KEY` is, it automatically switches to OpenRouter and maps the model name to its namespace
(`gpt-5.6-luna` → `openai/gpt-5.6-luna`). Note: The `gpt-5.6` series requires organization verification for direct OpenAI connection. Simply setting `OPENROUTER_API_KEY` (without `OPENAI_API_KEY`) forces the use of OpenRouter, which is more convenient.

## What the Demo Illustrates

A real run (`gpt-5.6-luna`) will show:

1. **Requirements Clarification Phase**: The Agent behaves by "continuously asking questions" — proactively inquiring about which file types to process, whether to recurse, whether to keep original names, move or copy, how to determine the target directory, and saves each requirement with `save_requirement`. It **does not write any code**.
2. **Code Implementation Phase**: After the prompt switch, the same Agent behaves by "writing code" — producing a Python script with `write_file`, self-testing with `execute_code`, and then calling `submit_for_review`.
3. **Code Review Phase**: The Agent behaves as a "critical reviewer" — sequentially running `run_linter` / `run_tests` / `analyze_complexity`, discovering real issues (e.g., missing module docstring, smoke test `FileNotFoundError`), and then calling `request_revision` to **fall back to the implementation phase**.
4. The implementation phase **rewrites and fixes** the code based on the issue list, then submits again; after the review passes, `approve_code` is called, and the task is complete.

In other words: **The prompt + tool set change with the phase, and the behavior pattern changes noticeably accordingly**, while the task state (requirements, code, review comments) remains continuously shared across phases. At the end of the run, a "behavior distribution" statistic for each role is printed, visually comparing the behavioral differences across the three phases.

## Expected Output Example

The following is an excerpt from a real run (`python demo.py`, `gpt-5.6-luna`, routed via OpenRouter), fully demonstrating the behavior switch across three phases
(In this run, the requirements clarification phase repeatedly asked about case-sensitivity rules, triggered 1 review fallback, and ultimately hit the total step limit
safety valve to end — a common outcome in real runs, see "Limitations" below):

```text
Model: openai/gpt-5.6-luna  | base_url: https://openrouter.ai/api/v1

======================================================================
Entering phase: requirements  |  Role: Requirements Analyst  |  Available tools: ['ask_clarifying_question', 'save_requirement', 'complete_requirements_analysis']
======================================================================
[Requirements Analyst] Question: What file types do you want the script to organize? For example, organize all common files by extension, or only handle specific types like images, documents, videos, etc.?
[Requirements Analyst] Simulated user answer: Categorize by file type: Images (jpg/png/gif), Documents (pdf/doc/txt), Audio (mp3/wav), Video (mp4/mov), Archives (zip/rar), and put the rest into Others.
[Requirements Analyst] Recorded requirement: file_categories = Categorize by file type: Images jpg/png/gif; Documents pdf/doc/txt; Audio mp3/wav; Video mp4/mov; Archives zip/rar; other extensions go into Others.
[Requirements Analyst] Question: Do you need to recursively process subdirectories within the Downloads folder, or only process files in the root of the Downloads folder?
[Requirements Analyst] Recorded requirement: recursive = Do not recursively process subdirectories, only organize files at the current level of the Downloads folder, ignoring existing subfolders.
[Requirements Analyst] Recorded requirement: operation = Move files (move), do not keep the original location.
[Requirements Analyst] Recorded requirement: name_conflicts = Keep original filenames; if a file with the same name exists in the target directory, add _1, _2, etc., before the extension to avoid overwriting.
... (The simulated user only gives a fallback answer to "whether extensions are case-sensitive," so the Agent repeatedly asks about the same point, asking a total of 19 questions)
[Requirements Analyst] Completed requirements analysis -> Handing over to implementation: Confirmed: Script categorizes by specified extensions and puts other files into Others; only processes the current level of the download directory; default path is ~/Downloads, can also be specified via command-line argument; moves files instead of copying; extensions are case-insensitive; keeps original filenames, appends _1, _2, etc., to avoid overwriting in case of conflicts.

======================================================================
Entering phase: implementation  |  Role: Software Engineer  |  Available tools: ['write_file', 'read_file', 'execute_code', 'submit_for_review']
======================================================================
[Software Engineer] Wrote file: Wrote file organize_downloads.py (4312 characters, 135 lines)
[Software Engineer] Executed code for self-test: from pathlib import Path from tempfile import TemporaryDirectory import organize ...
[Software Engineer] Submitted for review -> Handing over to review: organize_downloads.py

======================================================================
Entering phase: review  |  Role: Code Reviewer  |  Available tools: ['run_linter', 'run_tests', 'analyze_complexity', 'request_revision', 'approve_code']
======================================================================
[Code Reviewer] run_linter: [linter] Passed: No issues found.
[Code Reviewer] run_tests: [tests] Smoke test result: FAIL
[Code Reviewer] analyze_complexity: [complexity] Number of functions=6, Branch/loop statements=16, Max nesting depth=3
[Code Reviewer] Review not passed -> Falling back to implementation: Fallback #1: ['Smoke test failed: `from __future__ import annotations` not at the beginning of the file triggers SyntaxError. Please remove this future import or use a compatible approach.']

======================================================================
Entering phase: implementation  |  Role: Software Engineer  |  Available tools: ['write_file', 'read_file', 'execute_code', 'submit_for_review']
======================================================================
[Software Engineer] Wrote file: Wrote file organize_downloads.py (4218 characters, 133 lines)
[Software Engineer] Submitted for review -> Handing over to review: organize_downloads.py
... (review phase repeats, looping until `approve_code` or reaching step/rollback limit)

======================================================================
Execution Summary
======================================================================
[Requirements Analyst] Behavior distribution: questions×19, simulated user responses×19, recorded requirements×7, completed requirements analysis -> handoff to implementation×1
[Software Engineer] Behavior distribution: wrote files×2, executed code self-tests×4, read files×1, submitted review -> handoff to review×2
[Code Reviewer] Behavior distribution: run_linter×1, run_tests×1, analyze_complexity×1, review failed -> rollback to implementation×1

Confirmed requirements count: 7
Output files: ['organize_downloads.py']
Review rollback count: 1
```

The three "behavior distribution" sections clearly show the different behavior patterns of the same Agent under three different prompts: the Requirements Analyst only asks and never writes, the Software Engineer only writes and never reviews, and the Code Reviewer only reviews and never writes.

## Will a stronger model make this "phase scaffolding" redundant?

A common intuition is that scaffolding (here, a state machine that switches system prompts and tool sets by phase) is just a crutch for weaker models. With a stronger model, it would naturally self-organize into "clarify first, then implement, then review," making the scaffolding obsolete. Using the same code, the same task, the same simulated user, and running `gpt-4o-mini` and `gpt-5.6-luna` locally for a real comparison, the conclusion is negative:

| Observation | `gpt-4o-mini` (weaker) | `gpt-5.6-luna` (stronger reasoning model) |
| --- | --- | --- |
| Number of requirements clarification questions | 5 (one question per point, then moves on) | **21** (repeatedly harping on the edge case of "how to classify uppercase extensions / files without extensions") |
| Completed all three phases and obtained `approve_code` | **Yes** (passed review after 1 rollback, task completed) | **No** (hit the 40-step total step safety valve and was forcibly terminated) |
| Review rollback count | 1 | 1 |

(Run commands: `MODEL=gpt-4o-mini python demo.py --model gpt-4o-mini`; `python demo.py --model gpt-5.6-luna`. The latter was routed via OpenRouter as `openai/gpt-5.6-luna`.)

Two key points:

1. **This scaffolding is not a "crutch that can be turned off," but a structural constraint.** Each phase only exposes the tools of that phase to the model (the requirements phase has no `write_file`, the implementation phase has no `approve_code`). Role separation is enforced by **tool gating**, applied equally to both strong and weak models—no model can "self-organize" to skip or merge phases. For this very reason, **there is no baseline** in this experiment where scaffolding is turned off and the strong model is allowed to freely improvise, for a strict comparison.
2. **Switching to a stronger model did not make the scaffolding redundant; instead, it became more dependent on its safety valves.** `gpt-5.6-luna` is more "persistent," insisting on asking about an edge case that the simulated user cannot answer, and cleverly rephrasing the question each time, thereby bypassing the `SimulatedUser`'s anti-repetition mechanism of "asking the same question twice prompts it to move to the next phase." As a result, it idled for over twenty steps in the requirements phase, burning through the 40-step budget—ultimately, the `max_total_steps` scaffolding safety valve had to catch it. The weaker `gpt-4o-mini`, on the other hand, because it "asked a few broad questions and then stopped," completed the entire process smoothly.

**Honest boundary**: The fact that `gpt-5.6-luna` did not finish this time is largely due to the `SimulatedUser` with preset answers (see "Limitations")—it couldn't answer the edge-case questions the strong model pursued, which triggered the idle loop. With a real human answering (`--interactive`) or a smarter simulated user, the strong model would likely converge much faster. Therefore, this data **cannot** be used to conclude that "a stronger model performs worse on this task." It only supports a narrower, but more useful, conclusion for the reader: **Phase-based prompts + tool gating is a structural scaffolding. The role separation and safety valves it provides work equally for both strong and weak models and will not automatically become ineffective or redundant as models become stronger.**

## Limitations

- **Dependence on the selected model's capabilities**: The default uses the inexpensive flagship `gpt-5.6-luna` to control demonstration costs. Note that "stronger model = faster convergence" is not always true: more persistent reasoning models are more likely to get stuck in the requirements clarification phase, asking edge-case questions that the preset `SimulatedUser` cannot answer, leading to idle loops (see the real comparison in the previous section). In such cases, the `max_total_steps` / `max_revisions` scaffolding safety valves are more critical for catching failures.
- **Single fixed task**: The built-in demo task is "organize the downloads folder." Although a `--task` parameter has been added to override it, the preset Q&A in `simulated_user.py` is designed around this specific task scenario. For tasks that are very different, the simulated user may not provide relevant answers.
- **Simulated user uses preset answers**: The `SimulatedUser` matches preset answers based on keywords; it does not truly understand semantics. When the Agent asks questions outside the preset script, it degrades to a fallback response or urges the Agent to move to the next phase.
- **Real LLMs have randomness**: Even with `temperature=0.3`, the order of questions, implementation details, whether the review passes, and the number of rollbacks can vary between runs. It is also possible, as in the example above, to hit the `max_revisions` safety valve and be forcibly terminated instead of obtaining `approve_code`.

---

## 中文

# 实验 10-1：根据执行阶段决定系统提示词（Staged System Prompt）

《深入理解 AI Agent》配套实验代码。

## 实验目的

同一个 Coding Agent，在任务的不同**执行阶段**加载**不同的系统提示词 + 不同的工具集**，
从而在同一段对话里扮演不同角色、表现出不同的行为模式；同时让**对话历史与任务状态在阶段间连续共享**。

本实验用一个「Coding Agent」串起三个阶段：

| 阶段 | 角色 | 系统提示词强调 | 配套工具集 | 触发进入下一阶段的工具 |
| --- | --- | --- | --- | --- |
| 1 需求澄清 | 需求分析师 | 只提问确认、**不写代码** | `ask_clarifying_question` / `save_requirement` / `complete_requirements_analysis` | `complete_requirements_analysis` → 阶段2 |
| 2 代码实现 | 软件工程师 | 按已确认需求写高质量 Python | `write_file` / `read_file` / `execute_code` / `submit_for_review` | `submit_for_review` → 阶段3 |
| 3 代码审查 | 代码审查员 | 批判性把关质量 | `run_linter` / `run_tests` / `analyze_complexity` / `request_revision` / `approve_code` | `request_revision` → **回退阶段2**；`approve_code` → 完成 |

## 架构

```
demo.py                入口：一条命令跑通三阶段（任务 = “写一个整理下载文件夹的 Python 脚本”）
agent.py               StagedAgent：阶段状态机 + 工具调用循环 + 跨阶段共享上下文 + 执行日志
tools.py               三套工具的 Schema 与真实实现（虚拟工作区 / 真实执行代码 / linter / 复杂度分析）
simulated_user.py      模拟用户：需求澄清阶段自动回答 Agent 的提问（预设答案），实现无人值守
config.py              从环境变量读取 API Key / base_url / model
```

关键设计：

- **共享上下文**：`StagedAgent.history` 是一条贯穿始终的消息列表，切换阶段时**只替换 system 提示词、只切换传给模型的 tools**，历史消息（需求、代码、审查意见）全部保留。每次请求都是 `[system(当前阶段)] + history`。
- **阶段转换由工具调用触发**：主循环识别到 `complete_requirements_analysis` / `submit_for_review` / `request_revision` / `approve_code` 这些「信号工具」被调用时，注入一条跨阶段「交接」消息并切换阶段。
- **回退机制**：审查阶段发现问题时调用 `request_revision(issues)`，把问题清单退回实现阶段；设有 `max_revisions` 安全阀，避免无限循环烧 token。
- **真实执行**：`execute_code` / `run_tests` 会把代码写入临时目录并用子进程真实运行；`run_linter` / `analyze_complexity` 基于 `ast` 做真实静态分析，不是假返回。

## 如何运行

```bash
pip install -r requirements.txt

# 配置（二选一）
export OPENAI_API_KEY=sk-...           # 方式 A：直接 export
cp env.example .env && vi .env         # 方式 B：写到 .env

python demo.py

# 离线查看三阶段配置（角色 / 系统提示词 / 工具集 / 转换信号），无需 API Key
python demo.py --list-stages

# 查看可选参数（不影响默认行为）
python demo.py --help
```

可选命令行参数（默认值与不加参数完全一致）：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--task` | 整理下载文件夹的任务 | 覆盖交给 Agent 的用户任务 |
| `--start-stage` | `requirements` | 从哪个阶段开始。选 `implementation` 会预置一份等价于需求澄清产物的已确认需求、直接从实现阶段起步，便于单独调试后两个阶段（`review` 依赖实现阶段的代码，不能作为起点） |
| `--interactive` | 关 | 需求澄清阶段改由真人从标准输入回答 Agent 的提问（默认用 `simulated_user.py` 的模拟用户自动回答，可无人值守跑通全流程） |
| `--max-revisions` | `3` | 审查阶段允许的最大回退次数，超过则强制结束演示 |
| `--model` | 环境变量 `OPENAI_MODEL` | 覆盖使用的模型名 |
| `--list-stages` | — | 离线打印三阶段配置后退出，不调用任何 API（适合无 Key 时先看清机制） |

可配环境变量（见 `env.example`）：`OPENAI_API_KEY`、`OPENAI_BASE_URL`（默认官方）、
`OPENAI_MODEL`（默认 `gpt-5.6-luna`，当前便宜旗舰）、`OPENAI_TEMPERATURE`（默认 0.3）。
也可切到兼容 OpenAI 协议的 Kimi / Doubao。

**通用回退**：优先用 `OPENAI_API_KEY` 直连 OpenAI；若未设置该变量但设了
`OPENROUTER_API_KEY`，则自动改走 OpenRouter，并把模型名映射到其命名空间
（`gpt-5.6-luna` → `openai/gpt-5.6-luna`）。提示：`gpt-5.6` 系列直连 OpenAI 需组织验证，
只填 `OPENROUTER_API_KEY`（不填 `OPENAI_API_KEY`）即可强制走 OpenRouter，更省事。

## 演示说明了什么问题

一次真实运行（`gpt-5.6-luna`）会看到：

1. **需求澄清阶段**：Agent 表现为「不断提问」——主动追问处理哪些文件类型、是否递归、是否保留原名、移动还是复制、目标目录怎么定，并逐条 `save_requirement`。它**完全不写代码**。
2. **代码实现阶段**：同一个 Agent 换了提示词后表现为「写代码」——`write_file` 产出 Python 脚本，`execute_code` 自测，然后 `submit_for_review`。
3. **代码审查阶段**：Agent 表现为「批判审查」——依次跑 `run_linter` / `run_tests` / `analyze_complexity`，发现真实问题（如缺少模块 docstring、冒烟测试 `FileNotFoundError`）后 `request_revision` **退回实现阶段**。
4. 实现阶段据问题清单**重写并修复**，再次提交；审查通过后 `approve_code`，任务完成。

也就是说：**提示词 + 工具集随阶段切换，行为模式随之明显不同**，而任务状态（需求、代码、审查意见）在阶段间始终连续共享。运行结束时会打印每个角色的「行为分布」统计，直观对比三个阶段的行为差异。

## 预期输出示例

以下是一次真实运行（`python demo.py`，`gpt-5.6-luna`，经 OpenRouter 路由）的节选，完整展示三阶段的行为切换
（本次运行需求澄清阶段反复追问了大小写规则、触发了 1 次审查回退，最终撞到总步数上限
安全阀结束，也是真实运行中常见的一种结局，详见下方「局限」）：

```
模型：openai/gpt-5.6-luna  | base_url：https://openrouter.ai/api/v1

======================================================================
进入阶段：requirements  |  角色：需求分析师  |  可用工具：['ask_clarifying_question', 'save_requirement', 'complete_requirements_analysis']
======================================================================
[需求分析师] 提问: 你希望脚本整理哪些文件类型？例如按扩展名整理所有常见文件，还是只处理图片、文档、视频等指定类型？
[需求分析师] 模拟用户回答: 按文件类型分类：图片(jpg/png/gif)、文档(pdf/doc/txt)、音频(mp3/wav)、视频(mp4/mov)、压缩包(zip/rar)，其余归到 Others。
[需求分析师] 记录需求: file_categories = 按文件类型分类：图片 jpg/png/gif；文档 pdf/doc/txt；音频 mp3/wav；视频 mp4/mov；压缩包 zip/rar；其他扩展名归入 Others。
[需求分析师] 提问: 整理时是否需要递归处理下载文件夹的子目录，还是只处理下载文件夹根目录中的文件？
[需求分析师] 记录需求: recursive = 不递归处理子目录，只整理下载文件夹当前层级的文件，忽略已有子文件夹。
[需求分析师] 记录需求: operation = 移动文件（move），不保留原位置的文件。
[需求分析师] 记录需求: name_conflicts = 保留原文件名；目标目录存在同名文件时，在扩展名前添加 _1、_2 等序号，避免覆盖。
...（模拟用户对「扩展名是否区分大小写」只会给出兜底回答，Agent 因此反复追问同一点，共提问 19 次）
[需求分析师] 完成需求分析 -> 转交实现: 已确认：脚本按指定扩展名分类并将其他文件归入 Others；仅处理下载目录当前层级；默认路径为 ~/Downloads、也可通过命令行参数指定；移动文件而非复制；扩展名不区分大小写；保留原文件名，冲突时追加 _1、_2 等避免覆盖。

======================================================================
进入阶段：implementation  |  角色：软件工程师  |  可用工具：['write_file', 'read_file', 'execute_code', 'submit_for_review']
======================================================================
[软件工程师] 写文件: 已写入文件 organize_downloads.py（4312 字符，135 行）
[软件工程师] 执行代码自测: from pathlib import Path from tempfile import TemporaryDirectory import organize ...
[软件工程师] 提交审查 -> 转交审查: organize_downloads.py

======================================================================
进入阶段：review  |  角色：代码审查员  |  可用工具：['run_linter', 'run_tests', 'analyze_complexity', 'request_revision', 'approve_code']
======================================================================
[代码审查员] run_linter: [linter] 通过：未发现问题。
[代码审查员] run_tests: [tests] 冒烟测试结果：FAIL
[代码审查员] analyze_complexity: [complexity] 函数数量=6，分支/循环语句=16，最大嵌套深度=3
[代码审查员] 审查不通过 -> 回退实现: 第1次退回：['冒烟测试失败：`from __future__ import annotations` 不在文件开头触发 SyntaxError，请移除该 future import 或改用兼容写法。']

======================================================================
进入阶段：implementation  |  角色：软件工程师  |  可用工具：['write_file', 'read_file', 'execute_code', 'submit_for_review']
======================================================================
[软件工程师] 写文件: 已写入文件 organize_downloads.py（4218 字符，133 行）
[软件工程师] 提交审查 -> 转交审查: organize_downloads.py

...（审查阶段再次检查，如此循环，直到 approve_code 或达到步数/回退上限）

======================================================================
执行小结
======================================================================
[需求分析师] 行为分布：提问×19, 模拟用户回答×19, 记录需求×7, 完成需求分析 -> 转交实现×1
[软件工程师] 行为分布：写文件×2, 执行代码自测×4, 读文件×1, 提交审查 -> 转交审查×2
[代码审查员] 行为分布：run_linter×1, run_tests×1, analyze_complexity×1, 审查不通过 -> 回退实现×1

已确认需求条数：7
产出文件：['organize_downloads.py']
审查回退次数：1
```

三段「行为分布」清楚对照出同一个 Agent 在三种提示词下的不同行为模式：需求分析师只问不写，
软件工程师只写不审，代码审查员只查不写。

## 更强的模型会让这套「阶段脚手架」变得多余吗？

一个常见直觉是：脚手架（这里指「按阶段切换系统提示词 + 工具集」的状态机）只是给弱模型用的拐杖，
换上更强的模型，它自然会「先澄清、再实现、后审查」地自我组织，脚手架随之失效。
用同一套代码、同一个任务、同一个模拟用户，本地各**真实**跑一次 `gpt-4o-mini` 与 `gpt-5.6-luna` 对照，
结论是否定的：

| 观察项 | `gpt-4o-mini`（较弱） | `gpt-5.6-luna`（较强推理模型） |
| --- | --- | --- |
| 需求澄清提问次数 | 5（一问一点，问完即走） | **21**（反复纠缠「大写扩展名 / 无扩展名文件如何归类」这一个边角情形） |
| 是否跑完三阶段拿到 `approve_code` | **是**（1 次回退后审查通过、任务完成） | **否**（撞到 40 步总步数安全阀被强制结束） |
| 审查回退次数 | 1 | 1 |

（运行命令：`MODEL=gpt-4o-mini python demo.py --model gpt-4o-mini`；`python demo.py --model gpt-5.6-luna`。
后者经 OpenRouter 路由为 `openai/gpt-5.6-luna`。）

要点有两个：

1. **这套脚手架不是「可以关掉的拐杖」，而是结构性约束。** 每个阶段只把本阶段的工具暴露给模型
   （需求阶段根本没有 `write_file`，实现阶段根本没有 `approve_code`），角色分离是被**工具门控**强制出来的，
   对强弱模型一视同仁——没有哪个模型能「自我组织」跳过或合并阶段。也正因如此，本实验里**并不存在**
   一个「关掉脚手架、让强模型自由发挥」的基线可供严格对照。
2. **换上更强的模型并没有让脚手架变多余，反而更依赖它的安全阀。** `gpt-5.6-luna` 更「较真」，
   坚持把一个模拟用户答不上来的边角规则问到底，而且聪明到每次都换一种问法，
   恰好绕开了 `SimulatedUser`「同一问题问两次就催它进入下一阶段」的防重复机制，
   于是在需求阶段空转了二十多步、把 40 步预算烧光——最后是 `max_total_steps` 这个脚手架安全阀替它兜的底；
   较弱的 `gpt-4o-mini` 反而因为「问几个大方向就收手」顺利跑完了全程。

**诚实的边界**：`gpt-5.6-luna` 这次没跑完，很大程度上是被预设答案的 `SimulatedUser`（见「局限」）拖累的——
它答不上强模型追问的边角问题，才诱发了空转；换真人回答（`--interactive`）或更聪明的模拟用户，
强模型大概率能更快收敛。所以这组数据**不能**推出「强模型在这个任务上更差」，
只能支持一个更窄、但对读者更有用的结论：**阶段化提示词 + 工具门控是一种结构性脚手架，
它带来的角色分离与安全阀对强弱模型同样生效，不会因为模型变强就自动失效或变得多余。**

## 局限

- **依赖所选模型的能力**：默认用便宜旗舰 `gpt-5.6-luna` 控制演示成本。注意「更强的模型 = 更快收敛」
  并不总成立：越较真的推理模型越容易在需求澄清阶段追问预设 `SimulatedUser` 答不上的边角问题而空转
  （见上一节的真实对照），此时更依赖 `max_total_steps` / `max_revisions` 这两个脚手架安全阀兜底。
- **单一固定任务**：内置演示任务是「整理下载文件夹」，虽然新增了 `--task` 参数可覆盖，
  但 `simulated_user.py` 的预设问答是围绕这个任务场景设计的，换成差异很大的任务时模拟用户可能答不上点子上。
- **模拟用户是预设答案**：`SimulatedUser` 按关键词匹配预设回答，不是真正理解语义的用户，
  遇到 Agent 提出预设脚本之外的问题时会退化为兜底回答或催促进入下一阶段。
- **真实 LLM 有随机性**：即使 `temperature=0.3`，不同次运行的提问顺序、代码实现细节、
  审查是否通过、回退次数都可能不同；也可能像上面这次示例一样撞到 `max_revisions` 安全阀
  强制结束，而不是拿到 `approve_code`。
