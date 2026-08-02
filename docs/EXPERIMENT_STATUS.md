# Experiment status and evidence

This operational record is kept separate from the book README. It tracks the
cross-chapter experiments that require special local implementations, evidence
gates, external services, or hardware. Cloning a pinned source repository,
installing its dependencies, or passing a smoke test does not establish that an
experiment is complete.

Statuses in this file describe evidence retained in the repository. A local
checkpoint or run directory that is still untracked is useful work-in-progress,
but it does not close the clean-clone audit until a reviewable evidence package
is committed.

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
| 4-1 | External-service acceptance | **Incomplete.** The real MCP catalog covers the public-data, multimodal, and filesystem gates, but Google Calendar and Notion remain blocked by missing authorized credentials. See the [Chapter 4 ledger](../chapter4/EXPERIMENT_LEDGER.md). |
| 4-2 | External-service acceptance | **Incomplete only at Calendar/email authorization.** The canonical 20-call MCP campaign passes 13/15 gates: core safety, sandboxing, spreadsheet rendering, webhook, headless browser, real GitHub PR mutation, Xvfb Computer Use, and KVM-backed Android execution. Calendar and real email-provider mutations remain unsatisfied, so `official_complete` stays false. See the [canonical manifest](../chapter4/execution-tools/validation/experiment_4_2/real_mcp_gui_20260802T093657Z/manifest.json). |
| 4-3 | Human/external-channel acceptance | **Incomplete.** The Agent lifecycle and approval mechanism ran, but no real human decision or SMTP/Telegram/Slack notification is retained. See the [Chapter 4 ledger](../chapter4/EXPERIMENT_LEDGER.md). |
| 4-4 | External mailbox experiment | **Incomplete.** The Unipile credential probe returned 401 before mailbox mutation, so the three required real inbound-mail cases have not run. See the [Chapter 4 ledger](../chapter4/EXPERIMENT_LEDGER.md). |
| 5-12 | Local experiment | **Complete; strict joint-advantage hypothesis not observed.** Both Agent-creation arms passed their acceptance gates. The [formal comparison](../chapter5/agent-creator/runs/exp5-12-kimi-k3-20260730-v1/comparison.json) found equal deterministic quality and greater template-arm efficiency, but not strictly higher quality and efficiency together. |
| 6-1 | External benchmark execution | **Incomplete.** The pinned tau2-bench source and entrypoint are mapped, but no retained tau2 run or failure analysis exists. See the [Chapter 6 ledger](../chapter6/EXPERIMENT_LEDGER.md). |
| 6-2 | Reader exercise | **Incomplete.** The benchmark sources and entrypoints are mapped, but the required 18-task human trajectory set and official verification have not been retained. See the [Chapter 6 ledger](../chapter6/EXPERIMENT_LEDGER.md). |
| 6-3 | Local implementation | **Complete.** The four-grade memory rubric has 60 cases and 180/180 structured judgments with full scope in the [saved evidence](../chapter6/user-memory-system-evaluation/results/full_6_3_structured_rubric_evidence.json). |
| 6-4 | Local experiment | **Complete.** JSON Cards, RAG, and hybrid systems produced 180/180 real trajectories across 60 cases, with complete cost and failure analysis in the [saved campaign](../chapter6/user-memory-system-evaluation/results/full_6_4_60_cases_costed.json). |
| 6-7 | Local experiment | **Complete.** The neutral Coding Harness campaign retained 18/18 cells (two models × three tasks × three trials), zero API errors, full trajectories, summaries, and verified artifact hashes in the [manifest](../chapter6/model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json). |
| 6-9 | Long-running provider benchmark | **Incomplete.** The runner and analyzer exist, but retained evidence contains only 29 smoke/readiness observations: no standard N=100 cells, rate ramp, Agent-cost phase, or 168-hour availability campaign. See the [Chapter 6 ledger](../chapter6/EXPERIMENT_LEDGER.md). |
| 6-10 | Local experiment | **Complete.** The full 4 × 3 × 2 × 60 matrix retained 1,440/1,440 real trajectories with zero errors or unpriced usage, complete retrieval/task metrics and factorial analysis, and an independently passing verifier. See the [canonical matrix](../chapter6/user-memory-system-evaluation/results/full_6_9_60_case_matrix.json). |
| 6-11 | Emulator evaluation | **Incomplete.** Four paired Wi-Fi tasks ran, but the 116-task × five-seed candidate campaign and reference app image are absent. See the [Chapter 6 ledger](../chapter6/EXPERIMENT_LEDGER.md). |
| 6-12 | Simulation evaluation | **Incomplete.** The protocol and preflight exist, but the OpenVLA checkpoint, RoboTwin2 environment, and required CUDA stack are unavailable on the audited host. See the [preflight evidence](../chapter6/openvla-robotwin2-eval/results/preflight-20260729.json). |
| 7-6 | Local speech training experiment | **Incomplete.** Orpheus and Sesame training/inference entrypoints exist, but no trained adapters, generated comparison audio, or acceptance report is retained. See the [Chapter 7 ledger](../chapter7/EXPERIMENT_LEDGER.md). |
| 7-7 | Local multilingual training experiment | **Incomplete.** The SFT implementation exists, but the repository retains no checkpoint or before/after multilingual benchmark. See the [Chapter 7 ledger](../chapter7/EXPERIMENT_LEDGER.md). |
| 7-8 | Local training experiment | **Incomplete; GPU training and evaluation completed, teacher generation partial.** A real CUDA run produced a retained SmolLM2-135M-Instruct student checkpoint and comparison report in [`validation/exp7-8-kimi3-smollm2-20260730/`](../chapter8/prompt-distillation/validation/exp7-8-kimi3-smollm2-20260730/). Held-out results: teacher 65%, baseline 0%, trained 95%; ~180× latency speedup; ~61% input-token reduction. The remaining blocker is incomplete teacher test receipts (52/80 retained), so `real_teacher_receipts` is not yet satisfied. |
| 7-9 | Local training experiment | **Implementation complete; GPU execution finished but acceptance gates not closed.** Real CUDA training produced a Qwen2.5-1.5B-Instruct LoRA checkpoint in [`checkpoints/exp7-9-qwen25-1.5b-kimi-k3-20260801-v1/`](../chapter7/cot-distillation/checkpoints/exp7-9-qwen25-1.5b-kimi-k3-20260801-v1/) and a paired evaluation in [`validation/experiment_7_9_gpu_20260801_v1.json`](../chapter7/cot-distillation/validation/experiment_7_9_gpu_20260801_v1.json). Results: baseline 1/24, student 2/24, teacher 23/24; paired improvement is not significant (p=1.0). The experiment remains incomplete because one teacher trajectory timed out and the paired uplift did not reach significance. |
| 7-11–7-16 | External training reproductions | **Incomplete.** The GeneralPoints, V-IRL, SimpleVLA-RL, RLVP, ReTool, and AWorld sources/entrypoints are mapped to varying degrees, but none has a retained full training-and-evaluation campaign satisfying its manuscript gate. See the [Chapter 7 ledger](../chapter7/EXPERIMENT_LEDGER.md). |
| 8-6 | External-repository self-evolution experiment | **Complete for the autonomous, review-driven self-update loop; downstream benefit not evaluated.** Pinned Hermes received all ten English chapters and its own source without any supplied candidate gap. It independently chose to add evidence-backed learning signals to persisted trajectories. Three fresh terminal-review rejections were fed back to the original Hermes proposer session; it corrected production-format parsing, persistence-path coverage, and counting-consistency defects until a fourth fresh reviewer returned `VERDICT: ACCEPT`. The accepted patch passes 6 new plus 38 existing focused tests and clean-clone application, but remains unmerged; the proposed downstream ablation campaign was not run. See the [credential-free manifest](../chapter8/hermes-self-evolution/validation/exp8-6-hermes-gpt56luna-autonomous-20260802-v2/manifest.json). |
| 8-7 | Longitudinal continual-evolution evaluation | **Complete.** The static, append-only, and evolving arms ran 3 seeds × 14 ordered tasks (126 real model calls). The retained evidence separates transfer, rule replacement, retention, obsolete-rule citation, and paired statistics; only the evolving arm replaces the obsolete 20 kg rule and retains the current 23 kg rule. See the [canonical evidence](../chapter8/self-evolution-eval/validation/latest.json). |
| 9-2 | Local WebRTC speech experiment | **Complete.** Direct and ReAct arms each pass 20/20 gates over browser-microphone RTP, local Whisper, a real external LLM, TTS, and downlink RTP. PSTN/E.164 is outside the manuscript's local call-user gate. See the [manifest](../chapter9/phone-agent/validation/runs/exp9-2-webrtc-audio-20260731-v1/manifest.json). |
| 9-4 | Local omni-speech experiment | **Complete; the two paths tie overall with complementary failures.** Pinned MiniCPM-o 4.5 ran locally on one RTX PRO 6000. Native end-to-end and same-model self-cascade each scored 3/4: self-cascade fixed one semantic perception error, while end-to-end preserved speaking-rate evidence erased by the transcript. The [canonical evidence](../chapter9/end-to-end-speech/validation/runs/exp9-4-minicpmo45-20260801-v1/evidence.json) also retains a real 24kHz speech output and passes all acceptance checks. |
| 9-5 | Local controllable-TTS experiment | **Complete; the full subjective ordering was not reproduced.** Fish Audio S1 produced the 24-reference library and A/B/C media, and three position-balanced Voxtral listening passes rated the multi-reference arm highest. C > B > A did not reproduce because A outscored B. See the [acceptance evidence](../chapter9/controllable-tts/validation/acceptance.json). |
| 9-6 | External reference implementation | **Incomplete.** The Anthropic native `computer`/`bash`/editor Demo remains mapped and pinned but has not run. Readers without Anthropic access can exercise the same visual browser loop through the separate open-model 9-7 arm; that result does not close this model-specific native-tool arm. |
| 9-7 | Provider-portable Computer Use | **Complete on the open-model arm.** OpenRouter returned `qwen/qwen3-vl-32b-instruct` for 16/16 real calls; the Agent recovered from a Google CAPTCHA through weather.com and completed in 16 one-action steps. The [canonical evidence](../chapter9/computer-use-open-model/validation/latest.json) retains 15 screenshots, raw responses, the action trajectory, deterministic answer grounding, hashes, and a clean credential scan. |
| 9-8 | External hardware track | **Incomplete.** The XLeRobot source and non-actuating preflight are pinned, but no authorized physical teleoperation or book task has run. See the [experiment record](../chapter9/xlerobot-teleoperation/README.md). |
| 9-9 | External API and hardware track | **Incomplete.** The exact Gemini Robotics-ER request failed authentication and no robot navigation occurred. A successful planning response, authorized navigation run, and the remaining evidence gates are still required. See the [experiment record](../chapter9/gemini-xlerobot-navigation/README.md). |
| 9-10 | External Sim2Real track | **Incomplete.** No local ManiSkill environment, RGB-only PPO checkpoint, >90% simulation evaluation, or real deployment exists. Stages 1–2 require real-scene hardware inputs, stages 3–4 require a suitable GPU environment, and stage 5 requires authorized SO-100 actuation. See the [experiment record](../chapter9/rgb-sim2real-grasping/README.md). |
| 10-3 | Local multi-agent comparison | **Complete.** The four-role Manager and single-Agent arms translated all 26 units of the retained illustrated/code-heavy technical-book sample, with 12/12 acceptance gates and complete quality, context, token, latency, and resource comparisons. See the [canonical index](../chapter10/book-translation/validation/latest.json). |
| 10-4 | External concurrent-agent reproduction | **Incomplete.** The pinned TalkAct checkout is absent and the duplex/strawman benchmark has not run. See the [Chapter 10 record](../chapter10/README.md). |
| 10-5 | Local WebRTC orchestration experiment | **Complete.** A real LLM autonomously selected the Phone Agent; Playwright, bidirectional RTP, local TTS/Whisper, validation/re-asking, concurrent ask/fill, and one localhost submission pass all 9 gates. PSTN/E.164 is not required by the manuscript. See the [manifest](../chapter10/autonomous-phone-registration/validation/runs/exp10-5-webrtc-raw-20260731-v4/manifest.json). |
| 10-7 | External generative-agents reproduction | **Incomplete.** The pinned Stanford Generative Agents checkout is absent; the required 25-Agent two-day baseline, memory/reflection logs, custom scenario, and ablation have not run. See the [Chapter 10 record](../chapter10/README.md). |
| 10-8 | Local voice multi-agent experiment | **Incomplete in repository-retained evidence.** The retained v2 run passes end-to-end audio, isolation, rule winner, and three-cycle gates, but fails the strategy gate after a Villager exiles the uncontested Seer. See the [experiment record](../chapter10/voice-werewolf/README.md). |

## Detailed ledgers

The chapter ledgers are the canonical detailed records for acceptance scope,
saved evidence, and audit findings:

- [Chapter 5 experiment ledger](../chapter5/EXPERIMENT_LEDGER.md)
- [Chapter 6 experiment coverage ledger](../chapter6/EXPERIMENT_LEDGER.md)
- [Chapter 7 experiment coverage ledger](../chapter7/EXPERIMENT_LEDGER.md)

Update this summary whenever one of the tracked completion gates changes. Git
history provides the status change log.
