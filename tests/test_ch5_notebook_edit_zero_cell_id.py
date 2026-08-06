import pytest
import json
import sys
from pathlib import Path

ch5_tools_dir = Path(__file__).resolve().parent.parent / "chapter5" / "coding-agent"
if str(ch5_tools_dir) not in sys.path:
    sys.path.insert(0, str(ch5_tools_dir))

from tools.notebook_edit_tool import NotebookEditTool  # noqa: E402
from system_state import SystemState  # noqa: E402


@pytest.fixture
def temp_notebook(tmp_path):
    nb_path = tmp_path / "test_zero_id.ipynb"
    nb_data = {
        "cells": [
            {
                "id": "0",
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": ["print('original')\n"],
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    nb_path.write_text(json.dumps(nb_data), encoding="utf-8")
    return nb_path


def test_notebook_edit_accepts_integer_zero_cell_id(temp_notebook):
    state = SystemState()
    tool = NotebookEditTool(state)
    result = tool.execute({
        "notebook_path": str(temp_notebook),
        "cell_id": 0,
        "new_source": "print('updated')",
        "edit_mode": "replace",
    })
    assert result.success is True, f"Execution failed: {result.data}"
    assert result.data.get("action") == "replaced"
    
    nb_content = json.loads(temp_notebook.read_text(encoding="utf-8"))
    assert "".join(nb_content["cells"][0]["source"]) == "print('updated')"
