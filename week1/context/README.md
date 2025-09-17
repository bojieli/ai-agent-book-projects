# Context-Aware AI Agent with Ablation Studies

An advanced AI agent implementation supporting multiple LLM providers (SiliconFlow Qwen, ByteDance Doubao, and Moonshot Kimi), designed to demonstrate the critical importance of context components through systematic ablation studies.

## 🎯 Overview

This project implements a context-aware AI agent with multiple tools (PDF parsing, currency conversion, calculator, code interpreter) and provides comprehensive ablation testing to explore how different context components affect agent behavior and performance.

### Key Features

- **Multi-provider Support**: Works with SiliconFlow (Qwen), Doubao (ByteDance), and Kimi (Moonshot) LLMs
- **Multi-tool Agent**: PDF parsing, currency conversion, calculations, and Python code execution
- **Context Modes**: Five different context configurations for ablation studies
- **Interactive & Batch Modes**: Run single tasks or comprehensive test suites
- **Conversation History**: Maintains context across multiple queries in a session
- **Detailed Analytics**: Performance metrics, visualizations, and comprehensive reports

## 🤖 Supported LLM Providers

### Doubao (ByteDance) - Default
- **Model**: doubao-seed-1-6-thinking-250715 (customizable)
- **API**: OpenAI-compatible via Volcano Engine
- **Best for**: Advanced reasoning, faster responses, both English and Chinese tasks

### SiliconFlow
- **Model**: Qwen/Qwen3-235B-A22B-Thinking-2507 (customizable)
- **API**: OpenAI-compatible
- **Best for**: Complex reasoning tasks, detailed analysis

### Kimi (Moonshot AI)
- **Model**: kimi-k2-0905-preview (K2 model)
- **API**: OpenAI-compatible via Moonshot platform
- **Best for**: Advanced reasoning, multi-turn conversations, both English and Chinese tasks
- **Features**: Context caching for cost optimization

## 🏗️ Architecture

### Context Components

1. **Full Context** - Complete agent with all components
2. **No History** - Lacks historical tool call tracking
3. **No Reasoning** - Operates without strategic planning
4. **No Tool Calls** - Cannot execute external tools
5. **No Tool Results** - Blind to tool execution outcomes

### Available Tools

- **`parse_pdf(url)`** - Download and extract text from PDF documents
- **`convert_currency(amount, from, to)`** - Real-time currency conversion
- **`calculate(expression)`** - Simple mathematical expression evaluation
- **`code_interpreter(code)`** - Execute Python code for complex calculations, totals, and data processing

## 📋 Prerequisites

- Python 3.8+
- API key for one of the supported providers:
  - **SiliconFlow**: Get from [SiliconFlow](https://siliconflow.cn)
  - **Doubao (ByteDance)**: Get from [Volcano Engine](https://www.volcengine.com/)
  - **Kimi (Moonshot)**: Get from [Moonshot Platform](https://platform.moonshot.cn/)

## 📝 Sample Tasks

The system includes 5 pre-defined sample tasks demonstrating different capabilities:

1. **Simple Currency Conversion** - Basic multi-currency calculations
2. **Multi-Currency Budget Analysis** - Complex expense analysis across offices
3. **PDF Financial Analysis** - Parse and analyze financial documents
4. **Investment Growth Calculation** - Compound interest with currency conversion
5. **Comprehensive Financial Report** - Complete workflow using all tools

These samples are designed to showcase the agent's capabilities and the impact of context ablation.

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd projects/week1/context

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp env.example .env
# Edit .env and add your API key (SILICONFLOW_API_KEY or ARK_API_KEY)
```

### 2. Configure Provider

```bash
# For Doubao (ByteDance) - Default
export ARK_API_KEY=your_key_here  
python main.py  # Uses Doubao by default

# For SiliconFlow (Qwen)
export SILICONFLOW_API_KEY=your_key_here
python main.py --provider siliconflow

# For Kimi (Moonshot)
export MOONSHOT_API_KEY=your_key_here
python main.py --provider kimi

# Or specify a custom model
python main.py --model doubao-seed-1-6-thinking-250715
```

### 3. Testing Kimi Integration

```bash
# Quick test of Kimi K2 model
export MOONSHOT_API_KEY=your_key_here
python test_kimi.py

# Use Kimi in main script
python main.py --provider kimi --mode interactive

# Run ablation study with Kimi
python main.py --provider kimi --mode ablation
```

### 4. Run Interactive Mode (Recommended)

```bash
# Default (Doubao)
python main.py --mode interactive

# With SiliconFlow provider
python main.py --mode interactive --provider siliconflow

# In interactive mode, you can:
# - Type 'samples' to see pre-defined tasks
# - Type 'sample 3' to test PDF parsing
# - Type 'providers' to list available providers
# - Type 'provider kimi' to switch providers
# - Type 'status' to see current configuration
# - Type 'help' for all commands
```

### 5. Run Sample Tasks

```bash
# Run without arguments to select from samples
python main.py --mode single

# With specific provider
python main.py --mode single --provider doubao

# Or provide your own task
python main.py --mode single \
  --task "Convert $1000 USD to EUR, GBP, and JPY. Calculate the average." \
  --context-mode full \
  --provider siliconflow
```

### 6. Run Ablation Study

```bash
# With default provider
python main.py --mode ablation

# With Doubao provider
python main.py --mode ablation --provider doubao
```

## 🧪 Ablation Studies

The ablation studies systematically remove context components to understand their importance:

### Test Scenario

A complex financial analysis task requiring:
1. PDF document parsing
2. Multiple currency conversions
3. Mathematical calculations
4. Result aggregation

### Expected Behaviors

| Context Mode | Expected Behavior | Impact |
|-------------|-------------------|---------|
| **Full** | Complete successful execution | Baseline performance |
| **No History** | Redundant operations, inefficiency | May repeat tool calls |
| **No Reasoning** | Unstructured approach, potential errors | Lacks strategic planning |
| **No Tool Calls** | Complete failure | Cannot interact with external world |
| **No Tool Results** | Incorrect conclusions | Makes decisions without feedback |

### Running Tests

```bash
# Run full ablation study
python ablation_tests.py

# This will generate:
# - ablation_study_results.png (visualization)
# - ablation_study_report.md (detailed report)
# - ablation_results.json (raw data)
```

## 📊 Understanding Results

### Performance Metrics

- **Success Rate**: Whether the task was completed correctly
- **Execution Time**: Total time to complete the task
- **Iterations**: Number of agent-model interactions
- **Tool Calls**: Number of external tool invocations
- **Reasoning Steps**: Strategic planning iterations

### Sample Output

```
ABLATION STUDY RESULTS
================================================================================
| Test Name                      | Success | Time   | Iterations | Tool Calls |
|--------------------------------|---------|--------|------------|------------|
| Baseline - Full Context        | ✓       | 12.3s  | 5          | 8          |
| No Historical Tool Calls       | ✓       | 18.7s  | 8          | 12         |
| No Reasoning Process           | ✗       | 25.4s  | 10         | 15         |
| No Tool Call Commands          | ✗       | 3.2s   | 2          | 0          |
| No Tool Call Results           | ✗       | 15.6s  | 10         | 10         |
```

## 💡 Key Insights

### 1. Tool Calls Are Fundamental
Without tool call capability, the agent cannot interact with external systems, making task completion impossible.

### 2. Tool Results Provide Critical Feedback
Without seeing results, the agent operates blind, leading to incorrect conclusions and infinite loops.

### 3. Reasoning Enables Efficiency
Strategic planning reduces iterations and tool calls, improving both speed and accuracy.

### 4. History Prevents Redundancy
Historical context prevents repeated operations and maintains task coherence across iterations.

## 🛠️ Advanced Usage

### Interactive Mode Commands

The interactive mode supports the following commands:

| Command | Description |
|---------|-------------|
| `samples` | Display all available sample tasks |
| `sample <n>` | Run sample task number n |
| `providers` | List all available LLM providers |
| `provider <name>` | Switch to a different provider (e.g., `provider kimi`) |
| `modes` | List available context modes for ablation testing |
| `mode <name>` | Switch context mode (e.g., `mode no_history`) |
| `status` | Show current configuration (provider, model, mode, etc.) |
| `reset` | Reset agent trajectory (clear history) |
| `create_pdfs` | Generate sample PDF files for testing |
| `quit` | Exit interactive mode |

**Note:** The prompt shows the current provider in brackets, e.g., `[KIMI]>` or `[DOUBAO]>`

### Conversation History

The agent maintains conversation history throughout interactive sessions:

- **Persistent Context**: The agent remembers previous queries and responses within a session
- **Multi-turn Conversations**: You can reference information from earlier in the conversation
- **Tool Call Memory**: Previous tool executions are remembered and can be referenced
- **Reset on Demand**: Use the `reset` command to clear history and start fresh

Example conversation flow:
```
[DOUBAO]> Remember that our budget is $10,000. Calculate 15% of it.
# Agent calculates and remembers the budget

[DOUBAO]> Now convert that 15% amount to EUR
# Agent uses the previously calculated amount without re-asking

[DOUBAO]> What was our original budget?
# Agent recalls the $10,000 mentioned earlier
```

### Custom Tasks

Create your own test scenarios:

```python
from agent import ContextAwareAgent, ContextMode

agent = ContextAwareAgent(api_key, ContextMode.FULL)
result = agent.execute_task("""
    Download the PDF from https://example.com/report.pdf,
    extract all monetary values, convert them to EUR,
    and calculate the total.
""")
```

### Creating Test PDFs

Generate sample PDFs for testing:

```bash
python create_sample_pdf.py
# Creates test_pdfs/ directory with sample financial reports
```

### Configuration

Edit `config.py` or set environment variables:

```bash
export MODEL_TEMPERATURE=0.5
export MAX_ITERATIONS=15
export LOG_LEVEL=DEBUG
```

## 📁 Project Structure

```
context/
├── agent.py              # Core agent implementation
├── ablation_tests.py     # Ablation study test suite
├── main.py              # Entry point with CLI
├── config.py            # Configuration management
├── create_sample_pdf.py # PDF generation utility
├── requirements.txt     # Dependencies
├── env.example         # Environment template
└── README.md           # This file
```

## 🔬 Research Applications

This implementation is valuable for:

- **AI Safety Research**: Understanding failure modes
- **System Design**: Identifying critical components
- **Optimization**: Finding minimal viable configurations
- **Education**: Teaching agent architecture principles

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional tool implementations
- More sophisticated test scenarios  
- Alternative context ablation strategies
- Performance optimizations

## ⚠️ Limitations

- Currency rates are fixed (production should use real-time APIs)
- PDF parsing may fail on complex layouts
- Model token limits may affect very large documents

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- SiliconFlow for providing the Qwen model API
- OpenAI for the client library
- The AI agent research community

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Note**: This is an educational project demonstrating ablation studies in AI agents. For production use, implement proper error handling, rate limiting, and security measures.
