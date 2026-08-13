---
theme: seriph
title: "Lesson 20 — How Can an Agent Create Media It Can Actually Verify?"
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

# How Can an Agent Create Media It Can Actually Verify?

<p class="course-subtitle">Slidev, rendering, multimodal review, and video editing</p>

<div class="course-cover-meta">Lesson 20 of 42 · 18 minutes · Code-Driven Multimedia Generation; Proposer-Reviewer; Video Editing</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Proposer</h3>
<p>Plans content and writes artifact code.</p>
</div>
<div class="course-card green">
<h3>Renderer</h3>
<p>Converts code into the pixels users will see.</p>
</div>
<div class="course-card orange">
<h3>Reviewer</h3>
<p>Receives new visual evidence and returns structured fixes.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Artifact loop</h3>
<p>Source → render → inspect → revise</p>
</div>
<div class="course-card blue">
<h3>Context separation</h3>
<p>Proposer keeps text; Reviewer sees current pixels</p>
</div>
<div class="course-card green">
<h3>Explicit stop</h3>
<p>Quality gate or maximum iterations</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig5-5.svg" alt="Proposer-Reviewer loop for presentation generation">

<div class="course-caption">Proposer-Reviewer loop for presentation generation</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Self-review source vs. Rendered review

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Self-review source</h3><ul><li>Sees intended layout</li><li>Cannot observe overflow</li><li>Repeats assumptions</li></ul></div>
<div class="course-card green"><h3>Rendered review</h3><ul><li>Sees actual pixels</li><li>Detects crowding and clipping</li><li>Returns page-specific evidence</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The verifier is valuable because it receives new information.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Render before judging

~~~python
source = proposer.create_slidev(content)
images = renderer.export_png(source)
issues = vision_reviewer.inspect(images)
while issues.blocking:
    source = proposer.revise(source, issues)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>5-4</span><span>3 min</span></div>
<h3>Run the offline Slidev review loop</h3>
<p><strong>Observe:</strong> Crowded draft, rendered evidence, structured feedback, revised deck</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>5-6</span><span>2 min</span></div>
<h3>Smoke-test code-driven video editing</h3>
<p><strong>Observe:</strong> Generated editing script, executable path, and keyframe validation</p>
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
$ uv run python chapter5/paper-to-ppt/demo.py --dry-run

$ uv run python chapter5/video-edit/demo.py --smoke
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Source correctness and visual correctness are different properties.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Separating generation and visual review controls multimodal context growth.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Coarse-to-fine visual sampling reduces the cost of locating video events.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---

# Boundary → design rule

<div class="course-boundary">A visual reviewer can catch layout defects but may still miss factual or pedagogical errors.</div>

<div class="course-rule">Verify generated media in the modality consumed by the user.</div>

<!-- Presenter cue: State where the evidence stops, then turn that limitation into a reusable engineering rule. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter5/paper-to-video/">
<span class="course-link-title">Experiment 5-5: narrated video pipeline</span>
<span class="course-link-path">chapter5/paper-to-video/</span>
</a>
<a class="course-link" href="../chapter5/paper-to-ppt/validation/">
<span class="course-link-title">Presentation rendering artifacts</span>
<span class="course-link-path">chapter5/paper-to-ppt/validation/</span>
</a>
<a class="course-link" href="../chapter5/paper-to-video/validation/">
<span class="course-link-title">Paper-to-video evidence</span>
<span class="course-link-path">chapter5/paper-to-video/validation/</span>
</a>
<a class="course-link" href="../book-en/images/fig5-6.svg">
<span class="course-link-title">Video pipeline diagram</span>
<span class="course-link-path">book-en/images/fig5-6.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What new evidence becomes available only after your artifact is rendered or executed?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 21</div>

<div class="course-next">Use generated code to connect systems, create interfaces, and bootstrap new Agents.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
