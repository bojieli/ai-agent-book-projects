# Learning Suggestions

← [Back to main README](README.md)

## Core Concept: Agent = LLM + Context + Tools

The core formula of this book is **Agent = LLM + Context + Tools**. Chapter 1 explains the same Agent at three levels: the implementation level is this formula, the intuitive level is "brain + eyes + hands and feet," and the academic level maps onto policy, observation space, and action space.

| Component | Metaphor | Responsibility |
| :--: | :--: | --- |
| 🧠 **LLM** | Brain | Provides understanding, reasoning, and decision-making |
| 👁️ **Context** | Eyes | Everything the Agent can see at each decision point: system prompt, tool definitions, user messages, assistant replies, tool results |
| 🤲 **Tools** | Hands and feet | Perceive the environment, execute actions, interact with the outside world |

For production, Chapter 1 rewrites the same system as **Agent = Model + Harness**, where **Harness = context management + tool interfaces + constraints + verification + correction**. Those last three are exactly the gap between a demo that runs and a product that is reliable.

## Learning Path

The Introduction lays out the overall arc: **Chapters 1–6 build a complete method for constructing an Agent; Chapters 7–10 discuss raising its capability from four directions — evaluation, post-training, continuous evolution, and multi-Agent collaboration.** Each chapter carries one key insight:

| Part | Ch. | Coverage | Key insight |
| --- | :--: | --- | --- |
| **Build** | 1 | The three elements, the ReAct loop, orchestration patterns (workflow vs. autonomy), Harness engineering | The gap between a demo that runs and a reliable product lies in the Harness, not the model |
| | 2 | API message structure, KV Cache, prompt engineering and prompt-injection defense, Agent Skills, the Agent status bar, context compression | The single most important chapter; context sets the capability ceiling, and the more stable the prefix, the higher the cache hit rate |
| | 3 | Four progressive strategies for user memory, the RAG stack, organizing and retrieving knowledge, Agentic RAG, multimodal memory | Extends context from a single session into knowledge that accumulates across sessions |
| | 4 | Five tool categories (perception / execution / collaboration / event-trigger / user-communication), MCP, general design principles, active tool discovery | Perception tools control information volume, execution tools control risk; tool design should be generalized |
| | 5 | Coding Agent plus a file system, the OpenClaw architecture, six directions for code as a meta-capability | Code is not just writing programs — it is the meta-capability to create new tools at runtime |
| | 6 | Two axes, modality × timing: async and event-driven, voice, Computer Use, robot manipulation | All four interaction types share the same system primitives: wake-up, safe points, cancellation, preemption, fast/slow path separation |
| **Improve** | 7 | Evaluation environments, metrics, dataset design, LLM-as-a-Judge, statistical significance, observability, simulation environments | Without evaluation you cannot tell "improvement from design" apart from "random variation" |
| | 8 | The four-stage panorama, mid-training / SFT / RL, reward design, multi-turn credit assignment, distillation | SFT memorizes, RL generalizes; data and environments matter more than algorithms |
| | 9 | Learning signals (environment outcomes / process rules / LLM rubrics), four update carriers — knowledge, instructions, programs, parameters — plus staged rollout and rollback | The update carrier depends on how the capability is expressed and verified |
| | 10 | The classification framework (shared vs. isolated context × peer / manager / decentralized), the A2A protocol, six failure modes, Agent societies | Every multi-Agent design decision has a counterpart in the three elements of a single Agent |

## Prose and experiments

The book is not a step-by-step tutorial for one SDK. Short pseudocode and skeletons in the prose only answer "how state flows, where it can stop, which signals participate in verification"; chapter experiments provide complete implementations, model/environment adapters, tests, logs, and evidence. You do not need to understand every line of every file, and you should not treat one experiment's specific API usage as a general architecture.

Read at the three layers below; for a complex chapter, pick several mechanism experiments at the same layer rather than running only one project:

| Layer | Read first | Skip for now | Question it answers |
| :--: | --- | --- | --- |
| **Starter** | Project README: goal, minimum command, acceptance conditions; matching prose skeleton | credentials, UI, provider adapters, long raw logs | Which mechanism is this experiment meant to demonstrate? |
| **Builder** | entry point, core loop, state/message schema, tools, verifier | compatibility/deployment layers unrelated to the mechanism | Which variable changed the behavior? |
| **Maintainer** | tests, failure handling, evidence format, manifest/hash, rollback path | third-party details needed only when changing the experiment | Can the result be reproduced, and are failures recorded honestly? |

Each chapter README marks its own Starter entry point. The recommended first set is: Ch. 1 `context`, Ch. 2 `context-compression`, Ch. 3 `user-memory`, Ch. 4 `execution-tools`, Ch. 5 `coding-agent`, Ch. 6 `live-audio`, Ch. 7 `tau2-bench-eval`, Ch. 8 `cot-distillation`, Ch. 9 `trajectory-verifier`, Ch. 10 `parallel-web-research`. Each directory's Code map marks Run first, Core behavior, Verifier, and the parts you can skip on a first read.

## Difficulty Levels

| Level | Ch. | Suitable for |
| --- | :--: | --- |
| 🟢 Beginner | 1–2 | Newcomers; only Python basics and experience using an LLM are required |
| 🔵 Intermediate | 3–4 | Some programming background; covers retrieval systems and tool integration |
| 🟣 Advanced | 5–6 | Strong programming skills, complex system design; Ch. 6 assumes familiarity with HTTP/WebSocket |
| 🟡 Engineering | 7 | Evaluation infrastructure and statistical methods — heavy on engineering, light on mathematics |
| 🔴 Expert | 8 | The one chapter in the book that requires machine learning and model-training experience |
| 🟠 Applied | 9–10 | Combines everything above to build continuous-evolution loops and multi-Agent systems |

Experiments and exercises in the prose carry their own star ratings: ★ introductory, suitable for all readers; ★★ moderate, requiring some engineering practice; ★★★ advanced challenges, usually open-ended problems or complex system design.

## Practical Suggestions

| # | Suggestion | Notes |
| :--: | --- | --- |
| 1 | 🛠️ **Hands-on practice** | Every project is designed to run independently; run and modify the code yourself |
| 2 | 📚 **Read alongside the book** | Read the matching chapters in [`book-en/`](../../book-en/) (English) or [`book/`](../../book/) (Chinese original) to connect theory and practice |
| 3 | 🔬 **Compare experiments** | Many projects include ablation studies and comparative experiments; deepen understanding through comparison |
| 4 | 🪜 **Learn progressively** | Start with simple projects and gradually move into complex systems |
| 5 | 🔌 **Watch the protocols** | The MCP tool projects in Chapter 4 demonstrate standardized tool protocols, which are key to building scalable Agents |
