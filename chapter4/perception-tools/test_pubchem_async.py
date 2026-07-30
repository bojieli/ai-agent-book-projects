"""Deterministic regressions for PubChem asynchronous ListKey handling."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from pubchem_tools import PubChemClient


class _Response:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


def test_listkey_job_fault_resubmits_original_query(monkeypatch):
    client = PubChemClient()
    original = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/formula/C9H8O4/"
        "property/Title,MolecularFormula/JSON"
    )
    calls = []
    responses = iter([
        _Response(202, {"Waiting": {"ListKey": "first"}}),
        _Response(500, {"Fault": {"Code": "PUGREST.Unknown"}}),
        _Response(202, {"Waiting": {"ListKey": "second"}}),
        _Response(200, {"PropertyTable": {"Properties": [{"CID": 2244}]}}),
    ])

    def fake_get(url, params=None, timeout=None):
        calls.append(url)
        return next(responses)

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr(client, "_rate_limit", lambda: 0.0)
    monkeypatch.setattr("pubchem_tools.time.sleep", lambda _seconds: None)

    payload, latency = client.make_request(original)

    assert payload["PropertyTable"]["Properties"][0]["CID"] == 2244
    assert latency >= 0
    assert calls == [
        original,
        original.replace("formula/C9H8O4", "listkey/first"),
        original,
        original.replace("formula/C9H8O4", "listkey/second"),
    ]
