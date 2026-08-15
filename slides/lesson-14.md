---
theme: seriph
title: "Lesson 14 — What Makes a Tool Easy for a Model to Use?"
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

# What Makes a Tool Easy for a Model to Use?

<p class="course-subtitle">Capability boundaries, granularity, descriptions, and MCP</p>

<div class="course-cover-meta">Lesson 14 of 42 · 18 minutes · Tool Classification; Universal Principles; MCP; Perception Tools</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

<div class="course-kicker">Build · Chapter 4 · Tools</div>

# Problems this chapter will solve

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Lesson 14</h3>
<p>What Makes a Tool Easy for a Model to Use?</p>
</div>
<div class="course-card green">
<h3>Lesson 15</h3>
<p>How Do You Let an Agent Act Without Letting It Cause Damage?</p>
</div>
<div class="course-card purple">
<h3>Lesson 16</h3>
<p>When Should an Agent Ask for Help or Delegate?</p>
</div>
<div class="course-card blue">
<h3>Lesson 17</h3>
<p>How Can a Synchronous Model Live in an Asynchronous World?</p>
</div>
</div>

<!-- Presenter cue: Orient viewers to the chapter. Name the progression, then highlight today's first problem. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Granularity</h3>
<p>One broad tool or several composable operations?</p>
</div>
<div class="course-card green">
<h3>Description</h3>
<p>The model selects tools from names, schemas, and examples.</p>
</div>
<div class="course-card orange">
<h3>Fidelity</h3>
<p>Arguments must preserve the user's intended operation.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Perception</h3>
<p>Read the world without changing it</p>
</div>
<div class="course-card blue">
<h3>Execution</h3>
<p>Change state and create consequences</p>
</div>
<div class="course-card green">
<h3>Collaboration</h3>
<p>Reach another Agent or human</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig4-1.svg" alt="MCP protocol interaction sequence">

<div class="course-caption">MCP protocol interaction sequence</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Dedicated tool vs. Skill + executor

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Dedicated tool</h3><ul><li>Clear intent</li><li>Narrow schema</li><li>Many definitions at scale</li></ul></div>
<div class="course-card green"><h3>Skill + executor</h3><ul><li>General action surface</li><li>Instructions on demand</li><li>Needs stronger sandboxing</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Capability expression is a design choice.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# A schema is an Agent-facing API

~~~json
{
  "name": "weather",
  "description": "Current observed weather for one place",
  "parameters": {"city": {"type": "string"}},
  "required": ["city"]
}
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>4-1</span><span>3 min</span></div>
<h3>Discover and call perception tools</h3>
<p><strong>Observe:</strong> Tool discovery, typed arguments, truncation, and evidence returned</p>
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
$ uv run python chapter4/perception-tools/cli.py demo --offline
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Read-only tools are easier to cache, parallelize, and trust.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Descriptions should state scope, provenance, and failure behavior.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>MCP standardizes interoperability but not tool quality.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Every third-party server creates a new trust boundary for descriptions, credentials, and returned content.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Design tools for faithful action and inspectable evidence before optimizing convenience.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter4/perception-tools/">
<span class="course-link-title">MCP server implementation</span>
<span class="course-link-path">chapter4/perception-tools/</span>
</a>
<a class="course-link" href="../chapter4/DOCKER_DEPLOYMENT.md">
<span class="course-link-title">Container deployment</span>
<span class="course-link-path">chapter4/DOCKER_DEPLOYMENT.md</span>
</a>
<a class="course-link" href="../book-en/chapter4.md">
<span class="course-link-title">Tool taxonomy</span>
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

<div class="course-big course-reflection">Which parameter in your tool can silently change the meaning of the user's request?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 15</div>

<div class="course-next">Add execution power without letting a model become the security boundary.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
