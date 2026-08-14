---
theme: seriph
title: "Lesson 41 — When Is Multi-Agent Actually Better Than One Agent?"
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

# When Is Multi-Agent Actually Better Than One Agent?

<p class="course-subtitle">Information gain, parallelism, verification, budgets, and cost</p>

<div class="course-cover-meta">Lesson 41 of 42 · 18 minutes · When Is Multi-Agent Truly Better; Parallel Coordination; Budget Awareness</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">What does collaboration add that a single Agent with the same compute could not obtain?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>New evidence</h3>
<p>Execution, rendering, browsing, and independent observations change the answer.</p>
</div>
<div class="course-card green">
<h3>Parallel time</h3>
<p>Independent searches reduce wall-clock latency when resources allow.</p>
</div>
<div class="course-card orange">
<h3>Cost</h3>
<p>Multi-Agent systems may spend several times—or an order of magnitude—more tokens.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Information gain</h3>
<p>The verifier observes something unavailable at generation time</p>
</div>
<div class="course-card blue">
<h3>Single settlement</h3>
<p>One success can resolve the task and stop siblings</p>
</div>
<div class="course-card green">
<h3>Budget awareness</h3>
<p>Strategy changes with remaining steps and task value</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig10-8.svg" alt="Parallel web research architecture">

<div class="course-caption">Parallel web research architecture</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# More voices vs. More observations

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>More voices</h3><ul><li>Same text</li><li>Same evidence</li><li>More samples and debate</li></ul></div>
<div class="course-card green"><h3>More observations</h3><ul><li>Independent tools</li><li>Execution or visual feedback</li><li>Parallel environment interaction</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The advantage comes from information—not the number of Agent labels.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Settle once; cancel the rest

~~~python
jobs = spawn_parallel(search_shards)
for result in as_completed(jobs):
    evidence.merge(result.receipts)
    if verifier.sufficient(evidence):
        cancel_all(jobs); break
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>10-6</span><span>3 min</span></div>
<h3>Run parallel web research with independent browsers</h3>
<p><strong>Observe:</strong> Cited evidence, browser isolation, parallel speedup, timeout handling, and cleanup</p>
</div>
</div>

<div class="course-caption course-caption-strong">Demo budget: 3 minutes · one contiguous terminal block</div>

<!-- Presenter cue: State the prediction before running anything. Name the observation that could disconfirm it. -->

---
class: course-terminal
---

<div class="course-kicker">Live demo</div>

# Switching to the terminal

~~~bash
$ cd chapter10/parallel-web-research && python demo.py
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Debate over identical evidence often matches a single Agent at equal compute.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>External feedback can nearly double performance because it adds observations.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Parallel speedup is real only when setup, contention, and cancellation costs are included.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A speedup on one site and network condition does not prove lower total cost or better answer quality for every research task.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Add an Agent only when it owns a distinct observation, permission boundary, artifact, or parallelizable environment interaction.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter10/parallel-web-research/validation/">
<span class="course-link-title">Parallel research acceptance evidence</span>
<span class="course-link-path">chapter10/parallel-web-research/validation/</span>
</a>
<a class="course-link" href="../book-en/images/fig10-3.svg">
<span class="course-link-title">Proposer-reviewer loop</span>
<span class="course-link-path">book-en/images/fig10-3.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig10-7.svg">
<span class="course-link-title">Phone + computer dual-Agent architecture</span>
<span class="course-link-path">book-en/images/fig10-7.svg</span>
</a>
<a class="course-link" href="../chapter10/book-translation/">
<span class="course-link-title">Book translation Agent comparison</span>
<span class="course-link-path">chapter10/book-translation/</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What new information does your proposed second Agent obtain that the first Agent cannot?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 42</div>

<div class="course-next">Engineer against coordination failures—and examine what appears when Agent populations become societies.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
