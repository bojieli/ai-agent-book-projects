function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function slide(body, { layout, className, cue } = {}) {
  const lines = ["---"];
  if (layout || className) {
    if (layout) lines.push("layout: " + layout);
    if (className) lines.push("class: " + className);
    lines.push("---");
  }
  lines.push("", body.trim(), "");
  if (cue) lines.push("<!-- Presenter cue: " + cue + " -->", "");
  return lines.join("\n");
}

function frontmatter(lesson, chapterLesson, title, subtitle, minutes, body) {
  const lessonNo = String(lesson.number).padStart(2, "0");
  return [
    "---",
    "theme: seriph",
    "title: " + JSON.stringify("Chapter 1 · Lesson " + chapterLesson + " — " + title),
    "info: " + JSON.stringify("English video course for AI Agents in Depth"),
    "author: Bojie Li",
    "transition: slide-left",
    "mdc: true",
    "lineNumbers: false",
    "monaco: false",
    "aspectRatio: 16/9",
    "canvasWidth: 980",
    "layout: cover",
    "class: chapter-formula-cover",
    "---",
    "",
    body.trim(),
    "",
    '<div class="chapter-cover-footer"><span>Bojie Li · AI Agents in Depth</span><span>Course Lesson ' + lessonNo + " of 42 · " + minutes + " minutes</span></div>",
    "",
    "<!-- Presenter cue: Introduce the chapter thesis through the formula; the slide already carries the factual structure. -->",
    ""
  ].join("\n");
}

function renderLessonOne(lesson) {
  const deck = [];

  deck.push(frontmatter(
    lesson,
    1,
    "What Turns an LLM into an Agent?",
    "Reasoning engine + working context + action interfaces",
    18,
    String.raw`
<div class="chapter-kicker">BUILD · CHAPTER 1 · AGENT FUNDAMENTALS</div>

# What Turns an LLM into an Agent?

<div class="chapter-equation mt-7">
  <div class="chapter-equation-term blue"><strong>LLM</strong><span>Reasoning engine</span><small>Understand · plan · decide</small></div>
  <div class="chapter-equation-sign">+</div>
  <div class="chapter-equation-term green"><strong>Context</strong><span>Working set</span><small>Observe · remember · retrieve</small></div>
  <div class="chapter-equation-sign">+</div>
  <div class="chapter-equation-term orange"><strong>Tools</strong><span>Action interfaces</span><small>Search · execute · communicate</small></div>
</div>

<div class="chapter-cover-thesis">Agent = Reasoning Engine + Working Context + Action Interfaces</div>`
  ));

  deck.push(slide(String.raw`
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

<div class="chapter-callout green mt-4"><strong>Shared trait:</strong> they plan execution steps, call the tools a task requires, and revise their strategy as results arrive.</div>`, {
    className: "chapter-dense",
    cue: "Use the products to establish the behavioral shift described in the chapter opening."
  }));

  deck.push(slide(String.raw`
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
</div>`, {
    className: "chapter-dense",
    cue: "Define the three terms broadly, then mention that the RL column is only a vocabulary bridge."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-thesis-line mt-5">With the model held constant, expanding the right context or tool can make a previously unsolvable task solvable—without retraining.</div>`, {
    className: "chapter-dense",
    cue: "Trace the interface in both directions and emphasize the held-constant-model condition."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout orange mt-4"><strong>Expansion is not “include everything.”</strong> Irrelevant context adds noise; too many tools increase selection cost and security risk. Useful expansion is on-demand, relevant, and controlled.</div>`, {
    className: "chapter-dense",
    cue: "Use Manus and OpenClaw exactly as the chapter uses them: as interface-expansion examples."
  }));

  deck.push(slide(String.raw`
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
</div>`, {
    className: "chapter-dense",
    cue: "Compare products by architecture rather than by brand or feature list."
  }));

  deck.push(slide(String.raw`
# Tools Are More Than Callable APIs

<div class="chapter-five-grid mt-5">
<div class="chapter-panel blue"><h3>1 · Perception</h3><p>Bring information into the Agent: search, files, APIs, databases.</p></div>
<div class="chapter-panel green"><h3>2 · Execution</h3><p>Change external systems: code, files, commands, service APIs.</p></div>
<div class="chapter-panel purple"><h3>3 · Collaboration</h3><p>Delegate to sub-agents, request human confirmation, coordinate work.</p></div>
<div class="chapter-panel orange"><h3>4 · Event triggers</h3><p>Email, schedules, and Webhooks activate the Agent; the Agent does not call them.</p></div>
<div class="chapter-panel red"><h3>5 · User communication</h3><p>Report progress or ask questions by message, voice, or email.</p></div>
</div>

<div class="chapter-thesis-line mt-5">Tool quality defines what the Agent can accomplish reliably: vague interfaces cause misuse, weak error handling causes stalls, and broad permissions turn mistakes into irreversible actions.</div>`, {
    className: "chapter-dense",
    cue: "Preserve the chapter's broad definition of tools, especially event triggers and communication channels."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout blue mt-3"><strong>Division of responsibility:</strong> the developer declares and executes tools; the model decides whether to call one, which one, and with what arguments.</div>`, {
    className: "chapter-dense",
    cue: "Walk through the API sequence and point out that the tool result becomes the next observation."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout red mt-4"><strong>Code sandbox minimums:</strong> network disabled by default; authorized working directory only; path-traversal prevention; execution-time, CPU, memory, storage, file-type, and output limits.</div>`, {
    className: "chapter-dense",
    cue: "Present generality and safety as a design trade-off, not as competing ideologies."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout green mt-5"><strong>Why this matters for Agents:</strong> the next action is not blind trial and error. The model draws on learned causal relationships, decomposition strategies, and world knowledge before acting.</div>`, {
    className: "chapter-dense",
    cue: "Explain zero-shot and few-shot as sources of runtime adaptability, not as separate Agent components."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-source">Chapter 1 clarification prompted by GitHub Issue #30.</div>`, {
    className: "chapter-dense",
    cue: "Make the policy-versus-execution distinction explicit; it is a central correction in the chapter."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout orange mt-3"><strong>Pragmatic Bitter Lesson:</strong> models will absorb parts of today’s Harness, but training moves more slowly than real business requirements. The Harness covers the current capability boundary and moves when that boundary moves.</div>`, {
    className: "chapter-dense",
    cue: "Compare persistence, update cost, and expressiveness; do not present the paths as mutually exclusive."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout blue mt-3"><strong>Acceptance requires real provider receipts:</strong> direct Moonshot API, exact <code>kimi-k3</code> model, multiple distinct successful Fibers, sequential search rounds, reasoning, final answer, retrieval date, and official-source links.</div>`, {
    className: "chapter-dense",
    cue: "State the task and acceptance criteria before switching to the terminal."
  }));

  deck.push(slide(String.raw`
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

<div class="course-terminal-watch">Requires <code>MOONSHOT_API_KEY</code>. If the provider is unavailable during recording, inspect the accepted credential-free artifact on the next slide and label it retained evidence.</div>`, {
    className: "course-terminal chapter-terminal",
    cue: "Run one canonical attempt. Narrate why each follow-up search occurs; do not narrate every token."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-source">Evidence: chapter1/web-search-agent/validation/latest.json · evidence mode: real_api</div>`, {
    className: "chapter-dense",
    cue: "Separate the accepted evidence from the architectural interpretation."
  }));

  deck.push(slide(String.raw`
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
</div>`, {
    className: "chapter-dense",
    cue: "Close with the chapter's systems-engineering lever, then bridge to the working context in Lesson 2."
  }));

  return { markdown: deck.join("\n"), slideCount: deck.length };
}

function renderLessonTwo(lesson) {
  const deck = [];

  deck.push(frontmatter(
    lesson,
    2,
    "What Is Inside an Agent's Context?",
    "Static prefix + dynamic trajectory",
    19,
    String.raw`
<div class="chapter-kicker">BUILD · CHAPTER 1 · AGENT FUNDAMENTALS</div>

# What Is Inside an Agent's Context?

<div class="chapter-context-equation mt-6">
  <div class="chapter-context-group blue"><strong>Static prefix</strong><span>System prompt</span><span>Tool definitions</span></div>
  <div class="chapter-equation-sign">+</div>
  <div class="chapter-context-group green"><strong>Trajectory</strong><span>User messages</span><span>Assistant messages</span><span>Tool results</span></div>
</div>

<div class="chapter-cover-thesis">Every model call sees the prefix plus the trajectory accumulated so far.</div>`
  ));

  deck.push(slide(String.raw`
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

<div class="chapter-thesis-line mt-5">The Agent can decide only from information present at decision time—even if the missing fact exists elsewhere in the system.</div>`, {
    className: "chapter-dense",
    cue: "Distinguish persistent storage from the smaller working set exposed on the current call."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout blue mt-4"><strong>Experiment 1-1 tests four removals.</strong> The system prompt is exempt because without a basic identity definition the test no longer represents the same Agent.</div>`, {
    className: "chapter-dense",
    cue: "Use the failure column to make each component operational rather than definitional."
  }));

  deck.push(slide(String.raw`
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
</div>`, {
    className: "chapter-dense",
    cue: "Establish the exact equation that the next slides and experiment will probe."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout orange mt-3"><strong>The tool result is a separate message.</strong> The framework executes the proposal and appends the observation under the matching tool-call ID.</div>`, {
    className: "chapter-dense",
    cue: "Point out that the three fields need not appear together on every assistant response."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-thesis-line mt-3">Ablation is diagnostic: different missing components should create different, observable failure signatures.</div>`, {
    className: "chapter-dense",
    cue: "Define the controlled comparison before showing expected or observed behavior."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout purple mt-4"><strong>Important:</strong> the runner verifies the request contract itself—what the provider actually received—not merely the CLI mode name.</div>`, {
    className: "chapter-dense",
    cue: "State predictions in falsifiable form; the no-reasoning result will matter later."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout red mt-3"><strong>A loop also needs exit conditions:</strong> task complete, final-output tool called, no tool call, unrecoverable error, or maximum rounds reached.</div>`, {
    className: "chapter-dense",
    cue: "Explain why the name ReAct omits observation even though observation is operationally indispensable."
  }));

  deck.push(slide(String.raw`
# Every Round Sees the Entire Trajectory So Far

<img class="chapter-figure-wide mt-1" src="/images/fig1-3.svg" alt="ReAct trajectory for multi-currency revenue aggregation">

<div class="grid grid-cols-3 gap-4 mt-3">
<div class="chapter-mini blue"><strong>Round 1</strong><span>Reason about missing exchange rates; call currency tools in parallel.</span></div>
<div class="chapter-mini green"><strong>Round 2</strong><span>Observe conversions; call the code interpreter to aggregate.</span></div>
<div class="chapter-mini purple"><strong>Round 3</strong><span>Observe the calculation; return total and quarterly average.</span></div>
</div>

<div class="chapter-thesis-line mt-3">The trajectory is the dynamic part of the next prompt, not a log consulted after execution.</div>`, {
    className: "chapter-dense",
    cue: "Trace one item from action to observation to the next decision."
  }));

  deck.push(slide(String.raw`
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
</div>`, {
    className: "chapter-dense",
    cue: "Connect the pseudocode to the previous diagram; do not dwell on syntax."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout orange mt-5"><strong>The cost is cumulative.</strong> Every call receives the growing trajectory; long tasks therefore create token, latency, attention, and compression problems that Chapter 2 addresses directly.</div>`, {
    className: "chapter-dense",
    cue: "Use this slide to bridge runtime context to later chapters on compression and learning from experience."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-callout red mt-5"><strong>Do not overclaim:</strong> the live two-arm run is a focused comparison. The complete five-arm conclusion comes from the linked accepted artifact unless all five arms are rerun during recording.</div>`, {
    className: "chapter-dense",
    cue: "Set expectations before the terminal: one live comparison plus one retained-evidence inspection."
  }));

  deck.push(slide(String.raw`
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

<div class="course-terminal-watch">The live API command requires <code>MOONSHOT_API_KEY</code>. The second command reads credential-free retained evidence and is safe to use if the provider is unavailable.</div>`, {
    className: "course-terminal chapter-terminal",
    cue: "Run the two-arm comparison, then use jq to make all five retained outcomes visible."
  }));

  deck.push(slide(String.raw`
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

<div class="chapter-source">Evidence: chapter1/context/validation/latest.json · 31,870 total tokens · created 2026-07-29</div>`, {
    className: "chapter-dense",
    cue: "Lead with the negative result; it is stronger evidence of an honest experiment than a forced confirmation."
  }));

  deck.push(slide(String.raw`
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
</div>`, {
    className: "chapter-dense",
    cue: "Close on the experimentally supported components, then hand the compression problem to Chapter 2."
  }));

  return { markdown: deck.join("\n"), slideCount: deck.length };
}

export const chapter1PilotFigures = new Set([
  "fig1-1.svg",
  "fig1-2.svg",
  "fig1-3.svg",
  "fig1-4.svg",
  "fig1-5.svg"
]);

export function chapter1PilotSlideCount(number) {
  if (number === 2) return 16;
  if (number === 3) return 15;
  return null;
}

export function renderChapter1Pilot(lesson) {
  if (lesson.number === 2) return renderLessonOne(lesson);
  if (lesson.number === 3) return renderLessonTwo(lesson);
  return null;
}
