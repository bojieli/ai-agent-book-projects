# Experiment 7-12 AndroidWorld iteration report

- Run ID: `exp7-12-20260729T131911Z`
- Generated (UTC): `2026-07-29T14:12:27Z`
- Upstream commit: `0e95d641e244504c22087cc29b013f3b2428a261`
- Device: `sdk_gphone64_arm64`, API `35` (upstream tested reference: API `33`)
- Observation method: `varies_by_arm:uiautomator_vs_uiautomator_compact`
- Provider/model: `ark` / `doubao-seed-1-6-250615`
- Scope: 4 task(s), 1 trial(s), mode `paired`
- Full 116-task × 5-seed suite completed: **false**

The bundled ~88% baseline is historical input evidence. The manuscript's 88%→94% numbers are explicitly hypothetical and are not used as rerun results here.

## 1. Diagnose

- The historical run evaluated 116 tasks once each and reports approximately 88% overall success.
- Wi-Fi is a concentrated failure cluster: three of the four SystemWifiTurn* rows failed in the bundled per-task table.
- The capability matrix links the cluster to weak complex_ui_understanding, information_retrieval, and requires_setup behavior.
- The failed traces show navigation/state-verification loops; increasing the step cap alone would treat a symptom rather than the cause.

## 2. Hypothesis

The diagnosis produced explicit surface, middle, and deep hypotheses. Only one variable is changed in this run; the other hypotheses remain untested.

| Layer / ID | Proposed change | Target | Verification | Status |
| --- | --- | --- | --- | --- |
| surface / `H1` | Add Wi-Fi Settings navigation and final-state verification guidance. | At least one net paired success across the four Wi-Fi tasks, with no regression. | Paired upstream-prompt versus task-guideline ablation with matched seeds. | tested in source phase 1 |
| surface / `H2` | Add application-specific recognition rules for the non-standard Tasks UI. | Improve at least two of the six historical Tasks failures with no regression. | Paired Tasks-only prompt/tool-description ablation after app provisioning. | not tested |
| middle / `H3` | Repair and validate the multimodal input path for transcription tasks. | Raise transcription success above the historical 0% while bounding added tokens and latency. | Paired screenshot-disabled versus screenshot-enabled transcription run. | not tested |
| middle / `H4` | Conditionally enable deeper thinking for counting tasks. | Improve math/counting success without applying the cost to unrelated tasks. | Paired tag-routed thinking-mode ablation with latency and token guardrails. | not tested |
| middle / `H5` | Replace the API-35-incompatible gRPC accessibility feed with upstream's UIAutomator observation path. | At least one net paired Wi-Fi success with no regression and at most 1.5x latency/tokens. | Paired a11y-forwarder versus UIAutomator run with the same upstream T3A prompt and matched seeds. | tested in source phase 2 |
| middle / `H5C` | Filter non-semantic UIAutomator container nodes after H5 exposed excessive prompt-token cost. | Preserve H5 paired success with no regression while using at most 0.75x raw-UIAutomator tokens and 1.5x latency. | Paired raw-UIAutomator versus compact-UIAutomator run with matched tasks, seeds, prompt, and evaluator. | tested in this run |
| deep / `H6` | Combine screenshots with the structured UI tree and compare stronger vision-capable models. | Improve complex-UI success enough to justify multimodal latency and token cost. | Factorial UI-tree/screenshot/model ablation on the full tagged slice. | not tested |

Selected hypothesis: `H5C`
- Change: Use the real upstream UIAutomator hierarchy but retain only visible text, descriptions, and actionable/scrollable elements.
- Expected measurable result: Preserve H5 paired success with no regression while using at most 0.75x raw-UIAutomator tokens and 1.5x latency.
- Guardrails: Same model, seed, task parameters, emulator, checkout, and step budget; require at least four completed pairs, every compact-UIAutomator treatment pair successful, no paired regression, at most 1.5x mean latency, and at most 0.75x raw-UIAutomator mean tokens. Passing a paired gate permits only a full-suite candidate rerun; it is not deployment approval, and a subset must never be reported as full-suite success.

## 3. Controlled experiment

- Phase: `phase_2_cost_refinement` — middle-layer input-pipeline cost refinement after the H5 success/cost result
- Independent variable: raw versus semantic-filtered UIAutomator element list
- Controls: same checkout, model, task parameters, generated seed, step budget, and emulator; arm order alternates by pair.

| Arm | Episodes | Success | Reward | Steps | Latency (s) | LLM calls | Mean tokens | Input / output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 4/4 | 1.000 | 1.000 | 4.750 | 101.198 | 8.500 | 139439.500 | 549928 / 7830 |
| treatment | 4/4 | 1.000 | 1.000 | 4.750 | 99.184 | 8.500 | 70557.500 | 274067 / 8163 |

| Task / trial | Control | Treatment | Δ success | Control→treatment steps |
| --- | ---: | ---: | ---: | ---: |
| SystemWifiTurnOff / 1 | 1 | 1 | +0 | 5→5 |
| SystemWifiTurnOffVerify / 1 | 1 | 1 | +0 | 5→5 |
| SystemWifiTurnOn / 1 | 1 | 1 | +0 | 5→5 |
| SystemWifiTurnOnVerify / 1 | 1 | 1 | +0 | 4→4 |

## 4. Data-driven decision

- Outcome: **`promote_efficient_candidate_to_full_suite_rerun`**
- Reason: Treatment preserved paired success with no regression and passed the latency/token efficiency guardrails. This is a candidate decision only.
- Treatment/control mean latency ratio: 0.980
- Treatment/control mean token ratio: 0.506
- Treatment/control mean LLM-call ratio: 1.000
- Cost guardrails passed: **true**
- Deployment approved: **false**

## 5. Rerun and next report

This run is a real controlled subset/smoke rerun, not the complete AndroidWorld benchmark. The next gate is a conditionally enabled candidate rerun over all 116 tasks with five seeds after provisioning the upstream API-33 app environment.

### LLM analysis of this run

The following bounded interpretation was produced by the configured real LLM from the aggregate evidence (the JSON remains authoritative):

- Summary: A paired experiment comparing raw UIAutomator (control) and compact UIAutomator (treatment) on 4 system Settings tasks (SystemWifiTurnOff, SystemWifiTurnOffVerify, SystemWifiTurnOn, SystemWifiTurnOnVerify) in an API 35 AVD environment. Both arms completed 4 episodes with 100% success rate, identical mean steps (4.75) and LLM calls (8.5). Treatment showed lower mean total tokens (50.6% of control) and slightly lower mean latency (98.0% of control). The decision was to promote the treatment as a full-suite candidate rerun, as it preserved success, passed latency/token guardrails, but remains a subset with environment limitations.
- Cost/benefit interpretation: The treatment provides significant token efficiency (mean token ratio 0.506) with preserved success and marginal latency improvement (mean latency ratio 0.980) in the tested 4-task subset. However, interpretation is bounded by the API/app environment: results are from an API 35 AVD (not upstream API 33 reference), restricted to system Settings tasks (no full third-party app bundle), and use UIAutomator as a compatibility path (not upstream reference configuration), limiting generalizability beyond the tested scope.
- Next hypothesis `H5C-full` (middle): Evaluate compact UIAutomator (semantic-filtered elements) across the full AndroidWorld task suite to verify token efficiency and success preservation beyond the 4-task Settings subset. Target: Full task suite (all 116 tasks) with upstream reference environment (Pixel 6 / API 33) and provisioned full third-party AndroidWorld app bundle. Verification: Paired run comparing compact UIAutomator (treatment) vs raw UIAutomator (control) across all tasks, ensuring guardrails (mean token ratio ≤0.75, mean latency ratio ≤1.5, success non-inferiority) hold in the reference environment.

## Environment boundaries

- The available AVD is API 35, while upstream is tested on Pixel 6 / API 33. Results are real but not reference-environment comparable.
- The full third-party AndroidWorld app bundle was not provisioned. This run is restricted to system Settings tasks.
- UIAutomator is an upstream AndroidWorld observation option selected by the companion runner; it preserves real UI actions/evaluators but is a compatibility path, not the upstream API-33 reference configuration.
- Compact UIAutomator removes only non-semantic container nodes; observations, coordinates, Android actions, and AndroidWorld evaluators remain real.
- Per-task device-time setting was skipped because the non-root API-35 AVD rejects `adb shell date`; Wi-Fi evaluators do not depend on time.

The JSON beside this report is the authoritative evidence. It contains episode-level evaluator rewards, actions, timing, token counts, configuration, and explicit completion gates; credentials and raw prompts are not stored.
