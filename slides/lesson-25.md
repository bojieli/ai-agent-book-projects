---
theme: seriph
title: "Lesson 25 — Did the Agent Improve—or Did the Numbers Move?"
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

# Did the Agent Improve—or Did the Numbers Move?

<p class="course-subtitle">Significance, observability, ablations, and production evaluation</p>

<div class="course-cover-meta">Lesson 25 of 42 · 17 minutes · Statistical Significance; Agent Observability; Internal Evaluation Infrastructure; Simulation Fidelity</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">What evidence is required before an evaluation delta becomes an engineering decision?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Uncertainty</h3>
<p>Repeated samples expose variance and paired differences.</p>
</div>
<div class="course-card green">
<h3>Observability</h3>
<p>Traces connect aggregate regressions to mechanisms.</p>
</div>
<div class="course-card orange">
<h3>Release control</h3>
<p>Feature flags, A/B tests, rollback, and privacy-aware analytics</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Paired test</h3>
<p>Run old and new systems on the same cases</p>
</div>
<div class="course-card blue">
<h3>Confidence interval</h3>
<p>Report a plausible range—not only a mean</p>
</div>
<div class="course-card green">
<h3>Two-layer flags</h3>
<p>Separate mechanism enablement from experiment assignment</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig6-6.svg" alt="Observability technology stack for Agent systems">

<div class="course-caption">Observability technology stack for Agent systems</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Scoreboard vs. Evaluation infrastructure

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Scoreboard</h3><ul><li>One aggregate</li><li>No trace linkage</li><li>Manual reruns</li></ul></div>
<div class="course-card green"><h3>Evaluation infrastructure</h3><ul><li>Slices + uncertainty</li><li>Trajectory-level observability</li><li>Repeatable release gates</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The purpose of a benchmark report is to generate testable hypotheses.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Pair cases before estimating the delta

~~~python
deltas = [new[c] - old[c] for c in shared_cases]
estimate, interval = bootstrap_mean(deltas)
if interval.low <= 0: hold_release()
else: canary(new_system)
monitor_slices_and_rollback()
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>6-3 evidence</span><span>2 min</span></div>
<h3>Rebuild and audit structured-judge evidence</h3>
<p><strong>Observe:</strong> Case coverage, immutable source hashes, judge dimensions, and veto records</p>
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
$ cd chapter6/user-memory-system-evaluation && python build_63_evidence.py
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Paired case-level analysis is more sensitive than comparing unrelated averages.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Traces make a regression actionable by revealing the failing mechanism.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Evaluation becomes production infrastructure when it controls release and rollback.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Statistical significance does not imply practical importance, dataset validity, or simulation fidelity.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Ship only deltas that are repeatable, practically meaningful, slice-safe, and traceable to a plausible mechanism.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter6/android-world/">
<span class="course-link-title">Experiment 6-11: AndroidWorld failure analysis</span>
<span class="course-link-path">chapter6/android-world/</span>
</a>
<a class="course-link" href="../chapter6/openvla-robotwin2-eval/">
<span class="course-link-title">Experiment 6-12: OpenVLA + RoboTwin2</span>
<span class="course-link-path">chapter6/openvla-robotwin2-eval/</span>
</a>
<a class="course-link" href="../book-en/images/fig6-8.svg">
<span class="course-link-title">Simulation fidelity spectrum</span>
<span class="course-link-path">book-en/images/fig6-8.svg</span>
</a>
<a class="course-link" href="../book-en/chapter6.md">
<span class="course-link-title">Production evaluation chapter</span>
<span class="course-link-path">book-en/chapter6.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What would make a statistically significant improvement too small or too risky to ship?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Chapter 6 complete · Next · Lesson 26</div>

<div class="course-next">Use the evaluation environment as the practice ground for changing model behavior.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
