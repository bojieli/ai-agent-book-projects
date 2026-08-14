---
theme: seriph
title: "Lesson 22 — How Do You Test an Agent Instead of Its Final Answer?"
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

# How Do You Test an Agent Instead of Its Final Answer?

<p class="course-subtitle">Environments, state, datasets, and executable verification</p>

<div class="course-cover-meta">Lesson 22 of 42 · 18 minutes · Automated Evaluation Environment; Evaluation Task Datasets; Simulation Environments</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

<div class="course-kicker">Improve · Chapter 6 · Agent Evaluation</div>

# Problems this chapter will solve

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Lesson 22</h3>
<p>How Do You Test an Agent Instead of Its Final Answer?</p>
</div>
<div class="course-card green">
<h3>Lesson 23</h3>
<p>How Do You Judge Quality Without Hiding Failure?</p>
</div>
<div class="course-card purple">
<h3>Lesson 24</h3>
<p>Which Agent Should You Ship?</p>
</div>
<div class="course-card blue">
<h3>Lesson 25</h3>
<p>Did the Agent Improve—or Did the Numbers Move?</p>
</div>
</div>

<!-- Presenter cue: Orient viewers to the chapter. Name the progression, then highlight today's first problem. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Initial state</h3>
<p>Every run begins from the same controllable world.</p>
</div>
<div class="course-card green">
<h3>Interaction</h3>
<p>The Agent receives realistic tools, errors, and user disclosures.</p>
</div>
<div class="course-card orange">
<h3>Verification</h3>
<p>Success is read from external state—not self-reported.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Dataset</h3>
<p>Initial state + goal + boundary cases + success criteria</p>
</div>
<div class="course-card blue">
<h3>Environment</h3>
<p>State transitions, reset, tools, and termination</p>
</div>
<div class="course-card green">
<h3>Protocol</h3>
<p>Tool-only tasks or progressive user simulation</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig6-2.svg" alt="Tool-calling and human-computer interaction evaluation environments">

<div class="course-caption">Tool-calling and human-computer interaction evaluation environments</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Answer benchmark vs. Agent evaluation

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Answer benchmark</h3><ul><li>One prompt</li><li>One response</li><li>String or judge score</li></ul></div>
<div class="course-card green"><h3>Agent evaluation</h3><ul><li>Mutable state</li><li>Multi-turn trajectory</li><li>Executable outcome checks</li></ul></div>
</div>

<div class="course-caption course-caption-strong">An Agent can say the right thing while changing the world incorrectly.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Reset, act, and inspect

~~~python
state = environment.reset(case.seed)
trajectory = agent.run(case.goal, environment.tools)
outcome = environment.snapshot()
passed = verifier.check(outcome, trajectory)
store(case, trajectory, outcome, passed)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>Evaluation control</span><span>2 min</span></div>
<h3>Score a reporting Agent from external state</h3>
<p><strong>Observe:</strong> Tool-call correctness, arithmetic, evidence citations, and unsupported-claim vetoes</p>
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
$ cd chapter6/public-health-reporting-eval && python demo.py
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>A resettable environment turns a trajectory into a repeatable experiment.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Progressive disclosure tests whether an Agent knows what to ask.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Objective state checks are stronger than judging the final prose alone.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A simulator is useful only within its fidelity envelope; its omissions and biases become the Agent's test world.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Define the initial state, allowed transitions, and external success check before writing evaluation prompts.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment · 1/2

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter6/tau2-bench/">
<span class="course-link-title">Experiments 6-1 and 6-2: tau2-bench</span>
<span class="course-link-path">chapter6/tau2-bench/</span>
</a>
<a class="course-link" href="../chapter6/terminal-bench/">
<span class="course-link-title">Terminal-Bench reproduction</span>
<span class="course-link-path">chapter6/terminal-bench/</span>
</a>
<a class="course-link" href="../chapter6/SWE-bench/">
<span class="course-link-title">SWE-bench reproduction</span>
<span class="course-link-path">chapter6/SWE-bench/</span>
</a>
<a class="course-link" href="../chapter6/GAIA/">
<span class="course-link-title">GAIA reproduction</span>
<span class="course-link-path">chapter6/GAIA/</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---

# Continue the experiment · 2/2

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter6/OSWorld/">
<span class="course-link-title">OSWorld reproduction</span>
<span class="course-link-path">chapter6/OSWorld/</span>
</a>
<a class="course-link" href="../chapter6/android-world/">
<span class="course-link-title">AndroidWorld source and analysis</span>
<span class="course-link-path">chapter6/android-world/</span>
</a>
<a class="course-link" href="../chapter6/openvla-robotwin2-eval/">
<span class="course-link-title">OpenVLA + RoboTwin2 design</span>
<span class="course-link-path">chapter6/openvla-robotwin2-eval/</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which production state would reveal success even if the Agent's final message were hidden?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 23</div>

<div class="course-next">Turn observable outcomes into metrics that are consistent, diagnostic, and hard to game.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
