# System-Hint Enhanced AI Agent / Agent 状态栏（System Hint）实验

> Companion material for *AI Agents in Depth*, Chapter 2 — **Experiment 2-8 ★★: Useful Agent status-bar techniques**.  
> 配套《深入理解 AI Agent》第 2 章 **实验 2-8 ★★：几种好用的 Agent 状态栏技术**。

← [Chapter 2 index / 返回第 2 章目录](../README.md)

---

## English

### Overview

Corresponds to the book’s **Agent Status Bar** section. This directory is the `agent-status-bar` experiment framework—**system hint** and **Agent status bar** are two names for the same idea: inject a dynamic state summary as a temporary `role=user` message at the end of the context.

An advanced Agent that uses system hints to improve trajectories and reduce infinite loops, poor context awareness, and weak task management, with automatic trajectory saving for debugging.

### Offline preview first (no API key)

To see how the status bar changes the context the model would see, without any API key:

```bash
python main.py --mode preview
```

Renders five techniques (timestamps, tool-call counter, TODO list, detailed errors, system-state awareness), each as **without vs with** status bar, and prints the full status message appended at the end of context. Use `--no-timestamps` / `--no-counter` / `--no-todo` / `--no-errors` / `--no-state` to turn categories off. No LLM calls.

### Key features

#### 1. Timestamp tracking
- Timestamps on user messages and tool results
- Temporal context for multi-day style scenarios
- Optional simulated delays

#### 2. Tool call counter
- Counts calls per tool
- Helps prevent infinite loops / repetition
- Surfaces call number in tool responses (e.g. `Tool call #3 for 'read_file'`)

#### 3. TODO list management
- Task tracking with rules in the system prompt
- States: pending, in_progress, completed, cancelled
- Persistent rewrite/update across the conversation
- Agent auto-creates TODOs for complex (3+ step) tasks

#### 4. Detailed error messages
- Error type, arguments, traceback (verbose mode)
- Fix suggestions
- Helps the Agent adapt after failures

#### 5. System state awareness
- Current directory, shell, system info
- Updates as the Agent navigates
- Context for command execution

#### 6. Automatic trajectory saving
- Full history/state to `trajectory.json` each iteration
- Survives failed runs
- Includes history, tool calls, TODOs, config
- Analyze with `view_trajectory.py`

### Quick start

```bash
cd chapter2/system-hint
pip install -r requirements.txt
cp env.example .env
# Edit .env with your KIMI_API_KEY
export KIMI_API_KEY='your-api-key-here'
```

> **OpenRouter fallback:** If `KIMI_API_KEY` is unset but `OPENROUTER_API_KEY` is set, the experiment uses OpenRouter (`kimi-*` → `moonshotai/kimi-k2`). With `KIMI_API_KEY` set, behavior is unchanged.

#### Basic usage

```bash
# Offline status-bar preview (no API key)
python main.py --mode preview

# Interactive mode (default)
python main.py

# Sample task (analyze week1/week2 projects)
python main.py --mode sample

# Single task from CLI
python main.py --mode single --task "Create a hello world Python script"

# Provider / model / trajectory path
python main.py --mode single --task "..." --provider kimi --model kimi-k3 --output run1.json

# Demos
python main.py --mode demo --demo basic
python main.py --mode demo --demo loop
python main.py --mode demo --demo comparison

# Disable features (preview or live)
python main.py --mode single --no-todo --no-timestamps --task "Simple task"
python main.py --mode preview --no-todo --no-timestamps

python quickstart.py
python view_trajectory.py
python view_trajectory.py path/to/trajectory.json
```

#### Programmatic usage

```python
from agent import SystemHintAgent, SystemHintConfig

config = SystemHintConfig(
    enable_timestamps=True,
    enable_tool_counter=True,
    enable_todo_list=True,
    enable_detailed_errors=True,
    enable_system_state=True,
    save_trajectory=True,
    trajectory_file="my_trajectory.json"
)

agent = SystemHintAgent(
    api_key="your-api-key",
    provider="kimi",
    config=config,
    verbose=False
)

task = "Create a Python script that analyzes CSV files"
result = agent.execute_task(task, max_iterations=20)

print(f"Success: {result['success']}")
print(f"Final answer: {result['final_answer']}")
print(f"Trajectory saved to: {result['trajectory_file']}")
```

### Project structure

```
system-hint/
├── agent.py          # Agent with system hints
├── main.py           # CLI (multiple modes)
├── config.py         # Configuration
├── quickstart.py     # Quick demo
├── test_basic.py
├── test_hint_behavior.py
├── view_trajectory.py
├── requirements.txt
├── env.example
├── trajectory.json   # Created at runtime
├── CHANGELOG.md
├── NOTES.md
└── README.md
```

### How system hints work

Hints are **temporary user messages** added before each LLM call. They are **not** stored in conversation history, so they avoid permanent context pollution while still supplying state.

Example:

```python
# System hint example (added as user message before LLM call):
=== SYSTEM STATE ===
Current Time: 2024-12-13 10:30:45
Current Directory: /home/user/projects
System: Linux (5.15.0)
Shell Environment: Linux Shell (bash)
Python Version: 3.10.0

=== CURRENT TASKS ===
TODO List:
  [1] 🔄 Read configuration file (in_progress)
  [2] ⏳ Process data (pending)
  [3] ✅ Initialize environment (completed)
```

The system prompt also includes management rules: auto TODO for complex tasks, only one `in_progress` at a time, tool-call awareness, error recovery patterns.

### Configuration (`SystemHintConfig`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enable_timestamps` | `True` | Add timestamps to messages |
| `enable_tool_counter` | `True` | Track tool call counts |
| `enable_todo_list` | `True` | TODO list management |
| `enable_detailed_errors` | `True` | Detailed error info |
| `enable_system_state` | `True` | System state tracking |
| `timestamp_format` | `"%Y-%m-%d %H:%M:%S"` | Timestamp format |
| `simulate_time_delay` | `False` | Simulate time passing (demo) |
| `save_trajectory` | `True` | Save trajectory to file |
| `trajectory_file` | `"trajectory.json"` | Trajectory output path |

### Demonstrations

```bash
python main.py --mode preview                          # offline before/after
python main.py --mode demo --demo basic                # all hints together
python main.py --mode demo --demo loop                 # loop prevention via counter
python main.py --mode demo --demo comparison           # with vs without hints
```

### Sample tasks

1. Project analysis (week1/week2 style)
2. File operations
3. Code generation
4. System commands

### Analyzing results

```bash
python view_trajectory.py
# iterations, tool stats, TODO progress, highlights, config
```

Metrics: iterations, tool success/fail, TODO completion, time (if timestamps), final success.

### Testing

```bash
python test_basic.py
```

### Troubleshooting

1. **API key not set:** `export KIMI_API_KEY='your-api-key-here'`
2. **Tool loops:** enable `enable_tool_counter=True`
3. **Lost context:** enable timestamps + system state
4. **Task management:** enable TODO list

### Notes

- Hints are temporary user messages, not stored in history
- Trajectories capture full execution for debugging
- TODOs keep multi-step focus
- Counters reduce infinite loops
- Detailed errors help self-correction

---

## 中文

### 概述

对应书中 **实验 2-8：几种好用的 Agent 状态栏技术**（「Agent 状态栏 / Agent Status Bar」一节）。本目录即书中所说的 `agent-status-bar` 实验框架——「system hint（系统提示）」与「Agent 状态栏（status bar）」是同一概念的两种叫法：在上下文末尾以一条 `role=user` 的消息注入动态状态摘要。

本实验演示如何用系统提示改善 Agent 轨迹、减少无限循环、上下文感知不足与任务管理混乱，并自动保存轨迹便于调试。

### 先跑离线预览（无需 API Key）

想在不配置任何 API Key 的情况下直观看到状态栏如何改变模型看到的上下文：

```bash
python main.py --mode preview
```

该命令在本地渲染书中五种状态栏技术（时间戳、工具调用计数器、TODO 列表、详细错误信息、系统状态感知），对每一项做一次 **「无状态栏 vs 有状态栏」** 的前后对比，并打印最终追加到上下文末尾的完整状态栏消息。配合 `--no-timestamps` / `--no-counter` / `--no-todo` / `--no-errors` / `--no-state` 可分别关闭某一类。整个过程不发起任何 LLM 调用。

### 核心功能

#### 1. 时间戳跟踪
- 为用户消息与工具结果添加时间戳
- 帮助 Agent 理解时间上下文
- 可模拟时间流逝以演示多日场景

#### 2. 工具调用计数器
- 统计每个工具被调用次数
- 抑制无限循环与重复行为
- 在工具响应中展示调用序号（如 `Tool call #3 for 'read_file'`）

#### 3. TODO 列表管理
- 系统提示中带任务管理规则
- 四态：pending、in_progress、completed、cancelled
- 对话中可重写与更新
- 复杂任务（3 步以上）自动建 TODO

#### 4. 详细错误信息
- 错误类型、参数、堆栈（verbose）
- 修复建议
- 帮助 Agent 从失败中调整策略

#### 5. 系统状态感知
- 当前目录、Shell、系统信息
- 随文件系统导航动态更新
- 为命令执行提供上下文

#### 6. 自动轨迹保存
- 每轮将完整对话与状态写入 `trajectory.json`
- 执行失败也能保留调试信息
- 含历史、工具调用、TODO、配置
- 用 `view_trajectory.py` 分析

### 快速开始

```bash
cd chapter2/system-hint
pip install -r requirements.txt
cp env.example .env
# 编辑 .env，填入 KIMI_API_KEY
export KIMI_API_KEY='your-api-key-here'
```

> **通用回退（OpenRouter）**：未设置 `KIMI_API_KEY` 时，只要配置了 `OPENROUTER_API_KEY`，实验会自动改走 OpenRouter（`kimi-*` 会映射为 `moonshotai/kimi-k2`）。设置了 `KIMI_API_KEY` 时行为完全不变。

#### 基本用法

```bash
python main.py --mode preview
python main.py
python main.py --mode sample
python main.py --mode single --task "Create a hello world Python script"
python main.py --mode single --task "..." --provider kimi --model kimi-k3 --output run1.json
python main.py --mode demo --demo basic
python main.py --mode demo --demo loop
python main.py --mode demo --demo comparison
python main.py --mode single --no-todo --no-timestamps --task "Simple task"
python main.py --mode preview --no-todo --no-timestamps
python quickstart.py
python view_trajectory.py
python view_trajectory.py path/to/trajectory.json
```

#### 编程方式

```python
from agent import SystemHintAgent, SystemHintConfig

config = SystemHintConfig(
    enable_timestamps=True,
    enable_tool_counter=True,
    enable_todo_list=True,
    enable_detailed_errors=True,
    enable_system_state=True,
    save_trajectory=True,
    trajectory_file="my_trajectory.json"
)

agent = SystemHintAgent(
    api_key="your-api-key",
    provider="kimi",
    config=config,
    verbose=False
)

task = "Create a Python script that analyzes CSV files"
result = agent.execute_task(task, max_iterations=20)

print(f"Success: {result['success']}")
print(f"Final answer: {result['final_answer']}")
print(f"Trajectory saved to: {result['trajectory_file']}")
```

### 项目结构

```
system-hint/
├── agent.py          # 带 system hint 的 Agent 实现
├── main.py           # 多模式 CLI
├── config.py         # 配置管理
├── quickstart.py     # 快速演示
├── test_basic.py
├── test_hint_behavior.py
├── view_trajectory.py
├── requirements.txt
├── env.example
├── trajectory.json   # 运行时生成
├── CHANGELOG.md
├── NOTES.md
└── README.md
```

### System Hint 如何工作

System hint 是在发给 LLM **之前**以临时 **user 消息**注入的上下文信息，**不**写入对话历史，避免永久污染上下文，同时提供关键状态。

示例见英文节。系统提示中还包含 TODO 管理、错误处理与工具使用规则：复杂任务自动建 TODO、同时只有一个 `in_progress`、关注工具调用次数、错误恢复策略等。

### 配置项（`SystemHintConfig`）

| 参数 | 默认 | 说明 |
|------|------|------|
| `enable_timestamps` | `True` | 为消息添加时间戳 |
| `enable_tool_counter` | `True` | 跟踪工具调用次数 |
| `enable_todo_list` | `True` | 启用 TODO 管理 |
| `enable_detailed_errors` | `True` | 提供详细错误信息 |
| `enable_system_state` | `True` | 跟踪系统状态 |
| `timestamp_format` | `"%Y-%m-%d %H:%M:%S"` | 时间戳格式 |
| `simulate_time_delay` | `False` | 模拟时间流逝（演示） |
| `save_trajectory` | `True` | 保存轨迹到文件 |
| `trajectory_file` | `"trajectory.json"` | 轨迹输出路径 |

### 演示

```bash
python main.py --mode preview
python main.py --mode demo --demo basic
python main.py --mode demo --demo loop
python main.py --mode demo --demo comparison
```

### 示例任务

1. 项目分析（week1/week2 风格）
2. 文件操作
3. 代码生成
4. 系统命令

### 结果分析

```bash
python view_trajectory.py
# 迭代次数、工具统计、TODO 进度、对话亮点、配置
```

跟踪指标：迭代数、工具成功/失败、TODO 完成情况、耗时（若启用时间戳）、最终成败。

### 测试

```bash
python test_basic.py
```

### 故障排除

1. **未设置 API Key：** `export KIMI_API_KEY='your-api-key-here'`
2. **工具调用循环：** 启用 `enable_tool_counter=True`
3. **上下文丢失：** 启用时间戳与系统状态
4. **任务管理混乱：** 启用 TODO 列表

### 说明

- System hint 以临时 user 消息注入，不写入历史
- 轨迹文件保留完整执行状态便于调试
- TODO 帮助多步任务保持焦点
- 工具计数器自动抑制无限循环
- 带建议的详细错误帮助自我纠正

---

## Notes / 说明

- “System hint” and “Agent status bar” refer to the same mechanism in this lab.  
- 本实验中「System hint」与「Agent 状态栏」指同一机制。
