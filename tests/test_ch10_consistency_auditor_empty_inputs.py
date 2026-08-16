import importlib.util
from pathlib import Path
import sys
import pytest

_module_path = (
    Path(__file__).resolve().parent.parent
    / "chapter10"
    / "book-translation"
    / "consistency_auditor.py"
)
_spec = importlib.util.spec_from_file_location("consistency_auditor", _module_path)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["consistency_auditor"] = _mod
_spec.loader.exec_module(_mod)
BilingualConsistencyAuditor = _mod.BilingualConsistencyAuditor


def test_audit_empty_markdown_documents():
    auditor = BilingualConsistencyAuditor()
    score, findings = auditor._audit_code_blocks("", "")
    assert score == 1.0
    assert findings == []

    score, findings = auditor._audit_latex_formulas("", "")
    assert score == 1.0
    assert findings == []

    score, findings = auditor._audit_link_targets("", "")
    assert score == 1.0
    assert findings == []


def test_audit_empty_source_with_non_empty_target():
    auditor = BilingualConsistencyAuditor()
    score, findings = auditor._audit_code_blocks("", "```python\nprint('hello')\n```")
    assert score == 0.0
    assert len(findings) == 1

    score, findings = auditor._audit_link_targets("", "[Google](https://google.com)")
    assert score == 0.0
    assert len(findings) == 1
