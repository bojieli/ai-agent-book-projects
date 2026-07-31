# Chapter 7 · Model Post-Training

> A comprehensive view of the three stages: pre-training, SFT, and RL. When to choose SFT vs. RL, RLHF, algorithm comparison, data and environments, and cutting-edge exploration into teaching models tool calling and improving sample efficiency.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter7.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 7-1, 7-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | Runs Q-learning and an LLM Agent in the same treasure-hunt environment to learn from experience. |
| 7-8 | [prompt-distillation](../chapter8/prompt-distillation/) | 🚧 | Distills teacher examples into a student prompt and compares quality and cost. |
| 7-3, 7-4 | [MiniMind-pretrain](MiniMind-pretrain/) | 📖 | Pretrains a small language model from scratch to understand the complete pretraining process and key technologies. |
| 7-5 | [continued-pretraining](continued-pretraining/) | ✅ | Performs continued pretraining on domain-specific data to improve model performance in the target domain. |
| 7-6 | [sesame](sesame/) | ✅ | Sesame CSM speech SFT: LoRA fine-tuning of the 1B TTS model, controlling expression with paralinguistic tags like `<laugh>` and `<sigh>` |
| 7-6 | [orpheus](orpheus/) | ✅ | Orpheus 3B speech SFT: LoRA fine-tuning of the TTS model, voice cloning via reference audio for cross-sentence timbre consistency |
| 7-7 | [MultilingualReasoning](MultilingualReasoning/) | ✅ | Trains the reasoning ability of models in multiple language environments, improving performance on cross-lingual tasks. |
| 7-9 | [cot-distillation](cot-distillation/) | ✅ | Distills CoT trajectories from frontier models like Claude via OpenRouter; rule-verified and converted into SFT data (companion to Experiment 7-9). |
| 7-10 | [AdaptThink](AdaptThink/) | 📖 | Teaches reasoning models to adaptively choose their reasoning mode (Thinking vs NoThinking) based on problem difficulty. Through constrained optimization and importance sampling, it significantly reduces reasoning costs (45-69%) while improving accuracy. Based on the DeepSeek-R1-Distill-Qwen model, trained using the DAPO algorithm. |
| 7-11 | `SFTvsRL/` | 📖 | Systematically compares the effectiveness of Supervised Fine-Tuning (SFT) and Reinforcement Learning (RL) on different tasks, analyzing the strengths, weaknesses, and suitable application scenarios of both methods. |
| 7-12 | [SpatialReasoning](SpatialReasoning/) | 📖 | Focuses on training the spatial reasoning ability of models to handle problems involving spatial relationships such as position, direction, and distance. |
| 7-13 | [SimpleVLA-RL](SimpleVLA-RL/) | 📖 | Combines vision, language, and action in reinforcement learning training, enabling models to understand visual input and execute corresponding actions. |
| 7-14 | [RLVP](RLVP/) | 📖 | RLVP post-training research — reward the outcome, penalize the path (companion to Experiment 7-14); the full training/evaluation code lives in the separate paper repository `19PINE-AI/rlvp`, which you need to clone yourself. |
| 7-15 | [retool](retool/) | 📖 | Uses multi-turn dialogue and a code sandbox to enhance the mathematical reasoning ability of large language models. Through a two-stage training process of SFT and RL, the model learns to use a code execution environment to assist in solving mathematical problems. Based on Qwen2.5-32B-Instruct, trained on the AIME 2024 dataset, using the DAPO algorithm and SandboxFusion sandbox. |
| 7-16 | `AWorld/` · [AWorld-train](AWorld-train/) | 📖 | Trains embodied agents based on the AWorld framework, enabling agents to perform complex tasks in a virtual environment and learn from experience. |
| — | `verl/` | 📖 | verl is an efficient reinforcement learning framework specifically designed for RLHF training of large language models, supporting various algorithms such as PPO, GRPO, and DAPO. |
| — | [Intuitor](Intuitor/) | ✅ | Trains the intuitive reasoning ability of models, enabling them to make quick, reasonable judgments without requiring detailed chains of thought. |
| — | `tinker-cookbook/` | 📖 | Collects various practical tips and best practices for model training. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
