"""Evaluation 6.3: Pipeline Overhead Benchmarks.

Measures the performance cost of the permission/validation pipeline.
Compares:
  (a) Raw PostgreSQL writes (baseline)
  (b) PostgreSQL with RLS
  (c) Permission-embedded objects (our system)

Varies: rule count, hierarchy depth, validator count, cross-object fan-out.
Reports: write latency (p50/p95/p99), read latency, throughput.
"""

import json
import time
import uuid
import statistics
import psycopg2
import psycopg2.extras
import numpy as np
from tabulate import tabulate

from pedo.core.models import (
    AccessContext, DataObject, ObjectType, Operation,
    PermissionRule, PrivilegeType, ReactionDeclaration,
)
from pedo.core.store import ObjectStore

DSN = "dbname=pedo_test"


def setup_rls_tables(conn):
    """Set up PostgreSQL tables with Row-Level Security."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS rls_objects CASCADE")
        cur.execute("""
            CREATE TABLE rls_objects (
                id TEXT PRIMARY KEY,
                type_name TEXT NOT NULL,
                content JSONB NOT NULL DEFAULT '{}',
                owner_id TEXT NOT NULL,
                org_id TEXT NOT NULL DEFAULT ''
            )
        """)
        cur.execute("ALTER TABLE rls_objects ENABLE ROW LEVEL SECURITY")
        cur.execute("DROP POLICY IF EXISTS org_isolation ON rls_objects")
        cur.execute("""
            CREATE POLICY org_isolation ON rls_objects
                USING (org_id = current_setting('app.org_id', true))
        """)
        # Create a non-superuser role for RLS to apply
        cur.execute("DO $$ BEGIN CREATE ROLE rls_user LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$")
        cur.execute("GRANT ALL ON rls_objects TO rls_user")
    conn.commit()


def setup_raw_table(conn):
    """Set up raw table with no protections."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS raw_objects CASCADE")
        cur.execute("""
            CREATE TABLE raw_objects (
                id TEXT PRIMARY KEY,
                type_name TEXT NOT NULL,
                content JSONB NOT NULL DEFAULT '{}',
                owner_id TEXT NOT NULL,
                org_id TEXT NOT NULL DEFAULT ''
            )
        """)
    conn.commit()


def benchmark_raw_writes(n: int) -> dict:
    """Benchmark raw PostgreSQL INSERT."""
    conn = psycopg2.connect(DSN)
    setup_raw_table(conn)

    latencies = []
    for i in range(n):
        oid = str(uuid.uuid4())
        content = json.dumps({"title": f"Object {i}", "status": "active"})
        start = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO raw_objects (id, type_name, content, owner_id, org_id) VALUES (%s, %s, %s, %s, %s)",
                (oid, "document", content, "user1", "org1"),
            )
        conn.commit()
        latencies.append((time.perf_counter() - start) * 1000)  # ms

    conn.close()
    return _compute_stats(latencies, "raw_write")


def benchmark_raw_reads(n: int) -> dict:
    """Benchmark raw PostgreSQL SELECT."""
    conn = psycopg2.connect(DSN)

    # Pre-populate
    ids = []
    for i in range(n):
        oid = str(uuid.uuid4())
        ids.append(oid)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO raw_objects (id, type_name, content, owner_id, org_id) VALUES (%s, %s, %s, %s, %s)",
                (oid, "document", json.dumps({"title": f"Object {i}"}), "user1", "org1"),
            )
    conn.commit()

    latencies = []
    for oid in ids:
        start = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM raw_objects WHERE id = %s", (oid,))
            cur.fetchone()
        latencies.append((time.perf_counter() - start) * 1000)

    conn.close()
    return _compute_stats(latencies, "raw_read")


def benchmark_rls_writes(n: int) -> dict:
    """Benchmark PostgreSQL with RLS enabled."""
    conn = psycopg2.connect(DSN)
    setup_rls_tables(conn)

    latencies = []
    for i in range(n):
        oid = str(uuid.uuid4())
        content = json.dumps({"title": f"Object {i}", "status": "active"})
        start = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute("SET LOCAL app.org_id = 'org1'")
            cur.execute(
                "INSERT INTO rls_objects (id, type_name, content, owner_id, org_id) VALUES (%s, %s, %s, %s, %s)",
                (oid, "document", content, "user1", "org1"),
            )
        conn.commit()
        latencies.append((time.perf_counter() - start) * 1000)

    conn.close()
    return _compute_stats(latencies, "rls_write")


def benchmark_rls_reads(n: int) -> dict:
    """Benchmark PostgreSQL with RLS reads."""
    conn = psycopg2.connect(DSN)

    ids = []
    for i in range(n):
        oid = str(uuid.uuid4())
        ids.append(oid)
        with conn.cursor() as cur:
            cur.execute("SET LOCAL app.org_id = 'org1'")
            cur.execute(
                "INSERT INTO rls_objects (id, type_name, content, owner_id, org_id) VALUES (%s, %s, %s, %s, %s)",
                (oid, "document", json.dumps({"title": f"Object {i}"}), "user1", "org1"),
            )
        conn.commit()

    latencies = []
    for oid in ids:
        start = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute("SET LOCAL app.org_id = 'org1'")
            cur.execute("SELECT * FROM rls_objects WHERE id = %s", (oid,))
            cur.fetchone()
        conn.commit()
        latencies.append((time.perf_counter() - start) * 1000)

    conn.close()
    return _compute_stats(latencies, "rls_read")


def benchmark_pedo_writes(n: int, num_rules: int = 5, num_validators: int = 1,
                           hierarchy_depth: int = 1, cross_object_reads: int = 0) -> dict:
    """Benchmark permission-embedded object writes."""
    store = ObjectStore(DSN)
    store.clear_all()

    # Build validators
    validators = []
    for _ in range(num_validators):
        def simple_validator(proposed, existing, accessor, st):
            if not proposed.content.get("title"):
                return "Title required"
            return True
        validators.append(simple_validator)

    # Add cross-object read validators
    if cross_object_reads > 0:
        # Create target objects for validators to read
        ref_ids = []
        ref_type = ObjectType(
            name="ref_target", fields={"value": "str"},
            permission_rules=[PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {})],
            default_policy=Operation.ACCEPT,
        )
        store.register_type(ref_type)
        system = AccessContext(user_id="system", role="system")
        for i in range(cross_object_reads):
            ref = store.create(DataObject(
                type_name="ref_target",
                content={"value": f"ref_{i}"},
            ), system)
            ref_ids.append(ref.id)

        def cross_object_validator(proposed, existing, accessor, st):
            for rid in ref_ids:
                st.raw_read(rid)
            return True
        validators.append(cross_object_validator)

    # Build rules
    rules = []
    for i in range(num_rules):
        rules.append(PermissionRule(
            Operation.ACCEPT if i == num_rules - 1 else Operation.DENY,
            PrivilegeType.WRITE if i == num_rules - 1 else PrivilegeType.MANAGE,
            {"role": "writer"} if i == num_rules - 1 else {"role": f"role_{i}"},
        ))
    # Must also have INSERT and READ permissions
    rules.extend([
        PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "writer"}),
        PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "writer"}),
        PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"role": "writer"}),
    ])

    doc_type = ObjectType(
        name="bench_doc", fields={"title": "str", "status": "str"},
        permission_rules=rules,
        validators=validators,
        default_policy=Operation.DENY,
    )
    store.register_type(doc_type)

    # Build hierarchy if needed
    ctx = AccessContext(user_id="user1", role="writer", org_id="org1")

    # Create parent chain for hierarchy depth
    parent_id = None
    if hierarchy_depth > 1:
        container_type = ObjectType(
            name="container", fields={"name": "str"},
            permission_rules=[
                PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "writer"}),
                PermissionRule(Operation.ACCEPT, PrivilegeType.SELECT, {"role": "writer"}),
                PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {"role": "writer"}),
                PermissionRule(Operation.ACCEPT, PrivilegeType.UPDATE, {"role": "writer"}),
                PermissionRule(Operation.ACCEPT, PrivilegeType.DELETE, {"role": "writer"}),
            ],
            default_policy=Operation.ACCEPT,
        )
        store.register_type(container_type)
        for d in range(hierarchy_depth - 1):
            c = store.create(DataObject(
                type_name="container",
                content={"name": f"level_{d}"},
                parent_id=parent_id,
                org_id="org1",
            ), ctx)
            parent_id = c.id

    latencies = []
    for i in range(n):
        obj = DataObject(
            type_name="bench_doc",
            content={"title": f"Doc {i}", "status": "active"},
            parent_id=parent_id,
            org_id="org1",
        )
        start = time.perf_counter()
        store.create(obj, ctx)
        latencies.append((time.perf_counter() - start) * 1000)

    return _compute_stats(latencies, f"pedo_write(rules={num_rules},val={num_validators},"
                                     f"depth={hierarchy_depth},xobj={cross_object_reads})")


def benchmark_pedo_reads(n: int, num_rules: int = 5) -> dict:
    """Benchmark permission-embedded object reads."""
    store = ObjectStore(DSN)
    store.clear_all()

    rules = []
    for i in range(num_rules):
        rules.append(PermissionRule(
            Operation.ACCEPT if i == num_rules - 1 else Operation.DENY,
            PrivilegeType.READ if i == num_rules - 1 else PrivilegeType.MANAGE,
            {"role": "reader"} if i == num_rules - 1 else {"role": f"role_{i}"},
        ))
    rules.append(PermissionRule(Operation.ACCEPT, PrivilegeType.INSERT, {"role": "writer"}))

    doc_type = ObjectType(
        name="bench_doc", fields={"title": "str"},
        permission_rules=rules,
        default_policy=Operation.DENY,
    )
    store.register_type(doc_type)

    writer = AccessContext(user_id="user1", role="writer", org_id="org1")
    ids = []
    for i in range(n):
        obj = store.create(DataObject(
            type_name="bench_doc",
            content={"title": f"Doc {i}"},
            org_id="org1",
        ), writer)
        ids.append(obj.id)

    reader = AccessContext(user_id="user2", role="reader", org_id="org1")
    latencies = []
    for oid in ids:
        start = time.perf_counter()
        store.get(oid, reader)
        latencies.append((time.perf_counter() - start) * 1000)

    return _compute_stats(latencies, f"pedo_read(rules={num_rules})")


def _compute_stats(latencies: list[float], label: str) -> dict:
    arr = np.array(latencies)
    return {
        "label": label,
        "n": len(latencies),
        "p50": float(np.percentile(arr, 50)),
        "p95": float(np.percentile(arr, 95)),
        "p99": float(np.percentile(arr, 99)),
        "mean": float(np.mean(arr)),
        "throughput": len(latencies) / (sum(latencies) / 1000),  # ops/sec
    }


def run_all_benchmarks(n: int = 200):
    """Run the complete benchmark suite."""
    results = []

    print(f"\n{'='*80}")
    print(f"EVALUATION 6.3: Pipeline Overhead Benchmarks (n={n} per config)")
    print(f"{'='*80}\n")

    # ── Baseline comparisons ──
    print("Running baseline comparisons...")
    results.append(benchmark_raw_writes(n))
    results.append(benchmark_raw_reads(n))
    results.append(benchmark_rls_writes(n))
    results.append(benchmark_rls_reads(n))
    results.append(benchmark_pedo_writes(n, num_rules=5, num_validators=1))
    results.append(benchmark_pedo_reads(n, num_rules=5))

    # ── Rule count variation ──
    print("Running rule count variation...")
    for num_rules in [1, 5, 10, 20]:
        results.append(benchmark_pedo_writes(n, num_rules=num_rules, num_validators=1))

    # ── Validator count variation ──
    print("Running validator count variation...")
    for num_val in [0, 1, 3]:
        results.append(benchmark_pedo_writes(n, num_rules=5, num_validators=num_val))

    # ── Hierarchy depth variation ──
    print("Running hierarchy depth variation...")
    for depth in [1, 3, 5]:
        results.append(benchmark_pedo_writes(n, num_rules=5, num_validators=1, hierarchy_depth=depth))

    # ── Cross-object read fan-out ──
    print("Running cross-object fan-out variation...")
    for fan_out in [0, 1, 5]:
        results.append(benchmark_pedo_writes(n, num_rules=5, num_validators=1, cross_object_reads=fan_out))

    # ── Format results ──
    headers = ["Configuration", "N", "p50 (ms)", "p95 (ms)", "p99 (ms)", "Mean (ms)", "Throughput (ops/s)"]
    rows = []
    for r in results:
        rows.append([
            r["label"], r["n"],
            f"{r['p50']:.3f}", f"{r['p95']:.3f}", f"{r['p99']:.3f}",
            f"{r['mean']:.3f}", f"{r['throughput']:.0f}",
        ])

    print("\n" + tabulate(rows, headers=headers, tablefmt="grid"))

    # ── Compute overhead ratios ──
    raw_write = next(r for r in results if r["label"] == "raw_write")
    raw_read = next(r for r in results if r["label"] == "raw_read")

    print("\n\nOverhead Ratios (relative to raw PostgreSQL):")
    print("-" * 60)
    for r in results:
        if "write" in r["label"]:
            ratio = r["mean"] / raw_write["mean"]
            print(f"  {r['label']:60s} {ratio:.2f}x")
        elif "read" in r["label"]:
            ratio = r["mean"] / raw_read["mean"]
            print(f"  {r['label']:60s} {ratio:.2f}x")

    return results


if __name__ == "__main__":
    run_all_benchmarks()
