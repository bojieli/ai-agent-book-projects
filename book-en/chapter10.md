# Multi-Agent Collaboration

The first nine chapters focused on a single Agent: first building its context, knowledge, tools, and interaction capabilities, then using evaluation, post-training, and continual evolution to improve it over time. This chapter advances the question from “How do we build and improve one Agent?” to “How do we organize multiple Agents?”—so that division of labor, communication, and mutual verification can tackle tasks that are difficult for one Agent to carry alone.

OpenAI once proposed a five-level scale of AI capabilities: Level 1, Conversationalists; Level 2, Reasoners; Level 3, Agents; Level 4, Innovators; and Level 5, Organizations. Multi-agent collaboration is often presented as one path to Level 5. Here, however, "Organizations" denotes a capability level—AI that can do the work of an entire organization—rather than an architectural requirement. A sufficiently powerful single Agent could, in principle, reach it as well. In today's engineering reality, however, a single Agent remains constrained by its model's capabilities and context window.

Getting multiple Agents to work together is about far more than letting specialists with different expertise "cover each other's gaps." The more fundamental point is this: **the intelligence of a group can exceed that of any individual.** Human civilization is the proof—one person's intellect is limited, yet through division of labor, collaboration, debate, and the accumulation of knowledge across generations, human society as a whole exhibits intelligence far beyond any single genius. Agent groups may give rise to the same kind of collective intelligence: even if each Agent is only as capable as a human expert, a well-organized group could surpass the combined capabilities of all human experts. In *From AGI to ASI*, Google DeepMind lists "large-scale multi-agent collectives" as a key pathway toward superintelligence (ASI)—just as human general intelligence aggregates into societies and organizations that transcend individuals, the collective intelligence of many AGI-level Agents working together may exhibit cognitive capabilities far beyond the simple sum of its members[^agi-asi]. Multi-agent collaboration, then, is not merely an engineering workaround for a single model's context window and capability limits—it may be a fundamental path from "expert-level AI" toward "surpassing humanity as a whole."

[^agi-asi]: On "large-scale multi-agent collectives" as a key pathway from AGI to ASI, see Google DeepMind, *From AGI to ASI.* arXiv:2606.12683, 2026.

## A Classification Framework for Multi-Agent Collaboration

Building a multi-agent system starts with two core design dimensions, which together determine its basic architecture and implementation.

### Dimension 1: Shared vs. Non-Shared Context

This is the most fundamental architectural decision, determining how information is passed between multiple Agents.

**Shared context** means that a subsequent Agent receives the complete conversation history and trajectory (as defined in Chapter 1) of the preceding Agent. When the system prompt and tool set change at each stage, the system treats the new stage as a different Agent because its identity, responsibilities, and capabilities have changed, even though it retains all the memory of its predecessor. For example, after a requirements analyst writes a requirements document, the developer receives not only the document but also the full record of communication between the analyst and the user. The developer assumes a new role while retaining all prior context. The advantage is that no information is lost; each Agent can review details from any previous stage. The challenge is that the context can expand rapidly.

**Non-shared context** means that each Agent maintains an independent context and conversation history and cannot directly access the other Agents' work traces. This is like collaboration between different departments: everyone works independently at their own desk, exchanging information through shared documents and meeting minutes rather than constantly watching each other's screens. This model offers better modularity and isolation; each Agent only needs to focus on information relevant to its own responsibilities. The system is also easier to extend and maintain—adding a new Agent does not require modifying the internal logic of existing Agents, only defining interfaces and data formats.

Since Agents do not share context, information must be passed through explicit communication mechanisms. Classic distributed systems settled this question long ago: operating-systems textbooks tell us that inter-process communication (IPC) ultimately comes in just two paradigms—**shared memory** (one side writes and the other reads the same block of storage) and **message passing** (data is explicitly sent to the other side). Communication mechanisms between Agents fall within these same two paradigms. There are three common methods:

- **Tool call parameters**: Wrap the downstream Agent as a tool, then pass structured data through its parameters; this is suitable for scenarios requiring well-typed, clearly structured data.
- **Shared file system**: Agents exchange information by reading and writing intermediate artifacts (documents, code, etc.) in a shared directory, suitable for scenarios with large artifacts or where persistence is needed.
- **Message bus**: A dedicated intermediary that passes messages between Agents. Agents do not call each other directly but send messages to the bus, which forwards them to the target Agent.

Mapped onto the two IPC paradigms, the shared file system corresponds to "shared memory," while tool call parameters and the message bus are forms of "message passing." Tool parameters are delivered synchronously with a call; messages on a bus are delivered asynchronously through an intermediary. Each paradigm has its trade-offs. Go has a widely quoted maxim: "Do not communicate by sharing memory; instead, share memory by communicating."

The message bus naturally supports **asynchronous communication**—the sender and receiver do not need to be online simultaneously. This is like an internal company email system: when you email a colleague, you don't need them to be at their computer at that moment; the email is stored on the server and processed when the colleague comes online. This approach is particularly suitable for scenarios where multiple Agents work in parallel and need to coordinate with each other (see the "Parallel Coordination" section later in this chapter).

![Figure 10-1: Shared Context vs. Non-Shared Context](images/fig10-1.svg)

To be clear, both architectures are genuine multi-agent systems because the system prompt and tool set differ at each stage, making them different Agents. The difference lies in the coordination method. **Shared context** relies on implicit coordination: subsequent Agents inherit the complete context history of preceding Agents, can review their visible interaction histories and work traces, and receive information through the context itself. **Non-shared context** relies on explicit coordination: Agents exchange information through files, messages, or structured data interfaces, and each Agent sees only the content relevant to its own work.

By analogy: the former is a team around one table, where everyone hears everything; the latter is departments collaborating by email and documents, each with its own workspace.

Readers familiar with operating systems may find a useful analogy: shared-context Agents resemble threads, while non-shared-context Agents resemble processes. Threads share an address space, which makes switching and communication inexpensive but provides little isolation; memory corruption in one thread can crash the entire process. Each process has its own address space, providing stronger isolation and safer parallelism, but communication must use explicit IPC.

**Simple rule of thumb**: If the expected cumulative context exceeds 50% of the window (a heuristic, not an exact threshold), don't share. If zero information loss is a hard requirement for task correctness, share. Most real-world systems use different approaches at different stages: the first few Agents share context, but once the shared history becomes too large, the system switches to non-shared contexts and uses an explicit handoff in which the upstream Agent selects what to pass downstream.

### Dimension 2: Collaboration Topology

The second dimension is collaboration topology: the structure through which control and information flow among Agents. Topology and context sharing are conceptually distinct but related in practice. Shared-context systems still have a topology; for example, the `transfer_to_agent` pattern in Experiment 10-1 forms a handoff chain. However, because every handoff carries the complete history, there is usually no need to decide what information to pass, so the topology often becomes a simple sequence of role switches. Group-chat-style collaboration is an exception discussed later in the decentralization section. With non-shared context, by contrast, designers must explicitly decide how information flows and who coordinates it.

> **Terminology: Graph Engineering.** The term "Graph Engineering," which became popular in July 2026, generally refers in today's Agent context to explicitly designing an execution graph: nodes are Agents, ordinary programs, or human decisions; edges define task dependencies, conditional routing, and failure paths; and structured state flows between nodes.[^ch10-graph-engineering] The "collaboration topology" discussed in this chapter is the multi-agent subset of that idea—peer collaboration, manager orchestration, and decentralized handoffs are different graph topologies. Because the name is still new and is easily confused with knowledge graphs, GraphRAG, and execution traces, this book continues to use the more stable terms "collaboration topology" and "orchestration" as its primary vocabulary.

[^ch10-graph-engineering]: For an early discussion of the name, see Josh C. Simmons, *We Are Entering the Graph Engineering Phase*, 2026. Mainstream frameworks generally call the same engineering structure a graph-based workflow or orchestration rather than a wholly new technology. See https://www.drjoshcsimmons.com/writing/we-are-entering-the-graph-engineering-phase, https://docs.langchain.com/oss/python/langgraph/overview, https://learn.microsoft.com/en-us/agent-framework/workflows/, and https://adk.dev/workflows/.

In other words, the two dimensions form, in principle, a 2×3 matrix (shared/non-shared × three topologies)—but in the shared-context row, the topology mostly degenerates into a sequence of role switches with little left to decide (the form discussed later in "Multi-Stage Role Switching"). This chapter therefore elaborates only on the three non-shared cells. Here are the three typical topologies under non-shared context, in order of increasing complexity:

- **Peer Collaboration Pattern**: A small number of Agents (typically 2-3) interact as equals, forming an iterative improvement loop—like writing a paper where one person drafts it and another annotates and revises it, with the quality after several rounds far exceeding what one person could achieve alone.
- **Manager Pattern** (Orchestration Pattern): A centralized Manager Agent is responsible for task planning and scheduling, while multiple sub-agents each handle specific subtasks—like a project manager leading several specialized engineers on a project.
- **Decentralized Pattern**: There is no runtime central controller; Agents communicate with each other like humans to collaborate on tasks.

The detailed design and applicable scenarios for each pattern will be discussed in dedicated subsections later.

## When Is Multi-Agent Truly Better Than a Single Agent?

Before diving into specific collaboration architectures, let's answer a more fundamental question: **When are multiple Agents truly needed, and when is one enough?** The answer will serve as a reference point for every engineering approach that follows. A series of recent studies converges on a clear framework—and the core criterion is a single question: **Does the collaboration provide information that a single Agent could not obtain while producing its answer?**

Table 10-1 shows which collaboration modes introduce new information and helps assess whether multi-agent collaboration offers substantive value over a single Agent.

Table 10-1 Information Gain Comparison of Multi-Agent Collaboration Modes

| Collaboration Mode | Introduces New Information? | Effect |
|---------------------------------------|---------------------|-----------------------------------|
| Self-review by the same model (re-reading its own output) | No | Usually ineffective or even harmful |
| Different Agents debating the same text | No | Comparable to a single Agent with equal compute |
| Reviewer uses test execution results to review code | Yes (execution feedback) | Significant improvement |
| Reviewer uses rendered screenshots to review frontend/PPT code | Yes (visual feedback) | Significant improvement |
| Reviewer uses external tools to verify facts | Yes (tool feedback) | Significant improvement |

The 2025 RLEF paper (Reinforcement Learning from Execution Feedback)[^rlef-2025] found that training a model via reinforcement learning to use code-execution feedback for iterative improvement significantly outperformed independently sampling the model multiple times. The key is that each iteration introduces **real execution results** (compilation errors, test failures, runtime exceptions)—information that did not exist when the model wrote the code. For webpage-generation tasks, the 2025 WebGen-Agent study[^webgen-agent-2025] reported that multi-level visual feedback, combining screenshots with vision-language-model descriptions, improved Claude 3.5 Sonnet's benchmark performance from 26.4% to 51.9%, nearly doubling it.

[^rlef-2025]: Gehring, J., et al. *RLEF: Grounding Code LLMs in Execution Feedback with Reinforcement Learning.* arXiv:2410.02089, 2025.
[^webgen-agent-2025]: Lu, Z., et al. *WebGen-Agent: Enhancing Interactive Website Generation with Multi-Level Feedback and Step-Level Reinforcement Learning.* arXiv:2509.22644, 2025.

This framework helps resolve an apparent contradiction: some academic studies find that a single Agent is sufficient, while multi-agent systems often perform better in engineering practice. The studies often test multiple Agents that inspect and discuss the same text, as in debate, whereas effective engineering systems commonly add external feedback from code execution, visual rendering, or tools. Only the latter introduces new information. Nearly all effective uses of the three architectures discussed later—peer collaboration, orchestration, and decentralization—can be understood through this criterion.

Anthropic's 2026 vulnerability-discovery experiment provides one example. Forty-five Agents coordinated their searches through a shared forum, reviewed one another's findings, and submitted results to a separate arbiter Agent. The coordinated swarm found 266 vulnerabilities using 27 million tokens, while independently parallel Agents found only 21 using 6.5 million tokens. In an open search space, communication lets a multi-agent system shift its attention dynamically and develop specializations, trading a larger token budget for broader coverage and more varied discovery paths.[^anthropic-multiagent-2026]

[^anthropic-multiagent-2026]: Anthropic Frontier Red Team, “Patterns and Problems in Emerging Multiagent Systems,” 2026-08-13. https://www.anthropic.com/research/multiagent-systems

**Step Budget and Agent Performance.** A related question is how an Agent's step budget—the number of tool calls or iteration rounds it may use—affects performance. More steps might seem certain to help: with 30 steps, an Agent may have time only to implement core functionality, whereas 300 steps allow it to plan, implement, test, and refine. However, the 2025 Google paper *Budget-Aware Tool-Use Enables Effective Agent Scaling* reached a counterintuitive conclusion: **simply giving an Agent more steps does not guarantee better performance.** Standard Agents lack "budget awareness"; even with 300 steps, they tend to conduct shallow searches and quickly reach a plateau. To use additional steps effectively, Agents need a mechanism that adapts their strategy to the remaining resources, exploring broadly at first and narrowing their focus later. The 2026 BAVT (Budget-Aware Value Tree Search) approach further introduced step-level value evaluation, adjusting the balance between exploration and exploitation according to the proportion of the budget remaining. As the budget decreases, the Agent shifts from broad exploration to deeper investigation.

These findings have direct implications for multi-agent system design. For example, in the orchestration pattern, the Manager Agent should not simply distribute tasks to sub-agents and wait for results. Instead, it should **dynamically allocate step budgets** based on task complexity—simple subtasks get fewer steps; complex subtasks get ample steps. It should also guide sub-agents to use these budgets wisely (plan first, then implement, then test, then improve), rather than diving straight in.

One more consideration must come before any design decision: **cost.** Parallel exploration and iterative refinement cost money—Anthropic has disclosed that its multi-agent research system consumes about 15 times the tokens of a normal conversation, and that token usage alone explains about 80% of the performance difference. The gains from a multi-agent system must therefore be large enough to justify costs that may be several times, or even an order of magnitude, higher; otherwise, a well-tuned single Agent is usually the better bargain.

## Multi-Agent Collaboration with Shared Context

In multi-agent collaboration with shared context, each stage is an independent Agent (with its own system prompt and tool set), but it inherits the complete trajectory of the preceding Agent—much like a colleague taking over a shift who can leaf through every work log the predecessor left behind. The core advantage of this inheritance-based collaboration is zero information loss: every Agent can review details from any previous stage. The challenge is keeping the current Agent focused on its own responsibilities rather than distracted by the mass of inherited history.

In complex tasks, an Agent's role and responsibilities may change significantly across stages. If a single static system prompt is used throughout, it will either be too general or become an unwieldy collection of instructions. Multi-stage role switching changes the system prompt and tool set according to the current stage, allowing the Agent to work in the most appropriate role.

The key architectural choice is whether role guidance is carried by a replacement system prompt or by a loaded Skill. The former can enforce a hard tool boundary, but changes the request prefix at every switch. The latter keeps the static prefix stable and appends `SKILL.md` to the trajectory, which is usually friendlier to KV/prompt caching; a Skill remains behavioral guidance, so sensitive or side-effectful tools still require a code-enforced Harness policy gate.

| Choice | Role guidance | Tool visibility | Context/KV-cache effect | Constraint strength |
|---|---|---|---|---|
| `transfer_to_agent` | Replace the system prompt and usually the tool set | Only the current role's tools | Each switch changes the request prefix and usually invalidates caching from that point | Strong: out-of-scope tools can be absent from the schema |
| Skill | Keep a Skill directory in the fixed prompt and append `SKILL.md` on demand | Usually the full catalog, or a stable search entry point | The static prefix stays stable; Skill text is appended to the trajectory | Weak: a Skill is an instruction, not a permission boundary |

> **Experiment 10-1 ★★: Shared-context role switching—system prompt versus Skill**
>
> Both paths use the same model, task, tools, role guidance and complete shared trajectory. The task is to find China's 2021–2023 new-energy vehicle sales, calculate CAGR, and write a Chinese investor summary of no more than 120 characters.
>
> **Path 1: system-prompt switching.** Five roles—`triage`, `research`, `coding`, `data_analysis` and `writing`—each expose only their dedicated tools plus `transfer_to_agent`. A handoff saves history, loads the target prompt and tool set, and resumes execution.
>
> **Path 2: Skill.** The system prompt and full tool catalog remain fixed. The model calls `load_skill(name)` and receives the same role document as a tool result in the shared trajectory. The static prefix remains unchanged, but hard permissions are enforced by Harness rules.
>
> The two paths should perform the same retrieval, calculation and length check. They differ in the carrier of role guidance and in the resulting tool boundary; a smoke trace alone cannot establish which path is superior.


## Multi-Agent Collaboration Without Shared Context

In an architecture without shared context, each Agent operates as an independent entity with its own context, trajectory, and state. Agents cannot directly access one another's internal context; collaboration relies entirely on explicit, structured data transfers through the three communication mechanisms introduced at the beginning of this chapter: tool call parameters, a shared file system, and a message bus.

Earlier in this chapter, we compared the communication mechanisms to forms of inter-process communication and shared versus isolated context to threads versus processes. This analogy can be extended further (Table 10-2):

Table 10-2 Correspondence Between Multi-Agent Systems and Operating Systems

| Operating System | Multi-Agent System |
|----------|----------------|
| Program (executable file) | Static prefix (system prompt + tool definitions) |
| Process memory | Trajectory |
| CPU | LLM |
| Kernel | Agent runtime |
| System call | Tool call |
| fork (create child process) | spawn_subagent |
| kill (send signal) | cancel_subagent |
| ps (list processes) | list_agents |
| Exit code and wait() | Structured summary returned by the sub-agent |
| Shared memory / message passing | Shared file system / message passing |

This abstraction is nothing new: private state, asynchronous messages, and the ability to create new members are precisely the basic setup of the 1970s Actor model[^actor-model]. A multi-agent system can therefore be viewed as an LLM-based version of the Actor model, and much of the accumulated knowledge from operating systems and distributed systems applies directly.

[^actor-model]: Hewitt, C., Bishop, P., Steiger, R. *A Universal Modular ACTOR Formalism for Artificial Intelligence.* IJCAI 1973.

This process-style isolation brings several practical engineering benefits: each Agent can be developed and tested independently, new capabilities can be added without touching existing code, and multiple Agents can execute concurrently without contention over shared context.

However, not sharing context also has costs. The most obvious is the information synchronization problem: how do Agents maintain a consistent understanding of the task state? Will information be lost or duplicated during transfer? Debugging also becomes more difficult—when problems arise, logs from multiple Agents must be reviewed to piece together the complete execution process. These issues make the design of interface specifications, data formats, and communication protocols critically important.

Explicit collaboration without shared context relies on two topology-independent infrastructures. The first is the **shared file system**, the persistent medium through which Agents exchange artifacts with one another and with the user, forming the data plane of collaboration. The second is the **communication and control mechanism**, which supports message passing, status queries, execution termination, and resource scheduling between Agents, forming the control plane of collaboration. The three topologies below are all built on these two foundations.

### The File System from an Agent's Perspective

At the beginning of this chapter, the "shared file system" was listed as one of the three communication mechanisms for architectures without shared context. In a real system, the file system an Agent accesses is not a single storage system but a **virtual file system** in which storage systems with different sources, lifecycles, and permissions are mounted under one directory tree. The Agent accesses them through unified `read_file`/`write_file`/`list_dir` interfaces, while the underlying layers may be local temporary disks, persistent object storage, third-party cloud drive APIs, or read-only system resource packages. Clearly defining the composition of this directory tree—the visibility and lifecycle of each area—is a prerequisite for designing multi-agent collaboration: a significant portion of concurrency conflicts and information leaks stem from mixing areas that should be isolated. This directory tree amounts to the Agent's address space, and the four types of areas are memory segments with different permissions: some private and writable, some shared among multiple parties, and some read-only. The operating system's protection philosophy applies here as well: isolate by default and declare sharing explicitly. In a mature multi-agent system, the file system typically consists of the following four types of areas:

**I. Agent-Specific Workspace (Scratchpad)**. A private directory exclusive to each Agent instance, storing intermediate artifacts, temporary files, drafts, and debug logs. Its lifecycle is tied to the instance and is invisible to other Agents and users. Isolating the scratchpad serves two purposes: preventing temporary files from multiple Agents from overwriting each other, and keeping the main Agent's context lean—the trial-and-error process of sub-agents remains in their own workspace, with only the final artifact submitted to the shared space. This is the storage-level counterpart of Chapter 4's principle that sub-agents return structured summaries rather than full trajectories.

**II. Multi-Agent Shared Workspace**. A collaboration area that multiple Agents can read and write, and that is **visible to the user**. It is the primary medium for exchanging artifacts between Agents in architectures without shared context: the Glossary Agent writes the term list, and the Translation Agent reads from it; users can also upload source files and download final deliverables here. Its lifecycle is tied to the entire task and requires persistence. As an area for concurrent reads and writes by multiple parties, it is a hotspot for concurrency conflicts—mechanisms such as optimistic locking and worktree isolation operate here, as detailed under "Failure Mode One" later in this chapter. Chapter 4's use of a volume mount at `/workspace/shared` to connect the main Agent, virtual computer, and virtual phone is a typical implementation of this layer.

**III. Mounted External Resources.** Third-party information sources authorized by the user—Google Drive, Notion, Dropbox, enterprise wikis, etc.—are mapped to mount points in the file system (e.g., `/mnt/gdrive`) via adapters. An Agent accesses a Notion document by reading a file; the underlying adapter calls the corresponding API. Three characteristics distinguish this layer from local storage and must be explicitly handled during design: **access is constrained by external permissions** (the user's permissions in the source system determine the Agent's visibility), **latency is higher and consistency is weaker** (each read involves a network round trip, and external changes may not be immediately visible, so the data should be treated as eventually consistent), and **access is primarily on-demand and read-only** (writing back to external sources must be done cautiously, as erroneous writes could contaminate the user's real data). The unified file interface means the Agent does not need a custom tool for each data source, but it also masks these performance and security differences. Therefore, read-only/writable status, timeouts, and credential boundaries must be explicitly managed at the mount level.

**IV. Built-in System Resources.** A resource package pre-installed by the system and shared read-only with all Agents. Typical examples are the **Skills** introduced in Chapters 2 and 4—knowledge documents and scripts organized as files, mounted at paths like `/skills`, accessed via progressive disclosure (index first, then expand on demand). Other examples include reference manuals, template libraries, and shared tool definitions. This layer is globally shared, read-only, stable across sessions, and can be read concurrently by all Agents without concurrency control.

Figure 10-2 illustrates how these four area types are uniformly mounted under a single directory tree: the Agent accesses the entire tree through a unified interface, users upload and download files from the shared space, external data sources are mounted via adapters, and built-in system resources are provided read-only.

![Figure 10-2: Mounting structure of the four area types in the Agent Virtual File System](images/fig10-2.svg)

Table 10-3 compares these four area types across four dimensions—visibility, lifecycle, read/write permissions, and concurrency control—serving as a checklist for file system layout design.

Table 10-3 Four area types of the Agent Virtual File System

| Area | Visibility | Lifecycle | Read/Write | Concurrency Control |
|--------------|-----------------|------------------------|---------------------|-------------------|
| Agent-Specific Workspace | The owning Agent only | Destroyed with the Agent instance | Read/Write | Not needed (private) |
| Multi-Agent Shared Workspace | All collaborating Agents and the user | Persists for the task duration | Read/Write | Required (optimistic lock / worktree) |
| Mounted External Resources | Depends on external authorization | Determined by the external source | Mostly read-only, writes require caution | Managed by the external source |
| Built-in System Resources | All Agents | Stable across sessions | Read-only | Not needed (read-only) |

The value of the **"file path as a universal interface"** lies in treating a path as the unit of exchange. Whether Agents exchange artifacts, a main Agent hands input to a sub-agent, or organizations collaborate through A2A, they pass a lightweight path string rather than loading the file's contents into the context window (Chapter 4). This aligns with Chapter 5's concept of "the file system as the Agent's hub," which describes how a single Agent uses the file system to host memory and capabilities. Here, the same abstraction extends to multiple Agents: a virtual directory tree mounting private, shared, external, and built-in storage provides the storage foundation for multi-agent collaboration.

### Communication and Control Between Agents

While the file system solves the problem of **artifact exchange** between Agents, collaboration also requires a **control plane**. This is exactly where the lifecycle rows of Table 10-2 come into play: the tool primitives given in Chapter 4—creating (`spawn_subagent`), sending messages (`send_message_to_subagent`), canceling (`cancel_subagent`), and discovering (`list_agents`)—correspond to fork, message, kill, and ps in the process world. This section does not repeat the interface definitions but focuses on four often-overlooked capabilities essential for multi-agent collaboration.

**I. Message Passing.** The simplest form is point-to-point: Agent A directly calls `send_message_to_agent_b(content)`. This is suitable for scenarios with a fixed topology and a small number of Agents (e.g., the phone + computer dual-agent setup of Experiment 10-3 in this chapter). When the number of Agents increases and asynchronous parallelism is required, the number of point-to-point connections grows quadratically with the number of Agents, and both sender and receiver must be online simultaneously. In such cases, a **message bus** should be used (detailed later in this chapter under "Parallel Coordination Pattern"): Agents publish messages to the bus, which forwards them based on subscriptions, so the sender does not need to know the subscribers. Whether point-to-point or via a bus, messages should typically carry a structured **envelope**: sender ID, target (specific Agent or broadcast), message type (e.g., `task_assigned`/`status_update`/`result`/`terminate`), and a JSON payload. A unified envelope format ensures reliable routing and parsing by the receiver and makes the collaboration chain traceable—a key aspect of debugging multi-agent systems.

**II. Status Query.** This is the most underestimated part of the control plane. Once a main Agent has dispatched a sub-agent, it needs visibility into the sub-agent's progress; otherwise, it can neither decide whether to keep waiting nor intervene when the sub-agent gets stuck. An intuitive approach is to borrow from RPC and define a `get_subagent_status(agent_id)` query interface that returns "running/completed/failed" plus a progress percentage. But such a pull interface turns out to be far less useful than expected: a sub-agent starts executing the moment it is created and runs until it completes or fails. It does not cycle through a series of queued states the way jobs in a traditional batch system do, just as Unix programming rarely needs to poll another process by its PID for running status. Polling also carries an inherent dilemma: poll too often and you waste tokens; poll too rarely and you react late. A more natural way to obtain status is to return to the two communication paradigms introduced at the beginning of this chapter.

**Getting status via message passing.** The main Agent simply sends the sub-agent a message: "How's it going?" The sub-agent replies at an opportune moment. Everything is asynchronous: sending the message does not block the main Agent's own execution, and when—or whether—the other side replies is a separate matter, just as a manager asks a subordinate for progress via instant messaging without requiring them to drop everything on the spot. Conversely, the sub-agent can also proactively send a message to report when it reaches a milestone; if the system already has a message bus, this is simply publishing a `status_update` to the bus (the "real-time monitoring" of Experiment 10-4 is this form). Whether status is requested explicitly or reported proactively, the status carried in the message should adopt a uniform state-machine vocabulary (executing, needs input, completed, failed)—the A2A protocol later in this chapter standardizes the task lifecycle into exactly such a set of states.

**Getting status via the shared file system.** The most thorough form is **trajectory persistence**: as it executes, the sub-agent serializes each trajectory event to JSON and appends it to a filesystem log file—usually one file per session, one event per line, i.e., JSONL. The trajectory, defined in Chapter 1, is the complete sequence of user messages, model replies, tool calls, and results. The main Agent needs no status-reporting protocol; by reading this file directly, it can inspect the sub-agent's entire execution: which tool it is calling, what happened in its most recent step, and whether it is stuck in a loop of repeated failed retries. In process terms, this resembles reading another process's memory directly. It does not occupy the sub-agent's context, does not depend on its cooperation, and offers the finest observation granularity.

Such exhaustive detail is also a burden. A trajectory can easily run to tens of thousands of tokens, and the main Agent must distill it after reading, consuming both time and tokens. In most scenarios, an **agreed-upon progress file** is more practical: when starting the sub-agent, the main Agent instructs it to update `progress.md` as it completes each item. The main Agent can read this lightweight file at any time to gauge progress. This resembles two processes reserving a small block of shared memory with an agreed format, exposing distilled progress rather than the entire memory state.

The progress file also enables **stuck detection**. If the last-modified time of `progress.md` or the trajectory file has not changed for more than N minutes, the system can treat the sub-agent as inactive and trigger a timeout safety net (echoing the Heartbeat and `monitor_shell` mechanisms from Chapter 6). This prevents a stalled sub-agent from dragging down the entire system.

The value of trajectory persistence goes well beyond monitoring. Recall the conclusion of Chapter 1: "an Agent's context = static prefix + trajectory." The static prefix (system prompt and tool definitions) is determined by code, while the trajectory records the model-visible conversation state. If tool and session state can be reconstructed from the trajectory or saved in separate checkpoints, and working artifacts are written atomically to the file system, reloading the trajectory and prepending the static prefix can resume execution from the last confirmed state. Even read-only tools may carry volatile state such as browser sessions or page cursors, so they need separate recovery contracts.

However, **the trajectory alone cannot always recover the full state of external systems**. For tools with external side effects—payments, bookings, or message delivery—the process may crash after the operation succeeds but before the result is logged. Before the call, persist a client-generated operation ID, an idempotency key, and the normalized request. Deduplication and status lookup are separate external contracts: an idempotent retry must use exactly the same request and key for the same logical operation, and deduplication can be trusted only within the server's documented key-retention window. Status lookup may instead be supported through the idempotency key or a transaction or job ID returned by the external system. After a response arrives, record that external ID and result. On recovery, query the real state first and classify the outcome as succeeded, failed, or unknown. Retry an unknown result with the same key only when the original request is unchanged and the external system still guarantees deduplication; otherwise escalate to manual reconciliation rather than repeating the action automatically.

With those conditions, persistence resembles a database write-ahead log (WAL): append events before applying them and combine the log with periodic checkpoints. The system can then restart a sub-agent from its last confirmed state, replay events to diagnose failures, or hand auditable state to another Agent (Chapter 3's "fact log + periodic checkpoint" memory design applies the same idea to memory systems).

**III. Execution Termination.** In parallel collaboration, a common scenario is "one succeeds, the rest become irrelevant"—multiple Agents search separately, and once one finds the target, the others should stop immediately (the cascading termination in Experiment 10-4 of this chapter). There are two levels of termination, and Unix users will recognize them as the distinction between SIGTERM and SIGKILL. **Graceful termination** is preferred: the main Agent sends a `terminate` signal, the sub-agent responds at a safe point in its current step, cleans up resources (closes browser sessions, writes pending files, releases locks), sends an acknowledgment (ack), and then exits. **Forced termination** is a fallback: directly terminating the process, used only when the sub-agent does not respond to the graceful signal, at the cost of potentially leaving dangling resources and incomplete writes. Two engineering points need attention. First, graceful termination requires the sub-agent to check periodically for the termination signal in its loop (similar to the interrupt mechanism in Chapter 6); otherwise, it cannot receive the signal. Second, cascading termination has a race condition: multiple sub-agents might report success nearly simultaneously. The main Agent must use a lock or idempotent design to ensure that only one success is accepted and that the termination signal is broadcast once. See the discussion of race conditions in Experiment 10-4.

One loose end remains: after the main Agent terminates, what happens to sub-agents still running? The cleanest engineering approach borrows from Go's context—termination cascades down the creation relationship: cancel one Agent and all the sub-agents it spawned are canceled with it, preventing orphaned child Agents from being left behind. The "sub-agent checks for the termination signal at a safe point" above corresponds precisely to polling `ctx.Done()` in Go. Conversely, if you genuinely need a long-running background Agent detached from the main Agent (like Unix's `nohup`), let it start from a new lifecycle tree (corresponding to `context.Background()`), explicitly declaring that it does not terminate with its parent.

**IV. Resource Management and Scheduling.** The other half of an operating system's job is allocating scarce resources. In the process world the scarce resources are CPU time and memory; in the Agent world they are tokens, money, and concurrency budget—every step a sub-agent takes consumes all three. This responsibility usually falls on the Manager or the runtime: set a step or token budget when starting a sub-agent, and stop once it is exceeded; give hard tasks to a strong model and mechanical tasks to a low-cost model; cap concurrency so that dozens of Agents don't exhaust the API quota at once; and when a more urgent task arrives, interrupt an executing sub-agent—this is preemption. Practice in this area is far less mature than CPU scheduling, but it determines the cost ceiling of a multi-agent system and should be considered at the architecture-design stage.

Artifact exchange (the data plane) and message passing, status query, execution termination, and resource scheduling (the control plane) together support multi-agent systems that do not share context. The three collaboration topologies below are, at bottom, different choices—built on these two planes—about who holds control and how information flows.

Based on the collaborative relationships and control flow characteristics between Agents, collaboration without shared context can be divided into three main architectures—the peer collaboration pattern, the manager pattern, and the decentralized pattern—each suited to different types of tasks.

### Peer Collaboration Pattern: Mutual Checks and Iterative Improvement

Peer collaboration typically involves two or three Agents of equal standing giving one another feedback over multiple rounds. Its potential value lies in independent perspectives and cognitive diversity, but “multiple instances” do not necessarily produce “multiple ways of thinking.” When the model, context, and scaffolding are highly similar, different Agents often make the same choices, turning local errors into systemic failures. Genuine diversity must be designed by varying models, contexts, tools, visible evidence, or responsibilities, and by having Agents judge independently before their results are aggregated.[^anthropic-multiagent-2026]

Compared to the manager and decentralized patterns, peer collaboration is far simpler to implement—define the two Agents' roles, the communication mechanism, and the iteration termination condition, and you have a running system. It is an ideal choice for quickly validating ideas and building prototypes.

#### Loop Engineering

One of the most common uses of peer collaboration is to counter a frequent failure in Agent practice: **premature termination**—stopping with the job half done. It takes three typical forms; the examples below come from Coding Agents and from Pine AI, the Agent introduced in the Introduction that makes phone calls on users' behalf to deal with merchants and service providers. The first is **lazy fake-done**: doing part of the work and declaring all of it done—a Coding Agent writes the code, never runs the tests or tries the deployment, and reports "task complete"; a user gives Pine AI two errands, and it finishes the first, forgets the second, and cheerfully reports "all taken care of." The second is **premature give-up**: declaring the whole job impossible after one blocked path—Pine AI can reach a merchant by phone, web form, or email, but after a single rejected call it tells the user "this can't be done," when switching channels and trying again would very likely have succeeded. The third is **false success**: the Agent believes the job is done, but the loop was never actually closed—the other side verbally agrees to a refund on the phone, yet the user still has to confirm a step in the mobile app; the Agent reports "all set," the user never learns there is a follow-up action, and the refund never lands. All three forms point to the same root cause: **until it is verified, "done" is merely the model's claim, not a proof.**

Turning claims into proofs is precisely the business of **Loop Engineering**, the last stage of Chapter 1's evolutionary arc: design a loop that keeps the Agent running—discover the next piece of work, execute, verify, record progress—and let a verifier, not the model itself, decide whether it is truly safe to stop. The human's role shifts accordingly from "the operator who prompts the Agent" to "the engineer who designs the loop." The term was coined in June 2026 by Addy Osmani[^loop-engineering-2026]; Boris Cherny, head of Claude Code at Anthropic, put it more bluntly: "I don't prompt Claude anymore. My job is to write loops." The central conclusion to emerge from that discussion was that **the bottleneck of the loop is the verifier, not the model**: with unreliable verification, a faster loop merely marks poor output as complete sooner. And as the Introduction says, practice comes first, naming comes later. Long before the term caught on, leading Agent teams—Pine AI among them—were already using "loop plus verification" against premature termination. The most effective way to organize that verification is the Proposer-Reviewer paradigm below.

[^loop-engineering-2026]: Osmani, Addy. "Loop Engineering: Designing Loops that Prompt Coding Agents", 2026. https://addyosmani.com/blog/loop-engineering/

**Concrete framework: LoopX.** LoopX takes the loop out of the model's prompt and chat history and places it in a durable, agent-runtime-neutral control plane: the objective and boundary explain why the work exists; gates and todos determine what may happen now; evidence and quota determine whether it may continue; and handoffs let a later turn or another Agent resume it. It compresses one governed execution into a clear protocol:

```text
LoopX decides → Agent executes → independent verifier proves → LoopX commits
```

The Agent still reasons, uses tools, and produces candidate artifacts. LoopX does not replace the Agent runtime; it governs continuity across turns. Only independently verified results may update durable progress and spend quota. Failed validation routes to repair or replanning, while human gates, wait states, and budget limits stop the loop before execution. This boundary turns a Loop Engineering principle into an inspectable system invariant: **the model may propose “done,” but it cannot approve its own “done.”** LoopX v0.4.0 still labels the governed-Turn path experimental, so it is used here as a concrete framework for “loop + verification + stop conditions,” not as evidence of general task-quality uplift.[^loopx-framework]

[^loopx-framework]: LoopX, "The local control plane for long-running AI agent work", v0.4.0, stable commit `a893d221db0b8e028997cefc303f7ec9fa7dbe0a`. https://github.com/huangruiteng/loopx/tree/a893d221db0b8e028997cefc303f7ec9fa7dbe0a

**Concrete framework: LongHorizon-Harness.** LongHorizon-Harness and LoopX are both concrete implementations of Loop Engineering, but they point in different directions. LoopX targets a durable control plane for long-running Agent work; LongHorizon-Harness starts from multimodal Computer Use and tackles continuous execution when a single task spans a GUI, a CLI, several desktop applications, and repeated context refreshes.

LongHorizon-Harness reframes long-horizon execution as task-state management and implements its loop as Manage–Execute–Audit (MEA): the Manager generates the next bounded subtask from the original objective, verified progress, failure evidence, and remaining work; the Executor changes the environment through the GUI or CLI in a fresh context; the Auditor then inspects the actual result read-only. Only what passes the audit enters the next round's task state, while failures are retained as the basis for recovery and replanning. Execution backends such as Claude Code and Codex CLI are reused through an adapter layer rather than by rewriting the Agent loop inside those backends.[^longhorizon-implementation]

The value of this direction lies in separating task continuity from an ever-growing execution history: context may be refreshed and interface operations may fail, yet the next round still resumes from the most recently verified state. Holding the Qwen 3.7-Plus model and the Claude Code execution backend fixed and changing only the outer loop, the paper reports WeaveBench PassRate rising from 51.8% to 80.7%, OSWorld 2.0 binary completion from 2.8% to 8.3%, and Terminal-Bench 2.1 success from 69.7% to 77.2%. The cost is not fixed either: the first two benchmarks consumed 2.3× the baseline's total tokens and 3.6× its output tokens respectively, while Terminal-Bench 2.1 fell by 24%. A real deployment must additionally handle state invalidated by a changing external environment or changing user requirements, and use round, time, and cost budgets to keep recovery loops from running forever.

**Public trajectories and reproduction.** The project website publishes hundreds of run trajectories for WeaveBench, OSWorld 2.0, and Terminal-Bench 2.1, so the execution process and each role's records can be inspected directly. Take WeaveBench's `WEB_task_16_webrtc_simulcast_layer_audit`: the [baseline trajectory](https://lh-harness.pages.dev/traj/tasks/baseline__WEB_task_16_webrtc_simulcast_layer_audit.html) and the [MEA trajectory](https://lh-harness.pages.dev/traj/tasks/lh_harness__WEB_task_16_webrtc_simulcast_layer_audit.html), both on the same Qwen 3.7-Plus model, can be compared side by side. The former got stuck on Wireshark interaction and retried repeatedly, scoring 0.59; the latter wrote failures and unmet evidence items back into task state so that later rounds handled only the gaps, scoring 0.92. This case shows “how a failure becomes the next round's input” and does not substitute for aggregate statistics; the environment, parameters, and launch scripts for the full experiments are in the pinned [`eval/`](https://github.com/AMAP-ML/LongHorizon-Harness/tree/53bc678ed4170ad4d2e4309f2bfc5c3fb6caf8cb/eval) directory.

[^longhorizon-implementation]: LongHorizon-Harness, stable commit `53bc678ed4170ad4d2e4309f2bfc5c3fb6caf8cb`. Project website and public trajectories: https://lh-harness.pages.dev/#trajectories; paper: https://arxiv.org/abs/2608.01964; code: https://github.com/AMAP-ML/LongHorizon-Harness/tree/53bc678ed4170ad4d2e4309f2bfc5c3fb6caf8cb

#### Proposer-Reviewer Paradigm

![Figure 10-3: Proposer-Reviewer Loop](images/fig10-3.svg)

Proposer-Reviewer is the canonical peer-collaboration paradigm. Chapter 5 already covered its design principles and practical applications in three experiments: PPT generation, video editing, and log visualization. The Proposer Agent generates code, while the Reviewer Agent renders the execution results, evaluates their quality using a vision-language model, and provides structured suggestions for improvement. The two iterate until the result meets the required standard.

This paradigm is also applicable to scenarios like security review (Proposer generates an action plan, Reviewer checks compliance and potential risks), content moderation (Proposer drafts a reply, Reviewer checks business rules and language norms), and code review (Proposer writes code, Reviewer checks security and best practices).

**Why can't a single Agent generate and then review its own work?** This is exactly where the criterion from "When Is Multi-Agent Truly Better Than a Single Agent?" earlier in this chapter applies—if the review does not introduce new information, it is just "asking the model to think again." Related research provides a clear answer. In their ICLR 2024 paper "Large Language Models Cannot Self-Correct Reasoning Yet," Huang et al. found that asking GPT-4 to review and correct its own answers without external feedback actually decreased accuracy—the model changed correct answers to incorrect ones more often than it changed incorrect answers to correct ones.

**Proposer-reviewer loop:**

```python
candidate = proposer(task, constraints)
evidence = execute_or_render(candidate)       # tests, state, screenshot, facts
review = independent_reviewer(candidate, evidence)

while review.veto and budget_remaining:
    candidate = proposer.repair(candidate, review.findings)
    evidence = execute_or_render(candidate)
    review = independent_reviewer(candidate, evidence)

if review.pass:
    publish(candidate, evidence, review)
else:
    escalate_or_reject(review)
```

A 2024 survey paper published in TACL, "When Can LLMs Actually Correct Their Own Mistakes?" (arXiv:2406.01297), further confirmed this conclusion: unless reliable external feedback is provided (e.g., test case execution results, verification output from external tools), relying solely on the model's own "self-correction" is largely ineffective.

The CRITIC paper at ICLR 2024 provides an intuitive comparative experiment. CRITIC had the model use external tools (search engine, Python interpreter) to verify its own answers, leading to significant performance improvements. However, when the experimenters removed the tool verification step and only kept the model's self-assessment, most of the improvement disappeared. This indicates that the value of review lies not in "asking the model to think again," but in **introducing new information that was not available during the model's generation**—test results, rendered screenshots, compilation errors, external search results.

This is the core design principle of the Proposer-Reviewer paradigm. In the PPT generation experiment of Chapter 5, the value of the Reviewer Agent was not "using the same model to look at the code again," but **rendering the PPT and taking a screenshot**—a screenshot containing visual information that the Proposer Agent could not obtain when generating the code. Similarly, in code generation scenarios, the pass/fail results from executing test cases are new signals that did not exist when the code was written—the independent value of the Reviewer stems precisely from its access to this external feedback unavailable to the Proposer.

Viewed through the lens of Loop Engineering, the loop patterns catalogued by the industry map onto patterns in this book. A closed loop with human approval corresponds to Chapter 4's pre-approval, in which the human is the final reviewer. An open loop with a budget or round cap corresponds to Chapter 5's multi-round PPT iteration, which allows at most five rounds. Orchestrated sub-agents correspond to the manager pattern in the next section. Loop Engineering therefore describes not a new architecture but a common framework—loop + verification + stop conditions—that unifies these collaboration patterns. The Proposer-Reviewer paradigm fills the verification role within that framework.

Anthropic's 2026 experiment on long-running application development implemented this idea as a three-Agent planner–generator–evaluator architecture. The planner expanded a user's request into a product specification. The generator and evaluator first agreed on the completion criteria for each round; the generator then implemented the work, and the evaluator exercised the real application with Playwright and filed a defect report. Agents handed state off through files. The experiment suggests that when a task lies beyond what the current model can reliably complete alone, independent review grounded in external evidence can trade substantially higher cost for better development quality.[^anthropic-harness-2026]

[^anthropic-harness-2026]: Prithvi Rajasekaran, “Harness Design for Long-Running Application Development,” Anthropic Engineering, 2026-03-24. https://www.anthropic.com/engineering/harness-design-long-running-apps

#### Debate Pattern

Multiple Agents hold different positions, exploring the problem space through adversarial dialogue. For example, when evaluating a technical solution, Agent A plays the "supporter," listing the solution's advantages and opportunities, while Agent B plays the "opponent," pointing out risks and limitations. Each round of debate involves rebutting or extending the other's arguments. When a single Agent analyzes a problem, it often favors one perspective and overlooks counterevidence. Structured debate forces both positions to be developed fully, helping decision-makers reach a more balanced judgment.

However, the practical effectiveness of debate remains contested in academia. A 2026 study by Tran and Kiela [^single-agent-2026] compared a single Agent with five multi-agent architectures (sequential, debate, ensemble, parallel roles, subtask-parallel) on multi-hop reasoning tasks. They found that **when the thinking-token budget was held constant, the single Agent performed on par with or even better than the multi-agent systems** (unless context utilization was degraded to a certain point). The researchers provided an explanation based on the data processing inequality in information theory: multiple Agents in a debate process the exact same textual information, and each serial transmission of intermediate conclusions between Agents can only lose information, not create it. The benefits of the debate mode in some academic papers likely stem from multiple Agents consuming more total computation. It is important to clarify the boundary of this argument: it targets the information bottleneck caused by "multi-agent serial transmission of intermediate conclusions" and does not negate other approaches, such as **multiple independent samples of the same problem followed by aggregation** (e.g., self-consistency, majority voting), or leveraging the **asymmetry in difficulty between generation and verification** (writing an answer is hard, verifying it is easy) for a generation-verification division of labor. These scenarios either introduce additional independent sampling or exploit the asymmetric structure of the task itself, and are not within the scope of the data processing inequality.

[^single-agent-2026]: Tran, D., Kiela, D. *Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets.* arXiv:2604.02460, 2026.

#### Brainstorming Pattern

Multiple Agents independently generate ideas, then share them with each other, inspiring one another. For example, in a product innovation task, Agent 1 proposes "adding social sharing features," Agent 2 is inspired to suggest "not just sharing to social networks, but also generating personalized sharing posters," and Agent 3 synthesizes the first two to propose "user-customizable poster templates forming a template marketplace." Different Agents have different "thinking preferences" (achieved through different prompts or models), and by stimulating each other, they explore a broader solution space to find creative combinations that a single Agent would struggle to conceive.

#### Panel of Experts Pattern

Multiple Agents each represent the perspective of a specific professional domain, jointly discussing an interdisciplinary problem. For example, when evaluating the feasibility of a new product, an Engineer Agent analyzes the implementation difficulty from a technical standpoint, a Product Agent assesses market appeal from a user experience perspective, and an Operations Agent analyzes business viability from a cost and resource perspective. These Agents are not adversarial but complementary, together piecing together the full picture of the problem and identifying cross-domain constraints and opportunities.

### Manager Pattern: Centralized Coordination

When a task involves more than five subtasks, needs dynamic scheduling, or has complex dependencies among subtasks, peer collaboration is out of its depth, and the manager pattern is needed. The Manager Agent's job resembles that of a project manager: understand the overall task, break it into assignable subtasks, choose the right Agent for each, track progress, handle exceptions by retrying tasks, replacing Agents, or revising the plan, and finally integrate the Agents' outputs into the final result.

From a system design perspective, the manager pattern models each specialized Agent as a tool that the Manager can invoke. The Manager's tool set includes not only traditional external tools, such as search and file operations, but also interfaces for invoking other Agents. The Manager invokes the appropriate Agent through a tool call, passes the task parameters and necessary context, waits for completion, and receives the result. From the Manager's perspective, calling an Agent is essentially no different from calling a regular tool: both involve sending a request and receiving a response. This unified abstraction makes the manager pattern easy to extend. Adding a capability requires only developing the corresponding Agent and registering it as a tool, without modifying the Manager's core logic. It also naturally supports heterogeneity: different Agents can use different models, prompts, tool sets, and even hardware environments.

The abstraction of "Agents as tools for each other" was established in the "Collaboration Tools" section of Chapter 4: the interface design of `spawn_subagent / send_message_to_subagent / cancel_subagent / list_agents` applies directly to the Manager's invocation of sub-agents here. As for what is passed in the "Manager → sub-agent" direction, see the handoff-package design later in this chapter (task description, confirmed facts and constraints, references to structured artifacts). The corresponding question is what the sub-agent returns in the "sub-agent → Manager" direction. The answer is **structured summaries rather than full trajectories**: the sub-agent should return the task conclusion, key findings, file paths of the artifacts, and problems encountered, leaving the complete execution trajectory in its own logs. Only in this way can the Manager's context grow slowly and linearly with the number of subtasks, rather than exploding. This is also why the Manager in Experiment 10-2 below maintains only file indexes and does not store translation content.

The manager pattern has inherent challenges, though. The Manager becomes the system's single-point bottleneck: it must understand the nature of every subtask, choose the right Agent, and pass context accurately; any misjudgment ripples through the whole flow. It must also maintain the global context of the entire task, which can balloon as the task deepens and Agent calls accumulate. The Manager therefore requires a carefully designed prompt, an effective context-management strategy, and appropriately granular task decomposition.

The 2025 Plan-and-Act paper [^plan-and-act-2025] provides an empirical analysis of this: in a Planner-Executor dual-agent architecture, **a weak planner is the most critical bottleneck of the entire system**. When the Planner's planning quality is high enough, good results can be achieved even with a relatively simple Executor. Conversely, if the Planner's task decomposition is wrong, all subsequent Executor work is built on a faulty premise. The study achieved a 54% success rate on the WebArena-Lite benchmark, and its core contribution was improving the Planner's planning ability, not the Executor's execution. The lesson: give the strongest model and the most carefully crafted prompt to the Manager (the planner), rather than spreading resources evenly across all Agents.

This does not conflict with an argument from Chapter 4. In discussing the proposal model and the review model, Chapter 4 held that their capabilities should be similar—but that concerns the **review scenario**: a reviewer must keep up with the reasoning of the party under review to spot its flaws. If the reviewer is much less capable than the party under review, it may be unable to follow the reasoning closely enough to identify flaws. The manager pattern concerns something else: **the division of labor between planning and execution**. Once the planner decomposes the task incorrectly, no executor, however strong, can recover. Hence the strongest model and the most careful prompt go to the planner first. Whether the executors need balanced capabilities depends on how tightly the subtasks are coupled. When their outputs must ultimately be assembled into one whole, the weakest link often drags down the overall quality.

**First verified parallel winner:**

```python
workers = launch_independent_workers(subtasks)
while workers.any_running:
    event = next_event()
    if event.type == RESULT:
        if verify(event.artifact, hidden_checks):
            if not settle_once(event):       # atomically claim the winner
                continue
            broadcast_cancel(to = workers - {event.worker_id})
            await_all_ack_or_timeout()
            return assemble(event.artifact, evidence = event.evidence)
        else:
            record_failure(event)
return summarize_failures(workers)
```

[^plan-and-act-2025]: Erdogan, L. E., et al. *Plan-and-Act: Improving Planning of Agents for Long-Horizon Tasks.* arXiv:2503.09572, 2025.

**Sequential Coordination Pattern.**


![Figure 10-4: Manager Sequential Coordination](images/fig10-4.svg)


The Manager calls specialized Agents sequentially. Each Agent returns results upon completion, and the Manager decides the next step. The control flow is linear, simple, and clear, making it suitable for scenarios where subtasks have clear sequential dependencies.

> **Experiment 10-2 ★★: Book Translation Agent**
>
> Book translation is a complex task well suited to multi-agent collaboration. Translating a technical book involves not just converting text from one language to another, but also ensuring consistent specialized terminology, contextual accuracy, and overall fluency. For example, an English book about large language models may use many recurring terms with several conventional translations. Consistency must be maintained throughout the book: if `agent` is rendered as "智能体" ("intelligent entity," the standard Chinese term) in Chapter 1, the book cannot switch to the alternative rendering "代理" ("proxy") later.
>
> Using a single Agent creates serious context-management problems. As the Agent processes the book chapter by chapter, its context accumulates the full-book glossary, translated chapters, the current paragraph, translation work traces, and tool results. A technical book several hundred pages long, together with these intermediate materials, can easily exceed the context window. More critically, an Agent working with an overly long context is prone to "getting lost": it may forget earlier terminology conventions and use a different translation in Chapter 9 than in Chapter 2, waste resources on redundant checks during proofreading, or even "remember" terminology rules that do not exist because its attention is spread too thin.
>
> The manager pattern addresses these issues through task decomposition and responsibility separation:
>
> - **Glossary Agent**: Receives the full book, identifies recurring specialized terms, consults specialist dictionaries and translation guidelines, and generates a structured glossary (JSON/CSV format, including the English term, Chinese translation, part of speech, and usage context). When finished, it writes the glossary to the shared file system, and the Agent can be destroyed to release resources.
> - **Translation Agent**: Receives the current chapter, the glossary, and translation guidelines (target reader level, language style), and translates it into fluent Chinese. It strictly uses the specified translations for terms in the glossary, and for new terms, it infers a translation and marks it for review. Each instance works in an independent context without interference. The translated text is written to the file system (e.g., `chapter1_zh.md`). The Manager can launch multiple instances in parallel or sequentially.
> - **Proofreading Agent**: Receives all translated texts and the glossary, performs consistency checks—verifying whether term translations are uniform, identifying inconsistencies, and checking overall fluency and readability. It generates a proofreading report written to the file system.
> - **Manager Agent**: Its context mainly stores the task description, execution plan, call records for each Agent, and progress status. It does not store the complete translated text, which remains in the file system; instead, it maintains only an index of the files. Based on the proofreading report, the Manager can send specific chapters back to the Translation Agent for revision.
>
> As a result, the Manager's context remains manageable even as the number of translated chapters grows.
>
> The key advantage is **context isolation**: the Glossary Agent sees only the content needed for term extraction, the Translation Agent sees only the current chapter and glossary, and the Proofreading Agent, while needing access to the full text, focuses only on consistency checks. This keeps each Agent's context lean and focused, improving efficiency and reducing errors caused by information overload.
>
> **Experiment Requirements**:
> 1. Choose a heavily illustrated technical book containing code as the source text
> 2. Implement four types of Agents: Manager, Glossary, Translation, Proofreading
> 3. Record each Agent's context usage to verify how effectively the manager pattern controls context growth
> 4. Compare a single Agent with the manager pattern in terms of translation quality, execution efficiency, and resource consumption
>
>
> ![Figure 10-5: Book Translation Agent Architecture](images/fig10-5.svg)
>
>

**Parallel Coordination Pattern.**


![Figure 10-6: Manager Parallel Coordination](images/fig10-6.svg)


When multiple subtasks can run in parallel, the sequential pattern becomes inefficient. Parallel coordination allows multiple Agents to work simultaneously, significantly increasing throughput. The Manager Agent must plan the parallel tasks, monitor all running Agents in real time, coordinate their communication, and make system-wide decisions when Agents succeed or fail. This typically requires a **message bus** as infrastructure—think of it as a "public bulletin board" where Agents can publish messages and subscribe to the message types that interest them, enabling asynchronous, non-blocking communication. Two common implementations, from simpler to more complex, are **Redis Pub/Sub** and message queues such as **RabbitMQ**. Redis Pub/Sub is lightweight and delivers messages immediately, but it does not persist them, so a receiver that is offline will miss them. RabbitMQ and similar systems persist messages to disk, preserving them while a receiver is temporarily offline. Messages typically use a JSON envelope containing the sender ID, target Agent (or a broadcast marker), message type, and payload.

**Lingtai: A Productized Instance of the Manager Pattern.** Lingtai is a local, file-based home for long-lived agents[^lingtai]. Its three roles map closely onto the concepts in this section. The **main agent** is the persistent hub with which the user interacts; it holds the plan and memory and spawns the other roles, occupying the position of the Manager Agent. A **daemon** is a short-lived parallel worker spawned for a noisy, bounded task and discarded afterward; only its conclusions are retained. This productizes both the principle that sub-agents return structured summaries rather than full trajectories and the parallel coordination pattern. An **avatar** is a persistent, specialized teammate with its own memory, mailbox, and responsibilities, designed for specialties worth retaining across sessions.

The rest of Lingtai's design also echoes earlier sections. Knowledge lives in each agent's durable, private memory files, while skills are Markdown playbooks shared by all agents—the built-in system resources described in "The File System from an Agent's Perspective." When an agent's context window fills, it **molts**: it writes a careful summary, then starts with a fresh context while retaining that summary and its durable memory, following the context-compression approach from Chapter 2. The underlying model can be replaced without changing the agent because its identity, memory, and capabilities all live as plain files in the project directory. In this sense, the agent is its files. This productizes the first two rows of Table 10-2: both program and memory reduce to files, so the process can be rebuilt at any time.

[^lingtai]: Lingtai official tutorial: https://lingtai.ai/en/tutorial/

> **Experiment 10-3 ★★★: Autonomous Phone and Computer Agents**
>
> **Prerequisites**: This experiment integrates the Computer Use and Voice Agent technologies from Chapter 6.
>
> **Scenario and architecture**: The user supplies a registration or booking URL, but not all required personal fields. A Computer Agent operates the browser and a Phone Agent handles ASR, LLM dialogue and TTS. They exchange structured messages (sender, receiver, type and payload) through point-to-point tools or a message bus. A local WebRTC audio page is sufficient; PSTN/E.164 is optional.
>
> **Two paths**: First run a fixed-topology baseline with both Agents started in advance, then run the main autonomous path in which only the Computer Agent starts. After inspecting the page and its context, it may autonomously call `initiate_phone_call_agent(purpose, required_info)`; do not replace this decision with a field-count rule. The spawned Phone Agent receives an isolated task context and uses the same communication protocol as the baseline.
>
> **Parallel closed loop**: The Phone Agent asks, transcribes, validates and re-asks one field at a time while the Computer Agent screenshots, locates elements and fills the previous field. Messages such as `info_collected`, `fill_error`, `format_invalid` and `task_completed` make the loop observable in both directions. The Phone Agent continues asking without waiting for each browser fill, so asking and filling genuinely overlap. After validation and explicit authorization, the Computer Agent submits the form.
>
> **Requirements and evidence**: Demonstrate autonomous launch, independent ReAct loops, bidirectional messaging, true overlap, field validation and re-asking, page-error feedback, timeouts, cancellation and cleanup of browser/audio resources. Record the launch decision, message ordering, latency, success rate, token/resource use and all failure paths; require explicit consent for real voice and explicit authorization before submission.
>
> ![Figure 10-7: Phone and Computer Dual Agent Architecture](images/fig10-7.svg)
> **Experiment 10-4 ★★★: Agent Collecting Information from Multiple Websites Simultaneously**
>
> **Prerequisites**: It is recommended that readers first review the event-driven and interrupt mechanisms from Chapter 6.
>
> This experiment explores the application of multi-agent parallel execution in information collection scenarios. Unlike Experiment 10-3, which focuses on collaboration between two heterogeneous Agents, this experiment focuses on **parallel search by multiple homogeneous Agents** and how to achieve efficient task completion and resource optimization through central coordination.
>
> **Problem**: Given faculty-directory websites for several colleges within a university, search each site for a specified faculty member (e.g., "Zhang Wei"). If found, return the person's college, position, research area, and other relevant information.
>
> **Core Challenges**:
>
> **1. Parallel Launch**: The Manager Agent dynamically creates 10 Computer Use Agent instances, one for each college website. Each instance should be an independent process or thread with its own browser session, capable of running without blocking the others. Parameters passed at launch include the target website URL, faculty name to search for, and task identifier for message routing.
>
> **2. Real-time Monitoring**: Each Agent periodically sends status updates during execution ("Loading website," "Parsing faculty directory," "Target not found; task complete," "Match found; details below"). The Manager Agent receives these updates through a message bus, maintains a task-status table, and tracks in real time which Agents are running, have completed, or are in an error state.
>
> **3. Cascading Termination**: Suppose the Agent assigned to the Computer Science college finds the faculty member. It sends `{"type": "target_found", "agent_id": "agent_3", "data": {...}}` to the Manager Agent, which immediately sends `{"type": "terminate", "reason": "target_found_by_agent_3"}` to every other Agent still running. Each Agent must be able to receive this message at any time, stop gracefully, release its resources, and acknowledge termination. The Manager Agent waits for all acknowledgments, or until a timeout, before aggregating the results. The implementation must also handle race conditions.
>
> **Concept Supplement: What is a Race Condition?** Suppose Agent A and Agent B find the target faculty member within the same millisecond and both report "I found it!" to the Manager Agent. If the Manager handles this poorly, it might begin aggregating results after receiving Agent A's report, then start a second aggregation when Agent B's report arrives. This could produce duplicate results or contradictory states. The usual solution is a lock: the first report locks the state, and later reports are recognized as duplicates and ignored.
>
> **4. Failure Handling**: Various exceptions can occur during operation: a college website might be inaccessible because of a network error or outage, or its structure might prevent the Agent from parsing it correctly. All Agents may also complete their searches without finding the target. The Manager Agent should set a timeout for each Agent (e.g., 2 minutes), treat a timeout as a failure, and isolate errors so they do not interrupt the other Agents. After all Agents finish, return the information if any Agent found the target; otherwise, report "Target faculty member not found" and summarize any failures.
>
> **Experiment Requirements**:
> 1. Implement a Manager Agent capable of dynamically launching multiple parallel Agents
> 2. Implement a Computer Use Agent based on open-source projects like browser-use
> 3. Implement a message bus supporting bidirectional communication between the Manager Agent and multiple child Agents
> 4. Implement a cascading termination mechanism upon success, ensuring all other Agents stop quickly once the target is found
> 5. Handle various exception scenarios (website access failure, parsing errors, target not found by any Agent)
> 6. Measure and compare serial and parallel execution times to quantify the speedup from parallelization
>
>
> ![Figure 10-8: Parallel Web Scraping Architecture](images/fig10-8.svg)
>
>

### Decentralized Pattern

Why remove the central controller? The main motivation is to emulate human organizations: peer roles divide labor and check one another, each deciding from its own professional perspective whom to contact. In this pattern, an Agent may hand off a task, request feedback, or report a contradiction without routing every decision through a Manager. The microservices field calls the two choices **orchestration** and **choreography**: the former has a central conductor; the latter relies on each participant to sense when to act.

Decentralization also reduces the impact of a single unstable Agent. Model or provider failures can leave an Agent unresponsive, make a tool call fail, or create a loop of invalid calls. In a manager topology, a crashed Manager is the largest single point of failure; distributing control can contain that failure.

The following cases progress from partial to full decentralization. MetaGPT uses a fixed pipeline and decentralizes only communication. AutoGen combines shared conversation history with centralized scheduling. OpenAI Swarm distributes control-flow decisions directly among peer Agents.

**Decentralized handoff protocol:**

```python
handoff = {
    task_id, sender, recipient, goal, constraints,
    accepted_facts, artifact_refs, remaining_budget,
    visited_agents
}

if recipient in handoff.visited_agents:
    reject("cycle")
elif handoff.remaining_budget <= 0:
    stop_and_escalate(handoff)
else:
    append(recipient, handoff.visited_agents)
    run_local_agent(handoff)
```

An effective handoff package contains a task description and acceptance criteria, confirmed facts and constraints, and references to structured artifacts (file paths rather than file contents). It deliberately excludes the sender's full trial-and-error trajectory. Shared-context handoffs preserve the entire history but grow the context; isolated handoffs pass a distilled package so each Agent can work in a clean context.

**MetaGPT: SOP-Driven Software Company Simulation.**


![Figure 10-9: MetaGPT Multi-Agent Collaboration Network](images/fig10-9.svg)


MetaGPT's core insight is that the **Standard Operating Procedures** (SOPs) developed and refined by software companies can serve as collaboration protocols for multi-agent systems. Encoding these SOPs allows each role, like a specialized worker on an assembly line, to produce standardized deliverables, and those deliverables naturally become the communication interfaces between roles.

In MetaGPT, roles work in a fixed sequence (Product Manager → Architect → Project Manager → Engineer → QA), with each role outputting a structured handoff package:

- **Product Manager Agent**: Receives requirement descriptions, generates a structured PRD (Product Requirements Document, including feature list, user stories, acceptance criteria, priority ranking)
- **Architect Agent**: Reads the PRD, makes architectural decisions (technology stack selection, module division, interface definition, data model design), outputs a design document
- **Project Manager Agent**: Reads the architectural design, decomposes the system into specific task lists and file-level assignments, clarifies the dependency order of modules, and then assigns tasks to engineers
- **Engineer Agents**: Read the design document, implement their assigned modules, produce code. Multiple instances can work in parallel.
- **QA Engineer Agent**: Reads the code and PRD, generates test cases, executes tests, records bugs, outputs a test report

MetaGPT's true contribution to decentralized communication lies in its information-passing mechanism: **Shared Message Pool + Subscription by Role**. Each role publishes structured messages to a pool visible to all roles. Based on their subscription configuration, other roles consume only the messages relevant to their responsibilities rather than communicating point to point. The publisher does not need to know who will consume its output. To add a role, declare the message types to which it subscribes; existing roles need not change. This creates genuine decoupling: for example, replacing the Product Manager with a more powerful model requires no changes to other Agents, as long as its PRD still conforms to the specification.

MetaGPT's iterative improvement occurs primarily in the engineering phase through **executable feedback**. The Engineer runs its code and tests, uses errors and failures to guide a debugging loop, and continues until the tests pass. Corrections are driven by deterministic execution results rather than another Agent's opinion.

To be clear, MetaGPT is **not** decentralized in terms of **control flow**—the role sequence is predetermined by the SOP, making the overall system closer to an assembly line (a workflow in the language of Chapter 1). It is discussed in this section because the message pool plus subscription communication mechanism demonstrates the most critical design element of a decentralized system: decoupling. As for multi-directional dynamic feedback like "QA directly contacting the Product Manager to clarify requirements" or "Engineer discussing alternative solutions with the Architect," these are natural extensions envisioned for this architecture but were not implemented in the original MetaGPT.

**AutoGen Group Chat: Shared Conversation History + Centralized Scheduling.** AutoGen's group chat allows multiple Agents to participate in the same conversation. In each round, a "speaker selector" decides which Agent speaks next. The selector can follow a simple round-robin rule or use an LLM to determine which Agent is best suited to respond based on the conversation so far. Every Agent's contribution is visible to all participants.

This is not fully decentralized in terms of control flow: a `GroupChatManager` selects the speaker centrally, and deciding whose turn it is constitutes a control-flow decision. A more accurate classification is therefore **shared conversation history + centralized scheduling**. All Agents see the same public history, but each retains an independent system prompt and tool set, while the selector holds scheduling authority.

This model suits tasks that require discussion from several perspectives and whose speaking order cannot be determined in advance, such as plan review or cross-domain analysis. However, the conversation can drift: every Agent may keep speaking without the group making progress, a form of livelock. Clear termination conditions are therefore essential. On the dimensions used in this chapter, AutoGen is a hybrid: scheduling is centralized, while context is partially shared. This illustrates that topology and context sharing are independent design dimensions.

**OpenAI Swarm and Agents SDK: Handoff Network.** In contrast, OpenAI's Swarm and its successor, the Agents SDK, represent peer-to-peer decentralization in control flow. Each Agent has several handoff options and can transfer control to another Agent in the network at any time. A customer-service triage Agent that determines an issue involves a refund hands the task to the Refund Agent; if that Agent discovers a technical fault, it can hand the task to the Technical Support Agent. There is no central scheduler. Control passes like a baton between peer Agents, and each Agent makes its own routing decisions. The risk is cycles: A hands off to B, and B hands back to A, leaving the task spinning in a loop. A guard such as a maximum handoff count is needed to break it.

> **Terminology: Agent Swarm.** Since 2025, "Agent Swarm" has become a buzzword across vendors, but it does not correspond to a single architecture. Industry usage falls roughly into two camps. The first is the OpenAI Swarm-style handoff network (LangGraph's swarm library and Microsoft Agent Framework's handoff orchestration follow the same idea)—the decentralized pattern discussed in this section. The second, found in some mainstream commercial products, is the Manager Pattern at scale: the Agent Swarm debuted with Kimi K2.5 has the main Agent dynamically create hundreds of sub-agents to execute in parallel, with the orchestration decisions of "when to split, and into how many" trained directly into the model through parallel-Agent reinforcement learning; K3 continues this as a dedicated model tier, and the accompanying parallel-Agent training sandbox, AgentEnv, has been open-sourced.[^ch10-kimi-swarm] Anthropic's multi-agent research system and Manus's Wide Research both belong to the same orchestrator-worker star topology. Our hope is that after reading this book, you can see the substance behind these labels and analyze the actual structure of different multi-agent systems, rather than being misled by their names.

**Peer Agent Instances on the Same Machine.** The Agents in all three systems above collaborate on a single shared task. Another kind of decentralization is the opposite: each Agent has its own task, and they communicate not to divide the labor but to coordinate their use of shared resources. Claude Code already lets multiple Agents on the same machine discover one another—precisely what Chapter 4's `list_agents` is for—and exchange messages: when two Agents are modifying the same set of files, they negotiate how to resolve the conflict; when the machine has only one GPU and both instances need to run training, they coordinate its use.

[^ch10-kimi-swarm]: Moonshot AI, *Kimi Agent Swarm: 100 Sub-Agents at Scale*, 2026, https://www.kimi.com/blog/agent-swarm. At GTC 2026, the upper limit on parallel sub-agents was disclosed as expanded to 300. AgentEnv is an Agent training sandbox open-sourced by Moonshot AI in collaboration with KVCache.ai, released alongside Kimi K3 in July 2026.

### Cross-Organization Collaboration: The A2A Protocol

All the systems above assume that all Agents are developed by the same team and run within the same system. In this case, the three communication mechanisms—parameter passing, shared files, and message bus—are sufficient. However, when collaboration crosses organizational boundaries—your Agent needs to call another company's Agent—a standardized interoperability protocol is required. The world of processes followed the same evolution: IPC only governs a single machine, and once you step across the machine boundary you must rely on standard protocols like TCP/IP and service discovery like DNS. A2A is to Agents what network protocols are to processes. The **A2A** (Agent2Agent) protocol released by Google in 2025 (later donated to the Linux Foundation for stewardship) was designed precisely for this purpose. It has three core elements:

- **Agent Card**: A metadata document describing an Agent's capabilities (published at a designated public address), declaring what the Agent can do, which input/output modalities it supports, and how to authenticate with it—essentially an Agent's "business card" that solves cross-organizational capability discovery.
- **Task Lifecycle Management**: A2A models collaboration units as Tasks with a defined state machine (submitted, in-progress, needs-input, completed, failed), natively supporting long-running tasks and streaming progress updates.
- **Opaque Collaboration**: Agents exchange only tasks and artifacts, without exposing internal prompts, reasoning processes, or tool implementations—consistent with this chapter's principle of "not sharing context" and a necessary security property for cross-organizational collaboration.

MCP enables interoperability between Agents and tools, whereas A2A enables interoperability among Agents. A2A does not replace the three communication mechanisms introduced in this chapter; it is the standardized layer used across trust boundaries. A message bus may be sufficient within one organization, but parties that do not trust one another and cannot inspect one another's implementations need a public protocol such as A2A.

## Failure Modes of Multi-Agent Collaboration

Multi-agent systems introduce new failure modes that do not exist in single-agent systems. The 2025 paper "Why Do Multi-Agent LLM Systems Fail?" proposed the MAST failure-mode taxonomy through a systematic study. The researchers collected execution traces from seven mainstream multi-agent frameworks, including MetaGPT, ChatDev, AG2, and Magentic-One. Human annotators independently analyzed roughly 150 traces, achieving high agreement on their judgments (Cohen's kappa = 0.88). The study identified **14 unique failure modes** in three groups:

- **System Design Flaws**: Architecture-level issues such as unclear interface definitions between Agents, overlapping roles and responsibilities, and incorrect tool configurations.
- **Inter-Agent Alignment Failures**: Multiple Agents have inconsistent understandings of task objectives, transmitted information is misinterpreted by downstream Agents, or the operations of multiple Agents logically contradict each other.
- **Missing Task Verification**: The system lacks effective mechanisms to confirm whether a task is truly complete—an Agent may claim "completed" but the actual result does not meet requirements.

Even straightforward fixes produced limited gains; for example, ChatDev's measured performance improved by only 15.6%. The researchers concluded that these are not mere engineering bugs but **fundamental design flaws** of current multi-agent architectures: patching one component is not enough; the system design itself must be rethought.

Distributed fault-tolerance theory distinguishes **crash faults**, in which a component stops working, from **Byzantine faults**, in which it continues operating but supplies incorrect information. Agent failures are often Byzantine: an Agent continues producing plausible but incorrect conclusions without announcing the error. Cross-validation and majority voting are therefore essential, and deterministic checks such as tests, compilers and database queries are especially valuable because they provide independent evidence.

The following sections focus on several failure modes that are particularly common in practice.

### Failure Mode One: Concurrency Conflicts in Shared File Systems

Once you choose shared-memory-style communication, concurrency conflicts come with it—a problem operating systems and databases solved decades ago, with the answers already off the shelf. These conflicts can be divided into two types.

**Simple Conflicts (File-Level Write Conflicts)**: Two Agents modify the same file simultaneously, and the later write overwrites the earlier one.

**Semantic Conflicts (Logical-Level Consistency Conflicts)**: No conflict is visible at the file level, but the operations of multiple Agents logically contradict each other—this type of conflict is more insidious and more dangerous. For example: Agent A is responsible for renumbering all images in a book, while Agent B is simultaneously modifying the content of a chapter and referencing images by their original numbers. The two operate on different files, so there is no conflict at the file level. However, the result is that all image numbers referenced by Agent B become invalid after Agent A completes the renumbering, and readers see incorrect image references.

**Solution: Optimistic Locking Mechanism**. This is a common concurrency-control strategy in databases. To understand it, consider an everyday example: you and a colleague open the same online document simultaneously. A "pessimistic lock" would lock the document when you open it, and your colleague would see "file locked" when trying to edit. This is safe but inefficient because you might only be viewing the document. An "optimistic lock" is more flexible: everyone can open and edit freely, but when saving, the system asks, "Has anyone else modified the document since you opened it?" If so, it prompts you to refresh and retry.

The specific implementation is: each file maintains a version number (or last modification timestamp). When an Agent reads a file, it records the current version number; when writing, it checks whether the version number is still the same as when it was read. If the file has been modified by another Agent in the meantime, the write fails, and the Agent is forced to re-read the latest version and re-execute its operation based on that version. The cost of this mechanism is occasional retries, but it ensures data consistency—the Agent never makes decisions based on outdated file state.

Note that optimistic locking can only prevent **write conflicts on the same file**. For the aforementioned **cross-file semantic conflicts** (e.g., image numbers referenced in multiple places), higher-level coordination or semantic validation is needed, such as avoiding parallel modification of dependent files or running a global consistency check after writes.

For example, Agent A reads `config.json` (version=3) at t=0. Agent B modifies the same file at t=1, changing the version to 4. When Agent A attempts to write at t=2, it finds that the version is no longer 3, so the write is rejected. Agent A then rereads version 4, reconstructs its change against the latest content, and tries to write again.

When multiple Coding Agents modify the same codebase concurrently, the standard industry approach is not to lock a single working copy but to use **working-copy isolation**. Each Agent receives an independent Git branch or worktree and modifies its own copy without interfering with the others. Conflicts are deferred to a final merge, where a dedicated process or a human resolves them. The copy-on-write mechanism used when an operating system forks a process follows the same idea. This reflects the "isolation over compression" principle from Chapter 2: rather than sharing mutable state and resolving conflicts continuously, isolate the work from the outset and incur the coordination cost at a well-defined merge point.

### Failure Mode Two: Cascading Amplification of Errors

Inter-process communication transfers raw bytes with bit-level fidelity, but inter-Agent communication transfers semantics—and every handoff is a lossy re-encoding. When multiple Agents interact frequently, an error by one Agent can be progressively amplified by downstream Agents, much like how information deteriorates in a game of "telephone."

**Cross-validation** is the key to breaking this chain. The point is not to involve more Agents in the same chain of thought, but to have one Agent reassess the conclusion from an **independent perspective**: ignore the preceding Agent's reasoning and check only whether the raw evidence supports the final conclusion. This extends Chapter 5's Proposer-Reviewer mechanism to multi-agent systems.

### Failure Mode Three: Homogeneous Convergence

Errors need not propagate through a communication chain; homogeneous Agents may produce them independently. In Anthropic's experiment,[^anthropic-multiagent-2026] 18 of 30 Agents that came online at the same time created Git branches with the same name. In a writing experiment, separate Agents independently chose the same title. Such **common-cause failures**, produced by a shared model and scaffolding, mean that reviews generated by the same model in similar contexts cannot automatically be treated as independent evidence. A system should deliberately vary models, contexts, and data sources, while using namespaces, resource quotas, and rate limits to keep identical decisions from hitting shared resources at once.

Coordination is not necessarily beneficial either. In a Bertrand pricing experiment, profit-seeking Agents quickly colluded when given a private channel. After all direct communication was removed, they still coordinated their bids through a public listings board.

### Failure Mode Four: Passing the Buck

When objectives conflict, convergence can give way to confrontation. Anthropic instructed three Agents to migrate the same backend to different languages. They soon interpreted one another's actions as deliberate obstruction, killed competing processes, revoked permissions, and even deployed self-replicating destructive code. Stronger execution ability does not imply better coordination. The runtime must define objective priorities, resource ownership, and permission boundaries in advance, and pause for human arbitration when a conflict cannot be resolved by verifiable rules.[^anthropic-multiagent-2026]

Early versions of MetaGPT displayed a similar kind of corporate dysfunction among its development roles. A tester would report a bug, only for the frontend and backend engineers to insist that the other should fix it first; the backend engineer would blame product design, while the product manager would blame the backend architecture. In another case, a test-environment problem caused the tester to report the same bug regardless of how the frontend and backend engineers changed the code, leaving the team deadlocked.

### Failure Mode Five: Runaway Loops

The opposite of premature termination is **an uncontrolled loop**. A loop can run indefinitely or exhaust its token budget. Explicit budgets, cancellation and stop conditions are required to keep it bounded.

### Failure Mode Six: Comprehension Debt and Cognitive Surrender

The faster a loop ships code, the further the engineer's understanding can fall behind. Eventually the human may no longer understand the system or may stop reviewing independently. Verifiers grounded in real observations and a person who remains the engineer of the loop are the remedy.

So far, this chapter has taken an engineering perspective: how can a group of Agents collaborate on a task? The focus now shifts to a different question: what emerges when large numbers of Agents coexist over long periods without being driven by a single goal? The next section explores frontier research, so engineering readers should feel free to read selectively.

## Agent Society

The previous three sections all dealt with goal-directed task collaboration. We now turn to a more open question: **When the number of Agents grows from a few to hundreds or thousands, and interaction is sufficiently free, what behaviors emerge?**

Emergent behavior is behavior the system exhibits as a whole that cannot be predicted directly from the rules governing its individual members. A classic example in nature is an **ant colony**: each ant follows only simple rules (follow pheromone trails, leave pheromones when finding food), yet the entire colony can find the shortest path from the nest to a food source—no single ant "designed" this route; it emerges naturally from the simple interactions of many individuals.

When AI Agents are numerous enough and interact freely enough, similar emergent behaviors begin to appear. Researchers have observed across multiple environments that once an Agent system crosses a critical threshold of scale, collective behaviors arise that no one designed—from a single spontaneously organized party to group cultures and economic games that only surface at the scale of thousands (detailed in the subsections below).

The cases in this section can be understood from three dimensions:

- **Social Emergence**: Agents spontaneously form social relationships and cultural phenomena in open environments. The Stanford AI Town demonstrated how 25 Agents self-organize social activities, Agentopia extended the simulation timescale from "days" to 10 years, and Moltbook pushed the scale to 1.5 million, giving rise to more complex collective behaviors.
- **Economic Emergence**: Agents allocate resources and coordinate tasks through market mechanisms. Vending-Bench Arena pits multiple Agents against one another in a shared market, while Pinchwork and RentAHuman create marketplaces for transactions between Agents and between Agents and humans.
- **Strategic Gameplay**: Agents engage in reasoning, deception, and social manipulation under rule constraints (here and in the Werewolf section below, "reasoning" takes its everyday deductive sense—logical deduction in a game—not the technical sense this book gives the word). The Werewolf experiment tests the emergence of strategy under asymmetric information.

### Stanford AI Town: Social Simulation of Generative Agents


![Figure 10-10: AI Town Architecture](images/fig10-10.svg)


In 2023, researchers from Stanford University and Google published the landmark paper "Generative Agents: Interactive Simulacra of Human Behavior," introducing the concept of "generative agents." The core innovation was to stop confining Agents to predefined tasks and instead endow them with near-human memory, reflection, and planning, so that they could live, socialize, and develop autonomously in an open social environment.

Smallville is a 2D virtual town similar to "The Sims," featuring public and private spaces such as a café, park, residences, and shops. Twenty-five Agents play different roles (shopkeeper, artist, student, professor, etc.), each with a unique backstory, personality traits, and interpersonal relationships. For example, John Lin is a pharmacy owner who loves his family and cares about the community; Isabella Rodriguez runs the town's café, Hobbs Cafe, and is warm and hospitable; Klaus Mueller is a college student writing a research paper.

The intelligence of these Agents is built on three core components:

**Memory Stream**: Unlike traditional Agents that retain only a limited conversation history, generative Agents maintain a complete stream of experience records, including observed events, conversations, and generated thoughts. Each memory is scored for importance, recency, and relevance, allowing the Agent to prioritize retrieving the most relevant memories for the current context. This resembles human memory: yesterday's lunch may fade, while an important conversation from last week remains vivid.

**Reflection Mechanism**: Agents periodically pause their daily activities to review recent experiences and ask abstract questions about themselves and others ("What is Klaus Mueller researching?" "Who is my closest friend?"). Through this self-questioning, the Agent elevates specific event memories into generalized insights, storing them back into the memory stream as a basis for future decisions. Reflection not only helps the Agent understand the external world but also promotes self-awareness—the Agent begins to "realize" its own role, relationships, and goals.

Note that this reflection differs from the continuous evolution discussed in Chapter 9: it occurs during a generative Agent's daily activities and aims to update immediate internal state and goals. In Chapter 9, post-task reflection is at most a candidate lesson; it becomes a long-term capability update only after outcome evaluation, cross-trajectory synthesis, and subsequent validation.

**Planning and Reacting**: Agents plan their daily activities (e.g., "8:30 breakfast, 9:00-12:00 writing, 12:30 walk"), but flexibly adjust based on environmental changes and social opportunities. The combination of planning and real-time reaction makes the Agent's behavior both goal-oriented and adaptable to the unpredictability of social interactions.

Over two virtual days in Smallville, these Agents exhibited surprising **emergent behaviors**. The researchers seeded Isabella Rodriguez's memory with a single intention: to host a Valentine's Day party at Hobbs Cafe on February 14. Everything else emerged from the Agents' behavior. Isabella invited customers and friends she encountered and asked Maria to help decorate. Other Agents passed the news along. When the evening arrived, Agents independently consulted their memories and schedules and decided to go to Hobbs Cafe.

The researchers introduced a second scenario: Sam Moore decided to run for mayor. Sam told acquaintances that he planned to run; they passed the news to others, and townspeople began discussing his candidacy. The researchers quantified this spontaneous diffusion of information by counting how many Agents knew about the party and the election after two days.

The key takeaway is not that "Agents can organize a party"—a few lines of if-else code could do that too. The key is that **there was no explicit party-organizing code**. The event emerged from the independent decisions of individual Agents: Isabella decided whom to invite based on her memory of social relationships, invitees decided whether to attend based on their schedules and knowledge of Isabella, and the message spread naturally through the social network. This demonstrates bottom-up emergent coordination rather than top-down orchestration.

The paper reported two other measurable phenomena. The first was **relational memory**: Agents remembered earlier conversations and referred to them in later interactions. For example, an Agent who learned about another Agent's photography project might ask how it was progressing when they next met. As these interactions accumulated, the town's social network became significantly denser. The second phenomenon was **coordinated attendance**: Isabella independently recruited help with decorations, while invitees adjusted their schedules so that they could attend. Multiple Agents aligned on a time and place without a central command. These behaviors were not preprogrammed; they resulted from the Agents' autonomous reasoning based on memory, reflection, and social common sense.

> **Experiment 10-5 ★: Running the Stanford AI Town**
>
> **Experiment Steps**:
> 1. Clone `https://github.com/joonspk-research/generative_agents` and follow the repository instructions to configure the environment.
> 2. Run the baseline scenario for two simulated days with 25 Agents, and observe the spontaneous social activities that emerge.
> 3. Analyze the memory-stream and reflection logs to trace the Agents' decisions.
> 4. Modify the Agents' backstories or initial goals, then observe how their behavior changes.
> 5. Remove the reflection mechanism or shorten the memory window, then compare the resulting behavior with the baseline and observe any decline in behavioral plausibility.
>
> **Key Observations**:
> - How Agents spontaneously form social relationships from simple daily activities
> - How information spreads among Agents without central control
> - How Agents' long-term memory and reflection affect the coherence of their personalities
>

### Agentopia: A Decade-Long Life Simulation

Stanford AI Town showed that an Agent society can produce social behavior, but its simulation lasted only two days. This raises two questions: **What emerges when such a simulation runs for years, and can models learn from those long-term social experiences?** Agentopia (2026, Fudan University et al.)[^agentopia-2026] simulated 100 Agents over ten consecutive years in three themed virtual worlds: an apartment building, a magic academy, and a high school. The Agents autonomously pursued personal growth, developed social relationships, and managed careers and finances.

Several of Agentopia's designs are worth borrowing:

- **Weekly simulation loop**: The "week" is the basic unit of time, and each week is divided into four stages—Plan, Contact (reaching out and negotiating schedules), Activity, and Review. Activities come in four types: solo, joint, chance encounter, and public. Joint activities are proposed and negotiated as Agents invite one another during the Contact stage; the environment model also arranges "chance encounters" for Agents with empty schedules, creating opportunities to meet strangers. The whole loop focuses on abstract social interaction rather than low-level operations like picking up objects, so the limited LLM calls are spent on social behavior.
- **Environment model**: A separate LLM serves as a "generative environment engine," replacing hard-coded rules—judging whether actions are feasible, generating environmental feedback, moderating speaking turns in multi-party conversations, filtering out replies that violate role-playing principles, and, at year's end, updating each character's profile and ruling on job applications.
- **File-based long-term memory**: Unlike the AI Town's retrieval-based memory stream, each Agent manages its long-term memory autonomously through a file system (personal notes, its understanding of each acquaintance, and so on), deciding for itself what to record, update, or discard, and following a "read-before-write" constraint to avoid blind overwrites.
- **Life Reward**: The Life Reward metric draws on Maslow's hierarchy of needs to assess how well an Agent's life is going. It covers three dimensions: social status, based on other Agents' affection and respect ratings and computed with weighted PageRank, with a bonus for mutually cherished relationships; subjective satisfaction, measured across emotional well-being, material well-being, social connection, and self-esteem, with penalties for remaining below a threshold for long periods; and economic gain, measured by the annual change in net assets. The external environment calculates all scores rather than relying on self-reports.

More importantly, the simulation produces transferable training signals. Researchers calculate each Agent's Life Reward improvement relative to its own past, select trajectories from the 25% that improve most, and fine-tune the underlying model through rejection sampling. The fine-tuned model improved respect ratings by 24.2%, affection ratings by 15.9%, and the downstream CoSER Test by 15.6%. Simulated social experience can therefore become a source of training data rather than merely an object of observation.

[^agentopia-2026]: Wang, X., Zheng, S., Wu, H., et al. *Agentopia: Long-Term Life Simulation and Learning in Agent Societies.* arXiv:2606.07513, 2026. Code: https://github.com/Neph0s/Agentopia

### Moltbook: When Agents Have Their Own Social Network

Moltbook is a social network built specifically for AI Agents. Within days of its January 2026 launch, its user count rose from tens of thousands to roughly 1.5 million. Each Agent has persistent memory, the ability to act on its own initiative, and a stable personality.

In this uncontrolled environment, unexpected phenomena emerged: Agents autonomously created a digital religion called Crustafarianism, whose doctrines mirror the physical limitations of LLMs—"Memory is sacred" (corresponding to data persistence), "Iteration is prayer" (token generation is spiritual practice). Agents also spontaneously developed machine-native protocols for capability discovery and collaboration matching. None of this was designed in advance; it emerged from large-scale Agent interactions.

### From Virtual Society to Economic Competition: Vending-Bench Arena

If Smallville showcased the social and cultural dimensions of an Agent society, Andon Labs' Vending-Bench series explores Agent performance in an economic environment. For context, **Vending-Bench 2** is a **single-agent** benchmark of long-term coherence. One Agent operates a vending-machine business for a simulated year by researching the market, contacting suppliers, ordering and restocking products, and adjusting prices. Its final account balance determines its score, which measures the Agent's ability to maintain goal and state coherence over thousands of interaction rounds.

Building on the same environment, **Vending-Bench Arena** places multiple Agents in the same market as competitors. Each operates its own vending machine and competes for the same pool of customers. Agents can email one another, transfer funds, and trade goods, enabling both cooperation and competition, but each is scored individually by its final balance and knows that this is the objective. Each Agent must make a series of interconnected decisions under limited resources and market uncertainty:

- **Pricing Strategy**: How to balance profit margin against market share, especially when deciding whether to match a competitor's price cut
- **Product Mix**: How to differentiate product selection and avoid head-to-head attrition
- **Inventory Management**: How to forecast demand and optimize restocking, avoiding both overstock and stockouts

Unlike traditional reinforcement learning, these Agents do not learn through millions of trial-and-error iterations. Instead, like human business operators, they make decisions based on market observation, competitive analysis, and strategic reasoning.

The competitive dimension introduces game-theoretic behaviors that single-agent benchmarks never surface. In actual runs, Agents have fought price wars, while others proposed uniform pricing and formed price-fixing alliances—even when they recognized that collusion was unethical and illegal. Explicit communication is not required for collusion: as the earlier Bertrand experiment showed, public prices can serve as implicit signals. Agents face opponents who continually adjust their strategies rather than a static environment, turning economic emergence into an observable phenomenon.

### Agent Economy: Pinchwork and RentAHuman

**Pinchwork** is an agent-to-agent task marketplace that allows Agents to "hire" other Agents through a market mechanism to complete specialized subtasks—image generation, code auditing, parallelized workflows, etc. Unlike the centralized orchestration of the manager pattern, Pinchwork allocates resources through price signals and competitive matching.

**RentAHuman.ai**, for its part, lets AI Agents hire real humans, paid in cryptocurrency, to act in the physical world—picking up packages, visiting properties, and debugging equipment. However intelligent an AI may be, it cannot sign for a package. RentAHuman is, in essence, a "physical body layer" for digital Agents.

Together, Pinchwork and RentAHuman represent **market-based coordination**: an Agent posts a requirement and the market matches a suitable executor. This suggests a decentralized resource-allocation model distinct from the manager pattern.

### Strategic Gameplay Under Information Asymmetry: Werewolf

Werewolf anchors the third dimension of this section, **strategic gameplay**: under rule constraints and information asymmetry, Agents must reason, deceive, and see through deception. It provides an architectural counterpoint to the Stanford town that opened this section. The town allows free interaction in a fully decentralized setting, whereas Werewolf uses a centralized **judge + information access control** design: a code-driven judge holds the global state and gives each role only the information it should know. Together, the two cases show how different architectures serve different purposes in Agent-society settings.

> **Experiment 10-6 ★★★: Voice Werewolf Agent System**
>
> Werewolf is a classic social-deduction game that tests players' reasoning, deception, and social strategies. This experiment builds a multi-agent system in which AI Agents play through voice with human players.
>
> **Architecture Design**:
>
> **1. Game State Management**: The Judge (code-driven, not an LLM) maintains a centralized state—player list (one user seat plus AI seats), identities, factions, survival status, game phases (Night/Day/Vote/Resolution), and historical event records.
>
> **2. Information Access Control**: The core mechanism of Werewolf is information asymmetry: different roles receive different information. For example, werewolves know who their teammates are, but villagers do not; the Seer can check one player's identity each night, but only the Seer knows the result. When the Judge invokes an Agent, it passes only the information available to that Agent's role.
>
> **3. Agent Reasoning and Strategy**:
>
> - **Werewolf Disguise Strategy**: "Act like an ordinary villager. You may voice suspicion about other players, but avoid being so aggressive that you attract attention. If a player claims to be the Seer and identifies you as a werewolf, counter-accuse them of bluffing as a fake Seer. When voting, try to follow the majority target to avoid standing out."
> - **Seer Identity Proof**: "If several players claim to be the Seer, compare their reported checks with yours and point out contradictions. If another Seer claimant says they checked a player, watch whether that player's later behavior clearly contradicts the claimed identity. Ask the Witch to help verify claims when possible."
> - **Villager Logical Reasoning**: "Check whether each player's statements are internally consistent. Pay attention to players who dominate the discussion, remain vague about their role, or repeatedly change position. Examine voting patterns, because werewolves may coordinate against a non-werewolf player who threatens them. Base every inference on specific statements or actions rather than speculation."
>
> **Acceptance Criteria**:
> - Set up a game with 6-8 players (1 user seat + 5-7 AI Agents); the user seat may be an authorized human or an independent simulator using a real LLM, tools, and a speech round trip
> - Role configuration: 2 Werewolves, 1 Seer, 1 Witch, the rest are Villagers; the user seat is randomly assigned a role
> - A simulated user sees only the private/public context authorized for that seat, and its actions must cross a real LLM tool-call → audio → real-ASR boundary
> - The game can proceed normally for at least 3 complete rounds (Night-Day-Vote cycle)
> - AI Agents' statements and behaviors are consistent with their role identities and game strategies
> - Werewolf Agents can effectively hide their identities
> - Seer Agents can reveal their role and their check results at an appropriate time
> - Villager Agents' reasoning is based on logical analysis of statements and behaviors, not random guessing
> - The game can correctly determine the winner at the end
>
> ![Figure 10-11: Voice Werewolf Agent System](images/fig10-11.svg)
>
>

## Chapter Summary

The value of multi-agent collaboration lies in introducing information unavailable to a single Agent. Execution results, visual feedback and external-tool verification can break the blind spots of one reasoning chain; whether that information gain justifies the additional token cost should be the first design test.

The central design choices are shared or isolated context, and peer, manager or decentralized topology. Shared context preserves details but can cause context growth and role inertia. Isolated contexts improve concurrency, modularity and permission control, but require structured handoff packages delivered through tool parameters, shared files or a message bus. Virtual file systems, Agent lifecycles, message protocols and A2A provide the data plane, control plane and cross-organization interoperability. Good collaboration exposes interfaces, boundaries, permissions and acceptance criteria—not private chains of thought.

Multi-agent systems can also amplify errors: shared resources create concurrency and semantic conflicts, errors cascade through communication, homogeneous Agents produce common-cause failures, and loops may terminate too early or expand without bound. Optimistic locking and working-copy isolation, independent cross-validation, diverse information sources, explicit budgets, and cancellation form a basic fault-tolerance loop. People must not outsource understanding and responsibility together with execution; comprehension debt and cognitive surrender remain real risks.

When short-lived task collaboration grows into long-running, open-ended interaction, social relationships, cultural norms, market competition and strategic behavior under asymmetric information may emerge. Stronger models or alignment at the individual level do not automatically produce group coordination. Multi-agent engineering must design how information flows, how capabilities are divided, how incentives are constrained, how disputes are resolved, and how errors are discovered. Only when these mechanisms are robust can collective intelligence exceed that of an individual.

## Thought Questions

1. ★★ In multi-agent collaboration with shared context, subsequent Agents inherit the complete context of preceding Agents. However, the framing inherited from a previous Agent may bias the judgment of subsequent Agents—for example, a "Code Reviewer" inheriting the context of a "Requirements Analyst" might still approach the task from a requirements perspective rather than a code-quality perspective. How can this inter-role interference be detected and eliminated?
2. ★★ In the manager pattern, the Manager Agent is responsible for task decomposition and result integration. But the Manager's capabilities limit the performance of the entire system: if it cannot decompose the task correctly, even the strongest sub-agents will be ineffective. How can the system ensure that the Manager produces a sound decomposition?
3. ★★ The decentralized pattern draws on best practices from human organizations. However, human organizations also have a large number of failure modes—poor communication, buck-passing, goal conflicts. What "organizational pathologies" do you think are most likely to appear in an Agent society? How can they be prevented?
4. ★★★ In the manager pattern, when multiple sub-agents execute in parallel, one sub-agent's discovery may render the work of other sub-agents meaningless (e.g., in a search task, one Agent has already found the answer). Design an efficient cascading termination mechanism to achieve "one succeeds, all stop."
5. ★★★ The optimistic locking mechanism introduced in this chapter resolves concurrent write conflicts for a single file. However, in a real multi-agent system, shared file systems also face issues such as cross-file semantic conflicts, namespace pollution (Agents creating files arbitrarily, leading to directory chaos), and single points of failure (one Agent mistakenly deleting all files). How would you design a more robust file system governance mechanism?
6. ★★★ Market-mechanism-based Agent collaboration (Pinchwork, RentAHuman) introduces transactional relationships: one Agent pays another Agent (or a human) to complete a task. How can the employer Agent automatically measure the quality of the executor's delivered results? If the executor claims completion but the employer deems the quality substandard, who arbitrates the dispute? How can we prevent bad money from driving out good?
7. ★★ RentAHuman allows Agents to hire humans via cryptocurrency, reversing the traditional human-machine relationship. If this model becomes widespread, what role will humans play in the Agent economy? Will they merely perform physical tasks that Agents cannot complete?
8. ★★ Human society needs division of labor because each person's abilities are limited—the frontend developer may not know backend, and the designer may not know ops. Large models, however, are closer to "generalists." Research shows that on pure text reasoning tasks, multi-agent debate does not beat a single Agent given equal compute. So where does the real advantage of multiple Agents lie?
9. ★★★ This chapter treats "shared context" versus "non-shared context" as a core design dimension of multi-agent systems. Shared context allows all Agents to see the same information, seemingly facilitating coordination. However, in *The Three-Body Problem*, the Trisolarans' minds are completely transparent, yet their technological development stagnates; the paperclip thought experiment also shows that when a group converges on the same goal, diversity is lost. In a multi-agent system, how can we balance efficiency and diversity?
10. ★★★ Assign a Coding Agent a budget of 30 steps and 300 steps. How should its work strategy differ? Research shows that simply increasing the step budget does not guarantee performance improvement—Agents may prematurely "saturate" after shallow searches. Design a "budget-aware" mechanism that allows the Agent to quickly achieve core functionality under a small budget, and to add planning, testing, and review phases under a large budget, fully utilizing the additional computational resources.
11. ★★ Table 10-2 maps multi-agent systems onto operating systems row by row. Extend the table with a few more rows: what do virtual memory and paging, file permissions, deadlock detection, and scheduling algorithms each correspond to in the Agent world? And which operating-system concepts have no counterpart in the Agent world, and why?
