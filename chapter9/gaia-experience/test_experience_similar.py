"""Unit-test _is_similar without importing the full AWorld agent stack."""

import ast
from pathlib import Path


def _load_is_similar():
    src = Path(__file__).with_name("experience_agent.py").read_text()
    tree = ast.parse(src)
    method = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "ExperienceAgent":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "_is_similar":
                    method = item
                    break
    assert method is not None
    # Build a tiny class with only this method
    class_src = ast.Module(
        body=[
            ast.ClassDef(
                name="ExperienceAgent",
                bases=[],
                keywords=[],
                body=[method],
                decorator_list=[],
            )
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(class_src)
    ns = {}
    exec(compile(class_src, "experience_agent.py", "exec"), ns)
    return ns["ExperienceAgent"]()


def test_is_similar_none_question():
    agent = _load_is_similar()
    assert agent._is_similar(None, "what is 2+2") is False
    assert agent._is_similar("what is 2+2", None) is False
    assert agent._is_similar("what is 2+2", "what is 2+2") is True
