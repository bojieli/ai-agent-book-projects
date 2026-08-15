---
theme: seriph
title: "Lesson 05 — What Does the Model Actually See?"
info: "English video course for AI Agents in Depth"
author: Bojie Li
transition: slide-left
mdc: true
lineNumbers: false
monaco: false
aspectRatio: 16/9
canvasWidth: 980
layout: cover
class: cover
---

<div class="course-kicker">Build · Chapter 2 · Context Engineering</div>

# What Does the Model Actually See?

<p class="course-subtitle">Messages, tool calls, and the Agent core loop</p>

<div class="course-cover-meta">Lesson 05 of 42 · 18 minutes · Context: The Ceiling of Agent Capability; API-Level Context Structure</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

<div class="course-kicker">Build · Chapter 2 · Context Engineering</div>

# Problems this chapter will solve

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Lesson 05</h3>
<p>What Does the Model Actually See?</p>
</div>
<div class="course-card green">
<h3>Lesson 06</h3>
<p>Why Can One Timestamp Make an Agent Slow?</p>
</div>
<div class="course-card purple">
<h3>Lesson 07</h3>
<p>Why Do Better Prompts Need Structure, Not More Rules?</p>
</div>
<div class="course-card blue">
<h3>Lesson 08</h3>
<p>How Can an Agent Know What It Needs to Learn?</p>
</div>
<div class="course-card green">
<h3>Lesson 09</h3>
<p>How Can an Agent Stay Oriented in a Long Task?</p>
</div>
</div>

<!-- Presenter cue: Orient viewers to the chapter. Name the progression, then highlight today's first problem. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Roles</h3>
<p>System, user, assistant, and tool messages have different semantics.</p>
</div>
<div class="course-card green">
<h3>Ordering</h3>
<p>A tool result must follow the tool call it answers.</p>
</div>
<div class="course-card orange">
<h3>Composition</h3>
<p>Every call rebuilds a view from static and dynamic context.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Context is a list</h3>
<p>Messages—not an abstract cloud of memory</p>
</div>
<div class="course-card blue">
<h3>Tool call</h3>
<p>An assistant message proposing a structured action</p>
</div>
<div class="course-card green">
<h3>Tool result</h3>
<p>A new observation appended to the trajectory</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig2-3.svg" alt="Message sequence for two tool calls">

<div class="course-caption">Message sequence for two tool calls</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Single turn vs. Agent loop

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Single turn</h3><ul><li>One request</li><li>One response</li><li>No environmental feedback</li></ul></div>
<div class="course-card green"><h3>Agent loop</h3><ul><li>Repeated requests</li><li>Tool calls and results</li><li>Growing trajectory</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The API structure is the runtime state machine.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Context at the API boundary

~~~python
messages = [{"role": "user", "content": task}]
while True:
    reply = client.responses.create(messages=messages, tools=tools)
    messages.append(reply)
    if reply.final: break
    messages.append(run_tool(reply.tool_call))
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>2-1</span><span>3 min</span></div>
<h3>Run local tool calling and watch messages grow</h3>
<p><strong>Observe:</strong> Assistant tool call, tool result, and final answer</p>
</div>
</div>

<div class="course-caption course-caption-strong">Demo budget: 3 minutes · one contiguous terminal block</div>

<!-- Presenter cue: State the prediction before running anything. Name the observation that could disconfirm it. -->

---
class: course-terminal
---

<div class="course-kicker">Live demo</div>

# Switching to the terminal

~~~bash
$ uv run python chapter2/local_llm_serving/main.py --backend ollama --mode single --task "What is the weather in Tokyo?"
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>The model only knows a tool exists because its schema is in context.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Tool results are observations, not hidden side effects.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>A malformed message sequence changes the task state the model perceives.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Framework abstractions are convenient, but debugging requires inspecting raw API messages.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Log the exact message list and tool schemas for every reproducible Agent failure.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter2/local_llm_serving/benchmark.py">
<span class="course-link-title">Local serving benchmark</span>
<span class="course-link-path">chapter2/local_llm_serving/benchmark.py</span>
</a>
<a class="course-link" href="../book-en/chapter2.md">
<span class="course-link-title">Minimal core loop</span>
<span class="course-link-path">book-en/chapter2.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which part of your Agent state exists outside the message list, and how is it reintroduced?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 06</div>

<div class="course-next">Rearranging that list can change both latency and cost.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
