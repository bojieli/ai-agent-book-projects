# Chapter 2 · Context Engineering

> Context determines the upper bound of Agent capabilities. Delves into the context structure of LLM APIs, KV Cache-friendly design, prompt engineering, dynamic prompts and Agent Skills, status bar meta-information, and context compression strategies.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter2.md)

## How to Read the Experiments

The prose uses short mechanism skeletons to explain control flow; the experiment directory contains complete SDK adapters, logs, tests, and acceptance evidence. You do not need to read every file line by line.

- **Starter:** Start with the goal, minimum command, and acceptance conditions; begin with [context-compression](context-compression/);
- **Builder:** Follow the entry point, core loop, state/message schema, tools, and verifier.
- **Maintainer:** Then read tests, evidence manifests, failure handling, rollback paths, and provider adapters.

On a first pass, skip credential loading, presentation code, and provider-compatibility layers; return when reproducing a number.

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 2-1 | [local_llm_serving](local_llm_serving/) | ✅ | A cross-platform local LLM deployment solution that automatically selects the best backend (vLLM or Ollama). Demonstrates that even a 0.6B small model can achieve excellent tool calling capabilities through good system design. Supports streaming responses for real-time thought process display. |
| 2-2, 2-8 | [attention_visualization](attention_visualization/) | ✅ | Visualizes the complete input/output token sequence and attention weight distribution of an LLM, providing deep insight into how the model processes context, performs reasoning, and calls tools. |
| 2-3 | [kv-cache](kv-cache/) | ✅ | Explores the impact of different context management modes on KV Cache, demonstrating how common error patterns destroy cache efficiency. Shows through experiments how proper context design can significantly reduce latency and cost. |
| 2-4 | [prompt-engineering](prompt-engineering/) | ✅ | Extends the Tau-Bench framework to quantify the impact of different prompt engineering factors on Agent performance through systematic ablation experiments. Shows how factors like tone, instruction organization, and tool descriptions affect task completion rates. |
| 2-5 | [prompt-injection](prompt-injection/) | ✅ | Constructs a controlled experiment with 3 attack scenarios (direct injection, indirect injection, memory injection) × 4 defense configurations (no defense, prompt hardening, source tagging, combined defense). Uses deterministic rules to calculate attack success rates, visually demonstrating how layered defenses significantly reduce injection success rates. |
| 2-6 | [agent-skills-ppt](agent-skills-ppt/) | ✅ | Reproduces the "progressive disclosure" concept of Agent Skills: the Agent initially sees only a thin Skill directory. Only after identifying that the task requires the `pptx` Skill does it progressively load its complete workflow, detailed documentation, and bundled scripts, ultimately generating a real `.pptx` file using python-pptx. |
| 2-7 | Text experiment | 🚧 | Creates a lightweight writing Skill from personal examples, covering trigger conditions, rules, examples, scope, and iterative maintenance. |
| 2-9 | [system-hint](system-hint/) | ✅ | Studies the impact of System Hints on Agent behavior, exploring how to improve performance by optimizing system prompts. |
| 2-10 | [context-compression](context-compression/) | ✅ | Implements and compares multiple context compression strategies, including summarization, key information extraction, and semantic compression. Reduces token usage while maintaining Agent capabilities. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
