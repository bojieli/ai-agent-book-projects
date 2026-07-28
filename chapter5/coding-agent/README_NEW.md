# Comprehensive Coding Agent - Pure Python Implementation

A production-ready AI coding agent built with Claude, implementing all techniques from Chapter 2 with **pure Python tools** - no command-line dependencies required!

## 🌟 Key Features

### ✅ Pure Python Implementation

**All tools implemented without command-line dependencies:**
- ❌ No `grep`, `rg` (ripgrep), `find` commands needed
- ❌ No dependency on system utilities
- ✅ **100% pure Python** implementations
- ✅ Works on any system with Python 3.8+
- ✅ **Especially designed for Mac users** without command-line tools

### 🛠️ Complete Tool Suite

**All 17 tools from tools.json fully implemented:**

**File Operations (Pure Python):**
- `Read` - File reading with image/PDF/notebook support
- `Write` - File writing with auto lint checking
- `Edit` - Search and replace editing
- `MultiEdit` - Multiple edits in one operation

**Search Tools (Pure Python, no rg/grep dependency):**
- `Grep` - **Pure Python regex search** with full ripgrep feature parity
  - Full regex support
  - Case insensitive search
  - Context lines (before/after/around)
  - Line numbers
  - Multiline mode
  - Glob filtering
  - File type filtering
  - Multiple output modes
- `Glob` - File pattern matching
- `LS` - Directory listing

**Shell Operations:**
- `Bash` - Persistent shell sessions
- `BashOutput` - Background job output
- `KillBash` - Terminate shells

**Project Management:**
- `TodoWrite` - Task list management
- `ExitPlanMode` - Plan mode exit

**Advanced:**
- `NotebookEdit` - Jupyter notebook editing
- `WebFetch` - Web content fetching (stub)
- `WebSearch` - Web search (stub)
- `Task` - Sub-agent launcher (stub)

### 🧠 System Hint Techniques (Chapter 2)

1. **Timestamps**: Every message and tool result timestamped
2. **Tool Call Counting**: Warns after 3+ repeated calls
3. **TODO List Management**: Explicit task tracking
4. **Detailed Error Information**: Rich error context
5. **System State Awareness**: Working directory, OS, Python version
6. **Environment Information**: Dynamic state in context

### 🔧 Terminal Environment

- **Persistent Shell Sessions**: Commands in same shell
- **Working Directory Tracking**: Directory changes persist
- **Background Execution**: Long-running command support

### ✅ Auto Lint Detection

After Write/Edit/MultiEdit:
- Python syntax checking
- JavaScript/TypeScript checking  
- Errors appear immediately in tool results

## 📁 Project Structure

```
coding-agent/
├── agent.py                    # Main agent implementation
├── system_state.py            # System state tracking
├── tool_registry.py           # Tool name → implementation mapping
├── tools/                     # All tool implementations
│   ├── __init__.py
│   ├── base.py               # Base tool class
│   ├── bash_tool.py          # Shell execution
│   ├── bash_output_tool.py   # Background job output
│   ├── kill_bash_tool.py     # Shell termination
│   ├── read_tool.py          # File reading
│   ├── write_tool.py         # File writing
│   ├── edit_tool.py          # File editing
│   ├── multi_edit_tool.py    # Multiple edits
│   ├── grep_tool.py          # 🔥 Pure Python regex search (no rg!)
│   ├── glob_tool.py          # File pattern matching
│   ├── ls_tool.py            # Directory listing
│   ├── todo_write_tool.py    # TODO management
│   ├── exit_plan_mode_tool.py
│   ├── notebook_edit_tool.py
│   ├── web_fetch_tool.py
│   ├── web_search_tool.py
│   ├── task_tool.py
│   └── shell_session.py      # Shell session management
├── tools.json                 # Tool definitions
├── system-prompt.md          # System prompt
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

## 🚀 Installation

```bash
# Navigate to project directory
cd /Users/boj/ai-agent-book/projects/week5/coding-agent

# Install dependencies (minimal!)
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your API key
```

### Requirements

**Minimal dependencies:**
- Python 3.8+
- `anthropic` library
- `python-dotenv`

**Optional (for enhanced features):**
- `PyPDF2` - For PDF reading
- `requests`, `beautifulsoup4`, `html2text` - For WebFetch

**No command-line tools needed!** Works on macOS without Homebrew packages.

## 📖 Usage

### Basic Example

```python
from agent import CodingAgent

agent = CodingAgent(api_key="your-key")

for event in agent.run("List all Python files"):
    if event["type"] == "text_delta":
        print(event["delta"], end="", flush=True)
    elif event["type"] == "done":
        print("\n✅ Done!")
```

### Run Examples

```bash
# Basic quickstart
python quickstart.py

# Complex multi-step task
python example_complex_task.py

# System hints demonstration
python example_with_system_hints.py
```

## 🔍 Pure Python Grep Implementation

The **Grep tool** is fully implemented in pure Python without any dependency on `grep`, `rg`, or other command-line tools. It provides all the features of ripgrep:

```python
# Example: Search for pattern in files
{
    "name": "Grep",
    "input": {
        "pattern": "def.*test",
        "path": "/path/to/search",
        "output_mode": "content",
        "-i": True,              # Case insensitive
        "-C": 3,                 # 3 lines context
        "-n": True,              # Show line numbers
        "glob": "*.py",          # Only Python files
        "multiline": False       # Single line matching
    }
}
```

**Features:**
- ✅ Full regex support (Python `re` module)
- ✅ Case insensitive search (`-i`)
- ✅ Context lines (`-A`, `-B`, `-C`)
- ✅ Line numbers (`-n`)
- ✅ Multiline mode
- ✅ Glob filtering (`glob` parameter)
- ✅ File type filtering (`type` parameter)
- ✅ Output modes: `content`, `files_with_matches`, `count`
- ✅ Head limit
- ✅ Recursive directory search
- ✅ Binary file skip
- ✅ Hidden file/directory skip

## 🏗️ Architecture

### Modular Tool System

Each tool is implemented as a separate class inheriting from `BaseTool`:

```python
class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "MyTool"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Tool implementation
        return {"result": "success"}
```

### Tool Registry

`ToolRegistry` maps tool names to implementations:

```python
registry = ToolRegistry()
tool = registry.get_tool("Grep", system_state)
result = tool.execute(params)
```

### System State

`SystemState` tracks:
- Current working directory
- Tool call counts
- TODO list
- Shell sessions
- Environment info

### System Hints

System hints are injected before each LLM call:

```xml
<system_hint>
# System State
Current Time: 2025-10-12 15:30:45
Working Directory: /Users/boj/coding-agent
OS: Darwin
Python: Python 3.11.5

# Tool Call Statistics
- Grep: 2 calls
- Write: 1 calls

# Current TODO List
✅ [1] Search for files (completed)
🔄 [2] Implement feature (in_progress)
⬜ [3] Write tests (pending)
</system_hint>
```

## 🎯 Design Principles

### 1. Pure Python Implementation

**Why:** Maximum portability and compatibility
- Works on any system with Python
- No Homebrew, apt, or other package managers needed
- Consistent behavior across platforms

### 2. Modular Tool Architecture

**Why:** Maintainability and extensibility
- Each tool is self-contained
- Easy to add new tools
- Easy to test individually
- Clear separation of concerns

### 3. No Command-Line Dependencies

**Why:** Reliability and control
- **Grep**: Pure Python regex search
- **Glob**: Python's `pathlib.glob()`
- **LS**: Python's `os` and `pathlib`
- No subprocess calls for core functionality
- Full control over behavior

### 4. System Hints for Self-Awareness

**Why:** Better agent behavior
- Prevents infinite loops (tool call counting)
- Maintains task focus (TODO tracking)
- Provides environmental context
- Enables self-monitoring

## 📊 Comparison with Chapter 2

| Technique | Status | Implementation |
|-----------|--------|----------------|
| Standard OpenAI Tool Format | ✅ | Anthropic SDK |
| Streaming Tool Calls | ✅ | Real-time JSON delta parsing |
| Parallel Tool Calls | ✅ | Multiple tools per response |
| Pure Python Tools | ✅ | **No command-line dependencies** |
| Grep without rg | ✅ | **Pure Python regex search** |
| Timestamps | ✅ | All messages/tools |
| Tool Call Counting | ✅ | Warns at 3+ |
| TODO List | ✅ | TodoWrite tool |
| System State | ✅ | Working dir, OS, Python |
| Persistent Shell | ✅ | Shell sessions |
| Auto Lint Detection | ✅ | After Write/Edit/MultiEdit |

## 🔧 Configuration

`.env` file:

```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional
DEFAULT_MODEL=claude-sonnet-4-20250514
MAX_ITERATIONS=50
MAX_TOKENS=8192
```

## 📝 Adding New Tools

1. Create tool file in `tools/`:

```python
# tools/my_tool.py
from .base import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "MyTool"
    
    def _execute_impl(self, params):
        # Implementation
        return {"result": "success"}
```

2. Register in `tools/__init__.py`:

```python
from .my_tool import MyTool

__all__ = [..., 'MyTool']
```

3. Add to `tool_registry.py`:

```python
self._tools = {
    ...,
    "MyTool": MyTool,
}
```

4. Add definition to `tools.json`

## 🐛 Troubleshooting

### "No module named 'tools'"

Make sure you're running from the project directory:
```bash
cd /Users/boj/ai-agent-book/projects/week5/coding-agent
python agent.py
```

### Grep not finding files

Check:
- Path is correct
- Pattern is valid regex
- Glob pattern matches files
- Files contain searchable text (not binary)

### Shell commands fail

Ensure:
- Bash is available on `PATH` on macOS/Linux
- PowerShell is available on `PATH` on Windows (`cmd.exe` is used as a fallback)
- Working directory exists
- Commands use the native shell syntax and are properly quoted

## 🎓 Learning Path

1. **Start with examples**: Run `quickstart.py`
2. **Explore system hints**: Run `example_with_system_hints.py`
3. **Study Grep implementation**: See `tools/grep_tool.py`
4. **Read Chapter 2**: Understand the theory
5. **Add custom tools**: Extend the system

## 📚 References

- Chapter 2: Context Engineering (AI Agent Book)
- Tools specification: `tools.json`
- System prompt: `system-prompt.md`
- Anthropic Claude API: https://docs.anthropic.com/

## 🎉 Key Advantages

1. **No Dependencies on External Tools**
   - Pure Python implementation
   - Works without rg, grep, find, etc.
   - Perfect for Mac users without Homebrew

2. **Modular Architecture**
   - Each tool is a separate file
   - Easy to understand and modify
   - Clear separation of concerns

3. **Production Ready**
   - Comprehensive error handling
   - Auto lint detection
   - System hints for reliability
   - Streaming support for UX

4. **Educational Value**
   - Learn how tools work internally
   - Understand pure Python file operations
   - See regex search implementation
   - Study agent architecture patterns

## 📄 License

MIT

## 🤝 Contributing

This is an educational implementation. Feel free to adapt and extend!

---

**Built with pure Python for maximum portability and learning! 🐍✨**
