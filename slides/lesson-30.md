---
theme: seriph
title: "Lesson 30 — How Do You Reward a Long Agent Trajectory?"
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

<div class="course-kicker">Improve · Chapter 7 · Model Post-Training</div>

# How Do You Reward a Long Agent Trajectory?

<p class="course-subtitle">Credit assignment, reward density, process signals, and path penalties</p>

<div class="course-cover-meta">Lesson 30 of 42 · 17 minutes · From Single-Turn to Multi-Turn; Credit Assignment; Process vs. Outcome Reward; RLVP</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">When the final result fails, which earlier tool choice should the model change?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Sparse outcome</h3>
<p>One final bit leaves most actions unexplained.</p>
</div>
<div class="course-card green">
<h3>Process evidence</h3>
<p>Tool errors and rule violations identify local mistakes.</p>
</div>
<div class="course-card orange">
<h3>Partial credit</h3>
<p>Reachable progress can rescue information from all-fail groups.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Outcome reward</h3>
<p>Score the completed task—not a convenient proxy</p>
</div>
<div class="course-card blue">
<h3>Process reward</h3>
<p>Evaluate intermediate reasoning or actions</p>
</div>
<div class="course-card green">
<h3>RLVP</h3>
<p>Reward the outcome; penalize verified path violations</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig7-15.svg" alt="Credit assignment across a multi-turn interaction">

<div class="course-caption">Credit assignment across a multi-turn interaction</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Outcome only vs. Outcome + path evidence

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Outcome only</h3><ul><li>Objective final target</li><li>Simple verifier</li><li>Very sparse credit</li></ul></div>
<div class="course-card green"><h3>Outcome + path evidence</h3><ul><li>Retains final goal</li><li>Uses observed violations</li><li>Denser diagnosis</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Path signals should constrain the route without replacing the destination.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Separate success from path violations

~~~python
outcome = task_verifier(final_state)
violations = rule_verifier(trajectory)
progress = reachable_subgoals(trajectory)
reward = outcome - penalty(violations)
reward += partial_credit(progress, only_if_all_fail=True)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>7-14 gates</span><span>2 min</span></div>
<h3>Run verifier regressions for trajectory data</h3>
<p><strong>Observe:</strong> Malformed samples rejected before they can become supervision</p>
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
$ python -m pytest chapter7/cot-distillation/test_student_pipeline.py chapter7/cot-distillation/test_empty_problems.py -q
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Multi-turn tasks turn one outcome into a temporal attribution problem.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Environment feedback contains information that scalar outcome rewards discard.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>A process metric becomes dangerous when it is easier to optimize than the real goal.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">An LLM process judge can reward plausible-looking steps that did not causally produce the outcome.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Keep an objective outcome gate, add only externally verified path signals, and test explicitly for reward hacking.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter7/RLVP/">
<span class="course-link-title">Experiment 7-14: RLVP reproduction guide</span>
<span class="course-link-path">chapter7/RLVP/</span>
</a>
<a class="course-link" href="../chapter7/SpatialReasoning/">
<span class="course-link-title">Experiment 7-12: spatial reasoning</span>
<span class="course-link-path">chapter7/SpatialReasoning/</span>
</a>
<a class="course-link" href="../chapter7/SimpleVLA-RL/">
<span class="course-link-title">Experiment 7-13: SimpleVLA-RL</span>
<span class="course-link-path">chapter7/SimpleVLA-RL/</span>
</a>
<a class="course-link" href="../book-en/images/fig7-reward-density.svg">
<span class="course-link-title">Reward density spectrum</span>
<span class="course-link-path">book-en/images/fig7-reward-density.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which intermediate signal in your Agent is evidence of progress, and which is merely correlated with it?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 31</div>

<div class="course-next">Apply these signals to the combinatorial problem of learning when and how to call tools.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
