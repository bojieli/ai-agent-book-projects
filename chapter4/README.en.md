# Chapter 4 · Tools

> Tools are the hands of an Agent. Discusses tool classification and general design principles, the MCP protocol and challenges of tool selection, three types of tools (perception, execution, collaboration), and event-driven asynchronous Agents.

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter4.md)

## How to Read the Experiments

The prose uses short mechanism skeletons to explain control flow; the experiment directory contains complete SDK adapters, logs, tests, and acceptance evidence. You do not need to read every file line by line.

- **Starter:** Start with the goal, minimum command, and acceptance conditions; begin with [execution-tools](execution-tools/);
- **Builder:** Follow the entry point, core loop, state/message schema, tools, and verifier.
- **Maintainer:** Then read tests, evidence manifests, failure handling, rollback paths, and provider adapters.

On a first pass, skip credential loading, presentation code, and provider-compatibility layers; return when reproducing a number.

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | Build a comprehensive set of perception tools, providing capabilities for web search, multimodal understanding, file system operations, and access to public data sources. Most features are based on free, open APIs (DuckDuckGo, Open-Meteo, Yahoo Finance, OpenStreetMap, etc.) and require no API key. |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | The canonical 20-call campaign passes 13/15 gates, including safe execution, a real GitHub PR, Xvfb desktop Computer Use, and KVM-backed Android actions; only authorized Calendar and email mutations remain blocked. |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | Provide comprehensive collaboration capabilities, including browser automation (browser-use framework), Human-in-the-Loop, multi-channel notifications (Email, Telegram, Slack, Discord), and timer management. Supports admin approval for sensitive operations and scheduled task dispatching. |
| 4-5 | [active-tool-discovery](active-tool-discovery/) | ✅ | Compares two paradigms: "injecting all 120+ tool schemas" vs. "active on-demand discovery." The latter keeps only a few basic tools and a `discover_tools` meta-tool in the system prompt, using embedding similarity to retrieve the 3-5 most relevant specialized tools from a tool library. This saves tokens and prevents the model from incorrectly selecting or misusing general tools from an overly long list. |
| — | [active-tool-selection](active-tool-selection/) | ✅ | Implement an intelligent tool selection mechanism that allows the Agent to actively choose the most suitable combination of tools based on task requirements, rather than passively accepting a predefined tool set. |

Runnable-project status is separate from manuscript acceptance. Experiments
4-1 through 4-5 have substantial real execution coverage but remain officially
incomplete because authorized private-data, Calendar/email mutation,
human-decision, notification, or real-mailbox gates are still blocked. The
Android and Computer Use gates for 4-3 now have substantive retained execution.
See the [experiment ledger](EXPERIMENT_LEDGER.md) for the exact boundary.

> Additionally, `chapter4/docker-compose.yml` and `chapter4/DOCKER_DEPLOYMENT.md` provide a reference solution for containerizing and deploying the aforementioned MCP tool servers.
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
