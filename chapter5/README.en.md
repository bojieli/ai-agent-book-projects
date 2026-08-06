# Chapter 5 · Coding Agent and Code Generation

> Code is a "tool that can create new tools" and is the meta-capability of a general-purpose Agent. Uses a production-grade Coding Agent as an example to demonstrate the complete implementation of this most powerful general tool.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter5.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 5-1 | [code-for-math](code-for-math/) | ✅ | Compare "pure chain-of-thought" vs. "code-assisted" modes using the same model on the same set of competitive math problems. In the latter mode, problems are formalized into Python (sympy/numpy/scipy) and executed via function calling in a subprocess sandbox, replacing error-prone mental calculation with precise computation, resulting in significantly higher accuracy. |
| 5-2 | [code-for-logic](code-for-logic/) | ✅ | Transform "Knights and Knaves" logic puzzles into Constraint Satisfaction Problems (CSP). The Agent uses `python-constraint` to define variables and biconditional constraints, then invokes the solver. Compare the accuracy of pure natural language reasoning vs. code-assisted modes on a set of K&K puzzles. |
| 5-3 | [small-model-codified-rules](small-model-codified-rules/) | ✅ | A controlled experiment based on the τ-bench airline customer service scenario: after moving complex business policies (refund rules) from natural language prompts into code/tools, the task success rate and policy adherence of a small model improved dramatically. In-tool code validation can intercept the model's erroneous beliefs in real-time. |
| 5-4 | [paper-to-ppt](paper-to-ppt/) | ✅ | Reframe "making a PPT" as a code generation problem: The Proposer writes Slidev (Markdown+HTML) code, the Reviewer renders each page into a PNG and uses a Vision LLM to check for layout issues, iterating on revisions based on structured feedback. This dual-agent division of labor results in a significantly lower peak context size. |
| 5-5 | [paper-to-video](paper-to-video/) | ✅ | Building on "Paper → PPT", generate colloquial narration scripts for each slide, synthesize speech using TTS, and then use ffmpeg to synchronize each slide's screenshot with its audio, page by page, to create a narrated explanation video. |
| 5-6 | [video-edit](video-edit/) | ✅ | Given a multi-scene video and a natural language request, the Agent uses a "two-step Vision localization" process (coarse-to-fine frame extraction and reading) to determine the target scene's time boundaries. After cutting the segment, the Reviewer extracts keyframes from the resulting clip for verification, iterating if the result is unsatisfactory. |
| 5-7 | [adaptive-log-parser](adaptive-log-parser/) | ✅ | A self-evolving log parsing system: when encountering a new, unparseable format, it doesn't raise an error. Instead, it feeds the failed sample and error message to a code generation Agent to produce a `parse` function. After automatic testing passes, the function is hot-updated and registered into the parsing engine, requiring no human intervention throughout the entire process. |
| 5-8 | [log-diagnosis](log-diagnosis/) | ✅ | A diagnostic Agent reads live HTTP trajectories, architecture documents, and PRDs; generates and replays regression tests before and after the fix; and creates a real Issue through the official GitHub MCP server with credential-free receipts. |
| 5-9 | [dynamic-form](dynamic-form/) | ✅ | When faced with an incomplete request, the Agent doesn't ask questions one by one. Instead, it dynamically generates a self-contained HTML form with cascading logic, allowing the user to fill in all missing information at once. The frontend aggregates the form data into JSON and returns it to the Agent to continue the task. |
| 5-10 | [erp-agent](erp-agent/) | ✅ | Translate Chinese natural language queries into SQL for database execution, directly presenting the resulting table. The core is the artifact pattern: the LLM only generates the SQL artifact without moving the data itself, saving tokens and avoiding manual calculation errors. Even result sets with tens of thousands of rows can be returned instantly. |
| 5-11 | [conversational-ui](conversational-ui/) | ✅ | Users propose UI customization requests (color/font/text/layout) in natural language. The Agent autonomously locates and modifies the React frontend source code. Leveraging Vite's Hot Module Replacement (HMR), changes take effect instantly, supporting multi-turn iterative customization. |
| 5-12 | [permission-embedded-data-objects](permission-embedded-data-objects/) | ✅ | A PostgreSQL-backed object store keeps authorization, validation, referential integrity, and controlled reactions below dynamically generated application code. |
| 5-13 | [agent-creator](agent-creator/) | ✅ | A metaprogramming Agent compares creating a new Agent from a validated reference implementation with generating one from scratch; both arms are compiled, tested, and exercised through a real Kimi K3 tool-calling API campaign. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
