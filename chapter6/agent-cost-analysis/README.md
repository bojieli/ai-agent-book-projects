# Agent End-to-End Cost Analysis / Agent 任务端到端成本分析（实验 6-7）

## English

This project performs a full cost decomposition for a multi-turn agent workflow (refund handling), including input/cache/output tokens, latency, and cost distribution. It enables practical measurement of where costs come from and how optimization strategies affect total spend.

### What it does

The benchmark runs a fixed 8-turn customer refund scenario and records every LLM call with a lightweight tracing layer:
- token usage (prompt, cached prompt, output)
- latency
- model cost by pricing table

It then reports:
- per-step cost breakdown
- cost component breakdown (non-cached input / cached input / output)
- p50/p95/p99 for per-step cost
- full 2×2 A/B comparison between optimization levers

The two levers are:
- **KV-cache friendliness**: keep a stable prefix to maximize cache hits
- **Context compression**: summarize long tool outputs for earlier turns

### Default model and API behavior

- Default model: `gpt-5.6-luna`.
- Preferred credentials: `OPENAI_API_KEY`, fallback to `OPENROUTER_API_KEY` (`gpt-*` remapped to `openai/*`).
- If OpenRouter keys exist for `gpt-5.x`, it is preferred due to authentication requirements.
- Offline mode is supported via `sample_trace.json` so all tables can be recomputed without API calls.

### Files

| File | Purpose |
|---|---|
| `config.py` | pricing model definitions and pricing presets |
| `tracer.py` | tracing helper and cost decomposition/aggregation |
| `agent.py` | 8-turn refund agent with `run_scenario(kv_cache, compress)` |
| `demo.py` | CLI entry for online/offline runs |
| `sample_trace.json` | captured 2×2 scenario token records for offline recomputation |
| `requirements.txt` / `env.example` | dependencies and environment templates |

### Run

```bash
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...   # or OPENROUTER_API_KEY=sk-or-...
python demo.py
python demo.py --offline --scenario all
```

### CLI options

| Argument | Meaning |
|---|---|
| `--live` / `--offline` | call real model (default) / recompute from trace |
| `--scenario` | `ab` (naive+both), `all` (four scenarios), or subset list |
| `--trace` | trace file for offline mode |
| `--save-trace` | persist observed token usage from online runs |
| `--model` | model name for price preset |
| `--price-input` / `--price-cached` / `--price-output` | override per-million-token prices |
| `--no-warmup` | disable prefix warmup for KV-cache scenario |
| `--output` | export full result JSON |

### A/B scenarios (2×2)

| Scenario | KV-cache | Compression | Context design |
|---|---|---|---|
| `naive` | no | no | random session header + full tool returns |
| `kv` | yes | no | stable long prefix |
| `compress` | no | yes | only keep last 2 turns full; older turns summarized |
| `both` | yes | yes | stable prefix + compressed history |

The task logic is identical across scenarios so differences isolate optimization effects.

### Interpretation

Empirical results show:
- KV-cache can produce large improvements when prefixes are stable.
- Compression lowers prompt growth while keeping functional behavior.
- Joint optimization usually gives best total cost, though cache gains and compression gains are not simply additive.

### Offline recomputation

Offline mode reads `sample_trace.json` and re-runs only cost arithmetic, enabling:
- quick replication without keys
- quick “what-if” with different model prices

### Notes

- Observed numbers can vary due to real API behavior and cache timing.
- Prompt cache is best-effort and may miss in some turns.
- Tool-return token estimate uses tokenizer counts against current model encoder.
- Key precedence: prefer `OPENAI_API_KEY`; fallback is automatic via OpenRouter for supported paths.

---

## 中文

# 实验 6-7：Agent 任务的端到端成本分析

配套《深入理解 AI Agent》第 6 章「实验 6-7 ★：Agent 任务的端到端成本分析」。

对一个典型的多轮 Agent 任务（客服退款）做**全链路成本拆解**，用**自建的轻量 tracing / 可观测系统**记录每次 LLM 调用的输入/输出/缓存 token、时延与成本：按步骤聚合出「哪一步最贵」，按**成本构成**拆出「未缓存输入 / 缓存输入 / 输出各占多少、工具返回注入了多少 token」，并给出**单步成本分布（p50/p95/p99）**；再做完整 **2×2 A/B 对比**，量化 **KV-cache 复用** 与 **上下文压缩** 两个杠杆各自及叠加后的真实成本差异。

- 默认模型 **`gpt-5.6-luna`**（当前廉价旗舰），通过 openai Python SDK 调用。首选 `OPENAI_API_KEY`；未设置时**自动回退到 `OPENROUTER_API_KEY`**（走 OpenRouter 兼容端点，`gpt-*` 映射为 `openai/*`）。由于 `gpt-5.x` 直连 OpenAI 需组织实名认证，只要存在 `OPENROUTER_API_KEY` 就优先走 OpenRouter。
- KV-cache 的节省是**真实**的：利用 OpenAI 的自动 prompt caching（前缀 ≥ 1024 token 且命中近期相同前缀时，`usage.prompt_tokens_details.cached_tokens > 0`，这部分输入按缓存价 5 折计费）。
- 提供**离线模式**：不打模型，读入一份此前真实运行录下的 token 用量（`sample_trace.json`，canned token counts），用可配置单价**重新计算**成本/成本构成/A/B 对比表——无需 API key 即可复现全部表格，也可一键换算到其它模型定价。

## 文件

| 文件 | 说明 |
|------|------|
| `config.py` | 模型与价格：`Pricing` 单价对象 + 常见 OpenAI 模型单价预设，token→成本换算 |
| `tracer.py` | 自建轻量 tracing：包裹每次 LLM 调用记录 token/缓存/时延/成本；成本构成拆解、单步成本分布、按步骤拆解表；支持从录制用量离线复算（`from_records`）|
| `agent.py` | 多轮客服退款 Agent 任务；`run_scenario(kv_cache, compress)` 把两个开关正交组合成 2×2 场景，并用 tiktoken 估算「工具返回注入」token |
| `demo.py` | 命令行入口（argparse）：在线跑真实模型 / 离线复算；选择 A/B 场景、模型单价、输出文件 |
| `sample_trace.json` | 一次真实运行录下的四个场景逐步 token 用量（离线模式的输入，成本按当前单价重算）|
| `requirements.txt` / `env.example` | 依赖与环境变量示例 |

## 运行

```bash
pip install -r requirements.txt

# 在线（真实调用模型，需要 key）：默认跑 A(朴素)+B(优化) 两组
export OPENAI_API_KEY=sk-...           # 或 export OPENROUTER_API_KEY=sk-or-...（自动回退）
python demo.py

# 离线（无需 key）：用内置 canned trace 复算全部表格
python demo.py --offline --scenario all
```

在线模式会真实调用 OpenAI，`--scenario all` 约几十次 chat completion，运行一两分钟。

### 命令行参数（`python demo.py --help`）

| 参数 | 说明 |
|------|------|
| `--live` / `--offline` | 在线真实调用（默认）/ 离线从 trace 文件复算（无需 key）|
| `--scenario NAME` | `ab`(默认=naive+both) / `all`(2×2 四组) / 逗号分隔子集 `naive,kv,compress,both` |
| `--trace FILE` | 离线读取的 canned trace，默认 `sample_trace.json` |
| `--save-trace FILE` | 在线跑时把真实 token 用量落盘，供之后 `--offline` 复算 |
| `--model NAME` | 模型名（决定默认单价预设：`gpt-4o-mini`/`gpt-4o`/`gpt-4.1-mini`/`gpt-4.1`）|
| `--price-input/-cached/-output` | 覆盖三档单价（每百万 token 美元）|
| `--no-warmup` | 关闭 KV-cache 组的前缀预热（默认预热以稳定命中缓存）|
| `--output FILE` | 把成本拆解结果（含成本构成/分布/逐步用量）写成 JSON |

> **不改任何参数直接 `python demo.py`，行为与之前一致**：在线跑 A(朴素) 与 B(优化) 两组并打印拆解 + A/B 对比表。

## A/B 四种策略（完整 2×2）

同一个 8 轮客服退款任务（查订单 → 查物流 → 查退款政策 → 查知识库 → 风控 → 发起退款 → 通知 → 关单），四组做的是**同样的逻辑工作**，只在上下文构造上不同——因此成本差异纯粹来自「是否 KV-cache 友好」与「是否压缩上下文」两个正交开关：

| 场景 | KV-cache | 压缩 | 上下文构造 |
|------|:--:|:--:|------|
| `naive` A 朴素 | ✗ | ✗ | 每轮 system 前塞随机 session 头（破坏前缀）+ 历史工具返回原样带全 |
| `kv` 仅缓存 | ✓ | ✗ | 稳定长前缀（system 逐字节不变）+ 历史不压缩 |
| `compress` 仅压缩 | ✗ | ✓ | 前缀不稳定 + 仅最近 2 轮保留完整工具返回、更早压成一句话摘要 |
| `both` B 优化 | ✓ | ✓ | 稳定长前缀 + 上下文压缩（两个杠杆叠加）|

> 为聚焦「输入侧」两个杠杆，四组都用 `temperature=0` 且限制输出长度（`max_tokens=160`），让输出 token 成本近似为四组相等的固定项，避免模型生成长度的随机波动干扰对比。
>
> 工具环境是「受控」的（工具返回内容预设，真实系统里来自订单/物流/知识库后端），但**每一次 LLM 调用、每一份 token 用量、每一分成本都是真实打到 OpenAI 得到的**，保证可复现。

## 真实运行输出（gpt-4o-mini）

以下为一次真实运行（`python demo.py --scenario all`）的输出，`sample_trace.json` 即由该次运行落盘、供 `--offline` 复现。

### (a) 单次任务成本拆解：按步骤 + 按成本构成 + 分布

```
===== 成本拆解: A 朴素(无缓存/无压缩)（单次任务全链路拆解） =====
步骤       工具/动作                   输入tok    缓存tok    工具tok    输出tok    时延(s)        成本($)
---------------------------------------------------------------------------------------
turn-1   query_order              1113        0      276      104     3.15     0.000229
turn-2   query_logistics          1807        0      829       99     2.09     0.000330
turn-3   check_refund_policy      2154        0     1046      139     2.69     0.000406
turn-4   query_knowledge_base     2564        0     1287      160     2.92     0.000481
turn-5   query_user_history       2863        0     1389      136     2.69     0.000511
turn-6   issue_refund             3123        0     1490      160     3.07     0.000564
turn-7   send_notification        3408        0     1579      160     3.09     0.000607
turn-8   close_ticket             3668        0     1648      160     2.50     0.000646
---------------------------------------------------------------------------------------
合计                               20700        0     9544     1118    22.20     0.003776

最贵的一步 → turn-8 / close_ticket: $0.000646（占总成本 17.1%）
成本构成:
  未缓存输入     20700 tok  $0.003105  (82.2%)
  缓存输入           0 tok  $0.000000  (0.0%)
  输出            1118 tok  $0.000671  (17.8%)
  其中「工具返回注入」累计输入 9544 tok （同一份工具返回在后续每轮被反复计费）
单步成本分布(n=8): 均值 $0.000472  p50 $0.000481  p95 $0.000646  p99 $0.000646

===== 成本拆解: B 优化(KV缓存+压缩)（单次任务全链路拆解） =====
步骤       工具/动作                   输入tok    缓存tok    工具tok    输出tok    时延(s)        成本($)
---------------------------------------------------------------------------------------
turn-1   query_order              1056     1024      276      139     2.41     0.000165
turn-2   query_logistics          1781        0      829      112     2.18     0.000334
turn-3   check_refund_policy      2143     1024     1046      151     2.56     0.000335
turn-4   query_knowledge_base     2310        0     1052      160     3.03     0.000442
turn-5   query_user_history       2060     1024      635      160     2.48     0.000328
turn-6   issue_refund             2143     1024      551      160     2.71     0.000341
turn-7   send_notification        2188     1024      430      160     2.79     0.000347
turn-8   close_ticket             2354     1024      429      122     2.38     0.000349
---------------------------------------------------------------------------------------
合计                               16035     6144     5248     1164    20.54     0.002643

最贵的一步 → turn-4 / query_knowledge_base: $0.000442（占总成本 16.7%）
成本构成:
  未缓存输入      9891 tok  $0.001484  (56.1%)
  缓存输入        6144 tok  $0.000461  (17.4%)
  输出            1164 tok  $0.000698  (26.4%)
  其中「工具返回注入」累计输入 5248 tok （同一份工具返回在后续每轮被反复计费）
单步成本分布(n=8): 均值 $0.000330  p50 $0.000335  p95 $0.000442  p99 $0.000442
```

可以看到：朴素组 A 的输入 token 随轮次从 1113 一路涨到 3668（上下文累积效应，最后一步最贵），「工具返回注入」累计吃掉 9544 输入 token；优化组 B 的输入 token 被压缩策略压住（末轮 2354 而非 3668，工具注入累计降到 5248），且多数轮次持续命中 1024 缓存 token，缓存输入把整块费用打了 5 折。

### (b) 完整 2×2 A/B 对比

```
===== A/B 成本对比（同一个 8 轮客服退款任务）=====
方案                             总输入tok      缓存tok      缓存率    输出tok       总成本($)       vs基线
------------------------------------------------------------------------------------------
A 朴素(无缓存/无压缩)                   20700          0     0.0%     1118     0.003776         基线
KV 仅缓存(稳定前缀/不压缩)                20386      13568    66.6%     1112     0.002707     -28.3%
仅压缩(前缀不稳定/摘要)                   16177          0     0.0%     1147     0.003115     -17.5%
B 优化(KV缓存+压缩)                   16035       6144    38.3%     1164     0.002643     -30.0%
------------------------------------------------------------------------------------------

重点对比：A 朴素(无缓存/无压缩)  →  B 优化(KV缓存+压缩)
  总 token:   A=21818  →  B=17199   减少 4619 (21.2%)
  缓存 token: A=0  →  B=6144   （B 靠稳定前缀命中缓存）
  总成本:     A=$0.003776  →  B=$0.002643   降低 $0.001133 (30.0%)
  成本倍率:   A 是 B 的 1.43 倍
```

结论（读出两个杠杆各自与叠加的贡献）：
- **仅 KV-cache**：不改上下文长度，只靠稳定前缀让重复的系统提示/工具定义/历史轮次按缓存价计费，缓存率冲到 66.6%，端到端成本就降了 **28.3%**——本例中它是单个最有效的杠杆。
- **仅压缩**：把旧轮次工具返回压成摘要，总输入 token 从 20700 降到 16177（约 −22%），端到端成本降 **17.5%**；但因为前缀不稳定，缓存率为 0。
- **两者叠加（B 优化）**：输入 token 最少、又能命中缓存，端到端总成本降 **30.0%**（A 是 B 的 1.43 倍）。单看输入侧成本，降幅落在书中「KV Cache 可降低 30%-60% 输入 token 成本」的经验区间内。

> 注意 KV 与压缩并非简单相加：压缩缩短了历史，可被缓存的「历史轮次」也随之变少，所以 B 的缓存 token（6144）反而少于「仅 KV」（13568）。这正是评估的价值——两个优化叠加时要实测协同效应，而不是把各自的收益直接相加。

## 离线复算（无需 API key）

`sample_trace.json` 存的是上面这次真实运行的**逐步 token 用量（实测值）**；离线模式只做「按单价重算成本」这一步纯离线数学，因此无需 key 即可复现全部表格，还能一键换算到其它模型定价：

```bash
python demo.py --offline --scenario all                 # 用 gpt-4o-mini 单价复算
python demo.py --offline --scenario all --model gpt-4o  # 同一份 token 用量，换 gpt-4o 单价重算
python demo.py --offline --price-input 0.20 --price-cached 0.10 --price-output 0.80
```

换 `gpt-4o` 单价后，同一批 token 的四组总成本等比放大（结论与占比不变，A=$0.062930 → B=$0.044047，仍是 −30.0%）——这说明**成本优化的相对收益由 token 结构决定，与绝对单价无关**。

## 注意事项

- 具体数字每次在线运行会有小幅波动：OpenAI 的 prompt cache 是**尽力而为**的（按约 128 token 的块缓存、约 5–10 分钟过期、偶尔未命中），因此某些轮次可能出现 `cached_tokens=0`（如上面 B 组的 turn-2/turn-4）。`demo.py` 在正式计量前会先对 KV-cache 组跑一次「预热」把稳定前缀写入缓存，让命中更稳定；`--no-warmup` 可关闭。
- 价格写在 `config.py`（`PRICING_PRESETS`），默认是 gpt-4o-mini 的公开单价（输入 \$0.15 / 缓存 \$0.075 / 输出 \$0.60 每百万 token）。**换模型**：用 `--model`（如 `--model gpt-4o`）或 `--price-*` 直接覆盖单价即可；缓存命中要求稳定前缀 ≥ 1024 token，换更强模型不影响该机制。
- 「工具返回注入」token 用 tiktoken 按当前模型的编码器离线估算（统计每轮输入里工具返回文本占多少 token），用于回答书中「一次工具返回可能占 2000-5000 token，且在后续每轮被反复计费」这一放大因素。
- 凭据：首选 `OPENAI_API_KEY`；未设置时自动回退到 `OPENROUTER_API_KEY`（走 OpenRouter，`gpt-*` 映射为 `openai/*`）。`gpt-5.x` 直连需组织实名认证，故有 `OPENROUTER_API_KEY` 时优先走 OpenRouter。离线复算（`--offline`）无需任何 key。
