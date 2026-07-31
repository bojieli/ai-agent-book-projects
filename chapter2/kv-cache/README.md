# KV Cache Demonstration / KV Cache 与错误上下文管理模式

> Companion material for *AI Agents in Depth*, Chapter 2 — **Experiment 2-3 ★★: Common but harmful context management patterns**.  
> 配套《深入理解 AI Agent》第 2 章 **实验 2-3 ★★：常见的错误上下文管理模式**。

← [Chapter 2 index / 返回第 2 章目录](../README.md)

---

## English

### Overview

A ReAct agent with local filesystem tools that shows how **KV (Key-Value) cache** utilization changes under six implementation patterns—one correct and five incorrect. Small-looking changes can invalidate cache and hurt latency and cost.

Default model: Moonshot Kimi family (default `kimi-k2.6`), OpenAI tool-calling format.

> **Model note.** On the live Moonshot endpoint the current Kimi family (`kimi-k2.5` / `kimi-k2.6` / `kimi-k2.7*` / `kimi-k3`) are *reasoning* models: they emit `reasoning_content` and only accept `temperature=1` (handled automatically). They **do** report `cached_tokens`, which this experiment measures. Legacy non-reasoning `moonshot-v1-*` models do **not** report `cached_tokens`, so they cannot demonstrate the cache effect. Default `kimi-k2.6` reports cache hits with a lighter reasoning footprint (less noisy TTFT). Prefer **cache hit rate / cache ratio** as the robust signal; treat TTFT as secondary.

#### What is KV Cache?

KV cache stores attention key-value pairs. When conversation context stays stable, cached values can be reused, cutting compute and improving TTFT (Time to First Token).

### Features

- ReAct agent with standard OpenAI tool calling
- Safe local tools: `read_file`, `find`, `grep`
- Robust error handling (tool failures become results)
- Six modes: correct + five anti-patterns
- Metrics: TTFT, total time, cache hits/misses, tokens
- Offline comparison report (`--report`) from saved JSON—no API key
- Cost illustration via `--cache-price-ratio`
- Detailed logging and smart completion (no tool call → final answer)

### Implementation modes

#### 1. Correct (`correct`)
Stable context: fixed system prompt, consistent tool order, stable message format, no unnecessary context churn.

#### 2. Dynamic system prompt (`dynamic_system`)
Adds a timestamp to the system prompt every request → full context recreated → cache invalidation, higher TTFT.

#### 3. Shuffled tools (`shuffled_tools`)
Random tool order each request → cache break despite identical functionality.

#### 4. Dynamic user profile (`dynamic_profile`)
Changing user credits in context each iteration → invalidation for irrelevant dynamics (common production anti-pattern).

#### 5. Sliding window (`sliding_window`)
Keeps only the last 5 messages → appears shorter but breaks cache continuity; truncation can backfire.

#### 6. Text format (`text_format`)
History as plain text instead of structured messages → breaks expected format and cache use.

### Critical implementation detail

For incorrect modes to properly invalidate KV cache, the **entire message list must be recreated at the start of each iteration**.

1. **CORRECT:** build messages once; keep appending assistant/tool messages to the same list → stable prefix → cache works.
2. **Incorrect modes:** rebuild the full messages list from history at each iteration start (still append tool results *within* an iteration for API correctness) → next turn starts from a recreated list → cache invalidates.

Both modes append tool results within an iteration so the API sees a complete turn. The difference is whether the list is thrown away and rebuilt at the next iteration boundary.

### Installation

```bash
# From the repository root: use the shared Chapter 2 environment
uv sync --locked --python 3.12 --extra ch2

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch2]"

cd chapter2/kv-cache

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

cp env.example .env                  # edit .env with your key
# Or export MOONSHOT_API_KEY="your-api-key-here"
```

> **OpenRouter fallback:** If `MOONSHOT_API_KEY` / `KIMI_API_KEY` is unset but `OPENROUTER_API_KEY` is set, the experiment uses OpenRouter (`kimi-*` → `moonshotai/kimi-k2`). With a Moonshot key set, behavior is unchanged.

### Usage

#### Interactive mode (default)

```bash
python main.py
# Menu: 1–6 modes, 7 Compare All, 0 Exit
```

#### CLI flags

Chinese `--help`: `python main.py --help`. Key flags:

| Flag | Description |
|------|-------------|
| `--mode MODE` | One strategy: correct / dynamic_system / shuffled_tools / dynamic_profile / sliding_window / text_format |
| `--compare` | Run all strategies and print comparison table (needs API key) |
| `--report` | **Offline:** build comparison table from saved `result_*.json` / `comparison_*.json` (**no API key**) |
| `--input ...` | With `--report`: files / globs / dirs (default: scan cwd) |
| `--model MODEL` | Default `kimi-k2.6` (family models that report `cached_tokens` also work) |
| `--output PATH` | Result JSON path (default: mode + timestamp) |
| `--cache-price-ratio R` | Assumed bill ratio for cached tokens (default `0.1`); illustration only |
| `--task`, `--root-dir` | Custom task / filesystem tool root |

```bash
python main.py --mode correct
python main.py --mode sliding_window --model kimi-k2.6 --output run.json
python main.py --compare
python main.py --no-interactive --mode correct
```

#### Offline comparison report (no API key)

```bash
# Uses result_*.json already in this directory
python main.py --report

python main.py --report --input result_correct_*.json result_text_format_*.json
python main.py --report --cache-price-ratio 0.5
```

The table compares cache hit rate, cache ratio, TTFT, total time, and illustrative billable-token / savings. Supports legacy `AgentMetrics(...)` string metrics and newer dict-format files.

> `Bill.Tok` / `Save%` are a transparent function of *measured* tokens and `--cache-price-ratio`—an illustration, not a provider quote.

#### Custom tasks

```bash
python main.py --mode correct --task "Read all README files and summarize their contents"
python main.py --mode correct --root-dir ../.. --task "Analyze the project structure"
```

### Tests and manual checks

Offline regressions live under `tests/` and do not require API keys:

```bash
uv sync --locked --python 3.12 --extra ch2 --extra dev
source .venv/bin/activate
cd chapter2/kv-cache
python -m pytest tests
```

Live smoke checks and demonstrations live under `tests/manual/`. They are not
collected by pytest because their filenames use `check_*.py` or `demo_*.py`:

```bash
MOONSHOT_API_KEY="your-key" python tests/manual/demo_quick.py
MOONSHOT_API_KEY="your-key" python tests/manual/check_tool_calling.py
MOONSHOT_API_KEY="your-key" python tests/manual/check_cache_invalidation.py
MOONSHOT_API_KEY="your-key" python tests/manual/check_agent_error_recovery.py
```

### Metrics

**Performance:** TTFT (per iteration; cold start vs with cache), average TTFT, improvement %, total time, iterations, tool calls.

**Cache:** cached tokens, hits, misses, hit rate.

**Tokens:** prompt / completion tokens; **cache ratio** = share of prompt tokens served from cache.

### Expected results

1. **Correct:** after the first iteration, cached tokens appear; steady TTFT; stable prefix served from cache.
2. **Incorrect:** collapsing **cache ratio** (e.g. shuffled tools can drop ratio to ~1/3 of correct); higher TTFT (text_format / shuffle can more than double first-token latency); longer total time (up to ~2.4× for `text_format` in measured runs).

> On reasoning models TTFT has extra variance from hidden thinking—**cache ratio** is the cleanest evidence. Appending dynamic data at the *end* of an otherwise-stable prefix (`dynamic_system` / `dynamic_profile`) only invalidates *from that point*—base prefix may still cache, so headline cache ratio can look close to `correct` while total time still regresses. Keep dynamic data out of the prefix entirely.

### Example output

```
📊 Performance Metrics:
  • Time to First Token (TTFT): 0.823 seconds
  • TTFT per iteration:
      Iteration 1: 0.823s
      Iteration 2: 0.234s (with cache)
      ...
  • TTFT Analysis:
      First iteration: 0.823s
      Last iteration: 0.192s
      Average (after first): 0.203s
      Improvement: 76.7%
```

### Comparison table (`--report` on saved results)

Real numbers from one `--compare` run (`kimi-k2.6`, root = this folder, task = find Python files / read `main.py` + `agent.py` / summarize in 3 sentences), then `python main.py --report`:

```
Mode             Iters  1st TTFT   Avg TTFT   Total(s)   Prompt    Cached    Hit%    Cache%   Bill.Tok   Save%
----------------------------------------------------------------------------------------------------------------
correct          3      2.328      6.054      18.163     7,567     768       100.0   10.1     6,876      9.1
dynamic_profile  3      2.206      5.986      17.962     7,652     768       100.0   10.0     6,961      9.0
dynamic_system   3      2.497      8.085      24.260     7,639     768       100.0   10.1     6,948      9.0
shuffled_tools   3      7.818      11.122     33.369     7,568     256       100.0   3.4      7,338      3.0
sliding_window   5      2.234      3.649      14.704     2,224     1,510     100.0   67.9     865        61.1
text_format      3      6.189      14.432     43.297     7,430     674       100.0   9.1      6,823      8.2
```

Reading: `shuffled_tools` reorders tool definitions near the front of the prefix → **cache ratio 10.1% → 3.4%**, first TTFT ~2.3s → ~7.8s. `text_format` ~**2.4×** correct total time. `sliding_window` high ratio only because the prompt is truncated (high ratio on a tiny prompt ≠ efficient run).

`Cache%` = share of prompt tokens from cache; `Hit%` = share of *iterations* with any cache. Regenerate with `python main.py --compare`.

### Key insights

1. Stable context is critical  
2. Order matters (even reordering identical content breaks cache)  
3. Avoid dynamic metadata in the prefix  
4. Use the API’s structured message format  
5. Full history often beats aggressive truncation for cache  

### Architecture

```
kv-cache/
├── agent.py                # ReAct agent + modes
├── main.py                 # Experiment runner CLI
├── tests/                  # offline pytest regressions
│   └── manual/             # live/API smoke checks, not collected by pytest
├── requirements.txt
├── README.md
├── result_*.json           # retained receipts for offline --report
└── kv_cache_demo.log
```

**Components:** `KVCacheAgent`, `LocalFileTools`, `KVCacheMode`, `AgentMetrics`.

**Error handling:** tool/arg errors returned as results; continue on failure; deny paths outside root.

### Advanced configuration

```bash
export MOONSHOT_API_KEY="your-key"
export LOG_LEVEL="DEBUG"  # INFO, WARNING, ERROR
```

Extend `KVCacheMode` in `agent.py` and implement `_get_system_prompt()` / `_get_tools()` / `_format_messages()`.

### Best practices

1. Keep system prompts stable  
2. Keep tool order fixed  
3. Avoid counters/credits/timestamps in the prefix  
4. Use proper message structure  
5. Prefer continuity over aggressive truncation  
6. Design context with caching in mind  

### Troubleshooting

- **High TTFT in correct mode:** first request cold start; check key/network/model  
- **Zero cache hits:** use current Kimi models that report `cached_tokens` (not `moonshot-v1-*`); verify context stability  
- **Tool errors:** permissions, paths within root, files exist  

### References

- [Kimi API Documentation](https://platform.moonshot.cn/docs/api-reference)
- [ReAct Pattern Paper](https://arxiv.org/abs/2210.03629)
- [Transformer KV Cache Explanation](https://huggingface.co/docs/transformers/kv_cache)

---

## 中文

### 概述

用带本地文件系统工具的 ReAct Agent，展示 **KV（Key-Value）Cache** 在六种实现模式（一种正确、五种错误）下的利用率差异。看似无害的改动可能让缓存失效，显著拖慢延迟并推高成本。

默认模型：Moonshot Kimi 系列（默认 `kimi-k2.6`），标准 OpenAI 工具调用格式。

> **模型说明。** 线上 Moonshot 当前 Kimi 族（`kimi-k2.5` / `kimi-k2.6` / `kimi-k2.7*` / `kimi-k3`）均为*推理*模型：会吐 `reasoning_content`，且只接受 `temperature=1`（代码已自动处理）。它们**会上报** `cached_tokens`，本实验正依赖此指标。旧版非推理 `moonshot-v1-*` **不上报** `cached_tokens`，无法展示缓存效应。默认 `kimi-k2.6` 能报缓存命中且推理开销较轻（TTFT 噪声更小）。请以 **缓存命中率 / 缓存比例** 为稳健信号，TTFT 作辅助。

#### 什么是 KV Cache？

KV Cache 存储注意力机制中的键值对。对话上下文稳定时，可复用这些缓存值，显著减少计算并改善 TTFT（首 token 延迟）。

### 功能

- ReAct Agent + 标准 OpenAI 工具调用
- 安全本地工具：`read_file`、`find`、`grep`
- 工具失败以结果回传并继续执行
- 六种模式：正确 + 五种反模式
- 指标：TTFT、总时间、缓存命中/未命中、token
- 离线对比报告（`--report`）从已保存 JSON 生成——无需 API Key
- 通过 `--cache-price-ratio` 做成本示意
- 详细日志与智能收尾（无工具调用即视为最终答案）

### 实现模式

#### 1. 正确实现（`correct`）
全程稳定上下文：固定系统提示、一致工具顺序、稳定消息格式、无无谓上下文改动。

#### 2. 动态系统提示（`dynamic_system`）
每次请求在系统提示中加时间戳 → 整表重建 → 缓存失效、TTFT 上升。

#### 3. 打乱工具列表（`shuffled_tools`）
每次随机工具顺序 → 功能相同仍破坏缓存。

#### 4. 动态用户资料（`dynamic_profile`）
每轮把变化的用户额度塞进上下文 → 无关动态导致失效（常见生产反模式）。

#### 5. 滑动窗口（`sliding_window`）
只保留最近 5 条消息 → 看似更短，实则打断缓存连续性。

#### 6. 纯文本格式（`text_format`）
历史写成纯文本而非结构化消息 → 破坏约定格式与缓存。

### 关键实现细节

错误模式要**真正**使 KV Cache 失效，必须在**每一轮迭代开始时**整表重建 messages。

1. **CORRECT：** 首次构建 messages，之后只在同一列表上追加 assistant/tool → 前缀稳定 → 缓存生效。  
2. **错误模式：** 每轮开始从对话历史重建整个 messages（轮内仍追加 tool 结果以保证 API 流正确）→ 下一轮从新列表开始 → 缓存失效。

两模式在轮内都会追加 tool 结果；差异在于下一轮是否丢弃并重建列表。

### 安装

```bash
# 在仓库根目录使用统一的第 2 章环境
uv sync --locked --python 3.12 --extra ch2

# 切换目录前先激活环境：
# macOS/Linux：
source .venv/bin/activate
# Windows PowerShell：.venv\Scripts\Activate.ps1
# Windows cmd：.venv\Scripts\activate.bat

# 未安装 uv 时可用 pip 兜底：
# python -m pip install -e ".[ch2]"

cd chapter2/kv-cache

# 迁移期间仍支持单项目兼容路径：
# python -m pip install -r requirements.txt

cp env.example .env                  # 编辑 .env，填入 API Key
# 或 export MOONSHOT_API_KEY="your-api-key-here"
```

> **通用回退（OpenRouter）**：未设置 `MOONSHOT_API_KEY` / `KIMI_API_KEY` 时，只要配置了 `OPENROUTER_API_KEY`，实验会自动改走 OpenRouter（`kimi-*` 会映射为 `moonshotai/kimi-k2`）。设置了 Moonshot key 时行为完全不变。

### 用法

#### 交互模式（默认）

```bash
python main.py
# 菜单：1–6 模式，7 全部对比，0 退出
```

#### 命令行参数

中文 `--help`：`python main.py --help`。主要参数：

| 参数 | 说明 |
|------|------|
| `--mode MODE` | 单个策略（correct / dynamic_system / shuffled_tools / dynamic_profile / sliding_window / text_format） |
| `--compare` | 依次运行全部策略并打印横向对比表（需要 API Key） |
| `--report` | **离线**：从已保存的 `result_*.json` / `comparison_*.json` 生成对比表，**无需 API Key** |
| `--input ...` | 配合 `--report` 指定结果文件 / 通配符 / 目录（默认扫描当前目录） |
| `--model MODEL` | 默认 `kimi-k2.6`（会上报 `cached_tokens` 的同族模型亦可） |
| `--output PATH` | 结果 JSON 路径（默认按模式 + 时间戳命名） |
| `--cache-price-ratio R` | 缓存 token 相对正常 token 的计费比例示意（默认 `0.1`） |
| `--task`, `--root-dir` | 自定义任务 / 文件工具根目录 |

```bash
python main.py --mode correct
python main.py --mode sliding_window --model kimi-k2.6 --output run.json
python main.py --compare
python main.py --no-interactive --mode correct
```

#### 离线对比报告（无需 API Key）

```bash
python main.py --report
python main.py --report --input result_correct_*.json result_text_format_*.json
python main.py --report --cache-price-ratio 0.5
```

对比表包含缓存命中率、缓存比例、TTFT、总时间，以及示意性的可计费 token / 节省比例。兼容旧版 `AgentMetrics(...)` 字符串指标与新版 dict 格式。

> `Bill.Tok` / `Save%` 是实测 token 与 `--cache-price-ratio` 的透明函数——仅作成本示意，非某一厂商报价。

#### 自定义任务

```bash
python main.py --mode correct --task "Read all README files and summarize their contents"
python main.py --mode correct --root-dir ../.. --task "Analyze the project structure"
```

### 测试与手动检查

离线回归测试位于 `tests/`，不需要 API Key：

```bash
uv sync --locked --python 3.12 --extra ch2 --extra dev
source .venv/bin/activate
cd chapter2/kv-cache
python -m pytest tests
```

需要真实 API 的冒烟脚本和演示位于 `tests/manual/`。这些文件使用
`check_*.py` 或 `demo_*.py` 命名，因此不会被 pytest 默认收集：

```bash
MOONSHOT_API_KEY="your-key" python tests/manual/demo_quick.py
MOONSHOT_API_KEY="your-key" python tests/manual/check_tool_calling.py
MOONSHOT_API_KEY="your-key" python tests/manual/check_cache_invalidation.py
MOONSHOT_API_KEY="your-key" python tests/manual/check_agent_error_recovery.py
```

### 指标说明

**性能：** TTFT（按迭代；冷启动 vs 有缓存）、平均 TTFT、改善百分比、总时间、迭代次数、工具调用次数。

**缓存：** 缓存 token、命中、未命中、命中率。

**Token：** 提示 / 补全 token；**缓存比例** = 来自缓存的 prompt token 占比。

### 预期结果

1. **正确实现：** 第一轮之后上报缓存 token；TTFT 更稳；稳定前缀由缓存服务。  
2. **错误实现：** **缓存比例**崩塌（如打乱工具可将比例降到正确模式约 1/3）；TTFT 更高（text_format / 打乱工具可让首 token 延迟翻倍以上）；总时间更长（实测 `text_format` 可达约 2.4×）。

> 推理模型上 TTFT 因隐藏思考 token 方差更大——**缓存比例**是最干净的证据。把动态数据接在**已稳定前缀末尾**（`dynamic_system` / `dynamic_profile`）只会从改动点起失效——前缀前半仍可能命中，因此标题缓存比例可能接近 `correct`，但总时间仍变差。教训：动态数据不要进入前缀。

### 示例输出

```
📊 Performance Metrics:
  • Time to First Token (TTFT): 0.823 seconds
  • TTFT per iteration:
      Iteration 1: 0.823s
      Iteration 2: 0.234s (with cache)
      ...
  • TTFT Analysis:
      First iteration: 0.823s
      Last iteration: 0.192s
      Average (after first): 0.203s
      Improvement: 76.7%
```

### 对比表（对本目录已保存结果执行 `--report`）

一次 `--compare` 真实测得（`kimi-k2.6`，根目录为本文件夹，任务为查找 Python 文件 / 读 `main.py` + `agent.py` / 用 3 句话总结），再 `python main.py --report`：

```
Mode             Iters  1st TTFT   Avg TTFT   Total(s)   Prompt    Cached    Hit%    Cache%   Bill.Tok   Save%
----------------------------------------------------------------------------------------------------------------
correct          3      2.328      6.054      18.163     7,567     768       100.0   10.1     6,876      9.1
dynamic_profile  3      2.206      5.986      17.962     7,652     768       100.0   10.0     6,961      9.0
dynamic_system   3      2.497      8.085      24.260     7,639     768       100.0   10.1     6,948      9.0
shuffled_tools   3      7.818      11.122     33.369     7,568     256       100.0   3.4      7,338      3.0
sliding_window   5      2.234      3.649      14.704     2,224     1,510     100.0   67.9     865        61.1
text_format      3      6.189      14.432     43.297     7,430     674       100.0   9.1      6,823      8.2
```

解读：`shuffled_tools` 打乱靠前的工具定义 → **缓存比例 10.1% → 3.4%**，首 TTFT 约 2.3s → 7.8s。`text_format` 总时间约 **2.4×**。`sliding_window` 高比例只因提示词被截断（小提示词上的高比例 ≠ 高效运行）。

`Cache%` = 来自缓存的 prompt token 占比；`Hit%` = 出现任意缓存的*迭代*占比。用 `python main.py --compare` 重跑复现。

### 关键洞察

1. 稳定上下文至关重要  
2. 顺序也重要（相同内容重排也会破缓存）  
3. 前缀中避免动态元数据  
4. 使用 API 期望的结构化消息格式  
5. 完整历史往往比激进截断更利于缓存  

### 架构

```
kv-cache/
├── agent.py                # ReAct Agent + 各模式
├── main.py                 # 实验入口 CLI
├── tests/                  # 离线 pytest 回归测试
│   └── manual/             # 真实 API 冒烟脚本，不被 pytest 收集
├── requirements.txt
├── README.md
├── result_*.json           # 支持离线 --report 的保留结果
└── kv_cache_demo.log
```

**组件：** `KVCacheAgent`、`LocalFileTools`、`KVCacheMode`、`AgentMetrics`。

**错误处理：** 工具/参数错误以结果回传；失败后继续；拒绝根目录外访问。

### 进阶配置

```bash
export MOONSHOT_API_KEY="your-key"
export LOG_LEVEL="DEBUG"  # INFO, WARNING, ERROR
```

可在 `agent.py` 扩展 `KVCacheMode`，并实现 `_get_system_prompt()` / `_get_tools()` / `_format_messages()`。

### KV Cache 最佳实践

1. 系统提示保持稳定  
2. 工具顺序固定  
3. 前缀中避免计数器/额度/时间戳  
4. 使用正确的消息结构  
5. 优先保持连续性，慎用激进截断  
6. 从设计上考虑缓存友好  

### 故障排除

- **正确模式 TTFT 仍高：** 首请求冷启动；检查 key / 网络 / 模型  
- **缓存命中为零：** 使用会上报 `cached_tokens` 的当前 Kimi 模型（非 `moonshot-v1-*`）；确认上下文确实稳定  
- **工具执行错误：** 权限、路径在 root 内、文件可读  

### 参考

- [Kimi API Documentation](https://platform.moonshot.cn/docs/api-reference)
- [ReAct Pattern Paper](https://arxiv.org/abs/2210.03629)
- [Transformer KV Cache Explanation](https://huggingface.co/docs/transformers/kv_cache)

---

## Notes / 说明

- Saved `result_*.json` in this directory enable offline `--report` without spending API quota.  
- 本目录随附的 `result_*.json` 支持离线 `--report`，无需消耗 API 额度。
