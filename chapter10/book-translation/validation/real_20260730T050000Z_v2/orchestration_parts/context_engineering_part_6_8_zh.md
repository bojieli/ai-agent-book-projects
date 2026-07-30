### Context Engineering [Part 6/8]

Put differently, attention gives the model strong retrieval-like access to existing tokens. Given a question, it can often pull relevant raw records out of thousands of tokens, making every forward pass resemble a lightweight form of Retrieval-Augmented Generation (RAG). What is missing is an automatic **distillation layer**. The context is not automatically counted, indexed, or summarized in place. Any conclusion *about* the content—how many items there are, whether a limit has been exceeded, how far along the task is—must be recomputed from the raw records when the model needs it. The cost of that recomputation rises with the amount of content accumulated in the context.

Consider a real-world scenario: an Agent needs to make phone calls to complete business tasks, and the system prompt requires calling each merchant no more than three times. But after calling three times, the Agent often miscounts how many times it has called, makes a fourth call, or even falls into a loop repeatedly calling the same number.

The problem is that the answer to "How many times have I called?" is not automatically distilled into an explicit fact. Instead, it remains scattered across raw call records in the KV Cache. Each time the model makes a decision, it must spend extra reasoning tokens to scan the context and recount, a process that is highly inefficient and error-prone.

When we directly include the repeat call count in the tool call result for each phone call (e.g., "This is the third call to this merchant"), the model can immediately recognize that the limit has been reached and stop calling, significantly reducing error rates.

The essence of this mechanism is **distilling implicit states scattered throughout the context into explicit knowledge that can be directly used**. Information in the raw trajectory is highly redundant—a large number of tokens contain only a small amount of key state information. The Agent Status Bar actively extracts these key states, presenting—at minimal additional token cost—information that would otherwise require scanning thousands of tokens.

In long-context scenarios, the model's attention resources are limited. As context length increases, the model must allocate attention across more candidate content, so key information may receive insufficient weight. In complex Agent trajectories, task goals and early constraints can be overwhelmed by later tool results. The model also tends to over-focus on recent context, creating "attention decay" for information located in the middle of the context.

The Agent Status Bar addresses this problem by deliberately placing key meta-information in a structured format at the end of the context. Because this information is close to the tokens the model is about to generate, it is more likely to receive attention. This is a form of attention steering through placement.

> **Experiment 2-7 ★★: Verifying the Effect of the Agent Status Bar via Attention Visualization**
>
> Based on the `attention_visualization` project, we designed a controlled experiment where a customer service Agent handles a refund request. The Agent has already called Xfinity 3 times, interspersed with web searches. The user asks: "Can you call them again to follow up?"
>
> **Control Group A (No Status Bar):** The context contains the complete trajectory but no aggregated status information. The heatmap shows widely dispersed attention, with distinct concentrations around the three phone-call records. The reasoning tokens show the model counting and tallying information from the raw records.
>
> **Control Group B (With Status Bar):** The following is appended at the end of the trajectory:
>
> ```xml
> <agent_status>
> Current State:
> - Tool call summary: 'phone_call' has been invoked 3 times (Xfinity: 3 times)
> - Constraint check: Maximum calls to Xfinity reached (3/3)
> </agent_status>
> ```
>
> Attention is highly concentrated on the status bar information. The reasoning process directly uses the already distilled information, no longer computing statistics from the raw data. For a small model like Qwen3-0.6B, Control Group A frequently violates the constraint and continues calling, while Control Group B consistently adheres to the constraint.

Experiment 2-7 is a small qualitative demonstration. To quantify the value and limits of this "precompute and access directly" approach, the author and collaborators evaluated it with a dedicated benchmark[^ch2-7]. This approach has a general name: **Context Distillation**. The Agent Status Bar is its most common form. The benchmark covered three types of tasks (counting, rule induction, state tracking), 11 models (from advanced APIs to a 2B model that can run on a laptop), and nearly 24,000 evaluations. The results are clear:

- **For weak models, a precomputed status bar recovers accuracy**—the weakest models saw accuracy gains of 40 to 54 percentage points, and on these tasks a local 2B model even matched a frontier model that had no status bar.
- **For strong models that already answer correctly, it improves efficiency**—the same status bar reduces the reasoning effort, latency, and cost per query by roughly an order of magnitude (reasoning tokens are cut by 80–90% or more).
- The most fundamental change is: without a status bar, the reasoning effort per query **grows continuously** as the context lengthens; with a status bar, it becomes **essentially constant**—no matter how long the context gets, the model reads those few status entries directly. This is the quantified version of the heatmap from Experiment 2-7: originally, attention spreads thinner as N increases; after adding the status bar, it locks firmly onto those fixed entries.

(As an aside, the status bar must be written as key-value pairs that can be located quickly, like `Clothes: 9 items (Pass 7, Defect 2)`, not as a paragraph of prose—the paper showed that writing the same status information in prose form yielded significantly worse results, because the model still has to read and parse the prose, essentially returning to the scanning problem.)

However, **how the precomputation is performed matters greatly**. The most important takeaways from this work are three directly actionable lessons:

**1. Maintain the status bar with code, not with an LLM.** It may seem natural to ask another LLM to read the history and summarize the status bar, but the experiment found that this performed poorly. A 20-line regular-expression function achieved ground-truth-level accuracy, whereas a frontier model that processed the full history in one batch produced many incorrect entries and reduced downstream accuracy below the no-status-bar baseline. Asking an LLM to summarize a long history in one pass merely moves the original context-scanning problem elsewhere. A viable alternative is to **use code whenever possible**; if an LLM is necessary, have it **extract items one by one and then aggregate them with code, rather than summarizing the entire history in a single pass**.

**2. Before deleting the original context, confirm that the status bar covers all questions that might be asked.** The status bar is a **lossy projection** of the original context: it only precomputes the dimensions you *anticipate* will be relevant. If the status bar is sufficient, as it is for tasks such as counting and state tracking, the original records can be deleted and only the status bar retained, saving many tokens. Performance can deteriorate sharply, however, when a question asks for information the status bar was not designed to capture. In the paper's extreme test, the status bar stored only counts for "pairwise combinations," while the question asked about "triple intersections." Retaining only the status bar caused accuracy to collapse, with Claude falling from 100% to 7.6%. A plausible but incomplete status bar can therefore become a "false authority" that confidently misleads the model. In practice, treat a new type of question like **a change to a database table schema**: either add the corresponding field to the status bar first or retain both the status bar and the original context. Some tasks, such as multi-hop reasoning across long passages of prose, cannot be captured by a clean structured summary. For these tasks, the status bar may save tokens, but it should not be expected to improve accuracy.

**3. Monitor the accuracy of the status bar as a first-line production metric.** The experiment produced a striking finding: **the model almost unconditionally trusts the status bar**. If it says "called 3 times," the model accepts that value without checking or recalculating it. This trust makes the status bar effective, but it also allows errors to flow **directly** into the final answer. The system tolerates modest inaccuracies: the benefits are largely preserved when values are off by less than about 10%. Larger errors, however, can make an incorrect status bar worse than having none. This also connects to the **status bar poisoning** risk discussed earlier. Status information should come from reliable observations of the real world and never from data sources that can be externally contaminated; otherwise, the instrument will report the wrong state and lead the model astray.

[^ch2-7]: Li, Bojie and Noah Shi. *Distill, Don't Retrieve: Inference-Time Context Distillation for LLM Agent Reasoning.* 2026. https://01.me/research/context-distillation

(The following is optional advanced material from current research. It can be skipped on first reading without affecting your understanding of how to use the status bar; the preceding mechanisms, evidence, and three lessons are sufficient to guide practice.)

The two principles above—distilling implicit state and steering attention—explain why the status bar works. A deeper point is that the status bar can **feed the model information it could not have inferred on its own**[^ch2-5].

We often describe two ways to make a model stronger at test time: **reason longer** (generate a longer chain of thought) and **sample more** (sample multiple answers and select the best). Both paths share the same limitation: they operate only within the model's internal computation, using fixed weights and fixed context. They **cannot create information that was not already present in the context**; they can only rearrange existing information. Interaction provides a third path. The model produces an output, an external instrument observes its real-world effect, and that observation is written back into the context. The observation may contain information the model **cannot infer through reasoning alone**: whether code passed the test, whether a rendered button overflowed the page, or what system state resulted from an operation. These facts come from execution and measurement, not from the weights or the existing context. (This research also found that the yardstick used to measure improvement must itself be grounded in real observations. If a visual model that only inspects a screenshot is used to score, it may fail to detect the defects it just fixed, causing the loop to make no real progress.)

The Agent Status Bar is the most common application of this principle. The Harness acts as the instrument: it observes runtime state (how many calls were made, the current time, task progress, whether a tool reported an error), compresses those observations into a short segment, and writes them back into the context. The most valuable part of the status bar is often not information the model could have counted by scanning the transcript, but **external facts it could not infer**. The status bar turns an isolated reasoning task into one grounded in real-world observations. This also gives a design principle: the more the status bar draws from real observations, the more valuable it is. Conversely, if the status summary is fabricated or comes from a data source that can be contaminated, the instrument will report the wrong state and mislead the model (this corresponds to the status bar poisoning risk discussed earlier).

[^ch2-5]: Li, Bojie and Noah Shi. *Interaction Scaling: Grounding the Third Axis of Test-Time Compute.* arXiv:2607.11598, 2026.

Seen from this perspective, the Loop Engineering introduced at the end of Chapter 1's evolutionary arc, and developed further in Chapter 10 alongside multi-agent collaboration systems, turns this third axis of interaction into engineering practice. Each iteration makes real progress only when verification writes observations of the external world back into the context. Without that step, the model merely rearranges existing information. Thus, the claim that "the verifier, not the model, is the bottleneck" and the finding that the measuring instrument must be grounded in real observations express the same principle.

### Composition of the Agent Status Bar

Based on the theoretical foundation above, the Agent Status Bar includes the following types of information:

**Task Planning**: When an Agent handles complex, multi-step tasks, the trajectory can become very long. The Agent tends to focus excessively on the current local sub-task, forgetting the user's original request, core constraints, and subsequent work. Placing a TODO list that breaks the task into clear steps at the end of the trajectory continually reminds the model of its current progress and future goals, helping align its actions with the overall plan.

**Side-channel Information for Events**: Attach metadata to each event—precise time, geographic location, time interval since the last Agent reply, etc. Side-channel information refers to auxiliary information not transmitted in the main data channel but helpful for understanding the event. This information helps the model understand the temporal relationships and environmental context of events, enabling more contextually appropriate decisions.

**Current Environment State**: Includes dynamic environment information (system time, working directory, etc.), abnormal operation alerts ("This tool has been called N times repeatedly"), and the transformation from implicit state to explicit state. This design principle also applies to human interfaces—both Command Line Interfaces (CLI) and Graphical User Interfaces (GUI) aim to let users clearly perceive the current state of the system.

**Available Capability List**: When the Agent framework supports plugin-based capability extensions (like the Skills system from the previous section), the metadata list of all installed Skills also goes through this same end-of-context injection channel. It tells the model which specialized capabilities are currently available. It changes infrequently (only when the user installs or uninstalls a Skill), and its incremental sending mechanism was detailed in the previous Skills section, so it will not be repeated here.

Side-channel information and the available capability list usually do not change after being added, making them cache-friendly because they do not invalidate the cached prefix. Task planning and environment state are dynamic and must be appended to the end of the context as special user messages, then updated as the task progresses. The update method directly affects KV Cache cost, as discussed below.

### Specific Position of the Agent Status Bar in the Context

![Figure 2-15: Insertion Position of the Agent Status Bar in the API Message List](images/fig2-15.svg)

An important implementation detail is that the Agent Status Bar is inserted at the end of the context as **a message with the `user` role** at the API level, rather than by modifying the initial `system` message. The reason is the KV Cache constraint discussed earlier: modifying the `system` message would invalidate the cache for the entire prefix. One point requires clarification: the `user` role here is a technical choice at the API protocol level and is not equivalent to "input from the end-user" as defined in Chapter 1. The Harness borrows the `user` role message slot to inject system state information generated by the Agent framework. The content does not come from a real user; it simply uses the `user` message format to attach state information to the end of the context.

Below is the actual message list constructed by the Agent framework during the Nth API call:

```
messages: [
  { role: "system",    content: "You are a customer service assistant..." }  ← Fixed (KV Cache cached)
  { role: "user",      content: "Help me cancel my Xfinity plan" }  ← Original user request
  { role: "assistant", content: null, tool_calls: [...] }   ← Round 1: model decides to call
  { role: "tool",      content: "Call log..." }             ← Round 1: call result
  { role: "assistant", content: null, tool_calls: [...] }   ← Round 2: model decides to call again
  { role: "tool",      content: "Call log..." }             ← Round 2: call result
  ...(more rounds)
  { role: "user",      content: "Can you call them again to follow up?" }  ← User follow-up
  { role: "user",      content: "<agent_status>             ← Status bar injected by Agent framework
      Current State:                                           (as a user message)
      - phone_call invoked 3 times (Xfinity: 3/3 max)
      - Current time: 2025-09-14 10:30:45
      - TODO: [1] Cancel plan (in_progress)
    </agent_status>" }
]
```

Note the last message: its `role` is `user`, but the content is meta-information automatically generated by the Agent framework, wrapped in `<agent_status>` tags so the model can recognize its special nature. This message sits at the very end of the context, immediately adjacent to the new tokens the model is about to generate, thus receiving the highest attention weight. At the same time, because it is appended rather than modified, all previously cached content remains unaffected.

This design applies the core principle from the KV Cache section to the status bar: append dynamic information at the end, and keep static information unchanged.

### Two Implementations of Status Updates and Their Cache Costs

"Appending does not break the cache" only holds for a single injection. Status naturally changes over time: TODO items are completed, tool counts increase, and previous status messages become outdated. There are two ways to update the status bar, each with different cache costs:

**Implementation 1: Replace each round.** Before each API call, remove the previous round's status message from the message list and append the latest status at the end. This keeps only one current status in the context. The cost is that removing the old status invalidates all cached content after its position, which is the same invalidation mechanism discussed in the "dynamic timestamp" section of this chapter. The difference is that because the status message is near the end of the context, the invalidation range is limited to the most recent few rounds of messages rather than the entire prefix.

**Implementation 2: Persistent appending.** Once injected, the status message remains permanently in the trajectory, and a new status is appended at the end each round. Claude Code's `<system-reminder>` uses this approach: historical status messages remain in the transcript and are never deleted or modified. This method is fully cache-friendly because messages are only appended, never changed, so the prefix remains stable. The cost is that outdated statuses accumulate in the context, consuming tokens and requiring the model to rely on the latest status while ignoring obsolete ones.