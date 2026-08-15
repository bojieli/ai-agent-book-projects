# Experiment 6-7: Model action thresholds in a fixed coding harness

This experiment tests whether an explore-first or implement-first tendency
follows the **model** when the coding harness is held fixed. Both model
families receive the same system prompt, user task, repository, tool names,
JSON schemas, tool results, turn limit, and independent test command. By
default both are also routed through the same OpenRouter OpenAI-compatible
endpoint, reducing provider-adapter differences.

The neutral prompt does not require the model to read any number of files,
produce a plan, edit early, or run tests. The experiment records what the
model chooses to do.

## Tasks and metrics

Three miniature repositories cover a localized bug, a cross-cutting identity
change, and a public-contract-sensitive cache fix. Every fixture starts with
failing tests. Each run is performed in a fresh temporary copy and is
independently tested at the end.

Primary process metrics:

- tool calls and elapsed time before the first edit;
- read/search calls and unique files read before the first edit;
- whether the first model-triggered test run passes;
- edits after the first test, total edits, and files changed;
- final test success, latency, and token usage.

Time to first edit is not a quality score. Interpret it together with
first-patch acceptance, rework, final success, and total cost.

## Install and run

From the repository root:

```bash
uv sync --locked --extra ch6
export OPENROUTER_API_KEY=...
uv run python chapter6/model-action-threshold/experiment.py \
  --models openai/gpt-5.6-sol anthropic/claude-sonnet-5 \
  --trials 3 \
  --policy neutral \
  --output chapter6/model-action-threshold/results/my-run
```

The runner alternates model order between trials and checkpoints the campaign
after every cell. Re-running the same command and output directory resumes
only the missing model × task × trial cells. `config.json` hashes the system prompt and tool schema;
`observations.jsonl` retains every trajectory; `summary.json` aggregates the
metrics; and `manifest.json` hashes those three artifacts.

Run the optional harness ablation separately:

```bash
uv run python chapter6/model-action-threshold/experiment.py \
  --models openai/gpt-5.6-sol anthropic/claude-sonnet-5 \
  --trials 3 --policy explore-first \
  --output chapter6/model-action-threshold/results/explore-first
```

Do not merge neutral and explore-first observations into one model comparison.
The first run estimates the model effect under a neutral harness; comparing
the two campaigns estimates how much an explicit harness instruction modifies
that behavior.

## Validate the implementation

The offline tests verify path confinement, event-boundary accounting, rework
measurement, aggregation, and that every fixture starts in the intended
failing state:

```bash
python -m unittest discover -s chapter6/model-action-threshold/tests -v
```

The saved validation campaign in `results/` is considered complete only when
its manifest contains every requested model × task × trial observation and no
API errors. Model task failures remain valid experimental outcomes and are not
silently discarded.
