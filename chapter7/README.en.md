# Chapter 7 · Model Post-Training

> A comprehensive view of the three stages: pre-training, SFT, and RL. When to choose SFT vs. RL, RLHF, algorithm comparison, data and environments, and cutting-edge exploration into teaching models tool calling and improving sample efficiency.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter7.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 7-1, 7-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | Runs Q-learning and an LLM Agent in the same treasure-hunt environment to learn from experience. |
| 7-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | The [retained campaign](../chapter8/prompt-distillation/validation/exp7-8-kimi3-smollm2-20260730/) contains 160/160 training and 80/80 held-out Kimi K3 teacher receipts, a real CUDA-trained SmolLM2-135M-Instruct LoRA checkpoint, and passes all 8 gates; held-out accuracy is 100% for the teacher, 0% for baseline, and 95% for the trained student. |
| 7-3, 7-4 | [MiniMind-pretrain](MiniMind-pretrain/) | ✅ | Experiment 7-3's [canonical report](MiniMind-pretrain/validation/runs/exp7-3-training-report-20260731-v1/report.md) retains 49 historical LLM outputs and eight blind judgments. Experiment 7-4's [canonical report](MiniMind-pretrain/validation/runs/exp7-4-training-report-20260731-v1/report.md) retains all 64 historical outputs across eight VLM configurations and images plus eight real image-aware blind judgments. Original VLM SFT ranked highest at 1.9062 and matched QK-Norm+Muon comparisons did not improve, an explicit negative result. Historical checkpoints are not distributed or required for acceptance. |
| 7-5 | [continued-pretraining](continued-pretraining/) | ✅ | [Canonical training report](continued-pretraining/validation/runs/exp7-5-training-report-20260731-v1/report.md) binds the RTX 4090 three-stage output, 15 generations, five blind ARK judgments, source hashes, and current reproduction revisions; final Korean gained 1.7777, English fell 0.8333, and kimchi factual errors remain explicit. Checkpoints are not distributed or required for acceptance. |
| 7-6 | [sesame](sesame/) | ✅ | Sesame CSM tag SFT completed in the [bounded GPU campaign](speech-sft-experiment/): 60 LoRA updates, held-out loss, matched tag/no-tag audio, detector-proxy evaluation, hashes, and retained failures. |
| 7-6 | [orpheus](orpheus/) | ✅ | Orpheus voice-consistency SFT completed in the [bounded GPU campaign](speech-sft-experiment/): 60 LoRA updates, held-out loss, matched base/adapted audio, timbre-proxy evaluation, hashes, and retained failures. |
| 7-7 | [MultilingualReasoning](MultilingualReasoning/) | 🚧 | The multilingual reasoning SFT implementation exists; repository-retained completion still requires a checkpoint and a before/after benchmark across Chinese and trained languages. |
| 7-9 | [cot-distillation](cot-distillation/) | ✅ | All 24 Kimi K3 teacher cases completed and were rule-filtered; 23 entered SFT. A real CUDA checkpoint and three-arm comparison are retained. The student's 2/24 versus the baseline's 1/24 is nonsignificant (p=1.0) and is reported as a negative result. |
| 7-10 | [AdaptThink](AdaptThink/) | ✅ | The [checkpoint-free training report](AdaptThink/TRAINING_REPORT.md) records public W&B run `wubbn5tj` on 8×H100. At step 300, mean response length fell on all three benchmarks, while AIME mean@16 accuracy declined by 0.42 pp. The run continued through step 410 and then crashed; checkpoints are not distributed, and no independent checkpoint-evaluation receipt was retained. |
| 7-11 | `SFTvsRL/` | 📖 | Systematically compares the effectiveness of Supervised Fine-Tuning (SFT) and Reinforcement Learning (RL) on different tasks, analyzing the strengths, weaknesses, and suitable application scenarios of both methods. |
| 7-12 | [SpatialReasoning](SpatialReasoning/) | 📖 | Focuses on training the spatial reasoning ability of models to handle problems involving spatial relationships such as position, direction, and distance. |
| 7-13 | [SimpleVLA-RL](SimpleVLA-RL/) | 📖 | Combines vision, language, and action in reinforcement learning training, enabling models to understand visual input and execute corresponding actions. |
| 7-14 | [retool](retool/) | 📖 | Uses multi-turn dialogue and a code sandbox to enhance the mathematical reasoning ability of large language models. Through a two-stage training process of SFT and RL, the model learns to use a code execution environment to assist in solving mathematical problems. Based on Qwen2.5-32B-Instruct, trained on the AIME 2024 dataset, using the DAPO algorithm and SandboxFusion sandbox. |
| 7-15 | `AWorld/` · [AWorld-train](AWorld-train/) | 📖 | Trains embodied agents based on the AWorld framework, enabling agents to perform complex tasks in a virtual environment and learn from experience. |
| 7-16 | [RLVP](RLVP/) | 📖 | RLVP post-training research — reward the outcome, penalize the path (companion to Experiment 7-16); the full training/evaluation code lives in the separate paper repository `19PINE-AI/rlvp`, which you need to clone yourself. |
| 7-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | Bad-case DPO repair for premature completion on GPU. |
| 7-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | Audited scope-sensitive Chinese curved-quote SFT: 1,024/256/256 train/holdout/boundary cases across 10 article types and 9 programming languages; Qwen3-8B GPU run reaches 96.9%/97.7% exact with 100% protected-region preservation. |
| 7-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | Audited byte-exact special-string SFT: 1,024/256/256 train/holdout/boundary cases; Qwen3-8B reaches 78.9% holdout and 80.1% boundary, with Qwen3/Qwen2.5/Mistral tokenizer round-trip audit. |
| — | `verl/` | 📖 | verl is an efficient reinforcement learning framework specifically designed for RLHF training of large language models, supporting various algorithms such as PPO, GRPO, and DAPO. |
| — | [Intuitor](Intuitor/) | ✅ | Trains the intuitive reasoning ability of models, enabling them to make quick, reasonable judgments without requiring detailed chains of thought. |
| — | `tinker-cookbook/` | 📖 | Collects various practical tips and best practices for model training. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
