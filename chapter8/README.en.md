# Chapter 8 · Agent Self-Evolution

> Growth without changing weights. Three learning paradigms, learning from experience, and the journey from "tool user" to "tool creator," allowing Agents to progress from "smart" to "skilled."

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter8.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Experiment 8-1: combines environment outcomes, process rules, and language rubrics into evidence-backed diagnoses of customer-service trajectories |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | Experiment 8-2: compares successful, partially successful, and failed trajectories to generate cross-trajectory Markdown experience documents |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Experiment 8-3: generates minimal prompt patches from failed trajectories, controlling release with a boundary set and a retention set |
| 8-4 | [browser-use-rpa](browser-use-rpa/) | ✅ | Experiment 8-4: compiles browser trajectories into workflows with state predicates, verified by reset-and-replay |
| 8-5 | [self-modifying-agent](self-modifying-agent/) | ✅ | Experiment 8-5: repeated failures trigger retry/circuit-breaker code patches, regression tests, canary rollout, and rollback |
| 8-6 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Gives Hermes the whole book and its own source; it chooses an improvement, changes itself, and turns each Reviewer rejection into another learning round until accepted |
| 8-7 | [self-evolution-eval](self-evolution-eval/) | ✅ | Experiment 8-7: evaluates long-term evolution across four phases — learning, transfer, rule change, and retention |
| 8-8 | [harness-safety-gate](harness-safety-gate/) | ✅ | High-risk operation confirmation gate |
| 8-9 | [ai-style-skill](ai-style-skill/) | ✅ | Turns writing feedback into a verifiable Skill; the chapter also connects the curved-quote Skill to audited synthetic data and post-training, and separates tokenizer/Harness failures for exact-copy cases |

All experiments above offer offline entry points and unit tests that require no API Key; extension paths that need real models or a browser are documented in each project's README.

## Supplementary Cases

| Exp. | Project | Relation |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | Cross-chapter project on prompt distillation and parameterized learning; the training method belongs to Chapter 7 |
| — | [self-evolving-tools](self-evolving-tools/) | Alita-style tool discovery, encapsulation, and reuse — a supplementary case of "writing experience into programs" |

## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
