# Chapter 8 · Model Post-Training

> Four parts—pre-training, Mid-training, SFT, and RL: long-context curricula and data construction, SFT protocol shaping, RL environments and rewards, and sample efficiency from single-turn to multi-turn Agents.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter8.md)

## How to Read the Experiments

The prose uses short mechanism skeletons to explain control flow; the experiment directory contains complete SDK adapters, logs, tests, and acceptance evidence. You do not need to read every file line by line.

- **Starter:** Start with the goal, minimum command, and acceptance conditions; begin with [cot-distillation](cot-distillation/);
- **Builder:** Follow the entry point, core loop, state/message schema, tools, and verifier.
- **Maintainer:** Then read tests, evidence manifests, failure handling, rollback paths, and provider adapters.

On a first pass, skip credential loading, presentation code, and provider-compatibility layers; return when reproducing a number.

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 8-1, 8-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | Runs Q-learning and an LLM Agent in the same treasure-hunt environment to learn from experience. |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | The [retained campaign](../chapter8/prompt-distillation/validation/exp8-8-kimi3-smollm2-20260730/) contains 160/160 training and 80/80 held-out Kimi K3 teacher receipts, a real CUDA-trained SmolLM2-135M-Instruct LoRA checkpoint, and passes all 8 gates; held-out accuracy is 100% for the teacher, 0% for baseline, and 95% for the trained student. |
| 8-3, 8-4 | [MiniMind-pretrain](MiniMind-pretrain/) | ✅ | Experiment 8-3's [canonical report](MiniMind-pretrain/validation/runs/exp8-3-training-report-20260731-v1/report.md) retains 49 historical LLM outputs and eight blind judgments. Experiment 8-4's [canonical report](MiniMind-pretrain/validation/runs/exp8-4-training-report-20260731-v1/report.md) retains all 64 historical outputs across eight VLM configurations and images plus eight real image-aware blind judgments. Original VLM SFT ranked highest at 1.9062 and matched QK-Norm+Muon comparisons did not improve, an explicit negative result. Historical checkpoints are not distributed or required for acceptance. |
| 8-5 | [continued-pretraining](continued-pretraining/) | ✅ | [Canonical training report](continued-pretraining/validation/runs/exp8-5-training-report-20260731-v1/report.md) binds the RTX 4090 three-stage output, 15 generations, five blind ARK judgments, source hashes, and current reproduction revisions; final Korean gained 1.7777, English fell 0.8333, and kimchi factual errors remain explicit. Checkpoints are not distributed or required for acceptance. |
| 8-6 | [sesame](sesame/) | ✅ | Sesame CSM tag SFT completed in the [bounded GPU campaign](speech-sft-experiment/): 60 LoRA updates, held-out loss, matched tag/no-tag audio, detector-proxy evaluation, hashes, and retained failures. |
| 8-6 | [orpheus](orpheus/) | ✅ | Orpheus voice-consistency SFT completed in the [bounded GPU campaign](speech-sft-experiment/): 60 LoRA updates, held-out loss, matched base/adapted audio, timbre-proxy evaluation, hashes, and retained failures. |
| 8-7 | [MultilingualReasoning](MultilingualReasoning/) | 🚧 | The multilingual reasoning SFT implementation exists; repository-retained completion still requires a checkpoint and a before/after benchmark across Chinese and trained languages. |
| 8-9 | [cot-distillation](cot-distillation/) | ✅ | All 24 Kimi K3 teacher cases completed and were rule-filtered; 23 entered SFT. A real CUDA checkpoint and three-arm comparison are retained. The student's 2/24 versus the baseline's 1/24 is nonsignificant (p=1.0) and is reported as a negative result. |
| 8-10 | [AdaptThink](AdaptThink/) | ✅ | The [checkpoint-free training report](AdaptThink/TRAINING_REPORT.md) records public W&B run `wubbn5tj` on 8×H100. At step 300, mean response length fell on all three benchmarks, while AIME mean@16 accuracy declined by 0.42 pp. The run continued through step 410 and then crashed; checkpoints are not distributed, and no independent checkpoint-evaluation receipt was retained. |
| 8-11 | `SFTvsRL/` | 📖 | Systematically compares the effectiveness of Supervised Fine-Tuning (SFT) and Reinforcement Learning (RL) on different tasks, analyzing the strengths, weaknesses, and suitable application scenarios of both methods. |
| 8-12 | [SpatialReasoning](SpatialReasoning/) | 📖 | Focuses on training the spatial reasoning ability of models to handle problems involving spatial relationships such as position, direction, and distance. |
| 8-13 | [SimpleVLA-RL](SimpleVLA-RL/) | 📖 | Combines vision, language, and action in reinforcement learning training, enabling models to understand visual input and execute corresponding actions. |
| 8-14 | [retool](retool/) | 📖 | Uses multi-turn dialogue and a code sandbox to enhance the mathematical reasoning ability of large language models. Through a two-stage training process of SFT and RL, the model learns to use a code execution environment to assist in solving mathematical problems. Based on Qwen2.5-32B-Instruct, trained on the AIME 2024 dataset, using the DAPO algorithm and SandboxFusion sandbox. |
| 8-15 | `AWorld/` · [AWorld-train](AWorld-train/) | 📖 | Trains embodied agents based on the AWorld framework, enabling agents to perform complex tasks in a virtual environment and learn from experience. |
| 8-16 | [RLVP](RLVP/) | 📖 | RLVP post-training research — reward the outcome, penalize the path (companion to Experiment 8-16); the full training/evaluation code lives in the separate paper repository `19PINE-AI/rlvp`, which you need to clone yourself. |
| 8-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | Bad-case DPO repair for premature completion on GPU. |
| 8-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | Audited scope-sensitive Chinese curved-quote SFT: 1,024/256/256 train/holdout/boundary cases across 10 article types and 9 programming languages; Qwen3-8B GPU run reaches 96.9%/97.7% exact with 100% protected-region preservation. |
| 8-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | Audited byte-exact special-string SFT: 1,024/256/256 train/holdout/boundary cases; Qwen3-8B reaches 78.9% holdout and 80.1% boundary, with Qwen3/Qwen2.5/Mistral tokenizer round-trip audit. |
| — | `verl/` | 📖 | verl is an efficient reinforcement learning framework specifically designed for RLHF training of large language models, supporting various algorithms such as PPO, GRPO, and DAPO. |
| — | [Intuitor](Intuitor/) | ✅ | Trains the intuitive reasoning ability of models, enabling them to make quick, reasonable judgments without requiring detailed chains of thought. |
| — | `tinker-cookbook/` | 📖 | Collects various practical tips and best practices for model training. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
