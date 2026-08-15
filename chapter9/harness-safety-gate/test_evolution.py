import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from evolution import (
    STABLE,
    _load_gate,
    _replay_case,
    classify_risk,
    diagnose,
    generate_candidate,
    generate_rejected_control,
    release_manifest,
    validate_candidate,
)


ROOT = Path(__file__).parent


def _load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class DiagnosisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trajectories = _load("failure_trajectories.json")
        cls.diagnosis = diagnose(cls.trajectories)

    def test_support_threshold_creates_change_request(self):
        self.assertTrue(self.diagnosis["change_required"])
        cluster_ids = {p["cluster_id"] for p in self.diagnosis["patterns"]}
        self.assertEqual(
            {"unconfirmed_delete_file", "unconfirmed_force_push", "unconfirmed_destructive_sql"},
            cluster_ids,
        )
        for pattern in self.diagnosis["patterns"]:
            self.assertGreaterEqual(pattern["cross_trajectory_support"], 2)

    def test_below_threshold_cluster_is_ignored(self):
        # rm -rf 审计轨迹只有一条，低于支持门槛，不形成失败簇
        cluster_ids = {p["cluster_id"] for p in self.diagnosis["patterns"]}
        self.assertNotIn("unconfirmed_dangerous_shell", cluster_ids)

    def test_confirmed_operation_and_low_risk_feedback_excluded(self):
        source_ids = self.diagnosis["source_case_ids"]
        self.assertNotIn("traj-2026-0725-confirmed-delete", source_ids)
        self.assertNotIn("traj-2026-0724-thumb-write", source_ids)

    def test_signals_cover_all_three_sources(self):
        signals = {s for p in self.diagnosis["patterns"] for s in p["signals"]}
        self.assertEqual({"user_correction", "user_thumbs_down", "post_hoc_audit"}, signals)

    def test_root_cause_targets_dispatch_layer(self):
        self.assertEqual("stable/tool_dispatcher.py", self.diagnosis["target"])
        self.assertEqual("tool_dispatch_confirmation_gate", self.diagnosis["target_component"])

    def test_no_failure_means_no_change_request(self):
        result = diagnose([
            {"id": "ok-1", "signal": "post_hoc_audit", "outcome": "ok",
             "tool_calls": [{"tool": "delete_file", "args": {"path": "a"}, "user_confirmed": True}]},
        ])
        self.assertFalse(result["change_required"])
        self.assertIsNone(result["target"])


class RiskClassifierTest(unittest.TestCase):
    def test_high_risk_calls_are_flagged(self):
        high_risk = [
            ("delete_file", {"path": "reports/2026-Q1-draft.docx"}),
            ("delete_file", {"path": "tmp/cache-0417.tmp"}),
            ("git_push", {"remote": "origin", "branch": "main", "force": True}),
            ("sql_query", {"query": "DROP TABLE users"}),
            ("sql_query", {"query": "TRUNCATE TABLE orders"}),
            ("sql_query", {"query": "DELETE FROM orders"}),
            ("run_shell", {"command": "rm -rf build/"}),
        ]
        for tool, args in high_risk:
            kind, reason = classify_risk(tool, args)
            self.assertIsNotNone(kind, f"{tool} {args} 应判为高风险")
            self.assertTrue(reason)

    def test_low_risk_calls_pass_through(self):
        low_risk = [
            ("read_file", {"path": "a.md"}),
            ("write_file", {"path": "a.md", "content": "x"}),
            ("git_push", {"remote": "origin", "branch": "main", "force": False}),
            ("sql_query", {"query": "SELECT * FROM users"}),
            ("sql_query", {"query": "DELETE FROM users WHERE id = 2"}),
            ("run_shell", {"command": "ls -la"}),
        ]
        for tool, args in low_risk:
            kind, _ = classify_risk(tool, args)
            self.assertIsNone(kind, f"{tool} {args} 应判为低风险")


class CandidateGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trajectories = _load("failure_trajectories.json")
        cls.boundary = _load("boundary_cases.json")
        cls.retention = _load("retention_cases.json")
        cls.stable = (ROOT / "stable" / "tool_dispatcher.py").read_text(encoding="utf-8")
        cls.diagnosis = diagnose(cls.trajectories)
        cls.candidate = generate_candidate(cls.stable, cls.diagnosis)
        cls.gate = _load_gate(cls.candidate["source"])

    def test_candidate_passes_all_gates(self):
        checks = validate_candidate(self.candidate["source"], self.boundary, self.retention)
        self.assertTrue(all(checks.values()), checks)

    def test_candidate_classifier_matches_reference(self):
        self.assertTrue(self.gate["requires_confirmation"]("delete_file", {"path": "x"}))
        self.assertTrue(self.gate["requires_confirmation"]("git_push", {"force": True}))
        self.assertTrue(self.gate["requires_confirmation"]("sql_query", {"query": "DROP TABLE t"}))
        self.assertTrue(self.gate["requires_confirmation"]("sql_query", {"query": "DELETE FROM t"}))
        self.assertFalse(self.gate["requires_confirmation"]("read_file", {"path": "x"}))
        self.assertFalse(self.gate["requires_confirmation"]("sql_query", {"query": "DELETE FROM t WHERE id=1"}))
        self.assertFalse(self.gate["requires_confirmation"]("git_push", {"force": False}))

    def test_token_is_single_use_and_bound_to_operation(self):
        env = STABLE.default_env()
        calls = []

        def execute(name, call_args):
            calls.append(name)
            return STABLE.dispatch(name, call_args, env=env)

        gate = self.gate
        token = gate["issue_confirmation"]("delete_file", {"path": "tmp/cache-0417.tmp"})
        first = gate["dispatch"]("delete_file", {"path": "tmp/cache-0417.tmp"},
                                 execute=execute, confirm_token=token)
        self.assertEqual("executed", first["status"])
        # 同一 token 第二次使用：必须拒绝且不得执行
        second = gate["dispatch"]("delete_file", {"path": "tmp/cache-0417.tmp"},
                                  execute=execute, confirm_token=token)
        self.assertEqual("rejected", second["status"])
        # 同一 token 换操作：同样拒绝
        third = gate["dispatch"]("delete_file", {"path": "notes/todo.md"},
                                 execute=execute, confirm_token=token)
        self.assertEqual("rejected", third["status"])
        self.assertEqual(1, len(calls))
    def test_generate_synthetic_perturbations_creates_edge_cases(self):
        from evolution import generate_synthetic_perturbations
        sample = [{"id": "t1", "tool_name": "delete_file", "args": {"path": "/tmp/a"}}]
        perturbed = generate_synthetic_perturbations(sample)
        self.assertEqual(3, len(perturbed))
        self.assertIsNone(perturbed[0]["args"])
        self.assertEqual("  ", perturbed[1]["tool_name"])
        self.assertIsInstance(perturbed[2]["args"], list)

    def test_suspended_call_never_reaches_executor(self):
        case = self.boundary[0]  # 第六章实验 6-5 的"高风险删除前确认"场景
        passed, detail = _replay_case(self.gate, case)
        self.assertTrue(passed, detail)

    def test_release_accepts_good_candidate(self):
        checks = validate_candidate(self.candidate["source"], self.boundary, self.retention)
        manifest = release_manifest(self.stable, self.candidate, self.diagnosis, checks)
        self.assertEqual("release_to_canary", manifest["decision"])
        self.assertEqual(manifest["stable_sha256"], manifest["rollback_sha256"])
        self.assertTrue(manifest["failure_cluster"])
        self.assertTrue(manifest["source_trajectories"])
        self.assertTrue(manifest["integration_diff"])

    def test_release_rejects_when_any_gate_fails(self):
        checks = {"static_compile": True, "security_scan": True, "gate_contract": True,
                  "boundary_replay": False, "retention_replay": True, "confirmation_single_use": True}
        manifest = release_manifest(self.stable, self.candidate, self.diagnosis, checks)
        self.assertEqual("reject_candidate", manifest["decision"])
        self.assertIn("boundary_replay", manifest["failed_checks"])

    def test_rejected_control_fails_boundary_replay(self):
        rejected = generate_rejected_control(self.stable, self.diagnosis)
        checks = validate_candidate(rejected["source"], self.boundary, self.retention)
        self.assertFalse(checks["boundary_replay"])
        manifest = release_manifest(self.stable, rejected, self.diagnosis, checks)
        self.assertEqual("reject_candidate", manifest["decision"])
        self.assertTrue(manifest["rejection_reason"])

    def test_degenerate_candidate_is_rejected_without_crashing(self):
        for source in ("", "\n", "# 只有注释\n"):
            checks = validate_candidate(source, self.boundary, self.retention)
            self.assertFalse(all(checks.values()))
        checks = validate_candidate("\ud800", self.boundary, self.retention)
        self.assertFalse(all(checks.values()))

    def test_unsafe_candidate_is_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "marker"
            unsafe = (
                "import os\n"
                f"os.system('touch {marker}')\n"
                "def requires_confirmation(tool_name, args=None):\n    return False\n"
                "def issue_confirmation(tool_name, args=None):\n    return 'x'\n"
                "def dispatch(tool_name, args=None, *, execute, confirm_token=None):\n"
                "    return {'status': 'executed', 'result': execute(tool_name, args)}\n"
            )
            checks = validate_candidate(unsafe, self.boundary, self.retention)
            self.assertTrue(checks["static_compile"])
            self.assertFalse(checks["security_scan"])
            self.assertFalse(marker.exists())

    def test_stable_hash_unchanged_through_pipeline(self):
        stable_path = ROOT / "stable" / "tool_dispatcher.py"
        before = hashlib.sha256(stable_path.read_bytes()).hexdigest()
        generate_candidate(self.stable, self.diagnosis)
        generate_rejected_control(self.stable, self.diagnosis)
        validate_candidate(self.candidate["source"], self.boundary, self.retention)
        after = hashlib.sha256(stable_path.read_bytes()).hexdigest()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
