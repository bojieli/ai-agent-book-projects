---
theme: seriph
title: "Lesson 08 — How Can an Agent Know What It Needs to Learn?"
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

<div class="course-kicker">Build · Chapter 2 · Context Engineering</div>

# How Can an Agent Know What It Needs to Learn?

<p class="course-subtitle">Skills, progressive disclosure, and on-demand capability</p>

<div class="course-cover-meta">Lesson 08 of 42 · 18 minutes · Dynamic Prompts and Agent Skills; Skills and Tools</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">How can an Agent access hundreds of specialist procedures without carrying all of them in every prompt?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Discovery</h3>
<p>A thin index tells the Agent what knowledge exists.</p>
</div>
<div class="course-card green">
<h3>Disclosure</h3>
<p>Detailed instructions load only after a relevant trigger.</p>
</div>
<div class="course-card orange">
<h3>Execution</h3>
<p>Bundled scripts make repeated procedures deterministic.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Skill metadata</h3>
<p>Name and description stay visible</p>
</div>
<div class="course-card blue">
<h3>Skill body</h3>
<p>Workflow loads only when selected</p>
</div>
<div class="course-card green">
<h3>Resources</h3>
<p>References and scripts load only when required</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig2-11.svg" alt="Skills progressive disclosure">

<div class="course-caption">Skills progressive disclosure</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Everything preloaded vs. Progressive disclosure

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Everything preloaded</h3><ul><li>Large static prompt</li><li>High information competition</li><li>Every task pays the cost</li></ul></div>
<div class="course-card green"><h3>Progressive disclosure</h3><ul><li>Thin capability index</li><li>On-demand instructions</li><li>Task-specific context</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Skills trade metacognition risk for context efficiency.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# A Skill is a navigable package

~~~text
pptx/
├── SKILL.md          # when and how
├── reference.md      # details on demand
├── scripts/
│   └── render.py
└── templates/
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>2-6</span><span>3 min</span></div>
<h3>Generate a deck through progressive Skill loading</h3>
<p><strong>Observe:</strong> Metadata → Skill body → referenced script → verified artifact</p>
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
$ uv run python chapter2/agent-skills-ppt/demo.py --offline
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>The Agent initially sees a capability index rather than full instructions.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>File reads turn specialist knowledge into explicit trajectory events.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Scripts reduce token use and make artifact creation testable.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Progressive disclosure fails when the model does not recognize that a Skill is relevant.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Keep capability descriptions broad enough for discovery and Skill bodies narrow enough for reliable execution.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter2/agent-skills-ppt/run_official_experiment.py">
<span class="course-link-title">Official Skill runtime paths</span>
<span class="course-link-path">chapter2/agent-skills-ppt/run_official_experiment.py</span>
</a>
<a class="course-link" href="../book-en/images/fig2-12.svg">
<span class="course-link-title">Skill-enabled trajectory</span>
<span class="course-link-path">book-en/images/fig2-12.svg</span>
</a>
<a class="course-link" href="../book-en/chapter2.md">
<span class="course-link-title">Skills versus tools</span>
<span class="course-link-path">book-en/chapter2.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">How would you measure false-negative Skill discovery?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 09</div>

<div class="course-next">Long tasks need explicit state and selective forgetting, not only selective loading.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
