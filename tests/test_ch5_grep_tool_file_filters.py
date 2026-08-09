import sys
from pathlib import Path
import pytest

ch5_tools_dir = Path(__file__).resolve().parent.parent / "chapter5" / "coding-agent"
if str(ch5_tools_dir) not in sys.path:
    sys.path.insert(0, str(ch5_tools_dir))

from tools.grep_tool import GrepTool  # noqa: E402
from system_state import SystemState  # noqa: E402


@pytest.fixture
def temp_files(tmp_path):
    py_file = tmp_path / "script.py"
    py_file.write_text("def hello():\n    print('world')\n", encoding="utf-8")
    
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("just some text\n", encoding="utf-8")
    
    return {"py": py_file, "txt": txt_file}


def test_grep_tool_single_file_matching_file_type(temp_files):
    state = SystemState()
    tool = GrepTool(state)
    
    files = tool._get_files_to_search(temp_files["py"], glob_pattern=None, file_type="py")
    assert files == [temp_files["py"]]


def test_grep_tool_single_file_mismatched_file_type(temp_files):
    state = SystemState()
    tool = GrepTool(state)
    
    files = tool._get_files_to_search(temp_files["py"], glob_pattern=None, file_type="js")
    assert files == []


def test_grep_tool_single_file_matching_glob(temp_files):
    state = SystemState()
    tool = GrepTool(state)
    
    files = tool._get_files_to_search(temp_files["py"], glob_pattern="*.py", file_type=None)
    assert files == [temp_files["py"]]


def test_grep_tool_single_file_mismatched_glob(temp_files):
    state = SystemState()
    tool = GrepTool(state)
    
    files = tool._get_files_to_search(temp_files["py"], glob_pattern="*.js", file_type=None)
    assert files == []


def test_grep_tool_execute_single_file_mismatched_type(temp_files):
    state = SystemState()
    tool = GrepTool(state)
    
    result = tool.execute({
        "pattern": "hello",
        "path": str(temp_files["py"]),
        "type": "js"
    })
    assert result.success is True
    assert result.data["matches"] == 0
    assert result.data["output"] == "No files found matching criteria."


def test_grep_tool_execute_single_file_mismatched_glob(temp_files):
    state = SystemState()
    tool = GrepTool(state)
    
    result = tool.execute({
        "pattern": "hello",
        "path": str(temp_files["py"]),
        "glob": "*.txt"
    })
    assert result.success is True
    assert result.data["matches"] == 0
    assert result.data["output"] == "No files found matching criteria."
