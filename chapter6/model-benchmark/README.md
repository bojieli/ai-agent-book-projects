# Multi-dimensional Model Benchmarking / 多维度模型性能基准 / 实验 6-8

## English

This directory implements a practical benchmarking harness for comparing multiple OpenAI-compatible LLM providers. One command can produce a table including **TTFT, end-to-end latency, throughput, std, p50/p95/p99, and success rate**.

It supports:
- **Concurrency stress testing**: sweep concurrency to identify rate limits and observe metric curves.
- **Offline mock mode** (`--mock`): synthetic data pipeline for verifying aggregation logic without API keys/network.

The original chapter workflow describes hourly probes, multiple context windows, and threshold checks. This project focuses on the core locally reproducible piece: measure TTFT precisely via streaming, evaluate percentile latency under concurrency, and use success rate as availability signal.

## Metric definitions

| Metric | Meaning | How measured |
|---|---|---|
| Success rate | Availability | successful request count / total |
| TTFT | Time to first token | stream first non-empty chunk - request start |
| End-to-end latency | complete response time | request start -> final chunk |
| Throughput (tokens/s) | generation speed | output token count / (end-to-end - TTFT) |
| p50 / p95 / p99 | latency percentiles | interpolation over successful requests |
| std | standard deviation | per-provider latency dispersion |
| aggregate throughput / RPS | batch throughput metrics | aggregated output token rate and request rate |

If `usage.completion_tokens` is unavailable, token count falls back to chunk-count approximation with a documented caveat.

## Run

```bash
cd chapter6/model-benchmark
pip install -r requirements.txt

cp env.example .env
# or export OPENAI_API_KEY=... MOONSHOT_API_KEY=... ARK_API_KEY=...

python demo.py
```

### Common parameters

```bash
python demo.py --list
python demo.py --num-requests 20 --concurrency 5
python demo.py --serial
python demo.py --max-tokens 256
```

## Specify custom endpoint/model

Use `--base-url`, `--model`, and `--api-key-env` to test a new provider without changing `DEFAULT_PROVIDERS`.

```bash
python demo.py --base-url https://api.deepseek.com --model deepseek-chat \
  --api-key-env DEEPSEEK_API_KEY --name "DeepSeek官方/deepseek-chat"
```

## Concurrency sweep

```bash
python demo.py --model gpt-5.6-luna --concurrency-sweep 1,2,4,8,16 --num-requests 100
```

As concurrency increases, p95/p99/std generally get worse, and success rate may drop due to rate limits; aggregate throughput/RPS usually rises then plateaus.

## Metrics and export

```bash
python demo.py --metrics ttft,throughput
python demo.py --output result.json
```

## Offline mock validation

```bash
python demo.py --mock
python demo.py --mock --concurrency-sweep 1,2,4,8,16
```

This validates full aggregation logic with synthetic numbers labelled `[SYNTHETIC]`.

## Default providers

`DEFAULT_PROVIDERS` includes the keys that are present in environment:

- OpenAI-compatible entries (gpt-5.6-luna)
- Moonshot / doubao (explicit base_url + key)

OpenRouter fallback behavior:
- If `OPENAI_API_KEY` is missing, OpenAI-style entries can still run via OpenRouter (`OPENROUTER_API_KEY`), with model id mapping.
- For gpt-5.x, OpenRouter is preferred when `OPENROUTER_API_KEY` exists.

## Files

| File | Purpose |
|---|---|
| `benchmark.py` | core benchmark core: provider config, streaming measure, concurrency scheduling, aggregation |
| `demo.py` | CLI, parameter parsing, reporting and mock mode |
| `requirements.txt` | dependencies |
| `env.example` | env templates |

## Limitations

- Default parameters are low-cost defaults (`N=10`, `concurrency=3`, `max_tokens=64`).
- Larger requests increase cost and rate-limit risk.
- TTFT depends heavily on geography/network.
- Offline mock is for method validation only, not production decisions.

---

## 中文

# 多维度模型性能基准测试（实验 6-8 配套代码）

对多个 OpenAI 兼容的 LLM API 提供商做横向基准测试，一条命令跑出
**TTFT / 端到端延迟 / 吞吐 / 标准差 / p50 / p95 / p99 / 成功率** 的多维度对比表，
为模型选型提供实测依据。还支持**并发压测**（逐档加压找限流点，看指标随并发的变化）
与**离线自检**（`--mock` 合成数据，无需 key/网络即可验证指标聚合）。

对应《深入理解 AI Agent》第 6 章 **实验 6-8：多维度模型性能基准测试**。

## 目的

书中实验 6-8 的完整版要求"一周内每小时探测、8K/32K/128K 上下文、
100+ 请求、MTTR/限流阈值/综合成本"等。本配套代码聚焦其中**最核心、
可低成本本地复现**的一环：用**流式接口**精确测量首 token 延迟，
在**并发**下测出延迟分位数与吞吐，并以**成功率**刻画可用性——
让读者用几分钟、几分钱就能得到一张真实的多提供商对比表，
理解"选型是多维权衡而非单看排行榜"。

## 指标定义

| 指标 | 含义 | 怎么测的 |
| --- | --- | --- |
| 成功率（可用性） | 成功请求数 / 总请求数 | 单次请求任何异常（超时/限流/网络错误/空响应）都计为失败，不中断整表 |
| TTFT | 首个 token 到达延迟 | 流式读取，记录第一个"有内容" chunk 到达的时刻 − 请求发出时刻 |
| 端到端延迟 | 请求发出到响应结束的总耗时 | 最后一个 chunk 时刻 − 请求发出时刻 |
| 吞吐（tokens/s） | 生成阶段的输出速度 | 输出 token 数 / (端到端 − TTFT)，剥离首 token 等待，反映纯解码速度 |
| p50 / p95 / p99 | 延迟的中位数 / 95 / 99 分位 | 对同一 (provider, model) 的多次成功请求排序后线性插值；p95、p99 高说明长尾重、体验不稳 |
| 标准差（std） | 延迟的离散程度 | 样本标准差；书中强调"高延迟方差意味着用户体验不稳定" |
| 聚合吞吐 / RPS | 整批的总吞吐 | 并发压测时：全部成功请求的输出 token 总数 / 整批墙钟耗时（RPS 为成功请求数 / 墙钟）；随并发上升先增后趋平，触及服务端上限即触顶 |

> 输出 token 数优先取服务端回传的精确 `usage.completion_tokens`；
> 若服务不返回 usage，则以流式 chunk 数近似计数（会略微偏高，已在代码注释标明）。

## 运行

```bash
cd chapter6/model-benchmark
pip install -r requirements.txt

# 配置 key：只需填手上有的，未设置的提供商会自动跳过
cp env.example .env        # 然后编辑 .env
# 或直接 export OPENAI_API_KEY=... MOONSHOT_API_KEY=... ARK_API_KEY=...

python demo.py             # 一条命令跑出对比表
```

常用参数：

```bash
python demo.py --list                          # 仅列出将测试的提供商
python demo.py --num-requests 20 --concurrency 5   # 加大样本与并发
python demo.py --serial                        # 串行发送（并发=1，看无竞争下的基线延迟）
python demo.py --max-tokens 256                # 生成更长响应，更充分地测吞吐
```

默认参数（`N=10/家, 并发=3, max_tokens=64`）单次全跑成本约几分钱。
要接近书中"每配置 ≥100 次请求"的统计口径，把 `--num-requests` 调到 100 即可
（注意成本与限流会同步上升）。

### 指定任意 OpenAI 兼容端点（不改代码测新模型/新提供商）

书中要求"对同一模型测试不同 API 提供商（如 DeepSeek 官方 vs SiliconFlow）"。
用 `--base-url / --model / --api-key-env` 即可直接指定单个端点，无需改 `DEFAULT_PROVIDERS`：

```bash
python demo.py --base-url https://api.deepseek.com --model deepseek-chat \
               --api-key-env DEEPSEEK_API_KEY --name "DeepSeek官方/deepseek-chat"
# 换个 base_url、保持同一 model，即可对比"同模型不同提供商"
```

### 并发压测：逐步加压找限流点

书中实验 6-8 要求"通过逐步提升并发量来找到限流点，记录 RPM/TPM 上限"。
`--concurrency-sweep` 对同一模型逐档加压，产出一张随并发变化的指标表
（p50/p95/p99/std/成功率/RPS/聚合吞吐）：

```bash
python demo.py --model gpt-5.6-luna --concurrency-sweep 1,2,4,8,16 --num-requests 100
```

随着并发上升，单请求延迟长尾（p95/p99/std）通常变差、可用性可能因限流下降，
而**聚合吞吐（tokens/s）与 RPS 先升后趋平**——趋平点即服务端的实际吞吐上限。

### 选择要显示的指标 / 导出结果

```bash
python demo.py --metrics ttft,throughput      # 主表只看 TTFT 与吞吐（成功率始终显示）
python demo.py --output result.json           # 完整结果（含 p50/p95/p99/std）写入 JSON
```

### 离线自检（`--mock`，无需 key/网络）

用**合成（synthetic）数据**跑通整条指标聚合链路，便于在没有 API key 或无网络时
验证 p50/p95/p99/std/可用性/聚合吞吐的计算是否正确。**输出数字全部为伪随机合成，
带 `[SYNTHETIC]` 标注，绝非真实基准，切勿用于选型。**

```bash
python demo.py --mock                                   # 合成横向对比表
python demo.py --mock --concurrency-sweep 1,2,4,8,16     # 合成并发压测表
```

一次合成并发压测的输出（`--mock --concurrency-sweep 1,2,4,8,16 --num-requests 100`，
**数字为合成，仅演示趋势**）：

```
并发 | 成功率         | TTFT_p50 | TTFT_p95 | 端到端p50 | 端到端p95 | 端到端p99 | 端到端std | RPS  | 聚合吞吐
-----+----------------+----------+----------+-----------+-----------+-----------+-----------+------+----------
1    | 99/100 (99%)   | 301ms    | 514ms    | 0.73s     | 1.04s     | 1.16s     | 0.13s     | 1.3  | 49.8 t/s
2    | 100/100 (100%) | 335ms    | 570ms    | 0.79s     | 1.07s     | 1.19s     | 0.15s     | 2.5  | 94.4 t/s
4    | 98/100 (98%)   | 381ms    | 617ms    | 0.83s     | 1.11s     | 1.19s     | 0.16s     | 4.7  | 180.0 t/s
8    | 92/100 (92%)   | 523ms    | 932ms    | 0.96s     | 1.53s     | 1.67s     | 0.25s     | 8.0  | 305.3 t/s
16   | 97/100 (97%)   | 878ms    | 1487ms   | 1.30s     | 1.97s     | 2.37s     | 0.35s     | 11.9 | 441.0 t/s
```

可见随并发上升：端到端 p95/p99 与 std 走高（长尾变差），聚合吞吐持续增长（尚未触顶）。
真实端点上这条曲线会在某个并发处趋平并伴随可用性下降——那就是限流点。

## 默认测试的提供商

代码里 `DEFAULT_PROVIDERS` 默认只跑**手上有有效 key**的提供商（OpenAI 一个 key 测多个模型）：

| 展示名 | 模型 | base_url | key 环境变量 |
| --- | --- | --- | --- |
| OpenAI/gpt-5.6-luna | gpt-5.6-luna | （官方默认，可回退 OpenRouter） | OPENAI_API_KEY |
| Moonshot/moonshot-v1-8k | moonshot-v1-8k | https://api.moonshot.cn/v1 | MOONSHOT_API_KEY |
| Doubao/doubao-1.5-pro-32k | doubao-1-5-pro-32k-250115 | https://ark.cn-beijing.volces.com/api/v3 | ARK_API_KEY |

> **OpenRouter 回退**：`OpenAI/*` 这几条（base_url 为空的 OpenAI 原生条目）在未设置
> `OPENAI_API_KEY` 时会自动改走 **OpenRouter**（`OPENROUTER_API_KEY`，模型名映射为
> `openai/*`）。`gpt-5.x` 直连 OpenAI 需组织实名认证，因此只要设置了 `OPENROUTER_API_KEY`
> 就优先走 OpenRouter。带专属 `base_url` 的条目（Kimi/豆包）不参与回退。

**提供商列表是可配置的**：在 `benchmark.py` 的 `DEFAULT_PROVIDERS` 里追加
`ProviderConfig(...)` 即可扩展。所有提供商都走同一套 OpenAI 兼容协议，
只是 `base_url` 与 `model` 不同——这正是可以"同一模型对比不同提供商"
（如书中提到的 DeepSeek 官方 vs SiliconFlow）的原因。

## 真实运行结果（示例）

以下是一次真实运行的输出（`python demo.py --num-requests 10 --concurrency 3`，
测试机在中国大陆网络环境，`2026-07`）。**数字为真实测得，非虚构**；
不同网络/时段会有波动，请以自己跑出的结果为准。

```
Provider/Model            | 成功率       | TTFT均值 | TTFT_p95 | 端到端均值 | 端到端p95 | 吞吐      | 输出tok
--------------------------+--------------+----------+----------+------------+-----------+-----------+--------
OpenAI/gpt-5.6-luna       | 10/10 (100%) | 1360ms   | 2334ms   | 1.73s      | 2.54s     | 174.9 t/s | 26
Moonshot/moonshot-v1-8k   | 10/10 (100%) | 530ms    | 671ms    | 0.89s      | 1.07s     | 92.1 t/s  | 32
Doubao/doubao-1.5-pro-32k | 10/10 (100%) | 1097ms   | 1409ms   | 2.32s      | 2.91s     | 36.2 t/s  | 44
```

## 结论（基于上面这次运行）

- **可用性**：本次三家全部 10/10（100%）成功。可用性差异往往要在更大样本、
  更高并发或更长时间窗口下才暴露——这正是书中强调"一周每小时探测"的原因。
  代码已把单点失败设计成"记为可用性下降、不中断整表"，便于长时间挂机采样。
- **首 token 延迟（TTFT）**：本测试机在国内网络下，Kimi 的 TTFT（~530ms）明显低于
  跨境访问的 OpenAI/gpt-5.6-luna（~1.36s）；豆包 TTFT（~1.1s）略低于 OpenAI 但端到端更长。
  **TTFT 强依赖网络位置**——同一份代码在美国机房跑，OpenAI 的 TTFT 会大幅下降。
- **吞吐**：本次 gpt-5.6-luna（175 t/s）> Kimi（92 t/s）> 豆包（36 t/s）。
  吞吐决定长响应的等待时间，与 TTFT 是两个独立维度。
- **稳定性（p95）**：看 p95 与均值的差距。gpt-5.6-luna 跨境访问，TTFT p95(2.33s)/均值(1.36s)
  拉开较大，长尾更重；Kimi 的 p95 与均值最接近，本次最稳。
- **选型启示**：不存在"全面最优"的一家——延迟、吞吐、可用性、价格是**多维权衡**。
  面向国内用户的实时交互场景，低 TTFT 的本地化服务体验更好；
  批处理/长文本生成则更看重吞吐与单价。**务必在你自己的部署网络环境下实测**，
  不要直接照搬第三方监测平台（如 Artificial Analysis）的数字。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `benchmark.py` | 核心：提供商配置、单次流式测量、并发调度、指标聚合（含 p99/std/聚合吞吐）、并发扫描 `sweep_concurrency`、合成数据 `synthetic_summary` |
| `demo.py` | 命令行入口：解析参数、跑测试（含并发压测 / `--mock` 离线自检）、打印对比表、导出 JSON |
| `requirements.txt` | 依赖（openai SDK + 可选 python-dotenv） |
| `env.example` | key 配置模板 |

## 注意事项

- **成本控制**：默认 `max_tokens=64`、`N=10`，全跑成本极低。调大参数前请留意计费。
- **限流**：把并发或 N 调很大时可能触发提供商 RPM/TPM 限流，届时会以失败形式
  计入可用性下降——这本身也是一种"实测限流阈值"的方式（书中实验 6-8 的一环）。
- **TTFT 与网络强相关**：跨境访问的服务 TTFT 会显著偏高，结论需结合部署地点解读。
- **OpenRouter 回退**：未设置 `OPENAI_API_KEY` 时，`OpenAI/*` 条目自动经 OpenRouter 路由
  （需 `OPENROUTER_API_KEY`，`gpt-*` 映射为 `openai/*`）；`gpt-5.x` 只要有 `OPENROUTER_API_KEY`
  即优先走 OpenRouter（直连需实名认证）。其它提供商（DEEPSEEK / SILICONFLOW 等）如需启用，
  在 `DEFAULT_PROVIDERS` 中补充配置并设置对应环境变量即可。
