# GPT-5.6 Sol Deep Research / GPT-5.6 Sol 深度研究

> Responses API companion for Chapter 1, Experiment 1-3: hosted
> `web_search` + hosted `code_interpreter`, typed tool traces, citations, and an
> intent-clarification continuation. The canonical path is OpenAI GPT-5.6 Sol;
> acceptance is multi-provider and may be closed by any provider whose
> Responses API genuinely closes the search/code loop server-side — currently
> Alibaba Model Studio (DashScope) `qwen3.7-plus`.

← [Chapter 1 index / 返回第 1 章目录](../README.md) ·
📖 [Book experiment / 正文实验](../../book/chapter1.md)

## What this companion implements

The canonical path is the OpenAI **Responses API**, not a Chat Completions
request that merely contains similarly named tool objects. The active agent in
`agent.py` sends:

```json
{
  "model": "gpt-5.6-sol",
  "tools": [
    {"type": "web_search", "search_context_size": "medium"},
    {
      "type": "code_interpreter",
      "container": {"type": "auto", "memory_limit": "4g"}
    }
  ],
  "reasoning": {"effort": "high"},
  "text": {"verbosity": "high"}
}
```

The DashScope backend speaks the same `/responses` protocol against
`{DASHSCOPE_BASE_URL}/responses` with the provider's hosted-tool shapes:

```json
{
  "model": "qwen3.7-plus",
  "tools": [{"type": "web_search"}, {"type": "code_interpreter"}],
  "stream": true
}
```

DashScope runs thinking natively (no `reasoning.effort`/`text.verbosity`
knobs) and its gateway drops non-streaming requests that stay silent for
about 60 seconds, so the backend always streams and keeps the final
`response.completed` object, which has the same shape as a non-streaming
response.

Acceptance is based on provider output items. A successful ASEAN-capitals run
must contain completed `web_search_call` and `code_interpreter_call` items,
clickable URL citations, and the computed closest pair. A text answer that says
it used Python does not pass without the provider tool receipt.

The second scenario sends the deliberately ambiguous Bitcoin request used in
the chapter, requires the first response to clarify material preferences before
using tools, then continues with `previous_response_id` after the user supplies
the data source and indicators.

## Current evidence status

Run the complete validator with:

```bash
cd chapter1/search-codegen
python run_experiment_1_3.py --backends openai dashscope --reasoning high
```

The latest evidence is [validation/latest.json](validation/latest.json); raw
credential-free receipts, a manifest, and SHA-256 sidecars live in
`validation/runs/real_20260731T170529Z/`.

Result of the 2026-07-31 multi-provider acceptance run: **passed**, with
`dashscope` (`qwen3.7-plus`) as the acceptance backend.

- ASEAN capitals: one hosted `web_search_call` batching ten model-issued
  coordinate queries, then a hosted `code_interpreter_call` that enumerated all
  45 haversine pairs and found Kuala Lumpur–Singapore at 316.35 km — the same
  pair as the independent local reference computed from standard coordinates.
- Bitcoin technical analysis: the first turn asked which data source and which
  indicators to use **without calling any tool**; the continuation via
  `previous_response_id` ran 3 model-directed search rounds and 4 hosted
  `code_interpreter_call`s computing MA7/MA20, RSI14, MACD(12,26,9), period
  return and max drawdown, and plotted a close-price chart in the sandbox.
- The official OpenAI `gpt-5.6-sol` path is still intact but remains
  quota-blocked: both calls returned `credit_balance_exhausted` before any
  hosted tool ran, which is recorded in the same evidence file.
- Honest qualifications: the DashScope sandbox has no outbound network, so the
  daily closes were extracted through web search (the model disclosed this in
  its report); the chart PNG stays inside the sandbox because this Responses
  API returns execution logs only; and `qwen3.7-plus` only asks before acting
  when the system prompt carries an explicit clarify-first rule — the shipped
  prompt encodes it.
- The OpenRouter route is retained strictly as a diagnostic and is never
  accepted. No fallback model, local Python replacement, fabricated tool
  trace, or Chat-Completions approximation is counted as fulfillment.

Earlier blocked attempts are kept under `validation/real_20260729T155459Z/`
and `validation/real_20260730T033800Z/`.

## Setup and CLI

Python 3.9+ is required.

```bash
# From the repository root: use the shared Chapter 1 environment
uv sync --locked --extra ch1

# Activate it before changing directories:
source .venv/bin/activate

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch1]"

cd chapter1/search-codegen

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

export OPENAI_API_KEY=your-openai-api-key

# Exact official path
python main.py --backend openai --mode single \
  --request "东盟 10 国首都之间最近的一对是哪两个？请搜索并用 Python 计算" \
  --reasoning high --verbosity high --output result.json

# Equivalent-provider path (eligible for acceptance): Alibaba Model Studio
export DASHSCOPE_API_KEY=your-dashscope-api-key
python main.py --backend dashscope --mode single \
  --request "东盟 10 国首都之间最近的一对是哪两个？请搜索并用 Python 计算" \
  --output result.json

# Inspect the exact request without an API call
python main.py --backend openai --dry-run \
  --request "东盟 10 国首都之间最近的一对？" \
  --reasoning max --verbosity high

# Proxy diagnostic only; not canonical acceptance
export OPENROUTER_API_KEY=your-openrouter-api-key
python main.py --backend openrouter --mode single --request "Search current news"
```

Important options:

| Option | Meaning |
|---|---|
| `--backend openai` | Canonical `https://api.openai.com/v1/responses` path |
| `--backend dashscope` | Equivalent-provider path: DashScope Responses API, hosted `web_search` + `code_interpreter`, eligible for acceptance |
| `--backend openrouter` | Explicit proxy diagnostic; never silently substituted |
| `--reasoning` | `none`, `low`, `medium`, `high`, `xhigh`, or GPT-5.6 `max` |
| `--verbosity` | Responses `text.verbosity`: `low`, `medium`, or `high` |
| `--output` | Saves request, typed output items, citations, usage, and raw response |

## Verification

```bash
python -m pytest -q test_responses_agent.py
python -m py_compile agent.py config.py main.py run_experiment_1_3.py
```

The validator checks exact model identity, direct-vs-proxy provenance, both
hosted tool types, citations, clarification order, continuation linkage, token
usage, reported provider cost when available, and credential-free raw evidence.

## Official sources

- [GPT-5.6 Sol model](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
- [Web search](https://developers.openai.com/api/docs/guides/tools-web-search)
- [Code Interpreter](https://developers.openai.com/api/docs/guides/tools-code-interpreter)
- [GPT-5.6 model guidance](https://developers.openai.com/api/docs/guides/model-guidance?model=gpt-5.6-sol)
- [Alibaba Model Studio code interpreter (DashScope)](https://help.aliyun.com/zh/model-studio/qwen-code-interpreter)

## 中文说明

本项目使用正文所述的**精确协议**：Responses API、托管 `web_search` 与托管
`code_interpreter`。验收依据是服务端返回的 `web_search_call` /
`code_interpreter_call` 和 URL 引用，而不是代码里“声明了工具”或答案里
“声称用过 Python”。

按作者批准的多提供商政策，验收不绑定官方 OpenAI 账号：官方 `gpt-5.6-sol` 路径
完整保留（当前 Key 推理返回 `credit_balance_exhausted`，已在证据中如实记录），
具备等价托管工具的提供商同样可以验收。2026-07-31 的正式运行用阿里云百炼
`qwen3.7-plus`（DashScope Responses API）通过了全部验收门：东盟任务先搜索十个
首都坐标、再用托管 Python 枚举 45 对大圆距离（吉隆坡—新加坡 316.35 km，与独立
本地参考一致）；比特币任务先在不用任何工具的情况下澄清数据源与指标，再通过
`previous_response_id` 继续，完成 3 轮模型主导的搜索与 4 次托管代码执行
（MA7/MA20、RSI14、MACD、区间收益、最大回撤与走势图）。OpenRouter 只作为诊断
路径明确保留，不会被包装成替代品。
