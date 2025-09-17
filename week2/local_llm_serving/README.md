# Universal Tool Calling Demo

A cross-platform demonstration of LLM tool calling using standard OpenAI-compatible APIs. Works seamlessly on Windows, macOS, and Linux by automatically selecting the best backend for your system.

## 🌟 Features

- **Universal Compatibility**: Single entry point (`main.py`) that works on all platforms
- **Automatic Backend Selection**: 
  - Uses **vLLM** on Linux/Windows with NVIDIA GPU
  - Uses **Ollama** on macOS, Windows, or Linux without GPU
- **Standard Tool Calling**: Only uses OpenAI-compatible tool calling format
- **Built-in Tools**: Weather, calculator, time, and easy to add custom tools
- **Interactive & Example Modes**: Test with examples or chat interactively
- **🆕 Streaming Support**: Real-time display of thinking process, tool calls, and responses

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <repository>
cd projects/week2/chat_template

# 2. Install dependencies
pip install -r requirements.txt

# 3. Check your system compatibility
python check_compatibility.py

# 4. Run the main script (auto-detects best backend)
python main.py
```

That's it! The script automatically detects your platform and uses the appropriate backend.

## 📋 Prerequisites

### All Platforms
- Python 3.10+
- `pip install -r requirements.txt`

### Platform-Specific Setup

#### 🍎 macOS
```bash
# Install Ollama
brew install ollama

# Start Ollama service (in separate terminal)
ollama serve

# Download a model
ollama pull qwen3:0.6b
```

#### 🪟 Windows

**With NVIDIA GPU:**
- CUDA toolkit installed
- NVIDIA drivers 452.39+
- vLLM will be used automatically

**Without GPU:**
```bash
# Download and install Ollama
# From: https://ollama.com/download/windows

# Pull a model
ollama pull qwen3:0.6b
```

#### 🐧 Linux

**With NVIDIA GPU:**
- CUDA toolkit installed
- vLLM will be used automatically

**Without GPU:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start service
systemctl start ollama

# Pull a model
ollama pull qwen3:0.6b
```

## 🎮 Usage

### Basic Usage

```bash
# Run with auto-detection (recommended)
python main.py

# Run examples only
python main.py --mode examples

# Run interactive mode only
python main.py --mode interactive

# Force specific backend
python main.py --backend ollama  # Force Ollama
python main.py --backend vllm    # Force vLLM (requires GPU)

# Show system info
python main.py --info
```

### Using in Your Code

```python
from main import ToolCallingAgent

# Initialize (auto-detects best backend)
agent = ToolCallingAgent()

# Send a message
response = agent.chat("What's the weather in Tokyo?")
print(response)

# Disable tools for a query
response = agent.chat("Tell me a joke", use_tools=False)

# Reset conversation
agent.reset_conversation()
```

### Adding Custom Tools

```python
from tools import ToolRegistry

# Get the tool registry
registry = ToolRegistry()

# Define your tool function
def my_custom_tool(param1: str, param2: int) -> str:
    return f"Processed {param1} with {param2}"

# Register it
registry.register_tool(
    name="my_custom_tool",
    function=my_custom_tool,
    description="My custom tool description",
    parameters={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "First parameter"},
            "param2": {"type": "integer", "description": "Second parameter"}
        },
        "required": ["param1", "param2"]
    }
)
```

## 📁 Project Structure

```
chat_template/
├── main.py              # Main entry point (auto-detects backend)
├── agent.py             # vLLM agent implementation
├── ollama_native.py     # Ollama native tool calling
├── tools.py             # Tool implementations
├── config.py            # Configuration settings
├── server.py            # vLLM server manager
├── check_compatibility.py # System compatibility checker
├── requirements.txt     # Python dependencies
├── env.example         # Environment variables template
└── README.md           # This file
```

## 🛠️ Available Tools

1. **get_current_temperature**: Get real-time weather information using [Open-Meteo API](https://open-meteo.com/) (no API key required)
2. **get_current_time**: Get current time in different timezones
3. **convert_currency**: Convert between different currencies (simulated rates)
4. **parse_pdf**: Parse PDF documents from URL or local file
5. **code_interpreter**: Execute Python code for complex calculations and data processing

## 🎬 Streaming Mode

The agents now support streaming responses, which displays:
- 🧠 **Internal thinking** process (shown in gray)
- 🔧 **Tool calls** as they happen
- ✓ **Tool results** in real-time
- 📝 **Final response** streamed character by character

### Using Streaming

#### Interactive Mode (Default)
```bash
# Streaming is enabled by default
python main.py

# Disable streaming
python main.py --no-stream

# Toggle streaming during chat with /stream command
```

#### Programmatic Usage
```python
from main import ToolCallingAgent

# Initialize agent
agent = ToolCallingAgent()

# Stream response
for chunk in agent.chat("What's the weather in Tokyo?", stream=True):
    chunk_type = chunk.get("type")
    content = chunk.get("content", "")
    
    if chunk_type == "thinking":
        print(f"Thinking: {content}")
    elif chunk_type == "tool_call":
        print(f"Tool: {content['name']}")
    elif chunk_type == "tool_result":
        print(f"Result: {content}")
    elif chunk_type == "content":
        print(content, end="", flush=True)
```

### Test Streaming
```bash
# Run streaming demo
python demo_streaming.py

# Compare streaming vs regular mode
python test_streaming.py --mode compare
```

## 🔧 Configuration

Copy `env.example` to `.env` and customize:

```bash
# For vLLM (if you have GPU)
MODEL_NAME=Qwen/Qwen3-0.6B
VLLM_HOST=localhost
VLLM_PORT=8000

# Logging
LOG_LEVEL=INFO
```

## 📊 Tool Calling Format

This project uses **standard OpenAI-compatible tool calling**:

```json
{
  "tool_calls": [{
    "id": "call_123",
    "type": "function",
    "function": {
      "name": "get_weather",
      "arguments": {"location": "Tokyo"}
    }
  }]
}
```

No ad-hoc parsing or custom formats - just the standard that works across platforms.

## 🐛 Troubleshooting

### "Ollama not found"
- **Mac**: `brew install ollama && ollama serve`
- **Windows**: Download from [ollama.com](https://ollama.com/download/windows)
- **Linux**: `curl -fsSL https://ollama.com/install.sh | sh`

### "No models installed"
```bash
ollama pull qwen3:0.6b  # Default model used by this project
```

### "CUDA not available" (Linux/Windows)
- Install NVIDIA drivers and CUDA toolkit
- Or the script will automatically use Ollama instead

### Check System Compatibility
```bash
python check_compatibility.py
```

## 🤝 Supported Models

### Default Model:
- **Qwen3** (0.6B) - Default model used by this project. Small size with decent tool calling support.

### Other Compatible Models for Tool Calling:
- **Qwen3** (8B+) - Good tool support
- **Llama 3.1/3.2** (8B+) - Good tool support
- **Mistral Nemo** - Great tool calling

### For vLLM:
- Uses Qwen3-0.6B by default
- Any model supported by vLLM can be configured

## 📚 How It Works

1. **Platform Detection**: `main.py` detects your OS and GPU availability
2. **Backend Selection**: 
   - Has NVIDIA GPU? → Uses vLLM for best performance
   - No GPU or on Mac? → Uses Ollama for local inference
3. **Tool Execution**: Both backends use standard OpenAI tool calling format
4. **Response Generation**: Tools are executed and results fed back to the model

## 🔗 References

- [vLLM Documentation](https://docs.vllm.ai/)
- [Ollama Documentation](https://ollama.com/)
- [OpenAI Tool Calling](https://platform.openai.com/docs/guides/function-calling)

## 📄 License

This demo project is provided as-is for educational purposes.