"""Unit-test _analyze_action_types / _format_trajectory with null tool_name,
without importing the full AWorld agent stack (same ast-extraction trick as
test_experience_similar.py)."""
import ast
from pathlib import Path
from typing import Any, Dict, List


def _load_methods(*method_names):
    src = Path(__file__).with_name("trajectory_summarizer.py").read_text()
    tree = ast.parse(src)
    methods = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "TrajectorySummarizer":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name in method_names:
                    methods.append(item)
            break
    assert len(methods) == len(method_names)
    class_src = ast.Module(
        body=[
            ast.ClassDef(
                name="TrajectorySummarizer",
                bases=[],
                keywords=[],
                body=methods,
                decorator_list=[],
            )
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(class_src)
    ns = {"List": List, "Dict": Dict, "Any": Any}
    exec(compile(class_src, "trajectory_summarizer.py", "exec"), ns)
    return ns["TrajectorySummarizer"]()


def test_analyze_action_types_null_tool_name():
    ts = _load_methods("_analyze_action_types")
    # 轨迹步骤显式携带 "tool_name": null（框架序列化 ActionModel 无工具时的形态）
    traj = [{"action": {"tool_name": None, "action_name": "x", "params": {}}}]
    assert ts._analyze_action_types(traj) == {"other": 1}


def test_analyze_action_types_normal():
    ts = _load_methods("_analyze_action_types")
    traj = [
        {"action": {"tool_name": "mshtools-web_search", "action_name": "", "params": {}}},
        {"action": {"tool_name": "mshtools-web_search", "action_name": "", "params": {}}},
        {"action": {"tool_name": "mshtools-compute", "action_name": "", "params": {}}},
    ]
    result = ts._analyze_action_types(traj)
    assert result["search"] == 2
    assert result["computation"] == 1


def test_format_trajectory_null_tool_name():
    ts = _load_methods("_format_trajectory", "_truncate_value")
    traj = [{"action": {"tool_name": None, "action_name": None, "params": None}}]
    text = ts._format_trajectory(traj)
    assert "unknown" in text
    assert "None" not in text
