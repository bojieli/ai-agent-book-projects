# Experiment 6-1: τ²-bench telecom evaluation

This directory retains the bounded τ²-bench campaign requested by the
manuscript: five telecom tasks, one trial per task, with the same model acting
as the customer-service Agent and user simulator.

## Reproduction

The external checkout is deliberately not vendored. Clone and pin the
authoritative source first:

```bash
git clone https://github.com/sierra-research/tau2-bench.git chapter6/tau2-bench
git -C chapter6/tau2-bench checkout --detach 8d005b0e5b9e4af0bc055886fa7f95fc86d1710e
cd chapter6/tau2-bench
uv venv --python 3.12
uv pip install -e .
```

With `OPENROUTER_API_KEY` configured, the saved campaign used:

```bash
.venv/bin/tau2 run \
  --domain telecom \
  --agent-llm openrouter/openai/gpt-4.1-mini \
  --user-llm openrouter/openai/gpt-4.1-mini \
  --num-trials 1 \
  --num-tasks 5 \
  --max-concurrency 3 \
  --save-to exp6-1-openrouter-gpt41mini-telecom-5tasks-20260802-v1 \
  --log-level INFO
```

Both model temperatures were `0`; τ²-bench recorded seed `300`. The retained
raw trajectory is under
[`validation/runs/exp6-1-openrouter-gpt41mini-telecom-20260802-v1/`](validation/runs/exp6-1-openrouter-gpt41mini-telecom-20260802-v1/).

## Result

The Agent passed 4/5 tasks, for average reward and Pass@1 of **0.80**. All five
simulations ended normally with `user_stop`; there were no provider errors.
The retained provider-reported costs total about **$0.151312**: $0.112672 for
the Agent and $0.0386396 for the user simulator.

The failed task was
`[mobile_data_issue]data_saver_mode_on|data_usage_exceeded[PERSONA:Easy]`.
The customer supplied phone `555-123-2002`, but the Agent selected line
`L1001`. A later `get_details_by_id(L1001)` result explicitly associated that
line with phone `555-123-2001`; nevertheless, the Agent continued using its
3.2/5 GB usage reading. It correctly had the user disable Data Saver, but did
not inspect the matching `L1002` line or perform the required 2 GB data refuel.
It spent the remainder of a 71-message trajectory on unrelated diagnostics and
ultimately transferred to a human. Consequently, `refuel_data` and all three
downstream environment assertions failed. The trajectory also exposes an
earlier policy violation where the Agent emitted two customer-lookup tool calls
in one turn even though the telecom policy permits only one at a time.

This is a useful dual-control failure: the user-side Data Saver action occurred
and was verified in the shared environment, while the Agent-side line-selection
mistake prevented the second state mutation and final recovery.

## Verification boundary

The upstream public verifier reports:

- format validation: passed;
- trial-count validation: passed;
- task validation: failed because a public leaderboard submission must cover
  the full telecom task set.

That coverage failure is expected for the five-task command specified by this
book experiment. This evidence therefore establishes the bounded Experiment
6-1 campaign, not a full-domain τ²-bench leaderboard result. See
[`evidence.json`](validation/runs/exp6-1-openrouter-gpt41mini-telecom-20260802-v1/evidence.json)
for machine-readable outcomes and [`manifest.json`](validation/runs/exp6-1-openrouter-gpt41mini-telecom-20260802-v1/manifest.json)
for content hashes.
