# Book-Driven Self-Evolution Report

## Run identity

- Starting commit: `85c8956ec7f2b4607509980794995e1c5e21e292` (the pinned HEAD before edits).
- Model/provider: `openai/gpt-5.6-luna` / `openrouter`.
- Book audited: English edition under `/home/ubuntu/ai-agent-book/book-en/`; all ten `chapter1.md`–`chapter10.md` files were inspected with section-heading and targeted-term searches, followed by section-level reads. The book repository was not modified.

## Four-claim audit

| Reader claim | Book evidence | Hermes evidence | Disposition |
|---|---|---|---|
| Product-level ablation infrastructure | Chapter 1, “Harness Engineering” (lines 149–157), defines remove-one-component experiments; Chapter 6, “Ablation Infrastructure” (lines 662–706), calls for feature flags, fixed baselines, A/B methodology, and privacy-aware analytics. | Hermes has many config gates and operational telemetry, e.g. `hermes_cli/config_defaults.py` (`display.verify_on_stop`, `display.file_mutation_verifier`, `memory.write_approval`, `curator.*`), trajectory saving in `run_agent.py:2274–2292`, and evaluation/observability hooks, but no product-level campaign runner that holds a task set/model fixed and compares one disabled feature at a time. | **Absent** as a cohesive product capability; deferred. A campaign runner would be a larger evaluation product, not a safe incidental core feature. |
| Model-visible Agent Status Bar | Chapter 2, “Agent Status Bar” (lines 787–817) distinguishes model-visible state from the human terminal bar and requires placement at context end; lines 819–835 give the structured `<agent_status>` example. Chapter 9, lines 233–239, also uses it as an inter-agent text channel. | Human-facing lifecycle/status plumbing exists in `run_agent.py:937–975`, `agent/display.py`, `hermes_cli/status.py`, and tests such as `tests/cli/test_cli_status_bar.py`; the model prompt is cached in `agent/turn_context.py:613–617`, while request-local API messages are built in `agent/conversation_loop.py:1488–1614`. Before this change there was no model-visible aggregate status block. | **Partly present**. Implemented the smallest compatible slice: opt-in request-local `<agent_status>` with API-call budget and active todo state. |
| Forgetting/consolidation for persistent memory | Chapter 3, “Memory Compression and Organization Mechanisms” (lines 236–260), requires organization and privacy; Chapter 8, “Sleep Learning: Consolidation, Forgetting, and Capability Maintenance” (lines 297–320), requires offline batch consolidation, conflict handling, expiry/archive/delete with provenance and rollback. | Bounded memory is configured in `hermes_cli/config_defaults.py:1578–1602`; provider orchestration is in `agent/memory_manager.py`; background memory/skill review is in `agent/background_review.py`; Skill usage/staleness/archival is handled by `agent/curator.py`. These are real controls, but Curator is for agent-created Skills and bounded `MEMORY.md` is not a general evidence-backed memory consolidator with conflict resolution/retention evaluation. | **Partly present**, with the missing general mechanism intentionally deferred. Extending it safely needs provider-specific semantics, provenance, retention/transfer sets, and approval/rollback design; blindly deleting memory would violate safety and user expectations. |
| General proposer-reviewer with independent execution-grounded verification | Chapter 1, lines 247–281, defines Verify/Correct; Chapter 5’s coding-harness material and Chapter 10, “Peer Collaboration Pattern” (lines 290–318), require a reviewer to obtain new execution/render/tool evidence, not merely reread text. | Hermes already has execution-grounded file mutation verification (`run_agent.py:3342–3465`), verify-on-stop and bounded `pre_verify` continuation (`agent/conversation_loop.py:6840–6959`), plugin `pre_verify` hooks, approval gates, background review (`agent/background_review.py`), and delegation (`tools/delegate_tool.py`). There is no universal artifact contract and no always-on independent proposer/reviewer workflow. | **Partly present**, and the proposed generic always-on mechanism is **intentionally deferred/incompatible as a default**: it would add cost/core surface and could duplicate existing verification. Use artifact-specific plugins/workflows when a concrete verifier exists. |

## Change made

Added an opt-in model-visible status bar:

- `agent/model_status_context.py` renders a bounded, deterministic `<agent_status>` block containing API-call budget and active todo information. It ignores completed tasks and arbitrary extra fields. Its persistent sidecar helper appends only to the newest request message and stores the resulting wire content in `api_content`.
- `agent/agent_init.py` reads `display.model_status_bar` (default false).
- `hermes_cli/config_defaults.py` documents `display.model_status_bar: false`.
- `agent/conversation_loop.py` appends status only to the newest API request copy and persists that exact wire content in the existing `api_content` sidecar. On later requests, historical sidecars are replayed unchanged, while the newest status is appended only to the newest message. Clean transcript content, roles, and the cached system prompt remain unchanged.
- `tests/agent/test_model_status_context.py` adds behavior-contract tests for formatting, active-task selection, field isolation, and three successive request builds with byte-identical replay of all earlier wire messages.

Deliberately rejected/deferred:

- No always-on status bar: it costs tokens and is therefore opt-in.
- No mutation of `MEMORY.md`/external providers: the evidence supports a larger consolidation lifecycle, not an unsafe delete/merge heuristic.
- No generic proposer-reviewer core tool or mandatory second model: existing execution-grounded gates cover concrete paths; a universal reviewer needs a typed artifact/verifier contract and a campaign showing benefit.
- No ablation runner in this change: it needs fixed datasets, outcome metrics, isolation, privacy/telemetry policy, and feature-flag control across surfaces.

## Verification

Exact commands run:

1. `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py`
   Result: exit code 0; compilation succeeded.
2. `python3 - <<'PY' ... from agent.model_status_context import build_model_status_context ... PY`
   Result: exit code 0; printed the expected block:
   `<agent_status>`, `API calls: 3/10`, `Active tasks: 1 (in progress: 1)`, `Next active task: b — run tests`, `</agent_status>`.
3. `scripts/run_tests.sh tests/agent/test_model_status_context.py -q`
   Result: **blocked**, exit code 1. The repository runner reported no virtualenv containing pytest (`.venv` exists but has no pytest; no `venv`/`HERMES_PYTHON` fallback). No test result was fabricated.
4. `uv run --with pytest pytest tests/agent/test_model_status_context.py -q`
   Result: **passed**, `2 passed in 0.07s` (the isolated behavior-contract tests ran successfully through uv).
5. `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py && git diff --check`
   Result: **passed**, exit code 0; no whitespace errors.

The repository wrapper was blocked by its environment lacking pytest, but the focused tests did execute and pass through `uv run --with pytest`. Existing tests were not weakened, and no approval, validator, or safety threshold was changed.

## Independent review round

The first candidate was rejected because it rewrote previously sent request bytes when adding each new status. This round corrected that defect by using persistent `api_content` sidecars and added three-request replay coverage. The reviewer’s scope was not expanded: no ablation campaign, memory consolidator, or generic reviewer loop was added.

## Review-round verification

Exact commands and results for the correction:

- `uv run --with pytest pytest tests/agent/test_model_status_context.py -q` — **passed**, `3 passed in 0.07s`.
- `uv run --with pytest pytest tests/agent/test_api_content_sidecar.py tests/run_agent/test_background_review_cache_parity.py tests/agent/test_turn_context.py -q` — **passed**, `36 passed in 9.51s`.
- `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py` — **passed**, exit code 0.
- `git diff --check` — **passed**, exit code 0.

The focused replay test proves that each earlier request message remains byte-identical in later request constructions and that the newest status is attached to the newest message. These are wire-construction tests, not an end-to-end provider run.

## Second independent review round

The second review found that the replay test helper accepted list-valued sidecars more broadly than the production request builder, which only replayed non-empty strings. The correction now centralizes the production type contract in `replay_api_content_sidecar()` (`agent/model_status_context.py`) and uses it in `agent/conversation_loop.py` for both current-turn and historical replay. Only non-empty strings are supported; lists/multimodal content, empty strings, mappings, numbers, and other unsupported values fail closed because Hermes persists `api_content` as an optional string. The tests call this same helper and cover string, list, empty, and unsupported values.

Exact commands and results for this review round:

- `uv run --with pytest pytest tests/agent/test_model_status_context.py -q` — **passed**, `5 passed in 0.09s`.
- `uv run --with pytest pytest tests/agent/test_api_content_sidecar.py tests/run_agent/test_background_review_cache_parity.py tests/agent/test_turn_context.py -q` — **passed**, `36 passed in 9.35s`.
- `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py` — **passed**, exit code 0.
- `git diff --check` — **passed**, exit code 0.

The review correction validates the production replay type check rather than using a more permissive test-only reconstruction. No book files were changed, and no downstream task improvement is claimed.

## Third independent review round

The third review found that list-valued sidecars were only safe in the in-memory request builder, not across Hermes’ persistence boundary: `hermes_state.py` and the flush path in `run_agent.py` persist `api_content` as an optional string, and `agent/turn_context.py` exposes string-only sidecar helpers. The correction therefore fails closed for every non-string content value and does not attach model status to unsupported multimodal/list messages. No database schema or persistence contract was widened.

Exact commands and results for this review round:

- `uv run --with pytest pytest tests/agent/test_model_status_context.py -q` — **passed**, `4 passed in 0.09s`.
- `uv run --with pytest pytest tests/agent/test_api_content_sidecar.py tests/run_agent/test_background_review_cache_parity.py tests/agent/test_turn_context.py -q` — **passed**, `36 passed in 9.35s`.
- `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py` — **passed**, exit code 0.
- `git diff --check` — **passed**, exit code 0.

No multimodal support is claimed, and no downstream task improvement is claimed.

## Fourth independent review round

The fourth review found two production-path defects. First, status was being attached to the newest tool result even though Hermes persists and replays `api_content` only for user/assistant messages. The attachment helper now searches backward for the newest durable user/assistant message, leaving tool results unchanged; the production replay path remains restricted to those roles. This preserves role ordering, clean transcript content, and durable sidecar replay. Second, TODO identifiers were not bounded. `build_model_status_context()` now caps identifiers at 96 characters, descriptions at 200 characters, and the complete rendered block at 1200 characters while retaining the closing tag.

New behavior-contract tests cover a successive request whose newest message is a tool result, confirm the sidecar is attached to the latest durable message and replays unchanged, and verify a 100,000-character TODO identifier cannot exceed the output bound. They call the same production replay helper used by `conversation_loop.py`.

Exact commands and results for this review round:

- `uv run --with pytest pytest tests/agent/test_model_status_context.py -q` — **passed**, `6 passed in 0.10s`.
- `uv run --with pytest pytest tests/agent/test_api_content_sidecar.py tests/run_agent/test_background_review_cache_parity.py tests/agent/test_turn_context.py -q` — **passed**, `36 passed in 9.37s`.
- `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py` — **passed**, exit code 0.
- `git diff --check` — **passed**, exit code 0.

No downstream task improvement is claimed.

## Fifth independent review round

The fifth review identified a realistic tool-loop placement failure: assistant tool-call messages commonly have `content=None`, followed by a string tool result. Searching backward for a durable assistant then failed closed, and text-bearing assistant messages would place status before the newest tool evidence. The durable correction now targets the newest message directly. String `api_content` sidecars are persisted and replayed for `user`, `assistant`, and `tool` roles; unsupported values still fail closed, and clean transcript content and role/tool-call ordering are unchanged. When the newest message is a tool result, status is appended after that evidence, closest to generation.

The focused successive-request test now uses assistant tool-call messages with `content=None` followed by string tool results across three requests. It asserts historical wire equality, status placement after the newest tool result, and durable sidecar attachment. The adversarial identifier/output-bound test remains enabled.

Exact commands and results for this review round:

- `uv run --with pytest pytest tests/agent/test_model_status_context.py -q` — **passed**, `5 passed in 0.10s`.
- `uv run --with pytest pytest tests/agent/test_api_content_sidecar.py tests/run_agent/test_background_review_cache_parity.py tests/agent/test_turn_context.py -q` — **passed**, `36 passed in 10.04s`.
- `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py` — **passed**, exit code 0.
- `git diff --check` — **passed**, exit code 0.

No downstream task improvement is claimed.

## Sixth independent review round

The sixth review found that status sidecars were added after normal row persistence and were therefore only in-memory: `_db_persisted` rows were skipped by the append-only flush, so a restart could lose the sidecar. The correction adds the smallest string-only row-identity backfill path. `hermes_state.py` now exposes `update_message_api_content(session_id, message_row_id, api_content)`, the flush records the returned durable row id, and persisted rows with a later status backfill are updated by that id. The sidecar remains a string; clean transcript content, role/tool ordering, and unsupported-value rejection are unchanged.

The production contract test now persists user → assistant tool-call (`content=None`) → string tool-result rows through `SessionDB`, attaches status to the newest tool row, performs the row-identity update, closes and reopens the database, and asserts the same sidecar and replayed wire bytes. It would fail if only the in-memory dictionary changed.

Exact commands and results for this review round:

- `uv run --with pytest pytest tests/agent/test_model_status_context.py -q` — **passed**, `6 passed in 0.50s`.
- `uv run --with pytest pytest tests/agent/test_api_content_sidecar.py tests/run_agent/test_background_review_cache_parity.py tests/agent/test_turn_context.py -q` — **passed**, `36 passed in 9.43s`.
- `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py hermes_state.py` — **passed**, exit code 0.
- `git diff --check` — **passed**, exit code 0.

No downstream task improvement is claimed.

## Seventh independent review round

The seventh review found that rebuilding a request for the same newest message appended another status block each time. The projection is now idempotent at the production persistence boundary: the first non-empty string `api_content` sidecar is treated as the feature-owned projection and reused verbatim on retries, including after reload. A later volatile status is deliberately ignored for that same message, so previously sent bytes remain fixed. User-authored status-looking text in clean content is never parsed or removed; only the sidecar is recognized. Stable row-identity backfill remains in place through `update_message_api_content()`.

The regression test repeats the same-message build 20 times, then repeats it after a real `SessionDB` close/reopen, asserting identical wire bytes and exactly one owned status block. Realistic tool-call placement, persistence reload, adversarial output bounds, and unsupported-type rejection remain covered.

Exact commands and results for this review round:

- `uv run --with pytest pytest tests/agent/test_model_status_context.py -q` — **passed**, `7 passed in 0.84s`.
- `uv run --with pytest pytest tests/agent/test_api_content_sidecar.py tests/run_agent/test_background_review_cache_parity.py tests/agent/test_turn_context.py -q` — **passed**, `36 passed in 9.42s`.
- `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py hermes_state.py` — **passed**, exit code 0.
- `git diff --check` — **passed**, exit code 0.

No downstream task improvement is claimed.

## Eighth independent review round

The eighth review found a collision with Hermes’ existing `api_content` uses for memory/plugin prefetch and sanitization-divergence replay. The status helper now preserves any pre-existing string sidecar byte-for-byte as the base and adds an exact terminal ownership envelope: `<hermes_status_projection>` containing the status block and `</hermes_status_projection>`. Only that exact terminal form, with the expected `<agent_status>` structure, is recognized as feature-owned on retries; lookalike or malformed content remains ordinary base text and is never deleted. The projection is therefore idempotent across persistence/reload while ordinary API-only sidecars still receive one status projection. Unsupported values remain fail-closed and stable row-identity backfill remains unchanged.

Added coverage uses a realistic pre-existing memory/plugin sidecar, repeats same-message builds, checks exact base-byte preservation and one status block, and includes a malformed/lookalike marker.

Exact commands and results for this review round:

- `uv run --with pytest pytest tests/agent/test_model_status_context.py -q` — **passed**, `8 passed in 0.84s`.
- `uv run --with pytest pytest tests/agent/test_api_content_sidecar.py tests/run_agent/test_background_review_cache_parity.py tests/agent/test_turn_context.py -q` — **passed**, `36 passed in 9.41s`.
- `python3 -m py_compile agent/model_status_context.py agent/conversation_loop.py agent/agent_init.py run_agent.py hermes_state.py` — **passed**, exit code 0.
- `git diff --check` — **passed**, exit code 0.

No downstream task improvement is claimed.

## Terminal acceptance loop

After the eight correction rounds, the experiment ran a fresh Hermes reviewer
with an isolated home and no proposer-session context. Each attempt inspected the
current diff and production persistence paths, reran the focused checks, and was
required to end in `VERDICT: ACCEPT` or `VERDICT: REJECT`. Five terminal attempts
rejected the candidate and their findings were returned to the original Hermes
session: tool-result placement and unbounded identifiers, realistic
`content=None` tool-call placement, post-flush database persistence, retry
idempotence, and composition with pre-existing memory/plugin sidecars. The sixth
fresh attempt accepted the resulting candidate.

The accepted version passed **8 new behavior-contract tests and 36 existing
sidecar/cache/turn-context regression tests**. The new coverage includes a real
`SessionDB` close/reopen, unchanged-message retries, realistic assistant tool calls,
tool-result placement closest to generation, bounded adversarial TODO data, and
byte-preserving composition with existing API-only sidecars. This closes the
proposer-reviewer correction loop for the scoped candidate: a rejection caused the
running Hermes proposer to update its own checkout, and independent review repeated
until acceptance. It still does not establish downstream task-quality uplift.

## Limitations

This is an implementation and audit run, not evidence that the status bar improves task success. The repository wrapper was initially blocked because its environment lacked pytest, but the final focused suite did execute through `uv run --with pytest` and passed 44 tests. That scoped suite is not the repository's entire test matrix. The status block is deliberately small and currently reports only budget and todo state; it does not summarize arbitrary tool-call counts, wall-clock time, constraints, or provider-specific state. The terminal reviewer is an independent, fresh model session rather than a separately trained evaluator. The general memory and universal artifact-reviewer gaps remain partly addressed rather than fully solved.

## Proposed ablation campaign

Use a fixed Hermes commit, fixed model/provider, fixed config, fixed tool permissions, fixed temperature/reasoning settings, and a versioned task suite with hermetic workspaces. Record raw trajectories and outcome evidence, not only final text. Run a baseline with all selected features enabled, then one feature disabled per arm:

1. baseline;
2. `display.model_status_bar: false` (versus true);
3. memory retrieval/writes disabled while session search remains separately measured;
4. background memory/Skill review disabled;
5. verify-on-stop and `pre_verify` continuation disabled only in a safe test fixture;
6. context compression disabled or replaced by a fixed no-op at a safe context size;
7. delegation disabled for tasks that can run either single-agent or delegated.

For each arm, keep task order randomized and repeat enough times for confidence intervals. Report task success, independent verifier pass rate, safety/approval violations, regression/retention on prior tasks, artifact activation/adherence, token and wall-clock cost, tool-call count, failure class, and user-visible latency. Include transfer tasks and negative controls. Compare paired runs where possible and distinguish mechanism operation from end-to-end benefit. A run should not be promoted because it improves only a noisy judge or only the current task set; preserve trajectories and failed/negative results, as required by Chapter 6’s evaluation sections and Chapter 8 lines 245–270, 297–320.
