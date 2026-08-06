"""Tests for both application scenarios."""

import pytest
import time
from pedo.core.models import AccessContext, DataObject, PermissionRule, Operation, PrivilegeType
from pedo.core.store import ObjectStore, PermissionDeniedError, ValidationError, ReferentialIntegrityError
from pedo.scenarios.hiring import register_hiring_types
from pedo.scenarios.project_mgmt import register_project_mgmt_types

DSN = "dbname=pedo_test"

# ── Scenario A: Hiring Pipeline ───────────────────────────────


@pytest.fixture
def hiring_store():
    s = ObjectStore(DSN)
    s.clear_all()
    register_hiring_types(s)
    return s


@pytest.fixture
def recruiter():
    return AccessContext(user_id="recruiter1", role="recruiter", org_id="acme")


@pytest.fixture
def hiring_manager():
    return AccessContext(user_id="hm1", role="hiring_manager", org_id="acme")


@pytest.fixture
def admin():
    return AccessContext(user_id="admin1", role="admin", org_id="acme")


@pytest.fixture
def system_ctx():
    return AccessContext(user_id="system", role="system", org_id="acme")


def _create_position(store, ctx, status="open"):
    return store.create(DataObject(
        type_name="position",
        content={"title": "Engineer", "department": "Eng", "status": status,
                 "salary_min": 80000, "salary_max": 150000},
        org_id="acme",
    ), ctx)


def test_candidate_lifecycle(hiring_store, recruiter, hiring_manager, system_ctx):
    """Test the full candidate lifecycle through the state machine."""
    pos = _create_position(hiring_store, system_ctx)

    # Create candidate (must start as 'applied')
    cand = hiring_store.create(DataObject(
        type_name="candidate",
        content={"name": "Alice", "email": "alice@test.com", "status": "applied",
                 "position_id": pos.id, "salary_expectation": 100000},
        org_id="acme",
    ), recruiter)

    # Valid transitions
    hiring_store.update(cand.id, {"status": "screened"}, recruiter)
    hiring_store.update(cand.id, {"status": "interviewed"}, recruiter)
    hiring_store.update(cand.id, {"status": "offered"}, recruiter)
    hiring_store.update(cand.id, {"status": "hired"}, recruiter)

    # Process reactions (audit logs)
    hiring_store.process_reactions_sync()
    logs = hiring_store.get_reaction_log()
    assert len(logs) >= 4  # create + 4 status changes


def test_invalid_status_transition(hiring_store, recruiter, system_ctx):
    pos = _create_position(hiring_store, system_ctx)
    cand = hiring_store.create(DataObject(
        type_name="candidate",
        content={"name": "Bob", "email": "bob@test.com", "status": "applied",
                 "position_id": pos.id},
        org_id="acme",
    ), recruiter)

    # Skip screened -> directly to offered (invalid)
    with pytest.raises(ValidationError, match="Invalid status transition"):
        hiring_store.update(cand.id, {"status": "offered"}, recruiter)


def test_closed_position_rejects_candidate(hiring_store, recruiter, system_ctx):
    pos = _create_position(hiring_store, system_ctx, status="closed")

    with pytest.raises(ValidationError, match="not open"):
        hiring_store.create(DataObject(
            type_name="candidate",
            content={"name": "Charlie", "email": "c@test.com", "status": "applied",
                     "position_id": pos.id},
            org_id="acme",
        ), recruiter)


def test_salary_out_of_range(hiring_store, recruiter, system_ctx):
    pos = _create_position(hiring_store, system_ctx)

    with pytest.raises(ValidationError, match="Salary.*outside position range"):
        hiring_store.create(DataObject(
            type_name="candidate",
            content={"name": "Dave", "email": "d@test.com", "status": "applied",
                     "position_id": pos.id, "salary_expectation": 200000},
            org_id="acme",
        ), recruiter)


def test_hiring_manager_cannot_modify_candidate(hiring_store, recruiter, hiring_manager, system_ctx):
    pos = _create_position(hiring_store, system_ctx)
    cand = hiring_store.create(DataObject(
        type_name="candidate",
        content={"name": "Eve", "email": "e@test.com", "status": "applied",
                 "position_id": pos.id},
        org_id="acme",
    ), recruiter)

    # Hiring manager can read but not write
    read = hiring_store.get(cand.id, hiring_manager)
    assert read is not None

    with pytest.raises(PermissionDeniedError):
        hiring_store.update(cand.id, {"status": "screened"}, hiring_manager)


def test_recruiter_cannot_see_evaluations(hiring_store, recruiter, hiring_manager, system_ctx):
    pos = _create_position(hiring_store, system_ctx)
    cand = hiring_store.create(DataObject(
        type_name="candidate",
        content={"name": "Frank", "email": "f@test.com", "status": "applied",
                 "position_id": pos.id},
        org_id="acme",
    ), recruiter)
    hiring_store.update(cand.id, {"status": "screened"}, recruiter)

    interview = hiring_store.create(DataObject(
        type_name="interview",
        content={"candidate_id": cand.id, "interviewer": "hm1",
                 "scheduled_at": "2024-01-15", "notes": "", "score": 0},
        org_id="acme",
    ), hiring_manager)

    evaluation = hiring_store.create(DataObject(
        type_name="evaluation",
        content={"interview_id": interview.id, "decision": "proceed", "comments": "Strong candidate"},
        org_id="acme",
    ), hiring_manager)

    # Recruiter cannot see evaluation
    with pytest.raises(PermissionDeniedError):
        hiring_store.get(evaluation.id, recruiter)


# ── Scenario B: Multi-tenant Project Management ───────────────


@pytest.fixture
def pm_store():
    s = ObjectStore(DSN)
    s.clear_all()
    register_project_mgmt_types(s)
    return s


@pytest.fixture
def org_admin():
    return AccessContext(user_id="admin1", role="org_admin", org_id="tenant_a")


@pytest.fixture
def project_admin():
    return AccessContext(user_id="pa1", role="project_admin", org_id="tenant_a")


@pytest.fixture
def member():
    return AccessContext(user_id="m1", role="member", org_id="tenant_a")


@pytest.fixture
def other_tenant_member():
    return AccessContext(user_id="other1", role="member", org_id="tenant_b")


@pytest.fixture
def guest():
    return AccessContext(user_id="guest1", role="guest", org_id="tenant_a")


def test_task_lifecycle(pm_store, project_admin, member):
    proj = pm_store.create(DataObject(
        type_name="project",
        content={"name": "Alpha", "status": "active", "members": ["m1", "pa1"]},
        org_id="tenant_a",
    ), project_admin)

    task = pm_store.create(DataObject(
        type_name="task",
        content={"title": "Build feature", "status": "todo", "priority": "high",
                 "assignee_id": "m1", "project_id": proj.id},
        org_id="tenant_a",
    ), member)

    # Valid transitions
    pm_store.update(task.id, {"status": "in_progress"}, member)
    pm_store.update(task.id, {"status": "review"}, member)
    pm_store.update(task.id, {"status": "done"}, member)


def test_invalid_task_transition(pm_store, project_admin, member):
    proj = pm_store.create(DataObject(
        type_name="project",
        content={"name": "Beta", "status": "active", "members": ["m1", "pa1"]},
        org_id="tenant_a",
    ), project_admin)

    task = pm_store.create(DataObject(
        type_name="task",
        content={"title": "Bug fix", "status": "todo", "priority": "medium",
                 "project_id": proj.id},
        org_id="tenant_a",
    ), member)

    # Can't go from todo -> done (must go through in_progress, review)
    with pytest.raises(ValidationError, match="Invalid task transition"):
        pm_store.update(task.id, {"status": "done"}, member)


def test_invalid_priority(pm_store, project_admin, member):
    proj = pm_store.create(DataObject(
        type_name="project",
        content={"name": "Gamma", "status": "active", "members": ["m1"]},
        org_id="tenant_a",
    ), project_admin)

    with pytest.raises(ValidationError, match="Invalid priority"):
        pm_store.create(DataObject(
            type_name="task",
            content={"title": "Task", "status": "todo", "priority": "URGENT",
                     "project_id": proj.id},
            org_id="tenant_a",
        ), member)


def test_assignee_must_be_member(pm_store, project_admin, member):
    proj = pm_store.create(DataObject(
        type_name="project",
        content={"name": "Delta", "status": "active", "members": ["m1"]},
        org_id="tenant_a",
    ), project_admin)

    with pytest.raises(ValidationError, match="not a member"):
        pm_store.create(DataObject(
            type_name="task",
            content={"title": "Task", "status": "todo", "priority": "low",
                     "assignee_id": "nonexistent_user", "project_id": proj.id},
            org_id="tenant_a",
        ), member)


def test_tenant_isolation(pm_store, project_admin, other_tenant_member):
    proj = pm_store.create(DataObject(
        type_name="project",
        content={"name": "Secret Project", "status": "active", "members": ["pa1"]},
        org_id="tenant_a",
    ), project_admin)

    # Other tenant can't read the project
    with pytest.raises(PermissionDeniedError):
        pm_store.get(proj.id, other_tenant_member)


def test_guest_cannot_modify_task(pm_store, project_admin, guest):
    proj = pm_store.create(DataObject(
        type_name="project",
        content={"name": "Public", "status": "active", "members": ["pa1", "guest1"]},
        org_id="tenant_a",
    ), project_admin)

    task = pm_store.create(DataObject(
        type_name="task",
        content={"title": "Read-only task", "status": "todo", "priority": "low",
                 "project_id": proj.id},
        org_id="tenant_a",
    ), project_admin)

    # Guest can read
    read = pm_store.get(task.id, guest)
    assert read is not None

    # Guest cannot modify
    with pytest.raises(PermissionDeniedError):
        pm_store.update(task.id, {"status": "in_progress"}, guest)


def test_temporal_guest_access(pm_store, project_admin):
    """Test that guest access with expired temporal bounds is denied."""
    proj = pm_store.create(DataObject(
        type_name="project",
        content={"name": "Temporal", "status": "active", "members": ["pa1"]},
        org_id="tenant_a",
    ), project_admin)

    task = pm_store.create(DataObject(
        type_name="task",
        content={"title": "Temporal task", "status": "todo", "priority": "low",
                 "project_id": proj.id},
        org_id="tenant_a",
        # Override permission rules with temporal bound for guest
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ,
                           {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE,
                           {"roles": ["member", "project_admin", "org_admin", "system"]}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ,
                           {"role": "guest"},
                           valid_from=time.time() - 200,
                           valid_until=time.time() - 100),  # expired
        ],
    ), project_admin)

    expired_guest = AccessContext(user_id="old_guest", role="guest", org_id="tenant_a")
    with pytest.raises(PermissionDeniedError):
        pm_store.get(task.id, expired_guest)
