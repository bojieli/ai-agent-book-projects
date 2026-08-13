---
theme: seriph
title: "Lesson 06 — Why Can One Timestamp Make an Agent Slow?"
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

# Why Can One Timestamp Make an Agent Slow?

<p class="course-subtitle">Chat templates, attention, KV Cache, and stable prefixes</p>

<div class="course-cover-meta">Lesson 06 of 42 · 19 minutes · KV Cache-Friendly Context Design; Chat Template; Prompt Cache</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">Why can a harmless dynamic line near the top of the prompt invalidate most cached computation?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Token stream</h3>
<p>Message objects become one ordered sequence.</p>
</div>
<div class="course-card green">
<h3>Prefix reuse</h3>
<p>Matching early tokens reuse previous attention work.</p>
</div>
<div class="course-card orange">
<h3>Architecture</h3>
<p>Dynamic content placement becomes a systems decision.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>KV Cache</h3>
<p>Reuses keys and values within inference</p>
</div>
<div class="course-card blue">
<h3>Prompt Cache</h3>
<p>Reuses a stable prefix across API requests</p>
</div>
<div class="course-card green">
<h3>Stable prefix</h3>
<p>Instructions and tools that do not change turn to turn</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig2-10.svg" alt="KV Cache prefix reuse">

<div class="course-caption">KV Cache prefix reuse</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Cache-friendly vs. Cache-breaking

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Cache-friendly</h3><ul><li>Stable system prompt</li><li>Stable tool order</li><li>Dynamic state appended late</li></ul></div>
<div class="course-card green"><h3>Cache-breaking</h3><ul><li>Timestamp near the front</li><li>Randomized tool order</li><li>Reformatted history</li></ul></div>
</div>

<div class="course-caption course-caption-strong">One early mismatch invalidates everything that follows.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Move changing state after the stable prefix

~~~python
static = [system_prompt, stable_tool_schemas]
trajectory = load_messages(session_id)
status = make_dynamic_status(now, progress)
messages = static + trajectory + [status]
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>2-3</span><span>2 min</span></div>
<h3>Compare context-management cache reports</h3>
<p><strong>Observe:</strong> Prefix hits, recomputation, repeated work, and estimated cost</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>2-2</span><span>2 min</span></div>
<h3>Generate a small attention view</h3>
<p><strong>Observe:</strong> A token's weighted access to earlier tokens</p>
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
$ uv run python chapter2/kv-cache/main.py --report

$ uv run python chapter2/attention_visualization/attention_cli.py --prompt "Explain attention in one sentence." --output attention.png
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>The API's message abstraction hides an ordered token prefix.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Cache efficiency depends on exact prefix stability.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Correct context management can improve quality and latency together.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Cache-friendly does not mean never editing context; it means making edits deliberate and localized.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Place stable, frequently reused information first and dynamic information as late as its semantics allow.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../book-en/images/fig2-7.png">
<span class="course-link-title">Attention heatmap</span>
<span class="course-link-path">book-en/images/fig2-7.png</span>
</a>
<a class="course-link" href="../book-en/images/fig2-8.svg">
<span class="course-link-title">Chat-template token structure</span>
<span class="course-link-path">book-en/images/fig2-8.svg</span>
</a>
<a class="course-link" href="../book-en/chapter2.md">
<span class="course-link-title">Editable and composable notes</span>
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

<div class="course-big course-reflection">Which dynamic values in your system prompt silently destroy prefix reuse?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 07</div>

<div class="course-next">Even a perfectly cached prompt can fail if its instructions are poorly organized.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
