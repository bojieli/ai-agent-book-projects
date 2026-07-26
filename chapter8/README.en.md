# Chapter 8 · Agent Self-Evolution

> Growth without changing weights. Three learning paradigms, learning from experience, and the journey from "tool user" to "tool creator," allowing Agents to progress from "smart" to "skilled."

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter8.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | ✅ | Distills the effectiveness of complex prompts into model parameters, reducing prompt length during inference and solidifying contextual experience into parameterized knowledge. |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Based on the AWorld framework and GAIA benchmark, implements a complete "learn-apply" loop. The agent automatically summarizes successful task trajectories into structured experiences and retrieves and applies them in new tasks, achieving self-evolution. |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Automated system prompt learning based on human feedback: Using the tau-bench style airline customer service "over-transfer" problem as an example, a Coding Agent reads the system prompt file, identifies problematic rules, generates precise modifications, and actually rewrites the prompt file. It then re-evaluates the changes, forming a "feedback → rewrite → verify" loop. |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | Implements a workflow recording system for browser automation, automatically encapsulating repetitive operation sequences into parameterized tools. By switching from expensive LLM inference to precise automated execution, it achieves a 3-5x speed improvement. |
| 8-6 | [self-evolution-eval](self-evolution-eval/) | ✅ | A dedicated dataset and validation methodology designed to evaluate an agent's "self-evolution" capability (discovering, creating, and reusing tools on its own): 20 cross-domain tasks (without hinting at tool names) + a four-layer hierarchical validation harness + a controllable reference agent. It goes beyond checking "if the result is correct" to assess the quality of discovery, creation, and reuse. |
| — | [self-evolving-tools](self-evolving-tools/) | ✅ | An Alita-style "minimal predefined, maximum self-evolution" approach: The agent has no pre-built domain-specific tools, only five general meta-tools. When encountering a task it cannot perform, it searches the web for open-source libraries/APIs, reads documentation, tests them in a sandbox, encapsulates feasible solutions as new tools, stores them in the tool library for reuse, and emphasizes hallucination control throughout the process. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
