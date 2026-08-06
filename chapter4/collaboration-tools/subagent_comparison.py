"""Compare the two sub-agent context-passing strategies (实验 4-4「对比效果」).

Spawns a sub-agent under BOTH `minimal` and `llm_generated` strategies on the
SAME task and prints the difference (context tokens handed off, extra
preparation cost, whether private data leaked, and each sub-agent's result).

Run:
    export OPENAI_API_KEY=your-openai-api-key        # or OPENROUTER_API_KEY (default model: gpt-5.6-luna)
    python subagent_comparison.py
"""

import asyncio
import os
import sys

# Make the src/ modules importable (they use bare imports, matching quickstart).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from subagent_tools import run_context_strategy_comparison  # noqa: E402


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
        print("No LLM key set. Export OPENAI_API_KEY or OPENROUTER_API_KEY "
              "(universal fallback; default model: gpt-5.6-luna).")
        sys.exit(1)
    asyncio.run(run_context_strategy_comparison())
