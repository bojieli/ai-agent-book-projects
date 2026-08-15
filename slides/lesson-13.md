---
theme: seriph
title: "Lesson 13 — When Should the Agent Decide What to Retrieve?"
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

# When Should the Agent Decide What to Retrieve?

<p class="course-subtitle">Agentic RAG, contextual retrieval, and two-tier memory</p>

<div class="course-cover-meta">Lesson 13 of 42 · 19 minutes · Agentic RAG; Contextual Retrieval; Deep Knowledge Extraction</div>

<!-- Presenter cue: Open with the concrete problem. Add personal context in your own words; do not read the slide. -->

---

# Why this problem matters

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card blue">
<h3>Search decision</h3>
<p>The Agent decides whether retrieval is needed.</p>
</div>
<div class="course-card green">
<h3>Query reformulation</h3>
<p>New evidence changes the next search.</p>
</div>
<div class="course-card orange">
<h3>Stopping</h3>
<p>The Agent judges whether evidence is sufficient.</p>
</div>
</div>

<!-- Presenter cue: Connect each card to a product or experiment consequence. -->

---

# Three ideas to keep in view

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card purple">
<h3>Agentic RAG</h3>
<p>Retrieval becomes a tool inside ReAct</p>
</div>
<div class="course-card blue">
<h3>Contextual retrieval</h3>
<p>Restore document context before indexing each chunk</p>
</div>
<div class="course-card green">
<h3>Two-tier memory</h3>
<p>Resident overview + retrieved detail</p>
</div>
</div>

<!-- Presenter cue: Define unfamiliar terms in plain language; the audience is new to ML training and RL. -->

---

# The book's visual model

<img class="course-figure" src="/images/fig3-13.svg" alt="Agentic RAG architecture">

<div class="course-caption">Agentic RAG architecture</div>

<!-- Presenter cue: Trace the diagram in one direction and name the mechanism that matters for this lesson. -->

---

# Retrieve once vs. Agentic retrieval

<div class="grid grid-cols-2 gap-6 mt-5">
<div class="course-card orange"><h3>Retrieve once</h3><ul><li>Fixed query</li><li>Fixed top-k</li><li>One chance to find evidence</li></ul></div>
<div class="course-card green"><h3>Agentic retrieval</h3><ul><li>Iterative queries</li><li>Evidence-aware decisions</li><li>Explicit stopping</li></ul></div>
</div>

<div class="course-caption course-caption-strong">Autonomy adds flexibility and a new metacognition failure mode.</div>

<!-- Presenter cue: Explain the trade-off; avoid presenting the right column as universally superior. -->

---

# Retrieval becomes an action

~~~python
while not evidence_sufficient(context):
    query = agent.formulate_search(context)
    passages = search(query)
    context.add(passages)
return agent.answer_with_citations(context)
~~~

<!-- Presenter cue: Walk through the executable idea line by line; keep implementation details for the terminal. -->

---

# Test the claim

<div class="grid grid-cols-3 gap-4 mt-5">
<div class="course-card blue">
<div class="course-demo-head"><span>3-8</span><span>2 min</span></div>
<h3>Compare fixed and Agentic RAG offline</h3>
<p><strong>Observe:</strong> Query count, evidence coverage, answer quality, and cost</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>3-10</span><span>2 min</span></div>
<h3>Compare plain and contextual chunks</h3>
<p><strong>Observe:</strong> Failures repaired by adding document-level context</p>
</div>
<div class="course-card blue">
<div class="course-demo-head"><span>3-11</span><span>2 min</span></div>
<h3>Compare two-tier user memory</h3>
<p><strong>Observe:</strong> Resident overview plus on-demand conversation detail</p>
</div>
</div>

<div class="course-caption course-caption-strong">Demo budget: 6 minutes · one contiguous terminal block</div>

<!-- Presenter cue: State the prediction before running anything. Name the observation that could disconfirm it. -->

---
class: course-terminal
---

<div class="course-kicker">Live demo</div>

# Switching to the terminal

~~~bash
$ uv run python chapter3/agentic-rag/compare_offline.py

$ uv run python chapter3/contextual-retrieval/compare_retrieval.py --per-query

$ uv run python chapter3/contextual-retrieval-for-user-memory/contextual_compare.py
~~~

<div class="course-terminal-watch">Run the command(s), narrate decisions, and point to the observation—not just the output.</div>

<!-- Presenter cue: Switch windows now. Return to the next slide after every listed experiment is complete. -->

---

# What the evidence supports

<div class="grid grid-cols-3 gap-5 mt-6">
<div class="course-card green">
<h3>Finding 1</h3>
<p>Iterative retrieval helps when later queries depend on earlier evidence.</p>
</div>
<div class="course-card blue">
<h3>Finding 2</h3>
<p>Contextual prefixes repair semantic loss introduced by chunking.</p>
</div>
<div class="course-card purple">
<h3>Finding 3</h3>
<p>Overview and detail require different storage and access strategies.</p>
</div>
</div>

<!-- Presenter cue: Tie each finding to something viewers just observed; distinguish evidence from interpretation. -->

---

# Boundary → design rule

<div class="course-boundary">An Agent cannot retrieve what it does not realize it is missing.</div>

<div class="course-rule">Use Agentic retrieval for genuinely multi-step evidence gathering; keep simple questions on a simple path.</div>

<!-- Presenter cue: State where the evidence stops, then turn that limitation into a reusable engineering rule. -->

---

# Continue the experiment

<div class="grid grid-cols-2 gap-4 mt-6">
<a class="course-link" href="../chapter3/agentic-rag-for-user-memory/">
<span class="course-link-title">Experiment 3-9: Agentic RAG for memory</span>
<span class="course-link-path">chapter3/agentic-rag-for-user-memory/</span>
</a>
<a class="course-link" href="../chapter3/structured-knowledge-extraction/">
<span class="course-link-title">Experiment 3-12: structured knowledge extraction</span>
<span class="course-link-path">chapter3/structured-knowledge-extraction/</span>
</a>
<a class="course-link" href="../book-en/images/fig3-14.svg">
<span class="course-link-title">Contextual retrieval diagram</span>
<span class="course-link-path">book-en/images/fig3-14.svg</span>
</a>
<a class="course-link" href="../book-en/images/fig3-15.svg">
<span class="course-link-title">Knowledge extraction pipeline</span>
<span class="course-link-path">book-en/images/fig3-15.svg</span>
</a>
</div>

<!-- Presenter cue: Point viewers to the companion paths; do not walk through every extension. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Pause and apply</div>

# Your turn

<div class="course-big course-reflection">What independent signal can tell an Agent that its evidence is insufficient?</div>

<!-- Presenter cue: Invite viewers to pause the video. Offer your own answer after a short beat. -->

---
layout: center
class: text-center
---

<div class="course-kicker">Chapter 3 complete · Next · Lesson 14</div>

<div class="course-next">Turn knowledge into actions through carefully designed tools.</div>

<div class="course-next-arrow">→</div>

<!-- Presenter cue: Use this transition to make the course feel continuous rather than episodic. -->
