---
theme: seriph
title: "Lesson 26 — Why Does Model Training Happen in Three Stages?"
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

<div class="course-kicker">Improve · Chapter 7 · Model Post-Training</div>

# Why Does Model Training Happen in Three Stages?

<p class="course-subtitle">Pre-training, SFT, RL, and the agent-environment loop</p>

<div class="course-cover-meta">Lesson 26 of 42 · 17 minutes · Pre-training, SFT, RL: A Three-Stage Panorama; Classic RL Agents; Pre-training Basics</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

<div class="course-kicker">Improve · Chapter 7 · Model Post-Training</div>

# Problems this chapter will solve

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Lesson 26</h3>
<p>Why Does Model Training Happen in Three Stages?</p>
</div>
<div class="course-card green">
<h3>Lesson 27</h3>
<p>When Should You Teach with Examples—and When with Rewards?</p>
</div>
<div class="course-card purple">
<h3>Lesson 28</h3>
<p>How Do Preferences Become a Trainable Signal?</p>
</div>
<div class="course-card blue">
<h3>Lesson 29</h3>
<p>Why Do Data and Environments Matter More Than the Algorithm?</p>
</div>
<div class="course-card green">
<h3>Lesson 30</h3>
<p>How Do You Reward a Long Agent Trajectory?</p>
</div>
<div class="course-card purple">
<h3>Lesson 31</h3>
<p>How Can a Model Learn to Use Tools with Fewer Samples?</p>
</div>
</div>

<!-- Presenter cue: Orient viewers to the chapter. Name the progression, then highlight today's first problem. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Pre-training</h3>
<p>Acquire language, priors, knowledge, and basic reasoning.</p>
</div>
<div class="course-card green">
<h3>SFT</h3>
<p>Learn the response and tool-use protocol from demonstrations.</p>
</div>
<div class="course-card orange">
<h3>RL</h3>
<p>Explore decisions and increase actions that earn reward.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Policy</h3>
<p>A probability distribution over the next action</p>
</div>
<div class="course-card blue">
<h3>Environment</h3>
<p>The world that returns a new state and reward</p>
</div>
<div class="course-card green">
<h3>Update</h3>
<p>Move probability toward behavior supported by the signal</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig7-7.svg" alt="Q-learning and LLM Agent architectures in a treasure hunt">

<div class="course-caption">Q-learning and LLM Agent architectures in a treasure hunt</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Classic RL vs. LLM Agent

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Classic RL</h3><ul><li>Small state/action space</li><li>Learns mainly from trials</li><li>Explicit value estimates</li></ul></div>
<div class="course-card green"><h3>LLM Agent</h3><ul><li>Language observations/actions</li><li>Strong pretrained priors</li><li>Reasons in context before acting</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The loop is shared; the representation and prior knowledge are radically different.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# The Q-learning update

~~~python
target = reward + gamma * max(Q[next_state])
error = target - Q[state, action]
Q[state, action] += alpha * error
state = next_state
# experience changes the next choice
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>7-1</span><span>2 min</span></div>
<h3>Watch Q-learning discover hidden game mechanics</h3>
<p><strong>Observe:</strong> Learning curve, exploration decay, and final greedy success</p>
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
$ cd chapter1/learning-from-experience && python experiment.py --mode qlearning --rl-episodes 10000 --eval-episodes 100 --seed 42
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Pre-training supplies priors that tabular RL must discover from scratch.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>SFT and pre-training both predict tokens; their data and loss masks differ.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>RL needs an environment capable of producing a meaningful signal.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">The treasure hunt clarifies the loop, but its small state space does not represent the scale of language-model training.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Before choosing a training method, name the capability, the representation it should change, and the signal available to teach it.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter1/learning-from-experience/">
<span class="course-link-title">Experiment 7-2: Q-learning vs. LLM Agent</span>
<span class="course-link-path">chapter1/learning-from-experience/</span>
</a>
<a class="course-link" href="../book-en/images/fig7-3.svg">
<span class="course-link-title">Q-learning grid world</span>
<span class="course-link-path">book-en/images/fig7-3.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig7-5.svg">
<span class="course-link-title">Classic vs. modern Agent</span>
<span class="course-link-path">book-en/images/fig7-5.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig7-6.svg">
<span class="course-link-title">Training paradigm evolution</span>
<span class="course-link-path">book-en/images/fig7-6.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which capability in your Agent comes from weights, and which is reconstructed from context every run?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 27</div>

<div class="course-next">Decide when demonstrations are enough and when exploration is worth the cost.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
