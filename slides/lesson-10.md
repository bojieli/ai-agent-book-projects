---
theme: seriph
title: "Lesson 10 — What Should an Agent Remember About a User?"
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

<div class="course-kicker">Build · Chapter 3 · Memory and Knowledge</div>

# What Should an Agent Remember About a User?

<p class="course-subtitle">Memory levels, representations, evaluation, and privacy</p>

<div class="course-cover-meta">Lesson 10 of 42 · 19 minutes · User Memory System; Three-Level Framework; Four Storage Formats; Privacy</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

<div class="course-kicker">Build · Chapter 3 · Memory and Knowledge</div>

# Problems this chapter will solve

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Lesson 10</h3>
<p>What Should an Agent Remember About a User?</p>
</div>
<div class="course-card green">
<h3>Lesson 11</h3>
<p>Why Does Semantic Search Miss Exact Answers?</p>
</div>
<div class="course-card purple">
<h3>Lesson 12</h3>
<p>Why Is One Retrieval Index Never Enough?</p>
</div>
<div class="course-card blue">
<h3>Lesson 13</h3>
<p>When Should the Agent Decide What to Retrieve?</p>
</div>
</div>

<!-- Presenter cue: Orient viewers to the chapter. Name the progression, then highlight today's first problem. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Recall</h3>
<p>Recover an explicit fact from a previous session.</p>
</div>
<div class="course-card green">
<h3>Cross-session reasoning</h3>
<p>Combine evidence from several interactions.</p>
</div>
<div class="course-card orange">
<h3>Proactive service</h3>
<p>Notice a relevant need before the user repeats it.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Simple Notes</h3>
<p>Atomic facts with little context</p>
</div>
<div class="course-card blue">
<h3>JSON Cards</h3>
<p>Structured facts with evidence and scope</p>
</div>
<div class="course-card green">
<h3>Advanced Cards</h3>
<p>Conflicts, confidence, time, and applicability</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig3-2.svg" alt="Four strategies for representing user memory">

<div class="course-caption">Four strategies for representing user memory</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Store everything vs. Managed memory

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Store everything</h3><ul><li>High noise</li><li>Privacy exposure</li><li>Contradictory details</li></ul></div>
<div class="course-card green"><h3>Managed memory</h3><ul><li>Evidence-backed entries</li><li>Conflict resolution</li><li>Retention and sanitization</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Memory is a governed knowledge system, not a transcript archive.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# A memory needs provenance

~~~json
{
  "fact": "Prefers aisle seats",
  "scope": "long-haul flights",
  "evidence": ["session-18:turn-9"],
  "confidence": 0.82,
  "updated_at": "2026-08-03"
}
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>3-1/3-2</span><span>3 min</span></div>
<h3>Compare user-memory representations</h3>
<p><strong>Observe:</strong> What is extracted, how context is preserved, and how conflicts appear</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>3-3</span><span>2 min</span></div>
<h3>Sanitize a memory-bearing log</h3>
<p><strong>Observe:</strong> Secrets removed while diagnostic structure remains</p>
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
$ uv run python chapter3/user-memory/main.py --mode demo --memory-mode advanced_json_cards

$ uv run python chapter3/log-sanitization/main.py --demo
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Memory quality must be evaluated at several capability levels.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Structured representations retain scope and provenance better than flat notes.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Privacy controls belong in the ingestion path, before persistence.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---

# Boundary → design rule

<div class="course-boundary">A detailed schema improves precision but increases extraction cost and schema-maintenance burden.</div>

<div class="course-rule">Store the minimum durable claim together with evidence, scope, confidence, and time.</div>

<!-- Presenter cue: State where the evidence stops, then turn that limitation into a reusable engineering rule. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter3/user-memory-evaluation/">
<span class="course-link-title">Memory evaluation suite</span>
<span class="course-link-path">chapter3/user-memory-evaluation/</span>
</a>
<a class="course-link" href="../chapter3/mem0/">
<span class="course-link-title">Mem0 comparison</span>
<span class="course-link-path">chapter3/mem0/</span>
</a>
<a class="course-link" href="../chapter3/memobase/">
<span class="course-link-title">Memobase comparison</span>
<span class="course-link-path">chapter3/memobase/</span>
</a>
<a class="course-link" href="../book-en/images/fig3-4.svg">
<span class="course-link-title">Multi-type memory architecture</span>
<span class="course-link-path">book-en/images/fig3-4.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">How should a memory system respond when a newer statement contradicts an older one?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 11</div>

<div class="course-next">Retrieve external knowledge when exact words and semantic similarity disagree.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
