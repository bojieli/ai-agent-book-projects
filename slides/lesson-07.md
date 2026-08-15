---
theme: seriph
title: "Lesson 07 — Why Do Better Prompts Need Structure, Not More Rules?"
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

# Why Do Better Prompts Need Structure, Not More Rules?

<p class="course-subtitle">Process-oriented instructions, tool definitions, and injection boundaries</p>

<div class="course-cover-meta">Lesson 07 of 42 · 18 minutes · Prompt Engineering; Tool Definition Design; Prompt Injection</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Organization</h3>
<p>The model must retrieve the right instruction at the right step.</p>
</div>
<div class="course-card green">
<h3>Execution</h3>
<p>Rules should map to observable decisions and actions.</p>
</div>
<div class="course-card orange">
<h3>Trust</h3>
<p>Untrusted content must never inherit instruction authority.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Behavioral frame</h3>
<p>Tone and role set defaults—not guarantees</p>
</div>
<div class="course-card blue">
<h3>Process prompt</h3>
<p>Organize instructions around a task flow</p>
</div>
<div class="course-card green">
<h3>Layered defense</h3>
<p>Prompt hardening + source boundaries + tool checks</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig2-1.svg" alt="Composition of an Agent context window">

<div class="course-caption">Composition of an Agent context window</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Rule stack vs. Executable process

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Rule stack</h3><ul><li>Appended over time</li><li>Conflicting priorities</li><li>Hard to retrieve</li></ul></div>
<div class="course-card green"><h3>Executable process</h3><ul><li>Ordered stages</li><li>Explicit conditions</li><li>Observable outputs</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Prompt quality depends on information architecture.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Treat retrieved content as data

~~~python
content = web.read(url)
context.append({
  "role": "tool",
  "content": tag_untrusted(content)
})
policy.check(proposed_action)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>2-4</span><span>2 min</span></div>
<h3>Inspect prompt-ablation results</h3>
<p><strong>Observe:</strong> Effect of organization, tone, examples, and tool descriptions</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>2-5</span><span>3 min</span></div>
<h3>Compare an indirect injection with layered defense</h3>
<p><strong>Observe:</strong> Attack success with no defense versus combined defense</p>
</div>
</div>

<div class="course-caption course-caption-strong">Demo budget: 5 minutes · one contiguous terminal block</div>

<!-- Presenter cue: State the prediction before running anything. Name the observation that could disconfirm it. -->

---
class: course-terminal
---

<div class="course-kicker">Live demo</div>

# Switching to the terminal

~~~bash
$ uv run python chapter2/prompt-engineering/analyze_results.py --output prompt-summary.json

$ uv run python chapter2/prompt-injection/demo.py -n 1 -a 2 -d 1,4
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Disorganized correct rules can underperform a shorter process prompt.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Tool descriptions shape both action selection and argument quality.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Prompts reduce attacks but cannot form the final security boundary.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---

# Boundary → design rule

<div class="course-boundary">No system prompt can safely authorize irreversible actions using facts supplied only by the model.</div>

<div class="course-rule">Translate business policy into a process, then enforce critical invariants outside the model.</div>

<!-- Presenter cue: State where the evidence stops, then turn that limitation into a reusable engineering rule. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter2/prompt-engineering/">
<span class="course-link-title">Full prompt-ablation campaign</span>
<span class="course-link-path">chapter2/prompt-engineering/</span>
</a>
<a class="course-link" href="../chapter2/prompt-injection/">
<span class="course-link-title">All injection scenarios and defenses</span>
<span class="course-link-path">chapter2/prompt-injection/</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which sentence in your system prompt should instead be a tool-side invariant?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 08</div>

<div class="course-next">Keep specialist instructions out of the prompt until the task actually needs them.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
