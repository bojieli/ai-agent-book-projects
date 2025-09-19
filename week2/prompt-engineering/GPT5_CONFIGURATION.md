# GPT-5 Configuration Guide for tau-bench

## Overview
GPT-5 (via OpenRouter) uses internal "thinking" tokens similar to OpenAI's o1 models. This can result in high token usage if not properly configured.

## Key Configuration

### 1. Model and Provider
```python
model = "openai/gpt-5"
provider = "openrouter"  # Automatically set in our configuration
```

### 2. Minimize Thinking Tokens
Use `reasoning_effort` parameter via `extra_body`:

```python
from litellm import completion

response = completion(
    model="openai/gpt-5",
    custom_llm_provider="openrouter",
    messages=messages,
    temperature=1.0,  # GPT-5 only supports 1.0
    extra_body={"reasoning_effort": "low"}  # Critical for efficiency
)
```

### 3. Reasoning Effort Levels
- **"low"**: Minimal thinking tokens (~7-333 completion tokens)
- **"medium"**: Moderate thinking (~7-500 completion tokens)  
- **"high"**: Deep thinking (~71-1500+ completion tokens)
- **Not specified**: Defaults to variable, often high usage

## Token Usage Examples

| Task | Without reasoning_effort | With "low" | Savings |
|------|-------------------------|------------|---------|
| Simple greeting | 1358 tokens | 333 tokens | 75% |
| Math (2+2) | 7-71 tokens | 7 tokens | 90% |
| Complex reasoning | 2000+ tokens | 500-800 tokens | 60-75% |

## Implementation in tau-bench

The ablation agent now automatically sets `reasoning_effort="low"` for GPT-5:

```python
# In ablation_agent.py
if "gpt-5" in self.model:
    completion_kwargs["extra_body"] = {"reasoning_effort": "low"}
```

## Environment Variables

```bash
# Required for OpenRouter
export OPENROUTER_API_KEY="your_key"

# Optional debugging
export DEBUG_API_CALLS="true"  # Show API call details
export LITELLM_LOG="DEBUG"     # Show litellm internals
```

## Testing Tools

1. **Direct API test**: `python test_openrouter_direct.py`
2. **Reasoning comparison**: `python test_reasoning_effort.py`
3. **Single task debug**: `./test_single_task.sh`
4. **Full debug run**: `./debug_run.sh`

## Best Practices

1. **Always use `reasoning_effort="low"`** for tau-bench experiments unless you specifically need deep reasoning
2. **Monitor token usage** in the debug output to catch any issues
3. **Use temperature=1.0** (GPT-5 requirement)
4. **Batch similar tasks** to amortize thinking overhead

## Troubleshooting

If you see high token usage:
1. Check that `reasoning_effort="low"` is being passed
2. Verify it's in `extra_body` not as a direct parameter
3. Look for the "💭 Using reasoning_effort='low'" message in debug output
4. Consider the prompt complexity - very complex prompts may still use more tokens

## Cost Implications

With `reasoning_effort="low"`:
- ~75% reduction in token costs for typical tau-bench tasks
- Faster response times
- More consistent token usage across tasks
