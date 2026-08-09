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


class TestSafetyPolicyGateSecretKey(unittest.TestCase):
    def test_init_with_parameter(self):
        gate = SafetyPolicyGate(secret_key="custom-param-key")
        self.assertEqual(gate.secret_key, "custom-param-key")

    @patch.dict(os.environ, {"SAFETY_GATE_SECRET_KEY": "env-secret-key"})
    def test_init_with_env_var(self):
        gate = SafetyPolicyGate()
        self.assertEqual(gate.secret_key, "env-secret-key")

    @patch.dict(os.environ, {}, clear=True)
    def test_init_with_default(self):
        gate = SafetyPolicyGate()
        self.assertEqual(gate.secret_key, "safety-gate-secret-key")


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


if __name__ == "__main__":
    unittest.main()
