# Chapter 4 experiment ledger

This ledger separates execution coverage from the manuscript hypothesis and from external credential availability. `official_complete` is true only when every gate named by the manuscript has substantive real evidence. Mechanism tests and credential probes are retained, but never promoted as successful external executions.

| Experiment | Canonical run | Status | `official_complete` | Manifest SHA-256 |
| --- | --- | --- | --- | --- |
| 4-1 | `perception-tools/validation/experiment_4_1/real_mcp_dashscope_intl_20260730T070000Z` | blocked | false | `1863389c1e0dff0c2b085744436a3e499e8699cd8164b1d43915b9d886018121` |
| 4-2 | `execution-tools/validation/experiment_4_2/real_mcp_20260730T070500Z` | blocked | false | `f1743d28e763d79d7a8690fc118c62ffaf124270e062eb3236542fca9636f5ab` |
| 4-3 | `collaboration-tools/validation/experiment_4_3/real_mcp_kimi_20260730T065500Z` | blocked | false | `b3a06d0a2db68128a0cd3d659157f85bc6e541f3b992dafefb1641c7688837b3` |
| 4-4 | `agent-with-event-trigger/validation/experiment_4_4/credential_probe_20260730T064500Z` | blocked | false | `5c9f15094dbab0151539818522ccf71d88ec2ba2e7f0654f373db365a9992dd9` |
| 4-6 | exact Qwen3-4B campaign in progress | pending | false | pending |

## Experiment 4-1 — perception MCP

Manuscript gates: a real MCP catalog covering search, multimodal understanding, filesystem operations, public data, and authorized private data.

- Passed: real MCP `tools/list`; web and local-knowledge search; HTTPS download and webpage reading; PDF/DOCX/PPTX extraction; OCR; local Whisper transcription; video parsing; DashScope international `qwen-vl-max` image and video analysis with response IDs, token usage, and latency; confined file read/search/list/copy/move/delete; three escape probes; Open-Meteo, Yahoo Finance, exchange-rate, Wikipedia, and arXiv calls.
- Blocked: Google Calendar and Notion. No usable OAuth token or Notion integration credential exists in the environment. The failed calls and credential-free preflight are retained.
- Failed provenance retained: the first DashScope attempt used the mainland endpoint with an international-region key and received 401; the corrected run uses `dashscope-intl.aliyuncs.com`.

## Experiment 4-2 — execution MCP

Manuscript gates: verified file write/edit, terminal timeout and dangerous-command review, sandboxed Python, long-output persistence, Excel operations, external system mutations, and browser/desktop/mobile execution.

- Passed: deterministic Python compiler and Node `--check` linter; structured invalid-code responses; workspace escape rejection; timeout; Kimi K3 dangerous-command rejection with raw usage/latency receipts; Docker Python sandbox (`--network none`, read-only root, memory/CPU/PID limits); immutable full long-output retention; XLSX formulas rendered through LibreOffice and PyMuPDF; real HTTPS webhook; real Chromium navigation and screenshot.
- Blocked: no Google Calendar/SMTP credentials or active Android/Computer Use session. The execution server has no environment GitHub token; an unrelated local CLI login was not silently repurposed for mutation.

## Experiment 4-3 — collaboration MCP

Manuscript gates: sync/async sub-agent lifecycle, messages, cancellation/status, two context-passing strategies, HITL requests with timeout/default behavior, and real multi-channel notification.

- Passed: real Kimi K3 minimal and LLM-generated handoffs, privacy filtering, raw model receipts, synchronous completion, asynchronous completion/status, follow-up messages, cancellation, a pending approval resolved through the admin MCP primitive, and a conservative timeout.
- Blocked: the validation operator is explicitly not claimed to be a human decision, and no real SMTP/Telegram/Slack credentials are configured. Placeholder `.env` values are forced empty by the campaign and cannot satisfy a gate.
- Failed provenance retained: the first live run polled the async task for only five seconds; the model completed after that window. The accepted blocked-evidence run uses a bounded twenty-second poll and passes the lifecycle gate.

## Experiment 4-4 — event-driven mailbox agent

Manuscript gates: three real inbound test-mailbox events processed FIFO: meeting/calendar conflict plus draft, complaint extraction plus high-priority notification, and marketing archive plus provider verification.

- The campaign fetched and hashed all eight official Unipile Email/Calendar schema documents and made credential-redacted live API probes.
- Blocked before mailbox mutation: the configured Unipile credential returns 401 with both documented `X-API-KEY` and diagnostic Bearer authentication. Therefore zero local/synthetic mail objects were substituted and no three-email success is claimed.

## Experiment 4-6 — active tool discovery

The exact campaign uses local Ollama `qwen3:4b`, the perception MCP server's 120+ complete schemas, an over-50K-token full-schema control, a local `all-MiniLM-L6-v2` embedding index, five-schema dynamic injection, and the three manuscript tasks. Final metrics and status will be recorded after the immutable campaign terminates.
