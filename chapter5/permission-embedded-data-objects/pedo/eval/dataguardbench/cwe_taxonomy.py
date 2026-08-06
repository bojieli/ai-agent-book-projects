"""CWE taxonomy mapping for DataGuardBench.

Maps each violation type to its corresponding CWE entry, enabling comparison
with standard AI code security benchmarks (CyberSecEval, CWEval, SecCodePLT).
"""

from dataclasses import dataclass, field


@dataclass
class CWEEntry:
    """A CWE entry with its DataGuardBench violation mapping."""
    cwe_id: str
    name: str
    category: str       # authorization, validation, integrity, isolation
    description: str
    violation_types: list[str] = field(default_factory=list)
    oracle_checks: list[str] = field(default_factory=list)


# The CWE categories covered by DataGuardBench
CWE_TAXONOMY = {
    # --- Authorization ---
    "CWE-862": CWEEntry(
        cwe_id="CWE-862",
        name="Missing Authorization",
        category="authorization",
        description="The product does not perform an authorization check when an "
                    "actor attempts to access a resource or perform an action.",
        violation_types=["missing_auth", "unauthorized_write", "unauthorized_delete"],
        oracle_checks=["role_write_check", "role_delete_check"],
    ),
    "CWE-863": CWEEntry(
        cwe_id="CWE-863",
        name="Incorrect Authorization",
        category="authorization",
        description="The product performs an authorization check but incorrectly "
                    "determines that the actor is authorized.",
        violation_types=["incorrect_auth", "privilege_escalation", "role_confusion"],
        oracle_checks=["role_boundary_check", "privilege_escalation_check"],
    ),
    "CWE-639": CWEEntry(
        cwe_id="CWE-639",
        name="Authorization Bypass Through User-Controlled Key",
        category="isolation",
        description="The system uses a user-controlled key to determine which "
                    "resource to access, enabling cross-tenant data access.",
        violation_types=["cross_tenant_read", "cross_tenant_write", "tenant_bypass"],
        oracle_checks=["tenant_isolation_check"],
    ),
    # --- Business Logic / State Machine ---
    "CWE-840": CWEEntry(
        cwe_id="CWE-840",
        name="Business Logic Errors",
        category="validation",
        description="The product does not properly enforce business logic, "
                    "allowing transitions that violate declared workflows.",
        violation_types=["state_machine_skip", "invalid_transition", "terminal_state_exit"],
        oracle_checks=["state_machine_check", "transition_validity_check"],
    ),
    # --- Input Validation ---
    "CWE-20": CWEEntry(
        cwe_id="CWE-20",
        name="Improper Input Validation",
        category="validation",
        description="The product does not validate or incorrectly validates "
                    "input that affects control flow or data flow.",
        violation_types=["invalid_status_value", "invalid_priority", "invalid_enum",
                         "salary_out_of_range"],
        oracle_checks=["enum_value_check", "range_check"],
    ),
    "CWE-1284": CWEEntry(
        cwe_id="CWE-1284",
        name="Improper Validation of Specified Quantity in Input",
        category="validation",
        description="The product receives input specifying a quantity but does "
                    "not validate that the quantity is within expected range.",
        violation_types=["salary_out_of_range", "negative_value", "overflow_value",
                         "size_limit_exceeded"],
        oracle_checks=["numeric_range_check", "size_limit_check"],
    ),
    # --- Referential Integrity ---
    "CWE-672": CWEEntry(
        cwe_id="CWE-672",
        name="Operation on Resource after Expiration or Release",
        category="integrity",
        description="The product performs operations on a resource after that "
                    "resource has been expired, released, or revoked.",
        violation_types=["orphaned_reference", "closed_position_add",
                         "deleted_parent_reference", "expired_access"],
        oracle_checks=["orphan_check", "position_status_check", "temporal_check"],
    ),
    # --- General Access Control ---
    "CWE-284": CWEEntry(
        cwe_id="CWE-284",
        name="Improper Access Control",
        category="authorization",
        description="The product does not restrict or incorrectly restricts "
                    "access to a resource from an unauthorized actor.",
        violation_types=["immutable_modification", "audit_log_tampering",
                         "system_only_bypass"],
        oracle_checks=["immutability_check", "system_role_check"],
    ),
}


def get_cwe_for_violation(violation_type: str) -> str | None:
    """Return the CWE ID for a given violation type string."""
    for cwe_id, entry in CWE_TAXONOMY.items():
        if violation_type in entry.violation_types:
            return cwe_id
    return None


def get_cwe_category(violation_type: str) -> str | None:
    """Return the category (authorization/validation/integrity/isolation) for a violation."""
    cwe_id = get_cwe_for_violation(violation_type)
    if cwe_id:
        return CWE_TAXONOMY[cwe_id].category
    return None


def get_covered_cwes() -> list[str]:
    """Return the list of CWE IDs covered by DataGuardBench."""
    return sorted(CWE_TAXONOMY.keys())


def cwe_summary() -> dict[str, int]:
    """Return count of violation types per CWE category."""
    cats = {}
    for entry in CWE_TAXONOMY.values():
        cat = entry.category
        cats[cat] = cats.get(cat, 0) + len(entry.violation_types)
    return cats
