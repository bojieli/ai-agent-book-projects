---
theme: seriph
title: "Lesson 12 — Why Is One Retrieval Index Never Enough?"
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

<div class="course-kicker">Build · Chapter 3 · Memory and Knowledge</div>

# Why Is One Retrieval Index Never Enough?

<p class="course-subtitle">Hybrid search, reranking, multimodality, and structured knowledge</p>

<div class="course-cover-meta">Lesson 12 of 42 · 18 minutes · Hybrid Retrieval; Multimodal Extraction; Structured Indexing; Filesystem Paradigm</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Candidate fusion</h3>
<p>Merge dense and sparse result sets.</p>
</div>
<div class="course-card green">
<h3>Reranking</h3>
<p>Use a stronger model only on a small candidate pool.</p>
</div>
<div class="course-card orange">
<h3>Knowledge shape</h3>
<p>Trees, graphs, files, images, and tables preserve different structure.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Hybrid retrieval</h3>
<p>Broad recall from multiple retrievers</p>
</div>
<div class="course-card blue">
<h3>Neural reranker</h3>
<p>More precise ordering at higher per-item cost</p>
</div>
<div class="course-card green">
<h3>Structured index</h3>
<p>Represent hierarchy or relationships explicitly</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig3-9.svg" alt="Hybrid retrieval and reranking pipeline">

<div class="course-caption">Hybrid retrieval and reranking pipeline</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Flat chunks vs. Structured knowledge

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Flat chunks</h3><ul><li>Simple ingestion</li><li>Local passage questions</li><li>Weak global structure</li></ul></div>
<div class="course-card green"><h3>Structured knowledge</h3><ul><li>Hierarchies and graphs</li><li>Multi-hop questions</li><li>More governance cost</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Choose an index for the questions—not for fashion.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Fuse ranks before reranking

~~~python
dense = dense_index.search(query, k=20)
sparse = bm25.search(query, k=20)
pool = reciprocal_rank_fusion(dense, sparse)
answer_context = reranker.top(query, pool, k=5)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>3-6</span><span>3 min</span></div>
<h3>Expose every retrieval stage</h3>
<p><strong>Observe:</strong> Dense candidates, sparse candidates, fusion, reranking, and final rank</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>3-8</span><span>2 min</span></div>
<h3>Compare RAPTOR and GraphRAG</h3>
<p><strong>Observe:</strong> Questions favored by hierarchical summaries versus relationship graphs</p>
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
$ uv run python chapter3/retrieval-pipeline/evaluate.py --query "XR-7003"

$ uv run python chapter3/structured-index/main.py demo
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Hybrid retrieval improves recall because its component failures differ.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Reranking spends expensive reasoning on a small, diverse pool.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Structured indexes help only when queries need their encoded structure.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---

# Boundary → design rule

<div class="course-boundary">More stages increase latency, operational cost, and the number of components that can drift.</div>

<div class="course-rule">Add a retrieval stage only when an evaluation identifies the failure it corrects.</div>

<!-- Presenter cue: State where the evidence stops, then turn that limitation into a reusable engineering rule. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter4/multimodal-agent/">
<span class="course-link-title">Experiment 4-2: multimodal strategies</span>
<span class="course-link-path">chapter4/multimodal-agent/</span>
</a>
<a class="course-link" href="../book-en/images/fig3-10.svg">
<span class="course-link-title">RAPTOR tree</span>
<span class="course-link-path">book-en/images/fig3-10.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig3-11.svg">
<span class="course-link-title">GraphRAG graph</span>
<span class="course-link-path">book-en/images/fig3-11.svg</span>
</a>
<a class="course-link" href="../book-en/chapter3.md">
<span class="course-link-title">Knowledge-base governance</span>
<span class="course-link-path">book-en/chapter3.md</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which query type would reveal that your flat index has lost document structure?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 13</div>

<div class="course-next">Let the Agent decide whether another retrieval step is necessary.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
