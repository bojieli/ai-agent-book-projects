# Multi-Provider Support for User Memory System

The User Memory System now supports multiple LLM providers, allowing you to choose the best provider for your needs.

## Supported Providers

### 1. **Kimi/Moonshot** (Default)
- **Provider names**: `kimi` or `moonshot`
- **API Key**: `MOONSHOT_API_KEY`
- **Base URL**: `https://api.moonshot.cn/v1`
- **Default Model**: `kimi-k2-0905-preview`

### 2. **SiliconFlow**
- **Provider name**: `siliconflow`
- **API Key**: `SILICONFLOW_API_KEY`
- **Base URL**: `https://api.siliconflow.cn/v1`
- **Default Model**: `Qwen/Qwen3-235B-A22B-Thinking-2507`

### 3. **Doubao**
- **Provider name**: `doubao`
- **API Key**: `DOUBAO_API_KEY`
- **Base URL**: `https://ark.cn-beijing.volces.com/api/v3`
- **Default Model**: `doubao-seed-1-6-thinking-250715`

### 4. **OpenRouter**
- **Provider name**: `openrouter`
- **API Key**: `OPENROUTER_API_KEY`
- **Base URL**: `https://openrouter.ai/api/v1`
- **Default Model**: `google/gemini-2.5-pro`
- **Supported Models**:
  - `google/gemini-2.5-pro` - Google's Gemini 2.5 Pro model
  - `openai/gpt-5` - OpenAI's GPT-5 model
  - `anthropic/claude-sonnet-4` - Anthropic's Claude Sonnet 4 model

## Configuration

### Environment Variables

Set the appropriate API key for your chosen provider:

```bash
# For Kimi/Moonshot
export MOONSHOT_API_KEY="your-api-key-here"

# For SiliconFlow
export SILICONFLOW_API_KEY="your-api-key-here"

# For Doubao
export DOUBAO_API_KEY="your-api-key-here"

# For OpenRouter
export OPENROUTER_API_KEY="your-api-key-here"

# Set default provider (optional, defaults to 'kimi')
export PROVIDER="siliconflow"

# Override default model (optional)
export MODEL_NAME="your-custom-model-name"
```

### Command-Line Usage

```bash
# Use default provider (from env or 'kimi')
python main.py --mode interactive

# Specify provider
python main.py --provider siliconflow --mode interactive

# Specify provider and model
python main.py --provider doubao --model "doubao-seed-1-6-thinking-250715" --mode demo

# Full example with all options
python main.py \
    --provider siliconflow \
    --model "Qwen/Qwen3-235B-A22B-Thinking-2507" \
    --memory-mode enhanced_notes \
    --mode interactive \
    --user my_user

# Using OpenRouter with specific models
python main.py --provider openrouter --model "google/gemini-2.5-pro" --mode interactive
python main.py --provider openrouter --model "openai/gpt-5" --mode demo
python main.py --provider openrouter --model "anthropic/claude-sonnet-4" --mode evaluation
```

## Python API Usage

### UserMemoryAgent

```python
from agent import UserMemoryAgent, UserMemoryConfig
from config import MemoryMode

# Using SiliconFlow
agent = UserMemoryAgent(
    user_id="user123",
    provider="siliconflow",
    model="Qwen/Qwen3-235B-A22B-Thinking-2507",  # Optional, uses default if not specified
    config=UserMemoryConfig(memory_mode=MemoryMode.NOTES)
)

# Execute a task
result = agent.execute_task("Remember that I prefer Python for programming")
```

### ConversationalAgent

```python
from conversational_agent import ConversationalAgent, ConversationConfig

# Using Doubao
agent = ConversationalAgent(
    user_id="user456",
    provider="doubao",
    model="doubao-seed-1-6-thinking-250715",  # Optional
    config=ConversationConfig(enable_memory_context=True),
    memory_mode=MemoryMode.ENHANCED_NOTES
)

# Have a conversation
response = agent.chat("Hello, I'm John and I work at TechCorp")
```

### BackgroundMemoryProcessor

```python
from background_memory_processor import BackgroundMemoryProcessor, MemoryProcessorConfig

# Using Kimi (default)
processor = BackgroundMemoryProcessor(
    user_id="user789",
    provider="kimi",  # or "moonshot"
    config=MemoryProcessorConfig(
        conversation_interval=2,
        update_threshold=0.7
    ),
    memory_mode=MemoryMode.JSON_CARDS
)

# Using OpenRouter with specific model
processor = BackgroundMemoryProcessor(
    user_id="user_openrouter",
    provider="openrouter",
    model="google/gemini-2.5-pro",  # or "openai/gpt-5", "anthropic/claude-sonnet-4"
    config=MemoryProcessorConfig(
        conversation_interval=1,
        update_threshold=0.6
    ),
    memory_mode=MemoryMode.ENHANCED_NOTES
)

# Start background processing
processor.start_background_processing()
```

## Testing Providers

Run the test script to verify provider configuration:

```bash
python test_providers.py
```

This will test each configured provider and show which ones are properly set up.

## Provider Selection Guidelines

Choose your provider based on:

1. **Kimi/Moonshot**: Best for Chinese language support and general tasks
2. **SiliconFlow**: High-performance option with Qwen models
3. **Doubao**: ByteDance's offering with strong reasoning capabilities
4. **OpenRouter**: Access to multiple top-tier models including:
   - **Google Gemini 2.5 Pro**: Advanced multimodal understanding and reasoning
   - **OpenAI GPT-5**: Latest generation language model with superior capabilities
   - **Anthropic Claude Sonnet 4**: Strong reasoning with constitutional AI safety

## Troubleshooting

### API Key Not Found
If you see an error about missing API keys:
1. Check that the environment variable is set correctly
2. Verify the API key is valid
3. Ensure you're using the correct provider name

### Connection Errors
If you encounter connection issues:
1. Verify your network connection
2. Check if the provider's API endpoint is accessible
3. Ensure your API key has the necessary permissions

### Model Not Available
If a model is not available:
1. Check the provider's documentation for available models
2. Use the default model by not specifying the `--model` parameter
3. Update to a currently available model

## Adding New Providers

To add support for a new provider, update the following files:

1. **config.py**: Add API key and base URL configuration
2. **agent.py**: Add provider case in `__init__` method
3. **conversational_agent.py**: Add provider case in `__init__` method  
4. **background_memory_processor.py**: No changes needed (uses UserMemoryAgent)
5. **main.py**: Add provider to choices in argparse

Example for adding a new provider:

```python
# In agent.py __init__ method
elif self.provider == "new_provider":
    self.client = OpenAI(
        api_key=api_key,
        base_url="https://api.newprovider.com/v1"
    )
    self.model = model or "default-model-name"
elif self.provider == "openrouter":
    self.client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    self.model = model or "google/gemini-2.5-pro"
```
