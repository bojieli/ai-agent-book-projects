# Chapter 10 · Multi-Agent Collaboration

> Collective intelligence can surpass individual intelligence. Multi-Agent classification framework, when it truly outperforms a single Agent, collaboration with and without shared context, failure modes, and the emergent "Agent Society."

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter10.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | The same Coding Agent loads different system prompts and tool sets at different execution stages of a task (requirements clarification → code implementation → code review). This allows it to play different roles and exhibit different behaviors within a single conversation, while the dialogue history and task state are continuously shared between stages. If the review fails, it can fall back to the implementation stage. |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | Demonstrates chained handoff under a shared context: a single session contains multiple specialized role agents, each with its own system prompt and dedicated tool set. Using a `transfer_to_agent` tool, an agent autonomously decides when to switch to another role based on task progress. Because they share the same dialogue history, the complete context is naturally preserved during handoff. |
| 10-3 | [book-translation](book-translation/) | ✅ | Uses the orchestrator mode to decompose long document translation into specialized agents for glossary/translation/proofreading. The Manager only saves tasks, plans, call records, and file indices; the complete translated text is written to disk, keeping the context roughly constant. It compares this with a single-agent approach, using real token counts to illustrate how to control context explosion and ensure consistency across the book with a shared glossary. |
| 10-4 | `use-computer-while-calling/` | 📖 | Implements a dual-agent collaboration architecture with a Phone Call Agent and a Computer Use Agent. The two agents communicate directly via WebSocket without a coordinator. The Phone Agent handles voice interaction, while the Computer Agent performs browser automation, working in parallel to complete complex tasks requiring both voice and web operations. The code has evolved into the independently maintained [TalkAct](https://github.com/19PINE-AI/TalkAct); this repo does not bundle the directory (see the main README appendix for the clone command). |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | Demonstrates parallel search by multiple homogeneous agents with central coordination: the main coordinator simultaneously launches N sub-agents, each accessing one source to find an answer. Once one hits the target, the others gracefully stop. Message bus, parallel dispatch, real-time monitoring, cascading termination, and race condition handling are all implemented realistically (using controllable simulated information sources instead of a real browser). |
| 10-7 | `generative_agents/` | 📖 | Stanford's "AI town" generative agents (companion to Experiment 10-7); external repository `joonspk-research/generative_agents`, which you need to clone yourself (see the main README appendix). |
| 10-8 | [voice-werewolf](voice-werewolf/) | ✅ | Uses a multi-agent werewolf game to demonstrate information access control under "non-shared context": each player is an independent LLM agent with a strictly isolated private context. A code-driven deterministic judge decides which information is delivered to which player's context, registers it for auditing, and automatically verifies isolation correctness at the end of the game. Voice is an optional enhancement. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **Design Doc** | Architecture/implementation plan only, runnable code still WIP |
