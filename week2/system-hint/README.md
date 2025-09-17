# System-Hint Enhanced AI Agent

An advanced AI agent that demonstrates the power of system hints for improving agent trajectory and preventing common issues like infinite loops, poor context awareness, and inefficient task management, with automatic trajectory saving for debugging.

## 🌟 Key Features

### 1. **Timestamp Tracking**
- Adds timestamps to user messages and tool call results
- Helps the agent understand temporal context
- Simulates time delays for realistic multi-day scenarios

### 2. **Tool Call Counter**
- Tracks how many times each tool has been called
- Prevents infinite loops and repetitive behavior
- Shows call number in tool responses (e.g., "Tool call #3 for 'read_file'")

### 3. **TODO List Management**
- Built-in task tracking system with management rules in system prompt
- Four states: pending, in_progress, completed, cancelled
- Persistent across conversation with rewrite and update capabilities
- Agent automatically creates TODO lists for complex tasks (3+ steps)
- Helps maintain focus and track progress systematically

### 4. **Detailed Error Messages**
- Provides comprehensive error information instead of generic messages
- Includes error type, arguments, traceback (in verbose mode)
- Offers suggestions for fixing common errors
- Helps agent learn from failures and adapt strategies

### 5. **System State Awareness**
- Tracks current directory, shell environment, and system information
- Updates dynamically as agent navigates filesystem
- Provides context for command execution

### 6. **Automatic Trajectory Saving**
- Saves full conversation history and state to `trajectory.json` after each iteration
- Captures complete debugging information even if execution fails
- Includes conversation history, tool calls, TODO lists, and configuration
- Provides `view_trajectory.py` utility for analyzing saved trajectories

## 🚀 Quick Start

### Installation

```bash
# Clone the repository (if not already done)
cd projects/week2/system-hint

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp env.example .env
# Edit .env with your KIMI_API_KEY
export KIMI_API_KEY='your-api-key-here'
```

### Basic Usage

```bash
# Interactive mode (default)
python main.py

# Run the sample task (analyze week1/week2 projects)
python main.py --mode sample

# Execute a single task from command line
python main.py --mode single --task "Create a hello world Python script"

# Run demonstrations
python main.py --mode demo --demo basic
python main.py --mode demo --demo loop
python main.py --mode demo --demo comparison

# Disable specific features
python main.py --no-todo --no-timestamps --task "Simple task"

# Quick start with sample task
python quickstart.py

# View saved trajectory after running any task
python view_trajectory.py

# View a specific trajectory file
python view_trajectory.py path/to/trajectory.json
```

### Programmatic Usage

```python
from agent import SystemHintAgent, SystemHintConfig

# Configure system hints
config = SystemHintConfig(
    enable_timestamps=True,
    enable_tool_counter=True,
    enable_todo_list=True,
    enable_detailed_errors=True,
    enable_system_state=True,
    save_trajectory=True,
    trajectory_file="my_trajectory.json"
)

# Create agent
agent = SystemHintAgent(
    api_key="your-api-key",
    provider="kimi",
    config=config,
    verbose=False
)

# Execute task
task = "Create a Python script that analyzes CSV files"
result = agent.execute_task(task, max_iterations=20)

print(f"Success: {result['success']}")
print(f"Final answer: {result['final_answer']}")
print(f"Trajectory saved to: {result['trajectory_file']}")
```

## 📂 Project Structure

```
system-hint/
├── agent.py          # Main agent implementation with system hints
├── main.py           # CLI interface with multiple modes
├── config.py         # Configuration management
├── quickstart.py     # Quick demo script
├── test_basic.py     # Basic tests
├── view_trajectory.py # Trajectory viewing utility
├── requirements.txt  # Python dependencies
├── env.example       # Environment variable template
├── trajectory.json   # Auto-saved trajectory (created at runtime)
└── README.md        # This file
```

## 🔬 How System Hints Work

### System Hint Architecture

System hints are contextual information added to the conversation **as temporary user messages** before sending to the LLM. They are NOT stored in the conversation history, preventing context pollution while providing crucial state information.

```python
# System hint example (added as user message before LLM call):
=== SYSTEM STATE ===
Current Time: 2024-12-13 10:30:45
Current Directory: /home/user/projects
System: Linux (5.15.0)
Shell Environment: Linux Shell (bash)
Python Version: 3.10.0

=== CURRENT TASKS ===
TODO List:
  [1] 🔄 Read configuration file (in_progress)
  [2] ⏳ Process data (pending)
  [3] ✅ Initialize environment (completed)
```

### Management Rules in System Prompt

The system prompt includes explicit rules for TODO management, error handling, and tool usage patterns that guide the agent's behavior:

- Automatic TODO list creation for complex tasks
- Status management (only one in_progress at a time)
- Tool call awareness (check call numbers)
- Error recovery strategies

## 🛠 Configuration Options

### SystemHintConfig Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `enable_timestamps` | `True` | Add timestamps to messages |
| `enable_tool_counter` | `True` | Track tool call counts |
| `enable_todo_list` | `True` | Enable TODO list management |
| `enable_detailed_errors` | `True` | Provide detailed error information |
| `enable_system_state` | `True` | Track system state |
| `timestamp_format` | `"%Y-%m-%d %H:%M:%S"` | Timestamp format string |
| `simulate_time_delay` | `False` | Simulate time passing (demo) |
| `save_trajectory` | `True` | Save trajectory to file |
| `trajectory_file` | `"trajectory.json"` | Trajectory output file |

## 🔍 Demonstrations

### 1. Basic Features Demo

Shows all system hints working together:
```bash
python main.py --mode demo --demo basic
```

### 2. Loop Prevention Demo

Demonstrates how tool call counting prevents infinite loops:
```bash
python main.py --mode demo --demo loop
```

### 3. Comparison Demo

Shows the difference between with and without system hints:
```bash
python main.py --mode demo --demo comparison
```

## 🎯 Sample Tasks

The agent includes several pre-configured sample tasks:

1. **Project Analysis** - Analyze week1/week2 AI agent projects
2. **File Operations** - Create, read, and modify files
3. **Code Generation** - Generate Python scripts with specific functionality
4. **System Commands** - Execute shell commands and process results

## 📊 Analyzing Results

### Viewing Trajectories

After running any task, use the trajectory viewer:

```bash
python view_trajectory.py

# Output shows:
# - Total iterations
# - Tool usage statistics
# - TODO list progress
# - Conversation highlights
# - Configuration used
```

### Performance Metrics

The agent tracks:
- Number of iterations needed
- Tool calls made (with success/failure rates)
- TODO completion status
- Time taken (when timestamps enabled)
- Final success/failure state

## 🧪 Testing

```bash
# Run basic tests
python test_basic.py

# Test specific configurations
python -c "
from agent import SystemHintAgent, SystemHintConfig
config = SystemHintConfig(enable_todo_list=False)
agent = SystemHintAgent('api_key', config=config)
# Test without TODO lists
"
```

## 🔧 Troubleshooting

### Common Issues

1. **API Key Not Set**
   ```bash
   export KIMI_API_KEY='your-api-key-here'
   ```

2. **Tool Call Loops**
   - Enable tool counter: `enable_tool_counter=True`
   - Check tool call numbers in output

3. **Lost Context**
   - Enable timestamps: `enable_timestamps=True`
   - Enable system state: `enable_system_state=True`

4. **Task Management Issues**
   - Enable TODO list: `enable_todo_list=True`
   - Agent will automatically organize complex tasks

## 📝 Notes

- System hints are added as temporary user messages, not stored in history
- Trajectory files capture complete execution state for debugging
- TODO lists help agents maintain focus on multi-step tasks
- Tool call counters prevent infinite loops automatically
- Detailed errors with suggestions help agents self-correct

## 🤝 Contributing

Feel free to enhance the system hint features:
- Add new hint types
- Improve error suggestions
- Enhance TODO management rules
- Add visualization tools for trajectories

## 📄 License

MIT License - See LICENSE file for details
