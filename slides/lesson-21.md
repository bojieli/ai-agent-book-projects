---
theme: seriph
title: "Lesson 21 — How Can Code Let an Agent Create New Capabilities?"
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

<div class="course-kicker">Build · Chapter 5 · Coding Agents</div>

# How Can Code Let an Agent Create New Capabilities?

<p class="course-subtitle">Adapters, generative UI, hot repair, and Agent bootstrapping</p>

<div class="course-cover-meta">Lesson 21 of 42 · 19 minutes · Code as a System Adapter; Generative UI; Agent Bootstrapping</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Adapter</h3>
<p>Translate unstable external formats into stable internal ones.</p>
</div>
<div class="course-card green">
<h3>Interface</h3>
<p>Generate a UI that matches the current intent.</p>
</div>
<div class="course-card orange">
<h3>Bootstrap</h3>
<p>Create a specialized Agent from a validated reference.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Hot repair</h3>
<p>Failure sample → generated parser → tests → registration</p>
</div>
<div class="course-card blue">
<h3>Artifact pattern</h3>
<p>Pass paths and queries instead of moving large data through tokens</p>
</div>
<div class="course-card green">
<h3>Validated generation</h3>
<p>Compile, test, scan, and exercise generated Agents</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig5-11.svg" alt="Pipeline of an Agent that creates Agents">

<div class="course-caption">Pipeline of an Agent that creates Agents</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# One-off generation vs. Capability creation

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>One-off generation</h3><ul><li>Produces an artifact</li><li>Capability disappears after task</li><li>No reuse gate</li></ul></div>
<div class="course-card green"><h3>Capability creation</h3><ul><li>Packages implementation</li><li>Validates and versions it</li><li>Reuses on later tasks</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Bootstrapping begins when output becomes part of the next Agent.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Capability promotion needs gates

~~~python
candidate = agent.generate_tool(failure_sample)
compile(candidate)
run_security_scan(candidate)
run_regression_tests(candidate)
registry.promote(candidate)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-3 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>5-7</span><span>2 min</span></div>
<h3>Repair an unknown log format</h3>
<p><strong>Observe:</strong> Failure detection, generated parser, tests, and later reuse</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>5-9</span><span>2 min</span></div>
<h3>Generate a dynamic form</h3>
<p><strong>Observe:</strong> Intent gaps converted into fields and cascading constraints</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>5-12</span><span>2 min</span></div>
<h3>Inspect Agent-creation validation gates</h3>
<p><strong>Observe:</strong> Scratch versus template generation, compile, tests, and protocol audit</p>
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
$ uv run python chapter5/adaptive-log-parser/demo.py --offline

$ uv run python chapter5/dynamic-form/demo.py --offline

$ uv run python chapter5/agent-creator/demo.py --no-live --output chapter5/agent-creator/runs/course-smoke
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Generated adapters let a system follow changing data formats.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Generative UI moves structured clarification out of slow chat turns.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Reference-based Agent creation preserves a proven loop while specializing tools.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---

# Boundary → design rule

<div class="course-boundary">Self-modification is unsafe when the Agent can alter the validator that approves its own changes.</div>

<div class="course-rule">Promote generated code into capability only after independent security, functional, and reuse checks.</div>

<!-- Presenter cue: State where the evidence stops, then turn that limitation into a reusable engineering rule. -->

---

# Continue the experiment

<div class="grid grid-cols-3 gap-4 mt-6">
<a class="course-link" href="../chapter5/log-diagnosis/">
<span class="course-link-title">Experiment 5-8: log diagnosis</span>
<span class="course-link-path">chapter5/log-diagnosis/</span>
</a>
<a class="course-link" href="../chapter5/erp-agent/">
<span class="course-link-title">Experiment 5-10: ERP SQL Agent</span>
<span class="course-link-path">chapter5/erp-agent/</span>
</a>
<a class="course-link" href="../chapter5/conversational-ui/">
<span class="course-link-title">Experiment 5-11: conversational UI</span>
<span class="course-link-path">chapter5/conversational-ui/</span>
</a>
<a class="course-link" href="../book-en/images/fig5-8.svg">
<span class="course-link-title">Dynamic form architecture</span>
<span class="course-link-path">book-en/images/fig5-8.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig5-9.svg">
<span class="course-link-title">SQL artifact pattern</span>
<span class="course-link-path">book-en/images/fig5-9.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which generated artifact is safe to reuse, and who decides that it has become a capability?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Build complete · Next · Lesson 22</div>

<div class="course-next">Measure whether any of these architectural changes actually improve the Agent.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
