# Experiment 10-1 retained comparison report

## Outcome

This is a **complete bounded comparison**. The campaign
retains 30 paired tasks (60 main trajectories), 12 boundary trajectories,
289 raw provider receipts, 31 raw Tavily receipts, and
60 position-swapped blind-judge receipts. Every evidence gate passes
(12/12).

- Transfer passed 2/30 complete
  deterministic task gates; its declared capability sequence completed in 40.0% of runs.
- Skill passed 15/30 complete
  deterministic task gates. It loaded at least triage in 30/30 runs,
  and completed the declared sequence in 90.0% of runs.
- Both arms passed 6/6 boundary cases; boundary reliability is reported separately from end-to-end task success.
- The independent Gemini 2.5 Flash Lite judge preferred Skill 32/60
  swapped presentations, Transfer 20/60, and called
  8/60 ties. The two presentations per pair were retained to
  control position bias.

## Cost and latency

The Skill-minus-Transfer median delta was 6855.0 uncached input tokens,
4.368 seconds, and $0.00044304. Provider-reported
cached input was zero throughout, so this run does not establish a model-prefix cache benefit. The Skill document
cache recorded per-run misses (and no hits across a run), as expected for the fresh-session cache used by this harness.

## Interpretation

For `qwen/qwen3.5-flash-02-23` under this bounded OpenRouter campaign, the repaired Skill arm now follows the
progressive-disclosure state machine and materially improves deterministic acceptance (50.0% vs 6.7%). The trade-off
is higher median uncached input (+6855.0 tokens), latency (+4.368s),
and repriced cost (+$0.00044304). This is evidence for the documented architecture trade-off,
not a universal model-independent superiority claim.
