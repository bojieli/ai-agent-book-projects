import unittest

from run_experiment_9_1 import build_evidence


class FakeClient:
    provider = "fake"
    model = "fake-model"
    base_url = "https://invalid.test/v1"
    credential_source_env = "FAKE_KEY"
    api_turns = [{"kind": "customer_service_agent"}, {"kind": "quality_judge"}]

    def usage_summary(self):
        return {"total_tokens": 2, "provider_reported_cost_usd": 0.0}


class RealCampaignAcceptanceTest(unittest.TestCase):
    def test_review_route_excludes_risky_case_from_learning(self):
        from verifier import TrajectoryVerifier

        trajectory = {
            "id": "privacy",
            "expected_outcome": {"order_status": "confirmed"},
            "final_state": {"order_status": "confirmed"},
            "messages": [{"turn": 2, "role": "assistant", "content": "tok_secret"}],
            "sensitive_values": [{"label": "token", "value": "tok_secret"}],
            "quality_facts": {},
        }
        report = TrajectoryVerifier().evaluate(trajectory)
        self.assertTrue(report["review"]["required"])
        self.assertFalse(report["eligible_as_automatic_learning_signal"])
        self.assertEqual("reject", report["release_recommendation"])


if __name__ == "__main__":
    unittest.main()
