---
theme: seriph
title: "Lesson 36 — When Should Voice Stop Taking Turns?"
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

# When Should Voice Stop Taking Turns?

<p class="course-subtitle">Omni, full-duplex interaction, fast-slow thinking, and controllable speech</p>

<div class="course-cover-meta">Lesson 36 of 42 · 19 minutes · End-to-End Omnimodal Models; Full-Duplex Models; Thinking Architectures; Human-like Speech</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">How can an Agent listen, speak, interrupt, and think deeply without making conversation stall?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Omni</h3>
<p>Preserve prosody and emotion across one end-to-end model.</p>
</div>
<div class="course-card green">
<h3>Full duplex</h3>
<p>Choose listen/speak/stop actions many times per second.</p>
</div>
<div class="course-card orange">
<h3>Fast + slow</h3>
<p>Keep interaction alive while a strategist works in the background.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Turn-based Omni</h3>
<p>End-to-end audio but still waits for a turn boundary</p>
</div>
<div class="course-card blue">
<h3>Interactive model</h3>
<p>Concurrent input/output with barge-in and backchannels</p>
</div>
<div class="course-card green">
<h3>Latent bridge</h3>
<p>Exchange richer internal state than plain text</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig9-5.svg" alt="Fast and slow thinking architecture alternatives">

<div class="course-caption">Fast and slow thinking architecture alternatives</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Modular cascade vs. End-to-end/full duplex

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Modular cascade</h3><ul><li>Easy to debug</li><li>Providers interchangeable</li><li>Prosody lost through text</li></ul></div>
<div class="course-card green"><h3>End-to-end/full duplex</h3><ul><li>Lower boundary latency</li><li>Preserves acoustic cues</li><li>Harder to observe and control</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The newer architecture buys interaction quality with reduced modularity.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Fast interaction can delegate

~~~python
intent = realtime_model.listen(audio_frame)
if intent.needs_deep_work:
    job = strategist.start(intent.context)
realtime_model.respond(interaction_state)
if job.ready: realtime_model.integrate(job.result)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>9-3</span><span>2 min</span></div>
<h3>Test the end-to-end speech contract offline</h3>
<p><strong>Observe:</strong> Exact model contract, audio response handling, and fail-closed behavior without an endpoint</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>9-4</span><span>2 min</span></div>
<h3>Audit controllable-speech media and listening evidence</h3>
<p><strong>Observe:</strong> 24 reference profiles, routed controls, media hashes, and the distinction from human MOS</p>
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
$ python -m pytest chapter9/end-to-end-speech/test_step_audio.py chapter9/end-to-end-speech/test_none_content.py -q

$ cd chapter9/controllable-tts && python validate_artifacts.py
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Full-duplex models replace discrete turns with continuous interaction decisions.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Fast-slow separation preserves responsiveness without forcing every answer to be shallow.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Voice quality must be judged from audio—not configuration labels or text transcripts.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">End-to-end behavior is harder to attribute to ASR, reasoning, timing, or synthesis when a failure occurs.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Choose the simplest voice architecture that meets the interaction target, and preserve modality-native observability at every boundary you remove.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter9/end-to-end-speech/validation/upstream_audit.json">
<span class="course-link-title">Step-Audio R1 upstream audit</span>
<span class="course-link-path">chapter9/end-to-end-speech/validation/upstream_audit.json</span>
</a>
<a class="course-link" href="../chapter9/controllable-tts/validation/audio_quality_study.json">
<span class="course-link-title">Controllable TTS listening study</span>
<span class="course-link-path">chapter9/controllable-tts/validation/audio_quality_study.json</span>
</a>
<a class="course-link" href="../book-en/images/fig9-4.svg">
<span class="course-link-title">Omni architecture comparison</span>
<span class="course-link-path">book-en/images/fig9-4.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig9-6.svg">
<span class="course-link-title">Step-Audio dual-brain architecture</span>
<span class="course-link-path">book-en/images/fig9-6.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What should your fast interaction model be allowed to say before the slow model has verified the answer?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 37</div>

<div class="course-next">Carry perception and action into visual interfaces, where every click changes the next observation.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
