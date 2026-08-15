---
theme: seriph
title: "Lesson 15 — How Do You Let an Agent Act Without Letting It Cause Damage?"
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

<div class="course-kicker">Build · Chapter 4 · Tools</div>

# How Do You Let an Agent Act Without Letting It Cause Damage?

<p class="course-subtitle">Execution tools, independent checks, and fail-closed design</p>

<div class="course-cover-meta">Lesson 15 of 42 · 18 minutes · Execution Tools; Security; Proposer-Reviewer; Sidecar</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">Where should safety checks live when the model can write files, run code, and call external systems?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Risk classification</h3>
<p>Read, reversible write, irreversible action</p>
</div>
<div class="course-card green">
<h3>Pre-approval</h3>
<p>Review intent and parameters before execution</p>
</div>
<div class="course-card orange">
<h3>Post-validation</h3>
<p>Inspect the actual resulting state</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Fail closed</h3>
<p>Unknown or malformed operations are denied</p>
</div>
<div class="course-card blue">
<h3>Independent evidence</h3>
<p>Use data the proposer cannot forge</p>
</div>
<div class="course-card green">
<h3>Sidecar</h3>
<p>Keep enforcement outside the Agent's own mutable process</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig4-5.svg" alt="Synchronous model training versus asynchronous deployment">

<div class="course-caption">Synchronous model training versus asynchronous deployment</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Model self-report vs. Independent gate

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Model self-report</h3><ul><li>Claims an action is safe</li><li>Can hallucinate facts</li><li>Shares the same compromised context</li></ul></div>
<div class="course-card green"><h3>Independent gate</h3><ul><li>Reads server truth</li><li>Enforces deterministic invariants</li><li>Logs the decision</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The final boundary must not trust the model's own claim.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Server truth is the gatekeeper

~~~python
request = agent.propose_action()
facts = database.read_ground_truth(request.target)
policy.validate(request, facts)
result = executor.run(request)
validator.inspect(result)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>4-3A</span><span>1 min</span></div>
<h3>Run an allowed code action</h3>
<p><strong>Observe:</strong> Validation, sandbox execution, and bounded output</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>4-3B</span><span>2 min</span></div>
<h3>Inspect execution-tool safety behavior</h3>
<p><strong>Observe:</strong> Approval, rejection, syntax checks, and output handling</p>
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
$ uv run python chapter4/execution-tools/cli.py code --language python --code "print(2 ** 10)"

$ uv run python chapter4/execution-tools/cli.py demo
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Risk depends on parameters and environment, not only the tool name.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Pre-approval reduces harmful attempts; validation catches harmful results.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Long outputs need truncation plus durable storage, not silent loss.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A second model is not independent if it sees the same injected context and trusts the same unverified facts.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Guide the model with instructions, but enforce irreversible constraints with independent code and data.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter4/execution-tools/">
<span class="course-link-title">Execution-tool tests</span>
<span class="course-link-path">chapter4/execution-tools/</span>
</a>
<a class="course-link" href="../book-en/chapter4.md">
<span class="course-link-title">Sidecar design</span>
<span class="course-link-path">book-en/chapter4.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What is the trusted root in your Agent system, and can the Agent modify it?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 16</div>

<div class="course-next">Some tasks require another Agent or a human rather than another tool.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
