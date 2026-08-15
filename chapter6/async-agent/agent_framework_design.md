## Flux: An Event-Driven Framework for Asynchronous Agentic Workflows

**Abstract:** Flux is a software framework designed for building asynchronous and event-driven AI agents, with a strong emphasis on **enabling low-code development**. Drawing an analogy to a real human, Flux treats agents as entities whose state and understanding evolve based on their accumulating memory. Flux aims to empower users, **including those with limited programming experience**, to define complex agentic workflows primarily through **declarative configuration**, minimizing the need for writing extensive code. It supports persistent, per-user long-term memory, modular agent invocation, and seamless tool integration. Communication adheres to the Agent Messaging Protocol (AMP). Key features include asynchronous execution, optional synchronous tools, interrupt handling, streaming outputs, and a developer experience focused on ease of use and configuration over complex coding.

### 1. Introduction

Modern AI applications require agents capable of complex, stateful, and collaborative interactions. Flux addresses this need with an asynchronous, event-driven architecture inspired by human cognition and OS principles. Crucially, Flux is designed to **democratize agent development**. Instead of requiring deep programming expertise, it focuses on allowing developers to define agent behavior, logic, and workflows through **intuitive configuration files and well-defined prompts**. The goal is to provide a robust platform where the core complexity of asynchronous processing, state management, and communication is handled by the framework, freeing developers to concentrate on the agent's specific goals and capabilities.

Flux models an agent like a human, processing inputs, thinking internally, acting externally, and handling interruptions, all recorded in its memory. It supports both rollout-specific working memory (trajectory) and user-specific long-term memory. By leveraging LLMs for decision-making based on this memory and providing a **configuration-driven approach** to defining agents and tools, Flux facilitates the creation of sophisticated agents without demanding extensive coding skills, making agentic AI development more accessible.

### 2. Core Concepts

*   **Agent:** An agent is an autonomous computational entity, analogous to a real human expert or assistant. It possesses a defined set of capabilities (tools/skills), operates based on internal logic (primarily LLM-driven decision-making informed by its memory), and interacts with its environment through events within the scope of an **AMP Session**. An agent's understanding and state within a specific rollout are derived from its accumulated **trajectory**. It can also access and modify **User Long-Term Memory** to inform its behavior based on past interactions with a specific user. Each agent definition serves as a blueprint.
*   **Rollout:** A rollout represents a specific, running instance of an agent executing its defined logic within the context of an **AMP Session**. It is typically initiated by an event within that session (e.g., a user message, an agent invocation). Each rollout maintains its own independent **trajectory** and lifecycle state. Importantly, a single AMP Session can contain multiple participants (users and agents), and thus may involve multiple concurrent Flux Rollouts (one for each active agent participant in the session).
*   **Event:** The fundamental unit representing any occurrence relevant to a rollout, forming the building blocks of the agent's **trajectory**. All interactions, internal processing steps, and external stimuli within the rollout's scope are captured as events, appended chronologically to the rollout's trajectory. Drawing inspiration from OS process states and signals, events are categorized as Inputs, Interrupts, Thinking, and Actions:
    *   **Inputs:** Events originating externally to the agent's rollout, akin to sensory perception within the session.
        *   `user.input`: Messages or actions from a specific human user *within the current AMP session*.
        *   `agent.input`: Messages or results received from another invoked agent rollout *within the same AMP session*.
        *   `tool.result`: Data returned from a completed tool execution (sync or async), including results from memory access tools.
        *   `external.trigger`: Events from outside systems integrated with the framework (e.g., API webhook, database change, new social media post), potentially associated with the session or a user.
    *   **Interrupts:** Events that signal a need to alter or halt the current flow of execution within the rollout, often requiring immediate attention.
        *   `supervisor.instruction`: Commands from an administrative system or human supervisor pertaining to this rollout or session.
        *   `user.interrupt`: User actions (from a specific user in the session) like clicking a 'stop' button or explicitly cancelling an operation related to this rollout.
        *   `timer.trigger`: An event fired by a previously set timer associated with this rollout.
    *   **Thinking:** Events representing the agent's internal cognitive processes or state changes within the rollout.
        *   `agent.thought`: Internal reasoning steps, intermediate conclusions, or state changes logged by the agent for transparency or future context within its trajectory.
    *   **Actions:** Events representing the agent's decisions to interact with or affect the external world (including other participants in the session or external systems) or schedule future events for this rollout.
        *   `agent.output`: Messages or data prepared to be sent to a specific user (or all users) *within the current AMP session* (mediated via a tool call adhering to AMP).
        *   `agent.escalation`: A request sent to a supervisor system regarding this rollout or session.
        *   `tool.request`: An invocation request for an external tool, which might include tools for accessing/updating **User Long-Term Memory**.
        *   `agent.invocation`: A request to create and start a new rollout for another agent *within the same AMP session*, initiating collaboration.
        *   `agent.response`: A message sent back to the agent rollout that invoked the current one *within the same AMP session*.
        *   `agent.interrupt`: A signal sent to interrupt another specific agent rollout *within the same AMP session*.
        *   `timer.set`: An instruction to the framework to schedule a `timer.trigger` event for the future for this specific rollout.
*   **Trajectory:** The complete, time-ordered, immutable sequence of all events (Inputs, Interrupts, Thinking, and Actions) associated with a *specific rollout*. This **is** the agent's working memory for that rollout. It provides the primary context required by the LLM to understand the rollout's immediate history, its own past reasoning and actions *within that rollout*, and make informed decisions about the next thinking steps or actions for that rollout.
*   **User Long-Term Memory:** A persistent, key-value store associated with a unique user ID. This memory exists *across* different rollouts (AMP Sessions) involving that user. It's designed to hold relatively stable information like user preferences, summarized past interactions, contact details, or accumulated knowledge about the user relevant for personalization and continuity. Agents access and modify this memory explicitly via designated **Actions** (e.g., specific `tool.request` events). This is distinct from the rollout-specific trajectory.
*   **Rollout Business State:** (Optional) A developer-defined state representing the current logical phase or status of the rollout from the perspective of the agent's business logic (e.g., `needs_clarification`, `processing_request`, `waiting_for_payment`, `request_completed`). This is distinct from the framework's internal rollout lifecycle state (`running`, `waiting`) and complements the trajectory by providing a high-level summary of the rollout's progress according to the developer's intended workflow.
*   **Workflow:** A definition specifying the entry point agent and potential interactions. In Flux, workflows can be:
    *   **Emergent (Low-Code Default):** Driven primarily by the LLM's decisions based on memory and available tools. This approach typically requires **minimal explicit workflow configuration**, relying on the LLM's reasoning capabilities guided by prompts.
    *   **State-Guided (Optional/Advanced):** Influenced by developer-defined **Rollout Business States**. This offers more explicit control for complex scenarios but requires more configuration.

### 3. Architecture

Flux employs a modular architecture centered around asynchronous event processing within the context of AMP Sessions:

*   **Rollout Manager:** Responsible for creating, tracking, and terminating agent rollouts, associating them with their corresponding AMP Session and participant ID. It assigns unique IDs to rollouts and manages their lifecycle state.
*   **Event Queue (per Rollout):** Each active rollout has an associated event queue where incoming events (Inputs, Interrupts) relevant to that agent's role in the session are placed.
*   **Agent Runtime:** The core execution engine for a single rollout. It comprises:
    *   **Event Processor:** Dequeues events, appends them to the rollout's trajectory, and determines if an LLM invocation is needed.
    *   **LLM Invoker:**
        *   Formats the rollout's current trajectory into the structure expected by the configured LLM. Optionally includes the current **Rollout Business State**. May also optionally include relevant excerpts from **User Long-Term Memory** (retrieved via a previous Action or potentially through automatic framework injection based on configuration).
        *   Constructs the final prompt using the agent's system prompt, the formatted trajectory, and the user prompt template.
        *   Invokes the configured LLM API.
        *   Parses the LLM's response (Thinking/Action events), handling streaming for incremental processing.
    *   **Tool Executor:**
        *   Receives Action events (`tool.request`, `agent.invocation`, `agent.output`, `update_rollout_state`, etc.).
        *   Manages the execution of these actions, interacting with external tools, other agents within the session, the Communication Layer, potentially a **Long-Term Memory Service**, and updating the **Rollout Business State** if requested.
        *   Handles async/sync execution logic and cancellation.
        *   Generates corresponding Input events (`tool.result`, `agent.input`, `timer.trigger`) and places them back into the appropriate rollout's Event Queue.
    *   **Communication Layer:** Handles external communication via the AMP specification for the session. Translates incoming AMP messages/requests (addressed to the agent this rollout represents) into Flux Input/Interrupt events for the rollout. Translates agent Action events (`agent.output`) into outgoing AMP messages/streams targeted at the correct participants within the session. Manages SSE connections.

### 4. Agent Definition

Agents are defined declaratively, primarily through **configuration files (e.g., YAML, JSON)**, aligning with the low-code philosophy. An agent definition typically includes:

*   **Identifier:** Unique name/ID.
*   **System Prompt:** Defines persona, goals, constraints. **A key area for defining agent logic without code.**
*   **User Prompt Template:** Structures the prompt, potentially including placeholders for Rollout Business State. **Another key configuration point.**
*   **Model Configuration:** LLM choice and parameters (simple configuration).
*   **Tool Registry:** Lists available tools/agents. Referencing existing tools/agents is a simple configuration entry. Defining *new* tools may require code, but the framework provides clear interfaces and registration mechanisms to simplify this.
    *   Standard external tools.
    *   Memory tools (access/update can be explicit tool calls or potentially configured implicit actions, offering flexibility).
    *   References to other registered Flux agents.
    *   (Optional) Action for updating Rollout Business State (`update_rollout_state`).
*   **State Machine Definition (Advanced/Optional):** For agents requiring very specific, complex state management, developers *can* define explicit states and transitions. **This is not required for typical agents**, where state can be managed implicitly through the trajectory or LLM reasoning.
*   **Context Inheritance Policy (Advanced/Optional):** Configuration for how much context is passed to invoked agents. **Simple defaults are provided**, and explicit configuration is only needed for specialized use cases.
*   **Workflow Specification (Optional):** Can define entry points. More complex workflow logic is often better embedded within the system prompt or handled via the optional state mechanism, rather than requiring complex external workflow definitions.

**Core agent logic often resides within the prompts and the LLM's inherent capabilities, configured declaratively, rather than in complex code within the framework.**

### 5. Event Processing and LLM Interaction

The core loop for an active rollout:

1.  **Event Dequeue:** Get the next event for this rollout.
2.  **Memory Update:** Append the event to the trajectory.
3.  **LLM Trigger Check:** Decide if LLM processing is needed.
4.  **Context Formatting:** Translate trajectory into LLM format. Include the current **Rollout Business State** if defined. Optionally include retrieved **User Long-Term Memory** data (via explicit tool result or automatic injection).
5.  **LLM Invocation:** Send context and prompts to the LLM.
6.  **Response Parsing & Streaming:** Parse LLM response into Thinking/Action events.
7.  **Thinking/Action Generation & Internal State Update:** Add generated Thinking and Action events to the trajectory. If the LLM generated an `update_rollout_state` action, the Agent Runtime immediately processes it here, updating the rollout's current business state field.
8.  **Dispatch Actions to Executor:** Send all other generated Action events (those requiring interaction with external tools, other agents, the communication layer, timers, etc. – e.g., `tool.request`, `agent.invocation`, `agent.output`, `timer.set`) to the Tool Executor for handling.
9.  **Loop/Wait:** Wait for the next event.

#### 5.1 Event Processing Mechanisms

Flux supports two dynamic event processing strategies for handling events in a rollout. The framework automatically selects the appropriate mechanism based on the urgency of the incoming event:

1. **Cancellation-Based Processing:** When an urgent event arrives (e.g., user interrupts, high-priority inputs), the framework immediately stops the current LLM thinking or any synchronous tool call. All queued events in the pending queue along with the new urgent event are immediately appended to the trajectory. The LLM is then invoked with the complete updated trajectory to process all accumulated events together. This approach ensures that urgent, potentially invalidating events receive immediate attention and the agent can make decisions with the most critical, up-to-date information.

2. **Queued Processing:** When a non-urgent event arrives, it is queued at the end of the pending queue without interrupting ongoing processing. When any tool call (synchronous or asynchronous) of the agent completes and returns a `tool.result` event, the framework checks the pending queue before invoking the LLM. If there are pending events, all events in the pending queue are immediately moved to the end of the trajectory, and then the LLM is invoked to process the updated trajectory. This approach allows the agent to complete ongoing operations while efficiently batching non-urgent events, balancing responsiveness with computational efficiency.

**Urgency Determination:** The framework classifies events based on their type and context:
- **Urgent events:** User interrupts (`user.interrupt`), supervisor instructions (`supervisor.instruction`), explicit agent interrupts (`agent.interrupt`), and time-critical external triggers marked as urgent.
- **Non-urgent events:** Regular user inputs (`user.input`), agent messages (`agent.input`), tool results (`tool.result`), timer triggers (`timer.trigger`), and standard external triggers.

This dynamic selection ensures optimal responsiveness for critical events while maintaining efficiency for routine operations.

### 6. Tool Execution

Tools are fundamental.

*   **Definition:** Tools have a clear definition structure (name, description, parameters). Defining *new* tools involves implementing a defined interface, but *using* existing tools is purely configuration.
*   **Invocation:** Triggered by LLM via `tool.request` action based on prompt and available tools.
*   **Memory Tools:** Framework aims to provide flexible options (explicit call vs. implicit action) configurable by the developer.
*   **Execution:** Asynchronous/synchronous handling is managed by the framework, abstracted from the developer defining the agent.
*   **Results:** Fed back as events, handled by the framework.
*   **Cancellation:** Framework provides the mechanism.

### 7. Inter-Agent Communication (Actor Model within AMP Session)

Flux implements actor model principles constrained within an AMP Session:

*   **Invocation:** `Agent A` (Rollout A) invokes `Agent B` by generating an `agent.invocation` action. The Rollout Manager creates Rollout B for Agent B *within the same AMP Session*. Rollout B's initial event is the invocation details from Rollout A.
*   **Communication:** Rollout B can send results/messages back to Rollout A using `agent.response` actions, which arrive as `agent.input` events at Rollout A. Rollout B can also send messages directly to users in the session via `agent.output` actions, handled by the Communication Layer. All communication is asynchronous and potentially streaming via AMP.
*   **Context Sharing:** Simple defaults are provided. Explicit configuration of context sharing is an advanced option.

### 8. State Management

Flux manages state layers, abstracting complexity:

*   **Framework Rollout State:** Internal framework state.
*   **Trajectory:** Automatically maintained log.
*   **User Long-Term Memory:** Accessed via configured tools or actions.
*   **Developer-Defined Rollout Business State (Optional):** A straightforward key-value state field developers can optionally use and manage via configuration and LLM actions for more explicit control when needed.
*   **LLM Context:** Assembled automatically by the framework based on configuration and state.

### 9. Streaming and Communication Protocol

*   **AMP Adherence:** Handled by the framework's Communication Layer.
*   **Input/Output Mapping:** Handled by the framework.
*   **Streaming LLM Output:** Handled by the framework.

### 10. Developer Experience

Flux is fundamentally designed for **ease of use and low-code agent development**: 

*   **Declarative First:** The primary way to define agents, their logic (via prompts), tool usage, and basic workflows is through **declarative configuration files** (e.g., YAML, JSON), not procedural code.
*   **Abstraction:** The complexities of asynchronous execution, event loops, state persistence, AMP communication, and streaming are **handled internally by the framework**, allowing developers to focus on *what* the agent should do, not *how* the underlying machinery works.
*   **Configuration over Code:** Core agent behavior, personality, and decision-making logic are primarily defined in system prompts and by selecting available tools in the configuration.
*   **Simplified Tooling:** While new tools require some code, the framework provides clear interfaces. A library of pre-built common tools (including memory access) further reduces the need for coding.
*   **Emergent Workflows:** Simple agents can often function effectively by letting the LLM decide the next steps based on the trajectory and available tools, requiring minimal explicit workflow definition.
*   **Optional Complexity:** Features like explicit Rollout Business States and detailed Context Inheritance policies are available for advanced users needing fine-grained control, but are **not required** for basic agent development.
*   **Observability:** Clear logging and tracing mechanisms are provided to understand agent behavior without needing to debug complex framework internals.
*   **(Future) Visual Tools:** The declarative nature of Flux lends itself well to potential future development of GUI or visual flowcharting tools for defining agents and workflows, further enhancing accessibility.

### 11. Conclusion

Flux offers a robust, event-driven architecture designed for building sophisticated asynchronous AI agents while prioritizing **low-code development and accessibility**. By abstracting framework complexities and enabling agent definition primarily through **declarative configuration and prompting**, Flux empowers a wider range of developers, including those with limited coding experience, to create powerful agentic solutions. Its support for multiple memory types, modularity, adherence to AMP, and focus on a simplified developer experience makes it a strong foundation for building the next generation of collaborative and stateful AI applications.
