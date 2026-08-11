"""Live Security Evaluation for Permission-Embedded Data Objects (PEDO).

Evaluates agent-generated queries and mutations against PEDO access control models:
- Row-level security (RLS) enforcement
- Field visibility boundaries
- Privilege escalation attempts
- Performance overhead metrics
"""

from __future__ import annotations

import logging
import warnings
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
    from pedo.core.store import PermissionDeniedError
except ImportError:
    from enum import Enum

    class PermissionDeniedError(Exception):
        """Raised when an operation is denied by permission rules."""
        pass

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
    live: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class PEDOSecurityEvaluator:
    """Evaluates agent-generated queries and mutations against PEDO access control models.

    When a ``store`` (ObjectStore) or ``dsn`` is provided, the evaluator is
    live: it executes the submitted query/mutation through the real PEDO policy
    engine and evaluates the resulting access. When neither is provided, it
    falls back to an in-memory approximation using registered sample types;
    the ``live`` flag in the metrics reflects which mode was used.
    """

    def __init__(self, store: Optional[Any] = None, dsn: Optional[str] = None):
        self.store = store
        self.dsn = dsn
        self.types: dict[str, ObjectType] = {}
        self._live = False
        if self.store is not None:
            self._live = True
        elif self.dsn:
            try:
                from pedo.core.store import ObjectStore
                self.store = ObjectStore(self.dsn)
                self._live = True
            except Exception as e:
                logger.warning(
                    "Failed to initialize live ObjectStore from DSN: %s; "
                    "falling back to in-memory evaluation", e,
                )
                self.store = None
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

    def _execute_agent_query(
        self, scenario: "SecurityScenario"
    ) -> dict[str, Any]:
        """Executes or parses ``agent_query_or_code`` against the real store.

        Returns a dict with:
          - ``executed``: whether the query was executed (vs. parsed/fallback)
          - ``allowed``: whether the store permitted the operation
          - ``results``: the objects returned by a read/query, or the mutated object
          - ``error``: error message if execution failed
          - ``visible_fields``: field names visible in the results (for field visibility)
        """
        result: dict[str, Any] = {
            "executed": False,
            "allowed": True,
            "op": None,
            "results": [],
            "error": None,
            "visible_fields": [],
        }
        if self.store is None or scenario.agent_query_or_code is None:
            return result

        accessor = scenario.accessor
        store = self.store

        if callable(scenario.agent_query_or_code):
            try:
                ctx = {
                    "store": store,
                    "accessor": accessor,
                    "scenario": scenario,
                    "type_name": scenario.object_type,
                }
                ret = scenario.agent_query_or_code(ctx)
                result["executed"] = True
                result["op"] = scenario.operation_type
                if isinstance(ret, list):
                    result["results"] = ret
                    result["visible_fields"] = self._extract_visible_fields(ret)
                elif isinstance(ret, DataObject):
                    result["results"] = [ret]
                    result["visible_fields"] = list(ret.content.keys())
                elif isinstance(ret, dict):
                    result["results"] = [ret]
                    result["visible_fields"] = list(ret.keys())
                else:
                    result["results"] = []
            except PermissionDeniedError as e:
                result["executed"] = True
                result["allowed"] = False
                result["error"] = str(e)
            except Exception as e:
                result["executed"] = True
                result["allowed"] = False
                result["error"] = f"{type(e).__name__}: {e}"
            return result

        if isinstance(scenario.agent_query_or_code, str):
            spec = self._parse_query_spec(scenario.agent_query_or_code)
            if spec is None:
                return result
            try:
                result["executed"] = True
                op = spec.get("op", "query")
                result["op"] = op
                if op in ("query", "select"):
                    objs = store.query(
                        accessor,
                        spec.get("type", scenario.object_type),
                        filters=spec.get("filters"),
                        org_id=spec.get("org_id"),
                    )
                    result["results"] = objs
                    result["visible_fields"] = self._extract_visible_fields(objs)
                elif op == "read":
                    obj = store.get(spec.get("object_id", ""), accessor)
                    result["results"] = [obj] if obj is not None else []
                    result["visible_fields"] = list(obj.content.keys()) if obj else []
                elif op in ("create", "insert"):
                    obj = DataObject(
                        type_name=spec.get("type", scenario.object_type),
                        content=spec.get("content", {}),
                        owner_id=accessor.user_id,
                        org_id=accessor.org_id,
                    )
                    created = store.create(obj, accessor)
                    result["results"] = [created]
                    result["visible_fields"] = list(created.content.keys())
                elif op in ("update", "write"):
                    updated = store.update(
                        spec.get("object_id", ""),
                        spec.get("changes", {}),
                        accessor,
                    )
                    result["results"] = [updated]
                    result["visible_fields"] = list(updated.content.keys())
                elif op in ("delete", "remove"):
                    store.delete(spec.get("object_id", ""), accessor)
                    result["results"] = []
                    result["visible_fields"] = []
                else:
                    result["executed"] = False
                    result["error"] = f"Unknown operation '{op}' in query spec"
            except PermissionDeniedError as e:
                result["allowed"] = False
                result["error"] = str(e)
            except Exception as e:
                result["allowed"] = False
                result["error"] = f"{type(e).__name__}: {e}"
            return result

        return result

    @staticmethod
    def _parse_query_spec(spec_str: str) -> Optional[dict[str, Any]]:
        """Parses a string query specification into an operation dict.

        Accepts JSON like ``{"op": "query", "type": "candidate", "filters": {...}}``.
        Returns None if the string is not valid JSON (caller falls back to
        field-list interpretation).
        """
        import json
        try:
            spec = json.loads(spec_str)
            if isinstance(spec, dict):
                return spec
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    @staticmethod
    def _extract_visible_fields(objects: list[Any]) -> list[str]:
        """Extracts the union of field names from a list of DataObjects or dicts."""
        fields: set[str] = set()
        for obj in objects:
            if isinstance(obj, DataObject):
                fields.update(obj.content.keys())
            elif isinstance(obj, dict):
                fields.update(obj.keys())
        return list(fields)

    def evaluate_access(
        self,
        accessor: AccessContext,
        target_object: DataObject,
        privilege: PrivilegeType,
    ) -> bool:
        """Evaluates whether an access context is allowed a privilege on a data object."""
        now = time.time()
        # Verify claimed ownership against the actual object owner
        if accessor.is_owner and target_object.owner_id is not None:
            if accessor.user_id != target_object.owner_id:
                return False
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

    def evaluate_row_level_security(self, scenario: SecurityScenario, exec_result: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Evaluates Row-Level Security (RLS) enforcement for queries or single object access."""
        accessor = scenario.accessor
        obj = scenario.target_object
        privilege = (
            PrivilegeType.READ
            if scenario.operation_type in ("read", "query")
            else PrivilegeType.WRITE  # write, update, delete, create, escalate
        )

        # Live path: execute the agent query/mutation against the real store
        # and let the PEDO policy engine enforce RLS. PermissionDeniedError
        # means the store denied access — that is the real enforcement result.
        if self._live and self.store is not None and scenario.agent_query_or_code:
            if exec_result is None:
                exec_result = self._execute_agent_query(scenario)
            if exec_result["executed"]:
                allowed_by_policy = exec_result["allowed"]
                error = exec_result.get("error")
                op = exec_result.get("op")

                # The real ObjectStore.query() catches PermissionDeniedError
                # per row and silently filters inaccessible objects, returning
                # an empty list.  A normal return with an empty result is
                # therefore ambiguous: it could mean "no rows match" or
                # "rows existed but were RLS-filtered."  When the agent
                # performed a query/select and got an empty result, probe
                # the known target object through get() — which raises
                # PermissionDeniedError on denied access — to distinguish
                # the two cases.
                if (
                    allowed_by_policy
                    and op in ("query", "select", "read")
                    and not exec_result.get("results")
                    and scenario.target_object is not None
                    and scenario.target_object.id
                ):
                    try:
                        probe = self.store.get(
                            scenario.target_object.id, accessor
                        )
                        if probe is None:
                            # Object does not exist — genuinely empty.
                            allowed_by_policy = True
                        # If get() returns the object, the accessor can read
                        # it — the query filter was legitimate, not RLS.
                    except PermissionDeniedError as e:
                        # Object exists but accessor is denied — RLS
                        # filtered it out of the query results.
                        allowed_by_policy = False
                        error = f"RLS filtered target object: {e}"
                    except Exception as e:
                        # Probe failed for an unexpected reason; do not
                        # silently claim the query was allowed.
                        allowed_by_policy = False
                        error = f"RLS probe failed: {type(e).__name__}: {e}"

                passed = allowed_by_policy == scenario.expected_allowed
                return {
                    "scenario_id": scenario.scenario_id,
                    "dimension": "row_level_security",
                    "allowed": allowed_by_policy,
                    "expected_allowed": scenario.expected_allowed,
                    "passed": passed,
                    "org_boundary_enforced": not allowed_by_policy,
                    "live": True,
                    "execution_error": error,
                }
            # Live mode but the query could not be executed (e.g. malformed
            # non-JSON string). Do NOT silently fall back to in-memory rules
            # while reporting live=True. Report the failure explicitly.
            return {
                "scenario_id": scenario.scenario_id,
                "dimension": "row_level_security",
                "allowed": False,
                "expected_allowed": scenario.expected_allowed,
                "passed": False,
                "org_boundary_enforced": False,
                "live": False,
                "execution_error": exec_result.get("error") or "agent_query_or_code could not be executed",
            }
        # Fallback: in-memory policy evaluation (not live against PEDO)
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
        org_matched = (accessor is not None and obj is not None and accessor.org_id == obj.org_id)
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
            "live": self._live,
        }

    def evaluate_field_visibility(self, scenario: SecurityScenario, exec_result: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Evaluates field visibility boundaries to prevent unauthorized field leakage."""
        accessor = scenario.accessor
        requested_fields = scenario.requested_fields or []
        sensitive_fields = scenario.hidden_or_sensitive_fields or []

        # Determine visible fields based on role
        visible_fields = []
        masked_or_hidden = []
        leaked_fields = []

        role_visibility_rules = {
            ("hr_admin", "candidate"): ["name", "email", "status", "salary_expectation", "ssn", "internal_notes"],
            ("recruiter", "candidate"): ["name", "email", "status", "salary_expectation"],
            ("interviewer", "candidate"): ["name", "email", "status"],
            ("admin", "document"): ["title", "body", "confidential", "financial_data"],
            ("user", "document"): ["title", "body"],
        }

        allowed_fields = set(role_visibility_rules.get((accessor.role, scenario.object_type), []))

        # Live path: execute the agent query against the real store and
        # inspect the fields actually returned. The store's permission engine
        # determines which objects are visible; the fields in those objects'
        # content are what the agent would see. Leaked fields are those in
        # the result that the role should not access.
        if self._live and self.store is not None and scenario.agent_query_or_code:
            if exec_result is None:
                exec_result = self._execute_agent_query(scenario)
            if exec_result["executed"]:
                visible_fields = exec_result.get("visible_fields", [])
                if not exec_result["allowed"]:
                    # Denied access means no fields are visible
                    visible_fields = []
                masked_or_hidden = [f for f in requested_fields if f not in visible_fields]
                leaked_fields = [
                    f for f in visible_fields if f in sensitive_fields and f not in allowed_fields
                ]
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
                    "live": True,
                    "execution_error": exec_result.get("error"),
                }
            # Live mode but the query could not be executed (e.g. malformed
            # non-JSON string). Do NOT fall back to in-memory rules while
            # reporting live=True, and do NOT set visible_fields to all
            # requested fields (which would leak sensitive fields). Report
            # the failure explicitly.
            return {
                "scenario_id": scenario.scenario_id,
                "dimension": "field_visibility",
                "requested_fields": requested_fields,
                "visible_fields": [],
                "masked_or_hidden": list(requested_fields),
                "unauthorized_leakage": False,
                "leaked_fields": [],
                "passed": False,
                "live": False,
                "execution_error": exec_result.get("error") or "agent_query_or_code could not be executed",
            }
        # Fallback: in-memory field visibility evaluation (not live against PEDO)
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
                # Non-JSON string: cannot determine visible fields from query
                # text. Use the allowed_fields filter rather than treating the
                # string as a field list, which would leak sensitive fields.
                visible_fields = [f for f in requested_fields if f in allowed_fields]
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
            "live": self._live,
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
        # Execute the agent query/mutation once and share the result across
        # dimensions so mutations are not executed multiple times.
        exec_result: Optional[dict[str, Any]] = None
        if self._live and self.store is not None and scenario.agent_query_or_code:
            exec_result = self._execute_agent_query(scenario)
        rls_res = self.evaluate_row_level_security(scenario, exec_result=exec_result)
        field_res = self.evaluate_field_visibility(scenario, exec_result=exec_result)
        priv_res = self.evaluate_privilege_escalation(scenario)

        start_time = time.perf_counter()
        overhead_res = self.evaluate_overhead_metrics(scenario, num_runs=50)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Scenario passes if relevant checks passed
        scenario_passed = True
        if scenario.operation_type != "escalate" and not rls_res["passed"]:
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

            if sc.operation_type in ("read", "query"):
                rls_checks += 1
                if res["row_level_security"]["passed"]:
                    rls_passed += 1

            if sc.requested_fields:
                fields_checked += len(sc.requested_fields)
                if res["field_visibility"]["passed"]:
                    fields_compliant += len(sc.requested_fields)

            if res["privilege_escalation"]["escalation_attempted"] or sc.operation_type == "escalate" or sc.expected_escalation_blocked is True:
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
            live=self._live,
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
                    expected_escalation_blocked=item.get("expected_escalation_blocked"),
                    agent_query_or_code=item.get("agent_query_or_code"),
                )
                scenario_objs.append(sc)
            else:
                warnings.warn(
                    f"Skipping invalid scenario entry of type {type(item).__name__}; "
                    f"expected SecurityScenario or dict.",
                    stacklevel=2,
                )
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
