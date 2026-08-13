---
theme: seriph
title: "Lesson 16 — When Should an Agent Ask for Help or Delegate?"
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

<div class="course-kicker">Build · Chapter 4 · Tools</div>

# When Should an Agent Ask for Help or Delegate?

<p class="course-subtitle">Sub-agents, Human-in-the-Loop, and communication tools</p>

<div class="course-cover-meta">Lesson 16 of 42 · 18 minutes · Collaboration Tools; User Communication; Virtual Identity</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">How should an Agent hand work to another actor without losing context or control?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Handoff</h3>
<p>Pass only the facts and artifacts the collaborator needs.</p>
</div>
<div class="course-card green">
<h3>Lifecycle</h3>
<p>Spawn, message, query, cancel, and collect results.</p>
</div>
<div class="course-card orange">
<h3>Escalation</h3>
<p>Ask a human when authority or missing judgment requires it.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Minimal handoff</h3>
<p>Task parameters with almost no history</p>
</div>
<div class="course-card blue">
<h3>Distilled handoff</h3>
<p>Facts, constraints, artifacts, and open questions</p>
</div>
<div class="course-card green">
<h3>HITL</h3>
<p>A permission and information channel—not an error screen</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig4-2.svg" alt="Event-driven asynchronous Agent architecture">

<div class="course-caption">Event-driven asynchronous Agent architecture</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Full transcript vs. Handoff package

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Full transcript</h3><ul><li>Maximum context</li><li>Large and biasing</li><li>Leaks irrelevant information</li></ul></div>
<div class="course-card green"><h3>Handoff package</h3><ul><li>Confirmed facts</li><li>Artifact paths</li><li>Explicit responsibility</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Context sharing and delegation are separate design decisions.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Lifecycle primitives stay small

~~~python
worker = spawn_subagent(task, context=handoff)
send_message(worker, update)
status = get_status(worker)
if no_longer_needed(status):
    cancel_subagent(worker)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>4-4A</span><span>2 min</span></div>
<h3>Compare sub-agent handoff strategies</h3>
<p><strong>Observe:</strong> Context size, task completeness, and irrelevant carryover</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>4-4B</span><span>1 min</span></div>
<h3>Exercise a Human-in-the-Loop gate</h3>
<p><strong>Observe:</strong> Pending state, timeout, approval, and audit record</p>
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
$ uv run python chapter4/collaboration-tools/main.py subagent compare

$ uv run python chapter4/collaboration-tools/main.py hitl approve --message "Delete 1000 records?" --timeout 5 --auto-approve
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>A collaborator should receive a task contract, not indiscriminate history.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Cancellation and status are first-class parts of delegation.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Human intervention works best when the Agent explains the decision and safe defaults.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A slow or unavailable human cannot be treated as a synchronous function call.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Design collaboration as an asynchronous lifecycle with explicit authority and structured handoffs.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter4/collaboration-tools/">
<span class="course-link-title">Multi-channel notifications</span>
<span class="course-link-path">chapter4/collaboration-tools/</span>
</a>
<a class="course-link" href="../chapter4/collaboration-tools/">
<span class="course-link-title">Timers and delayed tasks</span>
<span class="course-link-path">chapter4/collaboration-tools/</span>
</a>
<a class="course-link" href="../chapter4/collaboration-tools/subagent_comparison.py">
<span class="course-link-title">Sub-agent comparison script</span>
<span class="course-link-path">chapter4/collaboration-tools/subagent_comparison.py</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What should the Agent do safely while waiting for a user's decision?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 17</div>

<div class="course-next">Allow events to arrive while the Agent is already working.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
