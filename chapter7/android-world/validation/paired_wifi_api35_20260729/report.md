# Experiment 7-12 AndroidWorld iteration report

- Run ID: `exp7-12-20260729T114648Z`
- Generated (UTC): `2026-07-29T12:13:15Z`
- Upstream commit: `0e95d641e244504c22087cc29b013f3b2428a261`
- Device: `sdk_gphone64_arm64`, API `35` (upstream tested reference: API `33`)
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

- ID: `H1`
- Change: Use upstream T3A.set_task_guidelines to add only Wi-Fi Settings navigation and final-state verification guidance.
- Expected measurable result: At least one net paired Wi-Fi success, with no paired regression; record reward, steps, latency, calls, and tokens.
- Guardrails: Same model, seed, task parameters, emulator, checkout, and step budget; do not treat a subset gain as full-suite success.

## 3. Controlled experiment

Control and treatment use the same checkout, model, task parameters, step budget, and emulator. Only the task-specific T3A guidelines differ. Arm order alternates by pair.

| Arm | Episodes | Success | Reward | Steps | Latency (s) | LLM calls | Input / output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| control | 4/4 | 0.250 | 0.500 | 8.500 | 233.465 | 15.750 | 411525 / 31094 |
| treatment | 4/4 | 0.250 | 0.500 | 8.000 | 156.985 | 12.500 | 190519 / 19520 |

| Task / trial | Control | Treatment | Δ success | Control→treatment steps |
| --- | ---: | ---: | ---: | ---: |
| SystemWifiTurnOff / 1 | 0 | 0 | +0 | 10→10 |
| SystemWifiTurnOffVerify / 1 | 0 | 0 | +0 | 10→10 |
| SystemWifiTurnOn / 1 | 0 | 0 | +0 | 10→10 |
| SystemWifiTurnOnVerify / 1 | 1 | 1 | +0 | 4→2 |

## 4. Data-driven decision

- Outcome: **`inconclusive_no_success_gain`**
- Reason: Treatment produced no paired success gain; keep the upstream control prompt.
- Treatment/control mean latency ratio: 0.672

## 5. Rerun and next report

This run is a real controlled subset/smoke rerun, not the complete AndroidWorld benchmark. The next gate is a conditionally enabled candidate rerun over all 116 tasks with five seeds after provisioning the upstream API-33 app environment.

Observed residual failures:
- `control / SystemWifiTurnOff / trial 1`: evaluator reward / completion gate was not satisfied
- `treatment / SystemWifiTurnOff / trial 1`: evaluator reward / completion gate was not satisfied
- `treatment / SystemWifiTurnOffVerify / trial 1`: evaluator reward / completion gate was not satisfied
- `control / SystemWifiTurnOffVerify / trial 1`: evaluator reward / completion gate was not satisfied
- `control / SystemWifiTurnOn / trial 1`: evaluator reward / completion gate was not satisfied
- `treatment / SystemWifiTurnOn / trial 1`: evaluator reward / completion gate was not satisfied

## Environment boundaries

- The available AVD is API 35, while upstream is tested on Pixel 6 / API 33. Results are real but not reference-environment comparable.
- The full third-party AndroidWorld app bundle was not provisioned. This run is restricted to system Settings tasks.
- Per-task device-time setting was skipped because the non-root API-35 AVD rejects `adb shell date`; Wi-Fi evaluators do not depend on time.

The JSON beside this report is the authoritative evidence. It contains episode-level evaluator rewards, actions, timing, token counts, configuration, and explicit completion gates; credentials and raw prompts are not stored.
