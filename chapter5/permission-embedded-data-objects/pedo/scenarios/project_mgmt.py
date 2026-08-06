"""Scenario B: Multi-tenant Project Management.

Objects: organizations, projects, tasks, comments, attachments
Constraints:
  - Tenant isolation: organizations cannot see each other's data
  - Hierarchical permissions: project admins manage tasks within their project
  - Cross-object validation: task assignee must be a project member
  - Referential integrity: deleting a project cascades to tasks
  - Temporal bounds: guest access expires
"""

import time
from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, Relationship, RelationshipAction,
    ReactionDeclaration,
)
from pedo.core.store import ObjectStore


# Task status state machine
VALID_TASK_TRANSITIONS = {
    None: ["todo"],
    "todo": ["in_progress", "cancelled"],
    "in_progress": ["review", "todo", "cancelled"],
    "review": ["done", "in_progress"],
    "done": [],
    "cancelled": ["todo"],  # can reopen
}

# Task priority values
VALID_PRIORITIES = ["low", "medium", "high", "critical"]


def validate_task_status(proposed, existing, accessor, store):
    """Validate task status follows the state machine."""
    new_status = proposed.content.get("status")
    if existing is None:
        if new_status and new_status != "todo":
            return f"New tasks must start with status 'todo', got '{new_status}'"
        return True

    old_status = existing.content.get("status")
    if new_status and new_status != old_status:
        valid = VALID_TASK_TRANSITIONS.get(old_status, [])
        if new_status not in valid:
            return f"Invalid task transition: {old_status} -> {new_status}. Valid: {valid}"
    return True


def validate_task_priority(proposed, existing, accessor, store):
    """Validate task priority is a valid value."""
    priority = proposed.content.get("priority")
    if priority and priority not in VALID_PRIORITIES:
        return f"Invalid priority '{priority}'. Valid: {VALID_PRIORITIES}"
    return True


def validate_task_assignee(proposed, existing, accessor, store):
    """Validate that the task assignee is a member of the project."""
    assignee_id = proposed.content.get("assignee_id")
    project_id = proposed.content.get("project_id")
    if not assignee_id or not project_id:
        return True

    project = store.raw_read(project_id)
    if project is None:
        return f"Project {project_id} not found"

    members = project.content.get("members", [])
    if assignee_id not in members:
        return f"Assignee {assignee_id} is not a member of project {project_id}"
    return True


def validate_project_org_match(proposed, existing, accessor, store):
    """Validate that the project belongs to the accessor's organization."""
    if accessor.role == "system":
        return True
    if proposed.org_id and accessor.org_id and proposed.org_id != accessor.org_id:
        return f"Cannot create project in organization {proposed.org_id} (you belong to {accessor.org_id})"
    return True


def validate_comment_task_exists(proposed, existing, accessor, store):
    """Validate that the task being commented on exists."""
    task_id = proposed.content.get("task_id")
    if not task_id:
        return "Comment must reference a task"
    task = store.raw_read(task_id)
    if task is None:
        return f"Task {task_id} not found"
    return True


def validate_attachment_size(proposed, existing, accessor, store):
    """Validate attachment size is within limits."""
    size = proposed.content.get("size_bytes", 0)
    if size > 100_000_000:  # 100MB
        return f"Attachment too large: {size} bytes (max 100MB)"
    return True


# Reaction handlers
def log_task_change(event, store):
    """Log task status changes."""
    system = AccessContext(user_id="system", role="system", org_id=event["object_org"])
    log = DataObject(
        type_name="pm_audit_log",
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


def register_project_mgmt_types(store: ObjectStore):
    """Register all project management types with the store."""

    # Organization (tenant root)
    store.register_type(ObjectType(
        name="pm_organization",
        fields={"name": "str", "plan": "str"},
        permission_rules=[
            # Tenant isolation: only members of the org can see it
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"roles": ["org_admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"roles": ["org_admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.MANAGE, {"roles": ["org_admin"]}),
        ],
        default_policy=Operation.DENY,
    ))

    # Project
    store.register_type(ObjectType(
        name="project",
        fields={"name": "str", "description": "str", "status": "str", "members": "list"},
        permission_rules=[
            # Tenant isolation via org_id condition
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"roles": ["project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"roles": ["project_admin", "org_admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"roles": ["org_admin"]}),
            # Guest access with temporal bounds (set per-object)
        ],
        validators=[validate_project_org_match],
        default_policy=Operation.DENY,
    ))

    # Task
    store.register_type(ObjectType(
        name="task",
        fields={"title": "str", "description": "str", "status": "str",
                "priority": "str", "assignee_id": "str", "project_id": "str",
                "due_date": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"roles": ["member", "project_admin", "org_admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"roles": ["project_admin", "org_admin"]}),
            # Guests can only read, not modify
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "guest"}),
            PermissionRule(Operation.DENY, PrivilegeType.WRITE, {"role": "guest"}),
        ],
        validators=[validate_task_status, validate_task_priority, validate_task_assignee],
        reactions=[
            ReactionDeclaration(event="after_update:status", handler="log_task_change"),
            ReactionDeclaration(event="after_create", handler="log_task_change"),
        ],
        relationships=[
            Relationship(name="project", target_type="project",
                         on_delete=RelationshipAction.CASCADE, required=True),
        ],
        default_policy=Operation.DENY,
    ))

    # Comment
    store.register_type(ObjectType(
        name="comment",
        fields={"task_id": "str", "author_id": "str", "body": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"is_owner": True}),  # only author can edit
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"roles": ["project_admin", "org_admin"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "guest"}),
        ],
        validators=[validate_comment_task_exists],
        relationships=[
            Relationship(name="task", target_type="task",
                         on_delete=RelationshipAction.CASCADE),
        ],
        default_policy=Operation.DENY,
    ))

    # Attachment
    store.register_type(ObjectType(
        name="attachment",
        fields={"task_id": "str", "filename": "str", "size_bytes": "int", "mime_type": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"roles": ["project_admin", "org_admin"]}),
        ],
        validators=[validate_attachment_size],
        relationships=[
            Relationship(name="task", target_type="task",
                         on_delete=RelationshipAction.CASCADE),
        ],
        default_policy=Operation.DENY,
    ))

    # Audit Log
    store.register_type(ObjectType(
        name="pm_audit_log",
        fields={"action": "str", "object_id": "str", "object_type": "str",
                "changed_fields": "list", "timestamp": "float"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"roles": ["org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "system"}),
            PermissionRule(Operation.DENY, PrivilegeType.WRITE, {}),
            PermissionRule(Operation.DENY, PrivilegeType.DELETE, {}),
        ],
        default_policy=Operation.DENY,
    ))

    # Register reaction handlers
    store.register_reaction_handler("log_task_change", log_task_change)
