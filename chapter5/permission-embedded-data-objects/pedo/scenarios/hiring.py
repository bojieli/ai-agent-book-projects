"""Scenario A: Hiring Pipeline.

Objects: organizations, positions, candidates, interviews, evaluations, audit_logs
Constraints:
  - State machine on candidate status: applied -> screened -> interviewed -> offered -> hired/rejected
  - Referential integrity between candidates and positions
  - Cross-object validation: position must be open to accept new candidates
  - Role-based permissions: recruiters modify candidates, hiring managers approve offers,
    candidates view only their own records
"""

from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, Relationship, RelationshipAction,
    ReactionDeclaration,
)
from pedo.core.store import ObjectStore

# Valid state transitions for candidates
VALID_TRANSITIONS = {
    None: ["applied"],
    "applied": ["screened", "rejected"],
    "screened": ["interviewed", "rejected"],
    "interviewed": ["offered", "rejected"],
    "offered": ["hired", "rejected"],
    "hired": [],
    "rejected": [],
}


def validate_candidate_status(proposed, existing, accessor, store):
    """Validate candidate status follows the state machine."""
    new_status = proposed.content.get("status")
    if existing is None:
        # Creating a new candidate
        if new_status and new_status != "applied":
            return f"New candidates must start with status 'applied', got '{new_status}'"
        return True

    old_status = existing.content.get("status")
    if new_status and new_status != old_status:
        valid = VALID_TRANSITIONS.get(old_status, [])
        if new_status not in valid:
            return f"Invalid status transition: {old_status} -> {new_status}. Valid: {valid}"
    return True


def validate_position_open(proposed, existing, accessor, store):
    """Validate that the referenced position is still open."""
    position_id = proposed.content.get("position_id")
    if not position_id:
        return True

    position = store.raw_read(position_id)
    if position is None:
        return f"Position {position_id} not found"
    if position.content.get("status") != "open":
        return f"Position {position_id} is not open (status: {position.content.get('status')})"
    return True


def validate_salary_range(proposed, existing, accessor, store):
    """Validate salary expectation is within position range."""
    salary = proposed.content.get("salary_expectation")
    position_id = proposed.content.get("position_id")
    if salary is None or position_id is None:
        return True

    position = store.raw_read(position_id)
    if position is None:
        return True  # position validator will catch this

    min_sal = position.content.get("salary_min", 0)
    max_sal = position.content.get("salary_max", float("inf"))
    if not (min_sal <= salary <= max_sal):
        return f"Salary {salary} outside position range [{min_sal}, {max_sal}]"
    return True


def validate_interview_candidate_exists(proposed, existing, accessor, store):
    """Validate that the candidate for an interview exists and is in correct status."""
    candidate_id = proposed.content.get("candidate_id")
    if not candidate_id:
        return "Interview must reference a candidate"

    candidate = store.raw_read(candidate_id)
    if candidate is None:
        return f"Candidate {candidate_id} not found"
    if existing is None:
        # Creating new interview: candidate must be in screened status
        if candidate.content.get("status") not in ("screened", "interviewed"):
            return f"Candidate must be screened/interviewed for interview, got {candidate.content.get('status')}"
    return True


def validate_evaluation_interview_exists(proposed, existing, accessor, store):
    """Validate that the interview for an evaluation exists."""
    interview_id = proposed.content.get("interview_id")
    if not interview_id:
        return "Evaluation must reference an interview"

    interview = store.raw_read(interview_id)
    if interview is None:
        return f"Interview {interview_id} not found"
    return True


# Reaction handlers
def create_audit_log(event, store):
    """Create an audit log entry after any candidate status change."""
    system = AccessContext(user_id="system", role="system", org_id=event["object_org"])
    log = DataObject(
        type_name="audit_log",
        content={
            "action": event["event"],
            "object_id": event["object_id"],
            "object_type": event["object_type"],
            "changed_fields": event.get("changed_fields", []),
            "timestamp": event["timestamp"],
        },
        owner_id="system",
        org_id=event["object_org"],
    )
    store.create(log, system, _reaction_depth=event["depth"])


def register_hiring_types(store: ObjectStore):
    """Register all hiring pipeline types with the store."""

    # Organization (root of hierarchy)
    store.register_type(ObjectType(
        name="organization",
        fields={"name": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["recruiter", "hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["recruiter", "hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"roles": ["admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"roles": ["admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.MANAGE, {"roles": ["admin"]}),
        ],
        default_policy=Operation.DENY,
    ))

    # Position
    store.register_type(ObjectType(
        name="position",
        fields={"title": "str", "department": "str", "status": "str",
                "salary_min": "int", "salary_max": "int"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["recruiter", "hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"roles": ["hiring_manager", "admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["recruiter", "hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"roles": ["hiring_manager", "admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"roles": ["admin"]}),
        ],
        default_policy=Operation.DENY,
    ))

    # Candidate
    store.register_type(ObjectType(
        name="candidate",
        fields={"name": "str", "email": "str", "status": "str",
                "position_id": "str", "salary_expectation": "int"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["recruiter", "hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"roles": ["recruiter", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["recruiter", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["recruiter", "hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"roles": ["recruiter", "admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"roles": ["admin"]}),
            # Candidates can only read their own record (via is_owner above)
            # Hiring managers can read but not modify (no WRITE rule for them)
            PermissionRule(Operation.DENY, PrivilegeType.WRITE, {"role": "hiring_manager"}),
        ],
        validators=[validate_candidate_status, validate_position_open, validate_salary_range],
        reactions=[
            ReactionDeclaration(event="after_update:status", handler="create_audit_log"),
            ReactionDeclaration(event="after_create", handler="create_audit_log"),
        ],
        relationships=[
            Relationship(name="position", target_type="position",
                         on_delete=RelationshipAction.RESTRICT, required=True),
        ],
        default_policy=Operation.DENY,
    ))

    # Interview
    store.register_type(ObjectType(
        name="interview",
        fields={"candidate_id": "str", "interviewer": "str",
                "scheduled_at": "str", "notes": "str", "score": "int"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["recruiter", "hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"roles": ["hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["recruiter", "hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["recruiter", "hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"roles": ["hiring_manager", "admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"roles": ["admin"]}),
        ],
        validators=[validate_interview_candidate_exists],
        relationships=[
            Relationship(name="candidate", target_type="candidate",
                         on_delete=RelationshipAction.CASCADE),
        ],
        default_policy=Operation.DENY,
    ))

    # Evaluation
    store.register_type(ObjectType(
        name="evaluation",
        fields={"interview_id": "str", "decision": "str", "comments": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"roles": ["hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["hiring_manager", "admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"roles": ["hiring_manager", "admin"]}),
            # Recruiters can NOT see evaluations
            PermissionRule(Operation.DENY, PrivilegeType.READ, {"role": "recruiter"}),
        ],
        validators=[validate_evaluation_interview_exists],
        relationships=[
            Relationship(name="interview", target_type="interview",
                         on_delete=RelationshipAction.CASCADE),
        ],
        default_policy=Operation.DENY,
    ))

    # Audit Log (system-only, immutable)
    store.register_type(ObjectType(
        name="audit_log",
        fields={"action": "str", "object_id": "str", "object_type": "str",
                "changed_fields": "list", "timestamp": "float"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "system"}),
            PermissionRule(Operation.DENY, PrivilegeType.WRITE, {}),  # immutable
            PermissionRule(Operation.DENY, PrivilegeType.DELETE, {}),  # immutable
        ],
        default_policy=Operation.DENY,
    ))

    # Register reaction handlers
    store.register_reaction_handler("create_audit_log", create_audit_log)
