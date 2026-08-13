---
theme: seriph
title: "Lesson 27 — When Should You Teach with Examples—and When with Rewards?"
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

# When Should You Teach with Examples—and When with Rewards?

<p class="course-subtitle">SFT, loss masking, distribution shift, and the form-first rule</p>

<div class="course-cover-meta">Lesson 27 of 42 · 19 minutes · SFT; When to Choose SFT and When to Choose RL; Single-Turn Reinforcement Learning</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">Is the target capability a stable mapping to imitate or a strategy that must survive new situations?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>SFT</h3>
<p>Dense token-level supervision; stable and sample-efficient.</p>
</div>
<div class="course-card green">
<h3>RL</h3>
<p>Sparse trajectory feedback; costly but allows exploration.</p>
</div>
<div class="course-card orange">
<h3>Shift</h3>
<p>Test whether the learned behavior survives changed rules and inputs.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Loss masking</h3>
<p>Supervise the assistant response—not the user prompt</p>
</div>
<div class="course-card blue">
<h3>Form first</h3>
<p>Stabilize parsable output before optimizing strategy</p>
</div>
<div class="course-card green">
<h3>Holdout shift</h3>
<p>Change values or environments while preserving the rule</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig7-11.svg" alt="SFT followed by RL as a two-stage training pipeline">

<div class="course-caption">SFT followed by RL as a two-stage training pipeline</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Use SFT vs. Consider RL

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Use SFT</h3><ul><li>Known demonstrations</li><li>Format/style/protocol</li><li>Deployment matches training</li></ul></div>
<div class="course-card green"><h3>Consider RL</h3><ul><li>Outcome can be verified</li><li>Many valid strategies</li><li>Generalization under shift matters</li></ul></div>
</div>

<div class="course-caption course-caption-strong">SFT and RL are sequential tools—not rival ideologies.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# SFT masks the prompt tokens

~~~python
tokens = prompt_ids + response_ids
labels = [-100] * len(prompt_ids) + response_ids
loss = cross_entropy(model(tokens), labels)
loss.backward()
# only the demonstrated response is supervised
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>7-4 evidence</span><span>2 min</span></div>
<h3>Audit retained VLM pre-training and SFT evidence</h3>
<p><strong>Observe:</strong> Hashed outputs, blind judgments, matched configurations, and negative results</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>7-5 evidence</span><span>2 min</span></div>
<h3>Audit continued-pretraining trade-offs</h3>
<p><strong>Observe:</strong> New-language gain, retained English ability, and persistent factual errors</p>
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
$ python chapter7/MiniMind-pretrain/validation/validate_vlm_evidence.py

$ python chapter7/continued-pretraining/validation/validate_evidence.py
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>SFT efficiently learns explicit protocols represented in examples.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>RL is justified when a verifier can reward strategies beyond one reference answer.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Training gains must be tested beside retention and distribution-shift failures.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">The slogan 'SFT memorizes, RL generalizes' is a tendency under controlled conditions—not a guarantee for every model and task.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Use SFT until output is stable; add RL only when exploration and verified generalization justify its cost.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-3 gap-4 mt-6">
<a class="course-link" href="../chapter7/MiniMind-pretrain/">
<span class="course-link-title">Experiment 7-3: MiniMind language training</span>
<span class="course-link-path">chapter7/MiniMind-pretrain/</span>
</a>
<a class="course-link" href="../chapter7/SFTvsRL/">
<span class="course-link-title">Experiment 7-11: SFT vs. RL reproduction</span>
<span class="course-link-path">chapter7/SFTvsRL/</span>
</a>
<a class="course-link" href="../chapter7/sesame/">
<span class="course-link-title">Experiment 7-6: Sesame speech SFT</span>
<span class="course-link-path">chapter7/sesame/</span>
</a>
<a class="course-link" href="../chapter7/orpheus/">
<span class="course-link-title">Experiment 7-6: Orpheus speech SFT</span>
<span class="course-link-path">chapter7/orpheus/</span>
</a>
<a class="course-link" href="../chapter7/MultilingualReasoning/">
<span class="course-link-title">Experiment 7-7: multilingual reasoning</span>
<span class="course-link-path">chapter7/MultilingualReasoning/</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What deployment change would reveal that your fine-tuned model learned an example instead of a rule?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 28</div>

<div class="course-next">Translate preferences and outcomes into optimization signals without losing the base policy.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
