"""Falsify real pilot traces to check that the acceptance criteria reject them.

These tests make no API calls and do not simulate evidence of model capability.
"""

import copy
import json
from pathlib import Path
import unittest

from experiment import judge

PILOT = Path(__file__).parent / "validation/runs/pilot-20260905-v2"


def read(arm):
    return [json.loads(line) for line in (PILOT / f"01-{arm}/events.jsonl").read_text().splitlines()]


def rewrite_final(rows, key, value):
    completed = [r for r in rows if r["event"].get("type") == "response.completed"]
    parts = completed[-1]["event"]["response"]["output"]
    for item in parts:
        if item.get("type") == "message":
            for part in item["content"]:
                if part.get("type") == "output_text":
                    text = part["text"]
                    start, end = text.index("{"), text.rindex("}") + 1
                    answer = json.loads(text[start:end])
                    answer[key] = value
                    part["text"] = json.dumps(answer)


class EvidenceTests(unittest.TestCase):
    def test_real_pilot_satisfies_stricter_judge(self):
        for arm in ("sync", "async", "steer_reasoning", "async_steer", "unsupported_steer"):
            with self.subTest(arm=arm):
                model = "gpt-5.6-sol" if arm == "unsupported_steer" else "gpt-6-astra"
                self.assertTrue(judge(read(arm), arm, model)["passed"])

    def test_accepted_without_successor_is_not_success(self):
        rows = read("steer_reasoning")
        ack = next(r["index"] for r in rows if r["event"].get("type") == "response.steer.accepted")
        self.assertFalse(judge([r for r in rows if r["index"] <= ack], "steer_reasoning", "gpt-6-astra")["passed"])

    def test_wrong_call_id_fails(self):
        rows = read("async")
        for r in rows:
            if r["direction"] == "client" and r["event"].get("previous_response_id"):
                r["event"]["input"][0]["call_id"] = "wrong_call"
        self.assertFalse(judge(rows, "async", "gpt-6-astra")["passed"])

    def test_duplicate_delivery_fails(self):
        rows = read("async")
        for r in rows:
            if r["direction"] == "client" and r["event"].get("previous_response_id"):
                r["event"]["input"].append(copy.deepcopy(r["event"]["input"][0]))
        self.assertFalse(judge(rows, "async", "gpt-6-astra")["passed"])

    def test_invented_receipt_fails(self):
        rows = read("async")
        rewrite_final(rows, "receipt", "invented")
        self.assertFalse(judge(rows, "async", "gpt-6-astra")["passed"])

    def test_old_budget_fails(self):
        rows = read("async_steer")
        rewrite_final(rows, "budget", 2000)
        self.assertFalse(judge(rows, "async_steer", "gpt-6-astra")["passed"])

    def test_wrong_model_fails_even_for_negative_control(self):
        self.assertFalse(judge(read("unsupported_steer"), "unsupported_steer", "gpt-6-astra")["passed"])

    def test_quota_failure_is_not_capability_rejection(self):
        rows = read("unsupported_steer")
        for r in rows:
            if r["event"].get("type") == "response.steer.failed":
                r["event"]["error"]["code"] = "credit_balance_exhausted"
        self.assertFalse(judge(rows, "unsupported_steer", "gpt-5.6-sol")["passed"])

    def test_stale_parent_for_result_fails(self):
        rows = read("async_steer")
        original = next(r["event"]["response"]["id"] for r in rows if r["event"].get("type") == "response.created")
        for r in rows:
            if r["direction"] == "client" and r["event"].get("type") == "response.create" and r["event"].get("previous_response_id"):
                r["event"]["previous_response_id"] = original
        self.assertFalse(judge(rows, "async_steer", "gpt-6-astra")["passed"])

    def test_no_output_during_execution_fails(self):
        rows = read("async")
        rows = [r for r in rows if r["event"].get("type") != "response.output_text.delta"]
        self.assertFalse(judge(rows, "async", "gpt-6-astra")["passed"])


if __name__ == "__main__":
    unittest.main()
