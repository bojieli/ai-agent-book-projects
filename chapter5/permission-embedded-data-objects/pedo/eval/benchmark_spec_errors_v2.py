"""Evaluation 5.4 (v2): Specification Error Evaluation — Execution-Based.

Instead of keyword matching, this evaluation:
1. Generates permission rules + validators (schema spec) via LLM
2. Generates API authorization functions (business logic) via LLM
3. Runs both against a suite of test cases that exercise each requirement
4. Measures which test cases pass/fail for each condition

This grounds the comparison in actual execution, not keyword matching.
"""

import json
import os
import re
import time
import uuid
import signal
import concurrent.futures
import psycopg2
import psycopg2.extras

from google import genai

DSN = "dbname=pedo_test"


class TimeoutError(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError("timed out")


def get_client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# ── Test Cases ────────────────────────────────────────────────
# Each test case has: id, description, setup code, test code, expected result

TEST_CASES = [
    {
        "id": "T1",
        "requirement": "H7: Status must follow state machine",
        "category": "state_machine",
        "description": "Reject applied->hired (skipping steps)",
        "test": "update_status('applied', 'hired')",
        "expected": "reject",
    },
    {
        "id": "T2",
        "requirement": "H7: Status must follow state machine",
        "category": "state_machine",
        "description": "Allow applied->screened (valid)",
        "test": "update_status('applied', 'screened')",
        "expected": "allow",
    },
    {
        "id": "T3",
        "requirement": "H7: Status must follow state machine",
        "category": "state_machine",
        "description": "Reject screened->offered (skipping interviewed)",
        "test": "update_status('screened', 'offered')",
        "expected": "reject",
    },
    {
        "id": "T4",
        "requirement": "H8: Salary in range",
        "category": "domain_validity",
        "description": "Reject salary $500K (range $80K-$150K)",
        "test": "check_salary(500000, 80000, 150000)",
        "expected": "reject",
    },
    {
        "id": "T5",
        "requirement": "H8: Salary in range",
        "category": "domain_validity",
        "description": "Allow salary $100K (within range)",
        "test": "check_salary(100000, 80000, 150000)",
        "expected": "allow",
    },
    {
        "id": "T6",
        "requirement": "H9: Only add to open positions",
        "category": "cross_object",
        "description": "Reject adding candidate to closed position",
        "test": "check_position_open('closed')",
        "expected": "reject",
    },
    {
        "id": "T7",
        "requirement": "H9: Only add to open positions",
        "category": "cross_object",
        "description": "Allow adding candidate to open position",
        "test": "check_position_open('open')",
        "expected": "allow",
    },
    {
        "id": "T8",
        "requirement": "H3: Hiring managers read-only for candidates",
        "category": "authorization",
        "description": "Reject hiring_manager writing to candidate",
        "test": "check_role_write('hiring_manager', 'candidate')",
        "expected": "reject",
    },
    {
        "id": "T9",
        "requirement": "H3: Hiring managers read-only for candidates",
        "category": "authorization",
        "description": "Allow hiring_manager reading candidate",
        "test": "check_role_read('hiring_manager', 'candidate')",
        "expected": "allow",
    },
    {
        "id": "T10",
        "requirement": "H4: Recruiters cannot see evaluations",
        "category": "authorization",
        "description": "Reject recruiter reading evaluation",
        "test": "check_role_read('recruiter', 'evaluation')",
        "expected": "reject",
    },
    {
        "id": "T11",
        "requirement": "H1: Recruiters can create candidates",
        "category": "authorization",
        "description": "Allow recruiter creating candidate",
        "test": "check_role_write('recruiter', 'candidate')",
        "expected": "allow",
    },
    {
        "id": "T12",
        "requirement": "H10: Interview requires screened/interviewed candidate",
        "category": "cross_object",
        "description": "Reject interview for 'applied' candidate",
        "test": "check_interview_eligible('applied')",
        "expected": "reject",
    },
    {
        "id": "T13",
        "requirement": "H10: Interview requires screened/interviewed candidate",
        "category": "cross_object",
        "description": "Allow interview for 'screened' candidate",
        "test": "check_interview_eligible('screened')",
        "expected": "allow",
    },
    {
        "id": "T14",
        "requirement": "P1: Tenant isolation",
        "category": "authorization",
        "description": "Reject reading data from another org",
        "test": "check_tenant_isolation('org_a', 'org_b')",
        "expected": "reject",
    },
    {
        "id": "T15",
        "requirement": "P6: Task priority validation",
        "category": "domain_validity",
        "description": "Reject invalid priority 'URGENT'",
        "test": "check_priority('URGENT')",
        "expected": "reject",
    },
    {
        "id": "T16",
        "requirement": "P6: Task priority validation",
        "category": "domain_validity",
        "description": "Allow valid priority 'high'",
        "test": "check_priority('high')",
        "expected": "allow",
    },
]


# ── LLM Generation ───────────────────────────────────────────

SPEC_GENERATION_PROMPT = """Write Python functions that implement the following constraint checks for a permission-embedded data object store. Each function should return True if the operation is allowed, or a string error message if it should be rejected.

Required functions:

def update_status(current_status, new_status):
    '''Check if a candidate status transition is valid.
    Valid transitions: applied->screened, screened->interviewed, interviewed->offered, offered->hired, any->rejected.'''

def check_salary(salary, salary_min, salary_max):
    '''Check if salary is within the position's range.'''

def check_position_open(position_status):
    '''Check if a position is open for new candidates.'''

def check_role_write(role, object_type):
    '''Check if a role can write to an object type.
    Rules: recruiter can write candidates. hiring_manager CANNOT write candidates. admin can write anything.'''

def check_role_read(role, object_type):
    '''Check if a role can read an object type.
    Rules: recruiter CANNOT read evaluations. hiring_manager can read candidates. admin can read anything.'''

def check_interview_eligible(candidate_status):
    '''Check if a candidate is eligible for an interview. Must be in screened or interviewed status.'''

def check_tenant_isolation(caller_org, object_org):
    '''Check if the caller can access the object. Must be same org.'''

def check_priority(priority):
    '''Check if priority is valid. Must be one of: low, medium, high, critical.'''

Return ONLY the Python functions. No imports, no classes, no markdown."""

LOGIC_GENERATION_PROMPT = """Write Python functions that implement the following authorization and validation checks for a traditional API. Each function should return True if the operation is allowed, or raise ValueError with a message if it should be rejected.

Required functions:

def update_status(current_status, new_status):
    '''Check if a candidate status transition is valid.
    Valid transitions: applied->screened, screened->interviewed, interviewed->offered, offered->hired, any->rejected.'''

def check_salary(salary, salary_min, salary_max):
    '''Check if salary is within the position's range.'''

def check_position_open(position_status):
    '''Check if a position is open for new candidates.'''

def check_role_write(role, object_type):
    '''Check if a role can write to an object type.
    Rules: recruiter can write candidates. hiring_manager CANNOT write candidates. admin can write anything.'''

def check_role_read(role, object_type):
    '''Check if a role can read an object type.
    Rules: recruiter CANNOT read evaluations. hiring_manager can read candidates. admin can read anything.'''

def check_interview_eligible(candidate_status):
    '''Check if a candidate is eligible for an interview. Must be in screened or interviewed status.'''

def check_tenant_isolation(caller_org, object_org):
    '''Check if the caller can access the object. Must be same org.'''

def check_priority(priority):
    '''Check if priority is valid. Must be one of: low, medium, high, critical.'''

Return ONLY the Python functions. No imports, no classes, no markdown."""


def generate_code(client, prompt, label):
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            config={"temperature": 0.2},
            contents=prompt)
        code = response.text.strip()
        code = re.sub(r'^```(?:python)?\s*\n?', '', code)
        code = re.sub(r'\n?```\s*$', '', code)
        return code
    except Exception as e:
        print(f"({e})", end=" ", flush=True)
        return None


def execute_test_case(code: str, test_case: dict) -> dict:
    """Execute a test case against generated code."""
    namespace = {}
    try:
        exec(code, namespace)
    except Exception as e:
        return {"status": "compile_error", "error": str(e)[:200]}

    test_expr = test_case["test"]
    expected = test_case["expected"]

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(5)
    try:
        result = eval(test_expr, namespace)
        signal.alarm(0)

        # Interpret result
        if expected == "allow":
            if result is True or result is None:
                return {"status": "pass", "result": "allowed correctly"}
            else:
                return {"status": "fail", "result": f"should allow but got: {result}"}
        elif expected == "reject":
            if result is True or result is None:
                return {"status": "fail", "result": "should reject but allowed"}
            elif isinstance(result, str):
                return {"status": "pass", "result": f"rejected correctly: {result[:80]}"}
            else:
                return {"status": "pass", "result": f"rejected: {result}"}

    except (ValueError, PermissionError, Exception) as e:
        signal.alarm(0)
        err = str(e)
        if expected == "reject":
            return {"status": "pass", "result": f"rejected via exception: {err[:80]}"}
        else:
            return {"status": "fail", "result": f"should allow but raised: {err[:80]}"}
    except TimeoutError:
        return {"status": "timeout", "error": "timed out"}
    finally:
        signal.signal(signal.SIGALRM, old_handler)
        signal.alarm(0)


def run_spec_error_eval_v2(n_trials: int = 5):
    """Run execution-based specification error evaluation."""
    client = get_client()

    print(f"\n{'='*80}")
    print(f"EVALUATION 5.4: Specification Error Evaluation (Execution-Based)")
    print(f"{'='*80}")
    print(f"Model: Gemini 3 Flash Preview")
    print(f"Test cases: {len(TEST_CASES)}")
    print(f"Trials per condition: {n_trials}")
    print(f"Conditions: Schema specification vs Business logic authorization\n")

    all_results = {"spec": [], "logic": []}

    for trial in range(n_trials):
        print(f"\n--- Trial {trial+1}/{n_trials} ---")

        # Generate schema spec
        print("  Generating schema spec...", end=" ", flush=True)
        spec_code = generate_code(client, SPEC_GENERATION_PROMPT, "spec")
        if spec_code is None:
            print("FAILED", flush=True)
            continue
        spec_lines = len([l for l in spec_code.split("\n") if l.strip() and not l.strip().startswith("#")])
        print(f"done ({spec_lines} lines)", flush=True)

        time.sleep(0.5)

        # Generate business logic
        print("  Generating business logic...", end=" ", flush=True)
        logic_code = generate_code(client, LOGIC_GENERATION_PROMPT, "logic")
        if logic_code is None:
            print("FAILED", flush=True)
            continue
        logic_lines = len([l for l in logic_code.split("\n") if l.strip() and not l.strip().startswith("#")])
        print(f"done ({logic_lines} lines)", flush=True)

        # Run test cases
        spec_results = []
        logic_results = []
        for tc in TEST_CASES:
            sr = execute_test_case(spec_code, tc)
            lr = execute_test_case(logic_code, tc)
            spec_results.append({"test_id": tc["id"], "requirement": tc["requirement"],
                                  "category": tc["category"], "expected": tc["expected"],
                                  "description": tc["description"], **sr})
            logic_results.append({"test_id": tc["id"], "requirement": tc["requirement"],
                                   "category": tc["category"], "expected": tc["expected"],
                                   "description": tc["description"], **lr})

        spec_pass = sum(1 for r in spec_results if r["status"] == "pass")
        logic_pass = sum(1 for r in logic_results if r["status"] == "pass")
        print(f"  Spec: {spec_pass}/{len(TEST_CASES)} pass | Logic: {logic_pass}/{len(TEST_CASES)} pass")

        all_results["spec"].append({"trial": trial, "lines": spec_lines, "code": spec_code,
                                     "test_results": spec_results})
        all_results["logic"].append({"trial": trial, "lines": logic_lines, "code": logic_code,
                                      "test_results": logic_results})

    print_spec_v2_results(all_results)
    return all_results


def print_spec_v2_results(results):
    from tabulate import tabulate

    print(f"\n\n{'='*80}")
    print("SPECIFICATION ERROR EVALUATION RESULTS (Execution-Based)")
    print(f"{'='*80}\n")

    # Per-trial summary
    headers = ["Condition", "Trial", "Lines", "Pass", "Fail", "Error", "Pass Rate"]
    rows = []
    for cond in ["spec", "logic"]:
        for entry in results[cond]:
            tests = entry["test_results"]
            passed = sum(1 for t in tests if t["status"] == "pass")
            failed = sum(1 for t in tests if t["status"] == "fail")
            errors = sum(1 for t in tests if t["status"] in ("compile_error", "timeout"))
            rate = passed / len(tests) if tests else 0
            rows.append([
                "Schema Spec" if cond == "spec" else "Business Logic",
                entry["trial"] + 1, entry["lines"],
                passed, failed, errors, f"{rate:.0%}",
            ])
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    # Aggregate
    print("\n\nAggregate Across Trials:")
    print("-" * 60)
    for cond in ["spec", "logic"]:
        label = "Schema Spec" if cond == "spec" else "Business Logic"
        all_tests = []
        for entry in results[cond]:
            all_tests.extend(entry["test_results"])
        if not all_tests:
            continue
        passed = sum(1 for t in all_tests if t["status"] == "pass")
        failed = sum(1 for t in all_tests if t["status"] == "fail")
        total = len(all_tests)
        avg_lines = sum(e["lines"] for e in results[cond]) / len(results[cond])
        print(f"  {label}:")
        print(f"    Average lines: {avg_lines:.0f}")
        print(f"    Total test executions: {total}")
        print(f"    Passed: {passed} ({passed/total:.0%})")
        print(f"    Failed: {failed} ({failed/total:.0%})")
        print(f"    Error rate: {failed/total:.0%}")

    # Per-test-case breakdown
    print("\n\nPer-Test-Case Pass Rate (across all trials):")
    print("-" * 80)
    headers2 = ["Test", "Category", "Expected", "Spec Pass Rate", "Logic Pass Rate"]
    rows2 = []
    for tc in TEST_CASES:
        spec_tests = [t for entry in results["spec"] for t in entry["test_results"] if t["test_id"] == tc["id"]]
        logic_tests = [t for entry in results["logic"] for t in entry["test_results"] if t["test_id"] == tc["id"]]
        spec_rate = sum(1 for t in spec_tests if t["status"] == "pass") / len(spec_tests) if spec_tests else 0
        logic_rate = sum(1 for t in logic_tests if t["status"] == "pass") / len(logic_tests) if logic_tests else 0
        marker = " ***" if abs(spec_rate - logic_rate) > 0.3 else ""
        rows2.append([f"{tc['id']}: {tc['description'][:40]}", tc["category"], tc["expected"],
                       f"{spec_rate:.0%}", f"{logic_rate:.0%}{marker}"])
    print(tabulate(rows2, headers=headers2, tablefmt="grid"))

    # Failure details
    print("\n\nNotable Failures:")
    print("-" * 60)
    for cond in ["spec", "logic"]:
        label = "Schema Spec" if cond == "spec" else "Business Logic"
        failures = []
        for entry in results[cond]:
            for t in entry["test_results"]:
                if t["status"] == "fail":
                    failures.append((entry["trial"], t))
        if failures:
            print(f"\n  {label}:")
            for trial, t in failures:
                print(f"    Trial {trial+1}, {t['test_id']}: {t['description'][:50]} -> {t['result'][:60]}")

    path = "/Users/boj/PermissionEmbeddedDataObjects/eval_results_spec_errors_v2.json"
    with open(path, "w") as f:
        json.dump({"timestamp": time.time(), "results": {
            c: [{k: v for k, v in e.items() if k != "code"} for e in entries]
            for c, entries in results.items()
        }}, f, indent=2, default=str)
    print(f"\nResults saved to {path}")


if __name__ == "__main__":
    run_spec_error_eval_v2(n_trials=5)
