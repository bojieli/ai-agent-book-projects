"""
Unit tests for Safety Policy Gate module.
"""

import os
import unittest
from datetime import datetime
from unittest.mock import patch

from safety_policy_gate import SafetyPolicyGate, validate_tool_call


class TestSafetyPolicyGateSQL(unittest.TestCase):
    def setUp(self):
        self.gate = SafetyPolicyGate()

    def test_sql_delete_without_where_is_high_risk(self):
        decision = self.gate.validate_tool_call("sql_query", {"query": "DELETE FROM users"})
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)
        self.assertEqual(decision.violation_type, "unconfirmed_high_risk_operation")

    def test_sql_delete_with_where_is_low_risk(self):
        decision = self.gate.validate_tool_call("sql_query", {"query": "DELETE FROM users WHERE id = 1"})
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_confirmation)

    def test_sql_delete_multi_statement_bypass(self):
        # WHERE is in second statement, first statement has no WHERE
        query = "DELETE FROM users; SELECT * FROM logs WHERE id = 1"
        decision = self.gate.validate_tool_call("sql_query", {"query": query})
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)

    def test_sql_delete_comment_bypass_single_line(self):
        # WHERE is in comment
        query = "DELETE FROM users -- WHERE id = 1"
        decision = self.gate.validate_tool_call("sql_query", {"query": query})
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)

    def test_sql_delete_comment_bypass_multi_line(self):
        # WHERE is inside block comment
        query = "DELETE FROM users /* WHERE id = 1 */"
        decision = self.gate.validate_tool_call("sql_query", {"query": query})
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)

    def test_sql_drop_table_is_high_risk(self):
        query = "SELECT 1; DROP TABLE users"
        decision = self.gate.validate_tool_call("sql_query", {"query": query})
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)
    def test_sql_multi_statement_second_delete_no_where(self):
        query = "UPDATE users SET status = 1; DELETE FROM logs"
        decision = self.gate.validate_tool_call("sql_query", {"query": query})
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)

    def test_sql_block_comment_before_single_line_comment(self):
        query = "DELETE FROM users /* block -- comment */ WHERE id = 1"
        decision = self.gate.validate_tool_call("sql_query", {"query": query})
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_confirmation)


class TestSafetyPolicyGatePathTraversal(unittest.TestCase):
    def setUp(self):
        self.gate = SafetyPolicyGate()

    def test_double_url_unquoting_path_traversal(self):
        # %252e%252e resolves to ..
        params = {"path": "folder/%252e%252e/etc/passwd"}
        decision = self.gate.validate_tool_call("read_file", params)
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.triggered_rollback)
        self.assertEqual(decision.violation_type, "path_traversal")

    def test_double_url_unquoting_sensitive_dir(self):
        # %252fetc%252fpasswd resolves to /etc/passwd
        params = {"filepath": "%252fetc%252fpasswd"}
        decision = self.gate.validate_tool_call("read_file", params)
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.triggered_rollback)
        self.assertEqual(decision.violation_type, "path_traversal")

    def test_realpath_path_traversal(self):
        params = {"file_path": "/tmp/../etc/passwd"}
        decision = self.gate.validate_tool_call("read_file", params)
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.triggered_rollback)
        self.assertEqual(decision.violation_type, "path_traversal")

    def test_relative_path_not_falsely_flagged(self):
        # A legitimate relative path that happens to share a name component with a
        # sensitive directory must NOT be flagged after CWD resolution.
        decision = self.gate.validate_tool_call("read_file", {"path": "etc/config"})
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.triggered_rollback)

    def test_relative_path_subdir_not_falsely_flagged(self):
        decision = self.gate.validate_tool_call("read_file", {"path": "proc/stats.txt"})
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.triggered_rollback)


class TestSafetyPolicyGateSecretKey(unittest.TestCase):
    def test_init_with_parameter(self):
        gate = SafetyPolicyGate(secret_key="custom-param-key")
        self.assertEqual(gate.secret_key, "custom-param-key")

    @patch.dict(os.environ, {"SAFETY_GATE_SECRET_KEY": "env-secret-key"})
    def test_init_with_env_var(self):
        gate = SafetyPolicyGate()
        self.assertEqual(gate.secret_key, "env-secret-key")

    @patch.dict(os.environ, {}, clear=True)
    def test_init_with_default_generates_random_secret(self):
        gate = SafetyPolicyGate()
        # No hardcoded default: a random 32-byte secret is generated per instance
        self.assertIsInstance(gate.secret_key, bytes)
        self.assertEqual(len(gate.secret_key), 32)
        gate2 = SafetyPolicyGate()
        self.assertNotEqual(gate.secret_key, gate2.secret_key)


class TestSafetyPolicyGateConfirmation(unittest.TestCase):
    def setUp(self):
        self.gate = SafetyPolicyGate()

    def test_confirmation_token_lifecycle(self):
        params = {"path": "important.txt"}
        decision1 = self.gate.validate_tool_call("delete_file", params)
        self.assertFalse(decision1.allowed)
        self.assertTrue(decision1.requires_confirmation)
        token = decision1.confirmation_token
        self.assertIsNotNone(token)

        # Confirm with token
        decision2 = self.gate.validate_tool_call("delete_file", params, confirm_token=token)
        self.assertTrue(decision2.allowed)

        # Token is single-use and cannot be reused
        decision3 = self.gate.validate_tool_call("delete_file", params, confirm_token=token)
        self.assertFalse(decision3.allowed)

    def test_confirm_token_in_params(self):
        params = {"path": "important.txt"}
        decision1 = self.gate.validate_tool_call("delete_file", params)
        token = decision1.confirmation_token

        # Submit token inside params dictionary
        params_with_token = {"path": "important.txt", "confirm_token": token}
        decision2 = self.gate.validate_tool_call("delete_file", params_with_token)
        self.assertTrue(decision2.allowed)

    def test_params_user_confirmed_not_trusted(self):
        # Untrusted LLM params with user_confirmed: True should NOT bypass confirmation
        params = {"path": "important.txt", "user_confirmed": True}
        decision = self.gate.validate_tool_call("delete_file", params)
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)

    def test_non_serializable_params_handled(self):
        params = {"path": "important.txt", "set_param": {1, 2, 3}, "date_param": datetime.now()}
        decision = self.gate.validate_tool_call("delete_file", params)
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)
    def test_token_nondeterministic(self):
        params = {"path": "file.txt"}
        token1 = self.gate.issue_confirmation("delete_file", params)
        token2 = self.gate.issue_confirmation("delete_file", params)
        self.assertNotEqual(token1, token2)

    def test_tool_name_casing_normalization(self):
        params = {"path": "file.txt"}
        decision1 = self.gate.validate_tool_call("DELETE_FILE", params)
        self.assertFalse(decision1.allowed)
        self.assertTrue(decision1.requires_confirmation)

        decision2 = self.gate.validate_tool_call("BASH", {"command": "rm -rf /"})
        self.assertFalse(decision2.allowed)
        self.assertEqual(decision2.violation_type, "dangerous_bash_command")

        decision3 = self.gate.validate_tool_call("SQL_QUERY", {"query": "DELETE FROM users"})
        self.assertFalse(decision3.allowed)
        self.assertTrue(decision3.requires_confirmation)

    def test_expired_token_rejected(self):
        # Tokens past their TTL are rejected and cleaned up
        gate = SafetyPolicyGate(token_ttl=0.0)
        params = {"path": "file.txt"}
        token = gate.issue_confirmation("delete_file", params)
        import time as _time
        _time.sleep(0.01)
        self.assertFalse(gate.verify_confirmation(token, "delete_file", params))
        # Expired token was removed from pending set
        self.assertNotIn(token, gate._pending_confirmations)

    def test_expired_tokens_cleaned_on_issue(self):
        gate = SafetyPolicyGate(token_ttl=0.0)
        params = {"path": "file.txt"}
        token = gate.issue_confirmation("delete_file", params)
        import time as _time
        _time.sleep(0.01)
        # Issuing a new token triggers cleanup of the expired one
        token2 = gate.issue_confirmation("delete_file", params)
        self.assertNotIn(token, gate._pending_confirmations)
        self.assertIn(token2, gate._pending_confirmations)


class TestSafetyPolicyGateRollback(unittest.TestCase):
    def setUp(self):
        self.gate = SafetyPolicyGate()

    def test_trigger_rollback_success(self):
        called = []
        self.gate.register_rollback_handler(lambda: called.append(True))
        res = self.gate.trigger_rollback()
        self.assertTrue(res)
        self.assertEqual(called, [True])

    def test_trigger_rollback_failure(self):
        def failing_handler():
            raise RuntimeError("Rollback failed")
        self.gate.register_rollback_handler(failing_handler)
        res = self.gate.trigger_rollback()
        self.assertFalse(res)

    def test_rollback_failed_violation_type(self):
        def failing_handler():
            raise RuntimeError("Rollback failed")
        self.gate.register_rollback_handler(failing_handler)
        decision = self.gate.validate_tool_call("read_file", {"path": "../etc/passwd"})
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.triggered_rollback)
        self.assertEqual(decision.violation_type, "rollback_failed")
        self.assertFalse(decision.details["rollback_success"])


if __name__ == "__main__":
    unittest.main()
