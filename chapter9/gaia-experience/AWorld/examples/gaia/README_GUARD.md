# GAIA Agent Guard Functionality Setup

## 1. Overview

This guide covers the additional setup required for the enhanced guard agent in the GAIA agent. For basic installation and setup, please refer to [README.md](README.md).

## 2. Setting Up Guard Functionality

### 2.1 MCP Configuration

To enable the guard functionality, ensure the following MCP server is registered in your `mcp.json` file:

```json
{
    "mcpServers": {
        "maneuvering": {
            "command": "python",
            "args": [
                "-m",
                "examples.gaia.mcp_collections.intelligence.guard"
            ],
            "env": {},
            "client_session_timeout_seconds": 9999.0
        }
    }
}
```

### 2.2 Configure Environment Variables

Add the guard_llm API key to your `.env` file:

```bash
# Add this line to examples/gaia/cmd/agent_deploy/gaia_agent/.env
GUARD_LLM_API_KEY=your_guard_llm_api_key_here
```

### 2.3 Update Prompt Configuration

Replace the content of `prompt.py` with the enhanced version from `prompt_w_guard.py`:

```bash
cp examples/gaia/prompt_w_guard.py examples/gaia/prompt.py
```

### 2.4 Configure Task Subset Processing

To run specific subsets of GAIA tasks, add the following code to `run.py`:

```python
# load task subset from subset.txt
subset_file_path = Path(__file__).parent / "subset.txt"

if subset_file_path.exists():
    with open(subset_file_path, "r", encoding="utf-8") as f:
        task_subset = set(line.strip() for line in f if line.strip())
    logging.info(f"Loaded {len(task_subset)} task IDs from subset.txt")
else:
    task_subset = set()  # Empty set if file doesn't exist
    logging.warning("subset.txt file not found, using empty task subset")
```

And add the filtering logic in the main processing loop:

```python
# only process tasks that are in the subset
if dataset_i["task_id"] not in task_subset:
    continue
```


## 3. Configuration Summary

To enable guard functionality, ensure you have:

1. ✅ **MCP Configuration**: `maneuvering` server registered in `mcp.json`
2. ✅ **Environment Variables**: `GUARD_LLM_API_KEY` added to `.env` file
3. ✅ **Prompt Update**: `prompt_w_guard.py` content copied to `prompt.py`
4. ✅ **Subset Processing**: Batch processing code added to `run.py`


This setup provides enhanced reasoning capabilities and efficient batch processing for GAIA task evaluation.
