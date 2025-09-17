# KV Cache Demonstration with ReAct Agent

A comprehensive demonstration of KV (Key-Value) cache importance in LLMs using a ReAct pattern agent with local file system tools. This project shows how different implementation patterns can significantly impact performance through their effect on KV cache utilization.

## 🎯 Overview

This project implements a ReAct (Reasoning and Acting) agent that uses the Kimi K2 model to analyze code projects. The agent uses the standard OpenAI tool calling format (similar to week1/context) and demonstrates six different implementation patterns - one correct and five incorrect - showing how seemingly minor changes can invalidate KV cache and dramatically impact performance.

### What is KV Cache?

KV cache stores the key-value pairs from the attention mechanism of transformer models. When the conversation context remains stable, these cached values can be reused, significantly reducing computation time and improving response latency (especially Time to First Token - TTFT).

## 🚀 Features

- **ReAct Pattern Agent**: Implements reasoning and acting pattern for systematic task execution
- **Standard Tool Calling**: Uses OpenAI's standard tool calling format (no manual parsing)
- **Local File System Tools**: Safe implementations of `read_file`, `find`, and `grep` commands
- **Robust Error Handling**: Continues execution when tools fail, passing errors as results
- **Six Implementation Modes**: Demonstrates correct and incorrect KV cache patterns
- **Comprehensive Metrics**: Tracks TTFT, total time, cache hits/misses, and token usage
- **Detailed Logging**: Provides insights into cache behavior and performance impact
- **Smart Completion**: Automatically considers responses without tool calls as final answers
- **Argument Filtering**: Safely handles unexpected tool arguments without breaking

## 📦 Implementation Modes

### 1. ✅ Correct Implementation (`correct`)
Maintains stable context throughout the conversation:
- Fixed system prompt
- Consistent tool ordering
- Stable message history format
- No unnecessary context changes

### 2. ❌ Dynamic System Prompt (`dynamic_system`)
Adds a timestamp to the system prompt on each request:
- **Recreates entire message context each iteration**
- Invalidates entire cache on every call
- Significantly increases TTFT
- Wastes computational resources

### 3. ❌ Shuffled Tools (`shuffled_tools`)
Randomly reorders the tool list for each request:
- **Recreates context with shuffled tools each iteration**
- Breaks cache even though functionality is identical
- Demonstrates importance of consistent ordering
- Shows how minor changes affect caching

### 4. ❌ Dynamic User Profile (`dynamic_profile`)
Includes changing user credits in the context:
- **Recreates context with updated credits each iteration**
- Adds unnecessary dynamic information
- Forces cache invalidation for irrelevant changes
- Simulates common anti-patterns in production

### 5. ❌ Sliding Window (`sliding_window`)
Keeps only the most recent 5 messages:
- **Recreates context with different message window each iteration**
- Appears to reduce context length
- Actually breaks cache continuity
- Demonstrates why truncation strategies can backfire

### 6. ❌ Text Format (`text_format`)
Formats conversation history as plain text instead of structured messages:
- **Recreates context in text format each iteration**
- Breaks the expected message format
- Prevents proper cache utilization
- Shows importance of following API conventions

### 🔑 Critical Implementation Details

**For KV cache to be properly invalidated in the incorrect modes, the entire message context must be recreated from scratch at the START of EACH iteration.** 

The implementation ensures this by:

1. **CORRECT mode**: 
   - Builds messages list **once** on first iteration
   - **Keeps using the same list** throughout execution
   - Appends new messages (assistant responses, tool results) to this persistent list
   - Result: Stable context → KV cache works efficiently

2. **Incorrect modes**:
   - **Recreates the entire messages list** from conversation history at the **start of each iteration**
   - Within an iteration, still appends tool results to ensure proper API flow
   - But next iteration starts fresh with recreated context
   - Result: Context changes → KV cache invalidated

**Important**: Both modes append tool results within an iteration to ensure the API sees the complete conversation flow. The key difference is that incorrect modes throw away the messages list and rebuild it at the start of each new iteration, which forces cache invalidation.

## 🛠️ Installation

```bash
# Navigate to the project directory
cd projects/week2/kv-cache

# Install dependencies
pip install -r requirements.txt

# Set your Kimi API key
export MOONSHOT_API_KEY="your-api-key-here"
```

## 📖 Usage

### Interactive Mode (Default)

```bash
# Run interactive mode selection menu
python main.py

# You'll see a menu like:
# ============================================================
# KV CACHE DEMONSTRATION - MODE SELECTION
# ============================================================
# 
# Select a mode to run:
# 
#   1. ✅ Correct Implementation - Optimal KV cache usage
#   2. ❌ Dynamic System Prompt - Adds timestamps
#   3. ❌ Shuffled Tools - Randomizes tool order
#   4. ❌ Dynamic Profile - Updates user credits
#   5. ❌ Sliding Window - Keeps only recent messages
#   6. ❌ Text Format - Plain text instead of structured
#   7. 📊 Compare All - Run all modes and compare
# 
#   0. Exit
```

### Command Line Options

```bash
# Run specific mode directly (bypasses menu)
python main.py --mode correct

# Run comparison across all modes
python main.py --compare

# Disable interactive mode
python main.py --no-interactive --mode correct

# Available modes: correct, dynamic_system, shuffled_tools, 
#                 dynamic_profile, sliding_window, text_format
```

### Custom Tasks

```bash
# Provide custom task via command line
python main.py --mode correct --task "Read all README files and summarize their contents"

# Use different root directory
python main.py --mode correct --root-dir ../.. --task "Analyze the project structure"
```

## 📊 Metrics Explained

### Performance Metrics
- **TTFT (Time to First Token)**: Time until the first token is generated - critical for user experience
  - Tracked per iteration to show cache benefits
  - First iteration: Cold start (no cache)
  - Subsequent iterations: Should show improvement with cache
- **TTFT Analysis**: 
  - Per-iteration tracking shows cache effectiveness
  - Average TTFT demonstrates overall performance
  - Improvement percentage quantifies cache benefits
- **Total Execution Time**: Complete time for task execution
- **Iterations**: Number of ReAct cycles performed
- **Tool Calls**: Number of tool invocations made

### Cache Statistics
- **Cached Tokens**: Number of tokens retrieved from cache
- **Cache Hits**: Successful cache retrievals
- **Cache Misses**: Failed cache retrievals requiring recomputation
- **Cache Hit Rate**: Percentage of successful cache usage

### Token Usage
- **Prompt Tokens**: Tokens in the input prompt
- **Completion Tokens**: Tokens generated by the model
- **Cache Ratio**: Percentage of prompt tokens served from cache

## 📈 Expected Results

When comparing implementations, you should observe:

1. **Correct Implementation**: 
   - High cache hit rate (>90% after first iteration)
   - Low TTFT after initial request
   - Most prompt tokens cached

2. **Incorrect Implementations**:
   - Low or zero cache hit rates
   - Consistently high TTFT
   - Minimal or no cached tokens
   - 2-5x slower than correct implementation

## 🔍 Example Output

```
📊 Performance Metrics:
  • Time to First Token (TTFT): 0.823 seconds
  • TTFT per iteration:
      Iteration 1: 0.823s
      Iteration 2: 0.234s (with cache)
      Iteration 3: 0.198s (with cache)
      Iteration 4: 0.187s (with cache)
      Iteration 5: 0.192s (with cache)
  • TTFT Analysis:
      First iteration: 0.823s
      Last iteration: 0.192s
      Average (after first): 0.203s
      Improvement: 76.7%

KV CACHE COMPARISON RESULTS
================================================================================

Mode                 First TTFT   Avg TTFT     Total (s)    Cached       Hit Rate    
---------------------------------------------------------------------------------------
correct              0.823        0.287        15.234       45,678       95.2        
dynamic_system       2.145        2.089        28.567       0            0.0         
shuffled_tools       2.089        2.012        27.123       1,234        12.3        
dynamic_profile      1.967        1.923        26.789       5,678        23.4        
sliding_window       1.234        1.189        20.456       12,345       45.6        
text_format          2.456        2.398        31.234       0            0.0         

📈 TTFT Progression (first 5 iterations):
  correct             : 0.82s → 0.23s → 0.20s → 0.19s → 0.19s
  dynamic_system      : 2.15s → 2.09s → 2.08s → 2.10s → 2.07s
  shuffled_tools      : 2.09s → 2.01s → 2.00s → 2.02s → 1.99s
```

## 💡 Key Insights

1. **Stable Context is Critical**: Any change to the message context invalidates KV cache
2. **Order Matters**: Even reordering identical content breaks caching
3. **Avoid Dynamic Metadata**: Timestamps, counters, and other changing data harm performance
4. **Proper Formatting**: Use the API's expected message format for optimal caching
5. **Context Continuity**: Maintaining full history often performs better than truncation

## 🏗️ Architecture

```
kv-cache/
├── agent.py                # ReAct agent implementation with different modes
├── main.py                 # Main script for running experiments
├── demo_quick.py           # Quick demonstration script
├── test_tools.py           # Test local file system tools
├── test_error_handling.py  # Test error recovery capabilities
├── test_completion.py      # Test final answer detection
├── requirements.txt        # Project dependencies
├── README.md              # This file
└── *.log                  # Generated log files
```

### Components

- **KVCacheAgent**: Main agent class implementing ReAct pattern
- **LocalFileTools**: Safe file system operations (read, find, grep)
- **KVCacheMode**: Enum defining different implementation patterns
- **AgentMetrics**: Dataclass for tracking performance metrics

### Error Handling

The agent implements robust error handling:
- **Tool Errors**: When a tool fails (e.g., file not found), the error is returned as a tool result
- **Argument Errors**: Unexpected tool arguments are filtered out automatically
- **Continuation**: The agent continues execution even when tools fail
- **Error Reporting**: Errors are passed to the model, which can acknowledge and work around them
- **Security**: Access outside the root directory is denied with clear error messages

## 🔧 Advanced Configuration

### Environment Variables

```bash
# API Configuration
export MOONSHOT_API_KEY="your-key"

# Logging Level
export LOG_LEVEL="DEBUG"  # INFO, WARNING, ERROR
```

### Custom Implementation Modes

You can extend the `KVCacheMode` enum in `agent.py` to add new patterns:

```python
class KVCacheMode(Enum):
    CUSTOM = "custom"  # Your new mode
```

Then implement the behavior in the corresponding methods:
- `_get_system_prompt()`
- `_get_tools()`
- `_format_messages()`

## 📝 Best Practices for KV Cache

Based on this demonstration, follow these practices:

1. **Keep System Prompts Stable**: Avoid adding timestamps or request-specific data
2. **Maintain Consistent Tool Order**: Don't shuffle or reorder tools dynamically
3. **Avoid Unnecessary Metadata**: Don't include counters, credits, or changing values
4. **Use Proper Message Format**: Follow the API's expected conversation structure
5. **Preserve Context Continuity**: Avoid aggressive truncation strategies
6. **Cache-Aware Design**: Design your prompts and context with caching in mind

## 🐛 Troubleshooting

### High TTFT with Correct Implementation
- Check if this is the first request (cold start)
- Verify API key and model availability
- Ensure stable network connection

### Zero Cache Hits
- Confirm using Kimi K2 model (supports caching)
- Check if context is actually stable
- Review logs for cache invalidation patterns

### Tool Execution Errors
- Verify root directory permissions
- Check file paths are within root directory
- Ensure files exist and are readable

## 📚 References

- [Kimi API Documentation](https://platform.moonshot.cn/docs/api-reference)
- [ReAct Pattern Paper](https://arxiv.org/abs/2210.03629)
- [Transformer KV Cache Explanation](https://huggingface.co/docs/transformers/kv_cache)

## 📄 License

This project is part of the AI Agent Book educational materials.
