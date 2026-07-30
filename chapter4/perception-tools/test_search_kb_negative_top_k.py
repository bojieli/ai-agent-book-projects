import json
from pathlib import Path
import pytest
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))
from search_tools import search_knowledge_base


@pytest.mark.asyncio
async def test_search_knowledge_base_negative_top_k(tmp_path: Path):
    (tmp_path / "doc1.txt").write_text("test content one", encoding="utf-8")
    (tmp_path / "doc2.txt").write_text("test content two", encoding="utf-8")

    res = await search_knowledge_base("test", str(tmp_path), top_k=-1)
    payload = json.loads(res.text)
    assert payload["success"] is True
    assert payload["message"]["total_found"] == 0
    assert payload["message"]["results"] == []
