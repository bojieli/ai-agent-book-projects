"""Focused tests for the Experiment 4-4 campaign controls."""

import json
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import hitl_tools
import subagent_tools

from run_experiment_4_4 import (
    SENSITIVE_ENV_NAMES,
    classify_status,
    human_decision_accepted,
    notification_readiness,
    parse_human_decision,
    publication_is_authorized,
    read_human_decision_line,
    redact_material,
    remaining_before_deadline,
    retain_human_decision,
)


class CampaignControlTests(unittest.TestCase):
    def test_parse_human_decision_accepts_explicit_choices(self) -> None:
        self.assertEqual(
            parse_human_decision("APPROVE: reviewed the scope"),
            (True, "reviewed the scope"),
        )
        self.assertEqual(
            parse_human_decision("reject"),
            (False, "No additional notes supplied by the live human operator."),
        )

    def test_parse_human_decision_rejects_ambiguous_input(self) -> None:
        for value in ("", "yes", "approved", "APPROVE later"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_human_decision(value)

    def test_notification_readiness_requires_every_channel_input(self) -> None:
        env = {
            "SMTP_USERNAME": "sender@example.test",
            "SMTP_PASSWORD": "smtp-secret",
            "HITL_ADMIN_EMAIL": "admin@example.test",
            "TELEGRAM_BOT_TOKEN": "telegram-secret",
            "TELEGRAM_DEFAULT_CHAT_ID": "12345",
            "SLACK_WEBHOOK_URL": "https://hooks.example.test/secret",
        }
        self.assertEqual(
            notification_readiness(env),
            {"email": True, "telegram": True, "slack": True},
        )
        env.pop("TELEGRAM_DEFAULT_CHAT_ID")
        self.assertFalse(notification_readiness(env)["telegram"])

    def test_sendgrid_readiness_requires_a_sender_identity(self) -> None:
        env = {
            "SENDGRID_API_KEY": "sendgrid-secret",
            "HITL_ADMIN_EMAIL": "admin@example.test",
        }
        self.assertFalse(notification_readiness(env)["email"])
        env["SMTP_FROM_EMAIL"] = "sender@example.test"
        self.assertTrue(notification_readiness(env)["email"])

    def test_redact_material_removes_credentials_and_delivery_identifiers(self) -> None:
        value = {
            "to": "admin@example.test",
            "nested": ["sent via token-secret", {"chat_id": "12345"}],
        }
        self.assertEqual(
            redact_material(
                value,
                ("admin@example.test", "token-secret", "12345"),
            ),
            {
                "to": "[REDACTED]",
                "nested": ["sent via [REDACTED]", {"chat_id": "[REDACTED]"}],
            },
        )

    def test_kimi_api_key_is_in_receipt_redaction_inputs(self) -> None:
        self.assertIn("KIMI_API_KEY", SENSITIVE_ENV_NAMES)

    def test_retained_human_decision_redacts_free_form_notes(self) -> None:
        secret = "kimi-secret-value"
        retained = retain_human_decision(
            {
                "request_id": "request-1",
                "approved": True,
                "admin_notes": f"approved with {secret}",
            },
            {
                "success": True,
                "request_id": "request-1",
                "approved": True,
                "admin_notes": f"approved with {secret}",
            },
            (secret,),
        )
        self.assertEqual(retained["admin_notes"], "approved with [REDACTED]")
        self.assertEqual(
            retained["mcp_result"]["admin_notes"],
            "approved with [REDACTED]",
        )

    def test_late_human_approval_does_not_authorize_publication(self) -> None:
        decision = {"request_id": "request-1", "approved": True}
        timed_out = {
            "success": True,
            "request_id": "request-1",
            "approved": False,
            "timeout": True,
        }
        self.assertFalse(human_decision_accepted(decision, timed_out))
        self.assertFalse(publication_is_authorized(decision, timed_out))

    def test_accepted_rejection_is_a_real_decision_but_not_publication_approval(self) -> None:
        decision = {"request_id": "request-1", "approved": False}
        rejected = {
            "success": True,
            "request_id": "request-1",
            "approved": False,
        }
        self.assertTrue(human_decision_accepted(decision, rejected))
        self.assertFalse(publication_is_authorized(decision, rejected))

    def test_interactive_human_failure_is_not_mislabeled_as_blocked(self) -> None:
        gates = {
            "core": True,
            "real_human_decision": False,
            "real_email_notification": False,
            "real_im_notification": False,
            "real_slack_notification": False,
        }
        self.assertEqual(
            classify_status(gates, interactive_human=True),
            "failed",
        )
        self.assertEqual(
            classify_status(gates, interactive_human=False),
            "blocked",
        )

    def test_retained_publication_authorization_matches_accepted_mcp_result(self) -> None:
        validation = Path(__file__).resolve().parent / "validation" / "experiment_4_4"
        expected = {
            "real_mcp_human_20260803_v1": False,
            "real_mcp_human_20260803_v2": True,
        }
        for campaign_id, authorized in expected.items():
            with self.subTest(campaign_id=campaign_id):
                run_dir = validation / campaign_id
                decision = json.loads(
                    (run_dir / "human_decision.json").read_text(encoding="utf-8")
                )
                summary = json.loads(
                    (run_dir / "summary.json").read_text(encoding="utf-8")
                )
                self.assertEqual(summary["publication_authorized"], authorized)
                self.assertEqual(
                    publication_is_authorized(decision, decision["mcp_result"]),
                    authorized,
                )


class HitlTerminalStateTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        hitl_tools._pending_requests.clear()

    async def asyncTearDown(self) -> None:
        hitl_tools._pending_requests.clear()

    async def test_late_response_cannot_change_timed_out_request(self) -> None:
        request_id = "expired-request"
        hitl_tools._pending_requests[request_id] = {
            "request_id": request_id,
            "status": "timeout",
        }
        result = await hitl_tools.respond_to_request(
            request_id,
            approved=True,
            admin_notes="late approval",
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["current_status"], "timeout")
        self.assertEqual(hitl_tools._pending_requests[request_id]["status"], "timeout")

    async def test_pending_request_accepts_one_terminal_decision(self) -> None:
        request_id = "pending-request"
        hitl_tools._pending_requests[request_id] = {
            "request_id": request_id,
            "status": "pending",
        }
        first = await hitl_tools.respond_to_request(
            request_id,
            approved=False,
            admin_notes="scope is too broad",
        )
        duplicate = await hitl_tools.respond_to_request(
            request_id,
            approved=True,
            admin_notes="changed later",
        )
        self.assertTrue(first["success"])
        self.assertFalse(first["approved"])
        self.assertFalse(duplicate["success"])
        self.assertEqual(duplicate["current_status"], "rejected")
        self.assertEqual(hitl_tools._pending_requests[request_id]["status"], "rejected")


class HumanInputTimeoutTests(unittest.IsolatedAsyncioTestCase):
    async def test_reads_one_available_line(self) -> None:
        read_descriptor, write_descriptor = os.pipe()
        try:
            os.write(write_descriptor, b"APPROVE: low risk\n")
            with os.fdopen(read_descriptor, encoding="utf-8") as stream:
                line = await read_human_decision_line(stream, 1)
            self.assertEqual(line, "APPROVE: low risk\n")
        finally:
            os.close(write_descriptor)

    async def test_times_out_without_leaving_a_blocked_read(self) -> None:
        read_descriptor, write_descriptor = os.pipe()
        try:
            with (
                os.fdopen(read_descriptor, encoding="utf-8") as stream,
                self.assertRaisesRegex(
                    RuntimeError,
                    "live human decision input timed out after 0.01 seconds",
                ),
            ):
                await read_human_decision_line(stream, 0.01)
        finally:
            os.close(write_descriptor)

    def test_shared_approval_deadline_rejects_an_expired_window(self) -> None:
        self.assertEqual(remaining_before_deadline(10, now=4), 6)
        with self.assertRaisesRegex(
            RuntimeError,
            "live human decision input timed out before presentation",
        ):
            remaining_before_deadline(10, now=10)


class SubagentTimestampTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        subagent_tools._subagents.clear()

    async def test_created_at_is_timezone_aware_utc(self) -> None:
        prepared = {
            "context_text": "test context",
            "context_tokens": 2,
            "prep_tokens": 0,
            "notes": "test",
        }
        turn = {"reply": "done", "prompt_tokens": 2, "total_tokens": 3}
        with (
            patch.object(subagent_tools, "_prepare_context", return_value=prepared),
            patch.object(subagent_tools, "_run_turn", return_value=turn),
        ):
            result = await subagent_tools.spawn_subagent("test task")
        created_at = datetime.fromisoformat(
            subagent_tools._subagents[result["subagent_id"]]["created_at"]
        )
        self.assertIsNotNone(created_at.utcoffset())
        self.assertEqual(created_at.utcoffset().total_seconds(), 0)


if __name__ == "__main__":
    unittest.main()
