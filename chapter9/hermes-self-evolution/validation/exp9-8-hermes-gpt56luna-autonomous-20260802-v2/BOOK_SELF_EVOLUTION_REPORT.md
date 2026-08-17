# Book-Driven Self-Evolution Report

## Run identity

- Starting commit: `85c8956ec7f2b4607509980794995e1c5e21e292` (the pinned HEAD at inspection time).
- Model/provider: `openai/gpt-5.6-luna` via `openrouter`.
- Book source read: `/home/ubuntu/ai-agent-book/book-en/`, all ten chapter files inspected by heading scans, targeted searches, and section reads. The book repository was not modified.

## Opportunities identified and disposition

1. **Evidence-backed trajectory signals (implemented).** Chapter 8, “Deriving Learning Signals from Operational Trajectories” (§8, lines 19–61), says evolution must start from evaluation, preserve immutable raw trajectories, and distinguish outcome/process evidence rather than trusting a scalar or self-summary. Hermes already persisted trajectories through `run_agent.py:2279-2292`, `agent/agent_runtime_helpers.py:76-243`, and `agent/trajectory.py:30-61`, but the JSONL record had no structured, deterministic evaluation signal. I added `agent.trajectory.derive_trajectory_signals()` and persisted its result under `evaluation`. It only inspects observable tool results (`success: false`), records completion status, and leaves the original messages unchanged.

2. **Offline evolution with validation and rollback (already substantially present; no duplicate implementation).** Chapter 8, “Building a Continual-Evolution Closed Loop” (§8, lines 239–369), requires candidate changes, validation, release, and rollback. Hermes has the curator lifecycle in `agent/curator.py:1496-1760`, skill validation in `tools/skill_manager_tool.py:566-623`, and recoverable snapshots/rollback in `agent/curator_backup.py:216-638`, with behavior tests in `tests/agent/test_curator.py` and `tests/agent/test_curator_backup.py`. Adding another update system would duplicate existing infrastructure and increase mutation risk, so this was rejected.

3. **Ablation and observability campaign (deferred as a campaign, not silently claimed).** Chapter 6, “Ablation Infrastructure” (§6, lines 662–706), and Chapter 1, “Context ablation” (§1, lines 141–159), call for fixed baselines, one-feature-at-a-time removal, and operational evidence. Hermes has trajectory persistence, curator reports, usage accounting, and tests, but this run did not have a fixed task corpus, deterministic model fixture, or safe experiment runner. Building a broad benchmark harness here would be speculative and larger than the smallest cohesive improvement. The report defines the campaign below.

4. **Multi-agent independent cross-validation (deferred).** Chapter 10, “When Is Multi-Agent Truly Better Than a Single Agent?” (§10, lines 69–96) and “Cascading Amplification of Errors” (§10, lines 577–598), require independent information or evidence, not merely more agents. Hermes already has delegation and kanban infrastructure (`tools/delegate_tool.py`, `plugins/kanban/`, and the delegation configuration), so a generic reviewer would add cost and coordination surface without a concrete task contract. No change made.

5. **Context-cache stability (preserved, not changed).** Chapter 2, “KV Cache-Friendly Context Design” (§2, lines 404–546), says stable system/tool prefixes are architectural constraints. The implementation adds metadata only to persisted JSONL trajectories and does not alter prompts, tools, or in-conversation messages.

## Changes made

- Added `derive_trajectory_signals()` to `agent/trajectory.py`.
- Added an `evaluation` object to saved JSONL entries. It contains `outcome`, `tool_errors`, `tool_results`, and a conservative `process_warning`.
- Added behavior-contract tests in `tests/agent/test_trajectory.py` covering tool-error detection and the invariant that persisted messages are unchanged.

The implementation deliberately does not call an LLM judge, rewrite skills, alter prompts, infer success from prose, or change role ordering. This keeps the core tool surface and safety gates unchanged.

## Deliberately rejected or deferred

- No automatic skill/prompt/program/model mutation from one trajectory. Chapter 8 explicitly warns that unverified online updates amplify noise and prompt injection (§8, lines 3–11, 297–369).
- No new core tool, environment variable, or dependency.
- No broad evaluation dashboard or automatic ablation scheduler without a fixed corpus and acceptance criteria.
- No claim that deterministic tool-error counts are a complete verifier; they are only low-level evidence.

## Review round correction

The independent review identified that the first implementation parsed only bare JSON, while the production conversion path emits bundled `<tool_response>` XML containing JSON envelopes with nested `content`. The implementation now recognizes multiple wrapped entries, parses nested object/string content conservatively, and ignores malformed or unsupported shapes. The new end-to-end test exercises `agent.agent_runtime_helpers.convert_to_trajectory_format()` before saving and verifies one failed result among two bundled responses. The original `conversations` list is asserted unchanged.

## Second review round correction

The fresh review found two real persistence paths that bypassed `save_trajectory()`: the JSONL entry assembled in `batch_runner.py` and the pretty-printed sample entry assembled in `run_agent.py` when `save_sample` is enabled. I inspected both paths and introduced `agent.trajectory.build_trajectory_entry()` as the shared entry builder. `agent/trajectory.py:91-128` now uses it for the existing append writer; `batch_runner.py:49-50,473-486` uses it while retaining its existing JSONL file I/O, flush/fsync behavior, filenames, and batch-specific fields; `run_agent.py:203-204,7530-7540` uses it while retaining the sample filename, pretty-printing, error handling, and query field. The builder preserves the supplied `conversations` object and adds the same backward-compatible `evaluation` field to all three persistence paths.

The focused contract test verifies shared-field preservation. The existing conversion-and-save test continues to verify production-shaped XML tool results and unchanged conversation data.

## Third review round correction

The third review found two issues. First, a single recognized envelope could increment `tool_errors` once for top-level `success: false` and again for nested `content.success: false`. The signal derivation now computes one `failed` boolean per recognized payload, so each tool result contributes at most one error. A regression test covers both flags together.

Second, a repository-wide search for direct ShareGPT/trajectory-shaped persistence found `mini_swe_runner.py` as the remaining production trajectory producer. Its `run_task()` result and `run_batch()` JSONL path now use `build_trajectory_entry()` while retaining the existing result fields, output filename handling, immediate flushes, and error record behavior. The empty error result also receives the metadata contract. The search also found unrelated records containing a `conversations` key (`mcp_serve.py`, session/audit exports, gateway state, plugins, and compression/transformation utilities); these are not ShareGPT trajectory producers and were deliberately left unchanged. The scope is therefore all identified Hermes ShareGPT trajectory producers: standard `save_trajectory()`, `run_agent.py` sample output, `batch_runner.py`, and `mini_swe_runner.py`.

## Verification

Exact commands and results:

```text
python3 - <<'PY' ...  # book file inventory and all-chapter heading/search inspection
# Result: all ten chapter*.md files inspected; targeted section output was collected.

.venv/bin/python -m pytest tests/agent/test_trajectory.py -q
# Result: failed before test execution: No module named pytest

scripts/run_tests.sh tests/agent/test_trajectory.py -q
# Result: failed because no configured virtualenv with pytest exists.

uv run --with pytest pytest tests/agent/test_trajectory.py -q
# Result (third review round): 6 passed in 0.12s

uv run --with pytest pytest tests/agent/test_trajectory.py tests/test_batch_runner_checkpoint.py tests/test_batch_runner_durability.py tests/integration/test_batch_runner.py tests/test_trajectory_compressor.py -q
# Result (third review round): 44 passed in 0.62s

python3 -m py_compile agent/trajectory.py agent/agent_runtime_helpers.py batch_runner.py run_agent.py mini_swe_runner.py tests/agent/test_trajectory.py
# Result (third review round): passed

git diff --check
# Result (third review round): passed
```

The repository's prescribed runner was attempted exactly and could not run because the checkout's `.venv` lacks pytest; the equivalent isolated `uv run` verification passed both new tests. No full suite was claimed.

## Limitations

- One implementation run and two unit tests show only that the metadata contract works. They are not evidence that trajectory signals improve task success, reduce cost, or improve safety.
- `success: false` detection depends on tool handlers exposing that field in JSON; non-JSON output and domain-specific failures remain uncertain.
- `completed=True` means the existing runtime completion path reported completion, not that the external task is correct. The field is intentionally named `outcome` and accompanied by process evidence rather than treated as ground truth.
- No live model calls, benchmark tasks, or user data were used.

## Proposed ablation campaign

Use a fixed, versioned task corpus with isolated temporary Hermes homes, pinned model/provider/config, fixed tool availability, and deterministic seeds where supported. Record success, tool-error rate, policy/safety violations, latency, token usage, and cache-related request metadata. Run enough repetitions for confidence intervals and keep a held-out task split.

Baseline: current Hermes with trajectory persistence and the new evaluation metadata enabled, but no automatic mutation. Compare one feature disabled at a time:

1. Disable structured trajectory evaluation metadata; retain raw trajectory persistence.
2. Disable raw trajectory persistence; retain ordinary task execution.
3. Disable curator offline review while retaining metadata.
4. Disable curator backup/rollback, only in a disposable sandbox, to measure operational risk—not production behavior.
5. Disable context compression while retaining stable prefixes.
6. Disable delegation for tasks that have a defined delegation path.
7. Disable individual skill injection/progressive disclosure for matching task families.

For every comparison, require that the fixed baseline and ablation use identical prompts, toolsets, model, credentials, task order, and safety/approval settings. Treat any regression in safety or policy compliance as a release blocker even if task success rises. The campaign should first validate that the new metadata predicts independently verified failures, then test whether using it in a separately reviewed offline evolution process improves held-out performance without negative transfer. A single run must never authorize self-modification.
