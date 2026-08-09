# Chapter 10 · Multi-Agent Collaboration

> Collective intelligence can surpass individual intelligence. Multi-Agent classification framework, when it truly outperforms a single Agent, collaboration with and without shared context, failure modes, and the emergent "Agent Society."

← [Back to main README](../docs/en/README.md) · 📖 [Read chapter text](../book-en/chapter10.md)

## Companion Projects

| Exp. | Project | Type | Description |
| :--: | --- | :--: | --- |
| 10-1 | [multi-role-transfer](multi-role-transfer/) | 🚧 | Compares `transfer_to_agent` (dynamic system-prompt/tool isolation) with fixed-prefix `load_skill` on the same shared trajectory. The runner evaluates cost, cache behavior, actual task effects and boundary instruction following, including an eight-task complex rule suite; historical Kimi/Tavily receipts remain evidence for the transfer arm only. |
| 10-2 | [book-translation](book-translation/) | ✅ | The formal 26-unit dual-arm run translates an illustrated, code-heavy technical-book sample and passes all 12 gates, including quality, context, token, latency, resource, checkpoint, receipt, and provenance comparisons. |
| 10-3 | [TalkAct reproduction record](talkact-reproduction/) + `use-computer-while-calling/` + [autonomous-phone-registration](autonomous-phone-registration/) | 📖 / ✅ | The retained 16/16-episode Anthropic-caller campaign passes all 17 gates. Both arms achieved 1.0 task success; duplex reduced median voice latency from 12.52 s to 2.32 s (5.40×), while the control had higher probe correctness and lower mean wall time. Because the Gemini credential was invalid, this run used TalkAct's supported Anthropic Sonnet caller override and must not be silently pooled with default-Gemini upstream results. A real LLM autonomously selected the Phone Agent, and the formal run passed all 9 gates over Playwright, bidirectional WebRTC/RTP, local TTS/Whisper, validation and re-asking, concurrent ask/fill, privacy, and one authorized localhost submission. The manuscript does not require PSTN/E.164. |
| 10-4 | [parallel-web-research](parallel-web-research/) | ✅ | N independent Playwright browser sessions search ten real university sites while a real LLM extracts cited evidence. Saved acceptance covers monitoring, timeout/error isolation, single settlement, cascading termination acknowledgements, resource cleanup, and a measured 3.142× same-site parallel speedup. |
| 10-5 | `generative_agents/` | 📖 | Stanford's "AI town" generative agents (companion to Experiment 10-5); external repository `joonspk-research/generative_agents`, which you need to clone yourself (see the main README appendix). |
| 10-6 | [voice-werewolf](voice-werewolf/) | 🚧 | Adds a real-LLM user simulator that sees only its seat context, must call tools, and enters only through synthesized audio plus real OpenRouter audio ASR. Strict revalidation rejected two early arms that mistook a bad transcript for abstention; unaffected v2 passes E2E, isolation, rule winner, and three cycles, but fails strategy after a Villager wrongly exiles the Seer. |
## Project Types

| Icon | Type | Meaning |
| :--: | --- | --- |
| ✅ | **Standalone** | Full code in this repo, runs after configuring API Key |
| 📖 | **Reproduction Guide** | Detailed doc depending on **external repos** to `git clone` |
| 🚧 | **In Progress** | Implementation or required acceptance evidence is incomplete; runnable code may exist but is not a full acceptance claim |
