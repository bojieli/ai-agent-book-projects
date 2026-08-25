# Chapter 4 experiment ledger

This ledger separates execution coverage from the manuscript hypothesis and from external credential availability. `official_complete` is true only when every gate named by the manuscript has substantive real evidence. Mechanism tests and credential probes are retained, but never promoted as successful external executions.

| Experiment | Canonical run | Status | `official_complete` | Manifest SHA-256 |
| --- | --- | --- | --- | --- |
| 4-1 | `active-tool-discovery/validation/experiment_4_1/rerun_20260825` | passed | true | `e5a70588804b8bc1a5ba38c18fe7f4537e8284e62f745d8a6e03401833046dae` |
| 4-2 | `perception-tools/validation/experiment_4_2/real_mcp_dashscope_intl_20260730T070000Z` | blocked | false | `f93ee0ad9bd1121ed9e7c9d730bbaf85847d03e89c9024487cfdf9f62b8557ab` |
| 4-3 | `multimodal-agent/validation/runs/20260729T185433Z-4_2-e028c9db` | passed | true | `1a9cc7bfd48717e73a03ebbde7fd786c7da2811a15267715a3794c0f1220362e` |
| 4-4 | `execution-tools/validation/experiment_4_4/real_mcp_gui_20260802T093657Z` | blocked | false | `fde8976b91b149a61b7d468f4c825c1bdfdc9da3062cbfa66aaa1fd0f3d1966f` |
| 4-5 | `collaboration-tools/validation/experiment_4_5/real_mcp_human_20260803_v2` | blocked | false | `9fae8eadec1f9583ba03e21df5c8bc660cc8bec2ba328cf304bcaa0039bd97a3` |

> **Numbering.** Chapter 4 renumbered its experiments when the “too many tools” section moved ahead of the
> three tool categories: active tool discovery 4-5 → 4-1, perception 4-1 → 4-2, multimodal 4-2 → 4-3,
> execution 4-3 → 4-4, collaboration 4-4 → 4-5. Run directories under `validation/` were renamed to match,
> but the sealed manifests and receipts inside them were left byte-identical, so every hash below still
> verifies against the file it was computed from. Receipts written before the renumber therefore still
> quote the old `experiment_4_N` paths and the old experiment label; that is a record of the run as it
> happened and is deliberately not rewritten.

> **One recorded hash still does not verify, predating this renumber and left as-is rather than
> silently replaced:** the mailbox experiment that became 6-1 has a manifest that now hashes to
> `5b8befd0…` after its `experiment` field was relabelled 4-5 → 6-1 during the chapter-6 split,
> while both `chapter6/EXPERIMENT_LEDGER.md` and `chapter6/.../latest.json` still record the
> pre-relabel `3f689dfe…`. Its Unipile credential still returns 401, so a re-run cannot lift the
> block; only the hash can be corrected, and that is left to a deliberate, documented recomputation.
> The 4-1 hash that previously matched no file has been resolved by the re-run recorded below.

## Experiment 4-1 — active tool discovery

The canonical campaign `rerun_20260825` uses local Ollama `qwen3:4b`, 127
complete schemas listed by the real perception MCP server, a 50,597-token
schema catalog, a local `all-MiniLM-L6-v2` index, five-schema user-history
injection with a cumulative status bar, and the three exact manuscript tasks in
both arms. All twelve formal gates are true. Both groups selected every
required capability and completed 3/3 tasks, so the manuscript's expected
accuracy/completion improvement was **not observed**: both arms scored 100%.
Active discovery was faster in this run (783.442 versus 3,056.294 seconds,
3.90×) and exposed much less schema text (1,251 initial system tokens per
treatment task plus 8,424 dynamic tokens across the group, versus 50,829 system
tokens per control task).

This campaign replaces `qwen3_4b_exact_v2_20260730T130600Z` as the canonical
run. That earlier run was made with MCP SDK v1 (`server_version` 1.26.0) and its
recorded manifest hash `ce9d6eda…` matched no file left in the directory, so it
could no longer be verified. The runner had also stopped working entirely: the
v2 migration in #630 covered only the perception experiment, leaving this runner
on the v1 `serverInfo` attribute that v2 renamed to `server_info`. Both are fixed
here, and the re-run reproduces the earlier campaign's qualitative finding —
no accuracy uplift, a large speed and schema-exposure advantage. Note that the
run requires `OLLAMA_FLASH_ATTENTION=0`: with flash attention enabled, ollama
0.20.7 crashes its llama runner on Metal when the control arm's ~50K-token
prompt is prefilled. That is a runtime workaround only; no experiment parameter
was changed.

The successful aggregate must not be read as clean treatment behavior. On the
Apple task, Qwen first issued a vague discovery, malformed JSON, an irrelevant
Google search and a real but irrelevant `code_interpreter` call that wrote a
215-byte empty contributor chart; two premature finishes were rejected before
it discovered and executed `yfinance_quote` and `search_news`. The recovered
arXiv task retained two protocol parse errors and a redundant vague discovery.
Those trajectories remain in the canonical receipts.

Failed evidence is also preserved. The first exact campaign
`qwen3_4b_exact_20260730T061700Z` completed but had treatment at only 1/3 tasks
(manifest SHA-256
`e3b98be25fca51e3454e442f2e312ff84aad24c89c2d44a7c1e46628cdbebe09`).
The canonical v2 campaign's first terminal attempt hit real arXiv
429/503/disconnect failures; its final search succeeded only on turn 12, too
late to download. Its failed manifest SHA-256 is
`e18bc4465606087c195a2abafbd375048c2921233bae812ef3bc3f522eb9b86b`.
A bounded same-campaign resume archived that failed summary, manifest and task
receipt, reused the other five completed receipts, then made one fresh real
attempt. With the arXiv client page bounded to the requested three results,
the official endpoint succeeded on its first call and all three PDFs were
downloaded, signature-checked and hashed. No cached result or mock substituted
for either failed attempt.

## Experiment 4-2 — perception MCP

Manuscript gates: a real MCP catalog covering search, multimodal understanding, filesystem operations, public data, and authorized private data.

- Passed: real MCP `tools/list`; web and local-knowledge search; HTTPS download and webpage reading; PDF/DOCX/PPTX extraction; OCR; local Whisper transcription; video parsing; DashScope international `qwen-vl-max` image and video analysis with response IDs, token usage, and latency; confined file read/search/list/copy/move/delete; three escape probes; Open-Meteo, Yahoo Finance, exchange-rate, Wikipedia, and arXiv calls.
- Blocked: Google Calendar and Notion. No usable OAuth token or Notion integration credential exists in the environment. The failed calls and credential-free preflight are retained.
- Failed provenance retained: the first DashScope attempt used the mainland endpoint with an international-region key and received 401; the corrected run uses `dashscope-intl.aliyuncs.com`.

## Experiment 4-3 — multimodal processing

Manuscript gates: run the same nontrivial image/PDF and questions through native multimodal, extract-to-text, and tool-on-demand paradigms, retaining real vision calls, tool-use traces, exact-answer quality, latency, usage, and an external judge for free-form output. The canonical run is retained under `multimodal-agent/validation/runs/20260729T185433Z-4_2-e028c9db/`.

## Experiment 4-4 — execution MCP

Manuscript gates: verified file write/edit, terminal timeout and dangerous-command review, sandboxed Python, long-output persistence, Excel operations, external system mutations, and browser/desktop/mobile execution.

- Passed: deterministic Python compiler and Node `--check` linter; structured invalid-code responses; workspace escape rejection; timeout; OpenRouter GPT-4.1-mini dangerous-command rejection with raw usage/latency receipts; Docker Python sandbox (`--network none`, read-only root, memory/CPU/PID limits); immutable full long-output retention; XLSX formulas rendered through LibreOffice and PyMuPDF; real HTTPS webhook; real headless Chromium navigation and screenshot; PR #605 created through the GitHub execution tool and then safely reused through query-before-mutation idempotency; headful Chromium on Xvfb driven through OS keyboard events with a hashed framebuffer; and a KVM-backed AndroidWorld API-33 emulator that opened Wi-Fi Settings, verified focus, captured pixels, and returned home through ADB input.
- Blocked: no Google Calendar or real email-provider credentials. Android, Computer Use, and GitHub are no longer blockers. The canonical run passes 13/15 gates while retaining `official_complete: false` for the two absent external mutations.
- Failed provenance retained: `real_mcp_gui_20260802T093348Z` established the GitHub/desktop/mobile gates but failed the spreadsheet gate because LibreOffice and the Chapter 4 PyMuPDF dependency were missing. The corrected canonical run installs/declares both and passes the spreadsheet gate; it reuses the already-open PR instead of creating a duplicate.

## Experiment 4-5 — collaboration MCP

Manuscript gates: sync/async sub-agent lifecycle, messages, cancellation/status, two context-passing strategies, HITL requests with timeout/default behavior, and real multi-channel notification.

- Passed: the canonical v2 run retains six unique Kimi K3 response/usage/latency receipts; real minimal and LLM-generated handoffs; privacy filtering; synchronous and asynchronous completion/status; follow-up messages; cancellation; a conservative timeout; and a live repository-user approval delivered to the same pending MCP request in 1,423.272 seconds within its four-hour response window. The independent validator checks the human/MCP IDs and decision, 55 tool receipts, all 61 manifest hashes, and credential absence.
- Blocked only on delivery: no real SMTP/SendGrid, Telegram, or Slack configuration exists. Credential-free preflights fail explicitly, so `official_complete` remains false even though the human-decision gate is now closed.
- Failed provenance retained: `real_mcp_human_20260803_v1` used a 30-minute live window; the response arrived just after timeout and exposed that an expired request could still be mutated. The failed run preserves the timeout and late-response receipts. The production HITL primitive now rejects late or duplicate responses to terminal requests, with focused regression tests. The earlier `real_mcp_kimi_20260730T063500Z` run also preserves the original too-short async polling failure.
