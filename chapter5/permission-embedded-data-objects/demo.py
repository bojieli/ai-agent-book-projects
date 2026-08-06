#!/usr/bin/env python3
"""实验 5-12：动态生成软件的数据层权限边界。"""

from __future__ import annotations

import os

from pedo.core.models import AccessContext, DataObject
from pedo.core.store import (
    ObjectStore,
    PermissionDeniedError,
    ValidationError,
)
from pedo.scenarios.hiring import register_hiring_types


def main() -> None:
    dsn = os.environ.get("PEDO_DSN", "dbname=pedo_test")
    store = ObjectStore(dsn)
    store.clear_all()
    register_hiring_types(store)

    system = AccessContext(user_id="system", role="system", org_id="acme")
    recruiter = AccessContext(user_id="recruiter1", role="recruiter", org_id="acme")
    other_tenant = AccessContext(
        user_id="intruder", role="recruiter", org_id="other-org"
    )

    position = store.create(
        DataObject(
            type_name="position",
            content={
                "title": "Platform Engineer",
                "department": "Infrastructure",
                "status": "open",
                "salary_min": 80_000,
                "salary_max": 150_000,
            },
            org_id="acme",
        ),
        system,
    )
    candidate = store.create(
        DataObject(
            type_name="candidate",
            content={
                "name": "Alice",
                "email": "alice@example.com",
                "status": "applied",
                "position_id": position.id,
                "salary_expectation": 100_000,
            },
            org_id="acme",
        ),
        recruiter,
    )

    store.update(candidate.id, {"status": "screened"}, recruiter)
    print("accepted: applied -> screened")

    attempts = [
        (
            "skip state transition",
            lambda: store.update(candidate.id, {"status": "hired"}, recruiter),
        ),
        (
            "salary outside position range",
            lambda: store.update(
                candidate.id, {"salary_expectation": 500_000}, recruiter
            ),
        ),
        (
            "cross-tenant read",
            lambda: store.get(candidate.id, other_tenant),
        ),
    ]

    for label, operation in attempts:
        try:
            operation()
        except (PermissionDeniedError, ValidationError) as exc:
            print(f"rejected: {label} -> {type(exc).__name__}: {exc}")
        else:
            raise AssertionError(f"data layer failed to reject: {label}")

    store.process_reactions_sync()
    print(f"objects: {store.count_objects()} | reactions: {len(store.get_reaction_log())}")


if __name__ == "__main__":
    main()
