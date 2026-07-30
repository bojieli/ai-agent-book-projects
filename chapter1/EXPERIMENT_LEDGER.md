# Chapter 1 experiment requirement/evidence ledger

The Chinese manuscript is authoritative. Runtime completion and manuscript
behavior claims are kept separate: a real, correctly controlled ablation may
finish even when one claimed degradation is not observed.

| Experiment | Exact manuscript gate | Status | Canonical evidence / qualification |
|---|---|---|---|
| 1-1 | One complete baseline plus removal of tool definitions, tool results, assistant reasoning, and prior history on the same multi-currency ReAct task | Exact five-arm real run completed; one prose behavior not reproduced | `context/validation/latest.json` retains direct Kimi K3 requests/responses, all tool observations, expected totals, and context contracts. Baseline was correct; no tools removed action; hidden tool results and history caused repeated calls. Removing reasoning still completed correctly, so the manuscript’s “contradictory decisions” claim is explicitly false for this run rather than fabricated. |
| 1-2 | Exact Kimi K3 with provider-hosted Formula web search, model-directed multiple search rounds, reasoning, current answer, and authoritative links | Passed | `web-search-agent/validation/latest.json`: direct Moonshot endpoint, exact model, 15 succeeded distinct Formula fibers over multiple rounds, official ASEAN/Indonesian sources, real response IDs and usage. |
| 1-3 | Official GPT-5.6 Sol Responses API with hosted web search + hosted Python on ASEAN distance, plus clarification-before-tools and continued Bitcoin analysis | Blocked before inference | `search-codegen/validation/latest.json`: official OpenAI calls reached the endpoint but returned `insufficient_quota` before any hosted tool execution. OpenRouter diagnostics are not accepted as the official experiment; README status remains 🚧. |

Legacy demos and provider-compatible substitutes are teaching aids only. A
provider rejection before inference is not converted into a model failure and
does not authorize accepting a narrower proxy.
