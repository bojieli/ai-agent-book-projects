# Experiment 7-12 AndroidWorld iteration report

- Run ID: `exp7-12-20260729T122904Z`
- Generated (UTC): `2026-07-29T13:17:47Z`
- Upstream commit: `0e95d641e244504c22087cc29b013f3b2428a261`
- Device: `sdk_gphone64_arm64`, API `35` (upstream tested reference: API `33`)
- Observation method: `varies_by_arm:a11y_forwarder_app_vs_uiautomator`
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
| middle / `H5` | Replace the API-35-incompatible gRPC accessibility feed with upstream's UIAutomator observation path. | At least one net paired Wi-Fi success with no regression and at most 1.5x latency/tokens. | Paired a11y-forwarder versus UIAutomator run with the same upstream T3A prompt and matched seeds. | tested in this run |
| deep / `H6` | Combine screenshots with the structured UI tree and compare stronger vision-capable models. | Improve complex-UI success enough to justify multimodal latency and token cost. | Factorial UI-tree/screenshot/model ablation on the full tagged slice. | not tested |

Selected hypothesis: `H5`
- Change: Select AndroidWorld's UIAUTOMATOR observation method in the companion runner without changing upstream source.
- Expected measurable result: At least one net paired Wi-Fi success with no regression and at most 1.5x latency/tokens.
- Guardrails: Same model, seed, task parameters, emulator, checkout, and step budget; require at least four completed pairs, no regression, and at most 1.5x mean latency and tokens; never treat a subset gain as full-suite success or deployment approval.

## 3. Controlled experiment

- Phase: `phase_2_middle` — middle-layer input-pipeline ablation prompted by phase-1 residual traces
- Independent variable: accessibility observation pipeline (gRPC forwarder versus UIAutomator)
- Controls: same checkout, model, task parameters, generated seed, step budget, and emulator; arm order alternates by pair.

| Arm | Episodes | Success | Reward | Steps | Latency (s) | LLM calls | Mean tokens | Input / output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 4/4 | 0.250 | 0.500 | 8.000 | 172.849 | 14.000 | 68310.500 | 251587 / 21655 |
| treatment | 4/4 | 1.000 | 1.000 | 5.750 | 136.235 | 11.000 | 170673.500 | 671404 / 11290 |

| Task / trial | Control | Treatment | Δ success | Control→treatment steps |
| --- | ---: | ---: | ---: | ---: |
| SystemWifiTurnOff / 1 | 0 | 1 | +1 | 10→6 |
| SystemWifiTurnOffVerify / 1 | 0 | 1 | +1 | 10→6 |
| SystemWifiTurnOn / 1 | 0 | 1 | +1 | 10→7 |
| SystemWifiTurnOnVerify / 1 | 1 | 1 | +0 | 2→4 |

## 4. Data-driven decision

- Outcome: **`restrict_candidate_due_to_cost`**
- Reason: Treatment improved paired success without regressions, but exceeded the latency/token guardrails (1.50x / 1.50x). Restrict it to targeted follow-up; do not promote it to the full suite yet.
- Treatment/control mean latency ratio: 0.788
- Treatment/control mean token ratio: 2.498
- Treatment/control mean LLM-call ratio: 0.786
- Cost guardrails passed: **false**
- Deployment approved: **false**

## 5. Rerun and next report

This run is a real controlled subset/smoke rerun, not the complete AndroidWorld benchmark. The next gate is a conditionally enabled candidate rerun over all 116 tasks with five seeds after provisioning the upstream API-33 app environment.

Observed residual failures:
- `control / SystemWifiTurnOff / trial 1`: evaluator reward / completion gate was not satisfied
- `control / SystemWifiTurnOffVerify / trial 1`: final evaluator state passed, but the agent never declared completion
- `control / SystemWifiTurnOn / trial 1`: evaluator reward / completion gate was not satisfied

### LLM analysis of this run

The following bounded interpretation was produced by the configured real LLM from the aggregate evidence (the JSON remains authoritative):

- Summary: Experiment 7-12 compared control (a11y-forwarder observation) and treatment (UIAutomator observation) arms in a paired setup with 4 Wi-Fi system Settings tasks. Treatment achieved 100% success (4/4) vs control's 25% (1/4), reduced mean latency (136.2s vs 172.8s) and LLM calls (11.0 vs 14.0), but had a mean token ratio (treatment/control) of 2.498, exceeding the 1.5x guardrail. Environment boundaries include API 35 AVD (vs upstream API 33 reference), restriction to Settings tasks, UIAutomator as a compatibility path (not reference config), and skipped device-time setting due to non-root AVD limitations.
- Cost/benefit interpretation: Treatment provides substantial benefit via improved success rate (net +3) and reduced latency/LLM calls, but incurs significantly higher token cost (2.498x control), violating token guardrails and limiting deployment despite success gains.
- Residual pattern: Treatment mean token ratio (2.498x) exceeds 1.5x guardrail
- Residual pattern: Control arm has low success rate (25%, 1/4 completed episodes)
- Next hypothesis `H6` (middle): Optimize UIAutomator observation pipeline to reduce token usage while maintaining treatment success rate Target: Mean token ratio (treatment/control) ≤1.5x and success rate ≥1.0 in paired Wi-Fi tasks Verification: Conduct paired run with optimized UIAutomator pipeline vs control, using same 4 Wi-Fi tasks, API 35 AVD environment, and guardrails; measure token ratio and success rate

## Environment boundaries

- The available AVD is API 35, while upstream is tested on Pixel 6 / API 33. Results are real but not reference-environment comparable.
- The full third-party AndroidWorld app bundle was not provisioned. This run is restricted to system Settings tasks.
- UIAutomator is an upstream AndroidWorld observation option selected by the companion runner; it preserves real UI actions/evaluators but is a compatibility path, not the upstream API-33 reference configuration.
- Per-task device-time setting was skipped because the non-root API-35 AVD rejects `adb shell date`; Wi-Fi evaluators do not depend on time.

The JSON beside this report is the authoritative evidence. It contains episode-level evaluator rewards, actions, timing, token counts, configuration, and explicit completion gates; credentials and raw prompts are not stored.
