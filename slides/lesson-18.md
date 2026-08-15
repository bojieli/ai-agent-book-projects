---
theme: seriph
title: "Lesson 18 — Why Is Code Generation Not Enough to Build a Coding Agent?"
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

# Why Is Code Generation Not Enough to Build a Coding Agent?

<p class="course-subtitle">Files, execution, harness recovery, and bounded verification</p>

<div class="course-cover-meta">Lesson 18 of 42 · 18 minutes · Coding as a Foundational Capability; Sessionless Design; Harness Engineering; Failure Recovery</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

<div class="course-kicker">Build · Chapter 5 · Coding Agents</div>

# Problems this chapter will solve

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Lesson 18</h3>
<p>Why Is Code Generation Not Enough to Build a Coding Agent?</p>
</div>
<div class="course-card green">
<h3>Lesson 19</h3>
<p>When Should an Agent Think in Code Instead of Words?</p>
</div>
<div class="course-card purple">
<h3>Lesson 20</h3>
<p>How Can an Agent Create Media It Can Actually Verify?</p>
</div>
<div class="course-card blue">
<h3>Lesson 21</h3>
<p>How Can Code Let an Agent Create New Capabilities?</p>
</div>
</div>

<!-- Presenter cue: Orient viewers to the chapter. Name the progression, then highlight today's first problem. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Workspace</h3>
<p>Files provide durable, inspectable state outside the context window.</p>
</div>
<div class="course-card green">
<h3>Action</h3>
<p>Search, editing, and execution tools let the Agent change that state.</p>
</div>
<div class="course-card orange">
<h3>Evidence</h3>
<p>Compilers, tests, and renderers expose mistakes independently.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Inspect</h3>
<p>Search before reading; locate the smallest relevant surface</p>
</div>
<div class="course-card blue">
<h3>Modify</h3>
<p>Apply localized, reviewable edits</p>
</div>
<div class="course-card green">
<h3>Recover</h3>
<p>Classify evidence, revise one hypothesis, and stop safely</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig5-2.svg" alt="Coding Agent workflow">

<div class="course-caption">Coding Agent workflow</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Chat code generation vs. Coding Agent

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Chat code generation</h3><ul><li>Produces a snippet</li><li>Cannot observe repository state</li><li>Leaves verification to the user</li></ul></div>
<div class="course-card green"><h3>Coding Agent</h3><ul><li>Navigates a workspace</li><li>Executes and revises</li><li>Stops with evidence</li></ul></div>
</div>

<div class="course-caption course-caption-strong">A workbench and recovery loop turn generation into engineering.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Verification drives the next action

~~~python
for attempt in range(max_attempts):
    patch = edit(inspect(task, workspace))
    evidence = verify(patch)
    if evidence.passed: return commit(patch)
    task = revise_hypothesis(evidence)
return stop_safely(evidence)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>Coding workflow</span><span>2 min</span></div>
<h3>Run a write-search-edit-verify workflow</h3>
<p><strong>Observe:</strong> A real file moves through write, search, localized edit, and independent verification</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>Harness tests</span><span>1 min</span></div>
<h3>Run editing and shell-session contracts</h3>
<p><strong>Observe:</strong> Exact-match edits, failure messages, state preservation, and safe boundaries</p>
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
$ uv run pytest -q chapter5/coding-agent/tests/test_integration.py::TestToolChaining::test_write_search_edit_workflow

$ uv run pytest -q chapter5/coding-agent/tests/test_edit_tool.py chapter5/coding-agent/tests/test_shell_session.py
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Files make Agent state durable, inspectable, and reproducible.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Tool and test failures become observations that guide the next hypothesis.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>A reliable loop distinguishes verified success, safe incompletion, and unsafe failure.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Passing available tests proves only their covered properties; the same workbench also exposes credentials and destructive commands.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Treat coding as a bounded inspect–modify–verify loop, with an evidence-driven recovery path for every failure class.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter5/coding-agent/">
<span class="course-link-title">Coding Agent implementation</span>
<span class="course-link-path">chapter5/coding-agent/</span>
</a>
<a class="course-link" href="../chapter5/coding-agent/tests/">
<span class="course-link-title">Complete Coding Agent test suite</span>
<span class="course-link-path">chapter5/coding-agent/tests/</span>
</a>
<a class="course-link" href="../book-en/images/fig5-3.svg">
<span class="course-link-title">Search-tool comparison</span>
<span class="course-link-path">book-en/images/fig5-3.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig5-4.svg">
<span class="course-link-title">File-editing comparison</span>
<span class="course-link-path">book-en/images/fig5-4.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which verifier would give your coding Agent genuinely new evidence after a wrong edit?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 19</div>

<div class="course-next">Use code to improve reasoning and enforce strict business rules.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
