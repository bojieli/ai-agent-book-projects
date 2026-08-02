# Book-driven self-evolution task

You are Hermes working on your own source repository. Read the English edition
of *AI Agents in Depth* at `/home/ubuntu/ai-agent-book/book-en/` before deciding
what to change. Inspect all ten chapter files, using targeted searches and
section-by-section reads so that conclusions are grounded in the actual text,
not the task summary below.

One reader reported four possible gaps in Hermes:

1. product-level ablation infrastructure for measuring whether major Harness
   features really help;
2. the model-visible Agent Status Bar described in Chapter 2 (not merely a
   human-facing terminal status bar);
3. a forgetting/consolidation mechanism for persistent memory (not merely
   bounded writes or Skill archival);
4. a general proposer-reviewer loop with independent, execution-grounded
   verification for generated artifacts.

Audit each claim against the current code and its design intent. Do not assume
the proposed mechanism is compatible with Hermes. For each claim, classify it
as already present, partly present, absent, or intentionally incompatible, and
cite both book sections and exact Hermes paths.

Then improve Hermes where the evidence supports a change. Prefer the smallest
cohesive implementation that demonstrates the book's mechanism through real
behavior. Preserve prompt-cache stability, message-role alternation, safety,
and the narrow core tool surface. Add behavior-contract tests. Run the relevant
tests and record their exact results. Do not weaken existing tests, validators,
approval gates, or safety thresholds.

Create `BOOK_SELF_EVOLUTION_REPORT.md` in the repository root. It must include:

- the pinned starting commit and model/provider used;
- a four-row audit table with evidence and disposition;
- changes made and changes deliberately rejected or deferred;
- exact verification commands and results;
- limitations, including why one run is not evidence that every new mechanism
  improves task success;
- a proposed ablation campaign that compares a fixed baseline with one feature
  disabled at a time, even if running the full campaign is beyond this run.

Do not open a pull request, push commits, access unrelated credentials, or edit
the book repository. Stop only after the report, implementation, and relevant
verification are complete, or after documenting a concrete blocker in the
report.
