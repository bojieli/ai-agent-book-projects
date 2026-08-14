---
theme: seriph
title: "Lesson 33 — Where Should an Agent Store What It Learns?"
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

<div class="course-kicker">Improve · Chapter 8 · Continual Evolution</div>

# Where Should an Agent Store What It Learns?

<p class="course-subtitle">Knowledge, instructions, programs, parameters, and meta-updates</p>

<div class="course-cover-meta">Lesson 33 of 42 · 19 minutes · Four Methods for Continual Agent Evolution; Updating the Update Method</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">Which representation makes a new capability easiest to verify, retrieve, change, and retire?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Knowledge</h3>
<p>Facts and experience remain traceable and editable.</p>
</div>
<div class="course-card green">
<h3>Instructions</h3>
<p>General procedures guide the model at inference time.</p>
</div>
<div class="course-card orange">
<h3>Programs</h3>
<p>Deterministic workflows enforce repeatable behavior.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Parameters</h3>
<p>Implicit perception, style, and broad policies</p>
</div>
<div class="course-card blue">
<h3>Local patch</h3>
<p>Change the smallest artifact that explains the failure</p>
</div>
<div class="course-card green">
<h3>Meta-update</h3>
<p>Improve the updater or workflow that creates artifacts</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig1-1.svg" alt="Three levels of persistent Agent capability updates">

<div class="course-caption">Three levels of persistent Agent capability updates</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Prompt patch vs. Program promotion

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Prompt patch</h3><ul><li>Fast to deploy</li><li>Easy to inspect</li><li>Global rules accumulate</li></ul></div>
<div class="course-card green"><h3>Program promotion</h3><ul><li>Deterministic execution</li><li>Tests and versioning</li><li>Narrower applicability</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The most powerful update is not always the safest or cheapest one.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Route a lesson to the smallest carrier

~~~python
if lesson.is_fact: update_knowledge(lesson)
elif lesson.is_rule: patch_skill(lesson)
elif lesson.is_deterministic: compile_workflow(lesson)
else: propose_parameter_training(lesson)
validate_transfer_and_retention()
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>8-4</span><span>2 min</span></div>
<h3>Compile browser experience into a replayable workflow</h3>
<p><strong>Observe:</strong> State predicates, reset-and-replay, and failure when the page state changes</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>Tool evolution</span><span>2 min</span></div>
<h3>Create, validate, register, and reuse an offline tool</h3>
<p><strong>Observe:</strong> Search miss, candidate creation, rejection gate, registration, and later reuse</p>
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
$ cd chapter8/browser-use-rpa && python workflow_validation_demo.py

$ cd chapter8/self-evolving-tools && python demo.py --offline
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Knowledge is easiest to trace; programs are easiest to execute deterministically.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Reusable tools convert one successful solution into a new action capability.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Local, reversible changes make causal evaluation and rollback possible.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A compiled workflow is brittle when its state predicates fail to capture meaningful environmental change.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Choose the most explicit, local, reversible representation that can express the capability reliably.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter8/prompt-auto-optimization/">
<span class="course-link-title">Experiment 8-3: prompt auto-optimization</span>
<span class="course-link-path">chapter8/prompt-auto-optimization/</span>
</a>
<a class="course-link" href="../chapter8/prompt-distillation/">
<span class="course-link-title">Experiment 7-8: prompt distillation</span>
<span class="course-link-path">chapter8/prompt-distillation/</span>
</a>
<a class="course-link" href="../chapter8/browser-use-rpa/README.md">
<span class="course-link-title">Real browser-use extension</span>
<span class="course-link-path">chapter8/browser-use-rpa/README.md</span>
</a>
<a class="course-link" href="../chapter8/self-evolving-tools/">
<span class="course-link-title">Self-evolving tool library</span>
<span class="course-link-path">chapter8/self-evolving-tools/</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Could the behavior you want be a testable program instead of another sentence in the system prompt?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 34</div>

<div class="course-next">Govern the complete loop so an improvement cannot approve or conceal its own regression.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
