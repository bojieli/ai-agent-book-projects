---
theme: seriph
title: "Lesson 39 — When Should Agents Share the Same Context?"
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

# When Should Agents Share the Same Context?

<p class="course-subtitle">Shared trajectories, isolated contexts, role switching, and handoffs</p>

<div class="course-cover-meta">Lesson 39 of 42 · 17 minutes · Classification Framework; Shared vs. Non-Shared Context; Multi-Stage Role Switching</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

<div class="course-kicker">Expand · Chapter 10 · Multi-Agent Collaboration</div>

# Problems this chapter will solve

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Lesson 39</h3>
<p>When Should Agents Share the Same Context?</p>
</div>
<div class="course-card green">
<h3>Lesson 40</h3>
<p>Who Should Coordinate Independent Agents?</p>
</div>
<div class="course-card purple">
<h3>Lesson 41</h3>
<p>When Is Multi-Agent Actually Better Than One Agent?</p>
</div>
<div class="course-card blue">
<h3>Lesson 42</h3>
<p>How Do Agent Teams Fail—and What Should We Build Next?</p>
</div>
</div>

<!-- Presenter cue: Orient viewers to the chapter. Name the progression, then highlight today's first problem. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Continuity</h3>
<p>Shared history preserves details and user decisions.</p>
</div>
<div class="course-card green">
<h3>Isolation</h3>
<p>Separate contexts reduce interference and permission leakage.</p>
</div>
<div class="course-card orange">
<h3>Scale</h3>
<p>Independent contexts enable parallel work beyond one window.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Shared context</h3>
<p>New prompt/tools, same complete trajectory</p>
</div>
<div class="course-card blue">
<h3>Non-shared context</h3>
<p>Independent trajectory + explicit communication</p>
</div>
<div class="course-card green">
<h3>IPC analogy</h3>
<p>Files as shared memory; calls/messages as message passing</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig10-1.svg" alt="Shared-context and non-shared-context multi-Agent architectures">

<div class="course-caption">Shared-context and non-shared-context multi-Agent architectures</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Shared context vs. Non-shared context

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Shared context</h3><ul><li>Near-zero handoff loss</li><li>Mostly serial roles</li><li>History grows and biases</li></ul></div>
<div class="course-card green"><h3>Non-shared context</h3><ul><li>Modular and parallel</li><li>Selective disclosure</li><li>Handoff can omit evidence</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Share when loss is unacceptable; isolate when scale, focus, or security dominates.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# A role is prompt + tools + visible state

~~~python
stage = router.choose(task_state)
agent = Agent(prompt=stage.prompt, tools=stage.tools)
if stage.shared:
    agent.resume(full_trajectory)
else: agent.start(handoff_package)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>10-1</span><span>1 min</span></div>
<h3>Inspect staged prompts, tools, and fallback gates</h3>
<p><strong>Observe:</strong> Requirements, implementation, review, and revision boundaries</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>10-2</span><span>1 min</span></div>
<h3>Inspect role-specific handoff capabilities</h3>
<p><strong>Observe:</strong> Distinct prompts, tools, transfer edges, and shared session state</p>
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
$ cd chapter10/staged-system-prompt && python demo.py --list-stages

$ cd chapter10/multi-role-transfer && python demo.py --list-roles
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Changing prompt and tools can create a specialist while preserving one trajectory.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Shared context removes handoff compression but can carry framing bias across roles.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Independent Agents require an explicit data plane and control plane.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Calling predefined stages 'multi-Agent' is useful architecturally, but the execution remains a workflow with a known path.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Choose context sharing before topology: it determines information loss, isolation, parallelism, and token growth.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../book-en/images/fig10-stage-switching.svg">
<span class="course-link-title">Stage-based role switching</span>
<span class="course-link-path">book-en/images/fig10-stage-switching.svg</span>
</a>
<a class="course-link" href="../chapter10/staged-system-prompt/README.md">
<span class="course-link-title">Staged-system full demo</span>
<span class="course-link-path">chapter10/staged-system-prompt/README.md</span>
</a>
<a class="course-link" href="../chapter10/multi-role-transfer/README.md">
<span class="course-link-title">Cross-domain transfer demo</span>
<span class="course-link-path">chapter10/multi-role-transfer/README.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which detail would be too dangerous to omit from a handoff—and which detail should not cross the boundary?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 40</div>

<div class="course-next">Choose who coordinates independent Agents and how artifacts and messages move between them.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
