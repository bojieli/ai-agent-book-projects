# VERL Adapter (AWorld Train)

This module hosts the VERL integration for AWorld training workflows.

- aworld_agent_loop.py: Base class bridging VERL AgentLoop with AWorld agents.
- common.py: 
  - Utilities for converting trajectories/messages to VERL AgentLoopOutput.
  - Utilities for getting MCP server configuration.

## Usage
Import adapter entrypoints from your example code:

```python
from train.adapter.verl.aworld_agent_loop import AworldAgentLoop
```
Then implement your example-specific loop:
```python
class MyLoop(AworldAgentLoop):
    def build_agents(self):
        ...
```

## Adding New Features
- Avoid putting example-specific code here; that belongs in train/examples/.

## Notes
- Prefer small, composable utilities and explicit public APIs.
