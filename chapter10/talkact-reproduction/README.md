# Experiment 10-4: TalkAct concurrent-agent reproduction

This record covers the pinned external TalkAct reproduction used by Experiment
10-4. The comparison runs concurrent fast/slow agents (`duplex`) against a
single-model control (`strawman`) over four hermetic tasks and two labeled
repetitions per task and condition.

Status: **complete for the retained Anthropic-caller configuration**. The
[canonical run](validation/runs/exp10-4-talkact-anthropic-caller-20260803-v2/)
contains all 16 episode logs, aggregate and per-episode analysis, the exact
protocol and environment, console logs, and a manifest. The independent
validator passes all 17 gates.

## Configuration and deviation

The campaign used the official `19PINE-AI/TalkAct` source at commit
`7d70007f72d45ddfc1a14e8e229b6d444e4919a2`, Python 3.12.11, Playwright
Chromium 149, and the hermetic Flask task server. The concurrent arm kept the
pinned source's fast `claude-haiku-4-5` and slow `claude-opus-4-8` agents; the
strawman arm kept the slow model alone.

TalkAct normally uses Gemini for its simulated caller, but the configured
Gemini credential returned `400 API_KEY_INVALID`. The campaign therefore used
the source-supported `CUV_USER_MODEL=claude-sonnet-4-5-20250929` override. This
preserves the task and agent topology but makes the caller Anthropic-based too,
which can introduce same-family bias. These results are a distinct
Anthropic-caller configuration and must not be silently pooled with upstream
results that use the default Gemini caller.

The exact campaign was:

```bash
CUV_USER_MODEL=claude-sonnet-4-5-20250929 python bench/run_bench.py \
  --tasks forms-insurance booking-flight webmail-report meeting-helper \
  --conditions duplex strawman \
  --seeds 2
```

## Results

| Metric | Duplex | Strawman |
| --- | ---: | ---: |
| Episodes | 8 | 8 |
| Task success | 1.000 | 1.000 |
| Partial credit | 1.000 | 1.000 |
| Probe correctness | 0.833 | 0.917 |
| Voice latency p50 | 2.32 s | 12.52 s |
| Voice latency p90 | 2.85 s | 21.14 s |
| Voice latency maximum | 4.03 s | 37.29 s |
| Mean episode wall time | 207.2 s | 178.0 s |
| Voice-latency samples | 47 | 44 |

All 12 action-scored episodes achieved full deterministic success and partial
credit. The four `meeting-helper` episodes intentionally have no action-success
field and instead earned perfect retained probe-answer scores. There were no
episode or provider errors.

The concurrent arm reduced median voice latency by about **5.40×**
(`12.52 / 2.32`), materially below the upstream roughly 15× result. It did not
improve task success: the arms tied. The control also had higher aggregate
probe correctness (0.917 versus 0.833) and lower mean wall time (178.0 seconds
versus 207.2 seconds). The retained run therefore supports a response-latency
advantage for duplex, not a blanket quality or total-runtime advantage.

## Evidence and validation

The 16 raw episodes retain 39 fast-to-slow relays, 33 slow-to-fast events, 91
voice-latency samples, deterministic task checks, probe grades, transcripts,
environment state, and aggregate provider usage. The duplex slow tier used
19,124 input and 26,105 output tokens across 166 steps; its fast tier used
98,945 input and 5,782 output tokens across 87 turns. The strawman slow tier
used 19,208 input and 28,966 output tokens across 177 steps. Cache-read and
cache-creation counts are retained in the episode records.

Run the validator from the repository root:

```bash
python chapter10/talkact-reproduction/validate_campaign.py \
  chapter10/talkact-reproduction/validation/runs/exp10-4-talkact-anthropic-caller-20260803-v2
```

The generated [acceptance report](validation/runs/exp10-4-talkact-anthropic-caller-20260803-v2/acceptance.json)
passes source-pin, campaign-shape, model, usage, error, concurrency, bridge,
latency, task-check, judge, aggregate, and credential-scan gates. The
[manifest](validation/runs/exp10-4-talkact-anthropic-caller-20260803-v2/manifest.json)
hashes the 23 inputs and outputs from which those generated files are derived.
The earlier [authentication preflight](validation/exp10-4-anthropic-auth-20260803-v1/preflight.json)
is retained as failure history, not as the final result.

## Limitations

- The pinned runner's `--seeds` option labels repetitions but does not inject a
  deterministic random seed into the episode runner or provider calls.
- The pinned source retains model labels and aggregate fast/slow token usage
  per episode, but not individual provider response IDs.
- Simulated-caller token usage is not retained by the pinned source.
- `meeting-helper` is evaluated through retained probe grades rather than the
  action-based success and partial-credit fields used by the other tasks.
- The Anthropic caller deviation preserves the benchmark topology but is not
  directly comparable to the upstream default-Gemini caller configuration.
