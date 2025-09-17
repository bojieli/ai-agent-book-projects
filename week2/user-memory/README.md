# User Memory System - Advanced Conversational Memory Management

A sophisticated user memory system featuring separated architecture for conversation and memory processing, with support for multiple LLM providers and memory storage modes. Built with React pattern and tool-based approach following best practices for production AI agents.

## 🌟 Key Features

- **Separated Architecture**: Decoupled conversational agent and background memory processor
- **Multiple Memory Modes**: From simple notes to advanced JSON cards with complete context
- **Multi-Provider Support**: Kimi/Moonshot, SiliconFlow, Doubao, OpenRouter (with Gemini 2.5 Pro, GPT-5, Claude Sonnet 4)
- **React Pattern**: Tool-based approach for structured memory operations
- **Streaming Support**: Real-time response streaming with tool call integration
- **Evaluation Framework**: Integration with user-memory-evaluation for systematic testing
- **Background Processing**: Automatic memory updates based on conversation intervals
- **Persistent Storage**: JSON-based storage with conversation history tracking

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Memory Modes](#memory-modes)
- [Execution Modes](#execution-modes)
- [Provider Configuration](#provider-configuration)
- [API Usage](#api-usage)
- [Evaluation Framework](#evaluation-framework)
- [Advanced Configuration](#advanced-configuration)
- [Project Structure](#project-structure)

## 🚀 Installation

### Prerequisites

- Python 3.8+
- API key for at least one supported LLM provider

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd projects/week2/user-memory
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp env.example .env
# Edit .env with your API keys
```

4. Set up your API key (choose one):
```bash
# For Kimi/Moonshot (default)
export MOONSHOT_API_KEY="your-api-key-here"

# For SiliconFlow
export SILICONFLOW_API_KEY="your-api-key-here"

# For Doubao
export DOUBAO_API_KEY="your-api-key-here"

# For OpenRouter
export OPENROUTER_API_KEY="your-api-key-here"
```

## 🎯 Quick Start

### Quickstart Demo
```bash
python quickstart.py
```

This runs a demonstration showing:
- Separated conversation and memory processing
- Memory operations after each conversation
- Memory persistence across sessions

### Interactive Mode
```bash
python main.py --mode interactive --user your_name
```

Commands available in interactive mode:
- `memory` - Show current memory state
- `process` - Manually trigger memory processing
- `save` - Save memory immediately
- `reset` - Start new conversation session
- `quit`/`exit` - Exit without saving

### Demo Mode
```bash
python main.py --mode demo --memory-mode enhanced_notes
```

### Evaluation Mode
```bash
python main.py --mode evaluation --memory-mode advanced_json_cards
```

## 🏗️ Architecture Overview

The system uses a **separated architecture** design:

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                        │
└────────────────────┬───────────────────────┬─────────────┘
                     │                       │
        ┌────────────▼─────────┐  ┌─────────▼──────────┐
        │ Conversational Agent │  │ Background Memory   │
        │                      │  │ Processor          │
        │ • Handles dialogue   │  │ • Analyzes context │
        │ • Reads memory       │  │ • Updates memory   │
        │ • Streams responses  │  │ • Tool-based ops   │
        └────────────┬─────────┘  └─────────┬──────────┘
                     │                       │
        ┌────────────▼───────────────────────▼──────────┐
        │              Memory Manager                   │
        │         (Notes/JSON Cards Storage)           │
        └───────────────────────────────────────────────┘
```

### Core Components

1. **ConversationalAgent** (`conversational_agent.py`)
   - Pure conversation handling
   - Memory context integration
   - Response streaming
   - No direct memory updates

2. **BackgroundMemoryProcessor** (`background_memory_processor.py`)
   - Analyzes conversation context
   - Determines memory updates
   - Uses UserMemoryAgent with tools
   - Configurable processing intervals

3. **UserMemoryAgent** (`agent.py`)
   - React pattern implementation
   - Tool-based memory operations
   - Streaming with tool calls
   - Trajectory logging

4. **MemoryManager** (`memory_manager.py`)
   - Multiple storage backends
   - CRUD operations
   - Search capabilities
   - Persistence handling

## 💾 Memory Modes

### 1. Simple Notes (`notes`)
Basic fact and preference storage:
```
- User email: john@example.com
- Favorite color: blue
- Works at: TechCorp
```

### 2. Enhanced Notes (`enhanced_notes`)
Comprehensive contextual paragraphs:
```
User works at TechCorp as a senior software engineer, specializing in 
machine learning for the past 3 years. They lead a team of 5 developers
and are passionate about open source contributions.
```

### 3. JSON Cards (`json_cards`)
Hierarchical structured storage:
```json
{
  "personal": {
    "contact": {
      "email": {
        "value": "john@example.com",
        "updated_at": "2024-01-15T10:30:00"
      }
    }
  }
}
```

### 4. Advanced JSON Cards (`advanced_json_cards`)
Complete memory card objects with metadata:
```json
{
  "medical": {
    "doctor_primary": {
      "backstory": "User shared their primary care physician details during health discussion",
      "date_created": "2024-01-15 10:30:00",
      "person": "John Smith (primary)",
      "relationship": "primary account holder",
      "doctor_name": "Dr. Sarah Johnson",
      "specialty": "Internal Medicine",
      "clinic": "City Medical Center"
    }
  }
}
```

## 🎮 Execution Modes

### Interactive Mode
Real-time conversation with automatic memory processing:
```bash
python main.py --mode interactive \
    --user john_doe \
    --memory-mode enhanced_notes \
    --conversation-interval 2  # Process every 2 conversations
```

### Demo Mode
Structured demonstration of memory system capabilities:
```bash
python main.py --mode demo \
    --provider siliconflow \
    --memory-mode json_cards
```

### Evaluation Mode
Test case-based evaluation with scoring:
```bash
python main.py --mode evaluation \
    --memory-mode advanced_json_cards \
    --provider kimi
```

## 🔌 Provider Configuration

### Supported Providers

| Provider | Models | Best For |
|----------|--------|----------|
| **Kimi/Moonshot** | kimi-k2-0905-preview | Chinese language, general tasks |
| **SiliconFlow** | Qwen3-235B-A22B-Thinking | High performance, reasoning |
| **Doubao** | doubao-seed-1-6-thinking | ByteDance ecosystem, reasoning |
| **OpenRouter** | Gemini 2.5 Pro, GPT-5, Claude Sonnet 4 | Multiple top-tier models |

### Configuration Examples

```bash
# Using SiliconFlow
python main.py --provider siliconflow --model "Qwen/Qwen3-235B-A22B-Thinking-2507"

# Using OpenRouter with Gemini
python main.py --provider openrouter --model "google/gemini-2.5-pro"

# Using Doubao
python main.py --provider doubao --model "doubao-seed-1-6-thinking-250715"
```

## 📚 API Usage

### Basic Conversation
```python
from conversational_agent import ConversationalAgent, ConversationConfig
from config import MemoryMode

# Initialize agent
agent = ConversationalAgent(
    user_id="user123",
    provider="kimi",
    config=ConversationConfig(
        enable_memory_context=True,
        temperature=0.7
    ),
    memory_mode=MemoryMode.ENHANCED_NOTES
)

# Have conversation
response = agent.chat("Hi, I'm Alice and I work at TechCorp")
print(response)
```

### Background Memory Processing
```python
from background_memory_processor import BackgroundMemoryProcessor, MemoryProcessorConfig

# Initialize processor
processor = BackgroundMemoryProcessor(
    user_id="user123",
    provider="kimi",
    config=MemoryProcessorConfig(
        conversation_interval=2,  # Process every 2 conversations
        enable_auto_processing=True
    ),
    memory_mode=MemoryMode.JSON_CARDS
)

# Start background processing
processor.start_background_processing()

# Manual processing
results = processor.process_recent_conversations()
```

### Tool-Based Memory Updates
```python
from agent import UserMemoryAgent, UserMemoryConfig

# Initialize agent with tools
agent = UserMemoryAgent(
    user_id="user123",
    provider="siliconflow",
    config=UserMemoryConfig(
        enable_memory_updates=True,
        memory_mode=MemoryMode.ADVANCED_JSON_CARDS
    )
)

# Execute task with tool calls
result = agent.execute_task(
    "Remember that I prefer Python and my email is john@example.com"
)

# Access tool call history
for call in result['tool_calls']:
    print(f"Tool: {call.tool_name}")
    print(f"Args: {call.arguments}")
    print(f"Result: {call.result}")
```

## 🧪 Evaluation Framework

The system integrates with `user-memory-evaluation` for systematic testing:

```bash
# Run evaluation with test cases
python main.py --mode evaluation --memory-mode advanced_json_cards

# In evaluation mode:
# 1. Select test case ID
# 2. System processes conversation histories
# 3. Generates response to user question
# 4. Receives evaluation score and feedback
```

### Test Case Structure
- Conversation histories for context building
- User questions to test memory recall
- Automatic scoring and feedback
- Support for 60+ predefined test cases

## ⚙️ Advanced Configuration

### Environment Variables
```bash
# Provider Selection
PROVIDER=kimi  # or siliconflow, doubao, openrouter

# Model Configuration
MODEL_TEMPERATURE=0.3
MODEL_MAX_TOKENS=4096

# Memory Settings
MEMORY_MODE=enhanced_notes
MAX_MEMORY_ITEMS=100
MEMORY_UPDATE_TEMPERATURE=0.2

# Processing Configuration
SESSION_TIMEOUT=3600
MAX_CONTEXT_LENGTH=8000

# Storage Paths
MEMORY_STORAGE_DIR=data/memories
CONVERSATION_HISTORY_DIR=data/conversations
```

### Command-Line Options
```bash
python main.py \
    --mode interactive \
    --user custom_user \
    --memory-mode advanced_json_cards \
    --provider openrouter \
    --model "google/gemini-2.5-pro" \
    --conversation-interval 3 \
    --background-processing True \
    --no-verbose
```

## 📁 Project Structure

```
user-memory/
├── main.py                          # Main entry point with all modes
├── quickstart.py                    # Quick demonstration script
├── agent.py                         # UserMemoryAgent with React pattern
├── conversational_agent.py         # Pure conversation handler
├── background_memory_processor.py  # Background memory processing
├── memory_manager.py               # Memory storage backends
├── config.py                       # Configuration and settings
├── conversation_history.py         # Conversation tracking
├── memory_operation_formatter.py   # Operation display utilities
├── run_evaluation.py              # Evaluation runner
├── locomo_benchmark.py            # LOCOMO benchmark integration
├── PROVIDERS.md                   # Provider documentation
├── requirements.txt               # Python dependencies
├── env.example                    # Environment template
├── data/                         # Data storage
│   ├── memories/                 # User memory files
│   └── conversations/            # Conversation histories
└── logs/                         # Application logs
```

## 🔧 Development

### Running Tests
```bash
# Test specific components
python test_agent.py
python test_streaming.py
python test_providers.py
```

### Adding New Providers
1. Update `config.py` with API key configuration
2. Add provider case in `agent.py` and `conversational_agent.py`
3. Update command-line choices in `main.py`
4. Add to `PROVIDERS.md` documentation

### Custom Memory Modes
1. Extend `BaseMemoryManager` in `memory_manager.py`
2. Implement required methods (CRUD operations)
3. Add to `MemoryMode` enum in `config.py`
4. Update mode handling in agents

## 📝 Notes

- Memory processing occurs asynchronously in background
- Tool calls are logged for debugging and evaluation
- Streaming is supported with real-time tool execution
- Memory state persists across sessions
- Supports both programmatic and interactive usage

## 📄 License

[Your License Here]

## 🤝 Contributing

[Contributing Guidelines]

## 📮 Support

[Support Information]
