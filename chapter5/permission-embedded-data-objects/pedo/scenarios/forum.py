"""Case study: Forum / community.

Architectural pattern demonstrated: **public-read + owner-edit + moderator override**.
Posts are publicly readable but only the author can edit them; moderators can
delete or lock any post regardless of authorship. Comments are owned by their
author. This pattern shows multiple-rule permission composition --- a single
type carries an owner rule, a public rule, and a moderator-override rule.

Object types: forum_post, comment, moderation_log
Key invariants:
  - posts are publicly readable
  - only the post author can edit content
  - moderators can lock or delete any post
  - locked posts cannot be edited (even by author)
  - comments inherit the lock from their parent post
"""
from __future__ import annotations

from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, ReactionDeclaration,
    Relationship, RelationshipAction,
)
from pedo.core.store import ObjectStore


def validate_post_not_locked(proposed, existing, accessor, store):
    """Locked posts cannot be edited (even by the author).
    Moderators can still lock/unlock via the 'locked' field itself."""
    if existing is None:
        return True
    if existing.content.get("locked"):
        # Allow only the moderator unlock action: the only legal change is
        # 'locked' going from True to False or remaining True.
        for field, new_val in proposed.content.items():
            if field == "locked":
                continue
            if existing.content.get(field) != new_val:
                if accessor.role != "moderator":
                    return f"post is locked; field {field!r} cannot be edited"
    return True


def validate_comment_parent_not_locked(proposed, existing, accessor, store):
    """Comments cannot be added to or edited on a locked post."""
    post_id = proposed.content.get("post_id")
    if not post_id:
        return True
    post = store.raw_read(post_id)
    if post is None:
        return f"parent post {post_id} not found"
    if post.content.get("locked") and accessor.role != "moderator":
        return "parent post is locked; comments cannot be added"
    return True


def log_moderation(event, store):
    """Reaction: log every moderator-driven change (lock, delete) to a
    moderation_log so the community can audit moderator actions."""
    sys_ctx = AccessContext(user_id="system", role="system", org_id=event["object_org"])
    log = DataObject(
        type_name="moderation_log",
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


def register_forum_types(store: ObjectStore) -> None:
    store.register_reaction_handler("log_moderation", log_moderation)

    store.register_type(ObjectType(
        name="forum_post",
        fields={"title": "str", "body": "str", "locked": "bool"},
        permission_rules=[
            # Public read.
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {}),
            # Any authenticated user can post.
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {}),
            # Author can edit.
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"is_owner": True}),
            # Moderators have override on edit + delete.
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "moderator"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"role": "moderator"}),
            # Author cannot delete (community-history preservation).
        ],
        validators=[validate_post_not_locked],
        reactions=[
            # Note: moderation log fires on every post update; in practice,
            # one would filter on changed_fields for moderator-only events.
            ReactionDeclaration(event="after_update:locked", handler="log_moderation"),
            ReactionDeclaration(event="after_delete", handler="log_moderation"),
        ],
        default_policy=Operation.DENY,
    ))

    store.register_type(ObjectType(
        name="comment",
        fields={"post_id": "str", "body": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"is_owner": True}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"role": "moderator"}),
        ],
        validators=[validate_comment_parent_not_locked],
        relationships=[
            Relationship(name="post", target_type="forum_post",
                         on_delete=RelationshipAction.CASCADE),
        ],
        default_policy=Operation.DENY,
    ))

    store.register_type(ObjectType(
        name="moderation_log",
        fields={"action": "str", "object_id": "str", "object_type": "str",
                "fields": "list", "timestamp": "float"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {}),  # public audit
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {}),
        ],
        default_policy=Operation.DENY,
    ))
