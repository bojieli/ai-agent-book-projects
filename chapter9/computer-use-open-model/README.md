# Open-model Computer Use companion

This is the provider-portable arm for Experiments 9-6 and 9-7. It runs the
same screenshot → structured action → browser execution loop without requiring
an Anthropic or OpenAI model account. The documented hosted route uses the
open-weight `qwen/qwen3-vl-32b-instruct` model through OpenRouter. The same
runner accepts a self-hosted vLLM/SGLang endpoint or another OpenAI-compatible
host.

The Anthropic Computer Use Demo remains a useful reference implementation for
its native `computer`, `bash`, and editor tools. This companion does not claim
that Qwen and Claude are interchangeable. Runs from different models are
separate experimental arms and must retain the actual endpoint and model ID.

## Current evidence

The [canonical open-model run](validation/latest.json) passed on 2026-08-01.
OpenRouter returned the requested `qwen/qwen3-vl-32b-instruct` model for all
16/16 calls. The Agent hit a Google CAPTCHA, recovered through weather.com,
and completed in 16 steps. The deterministic validator matched the final
64°F/Sunny answer to the retained browser observation, verified 15 screenshot
hashes and the one-action-per-step read-only trajectory, and found no retained
credential. This completes the Experiment 9-7 open-model arm only; the
Anthropic-native Experiment 9-6 arm remains unrun.

## Endpoint contract

An endpoint is eligible when it:

- accepts screenshot images in OpenAI-compatible chat messages;
- can produce the Browser Use action schema, either with native `json_schema`
  support or with schema-in-prompt JSON;
- returns enough information for the Agent to choose one browser action per
  step; and
- does not silently replace the requested model.

The reference open model is Qwen3-VL 32B Instruct. “Open model” describes the
weights/license; OpenRouter is only one hosted API route. Readers can use their
own compatible host instead.

## Install

Use Python 3.11 or newer. The isolated requirement pins the exact Browser Use
commit audited by the chapter (`ec9277c…`, package version `0.9.5`); the PyPI
release carrying the same version string is not substituted for that commit:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Hosted open-model route

```bash
cp env.example .env
export OPENROUTER_API_KEY='replace-with-your-key'

python main.py --dry-run
python main.py \
  --task "Open Google, search for San Francisco weather today, and report the temperature and conditions. Do not sign in or change any external data." \
  --max-steps 25 \
  --record-video
```

The default model is `qwen/qwen3-vl-32b-instruct`. Override
`OPEN_MODEL_MODEL` to select another explicitly open-weight vision model; do
not describe a proprietary model reached through the same gateway as an open
model.

## Self-hosted or another compatible API

Start a vision-capable OpenAI-compatible server, then configure its URL and
served model name. The runner does not require an OpenRouter key in this mode:

```bash
export OPEN_MODEL_API_KEY=local
export OPEN_MODEL_BASE_URL=http://127.0.0.1:8000/v1
export OPEN_MODEL_MODEL=Qwen/Qwen3-VL-32B-Instruct
python main.py --dry-run
python main.py --headless
```

If the host accepts images but rejects `response_format: json_schema`, set
`OPEN_MODEL_SCHEMA_MODE=prompt`. This is a compatibility fallback, and its
reliability should be reported separately because schema adherence can change.

## Retained evidence

Every non-dry run creates a new `runs/open-model-<UTC>/` directory containing:

- `preflight.json`: redacted endpoint, exact model, task, and execution limits;
- `api-receipts.json`: credential-free request hashes and raw provider responses,
  including provider-reported model IDs when supplied;
- `history.json`: ordered model decisions, actions, observations, and results;
- `screenshots/` plus `screenshots.json`: retained per-step visual observations;
- `summary.json` or `failure.json`: outcome and honest failure state; and
- `manifest.json`: SHA-256 and byte size for every retained artifact.

No API-key value is written. The Agent's `done` result is only an
agent-reported outcome; manuscript-level completion still requires independent
checking of the weather answer and action trajectory. A dry run, model-list
lookup, or browser launch alone is not completion evidence.

Validate a retained run against its provider receipts, one-action-per-step
limit, final browser observation, screenshot hashes, and credential scan:

```bash
python validate_run.py runs/<run-id> --latest validation/latest.json
```
