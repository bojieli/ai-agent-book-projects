"""Evaluation 6.5: Reaction System vs PostgreSQL Triggers.

Compares Tier 3 reactions with PostgreSQL AFTER triggers implementing
equivalent logic. Measures:
  - Cascade depth observed
  - Failure propagation behavior
  - Trace completeness for debugging
  - Execution time for consequence chains
"""

import json
import time
import uuid
import psycopg2
import psycopg2.extras
import numpy as np
from tabulate import tabulate

from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, ReactionDeclaration,
)
from pedo.core.store import ObjectStore, ValidationError

DSN = "dbname=pedo_test"


# ── PostgreSQL Trigger Setup ──────────────────────────────────

def setup_trigger_tables(conn):
    """Set up tables with PostgreSQL AFTER triggers implementing the same logic."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS trig_audit_log CASCADE")
        cur.execute("DROP TABLE IF EXISTS trig_counters CASCADE")
        cur.execute("DROP TABLE IF EXISTS trig_notifications CASCADE")
        cur.execute("DROP TABLE IF EXISTS trig_candidates CASCADE")
        cur.execute("""
            CREATE TABLE trig_candidates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'applied',
                org_id TEXT NOT NULL DEFAULT '',
                updated_at DOUBLE PRECISION NOT NULL DEFAULT 0
            );
            CREATE TABLE trig_audit_log (
                id SERIAL PRIMARY KEY,
                action TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                old_status TEXT,
                new_status TEXT,
                timestamp DOUBLE PRECISION NOT NULL
            );
            CREATE TABLE trig_notifications (
                id SERIAL PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DOUBLE PRECISION NOT NULL
            );
            CREATE TABLE trig_counters (
                status TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 0
            );
            INSERT INTO trig_counters (status, count) VALUES
                ('applied', 0), ('screened', 0), ('interviewed', 0),
                ('offered', 0), ('hired', 0), ('rejected', 0)
            ON CONFLICT (status) DO NOTHING;
        """)

        # Trigger 1: Audit log on status change
        cur.execute("""
            CREATE OR REPLACE FUNCTION trig_audit_status()
            RETURNS TRIGGER AS $$
            BEGIN
                IF OLD.status IS DISTINCT FROM NEW.status THEN
                    INSERT INTO trig_audit_log (action, candidate_id, old_status, new_status, timestamp)
                    VALUES ('status_change', NEW.id, OLD.status, NEW.status, EXTRACT(EPOCH FROM NOW()));
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            DROP TRIGGER IF EXISTS audit_status ON trig_candidates;
            CREATE TRIGGER audit_status AFTER UPDATE ON trig_candidates
                FOR EACH ROW EXECUTE FUNCTION trig_audit_status();
        """)

        # Trigger 2: Notification on status change
        cur.execute("""
            CREATE OR REPLACE FUNCTION trig_notify_status()
            RETURNS TRIGGER AS $$
            BEGIN
                IF OLD.status IS DISTINCT FROM NEW.status THEN
                    INSERT INTO trig_notifications (candidate_id, message, timestamp)
                    VALUES (NEW.id, 'Status changed to ' || NEW.status, EXTRACT(EPOCH FROM NOW()));
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            DROP TRIGGER IF EXISTS notify_status ON trig_candidates;
            CREATE TRIGGER notify_status AFTER UPDATE ON trig_candidates
                FOR EACH ROW EXECUTE FUNCTION trig_notify_status();
        """)

        # Trigger 3: Counter update on status change
        cur.execute("""
            CREATE OR REPLACE FUNCTION trig_update_counter()
            RETURNS TRIGGER AS $$
            BEGIN
                IF OLD.status IS DISTINCT FROM NEW.status THEN
                    UPDATE trig_counters SET count = count - 1 WHERE status = OLD.status;
                    UPDATE trig_counters SET count = count + 1 WHERE status = NEW.status;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            DROP TRIGGER IF EXISTS update_counter ON trig_candidates;
            CREATE TRIGGER update_counter AFTER UPDATE ON trig_candidates
                FOR EACH ROW EXECUTE FUNCTION trig_update_counter();
        """)

    conn.commit()


def setup_trigger_failure_test(conn):
    """Set up a trigger that will fail to test failure propagation."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS trig_fail_test CASCADE")
        cur.execute("""
            CREATE TABLE trig_fail_test (
                id TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            );
        """)
        # Trigger that fails on specific value
        cur.execute("""
            CREATE OR REPLACE FUNCTION trig_fail_on_value()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.value = 999 THEN
                    RAISE EXCEPTION 'Trigger failure: value 999 not allowed in consequence';
                END IF;
                -- try to insert into a log table
                INSERT INTO trig_audit_log (action, candidate_id, old_status, new_status, timestamp)
                VALUES ('value_change', NEW.id, '', CAST(NEW.value AS TEXT), EXTRACT(EPOCH FROM NOW()));
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            DROP TRIGGER IF EXISTS fail_trigger ON trig_fail_test;
            CREATE TRIGGER fail_trigger AFTER UPDATE ON trig_fail_test
                FOR EACH ROW EXECUTE FUNCTION trig_fail_on_value();
        """)
    conn.commit()


# ── PEDO Reaction Setup ──────────────────────────────────────

def setup_reaction_store():
    """Set up PEDO store with equivalent reaction logic."""
    store = ObjectStore(DSN)
    store.clear_all()

    def reaction_audit_log(event, st):
        system = AccessContext(user_id="system", role="system", org_id=event["object_org"])
        st.create(DataObject(
            type_name="r_audit_log",
            content={
                "action": "status_change",
                "candidate_id": event["object_id"],
                "old_status": "",
                "new_status": event["object_content"].get("status", ""),
                "timestamp": event["timestamp"],
            },
            org_id=event["object_org"],
        ), system, _reaction_depth=event["depth"])

    def reaction_notification(event, st):
        system = AccessContext(user_id="system", role="system", org_id=event["object_org"])
        st.create(DataObject(
            type_name="r_notification",
            content={
                "candidate_id": event["object_id"],
                "message": f"Status changed to {event['object_content'].get('status', '')}",
                "timestamp": event["timestamp"],
            },
            org_id=event["object_org"],
        ), system, _reaction_depth=event["depth"])

    def reaction_counter(event, st):
        # In PEDO model, counters would be maintained by updating a counter object
        system = AccessContext(user_id="system", role="system", org_id=event["object_org"])
        st.create(DataObject(
            type_name="r_counter_event",
            content={
                "new_status": event["object_content"].get("status", ""),
                "timestamp": event["timestamp"],
            },
            org_id=event["object_org"],
        ), system, _reaction_depth=event["depth"])

    store.register_type(ObjectType(
        name="r_candidate",
        fields={"name": "str", "status": "str"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "system"}),
        ],
        reactions=[
            ReactionDeclaration(event="after_update:status", handler="audit_log"),
            ReactionDeclaration(event="after_update:status", handler="notification"),
            ReactionDeclaration(event="after_update:status", handler="counter"),
        ],
        default_policy=Operation.DENY,
    ))

    for tname in ["r_audit_log", "r_notification", "r_counter_event"]:
        store.register_type(ObjectType(
            name=tname,
            fields={"action": "str", "candidate_id": "str", "message": "str",
                     "timestamp": "float", "old_status": "str", "new_status": "str"},
            permission_rules=[
                PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "system"}),
                PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            ],
            default_policy=Operation.DENY,
        ))

    store.register_reaction_handler("audit_log", reaction_audit_log)
    store.register_reaction_handler("notification", reaction_notification)
    store.register_reaction_handler("counter", reaction_counter)

    return store


# ── Benchmarks ────────────────────────────────────────────────

def benchmark_trigger_chain(n: int) -> dict:
    """Benchmark PostgreSQL triggers processing a status change chain."""
    conn = psycopg2.connect(DSN)
    setup_trigger_tables(conn)

    latencies = []
    for i in range(n):
        cid = str(uuid.uuid4())
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO trig_candidates (id, name, status, org_id, updated_at) VALUES (%s, %s, %s, %s, %s)",
                (cid, f"Candidate {i}", "applied", "org1", time.time())
            )
        conn.commit()

        # Status change triggers all 3 triggers
        start = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute("UPDATE trig_candidates SET status = 'screened', updated_at = %s WHERE id = %s",
                        (time.time(), cid))
        conn.commit()
        latencies.append((time.perf_counter() - start) * 1000)

    # Check results
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM trig_audit_log")
        audit_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM trig_notifications")
        notif_count = cur.fetchone()[0]

    conn.close()
    return {
        "latencies": latencies,
        "audit_count": audit_count,
        "notification_count": notif_count,
        "stats": _stats(latencies),
    }


def benchmark_reaction_chain(n: int) -> dict:
    """Benchmark PEDO reactions processing the same status change chain."""
    store = setup_reaction_store()
    system = AccessContext(user_id="system", role="system", org_id="org1")

    latencies = []
    for i in range(n):
        cand = store.create(DataObject(
            type_name="r_candidate",
            content={"name": f"Candidate {i}", "status": "applied"},
            org_id="org1",
        ), system)

        start = time.perf_counter()
        store.update(cand.id, {"status": "screened"}, system)
        store.process_reactions_sync()  # Process reactions synchronously for fair timing
        latencies.append((time.perf_counter() - start) * 1000)

    audit_count = store.count_objects("r_audit_log")
    notif_count = store.count_objects("r_notification")

    return {
        "latencies": latencies,
        "audit_count": audit_count,
        "notification_count": notif_count,
        "reaction_log": store.get_reaction_log(),
        "stats": _stats(latencies),
    }


def benchmark_trigger_failure(n: int) -> dict:
    """Test what happens when a trigger fails."""
    conn = psycopg2.connect(DSN)
    setup_trigger_tables(conn)
    setup_trigger_failure_test(conn)

    successes = 0
    failures = 0
    rollbacks = 0

    for i in range(n):
        rid = str(uuid.uuid4())
        with conn.cursor() as cur:
            cur.execute("INSERT INTO trig_fail_test (id, value) VALUES (%s, %s)", (rid, 0))
        conn.commit()

        try:
            with conn.cursor() as cur:
                # Update to 999 should trigger failure
                cur.execute("UPDATE trig_fail_test SET value = 999 WHERE id = %s", (rid,))
            conn.commit()
            successes += 1
        except Exception:
            conn.rollback()
            rollbacks += 1

            # Check: was the original update rolled back?
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM trig_fail_test WHERE id = %s", (rid,))
                val = cur.fetchone()[0]
                if val == 0:
                    failures += 1  # trigger failure rolled back the update

    conn.close()
    return {
        "total": n,
        "successes": successes,
        "trigger_failures_causing_rollback": failures,
        "rollbacks": rollbacks,
    }


def benchmark_reaction_failure(n: int) -> dict:
    """Test what happens when a reaction fails."""
    store = ObjectStore(DSN)
    store.clear_all()

    def failing_reaction(event, st):
        raise ValueError("Reaction failure: simulated error")

    store.register_type(ObjectType(
        name="fail_test",
        fields={"value": "int"},
        permission_rules=[
            PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.WRITE, {"role": "system"}),
            PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "system"}),
        ],
        reactions=[
            ReactionDeclaration(event="after_update:value", handler="fail_handler"),
        ],
        default_policy=Operation.DENY,
    ))
    store.register_reaction_handler("fail_handler", failing_reaction)

    system = AccessContext(user_id="system", role="system")
    original_writes_preserved = 0
    reaction_failures_logged = 0

    for i in range(n):
        obj = store.create(DataObject(
            type_name="fail_test",
            content={"value": 0},
        ), system)

        store.update(obj.id, {"value": 999}, system)
        store.process_reactions_sync()

        # Check: the original write should be preserved despite reaction failure
        current = store.raw_read(obj.id)
        if current and current.content["value"] == 999:
            original_writes_preserved += 1

    log = store.get_reaction_log()
    reaction_failures_logged = sum(1 for entry in log if not entry["success"])

    return {
        "total": n,
        "original_writes_preserved": original_writes_preserved,
        "reaction_failures_logged": reaction_failures_logged,
    }


def _stats(latencies):
    arr = np.array(latencies)
    return {
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "mean": float(np.mean(arr)),
    }


def run_reaction_benchmarks(n: int = 100):
    """Run the reaction vs trigger comparison."""
    print(f"\n{'='*80}")
    print(f"EVALUATION 6.5: Reaction System vs PostgreSQL Triggers (n={n})")
    print(f"{'='*80}\n")

    # ── Performance comparison ──
    print("Running trigger chain benchmark...")
    trig_result = benchmark_trigger_chain(n)
    print("Running reaction chain benchmark...")
    react_result = benchmark_reaction_chain(n)

    headers = ["System", "p50 (ms)", "p95 (ms)", "p99 (ms)", "Mean (ms)",
               "Audit Logs", "Notifications"]
    rows = [
        ["PG Triggers",
         f"{trig_result['stats']['p50']:.3f}", f"{trig_result['stats']['p95']:.3f}",
         f"{trig_result['stats']['p99']:.3f}", f"{trig_result['stats']['mean']:.3f}",
         trig_result['audit_count'], trig_result['notification_count']],
        ["PEDO Reactions",
         f"{react_result['stats']['p50']:.3f}", f"{react_result['stats']['p95']:.3f}",
         f"{react_result['stats']['p99']:.3f}", f"{react_result['stats']['mean']:.3f}",
         react_result['audit_count'], react_result['notification_count']],
    ]
    print("\nPerformance Comparison:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    # ── Failure propagation ──
    print("\n\nRunning failure propagation tests...")
    trig_fail = benchmark_trigger_failure(n)
    react_fail = benchmark_reaction_failure(n)

    print("\nFailure Propagation Behavior:")
    print("-" * 60)
    print(f"PostgreSQL Triggers (n={trig_fail['total']}):")
    print(f"  Trigger failure rolls back original write: {trig_fail['trigger_failures_causing_rollback']}/{trig_fail['total']}")
    print(f"  Original writes that succeeded despite trigger failure: {trig_fail['successes']}/{trig_fail['total']}")

    print(f"\nPEDO Reactions (n={react_fail['total']}):")
    print(f"  Original writes preserved despite reaction failure: {react_fail['original_writes_preserved']}/{react_fail['total']}")
    print(f"  Reaction failures logged: {react_fail['reaction_failures_logged']}/{react_fail['total']}")

    # ── Trace completeness ──
    print("\n\nTrace Completeness:")
    print("-" * 60)
    print(f"PostgreSQL Triggers: No built-in audit trace. Must query each table separately.")
    print(f"  Can reconstruct what happened: Partially (separate audit_log table)")
    print(f"  Can trace causality: No (no link between trigger and source event)")

    log = react_result["reaction_log"]
    print(f"\nPEDO Reactions: Full event trace with {len(log)} entries.")
    if log:
        print(f"  Each entry records: event, source_object_id, handler, success, error, depth")
        print(f"  Max depth observed: {max(e['depth'] for e in log)}")
        print(f"  Successful reactions: {sum(1 for e in log if e['success'])}/{len(log)}")
        print(f"  Failed reactions: {sum(1 for e in log if not e['success'])}/{len(log)}")

    return {
        "trigger_perf": trig_result,
        "reaction_perf": react_result,
        "trigger_failure": trig_fail,
        "reaction_failure": react_fail,
    }


if __name__ == "__main__":
    run_reaction_benchmarks()
