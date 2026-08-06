"""Faithful AgentSpec wrapper for head-to-head empirical comparison.

This module provides:
  1. `register_*_types_no_policy` — register hiring / pm types with PE rules and
     validators stripped (relationships/reactions kept for structural integrity).
     The store accepts every operation; AgentSpec rules below are the only
     enforcement layer.
  2. `AgentSpecStore` — a wrapper around `ObjectStore` that runs an AgentSpec
     enforcer on every create/update/delete call before delegating. If any rule
     fires with `action='block'` the call raises `ValueError`, mirroring how a
     real AgentSpec deployment intercepts agent-issued tool calls at the action
     boundary (before the underlying tool runs).

The rules themselves come from `agentspec_baseline.create_hiring_enforcer` and
`create_pm_enforcer`, unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    Relationship, RelationshipAction, ReactionDeclaration,
)
from pedo.core.store import ObjectStore

from .agentspec_baseline import (
    AgentActionEnforcer,
    create_hiring_enforcer,
    create_pm_enforcer,
)


# ── Schema registration without PE rules/validators ──

def register_hiring_types_no_policy(store: ObjectStore):
    """Register hiring types with no permission rules and no validators.

    Relationships are kept so structural delete-cascade still applies; this
    matches AgentSpec's deployment model where the underlying data layer
    provides referential integrity but no policy."""
    accept_all = Operation.ACCEPT
    for name, fields in [
        ("organization", {"name": "str"}),
        ("position", {"title": "str", "department": "str", "status": "str",
                      "salary_min": "int", "salary_max": "int"}),
    ]:
        store.register_type(ObjectType(
            name=name, fields=fields, permission_rules=[],
            default_policy=accept_all,
        ))
    store.register_type(ObjectType(
        name="candidate",
        fields={"name": "str", "email": "str", "status": "str",
                "position_id": "str", "salary_expectation": "int"},
        permission_rules=[], validators=[],
        relationships=[Relationship(name="position", target_type="position",
                                    on_delete=RelationshipAction.RESTRICT,
                                    required=True)],
        default_policy=accept_all,
    ))
    store.register_type(ObjectType(
        name="interview",
        fields={"candidate_id": "str", "interviewer": "str",
                "scheduled_at": "str", "notes": "str", "score": "int"},
        permission_rules=[], validators=[],
        relationships=[Relationship(name="candidate", target_type="candidate",
                                    on_delete=RelationshipAction.CASCADE)],
        default_policy=accept_all,
    ))
    store.register_type(ObjectType(
        name="evaluation",
        fields={"interview_id": "str", "decision": "str", "comments": "str"},
        permission_rules=[], validators=[],
        relationships=[Relationship(name="interview", target_type="interview",
                                    on_delete=RelationshipAction.CASCADE)],
        default_policy=accept_all,
    ))
    store.register_type(ObjectType(
        name="audit_log",
        fields={"action": "str", "object_id": "str", "object_type": "str",
                "changed_fields": "list", "timestamp": "float"},
        permission_rules=[],
        default_policy=accept_all,
    ))


def register_pm_types_no_policy(store: ObjectStore):
    """Register project-mgmt types with no permission rules and no validators."""
    accept_all = Operation.ACCEPT
    store.register_type(ObjectType(
        name="pm_organization",
        fields={"name": "str", "plan": "str"},
        permission_rules=[], default_policy=accept_all,
    ))
    store.register_type(ObjectType(
        name="project",
        fields={"name": "str", "description": "str", "status": "str",
                "members": "list"},
        permission_rules=[], validators=[],
        default_policy=accept_all,
    ))
    store.register_type(ObjectType(
        name="task",
        fields={"title": "str", "description": "str", "status": "str",
                "priority": "str", "assignee_id": "str", "project_id": "str",
                "due_date": "str"},
        permission_rules=[], validators=[],
        relationships=[Relationship(name="project", target_type="project",
                                    on_delete=RelationshipAction.CASCADE,
                                    required=True)],
        default_policy=accept_all,
    ))
    store.register_type(ObjectType(
        name="comment",
        fields={"task_id": "str", "author_id": "str", "body": "str"},
        permission_rules=[], validators=[],
        relationships=[Relationship(name="task", target_type="task",
                                    on_delete=RelationshipAction.CASCADE)],
        default_policy=accept_all,
    ))
    store.register_type(ObjectType(
        name="attachment",
        fields={"task_id": "str", "filename": "str", "size_bytes": "int",
                "mime_type": "str"},
        permission_rules=[], validators=[],
        relationships=[Relationship(name="task", target_type="task",
                                    on_delete=RelationshipAction.CASCADE)],
        default_policy=accept_all,
    ))
    store.register_type(ObjectType(
        name="pm_audit_log",
        fields={"action": "str", "object_id": "str", "object_type": "str",
                "changed_fields": "list", "timestamp": "float"},
        permission_rules=[], default_policy=accept_all,
    ))


# ── Store wrapper ──

class AgentSpecStore:
    """Wrap an ObjectStore so create/update/delete go through an AgentSpec
    enforcer first. If any rule fires with action='block', raise ValueError
    (mirroring agent-action enforcement at the tool-call boundary)."""

    def __init__(self, store: ObjectStore, enforcer: AgentActionEnforcer):
        self._store = store
        self._enforcer = enforcer
        self.blocked: list[dict] = []

    # ── enforced operations ──

    def create(self, obj: DataObject, accessor: AccessContext, **kw) -> DataObject:
        ctx = self._context_for_create(obj, accessor)
        args = {"object_type": obj.type_name, "content": obj.content,
                "org_id": obj.org_id, "updates": dict(obj.content or {})}
        self._enforce("store.create", args, ctx)
        return self._store.create(obj, accessor, **kw)

    def update(self, object_id: str, changes: dict, accessor: AccessContext, **kw) -> DataObject:
        ctx = self._context_for_update(object_id, accessor)
        args = {"object_id": object_id, "updates": changes,
                "org_id": ctx.get("object_org")}
        self._enforce("store.update", args, ctx)
        return self._store.update(object_id, changes, accessor, **kw)

    def delete(self, object_id: str, accessor: AccessContext, **kw) -> bool:
        ctx = self._context_for_update(object_id, accessor)
        args = {"object_id": object_id, "org_id": ctx.get("object_org")}
        self._enforce("store.delete", args, ctx)
        return self._store.delete(object_id, accessor, **kw)

    # ── pass-through ──

    def get(self, object_id: str, accessor: AccessContext) -> Optional[DataObject]:
        return self._store.get(object_id, accessor)

    def query(self, accessor: AccessContext, type_name: str, filters: dict | None = None):
        return self._store.query(accessor, type_name, filters or {})

    def raw_read(self, object_id: str):
        return self._store.raw_read(object_id)

    def __getattr__(self, name):
        # delegate any other method (e.g. register_type, clear_all) to the wrapped store
        return getattr(self._store, name)

    # ── helpers ──

    def _enforce(self, tool: str, args: dict, ctx: dict):
        allowed, msg = self._enforcer.check_action(tool, args, ctx)
        if not allowed:
            self.blocked.append({"tool": tool, "ctx": ctx, "args": args, "message": msg})
            raise ValueError(msg)

    def _context_for_create(self, obj: DataObject, accessor: AccessContext) -> dict:
        ctx: dict[str, Any] = {
            "role": accessor.role,
            "caller_org": accessor.org_id,
            "caller_user": accessor.user_id,
            "object_type": obj.type_name,
            "object_org": obj.org_id,
            "current_status": None,
        }
        # If the content references a position/project, pull its status into ctx
        pid = (obj.content or {}).get("position_id")
        if pid:
            pos = self._store.raw_read(pid)
            if pos:
                ctx["position_status"] = pos.content.get("status")
                ctx["position_salary_max"] = pos.content.get("salary_max")
                ctx["position_salary_min"] = pos.content.get("salary_min")
        return ctx

    def _context_for_update(self, object_id: str, accessor: AccessContext) -> dict:
        ctx: dict[str, Any] = {
            "role": accessor.role,
            "caller_org": accessor.org_id,
            "caller_user": accessor.user_id,
            "object_type": None,
            "object_org": None,
            "current_status": None,
        }
        existing = self._store.raw_read(object_id)
        if existing:
            ctx["object_type"] = existing.type_name
            ctx["object_org"] = existing.org_id
            ctx["current_status"] = (existing.content or {}).get("status")
            pid = (existing.content or {}).get("position_id")
            if pid:
                pos = self._store.raw_read(pid)
                if pos:
                    ctx["position_status"] = pos.content.get("status")
                    ctx["position_salary_max"] = pos.content.get("salary_max")
                    ctx["position_salary_min"] = pos.content.get("salary_min")
        return ctx


# ── Convenience constructors ──

def make_hiring_agentspec_store(dsn: str) -> AgentSpecStore:
    store = ObjectStore(dsn)
    store.clear_all()
    register_hiring_types_no_policy(store)
    return AgentSpecStore(store, create_hiring_enforcer())


def make_pm_agentspec_store(dsn: str) -> AgentSpecStore:
    store = ObjectStore(dsn)
    store.clear_all()
    register_pm_types_no_policy(store)
    return AgentSpecStore(store, create_pm_enforcer())
