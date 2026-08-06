"""Regression test for write_excel_data with empty data dictionary."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "chapter4" / "collaboration-tools" / "src"))

from excel_tools import write_excel_data


def test_write_excel_data_empty_dict(tmp_path: Path):
    target = str(tmp_path / "test_empty.xlsx")
    res = asyncio.run(write_excel_data(target, data={}, overwrite=True))
    assert res["success"] is False
    assert "Data dictionary cannot be empty" in res["error"] or "empty" in res["error"].lower()
