---
theme: seriph
title: "Lesson 23 — How Do You Judge Quality Without Hiding Failure?"
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

<div class="course-kicker">Improve · Chapter 6 · Agent Evaluation</div>

# How Do You Judge Quality Without Hiding Failure?

<p class="course-subtitle">Rubrics, vetoes, LLM judges, pairwise comparison, and Elo</p>

<div class="course-cover-meta">Lesson 23 of 42 · 19 minutes · Evaluation Metrics System; LLM-as-a-Judge; Pairwise Comparison and Model Ranking</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">How can an automated judge produce a useful signal without turning one score into false certainty?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Dimensions</h3>
<p>Separate correctness, completeness, efficiency, and safety.</p>
</div>
<div class="course-card green">
<h3>Evidence</h3>
<p>Require a reason tied to the source trajectory.</p>
</div>
<div class="course-card orange">
<h3>Vetoes</h3>
<p>Block catastrophic errors that an average would conceal.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Rubric</h3>
<p>Observable levels with boundary examples</p>
</div>
<div class="course-card blue">
<h3>Calibration</h3>
<p>Agreement, position bias, and human spot checks</p>
</div>
<div class="course-card green">
<h3>Pairwise ranking</h3>
<p>Compare A/B first; reconstruct relative strength later</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig6-4.svg" alt="LLM-as-a-Judge evaluation pipeline">

<div class="course-caption">LLM-as-a-Judge evaluation pipeline</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Single score vs. Structured judgment

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Single score</h3><ul><li>Easy to chart</li><li>Failure causes disappear</li><li>Can reward fluent hallucination</li></ul></div>
<div class="course-card green"><h3>Structured judgment</h3><ul><li>Dimension scores</li><li>Cited evidence</li><li>Independent safety veto</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Aggregation should happen after diagnosis—not before it.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Keep the veto outside the average

~~~python
grades = judge.score(trajectory, rubric)
hallucinated = verifier.unsupported_claim(trajectory)
if hallucinated: return 0.0
return weighted_mean(grades)
# retain every grade and its evidence
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>6-3</span><span>2 min</span></div>
<h3>Compare memory systems with an offline scored control</h3>
<p><strong>Observe:</strong> How direct recall diverges from cross-session synthesis</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>6-6</span><span>2 min</span></div>
<h3>Recover a leaderboard from simulated pairwise votes</h3>
<p><strong>Observe:</strong> Latent ranking, uncertainty intervals, and sensitivity to comparison data</p>
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
$ cd chapter3/user-memory-evaluation && python main.py --mode compare --metric keyword-recall --category layer3

$ cd chapter6/elo-leaderboard && python cli.py pipeline --source simulate --num-battles 1000 --method bradley-terry --bootstrap 20
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>A useful Rubric turns vague quality into inspectable decisions.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>A hallucination veto prevents polished falsehoods from averaging into a pass.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Pairwise judgments are often easier than absolute scores, but their ranking is still data-dependent.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">An LLM judge shares model biases, can be position-sensitive, and must not be treated as ground truth without calibration.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Ask the judge for dimension-level evidence, calibrate it, and keep hard safety failures outside weighted averages.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter6/user-memory-system-evaluation/">
<span class="course-link-title">Experiment 6-4: end-to-end memory systems</span>
<span class="course-link-path">chapter6/user-memory-system-evaluation/</span>
</a>
<a class="course-link" href="../chapter6/tts-quality-eval/">
<span class="course-link-title">Experiment 6-5: TTS quality evaluation</span>
<span class="course-link-path">chapter6/tts-quality-eval/</span>
</a>
<a class="course-link" href="../chapter3/user-memory-evaluation/validate_rubric.py">
<span class="course-link-title">Structured Rubric implementation</span>
<span class="course-link-path">chapter3/user-memory-evaluation/validate_rubric.py</span>
</a>
<a class="course-link" href="../chapter6/elo-leaderboard/validation/">
<span class="course-link-title">Elo full-data validation</span>
<span class="course-link-path">chapter6/elo-leaderboard/validation/</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which failure in your domain deserves a veto rather than a lower average score?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 24</div>

<div class="course-next">Use evaluation to select a whole Agent system—not merely a model name.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
