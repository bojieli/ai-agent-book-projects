"""Regression: extract_csv_content must honor max_rows in data, not hard-cap at 100."""
import json
from pathlib import Path

import pandas as pd
import pytest

from document_processing_tools import extract_csv_content


@pytest.mark.asyncio
async def test_csv_data_honors_max_rows(tmp_path: Path):
    path = tmp_path / "t.csv"
    pd.DataFrame({"id": range(250)}).to_csv(path, index=False)
    r = await extract_csv_content(str(path), max_rows=1000)
    payload = json.loads(r.text)
    msg = payload["message"]
    assert msg["rows"] == 250
    assert len(msg["data"]) == 250
    assert msg["truncated"] is False
