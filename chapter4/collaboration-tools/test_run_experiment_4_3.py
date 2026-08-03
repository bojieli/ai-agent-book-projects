"""Focused tests for the Experiment 4-3 campaign controls."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import hitl_tools

from run_experiment_4_3 import (
    notification_readiness,
    parse_human_decision,
    redact_material,
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


if __name__ == "__main__":
    unittest.main()
