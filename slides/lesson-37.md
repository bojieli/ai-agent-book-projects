---
theme: seriph
title: "Lesson 37 — How Does an Agent Act Through Pixels?"
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

<div class="course-kicker">Expand · Chapter 9 · Multimodal Interaction</div>

# How Does an Agent Act Through Pixels?

<p class="course-subtitle">GUI action spaces, visual grounding, and bounded interaction</p>

<div class="course-cover-meta">Lesson 37 of 42 · 18 minutes · Computer Use; Action Space Design; Visual Grounding; Real-Time Performance</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">How does an Agent turn a screenshot and a goal into the right interface action?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Observation</h3>
<p>A screenshot is a partial, time-sensitive view of application state.</p>
</div>
<div class="course-card green">
<h3>Grounding</h3>
<p>The Agent must map language to an element ID or coordinate.</p>
</div>
<div class="course-card orange">
<h3>Interaction</h3>
<p>Every click or keystroke changes the next observation.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Structured tree</h3>
<p>Use DOM or accessibility elements when they are reliable</p>
</div>
<div class="course-card blue">
<h3>Visual grounding</h3>
<p>Locate targets directly in pixels when structure is absent</p>
</div>
<div class="course-card green">
<h3>Bounded loop</h3>
<p>Observe → one guarded action → observe again</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig9-9.svg" alt="Visual grounding with annotated interface elements">

<div class="course-caption">Visual grounding with annotated interface elements</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Structured grounding vs. Visual grounding

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Structured grounding</h3><ul><li>DOM/accessibility IDs</li><li>Closed-set selection</li><li>Fails on custom drawing</li></ul></div>
<div class="course-card green"><h3>Visual grounding</h3><ul><li>Works from pixels</li><li>General interface coverage</li><li>Coordinate and scale errors</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Production systems need both paths, coordinate transforms, and a confidence-aware fallback.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Every action creates a new observation

~~~python
while budget.remaining:
    screenshot, tree = browser.observe()
    target = agent.ground(task, screenshot, tree)
    action = agent.choose_action(target)
    receipt = browser.execute(guard(action))
    if verifier.done(receipt): break
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>9-6 preflight</span><span>2 min</span></div>
<h3>Run offline Computer Use contract checks</h3>
<p><strong>Observe:</strong> Endpoint identity, screenshot retention, manifest integrity, and redaction boundaries</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>9-6 retained status</span><span>1 min</span></div>
<h3>Inspect the retained open-model acceptance pointer</h3>
<p><strong>Observe:</strong> Experiment arm, model scope, status, and the hashes required to trace the full run</p>
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
$ python -m pytest chapter9/computer-use-open-model/tests -q

$ python -m json.tool chapter9/computer-use-open-model/validation/latest.json
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>A Computer Use result is a trajectory of state changes—not a final textual answer.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Structured elements improve precision, while pixel grounding expands interface coverage.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Scaling, coordinate transforms, stale screenshots, and hidden state create distinct failure modes.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Offline contract tests and an acceptance pointer do not reproduce the retained browser trajectory or complete the separate Anthropic-native arm.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Execute one bounded GUI action at a time, re-observe after every state change, and retain screenshots plus external outcome evidence.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter9/claude-quickstarts/computer-use-demo/">
<span class="course-link-title">Experiment 9-5: Claude Computer Use</span>
<span class="course-link-path">chapter9/claude-quickstarts/computer-use-demo/</span>
</a>
<a class="course-link" href="../chapter9/computer-use-open-model/">
<span class="course-link-title">Experiment 9-6: open-model Computer Use</span>
<span class="course-link-path">chapter9/computer-use-open-model/</span>
</a>
<a class="course-link" href="../book-en/images/fig9-7.svg">
<span class="course-link-title">Screenshot-action loop</span>
<span class="course-link-path">book-en/images/fig9-7.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig9-10.svg">
<span class="course-link-title">Coordinate scaling</span>
<span class="course-link-path">book-en/images/fig9-10.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which state change would prove that your GUI action succeeded, even if the Agent claims it did?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 38</div>

<div class="course-next">Cross from visual interfaces into physical control, where latency and mistakes have mechanical consequences.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
