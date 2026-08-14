---
theme: seriph
title: "Lesson 28 — How Do Preferences Become a Trainable Signal?"
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

# How Do Preferences Become a Trainable Signal?

<p class="course-subtitle">RLHF, reward models, KL constraints, PPO, GRPO, and DPO</p>

<div class="course-cover-meta">Lesson 28 of 42 · 17 minutes · RLHF: From Human Preferences to Reward Models; Comparison of RL Algorithms</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">How can human comparisons change a policy without letting optimization destroy useful behavior?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Preference data</h3>
<p>Humans compare outputs more reliably than they author perfect ones.</p>
</div>
<div class="course-card green">
<h3>Reward model</h3>
<p>Generalizes pairwise labels into a scalar training signal.</p>
</div>
<div class="course-card orange">
<h3>Reference policy</h3>
<p>KL pressure limits drift away from known behavior.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>PPO</h3>
<p>Actor + critic + clipped policy update</p>
</div>
<div class="course-card blue">
<h3>GRPO</h3>
<p>Normalize rewards within a sampled response group</p>
</div>
<div class="course-card green">
<h3>DPO</h3>
<p>Optimize chosen over rejected responses without a rollout loop</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig7-13.svg" alt="Group Relative Policy Optimization flow">

<div class="course-caption">Group Relative Policy Optimization flow</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Outcome optimization vs. Preference optimization

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Outcome optimization</h3><ul><li>Can discover new outputs</li><li>Requires rollouts</li><li>Reward hacking risk</li></ul></div>
<div class="course-card green"><h3>Preference optimization</h3><ul><li>Uses chosen/rejected pairs</li><li>Simpler pipeline</li><li>Bounded by offline data</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The algorithm changes how the signal is used—not whether the signal is valid.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# A relative advantage removes the critic

~~~python
rewards = verifier(samples)
adv = (rewards - rewards.mean()) / (rewards.std() + 1e-6)
ratio = policy.prob(samples) / old_policy.prob(samples)
loss = clipped_policy_loss(ratio, adv)
loss += beta * kl(policy, reference)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-1 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>RL evaluation check</span><span>2 min</span></div>
<h3>Run answer-extraction tests for an RL-trained reasoner</h3>
<p><strong>Observe:</strong> Whether the evaluator recognizes the trained model's answer format without inflating accuracy</p>
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
$ python -m pytest chapter7/Intuitor/tests -q
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Preference labels can train either an explicit reward model or a direct objective.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Relative rewards reduce value-model complexity but do not fix a bad verifier.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>KL is a steering constraint, not proof that useful capabilities are retained.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">Offline preference methods cannot explore behaviors absent from their comparison data.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Choose the simplest optimizer that can use your signal, then spend most of the effort validating the signal and holdout behavior.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter7/Intuitor/">
<span class="course-link-title">Intuitor training companion</span>
<span class="course-link-path">chapter7/Intuitor/</span>
</a>
<a class="course-link" href="../chapter7/verl/">
<span class="course-link-title">verl RL training framework</span>
<span class="course-link-path">chapter7/verl/</span>
</a>
<a class="course-link" href="../chapter7/tinker-cookbook/">
<span class="course-link-title">Tinker cookbook</span>
<span class="course-link-path">chapter7/tinker-cookbook/</span>
</a>
<a class="course-link" href="../book-en/images/fig7-reward-paradigms.svg">
<span class="course-link-title">Reward paradigm evolution</span>
<span class="course-link-path">book-en/images/fig7-reward-paradigms.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What shortcut could maximize your proposed reward while making the real product worse?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 29</div>

<div class="course-next">Move attention from algorithm names to the data and environment that define the signal.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
