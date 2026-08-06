"""Tests for the core object store."""

import pytest
from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, Relationship, RelationshipAction,
    ReactionDeclaration,
)
from pedo.core.store import ObjectStore, PermissionDeniedError, ValidationError, ReferentialIntegrityError

DSN = "dbname=pedo_test"


@pytest.fixture
def store():
    s = ObjectStore(DSN)
    s.clear_all()

    # Register a simple type
    s.register_type(ObjectType(
        name="document",
        fields={"title": "str", "body": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "reader"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "writer"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "writer"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "writer"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"role": "reader"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"role": "writer"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"role": "writer"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"role": "writer"}),
        ],
        default_policy=Operation.DENY,
    ))
    return s


@pytest.fixture
def writer_ctx():
    return AccessContext(user_id="user1", role="writer", org_id="org1")


@pytest.fixture
def reader_ctx():
    return AccessContext(user_id="user2", role="reader", org_id="org1")


@pytest.fixture
def anon_ctx():
    return AccessContext(user_id="anon", role="anonymous")


def test_create_and_read(store, writer_ctx, reader_ctx):
    obj = DataObject(type_name="document", content={"title": "Hello", "body": "World"})
    created = store.create(obj, writer_ctx)
    assert created.id == obj.id

    read = store.get(created.id, reader_ctx)
    assert read is not None
    assert read.content["title"] == "Hello"


def test_permission_denied_on_read(store, writer_ctx, anon_ctx):
    obj = DataObject(type_name="document", content={"title": "Secret"})
    created = store.create(obj, writer_ctx)

    with pytest.raises(PermissionDeniedError):
        store.get(created.id, anon_ctx)


def test_permission_denied_on_write(store, writer_ctx, reader_ctx):
    obj = DataObject(type_name="document", content={"title": "Hello"})
    created = store.create(obj, writer_ctx)

    with pytest.raises(PermissionDeniedError):
        store.update(created.id, {"title": "Changed"}, reader_ctx)


def test_update(store, writer_ctx, reader_ctx):
    obj = DataObject(type_name="document", content={"title": "V1", "body": "text"})
    created = store.create(obj, writer_ctx)

    updated = store.update(created.id, {"title": "V2"}, writer_ctx)
    assert updated.content["title"] == "V2"
    assert updated.content["body"] == "text"


def test_delete(store, writer_ctx, reader_ctx):
    obj = DataObject(type_name="document", content={"title": "ToDelete"})
    created = store.create(obj, writer_ctx)

    store.delete(created.id, writer_ctx)
    assert store.raw_read(created.id) is None


def test_validator_rejects(store, writer_ctx):
    def no_empty_title(proposed, existing, accessor, st):
        if not proposed.content.get("title"):
            return "Title cannot be empty"
        return True

    store.types["document"].validators = [no_empty_title]

    obj = DataObject(type_name="document", content={"title": "", "body": "text"})
    with pytest.raises(ValidationError, match="Title cannot be empty"):
        store.create(obj, writer_ctx)


def test_reactions_fire(store, writer_ctx):
    log = []

    def on_create(event, st):
        log.append(event["event"])

    store.types["document"].reactions = [
        ReactionDeclaration(event="after_create", handler="log_create"),
    ]
    store.register_reaction_handler("log_create", on_create)

    obj = DataObject(type_name="document", content={"title": "Test"})
    store.create(obj, writer_ctx)
    store.process_reactions_sync()

    assert "after_create" in log


def test_temporal_permission():
    """Test that time-bounded permissions work."""
    import time
    rule = PermissionRule(
        Operation.ACCEPT, PrivilegeType.READ,
        condition={"role": "guest"},
        valid_from=time.time() - 100,
        valid_until=time.time() + 100,
    )
    ctx = AccessContext(user_id="g", role="guest")
    assert rule.matches(ctx, PrivilegeType.READ, time.time()) is True

    expired_rule = PermissionRule(
        Operation.ACCEPT, PrivilegeType.READ,
        condition={"role": "guest"},
        valid_from=time.time() - 200,
        valid_until=time.time() - 100,
    )
    assert expired_rule.matches(ctx, PrivilegeType.READ, time.time()) is False
