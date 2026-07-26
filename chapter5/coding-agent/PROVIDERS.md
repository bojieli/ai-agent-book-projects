# Provider Configuration Guide

The Coding Agent supports three providers: Anthropic, OpenAI, and OpenRouter. Each has different API formats and model options.

## 🎯 Quick Setup

### Anthropic (Recommended)

```bash
# .env
PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
DEFAULT_MODEL=claude-sonnet-5
```

**Available Models:**
- `claude-sonnet-5` (Latest Sonnet 4, recommended)
- `claude-3-5-sonnet-20241022` (Sonnet 3.5)
- `claude-3-opus-20240229` (Opus 3)
- `claude-3-haiku-20240307` (Haiku 3, faster/cheaper)

**Get API Key:** https://console.anthropic.com/

### OpenRouter

```bash
# .env
PROVIDER=openrouter
OPENROUTER_API_KEY=your-openrouter-api-key
DEFAULT_MODEL=anthropic/claude-sonnet-4
```

**Available Models (examples):**
- `anthropic/claude-sonnet-4` (Claude Sonnet 4 via OpenRouter)
- `anthropic/claude-3.5-sonnet` (Claude 3.5 Sonnet)
- `openai/gpt-4-turbo` (GPT-4 Turbo)
- `google/gemini-pro-1.5` (Gemini Pro 1.5)
- `meta-llama/llama-3.1-70b-instruct` (Llama 3.1 70B)

**Get API Key:** https://openrouter.ai/

**Advantages:**
- Access multiple providers with one API key
- Automatic fallback to cheaper models
- Pay-as-you-go pricing
- No separate API keys needed for each provider

### OpenAI

```bash
# .env
PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
DEFAULT_MODEL=gpt-5.6-luna
```

**Available Models:**
- `gpt-5.6-sol` (flagship, strongest reasoning)
- `gpt-5.6-luna` (fast / cheaper, default)

**Get API Key:** https://platform.openai.com/

## 🔧 API Format Differences

The agent automatically handles the different API formats:

### Anthropic Format
- System prompt: Separate parameter
- Tool calling: `tool_use` content blocks
- Tool results: Nested in user messages
- Streaming: Content block deltas

### OpenAI/OpenRouter Format
- System prompt: First message with role="system"
- Tool calling: `function` calls
- Tool results: Separate messages with role="tool"
- Streaming: Choice deltas

**The agent handles this transparently!** You just set `PROVIDER` and it works.

## 📊 Feature Comparison

| Feature | Anthropic | OpenAI | OpenRouter |
|---------|-----------|--------|------------|
| Tool Calling | ✅ Excellent | ✅ Excellent | ✅ Excellent |
| Streaming | ✅ Content blocks | ✅ Deltas | ✅ Deltas |
| System Hints | ✅ Native | ✅ Via system msg | ✅ Via system msg |
| Cost | $$$ | $$$ | $ - $$$ |
| Model Options | Claude only | GPT only | All models |
| Rate Limits | Generous | Strict | Varies by model |

## 🎯 Which Provider to Choose?

### Choose Anthropic if:
- ✅ You want the best coding performance
- ✅ You need long context (200K tokens)
- ✅ You prefer Claude's reasoning style
- ✅ You want native tool calling support

### Choose OpenRouter if:
- ✅ You want to try multiple models
- ✅ You want flexible pricing
- ✅ You need access to open source models
- ✅ You want automatic fallbacks
- ✅ You don't want to manage multiple API keys

### Choose OpenAI if:
- ✅ You're already using GPT-4
- ✅ You need specific GPT models
- ✅ You have existing OpenAI credits

## 🔄 Switching Providers

Just change your `.env`:

```bash
# From Anthropic to OpenRouter
PROVIDER=openrouter  # Changed this line
OPENROUTER_API_KEY=your-openrouter-api-key  # Add this
DEFAULT_MODEL=anthropic/claude-sonnet-4  # Update model name
```

Then restart the agent - no code changes needed!

## 🧪 Testing Different Providers

You can test without modifying `.env`:

```python
from agent import CodingAgent

# Test Anthropic
agent1 = CodingAgent(
    api_key="your-anthropic-api-key",
    model="claude-sonnet-5",
    provider="anthropic"
)

# Test OpenRouter
agent2 = CodingAgent(
    api_key="your-openrouter-api-key",
    model="anthropic/claude-sonnet-4",
    base_url="https://openrouter.ai/api/v1",
    provider="openrouter"
)

# Test OpenAI
agent3 = CodingAgent(
    api_key="your-openai-api-key",
    model="gpt-4-turbo",
    provider="openai"
)
```

## ⚙️ Advanced Configuration

### OpenRouter-Specific Settings

OpenRouter supports additional headers for tracking:

```python
# In your code (not yet implemented):
headers = {
    "HTTP-Referer": "https://yourapp.com",
    "X-Title": "My Coding Agent"
}
```

### Model-Specific Parameters

Different models may support different parameters:

```python
# Anthropic: Use thinking mode
DEFAULT_MODEL=claude-sonnet-5

# OpenAI: Use newer models
DEFAULT_MODEL=gpt-5.6-luna-2024-04-09

# OpenRouter: Access any provider
DEFAULT_MODEL=google/gemini-pro-1.5
```

## 🐛 Troubleshooting

### "Invalid API key" with OpenRouter

Make sure you copied an OpenRouter API key from the OpenRouter dashboard:
```bash
OPENROUTER_API_KEY=your-openrouter-api-key
```

### "Model not found"

Check model name matches provider:
- Anthropic: Must start with `claude-`
- OpenAI: Must start with `gpt-` or `o1-`
- OpenRouter: Use `provider/model` format (e.g., `anthropic/claude-sonnet-4`)

### "Authentication error"

1. Check your API key is correct
2. Check it's set for the right provider
3. Verify the key hasn't expired
4. For OpenRouter, check you have credits

### Rate Limits

If you hit rate limits:
- **Anthropic**: Wait or upgrade tier
- **OpenAI**: Wait or use GPT-3.5-turbo
- **OpenRouter**: Switch to a different model

## 📈 Cost Optimization

### Use Cheaper Models

```bash
# Anthropic: Use Haiku for simple tasks
DEFAULT_MODEL=claude-3-haiku-20240307

# OpenAI: Use GPT-3.5
DEFAULT_MODEL=gpt-3.5-turbo

# OpenRouter: Use open source models
DEFAULT_MODEL=meta-llama/llama-3.1-70b-instruct
```

### Use OpenRouter for Cost Control

OpenRouter often has better pricing than direct API access:
- Automatic routing to cheapest provider
- No need for separate API keys
- Pay-as-you-go without minimums

## 🎓 Best Practices

1. **Start with Anthropic**: Best performance for coding tasks
2. **Use OpenRouter for experimentation**: Try different models easily
3. **Keep API keys secure**: Never commit `.env` to git
4. **Monitor usage**: Check your API dashboard regularly
5. **Set MAX_ITERATIONS**: Prevent runaway costs

## 📚 References

- Anthropic API Docs: https://docs.anthropic.com/
- OpenAI API Docs: https://platform.openai.com/docs/
- OpenRouter Docs: https://openrouter.ai/docs
