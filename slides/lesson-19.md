---
theme: seriph
title: "Lesson 19 — When Should an Agent Think in Code Instead of Words?"
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

<div class="course-kicker">Build · Chapter 5 · Coding Agents</div>

# When Should an Agent Think in Code Instead of Words?

<p class="course-subtitle">Math, logic, and deterministic business constraints</p>

<div class="course-cover-meta">Lesson 19 of 42 · 19 minutes · Code as a Thinking Tool; Code as a Constraint for Business Rules</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Calculation</h3>
<p>Delegate exact arithmetic to a runtime.</p>
</div>
<div class="course-card green">
<h3>Logic</h3>
<p>Translate constraints into a solver.</p>
</div>
<div class="course-card orange">
<h3>Policy</h3>
<p>Use server-side ground truth for irreversible decisions.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Formalization</h3>
<p>Convert a verbal problem into variables and constraints</p>
</div>
<div class="course-card blue">
<h3>Execution feedback</h3>
<p>The environment returns exact results or errors</p>
</div>
<div class="course-card green">
<h3>Three-tier rule safety</h3>
<p>Prompt → checklist → server gate</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig5-10.svg" alt="Agent bootstrapping loop">

<div class="course-caption">Agent bootstrapping loop</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Language-only vs. Code-assisted

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Language-only</h3><ul><li>Flexible explanation</li><li>Probabilistic arithmetic</li><li>May invent policy facts</li></ul></div>
<div class="course-card green"><h3>Code-assisted</h3><ul><li>Exact execution</li><li>Testable constraints</li><li>Independent ground truth</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Use language to interpret and code to guarantee.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Never trust self-reported policy facts

~~~python
order = db.get(order_id)
now = server_clock.now()
eligible = policy.check(order, now)
if not eligible:
    return reject_with_reason(order)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-3 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>5-1</span><span>2 min</span></div>
<h3>Self-check code-assisted math</h3>
<p><strong>Observe:</strong> Exact sandbox execution and scoring against truth</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>5-2</span><span>2 min</span></div>
<h3>Solve logic as constraints</h3>
<p><strong>Observe:</strong> Variables, biconditional constraints, and verified solutions</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>5-3</span><span>2 min</span></div>
<h3>Run codified-rule self-tests</h3>
<p><strong>Observe:</strong> Checklist guidance versus server-side enforcement</p>
</div>
</div>

<div class="course-caption course-caption-strong">Demo budget: 6 minutes · one contiguous terminal block</div>

<!-- Presenter cue: State the prediction before running anything. Name the observation that could disconfirm it. -->

---
class: course-terminal
---

<div class="course-kicker">Live demo</div>

# Switching to the terminal

~~~bash
$ uv run python chapter5/code-for-math/demo.py --selfcheck

$ uv run python chapter5/code-for-logic/demo.py --mode solver --min-people 4

$ uv run python chapter5/small-model-codified-rules/demo.py --selftest
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Code replaces fragile mental computation with exact environmental feedback.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Constraint solvers reveal whether a verbal interpretation is internally consistent.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Critical rules must obtain facts from sources the model cannot forge.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---

# Boundary → design rule

<div class="course-boundary">Formalization can encode the wrong problem perfectly; interpretation still needs review.</div>

<div class="course-rule">Use the model to translate intent, code to enforce invariants, and tests to verify the translation.</div>

<!-- Presenter cue: State where the evidence stops, then turn that limitation into a reusable engineering rule. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter5/code-for-math/">
<span class="course-link-title">Full math comparison</span>
<span class="course-link-path">chapter5/code-for-math/</span>
</a>
<a class="course-link" href="../chapter5/code-for-logic/">
<span class="course-link-title">Full logic comparison</span>
<span class="course-link-path">chapter5/code-for-logic/</span>
</a>
<a class="course-link" href="../chapter5/small-model-codified-rules/">
<span class="course-link-title">Codified-rules campaign</span>
<span class="course-link-path">chapter5/small-model-codified-rules/</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which rule in your product is too important to exist only as natural language?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 20</div>

<div class="course-next">Generate visual artifacts by writing code, rendering pixels, and reviewing the result.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
