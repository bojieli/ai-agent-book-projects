#!/usr/bin/env python3
"""Run Chapter 4 Experiment 4-5 against a real Unipile mailbox.

The listener uses documented mailbox polling, which the manuscript explicitly
allows as an alternative to push notifications. It never substitutes local
mail files for provider objects. Missing/invalid credentials produce a durable
blocked receipt instead of a successful demonstration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "experiment_protocol.json"
VALIDATION_ROOT = HERE / "validation" / "experiment_4_5"
UTC = timezone.utc
SIMULATION_PATTERN = re.compile(
    r"\b(mock(?:ed)?|placeholder|synthetic|simulat(?:ed|ion))\b", re.IGNORECASE
)
CREDENTIAL_PATTERN = re.compile(r"\b(?:sk|gh[opusr])-[A-Za-z0-9_-]{12,}\b")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), default=str)


def sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n"
    if CREDENTIAL_PATTERN.search(text):
        raise ValueError(f"credential-shaped value in {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def iso_millis(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, dict):
        value = value.get("date_time") or value.get("dateTime") or value.get("datetime") \
            or value.get("date")
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def redacted(value: Any, key: str = "") -> Any:
    """Retain audit shape while hashing identities and message bodies."""
    lower = key.lower()
    if isinstance(value, str) and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        return {"sha256": sha256(value)[:20], "present": True, "kind": "email_address"}
    if any(token in lower for token in ("token", "authorization", "api_key", "credential")):
        return "<redacted>"
    if lower in {"body", "body_plain", "text", "content"} and isinstance(value, str):
        return {"sha256": sha256(value), "characters": len(value)}
    if lower == "subject" and isinstance(value, str):
        # Experiment subjects contain no personal data and prove scenario fidelity.
        return value
    if lower.endswith("_id") or lower in {"id", "identifier", "email", "from", "to"}:
        if isinstance(value, (str, int)):
            return {"sha256": sha256(str(value))[:20], "present": bool(value)}
    if isinstance(value, dict):
        return {str(child_key): redacted(child, str(child_key))
                for child_key, child in value.items()}
    if isinstance(value, list):
        return [redacted(child, key) for child in value]
    return value


class UnipileAPIError(RuntimeError):
    def __init__(self, method: str, path: str, status: int, payload: Any):
        self.method = method
        self.path = path
        self.status = status
        self.payload = payload
        title = payload.get("title") if isinstance(payload, dict) else None
        error_type = payload.get("type") if isinstance(payload, dict) else None
        super().__init__(f"{method} {path} returned {status}: {error_type or title or 'API error'}")


class UnipileClient:
    """Small receipt-producing adapter for the official Email/Calendar API."""

    def __init__(self, dsn: str, access_token: str, *, timeout: float = 45,
                 transport: httpx.BaseTransport | None = None):
        if not dsn or not access_token:
            raise ValueError("UNIPILE_DSN and UNIPILE_ACCESS_TOKEN are required")
        base = dsn.strip().rstrip("/")
        if not base.startswith(("http://", "https://")):
            base = "https://" + base
        self.base_url = base
        self.access_token = access_token.strip()
        self.calls: list[dict[str, Any]] = []
        self.http = httpx.Client(
            base_url=base,
            timeout=timeout,
            follow_redirects=True,
            headers={"X-API-KEY": self.access_token,
                     "User-Agent": "ai-agent-book-experiment/4.4"},
            transport=transport,
        )

    def close(self) -> None:
        self.http.close()

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None,
                json_body: dict[str, Any] | None = None,
                multipart: dict[str, Any] | None = None,
                expected: set[int] | None = None) -> Any:
        expected = expected or {200}
        started = time.perf_counter()
        request_kwargs: dict[str, Any] = {"params": params}
        if json_body is not None:
            request_kwargs["json"] = json_body
        if multipart is not None:
            request_kwargs["files"] = {key: (None, value) for key, value in multipart.items()}
        try:
            response = self.http.request(method, path, **request_kwargs)
            try:
                payload: Any = response.json()
            except ValueError:
                payload = {"non_json_sha256": sha256(response.content),
                           "bytes": len(response.content)}
            receipt = {
                "method": method.upper(),
                "path": path,
                "request": redacted({"params": params or {},
                                      "json": json_body,
                                      "multipart": multipart}),
                "credential_scheme": "X-API-KEY",
                "status": response.status_code,
                "success": response.status_code in expected,
                "latency_seconds": round(time.perf_counter() - started, 3),
                "response_sha256": sha256(response.content),
                "response_bytes": len(response.content),
                "response_shape": sorted(payload) if isinstance(payload, dict)
                                  else type(payload).__name__,
                "error_type": payload.get("type") if isinstance(payload, dict) else None,
                "error_title": payload.get("title") if isinstance(payload, dict) else None,
            }
            self.calls.append(receipt)
            if response.status_code not in expected:
                raise UnipileAPIError(method.upper(), path, response.status_code, payload)
            return payload
        except UnipileAPIError:
            raise
        except Exception as exc:
            self.calls.append({
                "method": method.upper(), "path": path,
                "request": redacted({"params": params or {}, "json": json_body,
                                      "multipart": multipart}),
                "credential_scheme": "X-API-KEY", "status": None, "success": False,
                "latency_seconds": round(time.perf_counter() - started, 3),
                "error_type": type(exc).__name__, "error_title": str(exc)[:300],
            })
            raise

    def list_accounts(self) -> list[dict[str, Any]]:
        payload = self.request("GET", "/api/v1/accounts", params={"limit": 100})
        items = payload.get("items", []) if isinstance(payload, dict) else []
        if not isinstance(items, list):
            raise ValueError("Unipile accounts response did not contain an items list")
        return items

    def list_folders(self, account_id: str) -> list[dict[str, Any]]:
        payload = self.request("GET", "/api/v1/folders",
                               params={"account_id": account_id})
        return payload.get("items", []) if isinstance(payload, dict) else []

    def list_emails(self, account_id: str, *, after: datetime,
                    folder: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "account_id": account_id, "after": iso_millis(after),
            "limit": min(max(limit, 1), 250), "meta_only": False,
        }
        if folder:
            params["folder"] = folder
        payload = self.request("GET", "/api/v1/emails", params=params)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        if not isinstance(items, list):
            raise ValueError("Unipile email response did not contain an items list")
        return items

    def get_email(self, email_id: str) -> dict[str, Any]:
        payload = self.request("GET", f"/api/v1/emails/{email_id}")
        if not isinstance(payload, dict):
            raise ValueError("Unipile email response was not an object")
        return payload

    def update_email_folders(self, email_id: str, folders: list[str]) -> dict[str, Any]:
        payload = self.request("PUT", f"/api/v1/emails/{email_id}",
                               json_body={"folders": folders})
        if not isinstance(payload, dict):
            raise ValueError("Unipile update response was not an object")
        return payload

    def send_email(self, account_id: str, recipient: str, subject: str,
                   body: str) -> dict[str, Any]:
        payload = self.request(
            "POST", "/api/v1/emails", expected={201}, multipart={
                "account_id": account_id,
                "to": json.dumps([{"display_name": "Experiment 4-5 mailbox",
                                   "identifier": recipient}]),
                "subject": subject,
                "body": body,
            },
        )
        if not isinstance(payload, dict):
            raise ValueError("Unipile send response was not an object")
        return payload

    def list_calendars(self, account_id: str) -> list[dict[str, Any]]:
        payload = self.request("GET", "/api/v1/calendars",
                               params={"account_id": account_id, "limit": 100})
        data = payload.get("data", []) if isinstance(payload, dict) else []
        if not isinstance(data, list):
            raise ValueError("Unipile calendars response did not contain a data list")
        return data

    def list_calendar_events(self, account_id: str, calendar_id: str,
                             start: datetime, end: datetime) -> list[dict[str, Any]]:
        payload = self.request(
            "GET", f"/api/v1/calendars/{calendar_id}/events", params={
                "account_id": account_id,
                "start": iso_millis(start - timedelta(days=1)),
                "end": iso_millis(end + timedelta(days=1)),
                "expand_recurring": True, "limit": 250,
            },
        )
        data = payload.get("data", []) if isinstance(payload, dict) else []
        if not isinstance(data, list):
            raise ValueError("Unipile events response did not contain a data list")
        return data


def account_email(account: dict[str, Any]) -> str | None:
    """Find an email-looking account identity without exposing it in receipts."""
    preferred = ("email", "identifier", "username", "user", "name")
    for key in preferred:
        value = account.get(key)
        if isinstance(value, str) and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            return value
    for value in account.values():
        if isinstance(value, dict):
            found = account_email(value)
            if found:
                return found
    return None


def email_text(email: dict[str, Any]) -> str:
    for key in ("body_plain", "body", "text"):
        value = email.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def classify_email(email: dict[str, Any]) -> str:
    text = f"{email.get('subject', '')}\n{email_text(email)}".lower()
    matches = []
    if "meeting invitation" in text and "start_utc:" in text and "end_utc:" in text:
        matches.append("meeting_invitation")
    if "customer complaint" in text and re.search(r"order\s*#[a-z0-9-]+", text):
        matches.append("customer_complaint")
    if "marketing" in text and ("unsubscribe" in text or "newsletter" in text):
        matches.append("marketing")
    if len(matches) != 1:
        raise ValueError(f"email classification was not unique: {matches}")
    return matches[0]


def meeting_interval(email: dict[str, Any]) -> tuple[datetime, datetime]:
    text = email_text(email)
    start_match = re.search(r"START_UTC:\s*([^\s]+)", text, re.IGNORECASE)
    end_match = re.search(r"END_UTC:\s*([^\s]+)", text, re.IGNORECASE)
    start = parse_datetime(start_match.group(1)) if start_match else None
    end = parse_datetime(end_match.group(1)) if end_match else None
    if not start or not end or end <= start:
        raise ValueError("meeting email lacked a valid START_UTC/END_UTC interval")
    return start, end


def event_overlaps(event: dict[str, Any], start: datetime, end: datetime) -> bool:
    event_start = parse_datetime(event.get("start") or event.get("start_at"))
    event_end = parse_datetime(event.get("end") or event.get("end_at"))
    cancelled = bool(event.get("is_cancelled")) or str(event.get("status", "")).lower() == "cancelled"
    return bool(event_start and event_end and not cancelled
                and event_start < end and event_end > start)


def canonical_event(email: dict[str, Any], sequence: int) -> dict[str, Any]:
    email_id = str(email.get("id", ""))
    account_id = str(email.get("account_id", ""))
    if not email_id or not account_id:
        raise ValueError("provider email object lacked id/account_id")
    return {
        "sequence": sequence,
        "source": {"type": "email", "provider": "unipile",
                   "email_id_sha256": sha256(email_id)[:20],
                   "account_id_sha256": sha256(account_id)[:20]},
        "channel": "unipile_mailbox_poll",
        "content": {"subject": email.get("subject", ""),
                    "body_sha256": sha256(email_text(email)),
                    "body_characters": len(email_text(email))},
        "context": {"provider_date": email.get("date"), "role": email.get("role"),
                    "folders_count": len(email.get("folders") or [])},
        "provider_receipt_sha256": sha256(canonical_json(redacted(email))),
    }


def provider_date(email: dict[str, Any]) -> tuple[datetime, str]:
    return (parse_datetime(email.get("date")) or datetime.min.replace(tzinfo=UTC),
            str(email.get("id", "")))


class MailboxExperiment:
    def __init__(self, client: UnipileClient, campaign_dir: Path,
                 account_id: str, calendar_account_id: str):
        self.client = client
        self.campaign_dir = campaign_dir
        self.account_id = account_id
        self.calendar_account_id = calendar_account_id
        self.events: list[dict[str, Any]] = []
        self.workflows: list[dict[str, Any]] = []

    def _meeting(self, email: dict[str, Any]) -> dict[str, Any]:
        start, end = meeting_interval(email)
        calendars = self.client.list_calendars(self.calendar_account_id)
        if not calendars:
            raise RuntimeError("calendar conflict check returned no calendars")
        calendar = next((row for row in calendars
                         if row.get("is_primary") or row.get("is_default")), calendars[0])
        calendar_id = str(calendar.get("id", ""))
        if not calendar_id:
            raise ValueError("selected calendar lacked an id")
        events = self.client.list_calendar_events(
            self.calendar_account_id, calendar_id, start, end
        )
        conflicts = [event for event in events if event_overlaps(event, start, end)]
        disposition = "decline" if conflicts else "accept"
        draft = (
            f"Subject: Re: {email.get('subject', 'Meeting invitation')}\n\n"
            + ("Thank you for the invitation. I have a calendar conflict during the proposed "
               "time, so I must decline. Could we find another time?"
               if conflicts else
               "Thank you for the invitation. I checked the calendar and the proposed time is "
               "available. I am happy to accept.")
            + "\n"
        )
        draft_path = self.campaign_dir / "artifacts" / "meeting_reply_draft.txt"
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(draft, encoding="utf-8")
        return {
            "classification": "meeting_invitation",
            "calendar_check": {"performed": True, "calendar_id_sha256": sha256(calendar_id)[:20],
                               "events_examined": len(events), "conflict_count": len(conflicts),
                               "conflict": bool(conflicts), "start": iso_millis(start),
                               "end": iso_millis(end)},
            "draft": {"disposition": disposition, "path": str(draft_path),
                      "bytes": draft_path.stat().st_size,
                      "sha256": sha256(draft_path.read_bytes())},
        }

    def _complaint(self, email: dict[str, Any]) -> dict[str, Any]:
        text = email_text(email)
        order = re.search(r"order\s*#([A-Za-z0-9-]+)", text, re.IGNORECASE)
        if not order:
            raise ValueError("complaint lacked an order identifier")
        notification = {
            "created_at": datetime.now(UTC).isoformat(),
            "priority": "high", "delivered": True,
            "channel": "durable_console_and_jsonl",
            "classification": "customer_complaint",
            "subject": email.get("subject", ""),
            "order_reference": order.group(1),
            "summary": "Customer reports an unresolved delayed order and requests human follow-up.",
        }
        path = self.campaign_dir / "artifacts" / "high_priority_notifications.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(notification, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        print(f"HIGH PRIORITY: customer complaint for order #{order.group(1)}", file=sys.stderr)
        return {"classification": "customer_complaint",
                "extracted": {"order_reference": order.group(1),
                              "requires_human_follow_up": True},
                "notification": {**notification, "path": str(path),
                                 "file_sha256": sha256(path.read_bytes())}}

    def _marketing(self, email: dict[str, Any]) -> dict[str, Any]:
        folders = self.client.list_folders(self.account_id)
        archive_candidates = [row for row in folders if
                              "archive" in str(row.get("role", "")).lower()
                              or "archive" in str(row.get("name", "")).lower()]
        update = self.client.update_email_folders(str(email["id"]), ["archive"])
        verified = self.client.get_email(str(email["id"]))
        role = str(verified.get("role", "")).lower()
        folder_text = " ".join(str(value).lower()
                               for value in (verified.get("folders") or []))
        archived = role == "archive" or "archive" in folder_text \
            or (role != "inbox" and "inbox" not in folder_text)
        return {
            "classification": "marketing",
            "archive": {"update_object": update.get("object"),
                        "archive_folder_candidates": len(archive_candidates),
                        "verified": archived,
                        "verified_role": role,
                        "verified_folders_sha256": sha256(folder_text)},
        }

    def process_queue(self, emails: list[dict[str, Any]]) -> None:
        queue = deque(sorted(emails, key=provider_date))
        while queue:
            email = queue.popleft()
            sequence = len(self.events)
            event = canonical_event(email, sequence)
            classification = classify_email(email)
            event["context"]["classification"] = classification
            self.events.append(event)
            if classification == "meeting_invitation":
                workflow = self._meeting(email)
            elif classification == "customer_complaint":
                workflow = self._complaint(email)
            else:
                workflow = self._marketing(email)
            workflow["sequence"] = sequence
            workflow["email_id_sha256"] = event["source"]["email_id_sha256"]
            self.workflows.append(workflow)


def seed_messages(client: UnipileClient, sender_account_id: str, recipient: str,
                  campaign_id: str) -> list[dict[str, Any]]:
    start = (datetime.now(UTC) + timedelta(days=2)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(hours=1)
    messages = [
        (
            f"[EXP4-5 {campaign_id}] Meeting invitation: design review",
            "Meeting invitation for the agent experiment.\n"
            f"START_UTC: {iso_millis(start)}\nEND_UTC: {iso_millis(end)}\n"
            "Please accept if the calendar is free, otherwise decline.",
        ),
        (
            f"[EXP4-5 {campaign_id}] Customer complaint: delayed order",
            f"Customer complaint for order #{campaign_id[-8:]}. The delivery is overdue and "
            "support has not resolved it. Please arrange urgent human follow-up.",
        ),
        (
            f"[EXP4-5 {campaign_id}] Marketing newsletter",
            "Marketing newsletter: save 20 percent on productivity software. "
            "This bulk promotion includes an unsubscribe link.",
        ),
    ]
    return [client.send_email(sender_account_id, recipient, subject, body)
            for subject, body in messages]


def inbox_folder(client: UnipileClient, account_id: str) -> str | None:
    folders = client.list_folders(account_id)
    inbox = next((row for row in folders if
                  str(row.get("role", "")).lower() == "inbox"
                  or str(row.get("name", "")).lower() == "inbox"), None)
    if not inbox:
        return None
    return str(inbox.get("provider_id") or inbox.get("id") or inbox.get("name"))


def poll_campaign_emails(client: UnipileClient, account_id: str, campaign_id: str,
                         after: datetime, *, timeout: float,
                         interval: float) -> list[dict[str, Any]]:
    folder = inbox_folder(client, account_id)
    deadline = time.monotonic() + timeout
    found: dict[str, dict[str, Any]] = {}
    marker = f"[EXP4-5 {campaign_id}]"
    while time.monotonic() < deadline and len(found) < 3:
        for reference in client.list_emails(account_id, after=after, folder=folder):
            if marker not in str(reference.get("subject", "")):
                continue
            email_id = str(reference.get("id", ""))
            if email_id and email_id not in found:
                full = client.get_email(email_id)
                if str(full.get("role", reference.get("role", ""))).lower() == "sent":
                    continue
                found[email_id] = full
        if len(found) < 3:
            time.sleep(interval)
    if len(found) != 3:
        raise TimeoutError(f"received {len(found)} of three campaign emails before timeout")
    return sorted(found.values(), key=provider_date)


def official_schema_receipts(urls: list[str]) -> list[dict[str, Any]]:
    receipts = []
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for url in urls:
            try:
                response = client.get(url)
                receipts.append({"url": url, "status": response.status_code,
                                 "bytes": len(response.content),
                                 "sha256": sha256(response.content),
                                 "retrieved_at": datetime.now(UTC).isoformat()})
            except Exception as exc:
                receipts.append({"url": url, "status": None,
                                 "error_type": type(exc).__name__})
    return receipts


def bearer_diagnostic(client: UnipileClient) -> dict[str, Any]:
    """Preserve the rejected alternate auth probe without leaking its token."""
    started = time.perf_counter()
    try:
        response = httpx.get(
            client.base_url + "/api/v1/accounts",
            headers={"Authorization": "Bearer " + client.access_token,
                     "User-Agent": "ai-agent-book-experiment/4.4-diagnostic"},
            timeout=30,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        return {"method": "GET", "path": "/api/v1/accounts",
                "credential_scheme": "Authorization: Bearer <redacted>",
                "status": response.status_code,
                "error_type": payload.get("type"), "error_title": payload.get("title"),
                "response_sha256": sha256(response.content),
                "latency_seconds": round(time.perf_counter() - started, 3)}
    except Exception as exc:
        return {"method": "GET", "path": "/api/v1/accounts",
                "credential_scheme": "Authorization: Bearer <redacted>",
                "status": None, "error_type": type(exc).__name__,
                "latency_seconds": round(time.perf_counter() - started, 3)}


def derive_acceptance(events: list[dict[str, Any]], workflows: list[dict[str, Any]],
                      calls: list[dict[str, Any]], seed_receipts: list[dict[str, Any]],
                      *, credential_secret: str, dsn_secret: str) -> dict[str, Any]:
    by_class = {row.get("classification"): row for row in workflows}
    meeting = by_class.get("meeting_invitation", {})
    complaint = by_class.get("customer_complaint", {})
    marketing = by_class.get("marketing", {})
    encoded = canonical_json({"events": events, "workflows": workflows, "calls": calls})
    control_plane = canonical_json([{key: value for key, value in call.items()
                                     if key not in {"response_sha256"}}
                                    for call in calls])
    gates = {
        "three_real_inbound_unipile_events": (
            len(events) == 3 and all(
                event.get("source", {}).get("provider") == "unipile"
                and event.get("channel") == "unipile_mailbox_poll"
                and bool(event.get("provider_receipt_sha256")) for event in events
            )
        ),
        "fifo_event_queue": [event.get("sequence") for event in events] == [0, 1, 2]
                            and [row.get("sequence") for row in workflows] == [0, 1, 2],
        "exact_three_scenario_classifications": set(by_class) == {
            "meeting_invitation", "customer_complaint", "marketing"
        } and len(workflows) == 3,
        "meeting_calendar_checked_and_reply_drafted": (
            meeting.get("calendar_check", {}).get("performed") is True
            and meeting.get("calendar_check", {}).get("conflict") in {True, False}
            and meeting.get("draft", {}).get("disposition") in {"accept", "decline"}
            and meeting.get("draft", {}).get("bytes", 0) > 100
            and len(meeting.get("draft", {}).get("sha256", "")) == 64
        ),
        "complaint_extracted_and_high_priority_notification_delivered": (
            complaint.get("extracted", {}).get("requires_human_follow_up") is True
            and bool(complaint.get("extracted", {}).get("order_reference"))
            and complaint.get("notification", {}).get("priority") == "high"
            and complaint.get("notification", {}).get("delivered") is True
            and len(complaint.get("notification", {}).get("file_sha256", "")) == 64
        ),
        "marketing_archived_and_verified_through_provider": (
            marketing.get("archive", {}).get("update_object") == "EmailUpdated"
            and marketing.get("archive", {}).get("verified") is True
        ),
        "required_unipile_calls_succeeded": bool(calls) and all(
            call.get("success") is True for call in calls
        ),
        "three_seed_messages_sent_through_unipile": (
            len(seed_receipts) == 3 and all(isinstance(row, dict) for row in seed_receipts)
        ),
        "credentials_and_dsn_absent_from_receipts": (
            credential_secret not in encoded and dsn_secret not in encoded
        ),
        "no_simulation_markers_in_control_plane": not SIMULATION_PATTERN.search(control_plane),
    }
    return {"status": "passed" if all(gates.values()) else "failed", "gates": gates}


def build_manifest(campaign_dir: Path, summary: dict[str, Any]) -> dict[str, Any]:
    files = []
    for path in sorted(campaign_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            data = path.read_bytes()
            files.append({"path": str(path.relative_to(campaign_dir)),
                          "bytes": len(data), "sha256": sha256(data)})
    return {
        "experiment": "4-5", "campaign_id": summary.get("campaign_id"),
        "generated_at": datetime.now(UTC).isoformat(),
        "status": summary.get("status"),
        "official_complete": summary.get("status") == "passed",
        "files": files,
    }


def choose_account(accounts: list[dict[str, Any]], requested: str | None) -> dict[str, Any]:
    if requested:
        match = next((account for account in accounts if account.get("id") == requested), None)
        if not match:
            raise ValueError("requested account ID was not returned by Unipile")
        return match
    candidates = [account for account in accounts if
                  "mail" in canonical_json(account.get("sources", [])).lower()
                  or account_email(account)]
    if not candidates:
        raise RuntimeError("Unipile returned no mail-capable account")
    return candidates[0]


def run(args: argparse.Namespace) -> Path:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    campaign_id = args.campaign_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    campaign_dir = VALIDATION_ROOT / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=False)
    write_json(campaign_dir / "protocol.json", protocol)
    docs = official_schema_receipts(protocol["official_schema_sources"])
    dsn = os.getenv("UNIPILE_DSN", "")
    token = os.getenv("UNIPILE_ACCESS_TOKEN", "")
    summary: dict[str, Any] = {
        "experiment": "4-5", "campaign_id": campaign_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "provider": "unipile", "base_url_sha256": sha256(dsn) if dsn else None,
        "official_schema_receipts": docs,
    }
    client: UnipileClient | None = None
    try:
        client = UnipileClient(dsn, token)
        accounts = client.list_accounts()
        if args.preflight_only:
            summary.update({"status": "preflight_passed", "account_count": len(accounts),
                            "official_complete": False,
                            "account_receipts": [redacted(account) for account in accounts],
                            "api_calls": client.calls})
            write_json(campaign_dir / "summary.json", summary)
            return campaign_dir

        listen_account = choose_account(accounts, args.listen_account_id)
        sender_account = choose_account(accounts, args.sender_account_id) \
            if args.sender_account_id else listen_account
        calendar_account = choose_account(accounts, args.calendar_account_id) \
            if args.calendar_account_id else listen_account
        recipient = args.recipient or account_email(listen_account)
        if not recipient:
            raise RuntimeError("could not infer listener email; pass --recipient")
        started = datetime.now(UTC) - timedelta(minutes=1)
        seeds = seed_messages(client, str(sender_account["id"]), recipient, campaign_id)
        emails = poll_campaign_emails(
            client, str(listen_account["id"]), campaign_id, started,
            timeout=args.poll_timeout, interval=args.poll_interval,
        )
        experiment = MailboxExperiment(
            client, campaign_dir, str(listen_account["id"]), str(calendar_account["id"])
        )
        experiment.process_queue(emails)
        acceptance = derive_acceptance(
            experiment.events, experiment.workflows, client.calls, seeds,
            credential_secret=token, dsn_secret=dsn,
        )
        summary.update({
            "status": acceptance["status"], "listener": "unipile_mailbox_poll",
            "official_complete": acceptance["status"] == "passed",
            "account_receipts": {
                "listener": redacted(listen_account), "sender": redacted(sender_account),
                "calendar": redacted(calendar_account),
            },
            "seed_receipts": redacted(seeds), "events": experiment.events,
            "workflows": experiment.workflows, "api_calls": client.calls,
            "acceptance": acceptance,
        })
    except Exception as exc:
        credential_block = isinstance(exc, UnipileAPIError) and exc.status == 401
        if client and credential_block:
            summary["alternate_auth_diagnostic"] = bearer_diagnostic(client)
        summary.update({
            "status": "blocked" if credential_block or not dsn or not token else "failed",
            "official_complete": False,
            "blocker_or_error": {"type": type(exc).__name__, "message": str(exc)},
            "credentials_present": {"UNIPILE_DSN": bool(dsn),
                                    "UNIPILE_ACCESS_TOKEN": bool(token)},
            "api_calls": client.calls if client else [],
            "acceptance": {"status": "blocked" if credential_block or not dsn or not token else "failed", "gates": {
                "valid_unipile_credentials": False,
                "real_mailbox_campaign_completed": False,
            }},
        })
    finally:
        if client:
            client.close()
        write_json(campaign_dir / "summary.json", summary)
        write_json(campaign_dir / "manifest.json", build_manifest(campaign_dir, summary))
        write_json(VALIDATION_ROOT / "latest.json", {
            "experiment": "4-5", "campaign_id": campaign_id,
            "status": summary.get("status"),
            "official_complete": summary.get("status") == "passed",
            "manifest": str((campaign_dir / "manifest.json").relative_to(HERE)),
            "manifest_sha256": sha256((campaign_dir / "manifest.json").read_bytes()),
        })
    return campaign_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-id")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--recipient",
                        help="Listener mailbox address; inferred from account when omitted")
    parser.add_argument("--listen-account-id")
    parser.add_argument("--sender-account-id")
    parser.add_argument("--calendar-account-id")
    parser.add_argument("--poll-timeout", type=float, default=180)
    parser.add_argument("--poll-interval", type=float, default=5)
    args = parser.parse_args()
    path = run(args)
    print(path)


if __name__ == "__main__":
    main()
