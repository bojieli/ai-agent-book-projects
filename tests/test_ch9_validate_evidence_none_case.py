import pytest
import json
import sys
from pathlib import Path

ch9_e2e = Path(__file__).resolve().parent.parent / "chapter9" / "end-to-end-speech"
if str(ch9_e2e) not in sys.path:
    sys.path.insert(0, str(ch9_e2e))

from validate_evidence import validate


def test_validate_handles_none_case_arms(tmp_path):
    evidence_file = tmp_path / "evidence.json"
    evidence_file.write_text(
        json.dumps({"cases": [{"direct": None, "self_cascade": None}]}),
        encoding="utf-8",
    )
    result = validate(evidence_file)
    assert result["passed"] is False
    assert result["checks"]["both_arms_complete"] is False
