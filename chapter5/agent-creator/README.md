# Experiment 5-13: An Agent That Creates Agents

This is the runnable companion for Chapter 5, Experiment 5-13. It implements the
book's complete comparison rather than merely pointing at `coding-agent` as a
possible starting point.

The experiment asks the same real model to create two specialized Agents:

1. **From scratch**: generate the Agent loop, tool protocol, domain tools, CLI,
   and tests with no reference implementation.
2. **Template adaptation**: copy the proven `reference_agent`, preserve its
   standard message/tool loop, and generate only the domain-specific prompt,
   tool schemas, implementations, documentation, and tests.

Both outputs pass the same gates:

- required-file and secret scan;
- Python AST/compile validation;
- standard `assistant.tool_calls → role=tool` protocol audit;
- bounded-loop audit;
- generated pytest suite;
- a real API run of the generated Agent on its own sample task.

The resulting `comparison.json` records generation time and token use, every
validation gate, the live Agent trace, and the winning strategy. There is no
mock fallback in the default experiment: missing credentials or a failed live
Agent run fails the command.

## Run

```bash
cd chapter5/agent-creator
pip install -r requirements.txt
cp env.example .env
python demo.py --output runs/release-agent
```

Use a custom target:

```bash
python demo.py \
  --requirements "Create an incident triage Agent that queries service health and drafts an evidence-backed escalation" \
  --output runs/incident-triage
```

`--no-live` exists only for deterministic CI/unit testing. It is not considered
a completed experiment run.

## Files

- `creator.py`: real-model creator and the two controlled comparison arms.
- `reference_agent/`: the known-good Agent that template mode copies.
- `validator.py`: common structural, test, and live-runtime gates.
- `demo.py`: one-command end-to-end comparison.
- `test_creator.py`: creator safety and orchestration tests.

## Security boundary

Generated paths are allowlisted, credentials are never placed in prompts or
generated files, and live execution occurs only after structural and test gates.
Generated domain tools still execute local code, so review them before using the
output outside an isolated experiment directory.
