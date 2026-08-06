import sys
from pathlib import Path

ch10_apr = Path(__file__).resolve().parent.parent / "chapter10" / "autonomous-phone-registration"
if str(ch10_apr) not in sys.path:
    sys.path.insert(0, str(ch10_apr))

from models import FieldSpec


def test_field_spec_validate_handles_none_value():
    # FieldSpec.validate(None) should not raise AttributeError when passed None.
    # Required field -> returns (False, error_msg)
    field_req = FieldSpec(name="email", label="Email", required=True)
    valid, msg = field_req.validate(None)
    assert valid is False
    assert "必填" in msg or "空" in msg

    # Optional field -> returns (True, "")
    field_opt = FieldSpec(name="note", label="Note", required=False)
    valid, msg = field_opt.validate(None)
    assert valid is True
    assert msg == ""
