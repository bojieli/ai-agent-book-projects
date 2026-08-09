# Chapter 1 · Agent Fundamentals

> Starting from the new paradigm of "Model as Agent," establishes the core formula **Agent = LLM + Context + Tools**, and introduces Harness engineering—all engineering capabilities beyond the model are the true competitive advantage.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter1.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | Demonstrates the importance of various Agent context components through systematic ablation experiments. Supports direct Alibaba Cloud Model Studio Qwen plus SiliconFlow Qwen, ByteDance Doubao, Moonshot Kimi, and other providers. |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | Implements an Agent with basic deep search capabilities, capable of multi-round searching and information integration. |
| 1-3 | [search-codegen](search-codegen/) | ✅ | Builds an Agent with basic deep search and code sandbox capabilities, utilizing tools like web search and code execution for complex analysis. |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | Compares traditional reinforcement learning (Q-learning) with LLM-based in-context learning, reproducing key insights from Shunyu Yao's "The Second Half" blog post. Demonstrates how LLMs can surpass traditional RL with 250-400x sample efficiency through a treasure hunt game. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
