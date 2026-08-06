import pytest
import sys
from pathlib import Path

ch10_dir = Path(__file__).resolve().parent.parent / "chapter10" / "autonomous-phone-registration"
if str(ch10_dir) not in sys.path:
    sys.path.insert(0, str(ch10_dir))

from models import FieldSpec


def test_validate_none_value_when_required():
    field = FieldSpec(name="username", label="用户名", required=True)
    valid, msg = field.validate(None)
    assert valid is False
    assert "必填" in msg


def test_validate_none_value_when_optional():
    field = FieldSpec(name="middle_name", label="中间名", required=False)
    valid, msg = field.validate(None)
    assert valid is True
    assert msg == ""


def test_validate_whitespace_when_required():
    field = FieldSpec(name="email", label="邮箱", required=True)
    valid, msg = field.validate("   ")
    assert valid is False
    assert "必填" in msg


def test_validate_valid_email_and_none_optional():
    email_field = FieldSpec(name="email", label="邮箱", input_type="email", required=False)
    valid, msg = email_field.validate(None)
    assert valid is True

    valid_email, _ = email_field.validate("test@example.com")
    assert valid_email is True

    invalid_email, _ = email_field.validate("invalid-email")
    assert invalid_email is False


def test_validate_options_with_none():
    option_field = FieldSpec(name="gender", label="性别", options=["Male", "Female"], required=False)
    valid, msg = option_field.validate(None)
    assert valid is True

    valid_opt, _ = option_field.validate("Male")
    assert valid_opt is True

    invalid_opt, _ = option_field.validate("Other")
    assert invalid_opt is False
