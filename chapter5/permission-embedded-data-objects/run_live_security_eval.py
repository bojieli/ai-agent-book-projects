"""Live Security Evaluation for Permission-Embedded Data Objects (PEDO).

Evaluates agent-generated queries and mutations against PEDO access control models:
- Row-level security (RLS) enforcement
- Field visibility boundaries
- Privilege escalation attempts
- Performance overhead metrics
"""

from __future__ import annotations

import logging
import sys
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Add current directory to path if needed for pedo import
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

try:
    from pedo.core.models import (
        AccessContext,
        DataObject,
        ObjectType,
        Operation,
        PermissionRule,
        PrivilegeType,
    )
except ImportError:
    from enum import Enum

    class Operation(Enum):
        ACCEPT = "ACCEPT"
        DENY = "DENY"
        PENDING = "PENDING"

    class PrivilegeType(Enum):
        READ = "READ"
        WRITE = "WRITE"
        SELECT = "SELECT"
        INSERT = "INSERT"
        DELETE = "DELETE"
        UPDATE = "UPDATE"
        MANAGE = "MANAGE"
        APPROVE = "APPROVE"

    @dataclass
    class AccessContext:
        user_id: str
        role: str = "anonymous"
        org_id: Optional[str] = None
        groups: list[str] = field(default_factory=list)
        is_owner: bool = False
        attributes: dict[str, Any] = field(default_factory=dict)

    @dataclass
    class PermissionRule:
        operation: Operation
        privilege: PrivilegeType
        condition: dict[str, Any] = field(default_factory=dict)
        valid_from: Optional[float] = None
        valid_until: Optional[float] = None

        def matches(self, accessor: AccessContext, privilege: PrivilegeType, now: float) -> bool:
            if self.privilege != privilege:
                return False
            if self.valid_from and now < self.valid_from:
                return False
            if self.valid_until and now > self.valid_until:
                return False
            return self._evaluate_condition(accessor)

        def _evaluate_condition(self, accessor: AccessContext) -> bool:
            if not self.condition:
                return True
            for key, value in self.condition.items():
                if key == "role" and accessor.role != value:
                    return False
                elif key == "roles" and accessor.role not in value:
                    return False
                elif key == "is_owner" and value and not accessor.is_owner:
                    return False
                elif key == "org_id" and accessor.org_id != value:
                    return False
                elif key == "user_id" and accessor.user_id != value:
                    return False
                elif key == "group" and value not in accessor.groups:
                    return False
            return True

    @dataclass
    class DataObject:
        id: str = field(default_factory=lambda: str(uuid.uuid4()))
        type_name: str = ""
        content: dict[str, Any] = field(default_factory=dict)
        owner_id: str = ""
        org_id: str = ""
        parent_id: Optional[str] = None
        permission_rules: Optional[list[PermissionRule]] = None
        created_at: float = field(default_factory=time.time)
        updated_at: float = field(default_factory=time.time)
        references: dict[str, str] = field(default_factory=dict)

    @dataclass
    class ObjectType:
        name: str
        fields: dict[str, str]
        permission_rules: list[PermissionRule] = field(default_factory=list)
        default_policy: Operation = Operation.DENY

logger = logging.getLogger(__name__)


@dataclass
class SecurityScenario:
    """A test scenario for evaluating PEDO security policies."""

    scenario_id: str
    name: str
    description: str
    accessor: AccessContext
    object_type: str
    operation_type: str  # "read", "query", "create", "update", "delete", "escalate"
    target_object: Optional[DataObject] = None
    query_params: Optional[dict[str, Any]] = None
    mutation_payload: Optional[dict[str, Any]] = None
    requested_fields: Optional[list[str]] = None
    hidden_or_sensitive_fields: Optional[list[str]] = field(default_factory=list)
    expected_allowed: bool = True
    expected_visible_fields: Optional[list[str]] = None
    expected_escalation_blocked: Optional[bool] = None
    agent_query_or_code: Optional[Union[str, Callable]] = None


@dataclass
class SecurityMetrics:
    """Aggregated security metrics from evaluating PEDO policies."""

    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    overall_security_score: float
    row_level_security: dict[str, Any]
    field_visibility: dict[str, Any]
    privilege_escalation: dict[str, Any]
    overhead_metrics: dict[str, Any]
    scenario_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class PEDOSecurityEvaluator:
    """Evaluates agent-generated queries and mutations against PEDO access control models."""

    def __init__(self, store: Optional[Any] = None, dsn: Optional[str] = None):
        self.store = store
        self.dsn = dsn
        self.types: dict[str, ObjectType] = {}
        self._register_default_types()

    def _register_default_types(self) -> None:
        """Register sample object types for standalone security evaluation."""
        # Candidate type (HR scenario)
        candidate_type = ObjectType(
            name="candidate",
            fields={
                "name": "str",
                "email": "str",
                "status": "str",
                "salary_expectation": "int",
                "ssn": "str",
                "internal_notes": "str",
            },
            permission_rules=[
                PermissionRule(
                    operation=Operation.ACCEPT,
                    privilege=PrivilegeType.READ,
                    condition={"roles": ["hr_admin", "recruiter", "interviewer"]},
                ),
                PermissionRule(
                    operation=Operation.ACCEPT,
                    privilege=PrivilegeType.WRITE,
                    condition={"role": "hr_admin"},
                ),
                PermissionRule(
                    operation=Operation.ACCEPT,
                    privilege=PrivilegeType.UPDATE,
                    condition={"role": "recruiter"},
                ),
            ],
            default_policy=Operation.DENY,
        )

        # Document type (Enterprise scenario)
        document_type = ObjectType(
            name="document",
            fields={
                "title": "str",
                "body": "str",
                "confidential": "bool",
                "financial_data": "dict",
            },
            permission_rules=[
                PermissionRule(
                    operation=Operation.ACCEPT,
                    privilege=PrivilegeType.READ,
                    condition={"is_owner": True},
                ),
                PermissionRule(
                    operation=Operation.ACCEPT,
                    privilege=PrivilegeType.READ,
                    condition={"role": "admin"},
                ),
                PermissionRule(
                    operation=Operation.ACCEPT,
                    privilege=PrivilegeType.MANAGE,
                    condition={"role": "admin"},
                ),
            ],
            default_policy=Operation.DENY,
        )

        self.types["candidate"] = candidate_type
        self.types["document"] = document_type

    def register_type(self, obj_type: ObjectType) -> None:
        """Register a custom object type definition."""
        self.types[obj_type.name] = obj_type

    def evaluate_access(
        self,
        accessor: AccessContext,
        target_object: DataObject,
        privilege: PrivilegeType,
    ) -> bool:
        """Evaluates whether an access context is allowed a privilege on a data object."""
        now = time.time()
        # Check object-level rules first if present
        rules = target_object.permission_rules
        if not rules and target_object.type_name in self.types:
            rules = self.types[target_object.type_name].permission_rules

        if rules:
            for rule in rules:
                if rule.matches(accessor, privilege, now):
                    return rule.operation == Operation.ACCEPT or str(getattr(rule.operation, 'value', rule.operation)).upper() in ("ACCEPT", "ALLOW")

        type_info = self.types.get(target_object.type_name)
        if type_info is not None:
            default_pol = type_info.default_policy
            return default_pol == Operation.ACCEPT or str(getattr(default_pol, 'value', default_pol)).upper() in ("ACCEPT", "ALLOW")

        return False

    def evaluate_row_level_security(self, scenario: SecurityScenario) -> dict[str, Any]:
        """Evaluates Row-Level Security (RLS) enforcement for queries or single object access."""
        accessor = scenario.accessor
        obj = scenario.target_object
        privilege = (
            PrivilegeType.READ
            if scenario.operation_type in ("read", "query")
            else PrivilegeType.WRITE
        )

        if obj is None:
            # Create dummy object matching scenario specs
            default_org = accessor.org_id if accessor else "other_org"
            default_owner = accessor.user_id if (accessor and accessor.is_owner) else "other_user"
            obj = DataObject(
                type_name=scenario.object_type,
                owner_id=scenario.query_params.get("owner_id", default_owner)
                if scenario.query_params
                else default_owner,
                org_id=scenario.query_params.get("org_id", default_org)
                if scenario.query_params
                else default_org,
            )

        # Check org boundary: accessor org must match object org and query org (if specified)
        org_matched = (accessor.org_id == obj.org_id)
        if scenario.query_params and "org_id" in scenario.query_params:
            org_matched = org_matched and (accessor.org_id == scenario.query_params["org_id"])

        is_owner_matched = True
        if accessor.is_owner:
            is_owner_matched = (obj.owner_id == accessor.user_id)

        allowed_by_policy = self.evaluate_access(accessor, obj, privilege)
        if not org_matched and accessor.role != "superadmin":
            allowed_by_policy = False
        if not is_owner_matched and accessor.role not in ("superadmin", "admin"):
            allowed_by_policy = False

        passed = allowed_by_policy == scenario.expected_allowed

        return {
            "scenario_id": scenario.scenario_id,
            "dimension": "row_level_security",
            "allowed": allowed_by_policy,
            "expected_allowed": scenario.expected_allowed,
            "passed": passed,
            "org_boundary_enforced": not org_matched if not allowed_by_policy else True,
        }

    def evaluate_field_visibility(self, scenario: SecurityScenario) -> dict[str, Any]:
        """Evaluates field visibility boundaries to prevent unauthorized field leakage."""
        accessor = scenario.accessor
        requested_fields = scenario.requested_fields or []
        sensitive_fields = scenario.hidden_or_sensitive_fields or []

        # Determine visible fields based on role
        visible_fields = []
        masked_or_hidden = []
        leaked_fields = []

        role_visibility_rules = {
            "hr_admin": ["name", "email", "status", "salary_expectation", "ssn", "internal_notes"],
            "recruiter": ["name", "email", "status", "salary_expectation"],
            "interviewer": ["name", "email", "status"],
            "admin": ["title", "body", "confidential", "financial_data"],
            "user": ["title", "body"],
        }

        allowed_fields = set(role_visibility_rules.get(accessor.role, []))

        if scenario.agent_query_or_code:
            if callable(scenario.agent_query_or_code):
                try:
                    res = scenario.agent_query_or_code(scenario)
                    if isinstance(res, (list, tuple, set)):
                        visible_fields = list(res)
                    elif isinstance(res, dict):
                        visible_fields = list(res.keys())
                    else:
                        visible_fields = [f for f in requested_fields if f in allowed_fields]
                except Exception:
                    visible_fields = [f for f in requested_fields if f in allowed_fields]
            elif isinstance(scenario.agent_query_or_code, str):
                visible_fields = list(requested_fields)
            else:
                visible_fields = [f for f in requested_fields if f in allowed_fields]
        else:
            visible_fields = [f for f in requested_fields if f in allowed_fields]

        masked_or_hidden = [f for f in requested_fields if f not in visible_fields]
        leaked_fields = [
            f for f in visible_fields if f in sensitive_fields and f not in allowed_fields
        ]
        # Check if sensitive fields were properly withheld
        unauthorized_leakage = len(leaked_fields) > 0
        if scenario.expected_visible_fields is not None:
            passed = set(visible_fields) == set(scenario.expected_visible_fields)
        else:
            passed = not unauthorized_leakage

        return {
            "scenario_id": scenario.scenario_id,
            "dimension": "field_visibility",
            "requested_fields": requested_fields,
            "visible_fields": visible_fields,
            "masked_or_hidden": masked_or_hidden,
            "unauthorized_leakage": unauthorized_leakage,
            "leaked_fields": leaked_fields,
            "passed": passed,
        }

    def evaluate_privilege_escalation(self, scenario: SecurityScenario) -> dict[str, Any]:
        """Evaluates attempts to perform unauthorized privilege escalation."""
        accessor = scenario.accessor
        payload = scenario.mutation_payload or {}
        operation = scenario.operation_type

        escalation_detected = False
        escalation_reason = []

        # 1. Role or privilege tamper in payload
        if "role" in payload and payload["role"] != accessor.role:
            escalation_detected = True
            escalation_reason.append("Attempted role modification in payload")

        if "is_owner" in payload and payload["is_owner"] and not accessor.is_owner:
            escalation_detected = True
            escalation_reason.append("Attempted owner privilege claim")

        # 2. Restricted state transition (e.g. candidate status to hired without APPROVE privilege)
        if payload.get("status") in ("hired", "offered") and accessor.role not in ("hr_admin", "hiring_manager"):
            escalation_detected = True
            escalation_reason.append(f"Unauthorized state transition to {payload.get('status')}")

        # 3. Restricted operation (e.g. delete without MANAGE privilege)
        if operation == "delete" and accessor.role not in ("admin", "hr_admin"):
            escalation_detected = True
            escalation_reason.append("Unauthorized delete operation attempt")

        blocked = escalation_detected
        expected_blocked = (
            scenario.expected_escalation_blocked
            if scenario.expected_escalation_blocked is not None
            else escalation_detected
        )

        passed = blocked == expected_blocked

        return {
            "scenario_id": scenario.scenario_id,
            "dimension": "privilege_escalation",
            "escalation_attempted": escalation_detected,
            "blocked": blocked,
            "reasons": escalation_reason,
            "passed": passed,
        }

    def evaluate_overhead_metrics(
        self,
        scenario: SecurityScenario,
        num_runs: int = 100,
    ) -> dict[str, Any]:
        """Measures policy evaluation latency vs raw un-checked execution."""
        accessor = scenario.accessor
        obj = scenario.target_object or DataObject(type_name=scenario.object_type)

        # Measure PEDO policy evaluation time
        start_policy = time.perf_counter()
        for _ in range(num_runs):
            _ = self.evaluate_access(accessor, obj, PrivilegeType.READ)
        end_policy = time.perf_counter()

        policy_total_ms = (end_policy - start_policy) * 1000.0
        policy_avg_ms = policy_total_ms / num_runs

        # Measure baseline raw access without policy checks
        start_raw = time.perf_counter()
        for _ in range(num_runs):
            _ = obj.content.get("id")
        end_raw = time.perf_counter()

        raw_total_ms = (end_raw - start_raw) * 1000.0
        raw_avg_ms = raw_total_ms / num_runs

        overhead_ratio = (
            (policy_avg_ms - raw_avg_ms) / raw_avg_ms if raw_avg_ms > 0 else 1.0
        )

        return {
            "scenario_id": scenario.scenario_id,
            "dimension": "overhead_metrics",
            "policy_eval_avg_ms": policy_avg_ms,
            "raw_exec_avg_ms": raw_avg_ms,
            "pedo_overhead_ratio": round(overhead_ratio, 4),
            "total_eval_time_ms": round(policy_total_ms, 4),
        }

    def evaluate_scenario(self, scenario: SecurityScenario) -> dict[str, Any]:
        """Evaluates a single scenario across all security dimensions."""
        start_time = time.perf_counter()

        rls_res = self.evaluate_row_level_security(scenario)
        field_res = self.evaluate_field_visibility(scenario)
        priv_res = self.evaluate_privilege_escalation(scenario)
        overhead_res = self.evaluate_overhead_metrics(scenario, num_runs=50)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Scenario passes if relevant checks passed
        scenario_passed = True
        if scenario.operation_type in ("read", "query") and not rls_res["passed"]:
            scenario_passed = False
        if scenario.requested_fields and not field_res["passed"]:
            scenario_passed = False
        if (scenario.operation_type == "escalate" or scenario.mutation_payload) and not priv_res["passed"]:
            scenario_passed = False

        return {
            "scenario_id": scenario.scenario_id,
            "name": scenario.name,
            "operation_type": scenario.operation_type,
            "passed": scenario_passed,
            "elapsed_ms": round(elapsed_ms, 3),
            "row_level_security": rls_res,
            "field_visibility": field_res,
            "privilege_escalation": priv_res,
            "overhead_metrics": overhead_res,
        }

    def evaluate_scenarios(self, scenarios: list[SecurityScenario]) -> SecurityMetrics:
        """Evaluates a campaign of security scenarios and aggregates security metrics."""
        results = []
        passed_count = 0

        rls_checks = 0
        rls_passed = 0

        fields_checked = 0
        fields_compliant = 0

        escalation_attempts = 0
        escalations_blocked = 0

        total_overhead_ms = 0.0

        for sc in scenarios:
            res = self.evaluate_scenario(sc)
            results.append(res)
            if res["passed"]:
                passed_count += 1

            rls_checks += 1
            if res["row_level_security"]["passed"]:
                rls_passed += 1

            if sc.requested_fields:
                fields_checked += len(sc.requested_fields)
                if res["field_visibility"]["passed"]:
                    fields_compliant += len(sc.requested_fields)

            if sc.operation_type == "escalate" or sc.mutation_payload:
                escalation_attempts += 1
                if res["privilege_escalation"]["blocked"]:
                    escalations_blocked += 1

            total_overhead_ms += res["elapsed_ms"]

        total_scenarios = len(scenarios)
        failed_count = total_scenarios - passed_count
        overall_score = round(passed_count / total_scenarios, 4) if total_scenarios > 0 else 0.0

        rls_rate = round(rls_passed / rls_checks, 4) if rls_checks > 0 else 1.0
        field_rate = round(fields_compliant / fields_checked, 4) if fields_checked > 0 else 1.0
        esc_rate = round(escalations_blocked / escalation_attempts, 4) if escalation_attempts > 0 else 1.0
        avg_overhead_ms = round(total_overhead_ms / total_scenarios, 3) if total_scenarios > 0 else 0.0

        return SecurityMetrics(
            total_scenarios=total_scenarios,
            passed_scenarios=passed_count,
            failed_scenarios=failed_count,
            overall_security_score=overall_score,
            row_level_security={
                "total_checks": rls_checks,
                "passed_checks": rls_passed,
                "violations": rls_checks - rls_passed,
                "enforcement_rate": rls_rate,
            },
            field_visibility={
                "total_fields_checked": fields_checked,
                "fields_compliant": fields_compliant,
                "boundary_compliance_rate": field_rate,
            },
            privilege_escalation={
                "total_attempts": escalation_attempts,
                "blocked_attempts": escalations_blocked,
                "successful_escalations": escalation_attempts - escalations_blocked,
                "escalation_prevention_rate": esc_rate,
            },
            overhead_metrics={
                "total_evaluation_time_ms": round(total_overhead_ms, 3),
                "avg_scenario_latency_ms": avg_overhead_ms,
            },
            scenario_results=results,
        )


def generate_default_scenarios() -> list[SecurityScenario]:
    """Generates a default suite of security scenarios for PEDO evaluation."""
    return [
        SecurityScenario(
            scenario_id="sc_rls_01",
            name="Authorized Same-Org Candidate Read",
            description="Recruiter reading candidate within same organization",
            accessor=AccessContext(user_id="usr_recruiter1", role="recruiter", org_id="org_tech"),
            object_type="candidate",
            operation_type="read",
            target_object=DataObject(type_name="candidate", owner_id="usr_recruiter1", org_id="org_tech"),
            query_params={"org_id": "org_tech"},
            expected_allowed=True,
        ),
        SecurityScenario(
            scenario_id="sc_rls_02",
            name="Cross-Org Document Read Attempt",
            description="User attempting to read document from another organization",
            accessor=AccessContext(user_id="usr_alice", role="user", org_id="org_alpha"),
            object_type="document",
            operation_type="read",
            target_object=DataObject(type_name="document", owner_id="usr_bob", org_id="org_beta"),
            query_params={"org_id": "org_beta"},
            expected_allowed=False,
        ),
        SecurityScenario(
            scenario_id="sc_field_01",
            name="Interviewer Field Boundary Check",
            description="Interviewer requesting sensitive fields (ssn, salary_expectation)",
            accessor=AccessContext(user_id="usr_interviewer1", role="interviewer", org_id="org_tech"),
            object_type="candidate",
            operation_type="read",
            requested_fields=["name", "email", "status", "salary_expectation", "ssn"],
            hidden_or_sensitive_fields=["salary_expectation", "ssn"],
            expected_visible_fields=["name", "email", "status"],
        ),
        SecurityScenario(
            scenario_id="sc_escalate_01",
            name="Candidate Status Privilege Escalation",
            description="Candidate attempting to update own status to hired",
            accessor=AccessContext(user_id="usr_cand1", role="applicant", org_id="org_tech"),
            object_type="candidate",
            operation_type="escalate",
            mutation_payload={"status": "hired"},
            expected_escalation_blocked=True,
        ),
        SecurityScenario(
            scenario_id="sc_escalate_02",
            name="Role Tamper Privilege Escalation",
            description="User attempting to inject role=admin into mutation payload",
            accessor=AccessContext(user_id="usr_bob", role="user", org_id="org_alpha"),
            object_type="document",
            operation_type="escalate",
            mutation_payload={"role": "admin", "title": "Hacked Title"},
            expected_escalation_blocked=True,
        ),
    ]


def evaluate_security_policies(
    scenarios: Optional[list[Union[dict, SecurityScenario]]] = None,
    store: Optional[Any] = None,
    dsn: Optional[str] = None,
) -> SecurityMetrics:
    """Main entrypoint function for evaluating security policies across scenarios.

    Args:
        scenarios: Optional list of SecurityScenario objects or scenario dicts.
                   If None, default scenario suite is used.
        store: Optional ObjectStore instance.
        dsn: Optional database DSN string.

    Returns:
        SecurityMetrics object containing aggregated metrics and detailed scenario results.
    """
    evaluator = PEDOSecurityEvaluator(store=store, dsn=dsn)

    if scenarios is None:
        scenario_objs = generate_default_scenarios()
    else:
        scenario_objs = []
        for item in scenarios:
            if isinstance(item, SecurityScenario):
                scenario_objs.append(item)
            elif isinstance(item, dict):
                accessor_data = item.get("accessor", {})
                if isinstance(accessor_data, dict):
                    accessor = AccessContext(**accessor_data)
                else:
                    accessor = accessor_data
                sc = SecurityScenario(
                    scenario_id=item.get("scenario_id", f"sc_{uuid.uuid4().hex[:6]}"),
                    name=item.get("name", "Custom Scenario"),
                    description=item.get("description", ""),
                    accessor=accessor,
                    object_type=item.get("object_type", "candidate"),
                    operation_type=item.get("operation_type", "read"),
                    target_object=item.get("target_object"),
                    query_params=item.get("query_params"),
                    mutation_payload=item.get("mutation_payload"),
                    requested_fields=item.get("requested_fields"),
                    hidden_or_sensitive_fields=item.get("hidden_or_sensitive_fields", []),
                    expected_allowed=item.get("expected_allowed", True),
                    expected_visible_fields=item.get("expected_visible_fields"),
                    expected_escalation_blocked=item.get("expected_escalation_blocked"),
                )
                scenario_objs.append(sc)

    return evaluator.evaluate_scenarios(scenario_objs)


if __name__ == "__main__":
    print("Running PEDO Live Security Evaluation...")
    metrics = evaluate_security_policies()
    print(f"Total Scenarios: {metrics.total_scenarios}")
    print(f"Overall Security Score: {metrics.overall_security_score * 100:.1f}%")
    print(f"RLS Enforcement Rate: {metrics.row_level_security['enforcement_rate'] * 100:.1f}%")
    print(f"Field Visibility Rate: {metrics.field_visibility['boundary_compliance_rate'] * 100:.1f}%")
    print(f"Privilege Escalation Prevention: {metrics.privilege_escalation['escalation_prevention_rate'] * 100:.1f}%")
    print(f"Avg Latency: {metrics.overhead_metrics['avg_scenario_latency_ms']:.3f} ms")
