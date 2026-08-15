# AWorld LLM Interface

A unified interface for interacting with various LLM providers through a consistent API.

## Features

- Unified API for multiple LLM providers. Currently, only OpenAI and Anthropic are supported.
- Synchronous and asynchronous calls with optional initialization control
- Streaming responses support
- Tool calls support
- Unified ModelResponse object for all provider responses
- Easy extension with custom providers

## Supported Providers

- `openai`: Models supporting OpenAI API protocol (OpenAI, compatible models)
- `anthropic`: Models supporting Anthropic API protocol (Claude models)
- `azure_openai`: Azure OpenAI service

## Basic Usage

### Quick Start

```python
from aworld.config.conf import AgentConfig
from aworld.models.llm import get_llm_model, call_llm_model, acall_llm_model

# Create configuration
config = AgentConfig(
    llm_provider="openai",  # Options: "openai", "anthropic", "azure_openai"
    llm_model_name="gpt-4o",
    llm_temperature=0.0,
    llm_api_key="your_api_key",
    llm_base_url="your_llm_server_address"
)

# Initialize the model
model = get_llm_model(config)

# Prepare messages
messages = [
    {"role": "system", "content": "You are a helpful AI assistant."},
    {"role": "user", "content": "Explain Python in three sentences."}
]

# Get response
response = model.completion(messages)
print(response.content)  # Access content directly from ModelResponse
```

### Using call_llm_model (Recommended)

```python
from aworld.models.llm import get_llm_model, call_llm_model

# Initialize model
model = get_llm_model(
    llm_provider="openai",
    model_name="gpt-4o",
    api_key="your_api_key",
    base_url="https://api.openai.com/v1"
)

# Prepare messages
messages = [
    {"role": "system", "content": "You are a helpful AI assistant."},
    {"role": "user", "content": "Write a short poem about programming."}
]

# Using call_llm_model - returns ModelResponse object
response = call_llm_model(model, messages)
print(response.content)  # Access content directly from ModelResponse

# Stream response with call_llm_model
for chunk in call_llm_model(model, messages, temperature=0.7, stream=True):
    if chunk.content:
        print(chunk.content, end="", flush=True)
```

### Asynchronous Calls with acall_llm_model

```python
import asyncio
from aworld.models.llm import get_llm_model, acall_llm_model

async def main():
    # Initialize model
    model = get_llm_model(
        llm_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        api_key="your_anthropic_api_key"
    )
    
    # Prepare messages
    messages = [
        {"role": "user", "content": "List 3 effective ways to learn programming."}
    ]
    
    # Async call with acall_llm_model
    response = await acall_llm_model(model, messages)
    print(response.content)
    
    # Async streaming with acall_llm_model
    print("\nStreaming response:")
    async for chunk in await acall_llm_model(model, messages, stream=True):
        if chunk.content:
            print(chunk.content, end="", flush=True)

# Run async function
asyncio.run(main())
```

### Selective Sync/Async Initialization

For performance optimization, you can control whether to initialize synchronous or asynchronous providers:
By default, both `sync_enabled` and `async_enabled` are set to `True`, which means both synchronous and asynchronous providers will be initialized.

```python
# Initialize only synchronous provider
model = get_llm_model(
    llm_provider="openai",
    model_name="gpt-4o",
    sync_enabled=True,    # Initialize sync provider
    async_enabled=False,  # Don't initialize async provider
    api_key="your_api_key"
)

# Initialize only asynchronous provider
model = get_llm_model(
    llm_provider="anthropic",
    model_name="claude-3-5-sonnet-20241022",
    sync_enabled=False,   # Don't initialize sync provider
    async_enabled=True,   # Initialize async provider
    api_key="your_api_key"
)

# Initialize both (default behavior)
model = get_llm_model(
    llm_provider="openai",
    model_name="gpt-4o",
    sync_enabled=True,
    async_enabled=True
)
```

### HTTP Client Mode

You can use direct HTTP requests instead of the SDK by specifying `client_type=ClientType.HTTP` parameter:

```python
from aworld.config.conf import AgentConfig, ClientType
from aworld.models.llm import get_llm_model, call_llm_model

# Initialize model with HTTP client mode
model = get_llm_model(
    llm_provider="openai",
    model_name="gpt-4o",
    api_key="your_api_key",
    base_url="https://api.openai.com/v1",
    client_type=ClientType.HTTP  # Use HTTP client instead of SDK
)

# Use it exactly the same way as SDK mode
messages = [
    {"role": "system", "content": "You are a helpful AI assistant."},
    {"role": "user", "content": "Tell me a short joke."}
]

# The model uses HTTP requests under the hood
response = call_llm_model(model, messages)
print(response.content)

# Streaming also works with HTTP client
for chunk in call_llm_model(model, messages, stream=True):
    if chunk.content:
        print(chunk.content, end="", flush=True)
```

This approach can be useful when:
- You need more control over the HTTP requests
- You have compatibility issues with the official SDK
- You're using a model that follows OpenAI API protocol but isn't fully compatible with the SDK

### Tool Calls Support

```python
from aworld.models.llm import get_llm_model, call_llm_model
import json

# Initialize model
model = get_llm_model(
    llm_provider="openai",
    model_name="gpt-4o",
    api_key="your_api_key"
)

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Prepare messages
messages = [
    {"role": "user", "content": "What's the weather like in San Francisco?"}
]

# Call model with tools
response = call_llm_model(model, messages, tools=tools, tool_choice="auto")

# Check for tool calls
if response.tool_calls:
    for tool_call in response.tool_calls:
        print(f"Tool name: {tool_call.name}")
        print(f"Arguments: {tool_call.arguments}")
        
        # Handle tool call
        if tool_call.name == "get_weather":
            # Parse arguments
            args = json.loads(tool_call.arguments)
            location = args.get("location")
            
            # Mock getting weather data
            weather = "Sunny, 25°C"
            
            # Add tool response to messages
            messages.append(response.message)  # Add assistant message
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.name,
                "content": f"{{\"weather\": \"{weather}\"}}"
            })
            
            # Call model again
            final_response = call_llm_model(model, messages)
            print("\nFinal response:", final_response.content)
else:
    print("\nResponse content:", response.content)
```

### Asynchronous Calls

```python
import asyncio
from aworld.models.llm import get_llm_model

async def main():
    # Initialize model
    model = get_llm_model(
        llm_provider="anthropic",
        model_name="claude-3-5-sonnet-20241022",
        temperature=0.0
    )
    
    # Prepare messages
    messages = [
        {"role": "user", "content": "Explain machine learning briefly."}
    ]
    
    # Async call
    response = await model.acompletion(messages)
    print(response.content)

# Run async function
asyncio.run(main())
```

### Streaming Responses

```python
# Synchronous streaming
for chunk in model.stream_completion(messages):
    print(chunk.content, end="", flush=True)
    
# Asynchronous streaming
async for chunk in model.astream_completion(messages):
    print(chunk.content, end="", flush=True)
```

## ModelResponse Object

All responses are encapsulated in a unified `ModelResponse` object with these key attributes:

- `id`: Response ID
- `model`: Model name used
- `content`: Generated text content
- `tool_calls`: List of tool calls (if any)
- `usage`: Token usage statistics
- `error`: Error message (if any)
- `message`: Complete message object for subsequent API calls

Example:
```python
response = call_llm_model(model, messages)
print(f"Content: {response.content}")
print(f"Model: {response.model}")
print(f"Total tokens: {response.usage['total_tokens']}")

# Get complete message for next call
messages.append(response.message)
```

## API Parameters

Essential parameters for model calls:

- `messages`: List of message dictionaries with `role` and `content` keys
- `temperature`: Controls response randomness (0.0-1.0)
- `max_tokens`: Maximum tokens to generate
- `stop`: List of stopping sequences
- `tools`: List of tool definitions
- `tool_choice`: Tool choice strategy

## Automatic Provider Detection

The system can automatically identify the provider based on model name or API endpoint:

```python
# Detect Anthropic based on model name
model = get_llm_model(model_name="claude-3-5-sonnet-20241022")

```

## Creating Custom Providers

Implement your own provider by extending `LLMProviderBase`:

```python
from aworld.models.llm import LLMProviderBase, register_llm_provider
from aworld.models.model_response import ModelResponse, ToolCall

class CustomProvider(LLMProviderBase):
    def _init_provider(self):
        # Initialize your API client
        return {
            "api_key": self.api_key,
            "endpoint": self.base_url
        }
    
    def _init_async_provider(self):
        # Initialize your asynchronous API client (optional)
        # If not implemented, async methods will raise NotImplementedError
        return None
    
    def preprocess_messages(self, messages):
        # Convert standard format to your API format
        return messages
    
    def postprocess_response(self, response):
        # Convert API response to ModelResponse
        return ModelResponse(
            id="response_id",
            model=self.model_name,
            content=response.get("text", ""),
            tool_calls=None  # Parse ToolCall objects if supported
        )
    
    def completion(self, messages, temperature=0.0, **kwargs):
        # Implement the actual API call
        processed = self.preprocess_messages(messages)
        # Call your API here...
        response = {"text": "Response from custom provider"}
        return self.postprocess_response(response)
    
    async def acompletion(self, messages, temperature=0.0, **kwargs):
        # Implement async API call
        # Similar to completion but asynchronous
        response = {"text": "Async response from custom provider"}
        return self.postprocess_response(response)

# Register your provider
register_llm_provider("custom_provider", CustomProvider)

# Use it like any other provider
model = get_llm_model(llm_provider="custom_provider", model_name="custom-model")
```

## API Key Management

Keys are retrieved in this order:
1. Direct `api_key` parameter
2. Environment variable in `.env` file
3. System environment variable

Example for OpenAI: `OPENAI_API_KEY` in parameters → `.env` → system env
