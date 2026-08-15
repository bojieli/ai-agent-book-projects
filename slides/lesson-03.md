---
theme: seriph
title: "Chapter 1 · Lesson 2 — What Is Inside an Agent's Context?"
info: "English video course for AI Agents in Depth"
author: Bojie Li
transition: slide-left
mdc: true
lineNumbers: false
monaco: false
aspectRatio: 16/9
canvasWidth: 980
layout: cover
class: chapter-formula-cover
---

<div class="chapter-kicker">BUILD · CHAPTER 1 · AGENT FUNDAMENTALS</div>

# What Is Inside an Agent's Context?

<div class="chapter-context-equation mt-6">
  <div class="chapter-context-group blue"><strong>Static prefix</strong><span>System prompt</span><span>Tool definitions</span></div>
  <div class="chapter-equation-sign">+</div>
  <div class="chapter-context-group green"><strong>Trajectory</strong><span>User messages</span><span>Assistant messages</span><span>Tool results</span></div>
</div>

<div class="chapter-cover-thesis">Every model call sees the prefix plus the trajectory accumulated so far.</div>

<div class="chapter-cover-footer"><span>Bojie Li · AI Agents in Depth</span><span>Course Lesson 03 of 42 · 19 minutes</span></div>

<!-- Presenter cue: Introduce the chapter thesis through the formula; the slide already carries the factual structure. -->

---
class: chapter-dense
---

# Context Is the Agent's Working Set—not Its Entire Memory

<div class="chapter-lead">Context is the information available to the Agent at one decision point: the task instructions, relevant references, earlier correspondence, current state, and the latest tool observations.</div>

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="chapter-panel blue">
<h3>What enters the working set</h3>
<ul>
<li>The system prompt and stable rules.</li>
<li>Definitions of tools currently available.</li>
<li>User input and retrieved external knowledge.</li>
<li>Earlier assistant decisions and actions.</li>
<li>Results returned by the environment.</li>
</ul>
</div>
<div class="chapter-panel orange">
<h3>What the model cannot use directly</h3>
<ul>
<li>State retained only inside application code.</li>
<li>A tool implementation whose definition was not supplied.</li>
<li>An execution result that was never appended.</li>
<li>A previous turn removed during compression.</li>
<li>Relevant knowledge that retrieval did not surface.</li>
</ul>
</div>
</div>

<div class="chapter-thesis-line mt-5">The Agent can decide only from information present at decision time—even if the missing fact exists elsewhere in the system.</div>

<!-- Presenter cue: Distinguish persistent storage from the smaller working set exposed on the current call. -->

---
class: chapter-dense
---

# The API-Level Context Has Five Components

<table class="chapter-table chapter-table-compact mt-3">
<thead><tr><th>Component</th><th>Who supplies it</th><th>What it carries</th><th>Failure if absent</th></tr></thead>
<tbody>
<tr><td><strong>System prompt</strong></td><td>Developer / framework</td><td>Identity, permissions, conduct, memory, injected state</td><td>No stable role or behavioral boundary</td></tr>
<tr><td><strong>Tool definitions</strong></td><td>Developer / provider</td><td>Names, descriptions, parameters, formats</td><td>The model cannot recognize or call the tool</td></tr>
<tr><td><strong>User messages</strong></td><td>User + retrieval layer</td><td>Request and dynamically retrieved knowledge</td><td>The current goal or required evidence is missing</td></tr>
<tr><td><strong>Assistant messages</strong></td><td>Model</td><td>Reasoning, user-facing content, tool calls</td><td>Prior decisions and proposed actions disappear</td></tr>
<tr><td><strong>Tool results</strong></td><td>Environment / Harness</td><td>Execution feedback and new observations</td><td>The Agent acts without knowing what happened</td></tr>
</tbody>
</table>

<div class="chapter-callout blue mt-4"><strong>Experiment 1-1 tests four removals.</strong> The system prompt is exempt because without a basic identity definition the test no longer represents the same Agent.</div>

<!-- Presenter cue: Use the failure column to make each component operational rather than definitional. -->

---
class: chapter-dense
---

# Static Prefix + Dynamic Trajectory

<div class="chapter-prefix-flow mt-5">
<div class="chapter-prefix-block blue">
<strong>Static prefix</strong>
<span>System prompt</span>
<span>Tool definitions</span>
<small>Stable across calls; cache-friendly</small>
</div>
<div class="chapter-plus">+</div>
<div class="chapter-prefix-block green wide">
<strong>Trajectory</strong>
<span>User → assistant reasoning/tool calls → tool results → assistant…</span>
<small>Grows after every interaction with the environment</small>
</div>
<div class="chapter-equals">=</div>
<div class="chapter-prefix-block purple">
<strong>Next LLM input</strong>
<span>Everything visible at this decision point</span>
</div>
</div>

<div class="grid grid-cols-2 gap-5 mt-6">
<div class="chapter-callout green"><strong>Why retain the trajectory?</strong> It records completed work, unresolved questions, decisions, tool arguments, observations, and progress.</div>
<div class="chapter-callout orange"><strong>Why not retain everything forever?</strong> The prompt grows, cost rises, irrelevant history competes for attention, and retrieval becomes harder.</div>
</div>

<!-- Presenter cue: Establish the exact equation that the next slides and experiment will probe. -->

---
class: chapter-dense
---

# An Assistant Message Can Carry Thought, Speech, and Action

<div class="grid grid-cols-2 gap-5 mt-3">
<div>
<pre class="chapter-code-block tall" v-pre><code>{
  "role": "assistant",
  "reasoning": "Need EUR, GBP, and JPY rates…",
  "content": "",
  "tool_calls": [
    {"name": "convert_currency",
     "arguments": {"amount": 2100000,
                   "from": "EUR", "to": "USD"}}
  ]
}</code></pre>
</div>
<div>
<div class="chapter-panel purple"><h3>Reasoning</h3><p>Preserves why the previous decision was made and supports coherence across steps.</p></div>
<div class="chapter-panel blue mt-3"><h3>Content</h3><p>Communicates with the user; often empty while the Agent is still acting.</p></div>
<div class="chapter-panel green mt-3"><h3>Tool calls</h3><p>Structured proposals for changing or observing the external environment.</p></div>
</div>
</div>

<div class="chapter-callout orange mt-3"><strong>The tool result is a separate message.</strong> The framework executes the proposal and appends the observation under the matching tool-call ID.</div>

<!-- Presenter cue: Point out that the three fields need not appear together on every assistant response. -->

---
class: chapter-dense
---

# Experiment 1-1 Removes One Information Channel at a Time

<div class="grid grid-cols-5 gap-5 mt-2 items-center">
<div class="col-span-3">
<img class="chapter-figure-large" src="/images/fig1-2.svg" alt="Experiment 1-1 context ablation design">
</div>
<div class="col-span-2">
<h3>Canonical task</h3>
<p class="chapter-small">Convert quarterly revenue in USD, EUR, GBP, and JPY into USD, then calculate the annual total and quarterly average without estimating exchange rates.</p>
<h3 class="mt-3">Control</h3>
<p class="chapter-small">The full arm keeps all five components and should complete in a small number of iterations.</p>
<h3 class="mt-3">Ablations</h3>
<p class="chapter-small">Remove tool definitions, tool results, retained reasoning, or message history while holding the task and model constant.</p>
</div>
</div>

<div class="chapter-thesis-line mt-3">Ablation is diagnostic: different missing components should create different, observable failure signatures.</div>

<!-- Presenter cue: Define the controlled comparison before showing expected or observed behavior. -->

---
class: chapter-dense
---

# What Should Break When Each Component Disappears?

<table class="chapter-table chapter-table-roomy mt-4">
<thead><tr><th>Arm</th><th>Actual request change</th><th>Predicted signature from the chapter</th><th>Disconfirming observation</th></tr></thead>
<tbody>
<tr><td><strong>Full</strong></td><td>No removal</td><td>Correct answer with a coherent sequence</td><td>Wrong answer, unnecessary repetition, or no completion</td></tr>
<tr><td><strong>No tool definitions</strong></td><td>Omit <code>tools</code> and <code>tool_choice</code></td><td>No tool action is possible</td><td>The model successfully invokes an undeclared tool</td></tr>
<tr><td><strong>No tool results</strong></td><td>Replace every observation with a hidden marker</td><td>Repeated calls or unsupported conclusions</td><td>Correct answer derived only from hidden observations</td></tr>
<tr><td><strong>No reasoning</strong></td><td>Remove prior reasoning from history</td><td>Less coherent or contradictory decisions</td><td>No measurable degradation on the tested task</td></tr>
<tr><td><strong>No history</strong></td><td>Send only system + current user each round</td><td>Restarting and repeated operations</td><td>The Agent remembers completed work anyway</td></tr>
</tbody>
</table>

<div class="chapter-callout purple mt-4"><strong>Important:</strong> the runner verifies the request contract itself—what the provider actually received—not merely the CLI mode name.</div>

<!-- Presenter cue: State predictions in falsifiable form; the no-reasoning result will matter later. -->

---
class: chapter-dense
---

# ReAct Connects Context, Model, and Tools

<div class="grid grid-cols-5 gap-5 mt-2 items-center">
<div class="col-span-3">
<img class="chapter-figure-large" src="/images/fig1-5.svg" alt="Execution loop of an autonomous Agent">
</div>
<div class="col-span-2">
<div class="chapter-panel purple"><h3>Reason</h3><p>Given the complete current context, decide what information or action is needed next.</p></div>
<div class="chapter-panel orange mt-3"><h3>Act</h3><p>Emit a structured tool call; the Harness executes it outside the model.</p></div>
<div class="chapter-panel green mt-3"><h3>Observe</h3><p>Append the result, creating a richer context for the next call.</p></div>
</div>
</div>

<div class="chapter-callout red mt-3"><strong>A loop also needs exit conditions:</strong> task complete, final-output tool called, no tool call, unrecoverable error, or maximum rounds reached.</div>

<!-- Presenter cue: Explain why the name ReAct omits observation even though observation is operationally indispensable. -->

---
class: chapter-dense
---

# Every Round Sees the Entire Trajectory So Far

<img class="chapter-figure-wide mt-1" src="/images/fig1-3.svg" alt="ReAct trajectory for multi-currency revenue aggregation">

<div class="grid grid-cols-3 gap-4 mt-3">
<div class="chapter-mini blue"><strong>Round 1</strong><span>Reason about missing exchange rates; call currency tools in parallel.</span></div>
<div class="chapter-mini green"><strong>Round 2</strong><span>Observe conversions; call the code interpreter to aggregate.</span></div>
<div class="chapter-mini purple"><strong>Round 3</strong><span>Observe the calculation; return total and quarterly average.</span></div>
</div>

<div class="chapter-thesis-line mt-3">The trajectory is the dynamic part of the next prompt, not a log consulted after execution.</div>

<!-- Presenter cue: Trace one item from action to observation to the next decision. -->

---
class: chapter-dense
---

# The Revenue Task Completes in 3 Iterations and 4 Tool Calls

<div class="grid grid-cols-2 gap-5 mt-3">
<div>
<pre class="chapter-code-block tall" v-pre><code>trajectory = [
  user("Q1 $2.5M, Q2 €2.1M, Q3 £1.8M, Q4 ¥380M"),
  assistant(
    reasoning="Convert non-USD quarters first",
    tool_calls=[eur_to_usd, gbp_to_usd, jpy_to_usd]),
  tool(eur_result), tool(gbp_result), tool(jpy_result),
  assistant(
    reasoning="Aggregate verified USD values",
    tool_calls=[code_interpreter(total_and_average)]),
  tool("Total $9,602,895.73; average $2,400,723.93"),
  assistant(content="FINAL ANSWER …"),
]</code></pre>
</div>
<div>
<h3>Why accumulation matters</h3>
<ol class="chapter-tight-list">
<li>The second call knows which conversions were requested.</li>
<li>It sees the returned rates rather than inventing them.</li>
<li>The third call sees the calculation result and knows the task is complete.</li>
<li>Structured roles keep proposals and observations distinguishable.</li>
</ol>
<div class="chapter-callout orange mt-4"><strong>Without the accumulated trajectory</strong>, each round can look like the beginning of the task.</div>
</div>
</div>

<!-- Presenter cue: Connect the pseudocode to the previous diagram; do not dwell on syntax. -->

---
class: chapter-dense
---

# A Trajectory Is Both Runtime State and Learning Evidence

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="chapter-panel blue">
<h3>During the current task</h3>
<ul>
<li>Preserves progress and unresolved work.</li>
<li>Prevents redundant actions.</li>
<li>Exposes why a decision followed an observation.</li>
<li>Makes execution interpretable and debuggable.</li>
</ul>
</div>
<div class="chapter-panel green">
<h3>Across many tasks</h3>
<ul>
<li>Reveals recurring behavior and failure patterns.</li>
<li>Identifies better decision paths and tool interfaces.</li>
<li>Can be distilled into knowledge or external artifacts.</li>
<li>Can provide data for reinforcement learning.</li>
</ul>
</div>
</div>

<div class="chapter-callout orange mt-5"><strong>The cost is cumulative.</strong> Every call receives the growing trajectory; long tasks therefore create token, latency, attention, and compression problems that Chapter 2 addresses directly.</div>

<!-- Presenter cue: Use this slide to bridge runtime context to later chapters on compression and learning from experience. -->

---
class: chapter-dense
---

# Live Comparison: Control, Ablation, and Retained Five-Arm Evidence

<div class="grid grid-cols-2 gap-5 mt-4">
<div class="chapter-panel blue">
<div class="chapter-demo-head"><span>1-1A · 3 min</span><strong>Run two arms live</strong></div>
<p>Compare the full context with <code>no_history</code> on one canonical case.</p>
<ul class="chapter-tight-list"><li>Count iterations and tool actions.</li><li>Watch whether the same calls repeat.</li><li>Check whether a final numerical answer appears.</li></ul>
</div>
<div class="chapter-panel green">
<div class="chapter-demo-head"><span>1-1B · 1 min</span><strong>Inspect the accepted five-arm artifact</strong></div>
<p>Use the retained direct-API run to compare all arms—including the negative no-reasoning result.</p>
<ul class="chapter-tight-list"><li>Verify evidence mode and acceptance.</li><li>Distinguish execution success from hypothesis support.</li></ul>
</div>
</div>

<div class="chapter-callout red mt-5"><strong>Do not overclaim:</strong> the live two-arm run is a focused comparison. The complete five-arm conclusion comes from the linked accepted artifact unless all five arms are rerun during recording.</div>

<!-- Presenter cue: Set expectations before the terminal: one live comparison plus one retained-evidence inspection. -->

---
class: course-terminal chapter-terminal
---

<div class="course-kicker">LIVE DEMO · EXPERIMENT 1-1</div>

# Switching to the terminal

~~~bash
$ uv run --extra ch1 python chapter1/context/main.py --mode ablation --provider kimi --ablation-modes full no_history --cases 1 --output /tmp/ch1-context-live.json

$ jq '{evidence_mode, accepted:.analysis.experiment_execution_accepted, claims:.analysis.manuscript_behavior_claims, arms:[.arms[]|{mode,iterations,actions:.behavior.tool_action_count,repeated:.behavior.has_repeated_tool_action,correct:.behavior.canonical_answer_correct}]}' chapter1/context/validation/latest.json
~~~

<div class="chapter-terminal-grid mt-4">
<div><strong>Control</strong><span>3 iterations, 4 actions, correct total in the accepted run.</span></div>
<div><strong>No history</strong><span>Iteration ceiling and repeated actions are the predicted signature.</span></div>
<div><strong>Negative result</strong><span>No-reasoning remained correct in the accepted run.</span></div>
</div>

<div class="course-terminal-watch">The live API command requires <code>MOONSHOT_API_KEY</code>. The second command reads credential-free retained evidence and is safe to use if the provider is unavailable.</div>

<!-- Presenter cue: Run the two-arm comparison, then use jq to make all five retained outcomes visible. -->

---
class: chapter-dense
---

# The Real Ablation Result Is More Useful Than a Perfect Story

<table class="chapter-table chapter-table-compact mt-3">
<thead><tr><th>Arm</th><th>Iterations</th><th>Tool actions</th><th>Repeated?</th><th>Correct answer?</th><th>Interpretation</th></tr></thead>
<tbody>
<tr><td><strong>Full</strong></td><td>3</td><td>4</td><td>No</td><td>Yes</td><td>Control completed normally.</td></tr>
<tr><td><strong>No history</strong></td><td>5, ceiling</td><td>15</td><td>Yes · 12 repeats</td><td>No answer</td><td>Lost progress and restarted work.</td></tr>
<tr><td><strong>No reasoning</strong></td><td>3</td><td>4</td><td>No</td><td><strong>Yes</strong></td><td><strong>Expected degradation was not reproduced.</strong></td></tr>
<tr><td><strong>No tool definitions</strong></td><td>1</td><td>0</td><td>No</td><td>No</td><td>Model declined to invent exchange rates.</td></tr>
<tr><td><strong>No tool results</strong></td><td>5</td><td>7</td><td>Yes · 3 repeats</td><td>No</td><td>Calls ran, but observations were hidden.</td></tr>
</tbody>
</table>

<div class="grid grid-cols-2 gap-5 mt-4">
<div class="chapter-callout green"><strong>Execution accepted:</strong> all five direct-provider request contracts were verified and the intended ablations were actually applied.</div>
<div class="chapter-callout orange"><strong>Manuscript hypothesis partially supported:</strong> three predicted failure mechanisms reproduced; the no-reasoning claim did not on this task and model.</div>
</div>

<div class="chapter-source">Evidence: chapter1/context/validation/latest.json · 31,870 total tokens · created 2026-07-29</div>

<!-- Presenter cue: Lead with the negative result; it is stronger evidence of an honest experiment than a forced confirmation. -->

---
class: chapter-dense
---

# Context Determines What the Agent Knows at Decision Time

<div class="grid grid-cols-3 gap-5 mt-4">
<div class="chapter-panel blue"><h3>Definitions enable action</h3><p>Without the tool schema, the model cannot recognize or call the action interface—even when it understands the task.</p></div>
<div class="chapter-panel green"><h3>Results close the loop</h3><p>Without observations, execution does not become evidence; the Agent repeats calls or refuses to invent a result.</p></div>
<div class="chapter-panel purple"><h3>History preserves progress</h3><p>Without earlier messages, each decision loses completed work and can restart from the original request.</p></div>
</div>

<div class="chapter-thesis-box mt-5">Before compressing or discarding context, identify the state carried by each message and the observable failure caused by losing it.</div>

<div class="grid grid-cols-2 gap-4 mt-4 chapter-links">
<a href="../chapter1/context/run_experiment_1_1.py"><strong>Complete five-arm runner</strong><span>chapter1/context/run_experiment_1_1.py</span></a>
<a href="../book-en/chapter1.md"><strong>Chapter thought question</strong><span>How can trajectory cost stop growing quadratically without losing critical information?</span></a>
</div>

<!-- Presenter cue: Close on the experimentally supported components, then hand the compression problem to Chapter 2. -->
