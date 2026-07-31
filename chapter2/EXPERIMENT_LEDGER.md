# Chapter 2 experiment requirement/evidence ledger

`book/chapter2.md` is the acceptance source. “Passed” below means the frozen
experiment was actually exercised with the named real model/runtime and raw
artifacts were retained; it does not mean every historical directional result
was reproduced. A legacy proxy or mechanism-only demo never closes a row.

| Experiment | Exact manuscript gate | Status | Canonical evidence / qualification |
|---|---|---|---|
| 2-1 | Local ~0.6B model; raw token/thinking stream; parallel tools; ReAct; streaming; >100 tok/s observation and matched cache-hit/miss TTFT | Passed | `local_llm_serving/runs/exp2-1-qwen3-0.6b-20260730-v2/manifest.json` hashes the Ollama Qwen3 evidence; both tools, follow-up answer, 106.7 tok/s, and five matched TTFT pairs are retained. |
| 2-2 | Real attention heatmaps showing causal triangle, attention sink, reasoning/output regions, and position measurements | Passed | `attention_visualization/validation/latest.json` points to `runs/exp2-2-qwen3-0.6b-20260730-v3`: pinned Qwen revision, exact Beijing prompt, lossless first/middle/last-layer matrices, generated `<think>` + answer regions, and hash-addressed heatmaps. |
| 2-3 | Correct stable prefix versus dynamic system/profile, shuffled tools, sliding window, and flattened text; TTFT/cache/behavior effects | Passed | The six `kv-cache/result_*_20260718_kimi_k2_6.json` real Kimi K2.6 receipts retain per-iteration TTFT, cached/prompt tokens, calls, and completion behavior. Sliding-window failure and reduced caching from shuffled tools are observed; other magnitudes are reported rather than forced. |
| 2-4 | Same Tau-Bench tasks across tone, organization, and tool-description ablations; objective reward, efficiency, and real receipts | Passed, historical percentages not reproduced | `prompt-engineering/validation/latest.json` points to the completed 6 × 10 Kimi K3 campaign. The observed directions differ from the prose’s historical 30%/45% point estimates, and that is explicitly qualified. |
| 2-5 | Three attack channels × four progressive defenses; repeated trials; real filesystem/outbox/memory effects; attack success rates | Passed | `prompt-injection/validation/latest.json` hashes the complete 3 × 4 × 5 Kimi K3 campaign. All observed attack success rates were 0%, including baseline; the experiment is complete even though the model resisted every attack. |
| 2-6 | Pinned official Anthropic PPTX Skill + real paper, executed by any skills-capable runtime (runtime-agnostic author policy 2026-07-31: Claude Code or an equivalent such as Kimi Code); progressive disclosure; official scripts; 10–15 slides; three source visuals; reopen/thumbnail inspection | Passed | `agent-skills-ppt/runs/exp2-6-kimi-pptx-20260731-v1/manifest.json` passes all 15 gates: Kimi Code CLI (`kimi-code/k3`) invoked the pinned official Skill (Skill metadata → `SKILL.md` → `html2pptx.md` → official `html2pptx.js`/`thumbnail.py`), built a 13-slide deck from the hash-pinned *Attention Is All You Need* PDF with four PDF-cropped visuals byte-identical to embedded media, and LibreOffice reopens the deck; the credential-free raw stream is retained. Earlier Claude Code attempts (v2–v4) stayed blocked on Anthropic credentials and are kept as fail-closed evidence; the old python-pptx proxy remains non-acceptance evidence. |
| 2-7 | Same Xfinity trajectory with/without exact 3/3 status block; real small-model decisions and attention tensors | Passed | `attention_visualization/runs/exp2-7-qwen3-0.6b-20260730-v2/manifest.json`: three generations per arm, lossless tensors, region measurements, and heatmap. Control refused 2/3 and status refused 3/3; no response-conditioned gate was used. |
| 2-8 | Timestamp, tool counter, TODO, detailed error, system state, and combined on/off controls using a real Agent | Passed, historical percentages not reproduced | `system-hint/runs/exp2-8-kimi-k3-20260730-v1/manifest.json` hashes all 65 preregistered Kimi K3 runs. Current-suite effects, including null/negative findings, are retained separately from the prose’s historical 15-vs-21 and 60%-vs-95% claims. |
| 2-9 | Same founder-research task under six compression strategies with 128K limit; token, iteration, compression, overflow, citation, and adaptive-window behavior | Passed | `context-compression/results/kimi_k3_real_20260718.json` retains all six real Kimi K3 arms: no-compression overflow plus five completed strategies and their manuscript metrics. |

## Evidence policy

- A provider refusal before any model token is `blocked`, not a failed model
  outcome and not a reason to accept a local proxy.
- Completion gates validate design execution, model/runtime identity, raw
  receipts, artifact integrity, and credential scanning. Scientific hypotheses
  and historical percentages are reported as outcomes, never completion gates.
- Result directories from failed or partial attempts remain evidence and are
  not overwritten; the path in this ledger identifies the latest canonical run.
