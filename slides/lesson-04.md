---
theme: seriph
title: "Lesson 04 — Why Doesn't a Stronger Model Make a Reliable Agent?"
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

<div class="course-kicker">Build · Chapter 1 · Agent Fundamentals</div>

# Why Doesn't a Stronger Model Make a Reliable Agent?

<p class="course-subtitle">Harness engineering, orchestration, and guardrails</p>

<div class="course-cover-meta">Lesson 04 of 42 · 17 minutes · Harness Engineering; Model Choice; Orchestration Patterns; Guardrails and Safety</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">If models keep improving, why does the software around them keep getting more important?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Constrain</h3>
<p>Permissions, budgets, and valid action boundaries</p>
</div>
<div class="course-card green">
<h3>Verify</h3>
<p>Independent evidence that work is actually complete</p>
</div>
<div class="course-card orange">
<h3>Recover</h3>
<p>Retries, fallbacks, checkpoints, and termination paths</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Context engineering</h3>
<p>Control what the model can see.</p>
</div>
<div class="course-card blue">
<h3>Loop engineering</h3>
<p>Control when the system continues or stops.</p>
</div>
<div class="course-card green">
<h3>Harness engineering</h3>
<p>Control the complete runtime around the model.</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig1-5.svg" alt="The execution loop of an autonomous Agent">

<div class="course-caption">The execution loop of an autonomous Agent</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Workflow vs. Autonomous Agent

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Workflow</h3><ul><li>Known stages</li><li>Predictable control flow</li><li>Easy to inspect</li></ul></div>
<div class="course-card green"><h3>Autonomous Agent</h3><ul><li>Open-ended plan</li><li>Adaptive tool use</li><li>Needs stronger verification</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Use the least autonomous pattern that can solve the task.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Verification must observe the world

~~~python
proposal = agent.execute(task)
evidence = environment.inspect(proposal)
if not verifier.accepts(evidence):
    agent.revise(evidence)
guardrails.check_before_commit()
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>1-3</span><span>2 min</span></div>
<h3>Inspect a search-and-code execution plan</h3>
<p><strong>Observe:</strong> Which work belongs to search, code, validation, and stopping logic</p>
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
$ uv run python chapter1/search-codegen/main.py --backend openai --dry-run --request "Compare ASEAN capitals"
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Most production code handles boundaries and failures rather than the happy path.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Independent observations add information that self-reflection cannot.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Model selection should follow an evaluation, not a reputation.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A Harness can patch unstable behavior, but it cannot make an unverifiable goal objectively verifiable.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Prompts first, workflows second, autonomous Agents only where adaptation creates real value.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../book-en/images/fig1-wf-routing.svg">
<span class="course-link-title">Workflow patterns</span>
<span class="course-link-path">book-en/images/fig1-wf-routing.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig1-wf-evaluator.svg">
<span class="course-link-title">Evaluator-optimizer workflow</span>
<span class="course-link-path">book-en/images/fig1-wf-evaluator.svg</span>
</a>
<a class="course-link" href="../book-en/images/n8n-workflow.png">
<span class="course-link-title">n8n workflow example</span>
<span class="course-link-path">book-en/images/n8n-workflow.png</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which failure in your Agent should be prevented, detected, recovered, or escalated?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Chapter 1 complete · Next · Lesson 05</div>

<div class="course-next">Move inside the context window and inspect what the API actually sends.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
