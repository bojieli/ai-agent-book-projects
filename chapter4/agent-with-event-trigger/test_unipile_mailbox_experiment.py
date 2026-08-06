"""Offline contract tests; these are not substitutes for the live campaign receipt."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "unipile_mailbox_experiment.py"
SPEC = importlib.util.spec_from_file_location("experiment_4_5_unipile", MODULE_PATH)
experiment = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = experiment
SPEC.loader.exec_module(experiment)


def _email(kind: str, date: str, suffix: str) -> dict:
    base = {"id": f"email-{suffix}", "account_id": "account-real",
            "date": date, "role": "inbox", "folders": ["Inbox"]}
    if kind == "meeting_invitation":
        return {**base, "subject": "Meeting invitation: design review",
                "body_plain": "START_UTC: 2026-08-03T10:00:00.000Z\n"
                              "END_UTC: 2026-08-03T11:00:00.000Z"}
    if kind == "customer_complaint":
        return {**base, "subject": "Customer complaint: delayed order",
                "body_plain": "Customer complaint for order #E44-TEST. Please escalate."}
    return {**base, "subject": "Marketing newsletter",
            "body_plain": "Marketing newsletter promotion. Click to unsubscribe."}


def _provider(request: httpx.Request) -> httpx.Response:
    assert request.headers.get("X-API-KEY") == "unit-secret"
    if request.method == "GET" and request.url.path == "/api/v1/calendars":
        return httpx.Response(200, json={"data": [{"id": "calendar-real",
                                                   "is_primary": True}]})
    if request.method == "GET" and request.url.path.endswith("/events"):
        return httpx.Response(200, json={"data": []})
    if request.method == "GET" and request.url.path == "/api/v1/folders":
        return httpx.Response(200, json={"items": [{"id": "folder-archive",
                                                    "name": "Archive",
                                                    "role": "archive"}]})
    if request.method == "PUT" and request.url.path == "/api/v1/emails/email-marketing":
        assert json.loads(request.content) == {"folders": ["archive"]}
        return httpx.Response(200, json={"object": "EmailUpdated"})
    if request.method == "GET" and request.url.path == "/api/v1/emails/email-marketing":
        return httpx.Response(200, json={"id": "email-marketing",
                                        "role": "archive", "folders": ["Archive"]})
    return httpx.Response(404, json={"type": "unexpected_test_request"})


def test_classification_is_unique_and_meeting_interval_is_exact():
    email = _email("meeting_invitation", "2026-08-01T00:00:01.000Z", "meeting")
    assert experiment.classify_email(email) == "meeting_invitation"
    start, end = experiment.meeting_interval(email)
    assert start.isoformat() == "2026-08-03T10:00:00+00:00"
    assert (end - start).total_seconds() == 3600
    ambiguous = {**email, "subject": "Meeting invitation and marketing newsletter",
                 "body_plain": email["body_plain"] + "\nMarketing unsubscribe"}
    with pytest.raises(ValueError, match="not unique"):
        experiment.classify_email(ambiguous)


def test_real_api_error_is_receipted_and_raises():
    def unauthorized(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"status": 401,
                                        "type": "errors/missing_credentials",
                                        "title": "Missing credentials"})

    client = experiment.UnipileClient(
        "api.example.invalid:12345", "unit-secret",
        transport=httpx.MockTransport(unauthorized),
    )
    with pytest.raises(experiment.UnipileAPIError):
        client.list_accounts()
    assert client.calls == [{
        **client.calls[0], "status": 401, "success": False,
        "credential_scheme": "X-API-KEY",
        "error_type": "errors/missing_credentials",
    }]
    assert "unit-secret" not in experiment.canonical_json(client.calls)
    client.close()

def test_three_email_workflow_and_acceptance(tmp_path):
    client = experiment.UnipileClient(
        "api.example.invalid:12345", "unit-secret",
        transport=httpx.MockTransport(_provider),
    )
    runner = experiment.MailboxExperiment(
        client, tmp_path, "account-real", "account-real"
    )
    # Deliberately unordered input proves that the FIFO queue uses provider time.
    emails = [
        _email("marketing", "2026-08-01T00:00:03.000Z", "marketing"),
        _email("meeting_invitation", "2026-08-01T00:00:01.000Z", "meeting"),
        _email("customer_complaint", "2026-08-01T00:00:02.000Z", "complaint"),
    ]
    runner.process_queue(emails)
    assert [row["classification"] for row in runner.workflows] == [
        "meeting_invitation", "customer_complaint", "marketing"
    ]
    result = experiment.derive_acceptance(
        runner.events, runner.workflows, client.calls,
        [{"object": "EmailSent"}] * 3,
        credential_secret="unit-secret", dsn_secret="api.example.invalid:12345",
    )
    assert result["status"] == "passed"
    assert all(result["gates"].values())
    assert (tmp_path / "artifacts" / "meeting_reply_draft.txt").stat().st_size > 100
    assert (tmp_path / "artifacts" / "high_priority_notifications.jsonl").is_file()
    assert "unit-secret" not in experiment.canonical_json(client.calls)
    client.close()


def test_acceptance_fails_when_provider_archive_verification_is_missing(tmp_path):
    client = experiment.UnipileClient(
        "api.example.invalid:12345", "unit-secret",
        transport=httpx.MockTransport(_provider),
    )
    runner = experiment.MailboxExperiment(client, tmp_path, "account-real", "account-real")
    runner.process_queue([
        _email("meeting_invitation", "2026-08-01T00:00:01.000Z", "meeting"),
        _email("customer_complaint", "2026-08-01T00:00:02.000Z", "complaint"),
        _email("marketing", "2026-08-01T00:00:03.000Z", "marketing"),
    ])
    runner.workflows[-1]["archive"]["verified"] = False
    result = experiment.derive_acceptance(
        runner.events, runner.workflows, client.calls, [{}, {}, {}],
        credential_secret="unit-secret", dsn_secret="api.example.invalid:12345",
    )
    assert result["status"] == "failed"
    assert not result["gates"]["marketing_archived_and_verified_through_provider"]
    client.close()
