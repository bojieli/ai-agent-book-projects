---
theme: seriph
title: "Lesson 29 — Why Do Data and Environments Matter More Than the Algorithm?"
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

# Why Do Data and Environments Matter More Than the Algorithm?

<p class="course-subtitle">Practice grounds, task distributions, synthetic data, and fidelity</p>

<div class="course-cover-meta">Lesson 29 of 42 · 17 minutes · Data and Environment: More Important Than Algorithms; Model-Simulated Environments</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">If PPO and GRPO are available off the shelf, where does the real training advantage come from?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Coverage</h3>
<p>Tasks must span the situations that deployment will create.</p>
</div>
<div class="course-card green">
<h3>Fidelity</h3>
<p>Errors and transitions must resemble the real environment.</p>
</div>
<div class="course-card orange">
<h3>Density</h3>
<p>Useful information should survive filtering and reach the learner.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Task distribution</h3>
<p>Optimize which examples are generated and sampled</p>
</div>
<div class="course-card blue">
<h3>Environment model</h3>
<p>Simulate transitions when the real world is unavailable</p>
</div>
<div class="course-card green">
<h3>Data verifier</h3>
<p>Reject corrupt, ungrounded, or unparseable trajectories</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig7-1.svg" alt="Reinforcement learning agent-environment interaction loop">

<div class="course-caption">Reinforcement learning agent-environment interaction loop</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Algorithm-first vs. Signal-first

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Algorithm-first</h3><ul><li>Tune optimizer knobs</li><li>Reuse weak tasks</li><li>Trust training reward</li></ul></div>
<div class="course-card green"><h3>Signal-first</h3><ul><li>Design task coverage</li><li>Audit environment fidelity</li><li>Measure held-out outcomes</li></ul></div>
</div>

<div class="course-caption course-caption-strong">A better optimizer learns the wrong lesson faster when the world is wrong.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Filter before the trajectory becomes data

~~~python
trajectory = policy.rollout(task, environment)
receipt = verifier.inspect(trajectory)
if receipt.grounded and receipt.complete:
    replay_buffer.add(trajectory, receipt)
sample_balanced(replay_buffer, task_slices)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>7-9 data</span><span>2 min</span></div>
<h3>Inspect verified teacher trajectories before SFT</h3>
<p><strong>Observe:</strong> Sample count, trajectory length, reflective behavior, and verifier failures</p>
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
$ cd chapter7/cot-distillation && python analyze_data.py --sft data/sft_cot_distill_aime_kimi_k3.jsonl --raw data/raw_trajectories_aime_kimi_k3.jsonl
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Training data quality includes task coverage, provenance, and verifier correctness.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>A model-simulated environment can scale practice but transfers its own biases.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Reward curves must be checked against independent deployment-shaped evaluations.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Synthetic diversity does not guarantee real diversity when every example comes from the same generator and assumptions.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Invest first in realistic transitions, difficult boundary cases, and independent verification; tune the optimizer afterward.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter8/prompt-distillation/">
<span class="course-link-title">Experiment 7-8: prompt distillation</span>
<span class="course-link-path">chapter8/prompt-distillation/</span>
</a>
<a class="course-link" href="../chapter7/cot-distillation/">
<span class="course-link-title">Experiment 7-9: CoT distillation</span>
<span class="course-link-path">chapter7/cot-distillation/</span>
</a>
<a class="course-link" href="../chapter7/AdaptThink/">
<span class="course-link-title">Experiment 7-10: adaptive reasoning length</span>
<span class="course-link-path">chapter7/AdaptThink/</span>
</a>
<a class="course-link" href="../book-en/chapter7.md">
<span class="course-link-title">Autodata and simulated-environment discussion</span>
<span class="course-link-path">book-en/chapter7.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which behavior in your simulator is easiest for a policy to exploit but impossible in production?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 30</div>

<div class="course-next">Assign credit when one final outcome depends on many earlier decisions.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
