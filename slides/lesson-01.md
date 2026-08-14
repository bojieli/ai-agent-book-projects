---
theme: seriph
title: "Lesson 01 — How Do We Replace Agent Intuition with Evidence?"
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

<div class="course-kicker">Build · Introduction · Orientation</div>

# How Do We Replace Agent Intuition with Evidence?

<p class="course-subtitle">A practice-first map of AI Agents in Depth</p>

<div class="course-cover-meta">Lesson 01 of 42 · 16 minutes · Introduction; Book Structure; How to Read This Book</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">Why do impressive Agent demos so often fail to become reliable products?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Demo success</h3>
<p>One lucky trajectory proves possibility—not reliability.</p>
</div>
<div class="course-card green">
<h3>Engineering judgment</h3>
<p>Every design choice needs a mechanism and a trade-off.</p>
</div>
<div class="course-card orange">
<h3>Scientific progress</h3>
<p>Without evaluation, change is indistinguishable from luck.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Build</h3>
<p>Context, knowledge, tools, and code generation</p>
</div>
<div class="course-card blue">
<h3>Improve</h3>
<p>Evaluation, post-training, and continual evolution</p>
</div>
<div class="course-card green">
<h3>Expand</h3>
<p>Voice, Computer Use, robotics, and collaboration</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig0-2.svg" alt="The four-part structure of the book">

<div class="course-caption">The four-part structure of the book</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Demo-driven vs. Principle-driven

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Demo-driven</h3><ul><li>Start with a framework</li><li>Celebrate one successful run</li><li>Change prompts by intuition</li></ul></div>
<div class="course-card green"><h3>Principle-driven</h3><ul><li>Start with a failure mode</li><li>Run a controlled comparison</li><li>Turn evidence into a design rule</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The course follows the right-hand loop.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# The course's experimental loop

~~~python
question = define_failure_mode()
hypothesis = predict_mechanism(question)
evidence = run_controlled_experiment(hypothesis)
rule = interpret(evidence, limitations=True)
evaluate(rule)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>Course tour</span><span>1 min</span></div>
<h3>Inspect one companion experiment before running it</h3>
<p><strong>Observe:</strong> Entry point, modes, providers, outputs, and reproducibility controls</p>
</div>
</div>

<div class="course-caption course-caption-strong">Demo budget: 1 minute · one contiguous terminal block</div>

<!-- Presenter cue: State the prediction before running anything. Name the observation that could disconfirm it. -->

---
class: course-terminal
---

<div class="course-kicker">Live demo</div>

# Switching to the terminal

~~~bash
$ uv run python chapter1/context/main.py --help
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>The book is organized around recurring engineering questions, not products.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Experiments expose mechanisms through controls, ablations, and receipts.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>The author's interpretation—not terminal output alone—is the course's value.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A short lesson cannot reproduce every long-running campaign. It can make the protocol and evidence traceable.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Never present an Agent result without first stating what would count as success or failure.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../docs/en/LEARNING.md">
<span class="course-link-title">Learning paths</span>
<span class="course-link-path">docs/en/LEARNING.md</span>
</a>
<a class="course-link" href="../book-en/introduction.md">
<span class="course-link-title">Book prerequisites</span>
<span class="course-link-path">book-en/introduction.md</span>
</a>
<a class="course-link" href="../docs/en/README.md">
<span class="course-link-title">Companion project index</span>
<span class="course-link-path">docs/en/README.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which Agent claim have you accepted after seeing only one successful run?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Introduction complete · Next · Lesson 02</div>

<div class="course-next">Define an Agent by the interfaces that connect it to the world.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
