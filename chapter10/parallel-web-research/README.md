## English

# Experiment 10-6 · Agent Collecting Information from Multiple Websites Simultaneously (★★)

A companion experiment for *Deep Understanding of AI Agents*. Demonstrates **parallel search with multiple homogeneous agents + central coordination**:
The main coordinator simultaneously launches N child agents, each accessing one "website/source" to find an answer;
once any child agent hits the target, the rest gracefully stop.

The prototype in the book is "10 parallel Computer Use Agents accessing different websites simultaneously to find information." For ease of
automated verification, this experiment **does not launch a real browser** but instead uses a set of **controllable simulated information sources**;
the focus is entirely on the coordination mechanism — **message bus, parallel dispatch, real-time monitoring, cascading termination, and race condition handling are all real implementations**.

## Directory Structure

| File | Role |
| --- | --- |
| `message_bus.py` | In-process asynchronous message bus (Redis Pub/Sub style), with `Envelope` envelope and subscription mechanism |
| `sources.py` | Simulated 10 "websites/sources", each with different delays; controllable keyword hit determination; `build_sources(n)` supports arbitrary parallelism |
| `llm.py` | Optional LLM judgment layer (default offline keyword judgment, uses real LLM if key is configured) |
| `agents.py` | Main coordinator `Coordinator` and child agent `WorkerAgent` (core coordination logic); `run_sequential` serial baseline |
| `demo.py` | Single-command demo entry point, with argparse CLI and assertion-based self-check at the end |

## Architecture and Mechanism

```text
                         ┌────────────────────────────┐
                         │   Coordinator (Main Coordinator)  │
                         │  · Parallel dispatch task_assigned  │
                         │  · Maintain task state table (state machine)  │
                         │  · First hit → lock settlement (idempotent)  │
                         │  · Broadcast one round of terminate  │
                         └───────────┬────────────────┘
                                     │
                    ┌────────────────┴─────── MessageBus (Async Message Bus) ───────┐
                    │  Envelope{ sender_id, target, type, payload, seq, ts }    │
                    │  type: task_assigned/status_update/result/terminate/ack   │
                    └──┬─────────┬─────────┬─────────┬──────────────┬──────────┘
                       │         │         │         │              │
                    ┌──▼──┐  ┌──▼──┐  ┌──▼──┐  ┌──▼──┐   ...   ┌──▼──┐
                    │W-00 │  │W-01 │  │W-02 │  │W-03 │         │W-09 │  Child Agents
                    │Site A│  │Site B│  │Site C│  │Site D│         │Site J│  (Homogeneous · Parallel)
                    └─────┘  └─────┘  └─────┘  └─────┘         └─────┘
```

Corresponds to the five mechanisms emphasized in the book:

1. **Message Bus**: All communication is **enveloped messages** published to the bus, subscribed by `type`.
   Each `BUS ...` line in the log represents one publish/delivery (in-process implementation of Redis Pub/Sub semantics).
2. **Parallel Dispatch**: The `Coordinator` simultaneously sends `task_assigned` to 10 child agents and executes them concurrently via `asyncio.create_task`.
3. **Real-time Monitoring (push paradigm)**: Child agents proactively report progress via `status_update` during execution;
   the main agent maintains a **task state table** and refreshes the printout in real-time upon state machine transitions.
   State machine: `Submitted → Executing → (Input Required) → Completed / Failed / Terminated`.
4. **Cascading Termination**: Once a child agent hits the target, the main agent **broadcasts `terminate`**; other child agents,
   upon detecting the signal at their **safety checkpoints** in the loop, reply with `ack` and exit gracefully (state set to "Terminated").
5. **Race Condition Handling**: Multiple child agents may hit the target almost simultaneously; the main agent uses `asyncio.Lock` +
   an idempotent flag `_settled` to ensure **only one settlement and only one round of termination broadcast**; late hits are recorded and ignored.

> To make "race conditions" and "cascading termination" reproducible, each source is assigned a different simulated delay, where the two correct sources,
> `geo-journal` and `forum-qa`, are set to **the same delay**, thus reliably hitting the target at the same time and triggering a race condition.

## Running

```bash
cd chapter10/parallel-web-research
pip install -r requirements.txt   # Can be skipped for offline demo; pure standard library is sufficient
python demo.py
```

Default uses **offline keyword judgment** (no internet required, results reproducible). To have child agents use a real LLM for judgment:

```bash
cp env.example .env
# Fill in OPENAI_API_KEY in .env (also supports Moonshot / Volcano Ark ARK's OpenAI-compatible gateway)
python demo.py
# Or without modifying .env, use command-line switches directly (still requires key configuration to take effect):
python demo.py --use-llm --model gpt-5.6-luna
```

Available keys: `OPENAI_API_KEY` (default model `gpt-5.6-luna`) / `MOONSHOT_API_KEY` / `ARK_API_KEY`
(fill into `OPENAI_API_KEY` and set `OPENAI_BASE_URL` and `OPENAI_MODEL` as needed).

**General fallback**: If `OPENAI_API_KEY` is not set but `OPENROUTER_API_KEY` is, the real LLM judgment
automatically switches to OpenRouter and maps the model name to its namespace (`gpt-5.6-luna` → `openai/gpt-5.6-luna`).
This does not affect the coordination mechanism, only the "hit or miss" judgment.

### Command-Line Arguments

`python demo.py --help` shows the full help. All parameters **do not change the default behavior** — passing no arguments gives the original
"10 Agents + built-in question + offline reproducible + detailed BUS log" demo.

| Parameter | Role | Default |
| --- | --- | --- |
| `-q, --query QUESTION` | Research question (offline keyword judgment is tuned for built-in sources; custom questions generally require `--use-llm`) | Built-in question |
| `-n, --agents N` | Number of parallel child agents (when N≥2, always includes two sources with answers to reliably demonstrate race conditions/cascading termination) | `10` |
| `--model MODEL` | LLM model name (equivalent to setting `OPENAI_MODEL`, only effective with `--use-llm` and configured key) | Environment variable |
| `-o, --output PATH` | Write the conclusion (including parallel/serial wall-clock time, winner, race condition statistics) to a JSON file | Not written |
| `--compare` | After parallel run, **actually measure** the serial baseline and print wall-clock time comparison | Off |
| `--use-llm` | Force real LLM judgment (still requires `OPENAI_API_KEY` or `OPENROUTER_API_KEY`, otherwise automatically falls back to offline judgment) | Off |
| `--quiet` | Reduce per-message BUS logs (state table/conclusion/self-check unaffected) | Off |

```bash
python demo.py --agents 6 --compare       # 6 parallel agents, compare with serial wall-clock time
python demo.py --output result.json        # Write conclusion to JSON file
```

### Parallel vs Serial Wall-Clock Benefit (`--compare`)

Corresponds to the experiment requirement in the book "Record and compare parallel/serial time differences." `--compare` runs the **serial baseline**
(fetch one by one via `await source.fetch()` + judgment, stop on hit) with the **exact same source set** after the parallel demo; the time is **actually measured**, not estimated. Example output (default 10 sources, offline judgment):

```text
5) Parallel execution wall-clock time: 1.57s (including convergence quiet period)
------------------------------------------------------------------------------
Parallel vs Serial Wall-Clock Comparison (--compare, serial baseline is actual measurement)
------------------------------------------------------------------------------
   Serial: Fetched 3/10 sources sequentially before hit, wall-clock time 2.60s, winner=geo-journal
   Parallel: Wall-clock time 1.57s, winner=worker-02
   Speedup ≈ 1.66×, saving approximately 1.03s (parallelism lets the fastest source end the global search immediately).
```

Serial must sequentially fetch baike-wiki→news-portal before reaching the fastest hit, geo-journal (cumulative 2.6s); parallel starts all sources simultaneously, and the fastest source triggers cascading termination upon hit, immediately ending the global search. The parallel wall-clock time includes the convergence overhead of cascading termination, so it is not the ideal "first source latency," but it is still significantly faster than serial — this is the value of parallelism + cascading termination.

## What the Demo Illustrates (Key Output Snippets from Actual Run)

**(a) Message bus publish/subscribe is working** — each enveloped message is printed:

```text
BUS [t=  0.00s #3  ] coordinator -> worker-02   | task_assigned  | {"question": "...", "source": "geo-journal"}
BUS [t=  0.00s #13 ]   worker-02 -> coordinator | status_update  | {"state": "Executing", ...}
```

**(b) N child agents execute in parallel + main agent refreshes state table in real-time**:

```text
── Task State Table (worker-02 -> Executing) ──
   worker-00  source=baike-wiki   state=Executing   | Starting source fetch
   worker-02  source=geo-journal  state=Executing   | Starting source fetch
   ...
```

**(c) Cascading termination** — after hit, broadcast terminate, other child agents ack and exit gracefully:

```text
BUS [t=0.60s #41 ] coordinator -> ALL         | terminate | {"reason":"answer_found","winner":"worker-02"}
BUS [t=0.67s #43 ]   worker-09 -> coordinator | ack       | {"acked":"terminate","source":"map-service"}
[ack] worker-09 confirmed termination (1 acked)
...All 8 non-hitting Workers final state=Terminated
```

**(d) Race condition: even if hits occur almost simultaneously, only one settlement and one round of termination broadcast**:

```text
BUS [t=0.60s #37 ]   worker-02 -> coordinator | result | {"found":true, "answer":"...Mount Everest...8848 meters..."}
BUS [t=0.60s #38 ]   worker-04 -> coordinator | result | {"found":true, "answer":"...Mount Everest...8848.86 meters..."}
[Settlement] First hit from worker-02 — lock settlement, broadcast one round of terminate.
[Race] worker-04 also hit, but already settled by worker-02 — ignoring this hit, no repeated termination broadcast.
```

`demo.py` has an **assertion-based self-check** at the end: `terminate broadcast rounds == 1`, `only one settlement == True`,
`winner is not empty`. Passing proves the mechanism is correct:

```text
4) Terminate broadcast rounds: 1 (should be 1, proving only one round broadcast)
   Late/concurrent duplicate hits ignored: ['worker-04']
[Self-check passed] Single settlement + single round termination broadcast + cascading ack all meet expectations.
```

## Limitations and Notes

This experiment focuses on the **coordination mechanism** (message bus / parallel dispatch / cascading termination / race-condition handling), all of which are real implementations. However, to enable offline execution and automated verification, the following three aspects have been simplified, which are known limitations:

- **Limitation · Simulated source is not a real browser**: No real browser is launched; the source is controllable simulated data plus delays. To connect to a real Computer Use, simply replace the "fetch one step + judge" logic inside `WorkerAgent.run()` with real browser operations—the coordination layer requires no changes.
- **Limitation · Race conditions rely on identical delays for stable reproduction**: The two correct sources, `geo-journal` and `forum-qa`, are artificially set to the same delay to reliably trigger "simultaneous hits." In real environments, race conditions are sporadic, but the locking + idempotent settlement logic works equally well for sporadic races and does not depend on this artificial setting.
- **Limitation · In-process bus is not real Redis**: `MessageBus` uses an **in-process async queue** to simulate Redis Pub/Sub, eliminating the need for an actual Redis installation. The semantics (envelope, subscription by type, point-to-point/broadcast delivery) are consistent, but it lacks cross-process/cross-machine capability, making it convenient for single-machine reproduction and automated verification.
- Sub-agents **periodically check the termination signal** in their loop (before and after each fetch step), so termination is a "safe-point response" rather than a forced kill, ensuring resources are properly cleaned up.

---

## 中文

# 实验 10-6 · 同时从多个网站搜集信息的 Agent（★★）

《深入理解 AI Agent》配套实验。演示**多个同构 Agent 的并行搜索 + 中心协调**：
主协调器同时启动 N 个子 Agent，每个子 Agent 访问一个"网站/来源"找答案；
一旦某个子 Agent 命中目标，其余立即优雅停止。

书中的原型是"10 个并行的 Computer Use Agent 同时访问不同网站找信息"。为便于
自动验证，本实验**不启动真实浏览器**，而是用一批**可控的模拟信息源**代替；把重点
完整放在协调机制上——**消息总线、并行派发、实时监控、级联终止、竞态处理均为真实实现**。

## 目录结构

| 文件 | 作用 |
| --- | --- |
| `message_bus.py` | 进程内异步消息总线（Redis Pub/Sub 风格），带 `Envelope` 信封与订阅机制 |
| `sources.py` | 模拟的 10 个"网站/来源"，各有不同延迟；可控的关键词命中判断；`build_sources(n)` 支持任意并行度 |
| `llm.py` | 可选的 LLM 判断层（默认离线关键词判断，配了 key 则用真实大模型） |
| `agents.py` | 主协调器 `Coordinator` 与子 Agent `WorkerAgent`（核心协调逻辑）；`run_sequential` 串行基线 |
| `demo.py` | 一条命令的演示入口，带 argparse CLI 与末尾断言式自检 |

## 架构与机制

```
                         ┌────────────────────────────┐
                         │   Coordinator（主协调器）    │
                         │  · 并行派发 task_assigned    │
                         │  · 维护任务状态表(状态机)     │
                         │  · 首个命中→加锁结算(幂等)    │
                         │  · 广播一轮 terminate        │
                         └───────────┬────────────────┘
                                     │
                    ┌────────────────┴─────── MessageBus（异步消息总线）───────┐
                    │  Envelope{ sender_id, target, type, payload, seq, ts }    │
                    │  type: task_assigned/status_update/result/terminate/ack   │
                    └──┬─────────┬─────────┬─────────┬──────────────┬──────────┘
                       │         │         │         │              │
                    ┌──▼──┐  ┌──▼──┐  ┌──▼──┐  ┌──▼──┐   ...   ┌──▼──┐
                    │W-00 │  │W-01 │  │W-02 │  │W-03 │         │W-09 │  子 Agent
                    │网站A│  │网站B│  │网站C│  │网站D│         │网站J│  （同构·并行）
                    └─────┘  └─────┘  └─────┘  └─────┘         └─────┘
```

对应书中强调的五个机制：

1. **消息总线（Message Bus）**：所有通信都是发布到总线的**带信封消息**，按 `type`
   订阅。日志中每条 `BUS ...` 行就是一次发布/投递（Redis Pub/Sub 语义的进程内实现）。
2. **并行派发**：`Coordinator` 同时给 10 个子 Agent 发 `task_assigned` 并 `asyncio.create_task` 并发执行。
3. **实时监控（push 范式）**：子 Agent 执行中主动 `status_update` 上报进度，
   主 Agent 维护**任务状态表**并在状态机跳变时实时刷新打印。
   状态机：`已提交 → 执行中 →（需要输入）→ 已完成 / 失败 / 已终止`。
4. **级联终止**：某子 Agent 命中后，主 Agent **广播 `terminate`**；其余子 Agent 在
   循环的**安全检查点**发现信号后回 `ack` 并优雅退出（状态置为"已终止"）。
5. **竞态处理**：多个子 Agent 可能几乎同时命中，主 Agent 用 `asyncio.Lock` +
   幂等标志 `_settled` 保证**只结算一次、只广播一轮终止**；迟到的命中被记录并忽略。

> 为让"竞态""级联终止"可复现，各来源被赋予不同的模拟延迟，其中 `geo-journal` 与
> `forum-qa` 两个正确源被设成**相同延迟**，从而稳定地在同一时刻命中、触发竞态。

## 运行

```bash
cd chapter10/parallel-web-research
pip install -r requirements.txt   # 仅离线演示的话可跳过，纯标准库即可运行
python demo.py
```

默认走**离线关键词判断**（无需联网、结果可复现）。若要让子 Agent 用真实 LLM 判断：

```bash
cp env.example .env
# 在 .env 填入 OPENAI_API_KEY（也支持 Moonshot / 火山方舟 ARK 的 OpenAI 兼容网关）
python demo.py
# 或不改 .env，直接用命令行开关（仍需配置 key 才会真正生效）：
python demo.py --use-llm --model gpt-5.6-luna
```

可用 key：`OPENAI_API_KEY`（默认模型 `gpt-5.6-luna`）/ `MOONSHOT_API_KEY` / `ARK_API_KEY`
（填到 `OPENAI_API_KEY` 并按需设置 `OPENAI_BASE_URL`、`OPENAI_MODEL`）。

**通用回退**：若未设置 `OPENAI_API_KEY` 但设了 `OPENROUTER_API_KEY`，则真实 LLM 判断
自动改走 OpenRouter，并把模型名映射到其命名空间（`gpt-5.6-luna` → `openai/gpt-5.6-luna`）。
不影响协调机制，仅改变"是否命中"的判断。

### 命令行参数

`python demo.py --help` 可查看完整帮助。所有参数都**不改变默认行为**——不传任何参数即为
原有的「10 个 Agent + 内置问题 + 离线可复现 + 详细 BUS 日志」演示。

| 参数 | 作用 | 默认 |
| --- | --- | --- |
| `-q, --query 问题` | 研究问题（离线关键词判断是针对内置来源调校的，自定义问题一般需搭配 `--use-llm`） | 内置问题 |
| `-n, --agents N` | 并行子 Agent 数量（N≥2 时始终包含两个含答案的源以稳定演示竞态/级联终止） | `10` |
| `--model MODEL` | LLM 模型名（等价于设 `OPENAI_MODEL`，仅 `--use-llm` 且配置 key 时生效） | 环境变量 |
| `-o, --output PATH` | 把结论（含并行/串行耗时、winner、竞态统计）写入 JSON 文件 | 不写 |
| `--compare` | 并行跑完后再**实测**一遍串行基线，打印墙钟耗时对比 | 关闭 |
| `--use-llm` | 强制真实 LLM 判断（仍需配 `OPENAI_API_KEY` 或 `OPENROUTER_API_KEY`，否则自动回退离线判断） | 关闭 |
| `--quiet` | 减少逐条 BUS 日志（状态表/结论/自检不受影响） | 关闭 |

```bash
python demo.py --agents 6 --compare       # 6 个并行 Agent，并对比串行墙钟耗时
python demo.py --output result.json        # 结论落盘为 JSON
```

### 并行 vs 串行的墙钟收益（`--compare`）

对应书中实验要求「记录并对比并行/串行时间差异」。`--compare` 会在并行演示之后，用**完全相同的
来源集合**再跑一遍**串行基线**（逐个 `await source.fetch()` + 判断，命中即止），耗时是**实测**而非
估算。示例输出（默认 10 源，离线判断）：

```
5) 并行执行墙钟耗时：1.57s（含收敛静默期）
------------------------------------------------------------------------------
并行 vs 串行 墙钟对比（--compare，串行基线为实测）
------------------------------------------------------------------------------
   串行：命中前逐个抓取了 3/10 个源，墙钟耗时 2.60s，winner=geo-journal
   并行：墙钟耗时 1.57s，winner=worker-02
   加速比 ≈ 1.66×，节省约 1.03s（并行让最快的源立即结束全局搜索）。
```

串行必须依次抓完 baike-wiki→news-portal 才轮到最快命中的 geo-journal（累计 2.6s）；并行则让
所有源同时开跑，最快的源一命中就触发级联终止、立刻结束全局搜索。并行墙钟包含级联终止的收敛
开销，因此不是理想的「首个源延迟」，但仍显著快于串行——这正是并行 + 级联终止的价值所在。

## 演示说明什么（真实运行输出关键片段）

**(a) 消息总线的发布/订阅在工作**——每条带信封的消息都打印出来：

```
BUS [t=  0.00s #3  ] coordinator -> worker-02   | task_assigned  | {"question": "...", "source": "geo-journal"}
BUS [t=  0.00s #13 ]   worker-02 -> coordinator | status_update  | {"state": "执行中", ...}
```

**(b) N 个子 Agent 并行执行 + 主 Agent 实时刷新状态表**：

```
── 任务状态表（worker-02 -> 执行中） ──
   worker-00  源=baike-wiki   状态=执行中   | 开始抓取来源
   worker-02  源=geo-journal  状态=执行中   | 开始抓取来源
   ...
```

**(c) 级联终止**——命中后广播 terminate，其余子 Agent ack 并优雅退出：

```
BUS [t=0.60s #41 ] coordinator -> ALL         | terminate | {"reason":"answer_found","winner":"worker-02"}
BUS [t=0.67s #43 ]   worker-09 -> coordinator | ack       | {"acked":"terminate","source":"map-service"}
[ack] worker-09 已确认终止（1 个已 ack）
...最终 8 个未命中的 Worker 全部状态=已终止
```

**(d) 竞态：即使几乎同时命中，也只结算一次、只广播一轮终止**：

```
BUS [t=0.60s #37 ]   worker-02 -> coordinator | result | {"found":true, "answer":"...珠穆朗玛峰...8848 米..."}
BUS [t=0.60s #38 ]   worker-04 -> coordinator | result | {"found":true, "answer":"...珠穆朗玛峰...8848.86 米..."}
[结算] 首个命中来自 worker-02 —— 加锁结算，广播一轮 terminate。
[竞态] worker-04 也命中，但已由 worker-02 结算 —— 忽略此次命中，不重复广播终止。
```

`demo.py` 末尾有**断言式自检**：`terminate 广播轮数 == 1`、`只结算一次 == True`、
`winner 非空`。跑通即证明机制正确：

```
4) terminate 广播轮数：1（应为 1，证明只广播一轮）
   迟到/并发的重复命中被忽略：['worker-04']
[自检通过] 单次结算 + 单轮终止广播 + 级联 ack 均符合预期。
```

## 局限与注意事项

本实验把重点放在**协调机制**（消息总线/并行派发/级联终止/竞态处理）上，这些均为真实
实现；但为了可离线运行与自动验证，以下三处做了简化，是已知局限：

- **局限·模拟源非真实浏览器**：不启动真实浏览器，来源是可控的模拟数据 + 延迟。若要接
  真实 Computer Use，只需把 `WorkerAgent.run()` 里的"抓取一步 + 判断"换成真实浏览器
  操作，协调层无需改动。
- **局限·竞态靠相同延迟稳定复现**：`geo-journal` 与 `forum-qa` 两个正确源被人为设成
  相同延迟，才能稳定触发"同时命中"；真实环境里竞态是偶发的，但加锁 + 幂等的结算逻辑
  对偶发竞态同样成立，不依赖这个人为设定。
- **局限·进程内总线非真实 Redis**：`MessageBus` 用**进程内 async 队列**模拟 Redis
  Pub/Sub，无需真装 Redis；语义（信封、按类型订阅、点对点/广播投递）一致，但不具备
  跨进程/跨机器能力，便于单机复现与自动验证。
- 子 Agent 在循环里**定期检查终止信号**（每步抓取前后），因此终止是"安全点响应"而非
  强杀，能保证资源被正常收尾。
