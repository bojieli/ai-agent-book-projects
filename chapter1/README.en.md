# Chapter 1 · Agent Fundamentals

> Starting from the new paradigm of "Model as Agent," establishes the core formula **Agent = LLM + Context + Tools**, and introduces Harness engineering—all engineering capabilities beyond the model are the true competitive advantage.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter1.md)

## How to Read the Experiments

The prose uses short mechanism skeletons to explain control flow; the experiment directory contains complete SDK adapters, logs, tests, and acceptance evidence. You do not need to read every file line by line.

- **Starter:** Start with the goal, minimum command, and acceptance conditions; begin with [context](context/);
- **Builder:** Follow the entry point, core loop, state/message schema, tools, and verifier.
- **Maintainer:** Then read tests, evidence manifests, failure handling, rollback paths, and provider adapters.

On a first pass, skip credential loading, presentation code, and provider-compatibility layers; return when reproducing a number.

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | Demonstrates the importance of various Agent context components through systematic ablation experiments. Supports direct Alibaba Cloud Model Studio Qwen plus SiliconFlow Qwen, ByteDance Doubao, Moonshot Kimi, and other providers. |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Implements an Agent with basic deep search capabilities, capable of multi-round searching and information integration. |
| 1-3 | [search-codegen](search-codegen/) | ✅ | Builds an Agent with basic deep search and code sandbox capabilities, utilizing tools like web search and code execution for complex analysis. |
| 1-4 | [image-gen-workflow](image-gen-workflow/) | ✅ | A real two-route comparison across concrete/broad requirements × workflow (kimi-k3 rewriting + Tongyi Wanxiang) vs. native (Gemini / GPT-Image 2): for concrete requirements the native route is more faithful (the poster copy was dropped into the negative prompts by the rewriting node); for broad requirements, the rewriting node's scene concretization brings imagination, but GPT-Image 2 can supply viewpoints on its own—empirical evidence that the adapter layer is internalized by the model. |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | Compares traditional reinforcement learning (Q-learning) with LLM-based in-context learning, reproducing key insights from Shunyu Yao's "The Second Half" blog post. Demonstrates how LLMs can surpass traditional RL with 250-400x sample efficiency through a treasure hunt game. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
