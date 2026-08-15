---
theme: seriph
title: "Lesson 24 — Which Agent Should You Ship?"
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

<div class="course-kicker">Improve · Chapter 6 · Agent Evaluation</div>

# Which Agent Should You Ship?

<p class="course-subtitle">Model behavior, latency, cost, and evaluation-driven selection</p>

<div class="course-cover-meta">Lesson 24 of 42 · 19 minutes · Evaluation-Driven Model Selection; Model Behavior; Cost Analysis; Continuous Iteration</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">Why is the highest benchmark score not enough to choose a production Agent?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Quality</h3>
<p>Success, boundary behavior, and variance across task slices</p>
</div>
<div class="course-card green">
<h3>Behavior</h3>
<p>When the model searches, edits, retries, or stops</p>
</div>
<div class="course-card orange">
<h3>Economics</h3>
<p>Latency, cache use, tokens, availability, and total task cost</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Fixed Harness</h3>
<p>Swap models to locate a model-side bottleneck</p>
</div>
<div class="course-card blue">
<h3>Ablation</h3>
<p>Remove one Harness component to measure its contribution</p>
</div>
<div class="course-card green">
<h3>Pareto frontier</h3>
<p>Choose a non-dominated quality/cost/latency point</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig6-7.svg" alt="Loop from benchmark results to system improvements">

<div class="course-caption">Loop from benchmark results to system improvements</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Leaderboard choice vs. Deployment choice

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Leaderboard choice</h3><ul><li>One public score</li><li>Unknown Harness</li><li>Average case</li></ul></div>
<div class="course-card green"><h3>Deployment choice</h3><ul><li>Your task distribution</li><li>Your complete Harness</li><li>Cost and failure boundaries</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The unit of selection is model + context + tools + runtime.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Filter before ranking

~~~python
eligible = [r for r in runs if r.safety_pass]
eligible = [r for r in eligible if r.p95_latency < sla]
frontier = pareto(eligible, maximize='success', minimize='cost')
winner = validate_on_holdout(frontier)
ship_with_feature_flag(winner)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>6-8</span><span>2 min</span></div>
<h3>Recompute a full Agent cost breakdown</h3>
<p><strong>Observe:</strong> Per-step cost, cache savings, compression savings, and non-additive interactions</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>6-7</span><span>2 min</span></div>
<h3>Validate a fixed-Harness action-threshold experiment</h3>
<p><strong>Observe:</strong> Event-boundary accounting, first-edit timing, rework, and independent final tests</p>
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
$ cd chapter6/agent-cost-analysis && python demo.py --offline --scenario all

$ python -m unittest discover -s chapter6/model-action-threshold/tests -v
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Different models carry different default tool-use policies inside the same Harness.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Cache-friendly context and compression change cost without changing the task.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>A model upgrade is a hypothesis that must clear your own gates.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A smoke run verifies integration, not steady-state availability, tail latency, or statistical superiority.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Select on a domain-specific Pareto frontier after safety and reliability gates—not on a global leaderboard rank.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter6/model-benchmark/">
<span class="course-link-title">Experiment 6-9: provider/model benchmark</span>
<span class="course-link-path">chapter6/model-benchmark/</span>
</a>
<a class="course-link" href="../chapter6/user-memory-system-evaluation/">
<span class="course-link-title">Experiment 6-10: full memory component matrix</span>
<span class="course-link-path">chapter6/user-memory-system-evaluation/</span>
</a>
<a class="course-link" href="../chapter6/model-action-threshold/results/">
<span class="course-link-title">Action-threshold canonical campaign</span>
<span class="course-link-path">chapter6/model-action-threshold/results/</span>
</a>
<a class="course-link" href="../chapter6/agent-cost-analysis/sample_trace.json">
<span class="course-link-title">Cost-analysis sample trace</span>
<span class="course-link-path">chapter6/agent-cost-analysis/sample_trace.json</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What is the first non-quality gate that would eliminate a model from your production shortlist?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 25</div>

<div class="course-next">Build evaluation infrastructure that can distinguish a real improvement from noise.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
