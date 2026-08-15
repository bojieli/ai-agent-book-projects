---
theme: seriph
title: "Lesson 09 — How Can an Agent Stay Oriented in a Long Task?"
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

# How Can an Agent Stay Oriented in a Long Task?

<p class="course-subtitle">Status bars, physical time, context rot, and compression</p>

<div class="course-cover-meta">Lesson 09 of 42 · 19 minutes · Agent Status Bar; Context Compression; Isolation Over Compression</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">Why does an Agent lose track of progress even before its context window is full?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Context rot</h3>
<p>Relevant facts remain present but become hard to retrieve.</p>
</div>
<div class="course-card green">
<h3>Implicit state</h3>
<p>Progress and time are scattered across the trajectory.</p>
</div>
<div class="course-card orange">
<h3>Compression</h3>
<p>Raw history must become high-density working state.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Status bar</h3>
<p>Explicit task, time, budget, and progress state</p>
</div>
<div class="course-card blue">
<h3>Hierarchical compression</h3>
<p>Preserve recent detail and summarize older phases</p>
</div>
<div class="course-card green">
<h3>Isolation</h3>
<p>Move independent work into separate contexts</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig2-16.svg" alt="Comparison of context compression strategies">

<div class="course-caption">Comparison of context compression strategies</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Long raw trajectory vs. Engineered working set

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Long raw trajectory</h3><ul><li>Repeated observations</li><li>Low information density</li><li>Reasoning cost grows</li></ul></div>
<div class="course-card green"><h3>Engineered working set</h3><ul><li>Explicit current state</li><li>Compressed completed phases</li><li>Isolated sub-tasks</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The goal is usable information—not maximum token retention.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Make hidden state explicit

~~~python
status = {
  "goal": task.goal,
  "done": completed_steps,
  "budget": remaining_steps,
  "elapsed": clock.elapsed()
}
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>2-8</span><span>1 min</span></div>
<h3>Preview the injected status information</h3>
<p><strong>Observe:</strong> Task progress, time, tool count, and remaining budget</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>2-9</span><span>3 min</span></div>
<h3>Compare compression strategies</h3>
<p><strong>Observe:</strong> What each strategy preserves, discards, and recomputes</p>
</div>
</div>

<div class="course-caption course-caption-strong">Demo budget: 4 minutes · one contiguous terminal block</div>

<!-- Presenter cue: State the prediction before running anything. Name the observation that could disconfirm it. -->

---
class: course-terminal
---

<div class="course-kicker">Live demo</div>

# Switching to the terminal

~~~bash
$ uv run python chapter2/system-hint/main.py --mode preview

$ uv run python chapter2/context-compression/experiment.py --list-strategies
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>A status bar turns repeated inference into direct retrieval.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Compression is needed for information density before token overflow.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Independent sub-tasks are often better isolated than summarized.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">An incorrect status bar can be more harmful than missing meta-information because the Agent trusts it.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Compress completed history into verifiable state; keep recent evidence available; isolate independent work.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter2/attention_visualization/run_status_bar_experiment.py">
<span class="course-link-title">Experiment 2-7: status-bar attention</span>
<span class="course-link-path">chapter2/attention_visualization/run_status_bar_experiment.py</span>
</a>
<a class="course-link" href="../chapter2/context-compression/run_all_strategies.py">
<span class="course-link-title">Run all six compression strategies</span>
<span class="course-link-path">chapter2/context-compression/run_all_strategies.py</span>
</a>
<a class="course-link" href="../book-en/images/fig2-15.svg">
<span class="course-link-title">Status insertion position</span>
<span class="course-link-path">book-en/images/fig2-15.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig2-17.svg">
<span class="course-link-title">Compression processing flow</span>
<span class="course-link-path">book-en/images/fig2-17.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which fields in a status bar can be computed deterministically instead of inferred by the model?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Chapter 2 complete · Next · Lesson 10</div>

<div class="course-next">Extend working context across sessions without turning memory into noise.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
