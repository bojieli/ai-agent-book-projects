"""Object store implementing the three-tier operation pipeline.

This is the core of the permission-embedded data objects prototype.
It sits as middleware on top of PostgreSQL, intercepting every operation
and running the full pipeline: permission checks, validators, object
store mechanics, and reactions.
"""

from __future__ import annotations
import json
import time
import logging
import threading
from collections import defaultdict
from dataclasses import asdict
from typing import Any, Callable, Optional
from queue import Queue

import psycopg2
import psycopg2.extras

from .models import (
    AccessContext, DataObject, ObjectType, Operation, PermissionRule,
    PrivilegeType, Relationship, RelationshipAction, ReactionDeclaration,
)

logger = logging.getLogger(__name__)


class PermissionDeniedError(Exception):
    """Raised when an operation is denied by permission rules."""
    pass


class ValidationError(Exception):
    """Raised when a validator rejects a proposed change."""
    pass


class ReferentialIntegrityError(Exception):
    """Raised when referential integrity would be violated."""
    pass


class ObjectStore:
    """Permission-embedded data object store with three-tier pipeline.

    Tier 1: Permission checks + read-only validators (synchronous, gates operation)
    Tier 2: Object store mechanics (synchronous, built-in, non-extensible)
    Tier 3: Reactions (asynchronous, queued, produces new operations)
    """

    def __init__(self, dsn: str, max_reaction_depth: int = 3):
        self.dsn = dsn
        self.max_reaction_depth = max_reaction_depth
        self.types: dict[str, ObjectType] = {}
        self.reaction_handlers: dict[str, Callable] = {}
        self._reaction_queue: Queue = Queue()
        self._reaction_thread: Optional[threading.Thread] = None
        self._reaction_log: list[dict] = []
        self._running = False
        self._setup_db()

    def _get_conn(self):
        return psycopg2.connect(self.dsn)

    def _setup_db(self):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS objects (
                        id TEXT PRIMARY KEY,
                        type_name TEXT NOT NULL,
                        content JSONB NOT NULL DEFAULT '{}',
                        owner_id TEXT NOT NULL,
                        org_id TEXT NOT NULL DEFAULT '',
                        parent_id TEXT,
                        permission_rules JSONB,
                        created_at DOUBLE PRECISION NOT NULL,
                        updated_at DOUBLE PRECISION NOT NULL,
                        refs JSONB NOT NULL DEFAULT '{}'
                    );
                    CREATE INDEX IF NOT EXISTS idx_objects_type ON objects(type_name);
                    CREATE INDEX IF NOT EXISTS idx_objects_parent ON objects(parent_id);
                    CREATE INDEX IF NOT EXISTS idx_objects_org ON objects(org_id);
                    CREATE INDEX IF NOT EXISTS idx_objects_owner ON objects(owner_id);

                    CREATE TABLE IF NOT EXISTS reaction_log (
                        id SERIAL PRIMARY KEY,
                        timestamp DOUBLE PRECISION NOT NULL,
                        event TEXT NOT NULL,
                        source_object_id TEXT NOT NULL,
                        handler TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        error TEXT,
                        depth INTEGER NOT NULL DEFAULT 0
                    );
                """)
            conn.commit()

    def register_type(self, obj_type: ObjectType):
        self.types[obj_type.name] = obj_type

    def register_reaction_handler(self, name: str, handler: Callable):
        self.reaction_handlers[name] = handler

    def start_reactions(self):
        self._running = True
        self._reaction_thread = threading.Thread(target=self._process_reactions, daemon=True)
        self._reaction_thread.start()

    def stop_reactions(self):
        self._running = False
        if self._reaction_thread:
            self._reaction_queue.put(None)  # sentinel
            self._reaction_thread.join(timeout=5)

    def drain_reactions(self, timeout: float = 5.0):
        """Wait for all queued reactions to complete."""
        self._reaction_queue.join()

    # ── Read Path ──────────────────────────────────────────────

    def get(self, object_id: str, accessor: AccessContext) -> Optional[DataObject]:
        """Read a single object. Permission check only (no validators/reactions)."""
        obj = self._load_object(object_id)
        if obj is None:
            return None
        self._check_permission(obj, accessor, PrivilegeType.READ)
        return obj

    def select(self, parent_id: str, accessor: AccessContext,
               type_name: Optional[str] = None,
               filters: Optional[dict] = None) -> list[DataObject]:
        """List child objects. Permission check on parent for SELECT."""
        parent = self._load_object(parent_id)
        if parent is None:
            return []
        self._check_permission(parent, accessor, PrivilegeType.SELECT)

        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM objects WHERE parent_id = %s"
                params: list[Any] = [parent_id]
                if type_name:
                    query += " AND type_name = %s"
                    params.append(type_name)
                cur.execute(query, params)
                rows = cur.fetchall()

        results = []
        for row in rows:
            obj = self._row_to_object(row)
            try:
                self._check_permission(obj, accessor, PrivilegeType.READ)
                if filters:
                    if all(obj.content.get(k) == v for k, v in filters.items()):
                        results.append(obj)
                else:
                    results.append(obj)
            except PermissionDeniedError:
                continue  # silently filter out inaccessible objects
        return results

    def query(self, accessor: AccessContext, type_name: str,
              filters: Optional[dict] = None, org_id: Optional[str] = None) -> list[DataObject]:
        """Query objects by type. Each result is permission-checked."""
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM objects WHERE type_name = %s"
                params: list[Any] = [type_name]
                if org_id:
                    query += " AND org_id = %s"
                    params.append(org_id)
                cur.execute(query, params)
                rows = cur.fetchall()

        results = []
        for row in rows:
            obj = self._row_to_object(row)
            try:
                self._check_permission(obj, accessor, PrivilegeType.READ)
                if filters:
                    if all(obj.content.get(k) == v for k, v in filters.items()):
                        results.append(obj)
                else:
                    results.append(obj)
            except PermissionDeniedError:
                continue
        return results

    # ── Write Path: Three-Tier Pipeline ────────────────────────

    def create(self, obj: DataObject, accessor: AccessContext,
               _reaction_depth: int = 0) -> DataObject:
        """Create a new object. Full pipeline."""
        obj_type = self._get_type(obj.type_name)

        # Tier 1: Permission check
        if obj.parent_id:
            parent = self._load_object(obj.parent_id)
            if parent is None:
                raise ReferentialIntegrityError(f"Parent {obj.parent_id} not found")
            self._check_permission(parent, accessor, PrivilegeType.INSERT)
        else:
            # Top-level create: check type-level permission rules
            self._check_type_permission(obj_type, accessor, PrivilegeType.INSERT)

        # Set ownership
        if not obj.owner_id:
            obj.owner_id = accessor.user_id
        if not obj.org_id and accessor.org_id:
            obj.org_id = accessor.org_id

        obj.created_at = time.time()
        obj.updated_at = obj.created_at

        # Tier 1: Validators
        for validator in obj_type.validators:
            result = validator(obj, None, accessor, self)
            if result is not True and result is not None:
                raise ValidationError(str(result))

        # Validate references
        self._validate_references(obj, obj_type)

        # Tier 2: Object store mechanics
        self._store_object(obj)

        # Tier 3: Queue reactions
        self._queue_reactions(obj, "after_create", _reaction_depth)

        return obj

    def update(self, object_id: str, changes: dict[str, Any],
               accessor: AccessContext, _reaction_depth: int = 0) -> DataObject:
        """Update an object. Full pipeline."""
        obj = self._load_object(object_id)
        if obj is None:
            raise ValueError(f"Object {object_id} not found")
        obj_type = self._get_type(obj.type_name)

        # Tier 1: Permission check
        if obj.parent_id:
            parent = self._load_object(obj.parent_id)
            if parent:
                self._check_permission(parent, accessor, PrivilegeType.UPDATE)
        # Also check self WRITE
        accessor_with_owner = AccessContext(
            user_id=accessor.user_id, role=accessor.role,
            org_id=accessor.org_id, groups=accessor.groups,
            is_owner=(accessor.user_id == obj.owner_id),
            attributes=accessor.attributes,
        )
        self._check_permission(obj, accessor_with_owner, PrivilegeType.WRITE)

        # Build proposed new state
        old_content = dict(obj.content)
        proposed = DataObject(
            id=obj.id, type_name=obj.type_name,
            content={**obj.content, **changes},
            owner_id=obj.owner_id, org_id=obj.org_id,
            parent_id=obj.parent_id, permission_rules=obj.permission_rules,
            created_at=obj.created_at, updated_at=time.time(),
            references=dict(obj.references),
        )

        # Tier 1: Validators
        for validator in obj_type.validators:
            result = validator(proposed, obj, accessor_with_owner, self)
            if result is not True and result is not None:
                raise ValidationError(str(result))

        # Tier 2: Commit the write
        obj.content = proposed.content
        obj.updated_at = proposed.updated_at
        self._update_object(obj)

        # Tier 3: Queue reactions
        changed_fields = [k for k in changes if old_content.get(k) != changes[k]]
        self._queue_reactions(obj, "after_update", _reaction_depth, changed_fields=changed_fields)

        return obj

    def delete(self, object_id: str, accessor: AccessContext,
               _reaction_depth: int = 0) -> bool:
        """Delete an object. Full pipeline."""
        obj = self._load_object(object_id)
        if obj is None:
            raise ValueError(f"Object {object_id} not found")
        obj_type = self._get_type(obj.type_name)

        # Tier 1: Permission check
        if obj.parent_id:
            parent = self._load_object(obj.parent_id)
            if parent:
                self._check_permission(parent, accessor, PrivilegeType.DELETE)
        accessor_with_owner = AccessContext(
            user_id=accessor.user_id, role=accessor.role,
            org_id=accessor.org_id, groups=accessor.groups,
            is_owner=(accessor.user_id == obj.owner_id),
            attributes=accessor.attributes,
        )
        self._check_permission(obj, accessor_with_owner, PrivilegeType.WRITE)

        # Tier 2: Object store mechanics — handle referential integrity
        self._handle_delete_cascades(obj, accessor, _reaction_depth)

        # Check for RESTRICT references from other objects
        self._check_restrict_references(obj)

        # Delete the object
        self._delete_object(object_id)

        # Tier 3: Queue reactions
        self._queue_reactions(obj, "after_delete", _reaction_depth)

        return True

    # ── Tier 1: Permission Evaluation ──────────────────────────

    def _check_permission(self, obj: DataObject, accessor: AccessContext,
                          privilege: PrivilegeType):
        """Evaluate permission filter chain. First match wins."""
        now = time.time()
        obj_type = self._get_type(obj.type_name)

        # Built-in tenant isolation: if the object has an org_id and the accessor
        # has a different org_id, deny access (unless the accessor is system)
        if (obj.org_id and accessor.org_id and
                obj.org_id != accessor.org_id and accessor.role != "system"):
            raise PermissionDeniedError(
                f"Tenant isolation: accessor org {accessor.org_id} != object org {obj.org_id}")

        # Collect rules: type-level rules + object-level overrides
        rules = obj.permission_rules if obj.permission_rules is not None else obj_type.permission_rules

        # Check hierarchy: walk up parent chain
        if obj.parent_id:
            parent_result = self._check_parent_permissions(obj.parent_id, accessor, privilege, now)
            if parent_result is not None:
                if parent_result == Operation.DENY:
                    raise PermissionDeniedError(
                        f"Access denied by parent hierarchy for {privilege.value} on {obj.id}")
                elif parent_result == Operation.ACCEPT:
                    return  # parent granted access

        # Evaluate own rules
        for rule in rules:
            # Map child privileges to self privileges for direct access
            effective_privilege = privilege
            if rule.matches(accessor, effective_privilege, now):
                if rule.operation == Operation.DENY:
                    raise PermissionDeniedError(
                        f"Access denied for {privilege.value} on {obj.id}")
                elif rule.operation == Operation.ACCEPT:
                    return
                elif rule.operation == Operation.PENDING:
                    raise PermissionDeniedError(
                        f"Access pending approval for {privilege.value} on {obj.id}")

        # Default policy
        if obj_type.default_policy == Operation.DENY:
            raise PermissionDeniedError(
                f"Default deny for {privilege.value} on {obj.id} (type={obj.type_name})")

    def _check_type_permission(self, obj_type: ObjectType, accessor: AccessContext,
                               privilege: PrivilegeType):
        """Check type-level permissions for top-level creates."""
        now = time.time()
        for rule in obj_type.permission_rules:
            if rule.matches(accessor, privilege, now):
                if rule.operation == Operation.DENY:
                    raise PermissionDeniedError(
                        f"Type-level deny for {privilege.value} on type {obj_type.name}")
                elif rule.operation == Operation.ACCEPT:
                    return
        if obj_type.default_policy == Operation.DENY:
            raise PermissionDeniedError(
                f"Default type-level deny for {privilege.value} on type {obj_type.name}")

    def _check_parent_permissions(self, parent_id: str, accessor: AccessContext,
                                  privilege: PrivilegeType, now: float) -> Optional[Operation]:
        """Walk up the hierarchy checking child permissions."""
        parent = self._load_object(parent_id)
        if parent is None:
            return None

        parent_type = self._get_type(parent.type_name)
        rules = parent.permission_rules if parent.permission_rules is not None else parent_type.permission_rules

        # Map self-privileges to child-privileges
        child_priv_map = {
            PrivilegeType.READ: PrivilegeType.SELECT,
            PrivilegeType.WRITE: PrivilegeType.UPDATE,
        }
        child_priv = child_priv_map.get(privilege, privilege)

        for rule in rules:
            if rule.matches(accessor, child_priv, now):
                return rule.operation

        # Recurse up
        if parent.parent_id:
            return self._check_parent_permissions(parent.parent_id, accessor, privilege, now)

        return None

    # ── Tier 2: Object Store Mechanics ─────────────────────────

    def _validate_references(self, obj: DataObject, obj_type: ObjectType):
        """Validate that all declared references point to existing objects."""
        for rel in obj_type.relationships:
            ref_id = obj.references.get(rel.name) or obj.content.get(rel.name + "_id")
            if ref_id:
                target = self._load_object(ref_id)
                if target is None:
                    raise ReferentialIntegrityError(
                        f"Referenced object {ref_id} for relationship {rel.name} not found")
                if target.type_name != rel.target_type:
                    raise ReferentialIntegrityError(
                        f"Referenced object {ref_id} is type {target.type_name}, expected {rel.target_type}")
            elif rel.required:
                raise ReferentialIntegrityError(
                    f"Required relationship {rel.name} not set on {obj.id}")

    def _handle_delete_cascades(self, obj: DataObject, accessor: AccessContext,
                                reaction_depth: int):
        """Handle CASCADE and NULLIFY for child objects."""
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Find children
                cur.execute("SELECT * FROM objects WHERE parent_id = %s", (obj.id,))
                children = cur.fetchall()

        for child_row in children:
            child = self._row_to_object(child_row)
            child_type = self.types.get(child.type_name)
            if child_type:
                # Default: cascade delete children
                self.delete(child.id, accessor, _reaction_depth=reaction_depth)

        # Handle reference-based cascades
        for type_name, obj_type in self.types.items():
            for rel in obj_type.relationships:
                if rel.target_type == obj.type_name:
                    if rel.on_delete == RelationshipAction.CASCADE:
                        referencing = self._find_referencing_objects(obj.id, type_name, rel.name)
                        for ref_obj in referencing:
                            self.delete(ref_obj.id, accessor, _reaction_depth=reaction_depth)
                    elif rel.on_delete == RelationshipAction.NULLIFY:
                        referencing = self._find_referencing_objects(obj.id, type_name, rel.name)
                        for ref_obj in referencing:
                            ref_obj.content[rel.name + "_id"] = None
                            ref_obj.references.pop(rel.name, None)
                            self._update_object(ref_obj)

    def _check_restrict_references(self, obj: DataObject):
        """Check if any RESTRICT references prevent deletion."""
        for type_name, obj_type in self.types.items():
            for rel in obj_type.relationships:
                if rel.target_type == obj.type_name and rel.on_delete == RelationshipAction.RESTRICT:
                    referencing = self._find_referencing_objects(obj.id, type_name, rel.name)
                    if referencing:
                        raise ReferentialIntegrityError(
                            f"Cannot delete {obj.id}: referenced by {len(referencing)} "
                            f"{type_name} objects via {rel.name} (RESTRICT)")

    def _find_referencing_objects(self, target_id: str, type_name: str,
                                  rel_name: str) -> list[DataObject]:
        """Find objects that reference the target via a given relationship."""
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Check both content field and refs
                cur.execute("""
                    SELECT * FROM objects
                    WHERE type_name = %s
                    AND (content->>%s = %s OR refs->>%s = %s)
                """, (type_name, rel_name + "_id", target_id, rel_name, target_id))
                return [self._row_to_object(r) for r in cur.fetchall()]

    # ── Tier 3: Reactions ──────────────────────────────────────

    def _queue_reactions(self, obj: DataObject, event: str,
                         depth: int, changed_fields: Optional[list[str]] = None):
        """Queue reactions for asynchronous processing."""
        if depth >= self.max_reaction_depth:
            logger.warning(f"Reaction depth limit reached ({depth}) for {obj.id}")
            return

        obj_type = self._get_type(obj.type_name)
        for reaction in obj_type.reactions:
            should_fire = False
            if reaction.event == event:
                should_fire = True
            elif event == "after_update" and changed_fields:
                # Check field-specific reactions like "after_update:status"
                if ":" in reaction.event:
                    _, field_name = reaction.event.split(":", 1)
                    if field_name in changed_fields:
                        should_fire = True

            if should_fire:
                self._reaction_queue.put({
                    "event": reaction.event,
                    "handler": reaction.handler,
                    "object_id": obj.id,
                    "object_type": obj.type_name,
                    "object_content": dict(obj.content),
                    "object_owner": obj.owner_id,
                    "object_org": obj.org_id,
                    "depth": depth + 1,
                    "changed_fields": changed_fields or [],
                    "timestamp": time.time(),
                })

    def _process_reactions(self):
        """Background thread that processes queued reactions."""
        while self._running:
            item = self._reaction_queue.get()
            if item is None:
                self._reaction_queue.task_done()
                break
            try:
                handler = self.reaction_handlers.get(item["handler"])
                if handler:
                    handler(item, self)
                    self._log_reaction(item, success=True)
                else:
                    self._log_reaction(item, success=False,
                                       error=f"Handler {item['handler']} not found")
            except Exception as e:
                self._log_reaction(item, success=False, error=str(e))
                logger.error(f"Reaction failed: {item['handler']} for {item['object_id']}: {e}")
            finally:
                self._reaction_queue.task_done()

    def process_reactions_sync(self):
        """Process all queued reactions synchronously (for testing)."""
        while not self._reaction_queue.empty():
            item = self._reaction_queue.get()
            if item is None:
                self._reaction_queue.task_done()
                continue
            try:
                handler = self.reaction_handlers.get(item["handler"])
                if handler:
                    handler(item, self)
                    self._log_reaction(item, success=True)
                else:
                    self._log_reaction(item, success=False,
                                       error=f"Handler {item['handler']} not found")
            except Exception as e:
                self._log_reaction(item, success=False, error=str(e))
            finally:
                self._reaction_queue.task_done()

    def _log_reaction(self, item: dict, success: bool, error: Optional[str] = None):
        entry = {
            "timestamp": time.time(),
            "event": item["event"],
            "source_object_id": item["object_id"],
            "handler": item["handler"],
            "success": success,
            "error": error,
            "depth": item["depth"],
        }
        self._reaction_log.append(entry)
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO reaction_log (timestamp, event, source_object_id, handler, success, error, depth)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (entry["timestamp"], entry["event"], entry["source_object_id"],
                      entry["handler"], entry["success"], entry["error"], entry["depth"]))
            conn.commit()

    def get_reaction_log(self) -> list[dict]:
        return list(self._reaction_log)

    # ── Storage Layer ──────────────────────────────────────────

    def _store_object(self, obj: DataObject):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                rules_json = None
                if obj.permission_rules is not None:
                    rules_json = json.dumps([{
                        "operation": r.operation.value,
                        "privilege": r.privilege.value,
                        "condition": r.condition,
                        "valid_from": r.valid_from,
                        "valid_until": r.valid_until,
                    } for r in obj.permission_rules])

                cur.execute("""
                    INSERT INTO objects (id, type_name, content, owner_id, org_id,
                                        parent_id, permission_rules, created_at, updated_at, refs)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (obj.id, obj.type_name, json.dumps(obj.content),
                      obj.owner_id, obj.org_id, obj.parent_id,
                      rules_json, obj.created_at, obj.updated_at,
                      json.dumps(obj.references)))
            conn.commit()

    def _update_object(self, obj: DataObject):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE objects SET content = %s, updated_at = %s, refs = %s,
                                      parent_id = %s, org_id = %s
                    WHERE id = %s
                """, (json.dumps(obj.content), obj.updated_at,
                      json.dumps(obj.references), obj.parent_id,
                      obj.org_id, obj.id))
            conn.commit()

    def _delete_object(self, object_id: str):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM objects WHERE id = %s", (object_id,))
            conn.commit()

    def _load_object(self, object_id: str) -> Optional[DataObject]:
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM objects WHERE id = %s", (object_id,))
                row = cur.fetchone()
                if row is None:
                    return None
                return self._row_to_object(row)

    def _row_to_object(self, row: dict) -> DataObject:
        rules = None
        if row.get("permission_rules"):
            raw_rules = row["permission_rules"]
            if isinstance(raw_rules, str):
                raw_rules = json.loads(raw_rules)
            rules = [
                PermissionRule(
                    operation=Operation(r["operation"]),
                    privilege=PrivilegeType(r["privilege"]),
                    condition=r.get("condition", {}),
                    valid_from=r.get("valid_from"),
                    valid_until=r.get("valid_until"),
                )
                for r in raw_rules
            ]

        content = row["content"]
        if isinstance(content, str):
            content = json.loads(content)
        refs = row.get("refs", "{}")
        if isinstance(refs, str):
            refs = json.loads(refs)

        return DataObject(
            id=row["id"],
            type_name=row["type_name"],
            content=content,
            owner_id=row["owner_id"],
            org_id=row["org_id"],
            parent_id=row.get("parent_id"),
            permission_rules=rules,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            references=refs,
        )

    def _get_type(self, type_name: str) -> ObjectType:
        if type_name not in self.types:
            raise ValueError(f"Unknown object type: {type_name}")
        return self.types[type_name]

    # ── Utilities ──────────────────────────────────────────────

    def clear_all(self):
        """Clear all data (for testing)."""
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM objects")
                cur.execute("DELETE FROM reaction_log")
            conn.commit()
        self._reaction_log.clear()

    def count_objects(self, type_name: Optional[str] = None) -> int:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                if type_name:
                    cur.execute("SELECT COUNT(*) FROM objects WHERE type_name = %s", (type_name,))
                else:
                    cur.execute("SELECT COUNT(*) FROM objects")
                return cur.fetchone()[0]

    def raw_read(self, object_id: str) -> Optional[DataObject]:
        """Read without permission checks (for validators and internal use)."""
        return self._load_object(object_id)

    def raw_query(self, type_name: str, filters: Optional[dict] = None,
                  org_id: Optional[str] = None) -> list[DataObject]:
        """Query without permission checks (for validators)."""
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = "SELECT * FROM objects WHERE type_name = %s"
                params: list[Any] = [type_name]
                if org_id:
                    query += " AND org_id = %s"
                    params.append(org_id)
                cur.execute(query, params)
                rows = cur.fetchall()
        results = []
        for row in rows:
            obj = self._row_to_object(row)
            if filters:
                if all(obj.content.get(k) == v for k, v in filters.items()):
                    results.append(obj)
            else:
                results.append(obj)
        return results
