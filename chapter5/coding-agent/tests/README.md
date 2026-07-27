# Test Suite for Coding Agent

Comprehensive test coverage for all tools and features from tools.json.

## 📊 Test Coverage

### Tools Tested

✅ **Grep Tool** (`test_grep_tool.py`) - 16 tests
- Basic pattern search
- Case insensitive search (-i)
- Output modes (content, files_with_matches, count)
- Line numbers (-n)
- Context lines (-A, -B, -C)
- Glob filtering
- File type filtering
- Head limit
- Regex patterns
- Multiline mode
- Error handling

✅ **Glob Tool** (`test_glob_tool.py`) - 10 tests
- Basic glob patterns
- Recursive search (**/*)
- Auto-prefix for recursive
- Modification time sorting
- Complex patterns
- Error handling

✅ **Read Tool** (`test_read_tool.py`) - 13 tests
- Basic file reading
- Line number format (cat -n)
- Offset and limit
- Long line truncation (>2000 chars)
- Empty files
- Binary file detection
- Image file handling
- PDF file handling
- Jupyter notebook reading
- Error handling

✅ **Write Tool** (`test_write_tool.py`) - 10 tests
- Basic file writing
- Overwriting existing files
- Parent directory creation
- Multiline content
- Python lint checking (success/failure)
- Unicode content
- Empty content
- Large files

✅ **Edit Tool** (`test_edit_tool.py`) - 12 tests
- Basic search and replace
- replace_all flag
- Uniqueness checking
- String not found errors
- Indentation preservation
- Multiline replacements
- Lint checking after edit
- Length tracking

✅ **MultiEdit Tool** (`test_multi_edit_tool.py`) - 10 tests
- Multiple edits in sequence
- Sequential application
- Atomic edits (all or nothing)
- File creation (empty old_string)
- Create and modify workflow
- replace_all in multi-edit
- Edit results tracking
- Lint checking
- Size tracking

✅ **LS Tool** (`test_ls_tool.py`) - 12 tests
- Basic directory listing
- Files and directories
- Hidden file exclusion
- Ignore patterns (single and multiple)
- Sorted output
- File sizes
- Directory size (0)
- Error handling

✅ **Bash Tool** (`test_bash_tool.py`) - 14 tests
- Basic command execution
- Exit code capture
- Persistent shell sessions
- Directory change persistence
- Timeout parameter
- Output truncation (>30000 chars)
- Background execution
- Multiple commands (; and &&)
- Quoted paths with spaces
- Shell ID tracking
- Working directory in result

✅ **TodoWrite Tool** (`test_todo_write_tool.py`) - 8 tests
- Create TODO list
- Update TODO list
- Validation (missing fields, invalid status)
- Valid status values (pending, in_progress, completed)
- Empty TODO list
- Statistics calculation

✅ **NotebookEdit Tool** (`test_notebook_edit_tool.py`) - 12 tests
- Replace cell (edit_mode=replace)
- Insert cell (edit_mode=insert)
- Delete cell (edit_mode=delete)
- Insert at beginning
- Change cell type
- Multiline source
- Cell not found error
- Notebook not found error
- Invalid notebook format
- Required parameters

✅ **BashOutput Tool** (`test_bash_output_tool.py`) - 4 tests
- Retrieve background output
- Filter parameter (regex filtering)
- Nonexistent bash_id error
- Output size tracking

✅ **KillBash Tool** (`test_kill_bash_tool.py`) - 3 tests
- Kill shell session
- Nonexistent session error
- Shell ID in response

✅ **ExitPlanMode Tool** (`test_exit_plan_mode_tool.py`) - 3 tests
- Basic plan submission
- Markdown plan support
- Empty plan

✅ **Integration Tests** (`test_integration.py`) - 7 tests
- System hint structure
- Tool call statistics
- Tool warning after 3+ calls
- TODO list in hints
- Write-then-read workflow
- Write-search-edit workflow
- Metadata consistency

## 📈 Total Test Coverage

- **Total Tests**: 130+ tests
- **Tools Covered**: 12/17 tools fully tested
- **Features Tested**: All major features from tools.json
- **Line Coverage**: ~90% (estimated)

### Not Yet Tested (Stub Implementations)
- WebFetch (requires external API)
- WebSearch (requires external API)
- Task (requires recursive agent)

## 🚀 Running Tests

### Run All Tests

```bash
# From the repository root: install the Chapter 5 and test environments
uv sync --locked --python 3.12 --extra ch5 --extra dev

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

cd chapter5/coding-agent
pytest
```

### Run Specific Test File

```bash
pytest tests/test_grep_tool.py
pytest tests/test_bash_tool.py
```

### Run Specific Test

```bash
pytest tests/test_grep_tool.py::TestGrepTool::test_basic_search
```

### Run with Coverage

```bash
pytest --cov=tools --cov-report=html
```

### Run Verbose

```bash
pytest -v
```

### Skip Slow Tests

```bash
pytest -m "not slow"
```

## 📋 Test Organization

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── pytest.ini               # Pytest configuration
├── test_grep_tool.py        # Grep tests (16 tests)
├── test_glob_tool.py        # Glob tests (10 tests)
├── test_read_tool.py        # Read tests (13 tests)
├── test_write_tool.py       # Write tests (10 tests)
├── test_edit_tool.py        # Edit tests (12 tests)
├── test_multi_edit_tool.py  # MultiEdit tests (10 tests)
├── test_ls_tool.py          # LS tests (12 tests)
├── test_bash_tool.py        # Bash tests (14 tests)
├── test_todo_write_tool.py  # TodoWrite tests (8 tests)
├── test_notebook_edit_tool.py  # NotebookEdit tests (12 tests)
├── test_bash_output_tool.py # BashOutput tests (4 tests)
├── test_kill_bash_tool.py   # KillBash tests (3 tests)
├── test_exit_plan_mode_tool.py  # ExitPlanMode tests (3 tests)
└── test_integration.py      # Integration tests (7 tests)
```

## 🎯 Test Features

### Fixtures (conftest.py)

- `system_state` - Fresh SystemState for each test
- `temp_dir` - Temporary directory (auto-cleaned)
- `sample_files` - Pre-created test files (Python, JS, text, nested)

### Test Categories

1. **Functionality Tests**: Verify core features work
2. **Parameter Tests**: Test all tool parameters
3. **Error Handling Tests**: Test error cases
4. **Edge Case Tests**: Test boundary conditions
5. **Integration Tests**: Test tool chaining

## 📝 Test Examples

### Testing Grep Features

```python
def test_case_insensitive_search(self, system_state, sample_files):
    """Test -i flag for case insensitive search"""
    tool = GrepTool(system_state)
    result = tool.execute({
        "pattern": "error",  # lowercase
        "path": str(sample_files["temp_dir"]),
        "-i": True
    })
    
    assert result.success
    assert "ERROR" in result.data["output"]  # Finds uppercase
```

### Testing Tool Chaining

```python
def test_write_search_edit_workflow(self, system_state, temp_dir):
    """Test complete workflow: write, search, edit"""
    # 1. Write file
    # 2. Search for pattern
    # 3. Edit the file
    # 4. Verify with another search
```

## 🐛 Debugging Failed Tests

### View Detailed Output

```bash
pytest -vv tests/test_grep_tool.py::TestGrepTool::test_basic_search
```

### Show Print Statements

```bash
pytest -s tests/test_bash_tool.py
```

### Stop on First Failure

```bash
pytest -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

## ✅ Continuous Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    uv sync --locked --python 3.12 --extra ch5 --extra dev
    uv run --locked --extra ch5 --extra dev --directory chapter5/coding-agent python -m pytest --cov=tools --cov-report=xml
```

## 📚 Adding New Tests

1. Create `tests/test_<tool_name>.py`
2. Import the tool and fixtures
3. Create test class
4. Add test methods

Example:

```python
from tools.my_tool import MyTool

class TestMyTool:
    def test_basic_functionality(self, system_state):
        tool = MyTool(system_state)
        result = tool.execute({"param": "value"})
        assert result.success
```

## 🎓 Test Best Practices

1. **One feature per test**: Each test should test one specific feature
2. **Descriptive names**: Test names should describe what they test
3. **Use fixtures**: Reuse common setup with fixtures
4. **Test errors**: Always test error cases
5. **Clean up**: Use temp_dir fixture for file operations
6. **Assert clearly**: Make assertions explicit and clear

## 📖 References

- pytest docs: https://docs.pytest.org/
- Coverage: https://pytest-cov.readthedocs.io/
