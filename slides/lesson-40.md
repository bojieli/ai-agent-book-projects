---
theme: seriph
title: "Lesson 40 — Who Should Coordinate Independent Agents?"
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

<div class="course-kicker">Expand · Chapter 10 · Multi-Agent Collaboration</div>

# Who Should Coordinate Independent Agents?

<p class="course-subtitle">Peer review, managers, decentralized handoffs, files, and control planes</p>

<div class="course-cover-meta">Lesson 40 of 42 · 17 minutes · Non-Shared Context; File System; Communication and Control; Collaboration Topologies; A2A</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">When Agents work in separate contexts, what structure keeps their work coherent?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Peer loop</h3>
<p>A proposer and reviewer iterate with independent evidence.</p>
</div>
<div class="course-card green">
<h3>Manager</h3>
<p>One planner decomposes, budgets, schedules, and integrates.</p>
</div>
<div class="course-card orange">
<h3>Decentralized</h3>
<p>Peers transfer work without a runtime central controller.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Data plane</h3>
<p>Workspaces, shared artifacts, external and system mounts</p>
</div>
<div class="course-card blue">
<h3>Control plane</h3>
<p>Spawn, message, status, terminate, and resource scheduling</p>
</div>
<div class="course-card green">
<h3>Handoff package</h3>
<p>Goal + evidence + artifacts + open questions + acceptance</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig10-4.svg" alt="Manager architecture for sequential multi-Agent coordination">

<div class="course-caption">Manager architecture for sequential multi-Agent coordination</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Manager topology vs. Decentralized topology

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Manager topology</h3><ul><li>Global plan</li><li>Simple supervision</li><li>Planner is bottleneck</li></ul></div>
<div class="course-card green"><h3>Decentralized topology</h3><ul><li>Local ownership</li><li>Flexible handoffs</li><li>Harder global consistency</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Topology determines where planning errors and coordination costs accumulate.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Pass artifacts; observe lifecycle

~~~python
job = manager.spawn(role, goal, budget)
manager.message(job, evidence_paths)
while job.running: manager.observe(job.status)
result = manager.verify(job.artifacts)
manager.cancel_dependents_if_satisfied(result)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>10-3</span><span>2 min</span></div>
<h3>Rehearse a four-role translation orchestration</h3>
<p><strong>Observe:</strong> Manager plan, glossary ownership, chapter budgets, proofreading, and integration</p>
</div>
</div>

<div class="course-caption course-caption-strong">Demo budget: 2 minutes · one contiguous terminal block</div>

<!-- Presenter cue: State the prediction before running anything. Name the observation that could disconfirm it. -->

---
class: course-terminal
---

<div class="course-kicker">Live demo</div>

# Switching to the terminal

~~~bash
$ cd chapter10/book-translation && python demo.py --dry-run
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Files handle large persistent artifacts; messages handle asynchronous coordination.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>The manager's decomposition quality caps the value of stronger workers.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Explicit status and termination semantics matter as much as task prompts.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A dry-run proves the orchestration graph and budgets—not translation quality or multi-Agent advantage.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Make ownership, artifact contracts, lifecycle states, budgets, and termination paths explicit before adding Agents.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-3 gap-4 mt-6">
<a class="course-link" href="../chapter10/autonomous-phone-registration/">
<span class="course-link-title">Experiment 10-3: fixed baseline + autonomous phone registration</span>
<span class="course-link-path">chapter10/autonomous-phone-registration/ (TalkAct baseline)</span>
</a>
<a class="course-link" href="../book-en/images/fig10-2.svg">
<span class="course-link-title">Agent virtual file system</span>
<span class="course-link-path">book-en/images/fig10-2.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig10-6.svg">
<span class="course-link-title">Manager parallel coordination</span>
<span class="course-link-path">book-en/images/fig10-6.svg</span>
</a>
<a class="course-link" href="../book-en/chapter10.md">
<span class="course-link-title">A2A and decentralized handoffs</span>
<span class="course-link-path">book-en/chapter10.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">If the manager decomposes the task incorrectly, which independent gate can detect the mistake before workers waste their budgets?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 41</div>

<div class="course-next">Test whether multiple Agents create new information or merely spend more tokens.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
