# Learning Suggestions

← [Back to main README](README.md)


### Core Concept: Agent = Model + Context + Tools

The core framework of this book is **Agent = Model + Context + Tools**. These three components collaborate to realize the intelligent behavior of an agent:

- **Model**: The brain of the agent, providing understanding, reasoning, and decision-making capabilities.
- **Context**: The operating system of the agent, containing system instructions, dialogue history, reasoning processes, tool interaction records, etc.
- **Tools**: The hands of the agent, enabling it to perceive the environment, execute actions, and interact with the external world.

### Learning Path

The learning path corresponds chapter by chapter to the entire book, unfolding layer by layer around the three pillars:

- **Chapter 1 · Foundations**: Establish a complete cognitive framework for agent systems—understand the definition of an agent in RL, compare the sample efficiency differences between traditional RL and LLM+RL paradigms, grasp the new paradigm of "model as agent," and master the core framework of **Agent = Model + Context + Tools**. **Key Insight**: The importance of prior knowledge surpasses algorithms and environments.

- **Chapters 2–3 · Context**: Context is the agent's operating system. Chapter 2 covers system prompts, KV Cache-friendly design, context compression, and prompt engineering ablation. Chapter 3 covers user memory, dense/sparse/hybrid retrieval, Agentic RAG, context-aware retrieval, and structured knowledge extraction. **Key Insight**: Complete context includes system instructions, dialogue history, reasoning processes, tool interaction records, user memory, and external knowledge.

- **Chapters 4–5 · Tools**: Tools are the bridge for the agent to interact with the world. Chapter 4 covers three types of MCP tools (perception/execution/collaboration), event triggering, and asynchronous architecture. Chapter 5 delves into the complete implementation of a production-grade Coding Agent. **Key Insight**: Tool design should be generalized (a code interpreter is better than a calculator); code is the meta-ability to create new tools.

- **Chapters 6–7 · Model**: How to measure and amplify intelligence. Chapter 6 covers evaluation benchmarks like Terminal-Bench, SWE-bench, GAIA, OSWorld, and Tau2-Bench. Chapter 7 covers post-training techniques like SFT, RL, RLHF, and sample efficiency. **Key Insight**: An independent verification signal is more reliable than "asking the model to think again"; "model as agent" internalizes tool calls as native capabilities through RL.

- **Chapter 8 · Self-Evolution**: Enable agents to grow from experience without changing weights—experience learning, externalizing workflows as tools, distilling prompts and observations into parameters. **Key Insight**: Learning from experience is the key for an agent to move from being "smart" to being "skilled."

- **Chapters 9–10 · Expansion and Collaboration**: Chapter 9 expands perception and action from text to speech, GUI, and the physical world. Chapter 10 uses multi-agent division of labor to handle complex tasks. **Key Insight**: Every design decision in a multi-agent system can find its counterpart in the three elements of a single agent.

## Prose and experiments

The book is not a step-by-step tutorial for one SDK. Short pseudocode and skeletons explain state flow, stopping points, and verification boundaries; chapter experiments contain complete implementations, model/environment adapters, tests, logs, and evidence.

| Layer | Read first | Skip for now | Question it answers |
| :--: | --- | --- | --- |
| **Starter** | Project README: goal, minimum command, acceptance conditions; matching prose skeleton | credentials, UI, provider adapters, long raw logs | Which mechanism is this experiment meant to demonstrate? |
| **Builder** | entry point, core loop, state/message schema, tools, verifier | compatibility/deployment layers unrelated to the mechanism | Which variable changed the behavior? |
| **Maintainer** | tests, failure handling, evidence format, manifest/hash, rollback path | third-party details needed only when changing the experiment | Can the result be reproduced, and are failures recorded honestly? |

### Difficulty Levels

- **Beginner** (Chapters 1–2): Suitable for beginners, understanding basic concepts.
- **Intermediate** (Chapters 3–4): Requires some programming foundation, involves system integration.
- **Advanced** (Chapters 5–6): Requires strong programming skills, involves complex system design.
- **Expert** (Chapters 7–8): Requires deep learning and training/self-evolution experience.
- **Application** (Chapters 9–10): Comprehensive application of previous knowledge to build practical applications.

### Practical Suggestions

1.  **Hands-on Practice**: Each project is designed to be run independently. It is recommended to run and modify the code yourself.
2.  **Combine with the Book**: Read the corresponding chapters in the manuscript in the [`book-en/`](../../book-en/) directory (English) or [`book/`](../../book/) directory (Chinese original) of this repository to understand the combination of theory and practice.
3.  **Experimental Comparison**: Many projects include ablation studies and comparative experiments. Deepen understanding through comparison.
4.  **Progressive Learning**: Start with simple projects and gradually delve into complex systems.
5.  **Focus on Protocols**: The MCP server project in Chapter 4 demonstrates standardized tool protocols, which are key to building scalable agents.
