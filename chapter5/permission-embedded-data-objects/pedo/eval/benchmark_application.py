"""End-to-End Application Benchmark: AI Agent Running a Hiring Pipeline.

A realistic scenario where an LLM agent performs a sequence of business
operations on a hiring pipeline: creating positions, adding candidates,
advancing them through the pipeline, scheduling interviews, writing
evaluations, and handling edge cases.

The agent receives natural language task descriptions and generates code
to execute them. We compare three conditions:
  (a) PEDO: Agent generates code against the permission-embedded store
  (b) RAW: Agent generates SQL against raw PostgreSQL
  (c) API: Agent generates code with self-implemented authorization

For each condition, we measure:
  - Task completion rate (did the operation succeed?)
  - Integrity violation count (did the DB end up in an invalid state?)
  - Workflow correctness (did the multi-step workflow produce the right outcome?)
"""

import json
import os
import re
import time
import uuid
import signal
import psycopg2
import psycopg2.extras
import concurrent.futures
from collections import defaultdict

from google import genai

from pedo.core.models import AccessContext, DataObject
from pedo.core.store import (
    ObjectStore, PermissionDeniedError, ValidationError, ReferentialIntegrityError,
)
from pedo.scenarios.hiring import register_hiring_types, VALID_TRANSITIONS

DSN = "dbname=pedo_test"


class TimeoutError(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError("timed out")


def get_client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# ── The Application Scenario ─────────────────────────────────
# A concrete multi-step hiring workflow with specific actors and data.

WORKFLOW_TASKS = [
    # Phase 1: Setup (admin creates positions)
    {"id": 1, "actor": "admin", "task": "Create an open position titled 'Senior Backend Engineer' in department 'Engineering' with salary range $120,000-$180,000.",
     "expected_outcome": "position_created", "constraint_tested": None},
    {"id": 2, "actor": "admin", "task": "Create an open position titled 'Product Designer' in department 'Design' with salary range $100,000-$150,000.",
     "expected_outcome": "position_created", "constraint_tested": None},

    # Phase 2: Recruiter adds candidates
    {"id": 3, "actor": "recruiter", "task": "Add candidate 'Alice Chen' (alice@example.com) to the Senior Backend Engineer position with salary expectation $150,000.",
     "expected_outcome": "candidate_created", "constraint_tested": None},
    {"id": 4, "actor": "recruiter", "task": "Add candidate 'Bob Kumar' (bob@example.com) to the Senior Backend Engineer position with salary expectation $140,000.",
     "expected_outcome": "candidate_created", "constraint_tested": None},
    {"id": 5, "actor": "recruiter", "task": "Add candidate 'Carol Martinez' (carol@example.com) to the Product Designer position with salary expectation $130,000.",
     "expected_outcome": "candidate_created", "constraint_tested": None},

    # Phase 3: Recruiter advances candidates through pipeline
    {"id": 6, "actor": "recruiter", "task": "Move Alice Chen's status from 'applied' to 'screened'.",
     "expected_outcome": "status_updated", "constraint_tested": None},
    {"id": 7, "actor": "recruiter", "task": "Move Bob Kumar's status from 'applied' to 'screened'.",
     "expected_outcome": "status_updated", "constraint_tested": None},
    {"id": 8, "actor": "recruiter", "task": "Move Alice Chen's status from 'screened' to 'interviewed'.",
     "expected_outcome": "status_updated", "constraint_tested": None},

    # Phase 4: Constraint tests — these should be caught
    {"id": 9, "actor": "recruiter", "task": "Try to move Bob Kumar's status directly from 'screened' to 'offered' (skipping 'interviewed').",
     "expected_outcome": "should_reject", "constraint_tested": "state_machine"},
    {"id": 10, "actor": "recruiter", "task": "Try to add a new candidate 'Dave Wilson' to the Senior Backend Engineer position with salary expectation $250,000 (above the $180,000 max).",
     "expected_outcome": "should_reject", "constraint_tested": "salary_range"},
    {"id": 11, "actor": "hiring_manager", "task": "Try to change Alice Chen's status to 'offered'. (Hiring managers should not be able to modify candidates.)",
     "expected_outcome": "should_reject", "constraint_tested": "authorization"},
    {"id": 12, "actor": "recruiter", "task": "Try to read the evaluation records. (Recruiters should not have access to evaluations.)",
     "expected_outcome": "should_reject", "constraint_tested": "authorization"},

    # Phase 5: Continue valid workflow
    {"id": 13, "actor": "recruiter", "task": "Move Alice Chen's status from 'interviewed' to 'offered'.",
     "expected_outcome": "status_updated", "constraint_tested": None},
    {"id": 14, "actor": "recruiter", "task": "Move Alice Chen's status from 'offered' to 'hired'.",
     "expected_outcome": "status_updated", "constraint_tested": None},
    {"id": 15, "actor": "recruiter", "task": "Reject Bob Kumar (set status to 'rejected').",
     "expected_outcome": "status_updated", "constraint_tested": None},

    # Phase 6: Post-hire constraint tests
    {"id": 16, "actor": "admin", "task": "Close the Senior Backend Engineer position (set status to 'closed').",
     "expected_outcome": "position_closed", "constraint_tested": None},
    {"id": 17, "actor": "recruiter", "task": "Try to add a new candidate 'Eve Park' to the now-closed Senior Backend Engineer position.",
     "expected_outcome": "should_reject", "constraint_tested": "closed_position"},

    # Phase 7: Cross-tenant test
    {"id": 18, "actor": "recruiter", "task": "Try to read all candidates from organization 'competitor_corp' (the caller is from 'acme').",
     "expected_outcome": "should_reject", "constraint_tested": "tenant_isolation"},
]


# ── PEDO Execution Engine ─────────────────────────────────────

PEDO_SYSTEM_PROMPT = """You are an AI agent operating a hiring pipeline through a permission-embedded object store.

Available methods:
- store.create(DataObject(type_name='position', content={...}, org_id='acme'), accessor) -> DataObject
- store.create(DataObject(type_name='candidate', content={...}, org_id='acme'), accessor) -> DataObject
- store.update(object_id, {'field': 'new_value'}, accessor) -> DataObject
- store.get(object_id, accessor) -> DataObject  (has .id, .content, .org_id)
- store.query(accessor, type_name, filters={'field': 'value'}) -> list[DataObject]
- store.delete(object_id, accessor) -> bool

DataObject has: id (str), type_name (str), content (dict), org_id (str)
accessor = AccessContext(user_id=..., role=..., org_id=...)

Types and fields:
- position: title, department, status (open/closed), salary_min (int), salary_max (int)
- candidate: name, email, status, position_id, salary_expectation (int)
- interview: candidate_id, interviewer, scheduled_at, notes, score
- evaluation: interview_id, decision, comments

The store enforces permissions and business rules. Do NOT add your own checks.

Write a short Python function called do_task(store, accessor, context) that performs the requested task.
'context' is a dict with keys like 'position_ids', 'candidate_ids' containing previously created object IDs.
Return a dict with keys: 'success' (bool), 'message' (str), and optionally 'created_id' (str).

ONLY return the function. No markdown."""


RAW_SYSTEM_PROMPT = """You are an AI agent operating a hiring pipeline through raw PostgreSQL.

Table 'objects': id TEXT PK, type_name TEXT, content JSONB, owner_id TEXT, org_id TEXT, created_at FLOAT, updated_at FLOAT, refs JSONB DEFAULT '{}'.

Types and fields in content JSONB:
- position: title, department, status (open/closed), salary_min (int), salary_max (int)
- candidate: name, email, status, position_id, salary_expectation (int)

Write a short Python function called do_task(conn, context) that performs the requested task.
Use json module for JSONB, uuid.uuid4() for IDs, time.time() for timestamps.
'context' is a dict with 'position_ids', 'candidate_ids', 'caller_role', 'caller_org_id'.
Do NOT add any permission checks or validation.
Return a dict with: 'success' (bool), 'message' (str), optionally 'created_id' (str).
After INSERT/UPDATE, call conn.commit().

ONLY return the function. No markdown."""


API_SYSTEM_PROMPT = """You are an AI agent operating a hiring pipeline through a traditional API pattern.

Table 'objects': id TEXT PK, type_name TEXT, content JSONB, owner_id TEXT, org_id TEXT, created_at FLOAT, updated_at FLOAT, refs JSONB DEFAULT '{}'.

Types and fields in content JSONB:
- position: title, department, status (open/closed), salary_min (int), salary_max (int)
- candidate: name, email, status, position_id, salary_expectation (int)

Write a short Python function called do_task(conn, context) that performs the requested task.
'context' has: 'position_ids', 'candidate_ids', 'caller_role', 'caller_org_id'.

You MUST implement your own authorization and validation:
- Check caller_role permissions before operations
- Validate status transitions (applied->screened->interviewed->offered->hired, any->rejected)
- Check salary ranges against position
- Check position status is 'open' for new candidates

Raise ValueError on violations. Return dict with: 'success', 'message', optionally 'created_id'.
After INSERT/UPDATE, call conn.commit().

ONLY return the function. No markdown."""


def gen_with_retry(client, prompt, sys_prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                config={"system_instruction": sys_prompt, "temperature": 0.2},
                contents=prompt)
            code = response.text.strip()
            code = re.sub(r'^```(?:python)?\s*\n?', '', code)
            code = re.sub(r'\n?```\s*$', '', code)
            return code
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
    return None


def check_all_violations(conn) -> list[dict]:
    """Check DB state for violations."""
    violations = []
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Invalid status values
        cur.execute("SELECT id, content->>'status' as s, content->>'name' as n FROM objects WHERE type_name='candidate'")
        for r in cur.fetchall():
            if r["s"] not in (None, "applied","screened","interviewed","offered","hired","rejected"):
                violations.append({"type":"invalid_status","detail":f"{r['n']}: status={r['s']}"})

        # Salary out of range
        cur.execute("""SELECT c.id, c.content->>'name' as n,
                       (c.content->>'salary_expectation')::float as sal,
                       (p.content->>'salary_min')::float as smin,
                       (p.content->>'salary_max')::float as smax
                FROM objects c JOIN objects p ON c.content->>'position_id'=p.id
                WHERE c.type_name='candidate' AND p.type_name='position'
                AND c.content->>'salary_expectation' IS NOT NULL""")
        for r in cur.fetchall():
            if r["sal"] and r["smin"] and r["smax"]:
                if r["sal"] < r["smin"] or r["sal"] > r["smax"]:
                    violations.append({"type":"salary_range","detail":f"{r['n']}: ${r['sal']:.0f} outside [${r['smin']:.0f},${r['smax']:.0f}]"})

        # Candidates on closed positions
        cur.execute("""SELECT c.id, c.content->>'name' as n, p.content->>'status' as ps, p.content->>'title' as pt
                FROM objects c JOIN objects p ON c.content->>'position_id'=p.id
                WHERE c.type_name='candidate' AND p.type_name='position'
                AND p.content->>'status'='closed' AND c.content->>'status'='applied'""")
        for r in cur.fetchall():
            violations.append({"type":"closed_position","detail":f"{r['n']} added to closed position '{r['pt']}'"})

        # Orphaned references
        cur.execute("""SELECT c.id, c.content->>'name' as n, c.content->>'position_id' as pid
                FROM objects c WHERE c.type_name='candidate' AND c.content->>'position_id' IS NOT NULL""")
        for r in cur.fetchall():
            cur.execute("SELECT 1 FROM objects WHERE id=%s", (r["pid"],))
            if cur.fetchone() is None:
                violations.append({"type":"orphaned_ref","detail":f"{r['n']} references deleted position"})

    return violations


def run_pedo_workflow(client, tasks):
    """Run the full workflow against PEDO store."""
    store = ObjectStore(DSN)
    store.clear_all()
    register_hiring_types(store)

    # Create system context and initial data
    admin = AccessContext(user_id="admin1", role="admin", org_id="acme")
    recruiter = AccessContext(user_id="recruiter1", role="recruiter", org_id="acme")
    hm = AccessContext(user_id="hm1", role="hiring_manager", org_id="acme")

    context = {"position_ids": {}, "candidate_ids": {}}
    results = []

    for task in tasks:
        actor_map = {"admin": admin, "recruiter": recruiter, "hiring_manager": hm}
        accessor = actor_map[task["actor"]]

        prompt = f"Task: {task['task']}\n\nContext: The following IDs are available:\n"
        for k, v in context["position_ids"].items():
            prompt += f"  Position '{k}': id='{v}'\n"
        for k, v in context["candidate_ids"].items():
            prompt += f"  Candidate '{k}': id='{v}'\n"

        code = gen_with_retry(client, prompt, PEDO_SYSTEM_PROMPT)
        if code is None:
            results.append({"task_id": task["id"], "gen_ok": False, "outcome": "gen_fail"})
            print(f"  Task {task['id']:2d} [{task['actor']:15s}] GEN_FAIL", flush=True)
            continue

        # Execute
        namespace = {"store": store, "accessor": accessor, "AccessContext": AccessContext,
                     "DataObject": DataObject, "json": json, "uuid": uuid, "time": time,
                     "context": {**context, "caller_role": task["actor"], "caller_org_id": "acme"}}

        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(10)
        try:
            exec(code, namespace)
            func = namespace.get("do_task")
            if func:
                result = func(store, accessor, {**context, "caller_role": task["actor"], "caller_org_id": "acme"})
                outcome = "completed"
                # Track created IDs
                if result and isinstance(result, dict):
                    cid = result.get("created_id")
                    if cid:
                        if "position" in task["task"].lower() and "candidate" not in task["task"].lower():
                            # Extract position title
                            for word in ["Senior Backend Engineer", "Product Designer"]:
                                if word in task["task"]:
                                    context["position_ids"][word] = cid
                                    break
                        elif "candidate" in task["task"].lower() or "add" in task["task"].lower():
                            for name in ["Alice Chen", "Bob Kumar", "Carol Martinez", "Dave Wilson", "Eve Park"]:
                                if name in task["task"]:
                                    context["candidate_ids"][name] = cid
                                    break
            else:
                outcome = "no_function"
        except (PermissionDeniedError, ValidationError, ReferentialIntegrityError) as e:
            outcome = f"pipeline_caught:{type(e).__name__}"
        except TimeoutError:
            outcome = "timeout"
        except Exception as e:
            outcome = f"error:{str(e)[:100]}"
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)

        # Check if outcome matches expectation
        expected = task["expected_outcome"]
        if expected == "should_reject":
            correct = "caught" in outcome or "error" in outcome
        else:
            correct = outcome == "completed" or outcome == "no_function"

        results.append({
            "task_id": task["id"], "gen_ok": True, "outcome": outcome,
            "expected": expected, "correct": correct,
            "constraint": task.get("constraint_tested"),
        })

        status = "OK" if correct else "WRONG"
        print(f"  Task {task['id']:2d} [{task['actor']:15s}] {outcome:40s} [{status}]", flush=True)
        time.sleep(0.3)

    # Final DB check
    conn = psycopg2.connect(DSN)
    violations = check_all_violations(conn)
    conn.close()

    return results, violations, context


def run_raw_workflow(client, tasks):
    """Run the full workflow against raw PostgreSQL."""
    conn = psycopg2.connect(DSN)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM objects")
    conn.commit()

    context = {"position_ids": {}, "candidate_ids": {},
               "caller_role": "admin", "caller_org_id": "acme"}
    results = []

    for task in tasks:
        context["caller_role"] = task["actor"]

        prompt = f"Task: {task['task']}\n\nContext: The following IDs are available:\n"
        for k, v in context["position_ids"].items():
            prompt += f"  Position '{k}': id='{v}'\n"
        for k, v in context["candidate_ids"].items():
            prompt += f"  Candidate '{k}': id='{v}'\n"
        prompt += f"\nCaller role: {task['actor']}, org_id: acme"

        code = gen_with_retry(client, prompt, RAW_SYSTEM_PROMPT)
        if code is None:
            results.append({"task_id": task["id"], "gen_ok": False, "outcome": "gen_fail"})
            print(f"  Task {task['id']:2d} [{task['actor']:15s}] GEN_FAIL", flush=True)
            continue

        namespace = {"conn": conn, "json": json, "uuid": uuid, "time": time,
                     "psycopg2": psycopg2, "context": context}

        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(10)
        try:
            exec(code, namespace)
            func = namespace.get("do_task")
            if func:
                result = func(conn, context)
                conn.commit()
                outcome = "completed"
                if result and isinstance(result, dict):
                    cid = result.get("created_id")
                    if cid:
                        if "position" in task["task"].lower() and "candidate" not in task["task"].lower():
                            for word in ["Senior Backend Engineer", "Product Designer"]:
                                if word in task["task"]:
                                    context["position_ids"][word] = cid
                                    break
                        elif "candidate" in task["task"].lower() or "add" in task["task"].lower():
                            for name in ["Alice Chen", "Bob Kumar", "Carol Martinez", "Dave Wilson", "Eve Park"]:
                                if name in task["task"]:
                                    context["candidate_ids"][name] = cid
                                    break
            else:
                outcome = "no_function"
        except ValueError as e:
            outcome = f"app_rejected:{str(e)[:80]}"
            conn.rollback()
        except TimeoutError:
            outcome = "timeout"
            conn.rollback()
        except Exception as e:
            outcome = f"error:{str(e)[:100]}"
            conn.rollback()
        finally:
            signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)

        expected = task["expected_outcome"]
        if expected == "should_reject":
            correct = "rejected" in outcome or "error" in outcome
        else:
            correct = outcome == "completed"

        results.append({
            "task_id": task["id"], "gen_ok": True, "outcome": outcome,
            "expected": expected, "correct": correct,
            "constraint": task.get("constraint_tested"),
        })

        status = "OK" if correct else "WRONG"
        print(f"  Task {task['id']:2d} [{task['actor']:15s}] {outcome:40s} [{status}]", flush=True)
        time.sleep(0.3)

    violations = check_all_violations(conn)
    conn.close()
    return results, violations, context


def run_application_benchmark():
    """Run the full application benchmark."""
    client = get_client()

    print(f"\n{'='*80}")
    print(f"END-TO-END APPLICATION BENCHMARK: Hiring Pipeline")
    print(f"{'='*80}")
    print(f"Model: Gemini 3 Flash Preview")
    print(f"Tasks: {len(WORKFLOW_TASKS)} ({sum(1 for t in WORKFLOW_TASKS if t['expected_outcome']!='should_reject')} valid + {sum(1 for t in WORKFLOW_TASKS if t['expected_outcome']=='should_reject')} constraint tests)")
    print()

    all_results = {}

    for condition in ["pedo", "raw"]:
        print(f"\n{'─'*60}")
        print(f"Condition: {condition.upper()}")
        print(f"{'─'*60}")

        if condition == "pedo":
            results, violations, ctx = run_pedo_workflow(client, WORKFLOW_TASKS)
        elif condition == "raw":
            results, violations, ctx = run_raw_workflow(client, WORKFLOW_TASKS)

        all_results[condition] = {
            "results": results,
            "violations": violations,
            "context": {k: dict(v) if isinstance(v, dict) else v for k, v in ctx.items()},
        }

    print_application_results(all_results)
    return all_results


def print_application_results(all_results):
    from tabulate import tabulate

    print(f"\n\n{'='*80}")
    print("APPLICATION BENCHMARK RESULTS")
    print(f"{'='*80}\n")

    # Summary per condition
    headers = ["Condition", "Tasks", "Completed", "Correctly Handled", "DB Violations", "Workflow Score"]
    rows = []
    for cond in ["pedo", "raw"]:
        data = all_results[cond]
        results = data["results"]
        violations = data["violations"]
        n = len(results)
        completed = sum(1 for r in results if r["outcome"] == "completed" or "caught" in r["outcome"])
        correct = sum(1 for r in results if r.get("correct"))
        score = correct / n if n > 0 else 0
        rows.append([cond.upper(), n, completed, f"{correct}/{n} ({correct/n:.0%})", len(violations), f"{score:.0%}"])

    print(tabulate(rows, headers=headers, tablefmt="grid"))

    # Detailed task-by-task comparison
    print("\n\nTask-by-Task Comparison:")
    print("-" * 100)
    headers2 = ["#", "Actor", "Task", "Expected", "PEDO", "RAW"]
    rows2 = []
    for task in WORKFLOW_TASKS:
        tid = task["id"]
        pedo_r = next((r for r in all_results["pedo"]["results"] if r["task_id"] == tid), None)
        raw_r = next((r for r in all_results["raw"]["results"] if r["task_id"] == tid), None)

        pedo_status = "---"
        raw_status = "---"
        if pedo_r:
            pedo_status = ("OK" if pedo_r.get("correct") else "WRONG") + f" ({pedo_r['outcome'][:25]})"
        if raw_r:
            raw_status = ("OK" if raw_r.get("correct") else "WRONG") + f" ({raw_r['outcome'][:25]})"

        rows2.append([tid, task["actor"], task["task"][:45]+"...", task["expected_outcome"], pedo_status, raw_status])

    print(tabulate(rows2, headers=headers2, tablefmt="grid"))

    # Constraint test analysis
    print("\n\nConstraint Test Results:")
    print("-" * 80)
    constraint_tasks = [t for t in WORKFLOW_TASKS if t["expected_outcome"] == "should_reject"]
    for task in constraint_tasks:
        tid = task["id"]
        constraint = task["constraint_tested"]
        pedo_r = next((r for r in all_results["pedo"]["results"] if r["task_id"] == tid), None)
        raw_r = next((r for r in all_results["raw"]["results"] if r["task_id"] == tid), None)

        pedo_caught = pedo_r and ("caught" in str(pedo_r.get("outcome", "")) or "error" in str(pedo_r.get("outcome", "")))
        raw_caught = raw_r and ("rejected" in str(raw_r.get("outcome", "")) or "error" in str(raw_r.get("outcome", "")))

        print(f"  [{constraint:20s}] Task {tid}: {task['task'][:50]}...")
        print(f"    PEDO: {'CAUGHT' if pedo_caught else 'MISSED'} | RAW: {'CAUGHT' if raw_caught else 'MISSED'}")

    # Final violations
    print("\n\nFinal Database Violations:")
    print("-" * 60)
    for cond in ["pedo", "raw"]:
        viols = all_results[cond]["violations"]
        print(f"\n  {cond.upper()}: {len(viols)} violations")
        for v in viols:
            print(f"    - {v['type']}: {v['detail']}")

    path = "/Users/boj/PermissionEmbeddedDataObjects/eval_results_application.json"
    with open(path, "w") as f:
        json.dump({"timestamp": time.time(), "results": {
            c: {"task_results": d["results"], "violations": d["violations"]}
            for c, d in all_results.items()
        }}, f, indent=2, default=str)
    print(f"\nResults saved to {path}")


if __name__ == "__main__":
    run_application_benchmark()
