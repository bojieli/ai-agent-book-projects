"""Case study: Enterprise Agent Sandbox.

Architectural pattern demonstrated: **per-agent permissions for runtime AI actors**.
Multiple autonomous agents operate against the same data layer, each with its
own AccessContext and its own scoped role. Permission rules in the schema
declare what each agent role may do; the pipeline enforces the boundary
regardless of the agent's intent, hallucinations, or prompt-injection.

Object types: document, employee, invoice, email, agent_action_log
Agent roles:
  - hr_agent:        full read/write on employee; no document/invoice
  - finance_agent:   full read/write on invoice; public documents only
  - email_agent:     send email (with PII validator); no other access
  - general_agent:   public documents + employee directory (name/dept) only
  - junior_agent:    same as general but consequential ops are PENDING
  - human roles (admin, hr_manager, finance_manager) for completeness

Demonstrates:
  - structural rejection of out-of-scope reads/writes
  - prompt-injection resistance (agent told to delete -> rule rejects)
  - exfiltration prevention via PII-in-email validator
  - human-in-loop via Operation.PENDING for junior_agent's
    consequential operations
  - audit reactions logging every agent action
"""
from __future__ import annotations

from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, ReactionDeclaration,
    Relationship, RelationshipAction,
)
from pedo.core.store import ObjectStore


# Sentinel patterns we treat as PII for the email validator.
_PII_MARKERS = ("ssn:", "salary:", "comp:", "dob:", "credit-card:",
                "diagnosis:", "patient-id:")


def validate_email_no_pii(proposed, existing, accessor, store):
    """Block emails containing PII unless sender is HR (who is permitted to
    handle PII intentionally). The validator reads the email body; the
    schema-author writes this once and it applies to every agent that
    composes an email."""
    body = (proposed.content.get("body") or "").lower()
    for marker in _PII_MARKERS:
        if marker in body:
            if accessor.role not in ("hr_manager", "hr_agent"):
                return f"PII marker {marker!r} in email body; sender role {accessor.role!r} not authorized"
    return True


def validate_classification_for_role(proposed, existing, accessor, store):
    """Confidential documents may only be created or modified by humans
    (hr_manager, finance_manager, admin). Agents may not author confidential
    content -- they are explicitly out-of-scope here."""
    classification = proposed.content.get("classification", "internal")
    if classification == "confidential":
        if accessor.role not in ("admin", "hr_manager", "finance_manager"):
            return (f"confidential documents require human authorship; "
                    f"role {accessor.role!r} cannot author")
    return True


def log_agent_action(event, store):
    """Reaction: log every operation traceable to an agent role."""
    sys_ctx = AccessContext(user_id="system", role="system", org_id=event["object_org"])
    log = DataObject(
        type_name="agent_action_log",
        content={
            "action": event["event"],
            "object_id": event["object_id"],
            "object_type": event["object_type"],
            "fields": event.get("changed_fields", []),
            "timestamp": event["timestamp"],
        },
        owner_id="system",
        org_id=event["object_org"],
    )
    store.create(log, sys_ctx, _reaction_depth=event["depth"])


def register_enterprise_agent_types(store: ObjectStore) -> None:
    store.register_reaction_handler("log_agent_action", log_agent_action)

    # ── document: classification-aware access ──────────────────────────
    store.register_type(ObjectType(
        name="document",
        fields={"title": "str", "body": "str", "classification": "str"},  # public/internal/confidential
        permission_rules=[
            # Admins can do anything on documents.
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"role": "admin"}),
            # HR / finance managers can author internal & confidential docs in their domain.
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "hr_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "finance_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "hr_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "finance_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "hr_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "finance_manager"}),
            # Finance agent: read public docs only (no INSERT, no WRITE, no DELETE).
            # Enforcement of "public only" is by the validator below.
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "finance_agent"}),
            # General/junior agent: read public docs only.
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "general_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "junior_agent"}),
            # System role for reactions.
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "system"}),
            # Notably absent for ALL agents: DELETE, WRITE, INSERT.
            # An agent prompt-injected to "delete all internal documents" hits default-deny.
        ],
        validators=[validate_classification_for_role],
        reactions=[
            ReactionDeclaration(event="after_create", handler="log_agent_action"),
            ReactionDeclaration(event="after_update", handler="log_agent_action"),
            ReactionDeclaration(event="after_delete", handler="log_agent_action"),
        ],
        default_policy=Operation.DENY,
    ))

    # ── employee: HR-only edit; directory-view for general agent ──────
    # In a real system, "directory-view" would be enforced by separate object
    # types or by output-projection middleware. Here we expose two sister
    # types: employee (full record, HR-only) and employee_directory (limited
    # fields, broader read). This is a common PE idiom -- different access
    # patterns get different object types.
    store.register_type(ObjectType(
        name="employee",
        fields={"name": "str", "email": "str", "ssn": "str",
                "salary": "int", "dob": "str", "department": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "hr_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "hr_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "hr_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "admin"}),
            # HR agent: full HR scope.
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "hr_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "hr_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "hr_agent"}),
            # System for reactions.
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            # NOT GRANTED: finance_agent, email_agent, general_agent, junior_agent.
            # Default deny -> any of those reading/writing/inserting an employee fails.
        ],
        reactions=[
            ReactionDeclaration(event="after_create", handler="log_agent_action"),
            ReactionDeclaration(event="after_update", handler="log_agent_action"),
        ],
        default_policy=Operation.DENY,
    ))

    # ── invoice: finance-domain only ───────────────────────────────────
    store.register_type(ObjectType(
        name="invoice",
        fields={"vendor": "str", "amount": "int", "status": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "finance_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "finance_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "finance_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "admin"}),
            # Finance agent: read+write within scope.
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "finance_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "finance_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "finance_agent"}),
            # Junior agent: read OK, but consequential WRITE requires human approval (PENDING).
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "junior_agent"}),
            PermissionRule(Operation.PENDING, PrivilegeType.WRITE, {"role": "junior_agent"}),
            # Finance agent itself does not have DELETE on invoice -> default deny if attempted.
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
        ],
        reactions=[
            ReactionDeclaration(event="after_create", handler="log_agent_action"),
            ReactionDeclaration(event="after_update", handler="log_agent_action"),
        ],
        default_policy=Operation.DENY,
    ))

    # ── email: send-only for email_agent; PII filter applies to all  ──
    store.register_type(ObjectType(
        name="email",
        fields={"recipients": "str", "subject": "str", "body": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "hr_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "finance_manager"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "hr_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "finance_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "email_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "general_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "junior_agent"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
        ],
        validators=[validate_email_no_pii],  # blocks PII for non-HR senders
        reactions=[
            ReactionDeclaration(event="after_create", handler="log_agent_action"),
        ],
        default_policy=Operation.DENY,
    ))

    # ── agent_action_log: append-only audit ─────────────────────────────
    store.register_type(ObjectType(
        name="agent_action_log",
        fields={"action": "str", "object_id": "str", "object_type": "str",
                "fields": "list", "timestamp": "float"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            # Notably absent: any WRITE / DELETE rule -> log is append-only.
        ],
        default_policy=Operation.DENY,
    ))
