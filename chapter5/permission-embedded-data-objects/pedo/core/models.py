"""Core data models for permission-embedded data objects."""

from __future__ import annotations
import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Operation(Enum):
    ACCEPT = "ACCEPT"
    DENY = "DENY"
    PENDING = "PENDING"


class PrivilegeType(Enum):
    # Self permissions
    READ = "READ"
    WRITE = "WRITE"
    # Child permissions
    SELECT = "SELECT"
    INSERT = "INSERT"
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    MANAGE = "MANAGE"
    APPROVE = "APPROVE"


class RelationshipAction(Enum):
    CASCADE = "CASCADE"
    RESTRICT = "RESTRICT"
    NULLIFY = "NULLIFY"


@dataclass
class PermissionRule:
    """A single permission rule in the filter chain."""
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
            if key == "role":
                if accessor.role != value:
                    return False
            elif key == "roles":
                if accessor.role not in value:
                    return False
            elif key == "is_owner":
                if value and not accessor.is_owner:
                    return False
            elif key == "org_id":
                if accessor.org_id != value:
                    return False
            elif key == "user_id":
                if accessor.user_id != value:
                    return False
            elif key == "group":
                if value not in accessor.groups:
                    return False
        return True


@dataclass
class AccessContext:
    """Identity and attributes of the accessor."""
    user_id: str
    role: str = "anonymous"
    org_id: Optional[str] = None
    groups: list[str] = field(default_factory=list)
    is_owner: bool = False
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """A declared relationship between object types."""
    name: str
    target_type: str
    on_delete: RelationshipAction = RelationshipAction.RESTRICT
    required: bool = False


@dataclass
class ReactionDeclaration:
    """A declared reaction that fires after a successful write."""
    event: str  # e.g., "after_update:status", "after_create", "after_delete"
    handler: str  # Name of the handler function


@dataclass
class ObjectType:
    """Schema definition for a type of object."""
    name: str
    fields: dict[str, str]  # field_name -> type_string
    permission_rules: list[PermissionRule] = field(default_factory=list)
    validators: list = field(default_factory=list)  # list of callable validators
    reactions: list[ReactionDeclaration] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    default_policy: Operation = Operation.DENY
    parent_type: Optional[str] = None  # Type name in management hierarchy


@dataclass
class DataObject:
    """A permission-embedded data object instance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type_name: str = ""
    content: dict[str, Any] = field(default_factory=dict)
    owner_id: str = ""
    org_id: str = ""
    parent_id: Optional[str] = None
    permission_rules: Optional[list[PermissionRule]] = None  # None = inherit from type
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    references: dict[str, str] = field(default_factory=dict)  # ref_name -> target_object_id
