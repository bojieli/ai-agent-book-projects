"""Trailing commas in page_range must not crash parse_page_range."""
import importlib.util
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src" / "document_processing_tools.py"
_spec = importlib.util.spec_from_file_location("document_processing_tools_page_range", _SRC)
_mod = importlib.util.module_from_spec(_spec)
# Load only parse_page_range without heavy optional deps (PyPDF2, etc.).
source = _SRC.read_text(encoding="utf-8")
start = source.index("def parse_page_range")
ns = {}
exec(compile(source[start:], str(_SRC), "exec"), ns)
parse_page_range = ns["parse_page_range"]


def test_trailing_comma_does_not_raise():
    assert parse_page_range("1,3,", 10) == [0, 2]


def test_duplicate_comma_does_not_raise():
    assert parse_page_range("1,,3", 10) == [0, 2]


def test_leading_comma_does_not_raise():
    assert parse_page_range(",1,5", 10) == [0, 4]


def test_normal_list_unchanged():
    assert parse_page_range("1,3,5", 10) == [0, 2, 4]


def test_range_with_trailing_comma():
    assert parse_page_range("1-3,", 10) == [0, 1, 2]
