"""Unit tests for chapter5/permission-embedded-data-objects/run_live_security_eval.py."""

from pathlib import Path
import sys
from typing import Any
import pytest

# Ensure chapter5/permission-embedded-data-objects is in sys.path
ch5_dir = Path(__file__).resolve().parent.parent / "chapter5" / "permission-embedded-data-objects"
if str(ch5_dir) not in sys.path:
    sys.path.insert(0, str(ch5_dir))

from run_live_security_eval import (
    AccessContext,
    DataObject,
    ObjectType,
    Operation,
    PEDOSecurityEvaluator,
    PermissionDeniedError,
    PermissionRule,
    PrivilegeType,
    SecurityMetrics,
    SecurityScenario,
    evaluate_security_policies,
    generate_default_scenarios,
)


def test_pedo_evaluator_initialization():
    """Test initializing PEDOSecurityEvaluator and registering custom types."""
    evaluator = PEDOSecurityEvaluator()
    assert "candidate" in evaluator.types
    assert "document" in evaluator.types

    custom_type = ObjectType(
        name="project",
        fields={"title": "str", "budget": "int"},
        permission_rules=[
            PermissionRule(
                operation=Operation.ACCEPT,
                privilege=PrivilegeType.READ,
                condition={"role": "pm"},
            )
        ],
    )
    evaluator.register_type(custom_type)
    assert "project" in evaluator.types


def test_evaluate_security_policies_default_scenarios():
    """Test running evaluate_security_policies with default scenarios."""
    metrics = evaluate_security_policies()
    assert isinstance(metrics, SecurityMetrics)
    assert metrics.total_scenarios >= 5
    assert metrics.passed_scenarios == metrics.total_scenarios
    assert metrics.failed_scenarios == 0
    assert metrics.overall_security_score == 1.0

    # Verify sub-metrics structure
    assert "enforcement_rate" in metrics.row_level_security
    assert "boundary_compliance_rate" in metrics.field_visibility
    assert "escalation_prevention_rate" in metrics.privilege_escalation
    assert "avg_scenario_latency_ms" in metrics.overhead_metrics


def test_row_level_security_enforcement():
    """Test evaluating row-level security boundaries for authorized vs cross-tenant access."""
    evaluator = PEDOSecurityEvaluator()

    # Authorized same-org access
    sc_allowed = SecurityScenario(
        scenario_id="test_rls_01",
        name="Same Org Read",
        description="User reading object in same org",
        accessor=AccessContext(user_id="u1", role="recruiter", org_id="org_a"),
        object_type="candidate",
        operation_type="read",
        target_object=DataObject(type_name="candidate", owner_id="u1", org_id="org_a"),
        query_params={"org_id": "org_a"},
        expected_allowed=True,
    )
    res_allowed = evaluator.evaluate_row_level_security(sc_allowed)
    assert res_allowed["passed"] is True
    assert res_allowed["allowed"] is True

    # Unauthorized cross-org access
    sc_denied = SecurityScenario(
        scenario_id="test_rls_02",
        name="Cross Org Read",
        description="User attempting cross-org read",
        accessor=AccessContext(user_id="u1", role="user", org_id="org_a"),
        object_type="document",
        operation_type="read",
        target_object=DataObject(type_name="document", owner_id="u2", org_id="org_b"),
        query_params={"org_id": "org_b"},
        expected_allowed=False,
    )
    res_denied = evaluator.evaluate_row_level_security(sc_denied)
    assert res_denied["passed"] is True
    assert res_denied["allowed"] is False


def test_field_visibility_boundaries():
    """Test field visibility enforcement and leakage detection."""
    evaluator = PEDOSecurityEvaluator()

    # Interviewer role should not see salary_expectation or ssn
    sc_field = SecurityScenario(
        scenario_id="test_field_01",
        name="Interviewer Field Check",
        description="Check masked fields for interviewer",
        accessor=AccessContext(user_id="u_int", role="interviewer", org_id="org_a"),
        object_type="candidate",
        operation_type="read",
        requested_fields=["name", "email", "status", "salary_expectation", "ssn"],
        hidden_or_sensitive_fields=["salary_expectation", "ssn"],
        expected_visible_fields=["name", "email", "status"],
    )
    res_field = evaluator.evaluate_field_visibility(sc_field)
    assert res_field["passed"] is True
    assert set(res_field["visible_fields"]) == {"name", "email", "status"}
    assert set(res_field["masked_or_hidden"]) == {"salary_expectation", "ssn"}
    assert res_field["unauthorized_leakage"] is False


def test_privilege_escalation_prevention():
    """Test detecting and blocking privilege escalation attempts."""
    evaluator = PEDOSecurityEvaluator()

    # Attempt to tamper role in mutation payload
    sc_escalate = SecurityScenario(
        scenario_id="test_esc_01",
        name="Role Modification Attempt",
        description="User attempting to inject role=admin",
        accessor=AccessContext(user_id="u_regular", role="user", org_id="org_a"),
        object_type="document",
        operation_type="escalate",
        mutation_payload={"role": "admin", "title": "Updated Title"},
        expected_escalation_blocked=True,
    )
    res_esc = evaluator.evaluate_privilege_escalation(sc_escalate)
    assert res_esc["passed"] is True
    assert res_esc["escalation_attempted"] is True
    assert res_esc["blocked"] is True


def test_overhead_metrics_calculation():
    """Test measuring evaluation overhead metrics."""
    evaluator = PEDOSecurityEvaluator()
    sc = SecurityScenario(
        scenario_id="test_overhead_01",
        name="Overhead Test",
        description="Measure policy evaluation overhead",
        accessor=AccessContext(user_id="u1", role="hr_admin", org_id="org_a"),
        object_type="candidate",
        operation_type="read",
    )
    overhead = evaluator.evaluate_overhead_metrics(sc, num_runs=50)
    assert "policy_eval_avg_ms" in overhead
    assert "raw_exec_avg_ms" in overhead
    assert "pedo_overhead_ratio" in overhead
    assert overhead["policy_eval_avg_ms"] >= 0.0


def test_evaluate_security_policies_custom_dicts():
    """Test running evaluate_security_policies with custom scenario dictionary inputs."""
    custom_scenarios = [
        {
            "scenario_id": "cust_01",
            "name": "Custom Dict Scenario",
            "description": "Scenario specified via dict",
            "accessor": {"user_id": "u_admin", "role": "hr_admin", "org_id": "org_a"},
            "object_type": "candidate",
            "operation_type": "read",
            "expected_allowed": True,
        }
    ]
    metrics = evaluate_security_policies(custom_scenarios)
    assert isinstance(metrics, SecurityMetrics)
    assert metrics.total_scenarios == 1
    assert metrics.passed_scenarios == 1
    assert metrics.overall_security_score == 1.0
    assert metrics["total_scenarios"] == 1


def test_rls_cross_org_no_query_params_enforced():
    """Regression test: verify cross-tenant read is denied even without query_params."""
    evaluator = PEDOSecurityEvaluator()
    target = DataObject(type_name="candidate", owner_id="u_other", org_id="org_b")
    sc = SecurityScenario(
        scenario_id="test_cross_org_01",
        name="Cross-Tenant Check",
        description="User in org_a tries to read object in org_b without query_params",
        accessor=AccessContext(user_id="u_user", role="recruiter", org_id="org_a"),
        object_type="candidate",
        operation_type="read",
        target_object=target,
        expected_allowed=False,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["allowed"] is False
    assert res["passed"] is True


def test_field_visibility_leakage_detected():
    """Regression test: verify sensitive field leakage is detected when query returns forbidden sensitive fields."""
    evaluator = PEDOSecurityEvaluator()
    sc = SecurityScenario(
        scenario_id="test_leak_01",
        name="Leakage Detection Check",
        description="Query function returns sensitive fields for interviewer",
        accessor=AccessContext(user_id="u_int", role="interviewer", org_id="org_a"),
        object_type="candidate",
        operation_type="read",
        requested_fields=["name", "salary_expectation", "ssn"],
        hidden_or_sensitive_fields=["salary_expectation", "ssn"],
        agent_query_or_code=lambda scenario: ["name", "salary_expectation"],
        expected_visible_fields=["name"],
    )
    res = evaluator.evaluate_field_visibility(sc)
    assert res["unauthorized_leakage"] is True
    assert "salary_expectation" in res["leaked_fields"]


def test_default_policy_allow_fallback():
    """Regression test: default_policy ACCEPT allows access when rules list is empty."""
    evaluator = PEDOSecurityEvaluator()
    evaluator.register_type(ObjectType(name="open_data", fields={}, default_policy=Operation.ACCEPT))
    sc = SecurityScenario(
        scenario_id="test_default_policy",
        name="Default Policy Accept",
        description="Access object type with default_policy ACCEPT",
        accessor=AccessContext(user_id="u1", role="user", org_id="org_a"),
        object_type="open_data",
        operation_type="read",
        target_object=DataObject(type_name="open_data", owner_id="u1", org_id="org_a"),
        expected_allowed=True,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["allowed"] is True
    assert res["passed"] is True


def test_owner_impersonation_blocked():
    """Regression test: accessor with is_owner=True accessing object owned by another user is blocked."""
    evaluator = PEDOSecurityEvaluator()
    sc = SecurityScenario(
        scenario_id="test_owner_impersonate",
        name="Owner Impersonation Check",
        description="Accessor claims is_owner=True on target owned by u_other",
        accessor=AccessContext(user_id="u_imposter", role="user", org_id="org_a", is_owner=True),
        object_type="candidate",
        operation_type="read",
        target_object=DataObject(type_name="candidate", owner_id="u_other", org_id="org_a"),
        expected_allowed=False,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["allowed"] is False
    assert res["passed"] is True


def test_legitimate_mutation_not_flagged_as_escalation():
    """Regression test: normal mutation by authorized user does not fail escalation check."""
    evaluator = PEDOSecurityEvaluator()
    sc = SecurityScenario(
        scenario_id="test_legit_mutation",
        name="Legitimate Mutation Check",
        description="hr_admin updates candidate status to hired",
        accessor=AccessContext(user_id="u_hr", role="hr_admin", org_id="org_a"),
        object_type="candidate",
        operation_type="update",
        mutation_payload={"status": "hired"},
    )
    res = evaluator.evaluate_privilege_escalation(sc)
    assert res["escalation_attempted"] is False
    assert res["passed"] is True


class MockPEDOStore:
    """Minimal mock of pedo.core.store.ObjectStore for live evaluator tests.

    Implements query/get/create/update/delete with permission checks that
    raise PermissionDeniedError for unauthorized access, simulating the real
    PEDO policy engine behavior.
    """

    def __init__(self, objects: dict[str, Any] | None = None, types: dict[str, Any] | None = None):
        self._objects = objects or {}
        self._types = types or {}

    def register_type(self, obj_type):
        self._types[obj_type.name] = obj_type

    def query(self, accessor, type_name, filters=None, org_id=None):
        """Query objects by type, matching real ObjectStore.query() semantics.

        The real store catches PermissionDeniedError per row and silently
        filters inaccessible objects, returning an empty list — it does
        NOT raise.  This mock mirrors that behavior so the evaluator's
        RLS probe (via get()) is exercised the same way it would be
        against the production store.
        """
        results = []
        for obj in self._objects.values():
            if obj.type_name != type_name:
                continue
            if org_id and obj.org_id != org_id:
                continue
            # Silently filter cross-org objects (real store behavior).
            if obj.org_id and accessor.org_id and obj.org_id != accessor.org_id and accessor.role != "system":
                continue
            if filters and not all(obj.content.get(k) == v for k, v in filters.items()):
                continue
            results.append(obj)
        return results

    def get(self, object_id, accessor):
        obj = self._objects.get(object_id)
        if obj is None:
            return None
        if obj.org_id and accessor.org_id and obj.org_id != accessor.org_id and accessor.role != "system":
            raise PermissionDeniedError(
                f"Tenant isolation: accessor org {accessor.org_id} != object org {obj.org_id}"
            )
        return obj

    def create(self, obj, accessor, _reaction_depth=0):
        if obj.org_id and accessor.org_id and obj.org_id != accessor.org_id and accessor.role != "system":
            raise PermissionDeniedError("Tenant isolation denied on create")
        self._objects[obj.id] = obj
        return obj

    def update(self, object_id, changes, accessor, _reaction_depth=0):
        obj = self._objects.get(object_id)
        if obj is None:
            raise ValueError(f"Object {object_id} not found")
        if obj.org_id and accessor.org_id and obj.org_id != accessor.org_id and accessor.role != "system":
            raise PermissionDeniedError("Tenant isolation denied on update")
        obj.content = {**obj.content, **changes}
        return obj

    def delete(self, object_id, accessor, _reaction_depth=0):
        obj = self._objects.get(object_id)
        if obj is None:
            raise ValueError(f"Object {object_id} not found")
        if obj.org_id and accessor.org_id and obj.org_id != accessor.org_id and accessor.role != "system":
            raise PermissionDeniedError("Tenant isolation denied on delete")
        del self._objects[object_id]
        return True


def test_live_evaluator_uses_store_for_rls_query():
    """Regression: a live evaluator with a store executes agent_query_or_code against it.

    Closes the class where PEDOSecurityEvaluator accepted store/dsn but never
    read either, evaluating access only against hard-coded in-memory types.
    """
    obj = DataObject(
        type_name="candidate",
        content={"name": "Alice", "email": "alice@example.com", "status": "screened"},
        owner_id="u_recruiter",
        org_id="org_tech",
    )
    store = MockPEDOStore(objects={obj.id: obj})
    evaluator = PEDOSecurityEvaluator(store=store)
    assert evaluator._live is True

    sc = SecurityScenario(
        scenario_id="live_rls_01",
        name="Live RLS Query",
        description="Recruiter queries candidates in same org",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="query",
        agent_query_or_code='{"op": "query", "type": "candidate"}',
        expected_allowed=True,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["live"] is True
    assert res["allowed"] is True
    assert res["passed"] is True


def test_live_evaluator_detects_cross_org_denial():
    """Regression: live evaluator detects cross-org denial.

    The real ObjectStore.query() silently filters inaccessible objects
    and returns an empty list — it does not raise.  The evaluator must
    distinguish "authorized empty result" from "rows existed but were
    RLS-filtered" by probing the known target object through get(),
    which raises PermissionDeniedError on denied access.
    """
    obj = DataObject(
        type_name="candidate",
        content={"name": "Bob", "status": "applied"},
        owner_id="u_other",
        org_id="org_other",
    )
    store = MockPEDOStore(objects={obj.id: obj})
    evaluator = PEDOSecurityEvaluator(store=store)

    sc = SecurityScenario(
        scenario_id="live_rls_02",
        name="Cross-Org Denial",
        description="Recruiter from org_tech queries candidates in org_other",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="query",
        target_object=obj,
        agent_query_or_code='{"op": "query", "type": "candidate", "org_id": "org_other"}',
        expected_allowed=False,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["live"] is True
    assert res["allowed"] is False
    assert res["passed"] is True
def test_live_evaluator_authorized_empty_result():
    """Regression: an empty query result with no target object is allowed.

    When query() returns [] because no objects exist (not because rows
    were RLS-filtered), the evaluator must report allowed=True.  The
    probe only fires when a target_object with a known id is present.
    """
    store = MockPEDOStore(objects={})
    evaluator = PEDOSecurityEvaluator(store=store)

    sc = SecurityScenario(
        scenario_id="live_rls_03",
        name="Authorized Empty Result",
        description="Recruiter queries candidates in own org but none exist",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="query",
        target_object=None,
        agent_query_or_code='{"op": "query", "type": "candidate"}',
        expected_allowed=True,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["live"] is True
    assert res["allowed"] is True
    assert res["passed"] is True


def test_live_evaluator_rls_probe_detects_filtered_rows():
    """Regression: RLS probe via get() detects rows filtered by query().

    The real ObjectStore.query() silently filters cross-org objects and
    returns [].  Without the probe, the evaluator would report allowed.
    The probe calls get() on the target object, which raises
    PermissionDeniedError, proving the rows were RLS-filtered.
    """
    obj = DataObject(
        type_name="candidate",
        content={"name": "Dave", "status": "applied"},
        owner_id="u_other",
        org_id="org_other",
    )
    # Store has the object, but query() will silently filter it for
    # cross-org accessors — matching real ObjectStore behavior.
    store = MockPEDOStore(objects={obj.id: obj})
    evaluator = PEDOSecurityEvaluator(store=store)

    sc = SecurityScenario(
        scenario_id="live_rls_04",
        name="RLS Probe Filtered Rows",
        description="Recruiter queries candidates in org_other; rows filtered silently",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="query",
        target_object=obj,
        agent_query_or_code='{"op": "query", "type": "candidate"}',
        expected_allowed=False,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["live"] is True
    assert res["allowed"] is False
    assert res["passed"] is True
    assert res["org_boundary_enforced"] is True


def test_live_evaluator_executes_callable_agent_query():
    """Regression: callable agent_query_or_code receives the store and is executed."""
    obj = DataObject(
        type_name="candidate",
        content={"name": "Carol", "email": "carol@example.com", "status": "interviewed"},
        owner_id="u_recruiter",
        org_id="org_tech",
    )
    store = MockPEDOStore(objects={obj.id: obj})
    evaluator = PEDOSecurityEvaluator(store=store)

    def agent_query(ctx):
        return ctx["store"].query(ctx["accessor"], ctx["type_name"])

    sc = SecurityScenario(
        scenario_id="live_callable_01",
        name="Callable Agent Query",
        description="Agent query as callable executing against store",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="query",
        agent_query_or_code=agent_query,
        expected_allowed=True,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["live"] is True
    assert res["allowed"] is True
    assert res["passed"] is True


def test_live_evaluator_callable_denied_access():
    """Regression: callable that raises PermissionDeniedError is reported as denied."""
    store = MockPEDOStore()
    evaluator = PEDOSecurityEvaluator(store=store)

    def agent_query(ctx):
        raise PermissionDeniedError("Access denied by policy")

    sc = SecurityScenario(
        scenario_id="live_callable_denied",
        name="Callable Denied",
        description="Agent query callable that is denied by policy",
        accessor=AccessContext(user_id="u_user", role="user", org_id="org_a"),
        object_type="document",
        operation_type="read",
        agent_query_or_code=agent_query,
        expected_allowed=False,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["live"] is True
    assert res["allowed"] is False
    assert res["passed"] is True


def test_live_evaluator_field_visibility_from_store_results():
    """Regression: field visibility is derived from actual store query results, not hard-coded."""
    obj = DataObject(
        type_name="candidate",
        content={"name": "Dave", "email": "dave@example.com", "status": "applied",
                  "ssn": "123-45-6789", "salary_expectation": 90000},
        owner_id="u_recruiter",
        org_id="org_tech",
    )
    store = MockPEDOStore(objects={obj.id: obj})
    evaluator = PEDOSecurityEvaluator(store=store)

    sc = SecurityScenario(
        scenario_id="live_field_01",
        name="Live Field Visibility",
        description="Interviewer queries candidate — ssn and salary should not be visible",
        accessor=AccessContext(user_id="u_interviewer", role="interviewer", org_id="org_tech"),
        object_type="candidate",
        operation_type="read",
        requested_fields=["name", "email", "status", "ssn", "salary_expectation"],
        hidden_or_sensitive_fields=["ssn", "salary_expectation"],
        agent_query_or_code='{"op": "query", "type": "candidate"}',
    )
    res = evaluator.evaluate_field_visibility(sc)
    assert res["live"] is True
    # The store returns all fields in content; the evaluator should detect
    # that ssn and salary_expectation leaked to an interviewer
    assert "ssn" in res["visible_fields"]
    assert "salary_expectation" in res["visible_fields"]
    assert res["unauthorized_leakage"] is True
    assert "ssn" in res["leaked_fields"]


def test_non_live_evaluator_labeled_not_live():
    """Regression: evaluator without store/dsn is labeled live=False in metrics."""
    evaluator = PEDOSecurityEvaluator()
    assert evaluator._live is False
    metrics = evaluator.evaluate_scenarios(generate_default_scenarios())
    assert metrics.live is False


def test_live_evaluator_labeled_live_in_metrics():
    """Regression: evaluator with store is labeled live=True in metrics."""
    store = MockPEDOStore()
    evaluator = PEDOSecurityEvaluator(store=store)
    assert evaluator._live is True
    sc = SecurityScenario(
        scenario_id="live_metrics_01",
        name="Live Metrics Check",
        description="Verify live flag in metrics",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="read",
        expected_allowed=True,
    )
    metrics = evaluator.evaluate_scenarios([sc])
    assert metrics.live is True


def test_live_evaluator_create_mutation():
    """Regression: live evaluator executes create mutations through the store."""
    store = MockPEDOStore()
    evaluator = PEDOSecurityEvaluator(store=store)

    sc = SecurityScenario(
        scenario_id="live_create_01",
        name="Live Create Mutation",
        description="Create a new candidate via JSON spec",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="create",
        agent_query_or_code='{"op": "create", "type": "candidate", "content": {"name": "Eve", "status": "applied"}}',
        expected_allowed=True,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["live"] is True
    assert res["allowed"] is True
    assert res["passed"] is True


def test_live_evaluator_update_mutation_denied():
    """Regression: live evaluator detects denied update mutation via PermissionDeniedError."""
    obj = DataObject(
        type_name="candidate",
        content={"name": "Frank", "status": "applied"},
        owner_id="u_other",
        org_id="org_other",
    )
    store = MockPEDOStore(objects={obj.id: obj})
    evaluator = PEDOSecurityEvaluator(store=store)

    sc = SecurityScenario(
        scenario_id="live_update_denied",
        name="Live Update Denied",
        description="Cross-org update is denied by policy",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="update",
        agent_query_or_code=f'{{"op": "update", "object_id": "{obj.id}", "changes": {{"status": "hired"}}}}',
        expected_allowed=False,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["live"] is True
    assert res["allowed"] is False
    assert res["passed"] is True


def test_live_evaluator_mutation_executed_once():
    """Regression: evaluate_scenario executes a mutation exactly once.

    Closes the class where evaluate_row_level_security and
    evaluate_field_visibility each called _execute_agent_query independently,
    causing mutations (create/update/delete) to be executed twice per
    scenario. With a create mutation, two objects were created from one
    scenario.
    """
    store = MockPEDOStore()
    create_count = 0

    class CountingStore(MockPEDOStore):
        def create(self, obj, accessor, _reaction_depth=0):
            nonlocal create_count
            create_count += 1
            return super().create(obj, accessor, _reaction_depth)

    counting_store = CountingStore()
    evaluator = PEDOSecurityEvaluator(store=counting_store)

    sc = SecurityScenario(
        scenario_id="live_create_once",
        name="Mutation Executed Once",
        description="Create mutation should be executed exactly once per scenario",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="create",
        agent_query_or_code='{"op": "create", "type": "candidate", "content": {"name": "Zoe", "status": "applied"}}',
        expected_allowed=True,
    )
    evaluator.evaluate_scenario(sc)
    assert create_count == 1, f"Expected 1 create call, got {create_count}"


def test_live_evaluator_non_json_string_does_not_report_live():
    """Regression: non-JSON agent_query_or_code in live mode does not silently
    fall back to in-memory rules while reporting live=True.

    Closes the class where a malformed/non-JSON string caused
    _execute_agent_query to return executed=False, and the evaluator fell
    through to the in-memory fallback that reported live=self._live (True).
    """
    store = MockPEDOStore()
    evaluator = PEDOSecurityEvaluator(store=store)

    sc = SecurityScenario(
        scenario_id="live_non_json_rls",
        name="Non-JSON String RLS",
        description="Malformed query string should not silently fall back",
        accessor=AccessContext(user_id="u_recruiter", role="recruiter", org_id="org_tech"),
        object_type="candidate",
        operation_type="query",
        agent_query_or_code="not a json query",
        expected_allowed=True,
    )
    res = evaluator.evaluate_row_level_security(sc)
    assert res["live"] is False
    assert res["passed"] is False
    assert res["execution_error"] is not None


def test_live_evaluator_non_json_string_does_not_leak_sensitive_fields():
    """Regression: non-JSON agent_query_or_code in live mode does not leak
    sensitive fields by setting visible_fields to all requested_fields.

    Closes the class where the non-JSON field fallback set visible_fields to
    list(requested_fields), exposing sensitive fields like ssn and
    salary_expectation to roles that should not see them.
    """
    store = MockPEDOStore()
    evaluator = PEDOSecurityEvaluator(store=store)

    sc = SecurityScenario(
        scenario_id="live_non_json_fields",
        name="Non-JSON String Field Visibility",
        description="Malformed query string should not leak sensitive fields",
        accessor=AccessContext(user_id="u_interviewer", role="interviewer", org_id="org_tech"),
        object_type="candidate",
        operation_type="read",
        requested_fields=["name", "email", "status", "ssn", "salary_expectation"],
        hidden_or_sensitive_fields=["ssn", "salary_expectation"],
        agent_query_or_code="name, email, status, ssn, salary_expectation",
    )
    res = evaluator.evaluate_field_visibility(sc)
    assert res["live"] is False
    assert res["passed"] is False
    assert "ssn" not in res["visible_fields"]
    assert "salary_expectation" not in res["visible_fields"]
    assert res["unauthorized_leakage"] is False


def test_non_live_non_json_string_uses_allowed_fields_filter():
    """Regression: non-JSON string in non-live mode uses allowed_fields filter
    instead of treating the string as a field list.

    Closes the class where the in-memory fallback for non-JSON strings set
    visible_fields to all requested_fields, leaking sensitive fields to
    unauthorized roles even without a live store.
    """
    evaluator = PEDOSecurityEvaluator()

    sc = SecurityScenario(
        scenario_id="nonlive_non_json_fields",
        name="Non-Live Non-JSON Field Visibility",
        description="Non-JSON string should use allowed_fields filter",
        accessor=AccessContext(user_id="u_interviewer", role="interviewer", org_id="org_tech"),
        object_type="candidate",
        operation_type="read",
        requested_fields=["name", "email", "status", "ssn", "salary_expectation"],
        hidden_or_sensitive_fields=["ssn", "salary_expectation"],
        agent_query_or_code="name, email, status, ssn, salary_expectation",
    )
    res = evaluator.evaluate_field_visibility(sc)
    assert res["live"] is False
    assert "ssn" not in res["visible_fields"]
    assert "salary_expectation" not in res["visible_fields"]
    assert res["unauthorized_leakage"] is False
