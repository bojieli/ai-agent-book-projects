# Chapter 3 experiment requirement/evidence ledger

This ledger treats `book/chapter3.md` as the acceptance source. A mechanism
test, hand-authored fixture, lexical proxy, or synthetic-only dataset may be a
useful check, but it does not by itself close an experiment. Every completed
campaign must write credential-free raw receipts and a canonical
`validation/latest.json` whose artifact/input hashes can be independently
verified.

| Experiment | Manuscript requirement | Companion | Acceptance gate | Canonical evidence |
|---|---|---|---|---|
| 3-1 | Three layers, 20 cases per layer; update memory after each session while retaining only memory state; answer a fresh question; independent LLM judge | `user-memory`, `user-memory-evaluation` | All 60 YAML cases load; campaign proves session-by-session state replacement (no prior raw history in later calls), covers every layer, and records external-judge receipts | `user-memory/validation/latest.json` |
| 3-2 | Four memory modes under one interface, each with generation and retrieval, compared on the 3-1 suite including cost/latency | `user-memory` | Same case selection, generator, answerer, and judge across notes/enhanced notes/JSON cards/advanced JSON cards; exact memory artifacts plus per-mode tokens/latency and layer scores | `user-memory/validation/latest.json` |
| 3-3 | Local Ollama Qwen3 PII detector with structured type/location/confidence output; compare regex, LLM, and hybrid on leakage/utility | `log-sanitization` | Real local model identity is captured; labeled nontrivial samples include structured, semi-structured, and natural-language secrets; span-level precision/recall, residual leakage, utility, and latency are computed | `log-sanitization/validation/latest.json` |
| 3-4 | Real dense embeddings and switchable ANNOY/HNSW comparison | `dense-embedding` | One real embedding model and identical vectors/queries; exact-search ground truth; recall@k, build/query latency, index size/RSS proxy, and incremental-update behavior for both backends | `dense-embedding/validation/latest.json` |
| 3-5 | From-scratch BM25 with transparent tokenization, inverted index, TF/IDF and scoring | `sparse-embedding` | Hand-calculable score check plus a labeled corpus benchmark and exact-vs-synonym failure analysis, using the implemented engine rather than a library substitute | `sparse-embedding/validation/latest.json` |
| 3-6 | Dense + sparse + fusion + neural reranker ablation on semantic, exact-name, multilingual, and code queries | `retrieval-pipeline` | Real local embedding and cross-encoder models; identical labeled queries; recall/MRR/nDCG and latency for sparse, dense, both fusion modes, and reranked hybrid; rank changes retained | `retrieval-pipeline/validation/latest.json` |
| 3-7 | RAPTOR vs GraphRAG on real Intel technical documentation | `structured-index` | Official Intel source URL/revision/hash; LLM-built hierarchical summaries and entity relationships (not hand-authored fixture); concept/detail and relation/multi-hop query sets; build/query metrics and raw LLM receipts | `structured-index/validation/latest.json` |
| 3-8 | Agentic vs non-agentic RAG on Chinese legal QA; simple questions roughly tie, complex multi-hop improves at added latency | `agentic-rag` | Real law corpus and labeled simple/complex questions; live LLM ReAct searches vs one-shot baseline; evidence recall, answer judge, citations, search count, latency, request/response receipts | `agentic-rag/validation/latest.json` |
| 3-9 | Fixed-window conversation indexing and `search_user_memory`; agent iterates when one search is incomplete | `agentic-rag-for-user-memory` | Uses cases from the 3-1 three-layer suite (not a separate proxy); live agent-generated searches; same external judge and layer metrics; search trajectories and raw chunks retained | `agentic-rag-for-user-memory/validation/latest.json` |
| 3-10 | Controlled plain-vs-LLM-contextualized dual index; same queries; BM25 and dense retrieval effects | `contextual-retrieval` | Prefixes generated live from source document plus target chunk; no hand-authored-prefix result is accepted; recall@k/MRR for plain/contextual BM25 and dense/hybrid, plus index-time usage/cost | `contextual-retrieval/validation/latest.json` |
| 3-11 | 3-9 plus contextual prefixes; conflict resolution and Advanced JSON Cards + RAG dual-layer proactive service | `contextual-retrieval-for-user-memory` | Uses the 3-1 layer suite including contradictory-financial and proactive-travel cases; live prefixes and cards; plain vs contextual vs dual-layer ablation; same independent judge and layer metrics | `contextual-retrieval-for-user-memory/validation/latest.json` |
| 3-12 | Real CAIL2018 cases; bottom-up factor discovery from hundreds of samples; modular extraction, archetypes, importance model, held-out advice and judge | `structured-knowledge-extraction` | Official CAIL archive URL/revision/hash; real train/held-out split; live discovery/extraction receipts; cluster diagnostics; held-out matching/advice grounded only in prototype statistics; independent judge and legal disclaimer | `structured-knowledge-extraction/validation/latest.json` |

## Evidence rules

- `validation/runs/<run-id>/evidence.json` is the detailed summarized result.
- `validation/runs/<run-id>/receipts.json` contains raw credential-free provider
  calls. Requests may contain public/synthetic experiment content, never API keys.
- `validation/runs/<run-id>/manifest.json` and `validation/latest.json` record
  SHA-256 hashes of results, receipts, and declared inputs.
- `status: passed` means every gate in that row was actually exercised. A
  campaign must use `blocked` or `partial` when a provider, local model, source
  dataset, or required scale was unavailable; it must not silently fall back to
  a proxy while claiming completion.

## Reproduction order

Run 3-1/3-2 first because 3-9 and 3-11 consume the same three-layer suite and
judge contract. Run 3-4 before 3-6/3-10 so the local dense encoder is warm. The
data-independent experiments (3-3/3-5) can run at any point. Experiment 3-12
downloads a bounded sample from the official CAIL2018 archive and should run
last because its live extraction campaign is the largest.
