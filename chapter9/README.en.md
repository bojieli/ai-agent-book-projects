# Chapter 9 · Agent Self-Evolution

> Growth without changing weights. Three learning paradigms, learning from experience, and the journey from "tool user" to "tool creator," allowing Agents to progress from "smart" to "skilled."

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter9.md)

## How to Read the Experiments

The prose uses short mechanism skeletons to explain control flow; the experiment directory contains complete SDK adapters, logs, tests, and acceptance evidence. You do not need to read every file line by line.

- **Starter:** Start with the goal, minimum command, and acceptance conditions; begin with [trajectory-verifier](trajectory-verifier/);
- **Builder:** Follow the entry point, core loop, state/message schema, tools, and verifier.
- **Maintainer:** Then read tests, evidence manifests, failure handling, rollback paths, and provider adapters.

On a first pass, skip credential loading, presentation code, and provider-compatibility layers; return when reproducing a number.

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 9-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | Experiment 9-1: combines environment outcomes, process rules, and language rubrics into evidence-backed diagnoses of customer-service trajectories |
| 9-2 | [gaia-experience](gaia-experience/) | ✅ | Experiment 9-2: compares successful, partially successful, and failed trajectories to generate cross-trajectory Markdown experience documents |
| 9-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | Experiment 9-3: generates minimal prompt patches from failed trajectories, controlling release with a boundary set and a retention set |
| 9-4 | Text experiment | 🚧 | Experiment 9-4: evolves a requirements-clarification and Spec-confirmation Skill from user feedback, with a three-arm A/B design and release gates |
| 9-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | Experiment 9-5: compiles browser trajectories into workflows with state predicates, verified by reset-and-replay |
| 9-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | Experiment 9-6: repeated failures trigger retry/circuit-breaker code patches, regression tests, canary rollout, and rollback |
| 9-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | Experiment 9-7: evolves a high-risk operation confirmation gate from user corrections and audits |
| 9-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | Experiment 9-8: gives Hermes the whole book and its own source; it chooses an improvement, changes itself, and turns each Reviewer rejection into another learning round until accepted |
| 9-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | Experiment 9-9: evaluates long-term evolution across four phases — learning, transfer, rule change, and retention |

All experiments above offer offline entry points and unit tests that require no API Key; extension paths that need real models or a browser are documented in each project's README.

## Supplementary Cases

| Exp. | Project | Relation |
| :--: | --- | --- |
| 8-8 | [prompt-distillation](../chapter8/prompt-distillation/) | Cross-chapter project on prompt distillation and parameterized learning; the training method belongs to Chapter 8 |
| — | [self-evolving-tools](self-evolving-tools/) | Alita-style tool discovery, encapsulation, and reuse — a supplementary case of "writing experience into programs" |
| — | [ai-style-skill](ai-style-skill/) | Supplementary writing-Skill case; the main example appears in Chapter 2 |

## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
