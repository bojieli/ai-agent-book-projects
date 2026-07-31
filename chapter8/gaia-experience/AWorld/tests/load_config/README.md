# YAML-based Config Guide

## Overview
Use a single YAML file to define multiple Agents and an optional Swarm topology. This loader supports two kinds of placeholders:
- `${ENV_VAR}`: Values come from system environment variables
- `${vars.KEY}`: Values come from the `vars` section of the same YAML file

When a field value is exactly a single placeholder like `${vars.DEFAULT_TEMPERATURE}`, the loader preserves the original type (e.g., float) instead of converting it to a string. This avoids type errors in LLM parameters such as `temperature`.

## Files in this folder
- `agents.yaml`: Example YAML configuration with environment and in-file variables
- `load_from_yaml.py`: Minimal runner that loads the YAML and executes a swarm

## Quick Start
1) Set your environment variables
   - PowerShell: `$env:OPENAI_API_KEY="your-openai-api-key" ; $env:OPENROUTER_API_KEY="your-openrouter-api-key"`
   - macOS/Linux: `export OPENAI_API_KEY="your-openai-api-key" ; export OPENROUTER_API_KEY="your-openrouter-api-key"`
2) Run the example
   - `python examples/load_config/load_from_yaml.py`

## YAML Schema
Top-level keys:
- `vars`: Optional. In-file variables used by `${vars.KEY}`
- `agents`: Required. Map of agent name -> agent configuration
- `swarm`: Optional. Defines the topology (workflow, handoff, or team)

Example (abridged):
```yaml
vars:
  DEFAULT_TEMPERATURE: 0.1
  OPENAI_URL: https://api.openai.com/v1
  OPENROUTER_URL: https://openrouter.ai/api/v1

agents:
  researcher:
    system_prompt: "You specialize at researching."
    llm_config:
      llm_provider: openai
      llm_model_name: gpt-4o
      llm_api_key: ${OPENAI_API_KEY}  # from system env
      llm_base_url: ${vars.OPENAI_URL}  # from vars section
      llm_temperature: ${vars.DEFAULT_TEMPERATURE}  # from vars section

  summarizer:
    system_prompt: "You specialize at summarizing."
    llm_config:
      llm_provider: openai
      llm_model_name: google/gemini-2.5-pro
      llm_api_key: ${OPENROUTER_API_KEY}  # from system env
      llm_base_url: ${vars.OPENROUTER_URL}  # from vars section
      llm_temperature: ${vars.DEFAULT_TEMPERATURE}  # from vars section

swarm:
  type: workflow
  order: [researcher, summarizer]
```

## Variable Substitution
- System env: `${OPENAI_API_KEY}`
- In-file vars: `${vars.DEFAULT_TEMPERATURE}`

Type-preserving rule:
- If the entire value is exactly `${vars.KEY}`, the raw value from `vars` is used with its original type (float/int/bool/string)
- If `${vars.KEY}` appears inside a longer string, it is replaced as text (string interpolation)

Tip: For numeric LLM parameters (like `llm_temperature`), prefer defining numbers in `vars` without quotes (e.g., `0.1`, not `"0.1"`).

## Swarm Topologies
- `workflow`
  - Execute agents in the given `order`
  - Example: `order: [researcher, summarizer]`
- `handoff`
  - Use `edges: [[left, right], ...]` to define agent handoffs
- `team`
  - Define a `root` agent and `members: [ ... ]`

If `swarm` is omitted, the loader defaults to a workflow in the order agents are declared in YAML.

## Running from Python
```python
from aworld.config.agent_loader import load_swarm_from_yaml
from aworld.runner import Runners

swarm, agents = load_swarm_from_yaml("examples/load_config/agents.yaml")
result = Runners.sync_run(
    input="Tell me a complete history about the universe",
    swarm=swarm,
)
```

Access a specific agent if needed:
```python
summarizer = agents["summarizer"]
```

## Advanced: YAML anchors and merge keys (optional)
You can also use YAML anchors/aliases/merge keys to reuse blocks within the same file:
```yaml
llm_defaults: &llm_defaults
  llm_provider: openai
  llm_temperature: 0.1

agents:
  a:
    llm_config:
      <<: *llm_defaults  # merge default fields
      llm_model_name: gpt-4o
```
Note: Anchors are structural reuse (not string interpolation). Use `${vars.KEY}` for string placeholders.

## Troubleshooting
- Temperature type error (e.g., cannot unmarshal string into float64)
  - Ensure the value comes from `${vars.KEY}` as a full value and that the `vars` value is a number (unquoted). The loader preserves numeric types on full-value substitution.
- Placeholders not replaced
  - Missing environment variables or missing `vars.KEY`. Check the comments in YAML and set the needed values.
- Import error for loader
  - Make sure you are running against the project source (e.g., `pip install -e .`) or your `PYTHONPATH` includes the project root.

## API Reference
- `load_agents_from_yaml(path) -> Dict[str, Agent]`
  - Load agents only
- `load_swarm_from_yaml(path) -> Tuple[Swarm, Dict[str, Agent]]`
  - Load agents and build a swarm based on the `swarm` section (or default workflow)

This loader reuses the existing Pydantic configuration models under `aworld.config.conf` and does not add new dependencies.
