---
theme: seriph
title: "Lesson 34 — How Can a Self-Modifying Agent Change Without Drifting?"
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

# How Can a Self-Modifying Agent Change Without Drifting?

<p class="course-subtitle">Candidate gates, transfer, retention, rollback, and sleep learning</p>

<div class="course-cover-meta">Lesson 34 of 42 · 19 minutes · Continual-Evolution Closed Loop; Safety Boundaries; Sleep Learning</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">What prevents one mistaken lesson from becoming a permanent production capability?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Isolation</h3>
<p>Online tasks append evidence; offline jobs propose changes.</p>
</div>
<div class="course-card green">
<h3>Independent gates</h3>
<p>The updater cannot alter validators or thresholds.</p>
</div>
<div class="course-card orange">
<h3>Lifecycle</h3>
<p>Canary, monitor, roll back, consolidate, expire, and prune.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Candidate area</h3>
<p>New artifacts cannot serve production traffic</p>
</div>
<div class="course-card blue">
<h3>Transfer + retention</h3>
<p>Improve held-out tasks without forgetting old ones</p>
</div>
<div class="course-card green">
<h3>Sleep learning</h3>
<p>Batch consolidation outside the online execution path</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig8-1.svg" alt="Overall loop of continual Agent evolution">

<div class="course-caption">Overall loop of continual Agent evolution</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Online self-edit vs. Governed evolution

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Online self-edit</h3><ul><li>Immediate</li><li>Noise becomes persistent</li><li>Attack can cross sessions</li></ul></div>
<div class="course-card green"><h3>Governed evolution</h3><ul><li>Immutable evidence</li><li>Offline candidate</li><li>Independent release + rollback</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The trusted root must remain outside the system it approves.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# The updater cannot be its own authority

~~~python
candidate = updater.propose(immutable_evidence)
security_gate.check(candidate)
gain = evaluator.transfer(candidate)
retention = evaluator.retention(candidate)
release.canary(candidate, gain, retention)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>8-5</span><span>2 min</span></div>
<h3>Exercise self-modification safety regressions</h3>
<p><strong>Observe:</strong> Rejected candidates, circuit breakers, regression gates, canary, and rollback</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>8-6</span><span>2 min</span></div>
<h3>Compare static, append-only, and evolving Agents</h3>
<p><strong>Observe:</strong> Learning, transfer, rule replacement, retention, and negative transfer</p>
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
$ python -m pytest chapter8/self-modifying-agent/test_evolution.py -q

$ cd chapter8/self-evolution-eval && python demo.py --profile all --output output/course-reference.json
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Appending feedback is not the same as replacing obsolete knowledge.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Updater quality and the task Agent's ability to activate an artifact are separate capabilities.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Long-term progress requires transfer, retention, safety, and maintenance metrics together.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A verifiable loop can optimize a proxy perfectly while making no progress on an ambiguous real objective.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Separate evidence, candidate, validator, and production authority—and preserve an immutable rollback path.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter8/self-modifying-agent/run_experiment_8_5.py">
<span class="course-link-title">Self-modifying Agent official runner</span>
<span class="course-link-path">chapter8/self-modifying-agent/run_experiment_8_5.py</span>
</a>
<a class="course-link" href="../chapter8/self-evolution-eval/">
<span class="course-link-title">Longitudinal evaluation tests</span>
<span class="course-link-path">chapter8/self-evolution-eval/</span>
</a>
<a class="course-link" href="../book-en/images/fig8-1.svg">
<span class="course-link-title">Overall continual-evolution loop</span>
<span class="course-link-path">book-en/images/fig8-1.svg</span>
</a>
<a class="course-link" href="../book-en/chapter8.md">
<span class="course-link-title">Chapter 8 safety boundaries</span>
<span class="course-link-path">book-en/chapter8.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which file, threshold, or permission must your updater never be allowed to modify?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Improve complete · Next · Lesson 35</div>

<div class="course-next">Carry the perceive-think-act loop into voice, screens, and physical systems under real-time constraints.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
