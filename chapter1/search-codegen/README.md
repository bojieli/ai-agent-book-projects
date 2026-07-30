# GPT-5.6 Sol Deep Research / GPT-5.6 Sol 深度研究

> Exact OpenAI Responses API companion for Chapter 1, Experiment 1-3: hosted
> `web_search` + hosted `code_interpreter`, typed tool traces, citations, and an
> intent-clarification continuation.

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
python run_experiment_1_3.py --backends openai openrouter --reasoning high
```

The latest evidence is [validation/latest.json](validation/latest.json).

Current result after a fresh official-OpenAI retry on 2026-07-30:

- The configured OpenAI key authenticates and can retrieve the
  `gpt-5.6-sol` model, but `/v1/responses` returns `insufficient_quota` before
  either hosted tool runs.
- The OpenRouter route is retained strictly as a diagnostic. It can proxy a
  real `openai/gpt-5.6-sol` Responses web-search call, but it does not establish
  the canonical OpenAI account execution and its hosted Python/container path
  currently fails. It is therefore not accepted as Experiment 1-3 evidence.
- No fallback model, local Python replacement, fabricated tool trace, or
  Chat-Completions approximation is counted as fulfillment.

The credential-free failed-transport receipt is retained at
`validation/real_20260730T033800Z/evidence.json`: both official Responses calls
returned HTTP 429 with `code=insufficient_quota` before a model response or
hosted-tool event, and provider usage remained zero.

Experiment 1-3 remains externally blocked until the official OpenAI account has
inference quota and both provider-hosted tool receipts can be saved.

## Setup and CLI

Python 3.9+ is required.

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=...

# Exact official path
python main.py --backend openai --mode single \
  --request "东盟 10 国首都之间最近的一对是哪两个？请搜索并用 Python 计算" \
  --reasoning high --verbosity high --output result.json

# Inspect the exact request without an API call
python main.py --backend openai --dry-run \
  --request "东盟 10 国首都之间最近的一对？" \
  --reasoning max --verbosity high

# Proxy diagnostic only; not canonical acceptance
export OPENROUTER_API_KEY=...
python main.py --backend openrouter --mode single --request "Search current news"
```

Important options:

| Option | Meaning |
|---|---|
| `--backend openai` | Canonical `https://api.openai.com/v1/responses` path |
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

## 中文说明

本项目已改为正文所述的**精确协议**：官方 OpenAI Responses API、
`gpt-5.6-sol`、托管 `web_search` 与托管 `code_interpreter`。验收依据是服务端
返回的 `web_search_call` / `code_interpreter_call` 和 URL 引用，而不是代码里
“声明了工具”或答案里“声称用过 Python”。

当前官方 Key 能通过模型查询，但推理返回 `insufficient_quota`，所以实验尚未完成。
OpenRouter 只作为诊断路径明确保留，不会被包装成官方托管 Python 的替代品。额度恢复后，
运行上面的 `run_experiment_1_3.py`；只有东盟搜索计算与“先澄清、再研究”两个场景都通过，
`acceptance.passed` 才会变为 `true`。
