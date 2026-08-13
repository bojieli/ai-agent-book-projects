---
theme: seriph
title: "Lesson 31 — How Can a Model Learn to Use Tools with Fewer Samples?"
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

# How Can a Model Learn to Use Tools with Fewer Samples?

<p class="course-subtitle">Tool-call RL, sandbox feedback, distillation, and practical boundaries</p>

<div class="course-cover-meta">Lesson 31 of 42 · 17 minutes · RL for Learning Tool Calling; Sample Efficiency; On-Policy Distillation; Practical Tips</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">How do we teach a model a policy over tools when most trajectories fail and every rollout is expensive?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Combinatorics</h3>
<p>Tool, argument, order, and stopping choices multiply quickly.</p>
</div>
<div class="course-card green">
<h3>Grounding</h3>
<p>Sandbox and environment feedback reveal what language alone cannot.</p>
</div>
<div class="course-card orange">
<h3>Dense teaching</h3>
<p>Distillation supplies token-level targets on the student's own paths.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>ReTool</h3>
<p>Interleave text, code calls, and sandbox observations</p>
</div>
<div class="course-card blue">
<h3>On-policy distillation</h3>
<p>Teacher scores the student's current trajectories token by token</p>
</div>
<div class="course-card green">
<h3>Self-distillation</h3>
<p>Privileged context turns the same model into a teacher</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig7-16.svg" alt="Tool-calling reinforcement learning reward loop">

<div class="course-caption">Tool-calling reinforcement learning reward loop</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Scalar RL signal vs. Dense distillation

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Scalar RL signal</h3><ul><li>One reward per trajectory</li><li>Many samples wasted</li><li>Can discover beyond teacher</li></ul></div>
<div class="course-card green"><h3>Dense distillation</h3><ul><li>Signal at each token</li><li>Higher sample efficiency</li><li>Teacher or privileged context required</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Both methods need trajectories shaped like real Agent interaction.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Learn on the student's own trajectory

~~~python
trajectory = student.rollout(task, tools)
teacher_logits = teacher.score(trajectory, privileged_info)
student_logits = student.score(trajectory)
loss = token_kl(student_logits, teacher_logits)
update(student, loss)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>7-9 preflight</span><span>2 min</span></div>
<h3>Check whether a CoT student-training run is actually ready</h3>
<p><strong>Observe:</strong> Data hash, sample count, dependencies, trainer compatibility, and CUDA readiness</p>
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
$ cd chapter7/cot-distillation && python train_student.py --preflight --train-data data/sft_cot_distill_aime_kimi_k3.jsonl --preflight-output validation/course-preflight.json
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Tool learning needs the same observation/action protocol at training and deployment.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Dense teacher distributions can succeed where sparse RL stalls.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>A preflight separates a configured recipe from a completed training claim.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Distillation cannot exceed information available to the teacher or privileged context, and GPU readiness is not training evidence.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Match rollout shape to deployment, preserve tool feedback, and choose the densest trustworthy signal available.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-3 gap-4 mt-6">
<a class="course-link" href="../chapter7/retool/">
<span class="course-link-title">Experiment 7-15: ReTool</span>
<span class="course-link-path">chapter7/retool/</span>
</a>
<a class="course-link" href="../chapter7/AWorld-train/">
<span class="course-link-title">Experiment 7-16: AWorld training</span>
<span class="course-link-path">chapter7/AWorld-train/</span>
</a>
<a class="course-link" href="../chapter7/AWorld/">
<span class="course-link-title">AWorld source checkout</span>
<span class="course-link-path">chapter7/AWorld/</span>
</a>
<a class="course-link" href="../book-en/chapter7.md">
<span class="course-link-title">On-policy distillation discussion</span>
<span class="course-link-path">book-en/chapter7.md</span>
</a>
<a class="course-link" href="../book-en/images/fig7-18.svg">
<span class="course-link-title">Tool ecosystem architecture</span>
<span class="course-link-path">book-en/images/fig7-18.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Could privileged information make your current model a useful teacher for itself?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Chapter 7 complete · Next · Lesson 32</div>

<div class="course-next">Move learning beyond model weights into knowledge, instructions, programs, and the updater itself.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
