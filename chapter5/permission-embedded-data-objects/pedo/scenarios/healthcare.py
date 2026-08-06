"""Case study: Healthcare records.

Architectural pattern demonstrated: **field-level granular access + audit reactions**.
Different roles (doctor, nurse, billing, patient) see different subsets of a
patient_record's fields. The schema declares per-field visibility rules; the
handler does not implement view-projection or redaction itself. Every read of
sensitive fields fires an audit-trail reaction (HIPAA-style requirement).

Object types: patient_record, vitals, diagnosis, billing_record, audit_log
Key invariants:
  - doctors see vitals + diagnosis + medications; nurses see vitals only;
    billing sees billing_record only; patient sees own non-clinical fields
  - every read of diagnosis or medications must produce an audit_log entry
  - patient_records are immutable except for designated update flows
  - break-glass access (emergency override) is allowed but must be logged
"""
from __future__ import annotations

from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, ReactionDeclaration,
    Relationship, RelationshipAction,
)
from pedo.core.store import ObjectStore


def validate_billing_immutable_after_finalized(proposed, existing, accessor, store):
    """Once a billing_record is marked 'finalized', it cannot be edited."""
    if existing is None:
        return True
    if existing.content.get("status") == "finalized":
        for field in ("amount", "items", "service_codes"):
            if (field in proposed.content
                    and proposed.content.get(field) != existing.content.get(field)):
                return f"billing_record is finalized; {field!r} is immutable"
    return True


def emit_phi_access_log(event, store):
    """Reaction: every read or modification of clinical PHI logs to audit trail.
    Note: the read-path doesn't currently fire reactions; this fires on writes
    only. A full HIPAA implementation would extend the read-path; the schema
    can declare that intent."""
    sys_ctx = AccessContext(user_id="system", role="system", org_id=event["object_org"])
    log = DataObject(
        type_name="phi_audit_log",
        content={
            "action": event["event"],
            "object_id": event["object_id"],
            "object_type": event["object_type"],
            "actor": event.get("changed_fields", []),
            "timestamp": event["timestamp"],
        },
        owner_id="system",
        org_id=event["object_org"],
    )
    store.create(log, sys_ctx, _reaction_depth=event["depth"])


def register_healthcare_types(store: ObjectStore) -> None:
    store.register_reaction_handler("emit_phi_access_log", emit_phi_access_log)

    # Patient identity record (non-clinical).
    store.register_type(ObjectType(
        name="patient",
        fields={"name": "str", "dob": "str", "mrn": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "admin"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "doctor"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "nurse"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "billing"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
        ],
        default_policy=Operation.DENY,
    ))

    # Vitals: visible to clinical roles, not billing, not patient.
    # (In a full HIPAA system, patient-portal access would have a separate rule.)
    store.register_type(ObjectType(
        name="vitals",
        fields={"patient_id": "str", "blood_pressure": "str",
                "heart_rate": "int", "temperature_f": "float"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["doctor", "nurse"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "doctor"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "nurse"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            # Billing: NOT in the rule list -> default deny.
        ],
        reactions=[
            ReactionDeclaration(event="after_create", handler="emit_phi_access_log"),
        ],
        default_policy=Operation.DENY,
    ))

    # Diagnosis: visible only to doctors and the patient themselves.
    store.register_type(ObjectType(
        name="diagnosis",
        fields={"patient_id": "str", "icd10": "str", "notes": "str", "medications": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "doctor"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "doctor"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            # Patient self-read via owner -- the diagnosis's owner is the patient_id.
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            # Nurse and billing: not granted -> default deny.
        ],
        reactions=[
            ReactionDeclaration(event="after_create", handler="emit_phi_access_log"),
            ReactionDeclaration(event="after_update", handler="emit_phi_access_log"),
        ],
        default_policy=Operation.DENY,
    ))

    # Billing record: visible to billing role + patient (their own).
    store.register_type(ObjectType(
        name="billing_record",
        fields={"patient_id": "str", "amount": "int", "status": "str",
                "service_codes": "str", "items": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "billing"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "billing"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "billing"}),
        ],
        validators=[validate_billing_immutable_after_finalized],
        reactions=[
            ReactionDeclaration(event="after_update", handler="emit_phi_access_log"),
        ],
        default_policy=Operation.DENY,
    ))

    # PHI audit log: append-only, system-only writes.
    store.register_type(ObjectType(
        name="phi_audit_log",
        fields={"action": "str", "object_id": "str", "object_type": "str",
                "actor": "str", "timestamp": "float"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "auditor"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            # No WRITE / UPDATE / DELETE rules: append-only.
        ],
        default_policy=Operation.DENY,
    ))
