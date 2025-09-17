# Context Compression Strategies Experiment

This project demonstrates and compares different context compression strategies for LLM agents, using the task of researching OpenAI co-founders' current affiliations as a test case.

## Overview

As LLM context windows grow larger (128K+ tokens), managing context efficiently becomes crucial for:
- **Cost optimization** - Reducing token usage
- **Performance** - Faster response times
- **Reliability** - Avoiding context overflow errors
- **Relevance** - Maintaining focus on important information

This experiment implements and compares 6 different context compression strategies to understand their trade-offs.

## Compression Strategies

### 1. No Compression
- **Description**: Puts all original webpage content directly into agent context
- **Expected Result**: Fails after a few tool calls due to context overflow
- **Purpose**: Demonstrates the baseline problem

### 2. Non-Context-Aware: Individual Summaries
- **Description**: Summarizes each webpage independently using LLM, then concatenates all summaries
- **Expected Result**: Preserves page-specific details but may lose cross-page relationships
- **Trade-off**: Multiple LLM calls (one per page) but maintains page boundaries
- **Best for**: When each source should be treated independently

### 3. Non-Context-Aware: Combined Summary
- **Description**: Concatenates all webpage content first, then creates a single comprehensive summary
- **Expected Result**: Better understanding of overall content but may lose page-specific attribution
- **Trade-off**: Single LLM call but might hit token limits with many pages
- **Best for**: When looking for overarching themes across multiple sources

### 4. Context-Aware Summarization
- **Description**: Combines all search results and creates query-focused summary
- **Expected Result**: Better relevance preservation
- **Trade-off**: Requires additional LLM call for summarization

### 5. Context-Aware with Citations
- **Description**: Similar to #4 but includes citations and source links
- **Expected Result**: Enables follow-up questions with source tracking
- **Trade-off**: Slightly larger context but maintains traceability

### 6. Windowed Context
- **Description**: Keeps full content for last tool call, compresses older history
- **Expected Result**: Balance between detail and efficiency
- **Trade-off**: Recent detail vs. historical compression
- **Smart Compression**: Only compresses uncompressed messages (marked with [COMPRESSED] to prevent re-compression)

## Installation

1. Clone the repository and navigate to the project:
```bash
cd projects/week2/context-compression
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your API keys
```

Required API keys:
- `MOONSHOT_API_KEY`: For Kimi K2 model (required)
- `SERPER_API_KEY`: For web search (optional, will use mock data if not provided)

Get API keys:
- Moonshot/Kimi: https://platform.moonshot.cn/
- Serper (free tier): https://serper.dev/

## Scripts Overview

| Script | Purpose | Output |
|--------|---------|--------|
| `demo.py` | Interactive demo with single strategy selection | Console output |
| `experiment.py` | Automated comparison of all strategies | Results in `results/` |
| `run_all_strategies.py` | Run all strategies with detailed logging | Logs in `logs/` |

## Usage

### Run Full Experiment

Compare all 6 strategies:
```bash
python experiment.py
```

This will:
- Test each compression strategy sequentially
- Research OpenAI co-founders' affiliations
- Generate metrics and comparison report
- Save results to `results/experiment_TIMESTAMP.json`

### Run All Strategies with Logging

Run all strategies with detailed logging and compression output:
```bash
python run_all_strategies.py
```

Features:
- Runs all 6 compression strategies sequentially
- Logs all compression summaries to file
- Shows streaming output in real-time
- Saves detailed logs to `logs/strategy_run_TIMESTAMP.log`
- Saves JSON results to `logs/strategy_results_TIMESTAMP.json`
- Generates comparison summary at the end

### Interactive Demo

Test individual strategies with streaming output:
```bash
python demo.py              # Default: streaming enabled
python demo.py --no-streaming  # Disable streaming output
```

Features:
- Choose any compression strategy
- Streaming responses enabled by default
- Optional `--no-streaming` flag to disable streaming
- See real-time execution
- Try follow-up questions (for citation strategy)

### Custom Usage

```python
from agent import ResearchAgent
from compression_strategies import CompressionStrategy

# Create agent with specific strategy
agent = ResearchAgent(
    api_key="your_api_key",
    compression_strategy=CompressionStrategy.CONTEXT_AWARE_CITATIONS,
    enable_streaming=True
)

# Execute research
result = agent.execute_research()

# Access results
if result['success']:
    print(result['final_answer'])
    print(f"Tool calls: {len(result['trajectory'].tool_calls)}")
```

## Project Structure

```
context-compression/
├── config.py                  # Configuration management
├── web_tools.py              # Web search and fetch tools
├── compression_strategies.py  # Compression strategy implementations
├── agent.py                  # Main research agent with streaming
├── experiment.py             # Experiment runner for comparisons
├── demo.py                   # Interactive demo
├── requirements.txt          # Python dependencies
├── env.example              # Environment variables template
└── results/                 # Experiment results (created on run)
```

## Key Components

### Web Tools (`web_tools.py`)
- **search_web**: Searches using Serper API, crawls each result
- **fetch_webpage**: Fetches and converts HTML to clean text
- **Mock data**: Provides sample data when API key unavailable

### Compression Strategies (`compression_strategies.py`)
- **ContextCompressor**: Implements all 5 strategies
- **CompressedContent**: Data class for compressed results
- **Dynamic compression**: Based on query and context

### Research Agent (`agent.py`)
- **Streaming support**: Real-time response streaming
- **Tool integration**: Web search and fetch capabilities
- **Message management**: Handles conversation history
- **Windowed compression**: Dynamic history compression

### Experiment Runner (`experiment.py`)
- **Automated testing**: Runs all strategies
- **Metrics collection**: Execution time, compression ratio, success rate
- **Comparison report**: Visual comparison table
- **Results persistence**: JSON output for analysis

## Metrics Collected

- **Success Rate**: Whether task completed successfully
- **Execution Time**: Total time to complete research
- **Compression Ratio**: Compressed size / original size
- **Context Overflows**: Number of times context limit approached
- **Tool Calls**: Number of web searches performed
- **Final Answer Length**: Size of generated report

## Expected Results

Based on the compression strategies:

1. **No Compression**: ❌ Fails with context overflow
2. **Non-Context-Aware**: ⚠️ Completes but may miss details
3. **Context-Aware**: ✅ Good balance of size and relevance
4. **With Citations**: ✅ Best for follow-ups, slightly larger
5. **Windowed Context**: ✅ Most efficient for long conversations

## Configuration

Edit `.env` or `config.py` for:

- `MODEL_NAME`: LLM model to use (default: kimi-k2-0905-preview)
- `MODEL_TEMPERATURE`: Response randomness (default: 0.3)
- `MAX_ITERATIONS`: Maximum tool calls (default: 50)
- `MAX_WEBPAGE_LENGTH`: Max chars per webpage (default: 50000)
- `SUMMARY_MAX_TOKENS`: Max tokens for summaries (default: 500)
- `CONTEXT_WINDOW_SIZE`: Model context limit (default: 128000)

## Troubleshooting

### No API Keys
The system will use mock data if SERPER_API_KEY is not set, allowing you to test the compression strategies without web search.

### Context Overflow
If you encounter context overflow with strategies other than "No Compression", try:
- Reducing `MAX_WEBPAGE_LENGTH`
- Decreasing `SUMMARY_MAX_TOKENS`
- Limiting search results with `num_results`

### Slow Execution
- Disable streaming in demo for faster output
- Reduce `MAX_ITERATIONS` for quicker experiments
- Use mock data instead of real web search

## Research Task

The experiment uses a specific research task:
> "Find the current affiliations of all OpenAI co-founders"

This task is ideal because it:
- Requires multiple searches (one per co-founder)
- Generates substantial content (biographical information)
- Tests context management (accumulating information)
- Has verifiable results (known affiliations)

## Extending the Project

To add new compression strategies:

1. Add strategy to `CompressionStrategy` enum
2. Implement in `ContextCompressor` class
3. Add handling in `compress_search_results()`
4. Update experiment runner if needed

To change the research task:

1. Modify system prompt in `agent.py`
2. Update mock data in `web_tools.py`
3. Adjust tool descriptions as needed

## License

This project is part of the AI Agent practical training course and is for educational purposes.
