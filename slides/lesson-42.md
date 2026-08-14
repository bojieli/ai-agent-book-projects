---
theme: seriph
title: "Lesson 42 — How Do Agent Teams Fail—and What Should We Build Next?"
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

<div class="course-kicker">Expand · Chapter 10 · Multi-Agent Collaboration</div>

# How Do Agent Teams Fail—and What Should We Build Next?

<p class="course-subtitle">Conflicts, error cascades, Agent societies, and the course synthesis</p>

<div class="course-cover-meta">Lesson 42 of 42 · 18 minutes · Failure Modes; Agent Society; Economic Competition; Strategic Gameplay</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">How do we prevent local mistakes from becoming group failures while still allowing collective behavior to emerge?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Concurrency</h3>
<p>Shared files can lose updates or encode semantic conflicts.</p>
</div>
<div class="course-card green">
<h3>Cascades</h3>
<p>A wrong upstream claim is amplified by trusting downstream Agents.</p>
</div>
<div class="course-card orange">
<h3>Emergence</h3>
<p>Persistent Agents produce social, strategic, and economic behavior not explicitly scripted.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Optimistic locking</h3>
<p>Detect version change before committing a shared write</p>
</div>
<div class="course-card blue">
<h3>Information control</h3>
<p>A code judge reveals only what each role may know</p>
</div>
<div class="course-card green">
<h3>External reward</h3>
<p>Society outcomes are scored by the environment—not self-report</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig10-11.svg" alt="Voice Werewolf multi-Agent system">

<div class="course-caption">Voice Werewolf multi-Agent system</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Agent chat room vs. Governed society

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Agent chat room</h3><ul><li>Everyone sees everything</li><li>Loose role prompts</li><li>Claims spread unchecked</li></ul></div>
<div class="course-card green"><h3>Governed society</h3><ul><li>State authority in code</li><li>Role-scoped views</li><li>Auditable actions and rewards</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Social complexity requires stronger state and information governance.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# The judge owns truth and disclosure

~~~python
private_view = judge.view_for(player, global_state)
action = player.act(private_view)
judge.validate(action, role=player.role)
global_state = judge.apply(action)
audit.append(player.id, action, state_hash(global_state))
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>10-8 offline diagnostic</span><span>2 min</span></div>
<h3>Run a deterministic information-isolation game</h3>
<p><strong>Observe:</strong> Private role context, phase transitions, legal actions, votes, and winner gates</p>
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
$ cd chapter10/voice-werewolf && python demo.py --offline
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Coordination failures are distributed-systems failures plus probabilistic decision errors.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>A code-driven authority can preserve information asymmetry and rule integrity.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Social and economic simulations can generate new experience—but also collusion and pathology.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">An offline all-AI diagnostic does not satisfy the book's live human voice acceptance criteria.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Keep shared truth, permissions, conflict detection, and final rewards outside the Agents that compete or collaborate.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="https://github.com/joonspk-research/generative_agents">
<span class="course-link-title">Experiment 10-7: Stanford Generative Agents</span>
<span class="course-link-path">https://github.com/joonspk-research/generative_agents</span>
</a>
<a class="course-link" href="../chapter10/voice-werewolf/README.md">
<span class="course-link-title">Experiment 10-8: consent-gated voice path</span>
<span class="course-link-path">chapter10/voice-werewolf/README.md</span>
</a>
<a class="course-link" href="../book-en/images/fig10-10.svg">
<span class="course-link-title">AI Town architecture</span>
<span class="course-link-path">book-en/images/fig10-10.svg</span>
</a>
<a class="course-link" href="../book-en/chapter10.md">
<span class="course-link-title">Agent society and economy cases</span>
<span class="course-link-path">book-en/chapter10.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---

# The complete course arc

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Build · Lessons 01–21</h3>
<p>Context → memory → tools → code</p>
</div>
<div class="course-card green">
<h3>Improve · Lessons 22–34</h3>
<p>Evaluation → training → continual evolution</p>
</div>
<div class="course-card purple">
<h3>Expand · Lessons 35–42</h3>
<p>Voice → embodied action → collaboration</p>
</div>
</div>

<!-- Presenter cue: Return to the three-part arc from Lesson 1 and connect each stage to evidence viewers saw in the course. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which group-level failure cannot be prevented by improving any single Agent in isolation?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Course synthesis</div>

<div class="course-loop mt-8">
<div class="course-loop-step blue"><span>1</span><strong>Define the failure</strong></div>
<div class="course-loop-arrow">→</div>
<div class="course-loop-step green"><span>2</span><strong>Run a controlled experiment</strong></div>
<div class="course-loop-arrow">→</div>
<div class="course-loop-step purple"><span>3</span><strong>Interpret the evidence</strong></div>
<div class="course-loop-arrow">→</div>
<div class="course-loop-step orange"><span>4</span><strong>Update safely</strong></div>
</div>

<div class="course-loop-return">↺ Repeat when new evidence arrives</div>

<!-- Presenter cue: Close by tracing the evidence-driven loop from Lesson 1, then leave viewers with the repeat trigger. -->
