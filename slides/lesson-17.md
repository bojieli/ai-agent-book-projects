---
theme: seriph
title: "Lesson 17 — How Can a Synchronous Model Live in an Asynchronous World?"
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

# How Can a Synchronous Model Live in an Asynchronous World?

<p class="course-subtitle">Events, interruption, parallelism, and proactive tool discovery</p>

<div class="course-cover-meta">Lesson 17 of 42 · 19 minutes · Event-Driven Asynchronous Agents; Proactive Tool Discovery</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Ingress</h3>
<p>External events can wake the Agent.</p>
</div>
<div class="course-card green">
<h3>Scheduling</h3>
<p>Queue, interrupt, or parallelize by urgency.</p>
</div>
<div class="course-card orange">
<h3>Discovery</h3>
<p>Find a capability without loading every schema.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Event queue</h3>
<p>Durable arrival, priority, and replay</p>
</div>
<div class="course-card blue">
<h3>Cancellation</h3>
<p>Stop work safely and preserve recoverable state</p>
</div>
<div class="course-card green">
<h3>Meta-tool</h3>
<p>Search a large tool catalog on demand</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig4-3.svg" alt="Three asynchronous event-processing strategies">

<div class="course-caption">Three asynchronous event-processing strategies</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Synchronous loop vs. Async Harness

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Synchronous loop</h3><ul><li>One request at a time</li><li>No mid-turn updates</li><li>Tool latency blocks attention</li></ul></div>
<div class="course-card green"><h3>Async Harness</h3><ul><li>Inbox and scheduler</li><li>Interrupt or parallel policy</li><li>Checkpoints and notifications</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The model remains turn-based; the Harness absorbs real-world concurrency.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Events need an explicit policy

~~~python
event = await inbox.get()
match event.urgency:
    case "interrupt": await cancel(current_task)
    case "immediate": spawn(event)
    case _: queue.append(event)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-3 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>4-5</span><span>2 min</span></div>
<h3>Trigger a timed event</h3>
<p><strong>Observe:</strong> Registration, event arrival, processing, and delivery</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>4-6</span><span>2 min</span></div>
<h3>Interrupt and recover a long-running task</h3>
<p><strong>Observe:</strong> Cancellation point, cleanup, checkpoint, and recovery</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>4-7</span><span>2 min</span></div>
<h3>Discover tools instead of injecting the catalog</h3>
<p><strong>Observe:</strong> Token count, retrieved schemas, and selected capability</p>
</div>
</div>

<div class="course-caption course-caption-strong">Demo budget: 6 minutes · one contiguous terminal block</div>

<!-- Presenter cue: State the prediction before running anything. Name the observation that could disconfirm it. -->

---
class: course-terminal
---

<div class="course-kicker">Live demo</div>

# Switching to the terminal

~~~bash
$ uv run python chapter4/agent-with-event-trigger/event_loop_demo.py --mock --trigger timer --delay 2 --duration 6

$ uv run python chapter4/async-agent/demo.py interrupt

$ uv run python chapter4/active-tool-discovery/demo.py --offline
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Priority is a product policy, not merely a queue implementation detail.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Graceful interruption requires tools and loops to expose safe cancellation points.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>On-demand discovery keeps a small stable prefix while preserving a large action space.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---

# Boundary → design rule

<div class="course-boundary">Today's models are trained mostly on synchronous trajectories; async behavior remains a Harness workaround.</div>

<div class="course-rule">Separate event intake, scheduling, model turns, tool execution, and user notification into explicit components.</div>

<!-- Presenter cue: State where the evidence stops, then turn that limitation into a reusable engineering rule. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter4/async-agent/">
<span class="course-link-title">Parallel and state demos</span>
<span class="course-link-path">chapter4/async-agent/</span>
</a>
<a class="course-link" href="../chapter4/active-tool-selection/">
<span class="course-link-title">Active tool selection</span>
<span class="course-link-path">chapter4/active-tool-selection/</span>
</a>
<a class="course-link" href="../book-en/images/fig4-7.svg">
<span class="course-link-title">Hierarchical matching</span>
<span class="course-link-path">book-en/images/fig4-7.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig4-8.svg">
<span class="course-link-title">Dynamic tool cache design</span>
<span class="course-link-path">book-en/images/fig4-8.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which external event should interrupt current work rather than wait in a queue?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Chapter 4 complete · Next · Lesson 18</div>

<div class="course-next">Use code as the most general action interface.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
