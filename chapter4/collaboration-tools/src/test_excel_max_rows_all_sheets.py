"""Regression: all-sheets read must honor max_rows (not a hard 100-row cap)."""
import asyncio
from pathlib import Path

import pandas as pd
import pytest
from openpyxl import Workbook

from excel_tools import read_excel_data


def _workbook(path: Path, n_rows: int) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(["id", "val"])
    for i in range(n_rows):
        ws.append([i, f"r{i}"])
    wb.save(path)


@pytest.mark.asyncio
async def test_all_sheets_honors_max_rows(tmp_path: Path):
    path = tmp_path / "wide.xlsx"
    _workbook(path, 150)

    all_sheets = await read_excel_data(str(path), sheet_name=None, max_rows=1000)
    named = await read_excel_data(str(path), sheet_name="Data", max_rows=1000)

    assert all_sheets["success"] is True
    assert named["success"] is True
    assert len(named["data"]["Data"]) == 150
    assert len(all_sheets["data"]["Data"]) == 150


@pytest.mark.asyncio
async def test_all_sheets_still_respects_smaller_max_rows(tmp_path: Path):
    path = tmp_path / "wide.xlsx"
    _workbook(path, 150)

    result = await read_excel_data(str(path), sheet_name=None, max_rows=40)
    assert result["success"] is True
    assert len(result["data"]["Data"]) == 40


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
