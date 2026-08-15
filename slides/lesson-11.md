---
theme: seriph
title: "Lesson 11 — Why Does Semantic Search Miss Exact Answers?"
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

# Why Does Semantic Search Miss Exact Answers?

<p class="course-subtitle">Chunking, dense retrieval, sparse retrieval, and evaluation</p>

<div class="course-cover-meta">Lesson 11 of 42 · 19 minutes · RAG Basics; Document Chunking; Dense Embeddings; Sparse Embeddings</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---
layout: center
class: text-center
---

<div class="course-kicker">The central question</div>

<div class="course-big">Why can a vector search understand a topic yet miss the exact identifier the user needs?</div>

<!-- Presenter cue: Let the question sit for a moment, then state the failure mode the lesson will explain. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Chunking</h3>
<p>Defines the atomic units that can be found.</p>
</div>
<div class="course-card green">
<h3>Dense retrieval</h3>
<p>Matches meaning and paraphrase.</p>
</div>
<div class="course-card orange">
<h3>Sparse retrieval</h3>
<p>Matches exact words, numbers, and identifiers.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Recall@k</h3>
<p>Did the relevant item enter the candidate set?</p>
</div>
<div class="course-card blue">
<h3>ANN index</h3>
<p>Trade exact search for speed and memory</p>
</div>
<div class="course-card green">
<h3>BM25</h3>
<p>Weight exact terms with saturation and length normalization</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig3-8.svg" alt="BM25 scoring mechanism for exact lexical retrieval">

<div class="course-caption">BM25 scoring mechanism for exact lexical retrieval</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Dense vs. Sparse

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Dense</h3><ul><li>Semantic similarity</li><li>Handles paraphrases</li><li>May miss rare identifiers</li></ul></div>
<div class="course-card green"><h3>Sparse</h3><ul><li>Exact lexical match</li><li>Transparent term scores</li><li>Misses synonyms</li></ul></div>
</div>

<div class="course-caption course-caption-strong">The failure modes are complementary.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Measure retrieval before generation

~~~python
candidates = index.search(query, k=10)
recall = any(doc.id in relevant_ids for doc in candidates)
for rank, doc in enumerate(candidates, 1):
    print(rank, doc.score, doc.id)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-2 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>3-4</span><span>2 min</span></div>
<h3>Compare ANN index behavior</h3>
<p><strong>Observe:</strong> Latency, recall, memory, and incremental-update trade-offs</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>3-5</span><span>2 min</span></div>
<h3>Explain one BM25 score</h3>
<p><strong>Observe:</strong> Per-term TF, IDF, saturation, and length effects</p>
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
$ uv run python chapter3/dense-embedding/cli.py --compare-ann -k 10

$ uv run python chapter3/sparse-embedding/cli.py -q "model distillation" --explain
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>A retrieval failure can begin at chunk boundaries rather than the model.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>ANN algorithms differ in update behavior as well as speed.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Exact and semantic search solve different parts of the problem.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---
layout: center
---

<div class="course-kicker course-kicker-red">Where the claim stops</div>

# Boundary condition

<div class="course-boundary">A higher retrieval score does not prove that the retrieved passage answers the question.</div>

<!-- Presenter cue: Say explicitly what this experiment does not establish. -->

---
layout: center
---

<div class="course-kicker">Engineering takeaway</div>

# Design rule

<div class="course-rule">Evaluate the candidate set independently before asking whether generation is good.</div>

<!-- Presenter cue: Present this as a reusable decision rule, then give one counterexample or trade-off. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../book-en/images/fig3-7.svg">
<span class="course-link-title">HNSW structure</span>
<span class="course-link-path">book-en/images/fig3-7.svg</span>
</a>
<a class="course-link" href="../chapter3/sparse-embedding/">
<span class="course-link-title">BM25 implementation</span>
<span class="course-link-path">chapter3/sparse-embedding/</span>
</a>
<a class="course-link" href="../chapter3/dense-embedding/">
<span class="course-link-title">Dense model comparison</span>
<span class="course-link-path">chapter3/dense-embedding/</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">Which queries in your domain are dominated by identifiers rather than semantics?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Next · Lesson 12</div>

<div class="course-next">Fuse complementary retrievers, then organize knowledge beyond flat chunks.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
