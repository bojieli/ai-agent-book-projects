# Experiment 10-7: Stanford Generative Agents reproduction

This project runs the manuscript's full Agent-society experiment against the
official `joonspk-research/generative_agents` source at commit
`fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4`. It preserves the upstream
25-persona Smallville environment and ten-second world step while replacing
the obsolete GPT-3 API surface with current OpenAI-compatible chat and
embedding endpoints at runtime. The upstream checkout is not modified.

Status: **campaign running**. Completion requires three equal 17,280-step
(two-virtual-day) arms and retained analysis:

- `baseline`: the original Isabella Rodriguez Valentine's party and Sam Moore
  mayoral-election seeds;
- `custom_goal`: the same history seed, with Isabella's initial party goal
  replaced by a community climate-resilience workshop at the same place and
  time;
- `no_reflection`: the baseline goal with `Persona.reflect()` disabled and the
  importance trigger raised defensively, preserving perception, retrieval,
  planning, execution, and chat memory but preventing new reflection thoughts.

All three arms fork one shared history-loaded step-zero seed. This controls for
the 248 relationship memories in upstream `agent_history_init_n25.csv` and for
their generated thought/event-triple/poignancy/embedding representations.

## Environment

Use an isolated Python 3.11 environment because the 2023 source depends on the
legacy `openai` 0.27 API:

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
git clone https://github.com/joonspk-research/generative_agents.git /tmp/generative_agents
git -C /tmp/generative_agents checkout --detach fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4
```

Set `DASHSCOPE_API_KEY` in the environment. The default current models are
`qwen3.7-flash` and `text-embedding-v4` through DashScope's international
OpenAI-compatible endpoint. `GA_OPENAI_API_BASE`, `GA_CHAT_MODEL`, and
`GA_EMBEDDING_MODEL` are explicit overrides; changing them defines a different
experimental configuration.

The adapter never serializes the credential. It retains full chat
requests/responses, provider IDs, token usage, latency, and errors. Embedding
vectors remain in the simulation memory state; receipts retain their dimension
and content hash instead of duplicating every float.

Transient transport failures (`APIConnectionError`, timeout, rate limit, or
service unavailable) are retried up to five times inside the same logical
provider call with bounded exponential backoff. The successful logical receipt
retains every failed transport attempt in `transport_retries`; an exhausted or
non-transient failure remains `success: false`. Any checkpoint containing a
failed logical call is quarantined as `.failed-*` and replayed from the last
clean checkpoint instead of advancing canonical status. Each physical request
has a 90-second client timeout by default; `GA_PROVIDER_TIMEOUT_SECONDS` is an
explicit override.

The runtime overlay also contains one narrow compatibility correction for the
legacy action-arena prompt. Upstream asks for `{arena}` but removes only the
closing brace before looking up the arena. The overlay strips response-only
braces, quotes, and whitespace, then matches case-insensitively to an exact
arena returned by the persona's spatial memory. Invalid output stays in the
current arena when that arena is accessible in the selected sector, otherwise
it uses the first accessible arena in upstream order. It can never return an
arena outside that accessible list. Every changed output is retained in a
credential-free per-checkpoint JSONL compatibility receipt.

## Run and resume

Prepare the identical history seed once:

```bash
.venv/bin/python run_campaign.py \
  --upstream /tmp/generative_agents \
  --output outputs/exp10-7 \
  --mode seed
```

Launch or resume all three arms as detached processes:

```bash
.venv/bin/python launch_campaigns.py \
  --upstream /tmp/generative_agents \
  --output outputs/exp10-7 \
  --python .venv/bin/python
```

Each arm saves after 360 steps (one virtual hour). A status file is updated
atomically only after the simulation state and compressed provider receipt are
durable. Restarting the launcher resumes from that checkpoint. The day-one
checkpoint and final state are retained; superseded hourly storage copies are
removed after the next checkpoint succeeds.

Run offline tests with:

```bash
python -m pytest tests
```

Generated campaigns belong under `outputs/` and are ignored until a completed,
validated evidence package is deliberately selected for retention.
