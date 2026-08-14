---
theme: seriph
title: "Lesson 35 — Why Does a Voice Agent Feel Slow?"
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

# Why Does a Voice Agent Feel Slow?

<p class="course-subtitle">Cascaded pipelines, latency waterfalls, streaming, and turn detection</p>

<div class="course-cover-meta">Lesson 35 of 42 · 18 minutes · Voice; Cascaded Pipeline; Full-Chain Streaming; Streaming Voice Perception</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

<div class="course-kicker">Expand · Chapter 9 · Multimodal Interaction</div>

# Problems this chapter will solve

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Lesson 35</h3>
<p>Why Does a Voice Agent Feel Slow?</p>
</div>
<div class="course-card green">
<h3>Lesson 36</h3>
<p>When Should Voice Stop Taking Turns?</p>
</div>
<div class="course-card purple">
<h3>Lesson 37</h3>
<p>How Does an Agent Act Through Pixels?</p>
</div>
<div class="course-card blue">
<h3>Lesson 38</h3>
<p>How Does an Agent Turn Plans into Physical Actions?</p>
</div>
</div>

<!-- Presenter cue: Orient viewers to the chapter. Name the progression, then highlight today's first problem. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Turn detection</h3>
<p>VAD waits for silence and can cut off a thinking pause.</p>
</div>
<div class="course-card green">
<h3>Serial work</h3>
<p>ASR, LLM, and TTS latency accumulate when stages wait.</p>
</div>
<div class="course-card orange">
<h3>Queueing</h3>
<p>High utilization amplifies latency nonlinearly.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Cascaded</h3>
<p>VAD → ASR → LLM → TTS</p>
</div>
<div class="course-card blue">
<h3>Streaming</h3>
<p>Emit partial transcripts, tokens, and audio chunks early</p>
</div>
<div class="course-card green">
<h3>Convergence</h3>
<p>Early recognition is fast but may change as context arrives</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig9-2.svg" alt="Latency waterfall for a serial voice pipeline">

<div class="course-caption">Latency waterfall for a serial voice pipeline</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Wait for completion vs. Stream the chain

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Wait for completion</h3><ul><li>Stable transcript</li><li>Simple control</li><li>Every stage adds delay</li></ul></div>
<div class="course-card green"><h3>Stream the chain</h3><ul><li>Earlier first audio</li><li>Overlapped work</li><li>Corrections and cancellation required</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Streaming changes when information becomes available—not the component boundaries.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Pipeline stages should overlap

~~~python
async for partial_text in asr.stream(audio):
    llm.update(partial_text)
async for sentence in llm.sentences():
    tts.enqueue(sentence)
if user_interrupts(): cancel_output()
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>9-1</span><span>1 min</span></div>
<h3>Preflight a cascaded voice Agent</h3>
<p><strong>Observe:</strong> VAD model, ASR/LLM/TTS provider configuration, and missing runtime prerequisites</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>9-2</span><span>2 min</span></div>
<h3>Generate controlled streaming-ASR scenarios</h3>
<p><strong>Observe:</strong> Normal speech, a 900 ms pause, and background noise under identical source content</p>
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
$ cd chapter9/live-audio/backend && npm run check

$ cd chapter9/streaming-speech && python prepare_scenarios.py audio/sentence.wav validation/course-scenarios
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>The silence threshold is both a latency control and a turn-taking assumption.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Streaming hides work behind speech but introduces unstable partial hypotheses.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Time to first useful audio matters more than full-response completion time.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A setup check or generated audio scenario verifies wiring and controls—not human conversational quality.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Instrument the latency of every boundary, then stream and overlap only where cancellation and correction are designed.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter9/phone-agent/">
<span class="course-link-title">Add-on (historical 9-2): browser WebRTC phone Agent</span>
<span class="course-link-path">chapter9/phone-agent/</span>
</a>
<a class="course-link" href="../chapter9/streaming-speech/run_official_experiment.py">
<span class="course-link-title">Streaming-speech official runner</span>
<span class="course-link-path">chapter9/streaming-speech/run_official_experiment.py</span>
</a>
<a class="course-link" href="../book-en/images/fig9-1.svg">
<span class="course-link-title">Serial voice architecture</span>
<span class="course-link-path">book-en/images/fig9-1.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig9-3.svg">
<span class="course-link-title">Queueing latency</span>
<span class="course-link-path">book-en/images/fig9-3.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which latency number would best predict whether a user interrupts or abandons your voice Agent?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 36</div>

<div class="course-next">Remove more boundaries—and decide what fast interaction should do while slow reasoning continues.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
