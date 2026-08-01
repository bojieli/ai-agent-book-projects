# Experiment Layout Conventions

This is the working convention for cleanup after the `chapter1/context` pilot.
It is intentionally small: chapter experiments stay independent teaching
projects, and only shared plumbing belongs in `agentbook/`.

## Target Shape

Use this shape for runnable Python experiments when it fits the project:

```text
experiment-name/
├── README.md
├── main.py
├── agent.py
├── config.py
├── fixtures/
├── tests/
│   └── manual/
├── requirements.txt
└── env.example
```

Not every experiment needs every file. Prefer the smallest structure that makes
the runnable entry point, tests, fixtures, and generated outputs obvious.

## Entry Points

- Prefer one documented command-line entry point, usually `main.py`.
- Keep helper modules next to the entry point when they are part of the teaching
  code, for example `agent.py`, `tools.py`, `config.py`, or `sources.py`.
- Keep setup helpers at the experiment root only when they are part of normal
  local use, for example `create_sample_pdf.py`.
- Move old quick checks or provider smoke scripts to `tests/manual/` unless they
  are the primary way readers run the experiment.
- Do not move teaching logic into `agentbook/`; shared provider/dependency
  plumbing can live there.

## Provider Portability

- A vendor-specific reference implementation may remain canonical when an
  experiment measures that exact model or native tool protocol, but ordinary
  readers should not need that vendor's credential merely to exercise the
  chapter's mechanism.
- Document a provider-portable path when an equivalent endpoint exists. Prefer
  an explicit base URL, requested model ID, and API-key variable over a hidden
  fallback. For visual Computer Use, retain at least one open-weight model API
  path plus a generic self-hosted OpenAI-compatible path.
- A fallback model is a separate experimental arm, not a reproduction of the
  reference model. Store the requested model, provider-reported model, endpoint,
  raw credential-free response, and behavior evidence for each arm.
- Fail closed when an endpoint drops required modalities, schemas, or tools.
  Successful authentication, model listing, installation, or browser launch is
  not task-completion evidence.
- Never put API-key values in receipts. Record only the environment-variable
  name used, and scan retained requests/responses before committing evidence.

## Installation Docs

- README setup should prefer the root chapter extra, for example
  `uv sync --locked --python 3.12 --extra chN`.
- Activate the root `.venv` before changing into the experiment directory.
- Keep the pip fallback: `python -m pip install -e ".[chN]"`.
- Keep `python -m pip install -r requirements.txt` as a commented compatibility
  path while the migration is active.
- Document platform-specific or isolated environments explicitly instead of
  pretending one root extra covers incompatible stacks.

## Tests

- Automated regression tests go under `tests/` and should run with
  `python -m pytest tests` from the experiment directory.
- When documenting pytest commands for a clean environment, include the `dev`
  extra from the repository root, for example
  `uv sync --locked --python 3.12 --extra chN --extra dev`.
- The equivalent pip testing fallback is `python -m pip install -e ".[chN,dev]"`.
- Automated tests should avoid live API calls, network dependence, GPU-only
  paths, and heavyweight model downloads unless they are explicitly marked and
  isolated.
- Use fixtures and mocks for deterministic behavior.
- If tests import root-level experiment modules after being moved, add a small
  `tests/conftest.py` path bootstrap rather than changing user-facing imports.
- Manual/live smoke scripts go under `tests/manual/` and should not be named
  `test_*.py` or `*_test.py`, so pytest does not collect them by default.
- Manual scripts should state which API keys or external tools they require.

## Fixtures

- Put deterministic local data under `fixtures/`, with subdirectories by type
  when useful, for example `fixtures/pdfs/`.
- Keep tracked fixtures small and stable.
- If a helper can regenerate a fixture, document both the helper and the fixture
  location in the README.
- Update code paths and README examples together when moving fixtures.

## Generated Outputs

- Do not track normal run outputs unless the file is a deliberate fixture or
  golden example.
- Prefer a documented output directory such as `output/`, `outputs/`, or
  `results/`, or an explicit `--output PATH` option.
- Make generated-output defaults consistent within an experiment before applying
  that convention to other experiments.
- Add or update ignore rules before changing commands that create new output
  paths.

## README Checklist

Each runnable experiment README should answer:

- What concept does this experiment teach?
- What is the one recommended install path?
- What is the compatibility install path during migration?
- What command runs the default demo?
- Which commands are offline/no-key and which need credentials?
- Where are tests, fixtures, manual smoke scripts, and generated outputs?
- Which platform/system dependencies are separate from Python dependencies?

## Migration Checklist

When cleaning an existing experiment:

- Move the smallest set of files needed to clarify the layout.
- Preserve direct execution from the experiment directory.
- Rename manual checks away from `test_*.py` if they need live credentials.
- Keep automated tests runnable through `python -m pytest tests`.
- Update code paths, README commands, and project structure diagrams in the same
  change.
- Run targeted validation for the experiment plus repository docs checks.

Baseline validation for a layout-only change:

```bash
git diff --check
python scripts/check_i18n_consistency.py
uv lock --check
```

Then add experiment-specific checks, for example:

```bash
uv sync --locked --python 3.12 --extra chN --extra dev
python -m pytest tests
python main.py --help
python tests/manual/show_sample_tasks.py
```
