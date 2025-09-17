# System-Hint Agent Implementation Notes

## Comparison with Week1/Context Pattern

This project follows the same ReAct loop pattern as week1/context with the following enhancements:

### Similarities to Week1/Context:
1. **ReAct Loop**: Standard Reasoning + Acting pattern
2. **Command-Line Interface**: Uses argparse for CLI arguments
3. **Interactive Mode**: Default mode for user interaction
4. **Task Execution**: `execute_task()` method with max iterations
5. **Kimi K2 Model**: Uses the same LLM provider setup

### Key Enhancements:

#### 1. System Prompt Architecture
- **Week1/Context**: Basic system prompt with tool descriptions
- **System-Hint**: Enhanced system prompt with:
  - TODO list management rules
  - Error handling guidelines
  - Loop prevention strategies
  - Behavioral instructions

#### 2. Context Management
- **Week1/Context**: Manages conversation history with optional context modes
- **System-Hint**: Dynamic system hints that update after each interaction:
  - Current timestamp
  - System state (directory, OS, shell)
  - TODO list status
  - Tool call counters

#### 3. Tool Feedback
- **Week1/Context**: Standard tool results
- **System-Hint**: Enhanced tool results with:
  - Timestamps on each result
  - Call numbers (e.g., "Tool call #3")
  - Detailed error messages with suggestions
  - Execution duration tracking

#### 4. Task Management
- **Week1/Context**: Single-task execution
- **System-Hint**: Built-in TODO list system:
  - Automatic creation for complex tasks
  - Status tracking (pending, in_progress, completed, cancelled)
  - Persistent across conversation turns

## Sample Task

The default sample task demonstrates analyzing week1 and week2 projects, similar to the context project's financial analysis tasks but focused on code exploration:

```python
# Sample task that exercises multiple tools
task = """Analyze and summarize the AI Agent projects in week1 and week2 directories:
1. Navigate to the parent directory to access both week1 and week2 folders
2. For week1 directory:
   - List all project folders
   - Read key files from projects
   - Identify the key concepts
3. For week2 directory:
   - List all project folders  
   - Read README files
   - Understand advanced features
4. Create a comprehensive analysis file
"""
```

## Command-Line Usage

Following week1/context pattern with additional options:

```bash
# Interactive mode (default)
python main.py

# Single task execution (like week1/context)
python main.py --mode single --task "Your task here"

# Sample task (new)
python main.py --mode sample

# Feature flags (new)
python main.py --no-todo --no-timestamps --mode single --task "Simple task"
```

## Configuration Flexibility

Unlike week1/context which has fixed context modes, system-hint allows granular control:

```python
# Week1/Context approach
context_mode = ContextMode.FULL  # or NO_HISTORY, NO_REASONING, etc.

# System-Hint approach
config = SystemHintConfig(
    enable_timestamps=True,     # Toggle individually
    enable_tool_counter=True,
    enable_todo_list=True,
    enable_detailed_errors=True,
    enable_system_state=True
)
```

## Best Practices Demonstrated

1. **Prevent Infinite Loops**: Tool call counter shows "Tool call #N" to help agent recognize repetitive behavior
2. **Temporal Awareness**: Timestamps help agent understand event sequences
3. **Task Organization**: TODO lists for complex multi-step objectives
4. **Error Recovery**: Detailed error messages with actionable suggestions
5. **Context Preservation**: System state tracking across tool calls

## Testing

Similar to week1/context with additional component tests:

```bash
# Basic component tests
python test_basic.py

# Quick demonstration
python quickstart.py

# Full interactive testing
python main.py
```

## Key Learnings

1. **System hints significantly improve agent efficiency** - Agents complete tasks with fewer iterations
2. **TODO lists provide structure** - Complex tasks become manageable
3. **Tool counters prevent loops** - Agents recognize and avoid repetitive behavior
4. **Detailed errors enable recovery** - Agents can adapt strategies based on specific error information
5. **Timestamps provide context** - Useful for multi-session or long-running tasks

## Future Enhancements

Potential improvements building on this foundation:
- Memory persistence across sessions
- Collaborative TODO lists for multi-agent systems
- Adaptive hint generation based on task complexity
- Performance metrics tracking
- Integration with external task management systems
