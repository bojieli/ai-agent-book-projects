---
theme: seriph
title: "Lesson 32 — How Do Failed Trajectories Become Learning Signals?"
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

# How Do Failed Trajectories Become Learning Signals?

<p class="course-subtitle">Outcome verification, process rules, Rubrics, and cross-trajectory experience</p>

<div class="course-cover-meta">Lesson 32 of 42 · 19 minutes · Deriving Learning Signals from Operational Trajectories; Consolidating Experience into Knowledge</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

<div class="course-kicker">Improve · Chapter 8 · Continual Evolution</div>

# Problems this chapter will solve

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Lesson 32</h3>
<p>How Do Failed Trajectories Become Learning Signals?</p>
</div>
<div class="course-card green">
<h3>Lesson 33</h3>
<p>Where Should an Agent Store What It Learns?</p>
</div>
<div class="course-card purple">
<h3>Lesson 34</h3>
<p>How Can a Self-Modifying Agent Change Without Drifting?</p>
</div>
</div>

<!-- Presenter cue: Orient viewers to the chapter. Name the progression, then highlight today's first problem. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Outcome</h3>
<p>Read what changed in the environment.</p>
</div>
<div class="course-card green">
<h3>Process</h3>
<p>Locate rule violations and ineffective decisions.</p>
</div>
<div class="course-card orange">
<h3>Meaning</h3>
<p>Use a Rubric for dimensions that code cannot settle.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Trajectory verifier</h3>
<p>Outcome checks + process rules + language Rubric</p>
</div>
<div class="course-card blue">
<h3>Contrastive evidence</h3>
<p>Compare success, partial success, and failure</p>
</div>
<div class="course-card green">
<h3>Experience document</h3>
<p>Mechanism + conditions + evidence + exceptions</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig8-2.svg" alt="Three-layer trajectory verification from outcomes to an LLM Rubric">

<div class="course-caption">Three-layer trajectory verification from outcomes to an LLM Rubric</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Save the trajectory vs. Consolidate experience

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Save the trajectory</h3><ul><li>High detail</li><li>Hard to retrieve</li><li>Incidental actions become noise</li></ul></div>
<div class="course-card green"><h3>Consolidate experience</h3><ul><li>Cross-run pattern</li><li>Explicit applicability</li><li>Evidence and counterexamples</li></ul></div>
</div>

<div class="course-caption course-caption-strong">A trajectory is evidence; it is not yet a lesson.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Diagnose before updating

~~~python
outcome = environment_verifier(trajectory)
violations = process_verifier(trajectory)
rubric = semantic_judge(trajectory, outcome)
diagnosis = triangulate(outcome, violations, rubric)
experience = consolidate(similar_diagnoses)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>8-1</span><span>2 min</span></div>
<h3>Diagnose customer-service trajectories with three evidence layers</h3>
<p><strong>Observe:</strong> False promises, privacy violations, over-refusal, and cited evidence</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>8-2</span><span>2 min</span></div>
<h3>Consolidate several trajectories into experience documents</h3>
<p><strong>Observe:</strong> Transfer gain, retrieval cost, negative transfer, and applicability conditions</p>
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
$ cd chapter8/trajectory-verifier && python demo.py

$ cd chapter8/gaia-experience && python demo_documents.py
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Environment outcomes constrain what a language judge may claim.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Failures and partial successes reveal conditions hidden by successful runs.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Cross-trajectory documents can transfer while using fewer tokens than raw history.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A pattern supported by past trajectories may become obsolete after an API, policy, or environment change.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Promote experience only with provenance, applicability conditions, counterevidence, and a revalidation trigger.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter8/trajectory-verifier/test_verifier.py">
<span class="course-link-title">Trajectory verifier tests</span>
<span class="course-link-path">chapter8/trajectory-verifier/test_verifier.py</span>
</a>
<a class="course-link" href="../chapter8/gaia-experience/">
<span class="course-link-title">Experience-document implementation</span>
<span class="course-link-path">chapter8/gaia-experience/</span>
</a>
<a class="course-link" href="../book-en/images/fig8-4.svg">
<span class="course-link-title">Knowledge-document architecture</span>
<span class="course-link-path">book-en/images/fig8-4.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which detail in a successful trajectory was causal, and how would you distinguish it from coincidence?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 33</div>

<div class="course-next">Choose the artifact that should change: knowledge, instructions, programs, or parameters.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
