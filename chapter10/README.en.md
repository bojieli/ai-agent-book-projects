# Chapter 10 · Multi-Agent Collaboration

> Collective intelligence can surpass individual intelligence. Multi-Agent classification framework, when it truly outperforms a single Agent, collaboration with and without shared context, failure modes, and the emergent "Agent Society."

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter10.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | The same Coding Agent loads different system prompts and tool sets at different execution stages of a task (requirements clarification → code implementation → code review). This allows it to play different roles and exhibit different behaviors within a single conversation, while the dialogue history and task state are continuously shared between stages. If the review fails, it can fall back to the implementation stage. |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | Demonstrates chained handoff under a shared context: a single session contains multiple specialized role agents, each with its own system prompt and dedicated tool set. Using a `transfer_to_agent` tool, an agent autonomously decides when to switch to another role based on task progress. Because they share the same dialogue history, the complete context is naturally preserved during handoff. |
| 10-3 | [book-translation](book-translation/) | ✅ | The formal 26-unit dual-arm run translates an illustrated, code-heavy technical-book sample and passes all 12 gates, including quality, context, token, latency, resource, checkpoint, receipt, and provenance comparisons. |
| 10-4 | [TalkAct reproduction record](talkact-reproduction/) + `use-computer-while-calling/` | 📖 | The pinned `7d70007…` source and six runtime file hashes match and Python 3.12 is available, but the 2026-08-03 official Anthropic endpoint probe returned HTTP 401. Both fast/slow tiers are externally blocked before a model call; no 16-episode comparison is claimed. |
| 10-5 | [autonomous-phone-registration](autonomous-phone-registration/) | ✅ | A real LLM autonomously selected the Phone Agent, and the formal run passed all 9 gates over Playwright, bidirectional WebRTC/RTP, local TTS/Whisper, validation and re-asking, concurrent ask/fill, privacy, and one authorized localhost submission. The manuscript does not require PSTN/E.164. |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | N independent Playwright browser sessions search ten real university sites while a real LLM extracts cited evidence. Saved acceptance covers monitoring, timeout/error isolation, single settlement, cascading termination acknowledgements, resource cleanup, and a measured 3.142× same-site parallel speedup. |
| 10-7 | `generative_agents/` | 📖 | Stanford's "AI town" generative agents (companion to Experiment 10-7); external repository `joonspk-research/generative_agents`, which you need to clone yourself (see the main README appendix). |
| 10-8 | [voice-werewolf](voice-werewolf/) | 🚧 | Adds a real-LLM user simulator that sees only its seat context, must call tools, and enters only through synthesized audio plus real OpenRouter audio ASR. Strict revalidation rejected two early arms that mistook a bad transcript for abstention; unaffected v2 passes E2E, isolation, rule winner, and three cycles, but fails strategy after a Villager wrongly exiles the Seer. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **In Progress** | Implementation or required acceptance evidence is incomplete; runnable code may exist but is not a full acceptance claim |
