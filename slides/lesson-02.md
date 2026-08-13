---
theme: seriph
title: "Chapter 1 · Lesson 1 — What Turns an LLM into an Agent?"
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

# What Turns an LLM into an Agent?

<div class="chapter-equation mt-7">
  <div class="chapter-equation-term blue"><strong>LLM</strong><span>Reasoning engine</span><small>Understand · plan · decide</small></div>
  <div class="chapter-equation-sign">+</div>
  <div class="chapter-equation-term green"><strong>Context</strong><span>Working set</span><small>Observe · remember · retrieve</small></div>
  <div class="chapter-equation-sign">+</div>
  <div class="chapter-equation-term orange"><strong>Tools</strong><span>Action interfaces</span><small>Search · execute · communicate</small></div>
</div>

<div class="chapter-cover-thesis">Agent = Reasoning Engine + Working Context + Action Interfaces</div>

<div class="chapter-cover-footer"><span>Bojie Li · AI Agents in Depth</span><span>Course Lesson 02 of 42 · 18 minutes</span></div>

<!-- Presenter cue: Introduce the chapter thesis through the formula; the slide already carries the factual structure. -->

---
class: chapter-dense
---

# You Have Already Used an AI Agent

<div class="chapter-lead">Chapter 1 begins with products that have crossed the boundary from <strong>answering</strong> to <strong>acting</strong>.</div>

<table class="chapter-table mt-4">
<thead><tr><th>Product</th><th>What it observes</th><th>What it does</th><th>How it adapts</th></tr></thead>
<tbody>
<tr><td><strong>Cursor</strong></td><td>Requirements, codebase, terminal</td><td>Searches, edits, runs tests</td><td>Debugs until tests pass</td></tr>
<tr><td><strong>Deep Research</strong></td><td>Web, papers, local files</td><td>Searches, reads, synthesizes</td><td>Changes the research direction</td></tr>
<tr><td><strong>Manus</strong></td><td>Browser, files, screen</td><td>Clicks, types, executes code</td><td>Replans from interface feedback</td></tr>
<tr><td><strong>Doubao</strong></td><td>Phone screen and apps</td><td>Opens, swipes, types, confirms</td><td>Responds to the app state</td></tr>
<tr><td><strong>Pine AI</strong></td><td>Accounts, bills, provider knowledge</td><td>Calls, emails, negotiates</td><td>Adjusts strategy during the task</td></tr>
</tbody>
</table>

<div class="chapter-callout green mt-4"><strong>Shared trait:</strong> they plan execution steps, call the tools a task requires, and revise their strategy as results arrive.</div>

<!-- Presenter cue: Use the products to establish the behavioral shift described in the chapter opening. -->

---
class: chapter-dense
---

# One Formula, Three Levels of Description

<table class="chapter-table chapter-table-roomy mt-5">
<thead><tr><th>Intuition</th><th>Agent component</th><th>RL term <span class="chapter-muted">(optional)</span></th><th>Responsibility</th></tr></thead>
<tbody>
<tr><td><strong>Reasoning engine</strong></td><td><strong>LLM</strong></td><td>Policy</td><td>Given current information, choose what to do next.</td></tr>
<tr><td><strong>Working context</strong></td><td><strong>Context</strong></td><td>Observation space</td><td>Everything the Agent can observe, read, remember, and retrieve.</td></tr>
<tr><td><strong>Action interfaces</strong></td><td><strong>Tools</strong></td><td>Action space</td><td>Everything the Agent can do—from messages and APIs to code and GUI control.</td></tr>
</tbody>
</table>

<div class="grid grid-cols-2 gap-5 mt-5">
<div class="chapter-callout blue"><strong>The minimal system:</strong> LLM + context + tools is enough to demonstrate an Agent loop.</div>
<div class="chapter-callout orange"><strong>The production question:</strong> later in the chapter, Harness Engineering adds constraints, verification, and correction.</div>
</div>

<!-- Presenter cue: Define the three terms broadly, then mention that the RL column is only a vocabulary bridge. -->

---
class: chapter-dense
---

# Observation + Action Spaces Are the Agent's ISA

<div class="chapter-lead">Hennessy and Patterson use the instruction set architecture as the interface between software and hardware. Chapter 1 applies the same idea to Agents.</div>

<div class="chapter-interface mt-6">
  <div class="chapter-interface-world"><strong>External world</strong><span>Web · files · apps · people</span></div>
  <div class="chapter-interface-arrow"><span>Observation space</span>→</div>
  <div class="chapter-interface-model"><strong>LLM</strong><span>Reasons over what enters context</span></div>
  <div class="chapter-interface-arrow"><span>Action space</span>→</div>
  <div class="chapter-interface-world"><strong>External world</strong><span>Changed by tool execution</span></div>
</div>

<div class="grid grid-cols-2 gap-5 mt-6">
<div class="chapter-callout red"><strong>Outside the observation space:</strong> information effectively does not exist for the model.</div>
<div class="chapter-callout orange"><strong>Outside the action space:</strong> the model can recommend an operation, but it cannot perform it.</div>
</div>

<div class="chapter-thesis-line mt-5">With the model held constant, expanding the right context or tool can make a previously unsolvable task solvable—without retraining.</div>

<!-- Presenter cue: Trace the interface in both directions and emphasize the held-constant-model condition. -->

---
class: chapter-dense
---

# Generality Often Comes from Expanding the Interface Boundary

<div class="grid grid-cols-2 gap-6 mt-4">
<div class="chapter-panel blue">
<h3>Manus: unite previously separate spaces</h3>
<ul>
<li><strong>Deep Research:</strong> the web enlarges observation.</li>
<li><strong>Coding:</strong> files and code execution enlarge action.</li>
<li><strong>Computer Use:</strong> screen perception and clicking enter both spaces.</li>
</ul>
<p class="chapter-conclusion">Its generality did not come merely from swapping in a stronger model; it took the union of three earlier Agent categories.</p>
</div>
<div class="chapter-panel green">
<h3>OpenClaw: extend into the user's digital life</h3>
<ul>
<li>Messaging channels make the Agent reachable from almost anywhere.</li>
<li>A local-first Gateway reaches authorized local files and cloud applications.</li>
<li>Plugins and Skills enlarge the action interface on demand.</li>
</ul>
<p class="chapter-conclusion">The product boundary moves outward—but authorization, relevance, and verification must move with it.</p>
</div>
</div>

<div class="chapter-callout orange mt-4"><strong>Expansion is not “include everything.”</strong> Irrelevant context adds noise; too many tools increase selection cost and security risk. Useful expansion is on-demand, relevant, and controlled.</div>

<!-- Presenter cue: Use Manus and OpenClaw exactly as the chapter uses them: as interface-expansion examples. -->

---
class: chapter-dense
---

# Five Agent Products, Compared on the Same Three Dimensions

<table class="chapter-table chapter-table-compact mt-3">
<thead><tr><th>Agent type</th><th>Working context</th><th>Action interfaces</th><th>Execution strategy</th></tr></thead>
<tbody>
<tr><td><strong>Coding</strong></td><td>Requirements, repository, terminal</td><td>Search, read/write files, commands</td><td>Understand → edit → test → debug</td></tr>
<tr><td><strong>Search</strong></td><td>Web, academic databases, local files</td><td>Queries, web reading, synthesis</td><td>Iteratively deepen and redirect research</td></tr>
<tr><td><strong>Computer control</strong></td><td>Screen, browser, file system</td><td>Click, type, scroll, screenshot, code</td><td>Observe interface → act → verify</td></tr>
<tr><td><strong>Phone assistant</strong></td><td>Phone screen, installed applications</td><td>Click, swipe, type, open apps</td><td>Understand intent → operate → confirm</td></tr>
<tr><td><strong>Personal task</strong></td><td>Accounts, bills, provider knowledge</td><td>Calls, email, forms, user confirmation</td><td>Gather → plan → contact → negotiate → report</td></tr>
</tbody>
</table>

<div class="grid grid-cols-3 gap-4 mt-4">
<div class="chapter-mini blue"><strong>Open-ended action</strong><span>Generate language and code—not select only from fixed buttons.</span></div>
<div class="chapter-mini purple"><strong>Internal reasoning</strong><span>Plan before changing the environment.</span></div>
<div class="chapter-mini green"><strong>Continuous interaction</strong><span>Use environmental feedback to choose the next step.</span></div>
</div>

<!-- Presenter cue: Compare products by architecture rather than by brand or feature list. -->

---
class: chapter-dense
---

# Tools Are More Than Callable APIs

<div class="chapter-five-grid mt-5">
<div class="chapter-panel blue"><h3>1 · Perception</h3><p>Bring information into the Agent: search, files, APIs, databases.</p></div>
<div class="chapter-panel green"><h3>2 · Execution</h3><p>Change external systems: code, files, commands, service APIs.</p></div>
<div class="chapter-panel purple"><h3>3 · Collaboration</h3><p>Delegate to sub-agents, request human confirmation, coordinate work.</p></div>
<div class="chapter-panel orange"><h3>4 · Event triggers</h3><p>Email, schedules, and Webhooks activate the Agent; the Agent does not call them.</p></div>
<div class="chapter-panel red"><h3>5 · User communication</h3><p>Report progress or ask questions by message, voice, or email.</p></div>
</div>

<div class="chapter-thesis-line mt-5">Tool quality defines what the Agent can accomplish reliably: vague interfaces cause misuse, weak error handling causes stalls, and broad permissions turn mistakes into irreversible actions.</div>

<!-- Presenter cue: Preserve the chapter's broad definition of tools, especially event triggers and communication channels. -->

---
class: chapter-dense
---

# Tool Calling Is a Four-Step Context Update

<div class="grid grid-cols-2 gap-4 mt-4 chapter-code-grid">
<div><div class="chapter-step-label">1 · Declare the interface</div>
<pre class="chapter-code-block" v-pre><code>{
  "name": "get_weather",
  "parameters": {"city": "string"}
}</code></pre>
</div>
<div><div class="chapter-step-label">2 · The model decides</div>
<pre class="chapter-code-block" v-pre><code>{
  "tool_calls": [{
    "name": "get_weather",
    "arguments": {"city": "Beijing"}
  }]
}</code></pre>
</div>
<div><div class="chapter-step-label">3 · Execute and append the result</div>
<pre class="chapter-code-block" v-pre><code>{
  "role": "tool",
  "tool_call_id": "call_1",
  "content": "{\"temp\":28,\"sky\":\"clear\"}"
}</code></pre>
</div>
<div><div class="chapter-step-label">4 · Decide again from the new context</div>
<pre class="chapter-code-block" v-pre><code>{
  "role": "assistant",
  "content": "Today in Beijing: 28°C, sunny."
}</code></pre>
</div>
</div>

<div class="chapter-callout blue mt-3"><strong>Division of responsibility:</strong> the developer declares and executes tools; the model decides whether to call one, which one, and with what arguments.</div>

<!-- Presenter cue: Walk through the API sequence and point out that the tool result becomes the next observation. -->

---
class: chapter-dense
---

# General Tools Compose; Specialized Tools Constrain

<div class="grid grid-cols-2 gap-6 mt-4">
<div class="chapter-panel green">
<h3>General-purpose foundations</h3>
<ul>
<li>A calculator is enough for basic arithmetic.</li>
<li>A constrained Python interpreter combines spreadsheet reading, cleaning, statistics, and plotting.</li>
<li>A controlled working directory preserves plans, logs, intermediate results, and artifacts across long tasks.</li>
</ul>
<div class="chapter-tag green">Use for composition and exploration</div>
</div>
<div class="chapter-panel orange">
<h3>Specialized high-risk operations</h3>
<ul>
<li>Payments, deletion, email, and production deployment need explicit parameters.</li>
<li>Restrict permissions and make the complete operation auditable.</li>
<li>Add preview and human confirmation when an action is sensitive or irreversible.</li>
</ul>
<div class="chapter-tag orange">Use to enforce business rules</div>
</div>
</div>

<div class="chapter-callout red mt-4"><strong>Code sandbox minimums:</strong> network disabled by default; authorized working directory only; path-traversal prevention; execution-time, CPU, memory, storage, file-type, and output limits.</div>

<!-- Presenter cue: Present generality and safety as a design trade-off, not as competing ideologies. -->

---
class: chapter-dense
---

# The LLM Supplies Reasoning Before It Supplies Action

<div class="chapter-lead">The reasoning engine must infer intent, decompose a vague task, and repeatedly decide what to do next, whether to call a tool, and which arguments to use.</div>

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="chapter-panel blue">
<h3>Zero-shot generalization</h3>
<p>Solve a task with no demonstrations by recombining knowledge and reasoning patterns acquired during pre-training.</p>
<div class="chapter-example">Example: produce a reasonable poem about quantum physics without being trained on that exact request.</div>
</div>
<div class="chapter-panel purple">
<h3>Few-shot adaptation</h3>
<p>Infer a new task pattern from two or three examples placed in the current context.</p>
<div class="chapter-example">Example: learn a new user-comment → sentiment-label format from a handful of demonstrations.</div>
</div>
</div>

<div class="chapter-callout green mt-5"><strong>Why this matters for Agents:</strong> the next action is not blind trial and error. The model draws on learned causal relationships, decomposition strategies, and world knowledge before acting.</div>

<!-- Presenter cue: Explain zero-shot and few-shot as sources of runtime adaptability, not as separate Agent components. -->

---
class: chapter-dense
---

# “Model as Agent” Internalizes the Decision Policy—not the Tools

<div class="grid grid-cols-2 gap-6 mt-4">
<div class="chapter-panel purple">
<h3>What post-training can write into weights</h3>
<ul>
<li>When a tool call is useful.</li>
<li>Which tool to choose.</li>
<li>What arguments to pass.</li>
<li>Whether to continue after a result.</li>
<li>How to chain many calls coherently.</li>
</ul>
</div>
<div class="chapter-panel orange">
<h3>What remains outside the model</h3>
<ul>
<li>The search engine and code sandbox.</li>
<li>Tool declarations and provider infrastructure.</li>
<li>Execution, permissions, and returned results.</li>
<li>The server-side or client-side orchestration loop.</li>
</ul>
</div>
</div>

<div class="chapter-thesis-line mt-5">The orchestration loop has not disappeared: decision-making may move into the model while execution moves to the API server.</div>

<div class="chapter-source">Chapter 1 clarification prompted by GitHub Issue #30.</div>

<!-- Presenter cue: Make the policy-versus-execution distinction explicit; it is a central correction in the chapter. -->

---
class: chapter-dense
---

# Agents Learn on Three Timescales

<div class="grid grid-cols-5 gap-5 mt-2 items-center">
<div class="col-span-3">
<img class="chapter-figure-large" src="/images/fig1-1.svg" alt="Three levels of Agent capability updates">
</div>
<div class="col-span-2 chapter-stack">
<div class="chapter-mini blue"><strong>Contextual adaptation</strong><span>Inference-time, immediate, temporary, bounded by the context window.</span></div>
<div class="chapter-mini green"><strong>Externalized learning</strong><span>Knowledge, prompts, Skills, programs, and Harnesses persist across tasks and remain auditable.</span></div>
<div class="chapter-mini purple"><strong>Parameter updates</strong><span>Training-time, costly, persistent, useful for high-dimensional capabilities and implicit policies.</span></div>
</div>
</div>

<div class="chapter-callout orange mt-3"><strong>Pragmatic Bitter Lesson:</strong> models will absorb parts of today’s Harness, but training moves more slowly than real business requirements. The Harness covers the current capability boundary and moves when that boundary moves.</div>

<!-- Presenter cue: Compare persistence, update cost, and expressiveness; do not present the paths as mutually exclusive. -->

---
class: chapter-dense
---

# Experiment 1-2: Can Kimi K3 Sustain Native Tool Use?

<div class="grid grid-cols-5 gap-5 mt-2">
<div class="col-span-3">
<img class="chapter-figure-medium" src="/images/fig1-4.svg" alt="Model as Agent architecture with native tool calling">
</div>
<div class="col-span-2">
<h3>Canonical task</h3>
<p class="chapter-small">Verify ASEAN membership and the legal status of Jakarta versus Nusantara from official sources. Search once, inspect what evidence is missing, then perform distinct follow-up searches.</p>
<h3 class="mt-3">Exact provider route</h3>
<ol class="chapter-tight-list">
<li>Fetch Moonshot’s authoritative <code>web_search</code> declaration.</li>
<li>Kimi decides when and how to call it.</li>
<li>Each call runs through a Formula Fiber.</li>
<li>The result returns as the next observation.</li>
</ol>
</div>
</div>

<div class="chapter-callout blue mt-3"><strong>Acceptance requires real provider receipts:</strong> direct Moonshot API, exact <code>kimi-k3</code> model, multiple distinct successful Fibers, sequential search rounds, reasoning, final answer, retrieval date, and official-source links.</div>

<!-- Presenter cue: State the task and acceptance criteria before switching to the terminal. -->

---
class: course-terminal chapter-terminal
---

<div class="course-kicker">LIVE DEMO · EXPERIMENT 1-2 · REAL API</div>

# Switching to the terminal

~~~bash
$ uv run --extra ch1 python chapter1/web-search-agent/run_experiment_1_2.py --attempts 1 --timeout 120
~~~

<div class="chapter-terminal-grid mt-5">
<div><strong>Watch the policy</strong><span>Search queries change as missing evidence becomes visible.</span></div>
<div><strong>Watch the interface</strong><span>Every action is a standard <code>web_search</code> call executed by a Formula Fiber.</span></div>
<div><strong>Watch the receipts</strong><span>Response IDs, Fiber IDs, sources, token usage, and acceptance checks are retained.</span></div>
</div>

<div class="course-terminal-watch">Requires <code>MOONSHOT_API_KEY</code>. If the provider is unavailable during recording, inspect the accepted credential-free artifact on the next slide and label it retained evidence.</div>

<!-- Presenter cue: Run one canonical attempt. Narrate why each follow-up search occurs; do not narrate every token. -->

---
class: chapter-dense
---

# What the Accepted Run Actually Demonstrated

<div class="chapter-metrics mt-4">
<div><strong>5</strong><span>reasoning iterations</span></div>
<div><strong>15</strong><span>successful Formula Fibers</span></div>
<div><strong>58,123</strong><span>total tokens</span></div>
<div><strong>29,952</strong><span>cached prompt tokens</span></div>
</div>

<div class="grid grid-cols-2 gap-6 mt-5">
<div>
<h3>Observed in retained real-API evidence</h3>
<ul class="chapter-tight-list">
<li>Different searches occurred over multiple sequential rounds.</li>
<li>Every model action matched a provider-side Fiber request.</li>
<li>The final answer cited ASEAN and Indonesian official sources.</li>
<li>All acceptance checks passed on 2026-07-29.</li>
</ul>
</div>
<div>
<h3>What this does—and does not—show</h3>
<ul class="chapter-tight-list">
<li><strong>Shows:</strong> the model controls a long search policy and revises it from observations.</li>
<li><strong>Does not show:</strong> that the search engine or execution infrastructure lives in the weights.</li>
<li><strong>Cost:</strong> autonomy can require many calls and a large cumulative context.</li>
</ul>
</div>
</div>

<div class="chapter-source">Evidence: chapter1/web-search-agent/validation/latest.json · evidence mode: real_api</div>

<!-- Presenter cue: Separate the accepted evidence from the architectural interpretation. -->

---
class: chapter-dense
---

# The Capability Boundary Is Often the Interface Boundary

<div class="grid grid-cols-3 gap-5 mt-5">
<div class="chapter-panel blue"><h3>Reasoning engine</h3><p>The LLM supplies world knowledge, planning, judgment, zero-shot generalization, and a learned tool-use policy.</p></div>
<div class="chapter-panel green"><h3>Working context</h3><p>The observation space determines which task state, evidence, memory, and environmental feedback can influence a decision.</p></div>
<div class="chapter-panel orange"><h3>Action interfaces</h3><p>Tools determine which operations can affect the world; broader interfaces require stronger permissions and verification.</p></div>
</div>

<div class="chapter-thesis-box mt-5">When an Agent cannot solve a task, first locate the missing capability: model policy, observable information, or executable action.</div>

<div class="grid grid-cols-2 gap-4 mt-4 chapter-links">
<a href="../chapter1/search-codegen/"><strong>Next experiment</strong><span>Experiment 1-3 · GPT-5.6 search + code</span></a>
<a href="../book-en/chapter1.md"><strong>Book question</strong><span>When would you choose a stronger model, richer context, or more tools?</span></a>
</div>

<!-- Presenter cue: Close with the chapter's systems-engineering lever, then bridge to the working context in Lesson 2. -->
