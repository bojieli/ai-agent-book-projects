"""Offline regression test for bounded official arXiv API pages."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

import public_data_tools  # noqa: E402


def test_search_arxiv_bounds_client_page_size(monkeypatch):
    observed: dict[str, object] = {}

    class FakeSearch:
        def __init__(self, **kwargs):
            observed["search"] = kwargs

    class FakeClient:
        def __init__(self, **kwargs):
            observed["client"] = kwargs

        def results(self, _search):
            return iter([
                SimpleNamespace(
                    title="A real paper",
                    authors=[SimpleNamespace(name="Author")],
                    summary="Summary",
                    published=datetime(2026, 7, 30, tzinfo=timezone.utc),
                    entry_id="https://arxiv.org/abs/2607.00001",
                    pdf_url="https://arxiv.org/pdf/2607.00001",
                    categories=["cs.AI"],
                )
            ])

    fake_arxiv = SimpleNamespace(
        Search=FakeSearch,
        Client=FakeClient,
        SortCriterion=SimpleNamespace(
            Relevance="relevance",
            LastUpdatedDate="lastUpdatedDate",
            SubmittedDate="submittedDate",
        ),
    )
    monkeypatch.setitem(sys.modules, "arxiv", fake_arxiv)

    result = asyncio.run(public_data_tools.search_arxiv(
        "transformer", max_results=3, sort_by="submittedDate"
    ))
    payload = json.loads(result.text)

    assert observed["search"] == {
        "query": "transformer",
        "max_results": 3,
        "sort_by": "submittedDate",
    }
    assert observed["client"] == {
        "page_size": 3,
        "delay_seconds": 3.0,
        "num_retries": 3,
    }
    assert payload["success"] is True
    assert payload["message"]["count"] == 1
def test_download_paper_case_insensitive_arxiv_prefix(monkeypatch, tmp_path):
    import arxiv_enhanced

    class FakeResponse:
        content = b"%PDF-1.7\n" + b"0" * 1000
        headers = {"content-type": "application/pdf"}

        def raise_for_status(self):
            pass

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

        async def get(self, _url):
            return FakeResponse()

    monkeypatch.setattr(arxiv_enhanced.httpx, "AsyncClient", FakeClient)
    result = asyncio.run(
        arxiv_enhanced.download_paper("arXiv:2301.07041", download_dir=str(tmp_path))
    )
    payload = json.loads(result.text)
    assert payload["success"] is True
    assert payload["message"]["paper_id"] == "2301.07041"
