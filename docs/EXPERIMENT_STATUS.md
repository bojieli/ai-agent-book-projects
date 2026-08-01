# Experiment status and evidence

This operational record is kept separate from the book README. It tracks the
cross-chapter experiments that require special local implementations, evidence
gates, external services, or hardware. Cloning a pinned source repository,
installing its dependencies, or passing a smoke test does not establish that an
experiment is complete.

Status meanings:

- **Complete**: the manuscript's execution and evidence gates have substantive
  saved evidence. A complete experiment may still produce a negative result.
- **Incomplete**: some implementation, execution, or evidence gates remain
  unsatisfied.
- **Reader exercise**: completion requires a reader-operated campaign and its
  retained evidence rather than a repository checkout alone.

## Tracked experiments

| Experiment | Track | Current status and evidence |
| --- | --- | --- |
| 5-12 | Local experiment | **Complete; strict joint-advantage hypothesis not observed.** Both Agent-creation arms passed their acceptance gates. The [formal comparison](../chapter5/agent-creator/runs/exp5-12-kimi-k3-20260730-v1/comparison.json) found equal deterministic quality and greater template-arm efficiency, but not strictly higher quality and efficiency together. |
| 6-2 | Reader exercise | **Incomplete.** The benchmark sources and entrypoints are mapped, but the required 18-task human trajectory set and official verification have not been retained. See the [Chapter 6 ledger](../chapter6/EXPERIMENT_LEDGER.md). |
| 6-3 | Local implementation | **Complete.** The four-grade memory rubric has 60 cases and 180/180 structured judgments with full scope in the [saved evidence](../chapter6/user-memory-system-evaluation/results/full_6_3_structured_rubric_evidence.json). |
| 6-4 | Local experiment | **Complete.** JSON Cards, RAG, and hybrid systems produced 180/180 real trajectories across 60 cases, with complete cost and failure analysis in the [saved campaign](../chapter6/user-memory-system-evaluation/results/full_6_4_60_cases_costed.json). |
| 6-7 | Local experiment | **Complete.** The neutral Coding Harness campaign retained 18/18 cells (two models × three tasks × three trials), zero API errors, full trajectories, summaries, and verified artifact hashes in the [manifest](../chapter6/model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json). |
| 6-10 | Local experiment | **Incomplete.** The runner and readiness gates exist, but only 5/9 backends are ready and the required 4 × 3 × 2 × 60 matrix has not run. See the [results manifest](../chapter6/user-memory-system-evaluation/results/manifest.json). |
| 6-12 | Simulation evaluation | **Incomplete.** The protocol and preflight exist, but the OpenVLA checkpoint, RoboTwin2 environment, and required CUDA stack are unavailable on the audited host. See the [preflight evidence](../chapter6/openvla-robotwin2-eval/results/preflight-20260729.json). |
| 7-8 | Local training experiment | **Incomplete.** Teacher generation, student training, and the paired quality/latency/cost comparison still need a retained student checkpoint and completed report. See the [Chapter 7 ledger](../chapter7/EXPERIMENT_LEDGER.md). |
| 7-9 | Local training experiment | **Implementation complete; execution incomplete.** The implementation retains 23/24 verified teacher trajectories and passes the training-stack preflight, but no CUDA device was available for student training and evaluation. See the [preflight evidence](../chapter7/cot-distillation/validation/student_sft_preflight_20260730.json). |
| 9-6 | External reference implementation | **Incomplete.** The Anthropic native `computer`/`bash`/editor Demo remains mapped and pinned but has not run. Readers without Anthropic access can exercise the same visual browser loop through the separate open-model 9-7 arm; that result does not close this model-specific native-tool arm. |
| 9-7 | Provider-portable Computer Use | **Complete on the open-model arm.** OpenRouter returned `qwen/qwen3-vl-32b-instruct` for 16/16 real calls; the Agent recovered from a Google CAPTCHA through weather.com and completed in 16 one-action steps. The [canonical evidence](../chapter9/computer-use-open-model/validation/latest.json) retains 15 screenshots, raw responses, the action trajectory, deterministic answer grounding, hashes, and a clean credential scan. |
| 9-8 | External hardware track | **Incomplete.** The XLeRobot source and non-actuating preflight are pinned, but no authorized physical teleoperation or book task has run. See the [experiment record](../chapter9/xlerobot-teleoperation/README.md). |
| 9-9 | External API and hardware track | **Incomplete.** The exact Gemini Robotics-ER request failed authentication and no robot navigation occurred. A successful planning response, authorized navigation run, and the remaining evidence gates are still required. See the [experiment record](../chapter9/gemini-xlerobot-navigation/README.md). |
| 9-10 | External Sim2Real track | **Incomplete.** No local ManiSkill environment, RGB-only PPO checkpoint, >90% simulation evaluation, or real deployment exists. Stages 1–2 require real-scene hardware inputs, stages 3–4 require a suitable GPU environment, and stage 5 requires authorized SO-100 actuation. See the [experiment record](../chapter9/rgb-sim2real-grasping/README.md). |

## Detailed ledgers

The chapter ledgers are the canonical detailed records for acceptance scope,
saved evidence, and audit findings:

- [Chapter 5 experiment ledger](../chapter5/EXPERIMENT_LEDGER.md)
- [Chapter 6 experiment coverage ledger](../chapter6/EXPERIMENT_LEDGER.md)
- [Chapter 7 experiment coverage ledger](../chapter7/EXPERIMENT_LEDGER.md)

Update this summary whenever one of the tracked completion gates changes. Git
history provides the status change log.
