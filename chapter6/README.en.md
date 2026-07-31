# Chapter 6 · Agent Evaluation

> Turns Agent performance into comparable signals. Covers evaluation environments, dataset design, metric systems, statistical significance, observability, evaluation-driven selection, and production-grade internal evaluation and simulation environments.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter6.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 6-1 | `tau2-bench/` | 📖 | Focuses on evaluating an agent's ability to use tools for complex reasoning, including scenarios such as computation, search, and data processing. |
| 6-2 | `tau2-bench/` | 📖 | Manually completes graded τ²-bench tasks and records their trajectories. |
| 6-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | Runs the four-level rubric over 180 structured judgments with evidence and a hallucination veto. |
| 6-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | Runs 60 cases across three systems with complete cost accounting. |
| 6-10 | [user-memory-system-evaluation](user-memory-system-evaluation/) | 🚧 | The full 4×3×2×60 component, model, and evaluator matrix remains pending. |
| 6-12 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | 🚧 | Pins the OpenVLA and RoboTwin2 setup; completion requires a checkpoint, simulator, and 8 GPUs. |
| 6-2 | `terminal-bench/` | 📖 | Terminal-Bench is a benchmark for testing AI Agent performance in real terminal environments. From compiling code to training models and setting up servers, it evaluates how Agents handle real end-to-end tasks. Includes a dataset of ~100 tasks and an execution framework, supporting various Agent implementations. |
| 6-2 | `SWE-bench/` | 📖 | SWE-bench is a benchmark for evaluating the ability of large language models to solve real GitHub issues. Given a codebase and an issue description, the model must generate a patch that resolves the problem. Includes multiple versions: SWE-bench, SWE-bench Lite, SWE-bench Verified, and SWE-bench Multimodal. |
| 6-2 | `GAIA/` | 📖 | GAIA aims to evaluate next-generation LLMs (those with tool augmentation, efficient prompting, search access, etc.). It contains 450+ non-trivial questions requiring varying degrees of tool use and autonomy, with unambiguous answers. Divided into 3 difficulty levels. |
| 6-2 | `OSWorld/` | 📖 | Evaluates the ability of agents to perform complex tasks within a complete operating system environment, including file management, application operation, and system configuration. |
| 6-2, 6-11 | `android_world/` | 📖 | Evaluates agent performance in an Android mobile environment, including app navigation, UI interaction, and task completion capabilities (external benchmark repo). |
| 6-5 | [tts-quality-eval](tts-quality-eval/) | ✅ | Synthesizes the same set of challenging texts using various TTS configurations (different model/voice/speed), then uses a multimodal LLM-as-a-Judge to score each dimension (clarity, naturalness, etc.) according to a Rubric, aggregating the results into a reproducible configuration comparison table. |
| 6-6 | [elo-leaderboard](elo-leaderboard/) | ✅ | Implements an agent performance leaderboard based on the ELO rating system, evaluating the relative abilities of different agents through pairwise comparisons. |
| 6-7 | [model-action-threshold](model-action-threshold/) | ✅ | Compares GPT-5.6-sol and Claude Sonnet 5 at the transition from exploration to the first edit under the same neutral Coding Harness; all 18/18 cells completed without API errors, and the [manifest](model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json) binds the trajectories and summaries with verifiable hashes. |
| 6-8 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | Performs a full-chain cost breakdown for a typical multi-turn agent task (customer service refund): uses a custom lightweight tracing system to record input/output/cache tokens, latency, and cost for each LLM call, aggregates to identify "which step is the most expensive," and then uses A/B testing to quantify the real savings from KV-cache-friendly design and context compression. |
| 6-9 | [model-benchmark](model-benchmark/) | ✅ | Conducts a horizontal benchmark of multiple OpenAI-compatible LLM API providers. It uses a streaming interface to precisely measure Time to First Token (TTFT), calculates end-to-end latency percentiles (p50/p95), throughput, and success rate under concurrency. A single command produces a multi-dimensional comparison table, illustrating that model selection is a multi-faceted trade-off rather than just looking at a leaderboard. |
| 6-11 | [android-world](android-world/) | 📖 | In-repo T3A evaluation report and failure analysis notes on AndroidWorld (starting point for Experiment 6-11; not the benchmark source). |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | Uses synthetic DHIS2-style aggregate data to objectively evaluate a public-health reporting agent's tool calls, calculation accuracy, evidence citations, and unsupported claims. |

> Backtick-named external benchmarks must be cloned separately. [`android-world/`](android-world/) (hyphenated) is this repo's **T3A evaluation analysis notes** (see its [README](android-world/README.md)), not the same path as the external `android_world/` benchmark source.
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
