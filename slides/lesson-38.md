---
theme: seriph
title: "Lesson 38 — How Does an Agent Turn Plans into Physical Actions?"
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

# How Does an Agent Turn Plans into Physical Actions?

<p class="course-subtitle">Planning-control separation, VLA control, safety gates, and Sim2Real</p>

<div class="course-cover-meta">Lesson 38 of 42 · 18 minutes · Robot Manipulation; Planning and Control; VLA Control; Sim2Real Transfer</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">How can slow semantic planning drive fast physical control without losing safety?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Planning</h3>
<p>A vision-language model selects goals and interprets the scene.</p>
</div>
<div class="course-card green">
<h3>Control</h3>
<p>A fast policy turns the current observation into motor commands.</p>
</div>
<div class="course-card orange">
<h3>Safety</h3>
<p>External gates must constrain forces, motion, workspace, and authority.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Two-layer loop</h3>
<p>Slow planning chooses subgoals; fast control executes motion</p>
</div>
<div class="course-card blue">
<h3>Action chunking</h3>
<p>Predict several future controls per expensive inference</p>
</div>
<div class="course-card green">
<h3>Sim2Real</h3>
<p>Train across calibrated visual and physical variation</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig9-11.svg" alt="Vision-Language-Action model architecture">

<div class="course-caption">Vision-Language-Action model architecture</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Open-loop plan vs. Guarded feedback loop

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Open-loop plan</h3><ul><li>Commit to a long motion</li><li>Assume the world stays fixed</li><li>Detect errors late</li></ul></div>
<div class="course-card green"><h3>Guarded feedback loop</h3><ul><li>Short action horizon</li><li>Re-observe continuously</li><li>Interrupt on state change</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Physical autonomy depends on feedback frequency and authority boundaries.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Slow plan, fast guarded control

~~~python
subgoal = planner.choose(observation, task)
chunk = controller.predict(observation, subgoal)
for action in safety_filter(chunk):
    robot.execute(action)
    observation = robot.observe()
    if world_changed(observation): break
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>9-9 dry configuration</span><span>1 min</span></div>
<h3>Inspect a fail-closed robot navigation contract</h3>
<p><strong>Observe:</strong> Exact model ID, task, camera, three motion tools, decision frequency, and no actuation</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>Robot safety gates</span><span>2 min</span></div>
<h3>Run evidence-validator regressions for physical experiments</h3>
<p><strong>Observe:</strong> Why dry runs, mock artifacts, and unverified motion cannot satisfy completion</p>
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
$ python chapter9/gemini-xlerobot-navigation/navigation.py

$ python chapter9/xlerobot-teleoperation/test_validator.py && python chapter9/gemini-xlerobot-navigation/test_validator.py && python chapter9/rgb-sim2real-grasping/test_validator.py
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Planning and control operate at different semantic and temporal scales.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Action chunks reduce inference pressure but delay response to unexpected change.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Physical completion requires calibrated hardware, authorization, measurements, and direct artifacts.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A source audit, preflight, validator test, or dry configuration demonstrates architecture and blockers—not a successful robot run.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Keep physical actions behind external safety gates, short feedback horizons, and measurements the model cannot fabricate.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter9/xlerobot-teleoperation/">
<span class="course-link-title">Experiment 9-7: XLeRobot teleoperation</span>
<span class="course-link-path">chapter9/xlerobot-teleoperation/</span>
</a>
<a class="course-link" href="../chapter9/gemini-xlerobot-navigation/">
<span class="course-link-title">Experiment 9-9: robot navigation</span>
<span class="course-link-path">chapter9/gemini-xlerobot-navigation/</span>
</a>
<a class="course-link" href="../chapter9/rgb-sim2real-grasping/">
<span class="course-link-title">Experiment 9-11: RGB Sim2Real grasping</span>
<span class="course-link-path">chapter9/rgb-sim2real-grasping/</span>
</a>
<a class="course-link" href="../book-en/images/fig9-13.svg">
<span class="course-link-title">Sim2Real pipeline</span>
<span class="course-link-path">book-en/images/fig9-13.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">How quickly must a physical controller reconsider an action when the world changes unexpectedly?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Chapter 9 complete · Next · Lesson 39</div>

<div class="course-next">Scale from one Agent loop to several loops that exchange context, artifacts, and control.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
