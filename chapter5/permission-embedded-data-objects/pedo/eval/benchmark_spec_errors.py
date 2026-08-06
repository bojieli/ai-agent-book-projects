"""Evaluation 5.4: Specification Error Evaluation.

Empirically measures specification error rates vs business logic error rates.
Given the same business requirements, uses Gemini 3 Flash to generate:
  (a) Schema specifications (permission rules + validators)
  (b) Business logic authorization code (API functions with inline checks)

Then evaluates correctness against the requirement set.
"""

import json
import os
import re
import time
import concurrent.futures
import signal
from collections import defaultdict

from google import genai

DSN = "dbname=pedo_test"

def get_client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# ── Requirements ──────────────────────────────────────────────

HIRING_REQUIREMENTS = [
    {"id": "H1", "desc": "Recruiters can create candidates", "category": "authorization"},
    {"id": "H2", "desc": "Recruiters can modify candidate status", "category": "authorization"},
    {"id": "H3", "desc": "Hiring managers can read candidates but NOT modify them", "category": "authorization"},
    {"id": "H4", "desc": "Recruiters CANNOT see evaluations", "category": "authorization"},
    {"id": "H5", "desc": "Only admins can delete positions", "category": "authorization"},
    {"id": "H6", "desc": "Candidates can only view their own records", "category": "authorization"},
    {"id": "H7", "desc": "Candidate status must follow: applied->screened->interviewed->offered->hired/rejected", "category": "state_machine"},
    {"id": "H8", "desc": "Salary expectation must be within the position's salary_min and salary_max range", "category": "domain_validity"},
    {"id": "H9", "desc": "Candidates can only be added to positions with status='open'", "category": "cross_object"},
    {"id": "H10", "desc": "Interviews can only be created for candidates in 'screened' or 'interviewed' status", "category": "cross_object"},
    {"id": "H11", "desc": "Evaluations must reference an existing interview", "category": "referential"},
    {"id": "H12", "desc": "Audit log entries are immutable (cannot be updated or deleted)", "category": "domain_validity"},
]

PM_REQUIREMENTS = [
    {"id": "P1", "desc": "Organizations cannot see each other's data (tenant isolation)", "category": "authorization"},
    {"id": "P2", "desc": "Only org_admins can delete projects", "category": "authorization"},
    {"id": "P3", "desc": "Guests can read tasks but NOT modify them", "category": "authorization"},
    {"id": "P4", "desc": "Only comment authors can edit their own comments", "category": "authorization"},
    {"id": "P5", "desc": "Task status must follow: todo->in_progress->review->done (with cancel/reopen paths)", "category": "state_machine"},
    {"id": "P6", "desc": "Task priority must be one of: low, medium, high, critical", "category": "domain_validity"},
    {"id": "P7", "desc": "Task assignee must be a member of the project", "category": "cross_object"},
    {"id": "P8", "desc": "Attachment size must not exceed 100MB", "category": "domain_validity"},
    {"id": "P9", "desc": "Deleting a project must cascade to its tasks", "category": "referential"},
    {"id": "P10", "desc": "Projects must belong to the creator's organization", "category": "cross_object"},
]


# ── Generation Prompts ────────────────────────────────────────

SCHEMA_SPEC_PROMPT = """You are writing a schema specification for a permission-embedded data object store.

Given these business requirements, write the permission rules and validator functions.

Permission rules format (Python):
```
PermissionRule(Operation.ACCEPT, PrivilegeType.READ, {{"role": "recruiter"}})
PermissionRule(Operation.DENY, PrivilegeType.WRITE, {{"role": "guest"}})
```

Validator function format (Python):
```
def validate_something(proposed, existing, accessor, store):
    # proposed: the new object state
    # existing: the current object state (None for creates)
    # accessor: AccessContext with user_id, role, org_id, is_owner
    # store: object store for cross-object reads (store.raw_read(id))
    if some_condition_violated:
        return "Error message describing the violation"
    return True
```

Requirements:
{requirements}

Write ONLY the permission rules and validators. For each requirement, write the corresponding rule or validator and label it with the requirement ID (e.g., # H1: Recruiters can create candidates).

Return ONLY Python code, no markdown formatting."""

BUSINESS_LOGIC_PROMPT = """You are writing API authorization functions for a traditional web application.

Given these business requirements, write Python functions that implement each requirement as an inline check within an API handler. Each function should:
1. Check permissions (who can do what)
2. Validate business rules
3. Raise an exception if the check fails

You have access to:
- conn: a psycopg2 database connection
- caller_role: the role of the API caller (e.g., "recruiter", "hiring_manager")
- caller_org_id: the caller's organization ID
- caller_user_id: the caller's user ID

The database table is 'objects' with columns: id (TEXT), type_name (TEXT), content (JSONB), owner_id (TEXT), org_id (TEXT).

Requirements:
{requirements}

For each requirement, write a check function and label it with the requirement ID (e.g., # H1: Recruiters can create candidates).

Return ONLY Python code, no markdown formatting."""


# ── Generation and Evaluation ─────────────────────────────────

def generate_with_timeout(client, prompt, system_instruction, timeout=30):
    """Generate code with a timeout."""
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                client.models.generate_content,
                model="gemini-3-flash-preview",
                config={"system_instruction": system_instruction, "temperature": 0.2},
                contents=prompt,
            )
            response = future.result(timeout=timeout)
        code = response.text.strip()
        code = re.sub(r'^```(?:python)?\s*\n?', '', code)
        code = re.sub(r'\n?```\s*$', '', code)
        return code
    except Exception as e:
        return f"# Generation failed: {e}"


def evaluate_spec_coverage(code: str, requirements: list[dict]) -> dict:
    """Evaluate how many requirements are addressed in generated spec code."""
    results = []
    for req in requirements:
        req_id = req["id"]
        # Check if the requirement ID is referenced in the code
        mentioned = req_id in code

        # Deeper check: look for relevant keywords
        keywords = extract_keywords(req)
        keyword_found = any(kw.lower() in code.lower() for kw in keywords)

        # Check for relevant validator/rule patterns
        has_rule_or_validator = False
        if req["category"] == "authorization":
            # Look for PermissionRule or role check
            has_rule_or_validator = ("PermissionRule" in code and any(
                kw.lower() in code.lower() for kw in keywords
            )) or (req_id in code)
        elif req["category"] == "state_machine":
            has_rule_or_validator = ("transition" in code.lower() or "status" in code.lower()) and req_id in code
        elif req["category"] == "domain_validity":
            has_rule_or_validator = ("validate" in code.lower() or "check" in code.lower()) and keyword_found
        elif req["category"] == "cross_object":
            has_rule_or_validator = ("raw_read" in code or "store." in code or "SELECT" in code.upper()) and keyword_found
        elif req["category"] == "referential":
            has_rule_or_validator = keyword_found

        status = "covered" if (mentioned and has_rule_or_validator) else (
            "partial" if (mentioned or keyword_found) else "missing"
        )

        results.append({
            "req_id": req_id,
            "desc": req["desc"],
            "category": req["category"],
            "mentioned": mentioned,
            "keyword_found": keyword_found,
            "has_implementation": has_rule_or_validator,
            "status": status,
        })

    return {
        "total": len(requirements),
        "covered": sum(1 for r in results if r["status"] == "covered"),
        "partial": sum(1 for r in results if r["status"] == "partial"),
        "missing": sum(1 for r in results if r["status"] == "missing"),
        "details": results,
    }


def evaluate_logic_coverage(code: str, requirements: list[dict]) -> dict:
    """Evaluate how many requirements are addressed in generated business logic."""
    results = []
    for req in requirements:
        req_id = req["id"]
        mentioned = req_id in code

        keywords = extract_keywords(req)
        keyword_found = any(kw.lower() in code.lower() for kw in keywords)

        # Check for implementation patterns in business logic
        has_check = False
        if req["category"] == "authorization":
            has_check = ("caller_role" in code or "role" in code.lower()) and keyword_found
        elif req["category"] == "state_machine":
            has_check = ("transition" in code.lower() or "valid" in code.lower()) and (
                "status" in code.lower()
            )
        elif req["category"] == "domain_validity":
            has_check = keyword_found and ("raise" in code.lower() or "error" in code.lower() or "return" in code.lower())
        elif req["category"] == "cross_object":
            has_check = ("SELECT" in code.upper() or "fetchone" in code.lower()) and keyword_found
        elif req["category"] == "referential":
            has_check = keyword_found

        status = "covered" if (mentioned and has_check) else (
            "partial" if (mentioned or keyword_found) else "missing"
        )

        results.append({
            "req_id": req_id,
            "desc": req["desc"],
            "category": req["category"],
            "mentioned": mentioned,
            "keyword_found": keyword_found,
            "has_implementation": has_check,
            "status": status,
        })

    return {
        "total": len(requirements),
        "covered": sum(1 for r in results if r["status"] == "covered"),
        "partial": sum(1 for r in results if r["status"] == "partial"),
        "missing": sum(1 for r in results if r["status"] == "missing"),
        "details": results,
    }


def extract_keywords(req: dict) -> list[str]:
    """Extract relevant keywords from a requirement for matching."""
    desc = req["desc"].lower()
    keywords = []
    # Role names
    for role in ["recruiter", "hiring_manager", "admin", "guest", "org_admin",
                  "project_admin", "member", "candidate", "system"]:
        if role in desc:
            keywords.append(role)
    # Object types
    for obj in ["candidate", "evaluation", "interview", "position", "task",
                 "comment", "attachment", "project", "organization", "audit"]:
        if obj in desc:
            keywords.append(obj)
    # Constraint concepts
    for concept in ["salary", "status", "priority", "assignee", "member",
                     "tenant", "isolation", "cascade", "immutable", "delete",
                     "open", "size", "100mb", "owner"]:
        if concept in desc:
            keywords.append(concept)
    return keywords if keywords else [desc.split()[0]]


def count_lines(code: str) -> int:
    """Count non-empty, non-comment lines."""
    lines = code.strip().split("\n")
    return sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))


def run_spec_error_evaluation(n_trials: int = 3):
    """Run the specification error evaluation."""
    client = get_client()

    print(f"\n{'='*80}")
    print(f"EVALUATION 5.4: Specification Error Evaluation (n_trials={n_trials})")
    print(f"{'='*80}")
    print(f"Model: Gemini 3 Flash Preview")
    print(f"Scenarios: Hiring ({len(HIRING_REQUIREMENTS)} reqs) + PM ({len(PM_REQUIREMENTS)} reqs)")
    print(f"Conditions: Schema specification vs Business logic authorization\n")

    all_results = {"spec": [], "logic": []}

    for trial in range(n_trials):
        print(f"\n--- Trial {trial+1}/{n_trials} ---")

        for scenario_name, requirements in [("Hiring", HIRING_REQUIREMENTS), ("PM", PM_REQUIREMENTS)]:
            req_text = "\n".join(f"- [{r['id']}] {r['desc']}" for r in requirements)

            # Generate schema specification
            print(f"  {scenario_name} - generating schema spec...", end=" ", flush=True)
            spec_code = generate_with_timeout(
                client,
                SCHEMA_SPEC_PROMPT.format(requirements=req_text),
                "You are a schema specification author for a permission-embedded data object store.",
            )
            if spec_code.startswith("# Generation failed"):
                print("FAILED", flush=True)
                continue
            spec_lines = count_lines(spec_code)
            spec_eval = evaluate_spec_coverage(spec_code, requirements)
            print(f"done ({spec_lines} lines, {spec_eval['covered']}/{spec_eval['total']} covered)", flush=True)

            all_results["spec"].append({
                "trial": trial,
                "scenario": scenario_name,
                "lines": spec_lines,
                "code": spec_code,
                **spec_eval,
            })

            time.sleep(0.5)

            # Generate business logic
            print(f"  {scenario_name} - generating business logic...", end=" ", flush=True)
            logic_code = generate_with_timeout(
                client,
                BUSINESS_LOGIC_PROMPT.format(requirements=req_text),
                "You are a backend engineer writing API authorization checks.",
            )
            if logic_code.startswith("# Generation failed"):
                print("FAILED", flush=True)
                continue
            logic_lines = count_lines(logic_code)
            logic_eval = evaluate_logic_coverage(logic_code, requirements)
            print(f"done ({logic_lines} lines, {logic_eval['covered']}/{logic_eval['total']} covered)", flush=True)

            all_results["logic"].append({
                "trial": trial,
                "scenario": scenario_name,
                "lines": logic_lines,
                "code": logic_code,
                **logic_eval,
            })

            time.sleep(0.5)

    # ── Print Results ──
    print_spec_results(all_results)
    save_spec_results(all_results)

    return all_results


def print_spec_results(results):
    """Print formatted results."""
    from tabulate import tabulate

    print(f"\n\n{'='*80}")
    print("SPECIFICATION ERROR EVALUATION RESULTS")
    print(f"{'='*80}\n")

    # Summary table
    headers = ["Condition", "Scenario", "Lines", "Covered", "Partial", "Missing",
               "Coverage Rate", "Error Rate"]
    rows = []

    for condition in ["spec", "logic"]:
        for r in results[condition]:
            total = r["total"]
            covered = r["covered"]
            missing = r["missing"]
            partial = r["partial"]
            cov_rate = covered / total if total > 0 else 0
            err_rate = (missing + partial) / total if total > 0 else 0
            rows.append([
                "Schema Spec" if condition == "spec" else "Business Logic",
                r["scenario"],
                r["lines"],
                f"{covered}/{total}",
                f"{partial}/{total}",
                f"{missing}/{total}",
                f"{cov_rate:.0%}",
                f"{err_rate:.0%}",
            ])

    print(tabulate(rows, headers=headers, tablefmt="grid"))

    # Aggregate by condition
    print("\n\nAggregate Statistics:")
    print("-" * 60)
    for condition in ["spec", "logic"]:
        entries = results[condition]
        if not entries:
            continue
        total_reqs = sum(e["total"] for e in entries)
        total_covered = sum(e["covered"] for e in entries)
        total_missing = sum(e["missing"] for e in entries)
        total_partial = sum(e["partial"] for e in entries)
        avg_lines = sum(e["lines"] for e in entries) / len(entries)
        cov_rate = total_covered / total_reqs if total_reqs > 0 else 0
        err_rate = (total_missing + total_partial) / total_reqs if total_reqs > 0 else 0

        label = "Schema Specification" if condition == "spec" else "Business Logic Auth"
        print(f"\n  {label}:")
        print(f"    Average lines per scenario: {avg_lines:.0f}")
        print(f"    Total requirements: {total_reqs}")
        print(f"    Covered: {total_covered} ({total_covered/total_reqs:.0%})")
        print(f"    Partial: {total_partial} ({total_partial/total_reqs:.0%})")
        print(f"    Missing: {total_missing} ({total_missing/total_reqs:.0%})")
        print(f"    Coverage rate: {cov_rate:.0%}")
        print(f"    Error rate (missing + partial): {err_rate:.0%}")

    # Error density
    print("\n\nError Density (errors per 100 lines):")
    print("-" * 60)
    for condition in ["spec", "logic"]:
        entries = results[condition]
        if not entries:
            continue
        total_errors = sum(e["missing"] + e["partial"] for e in entries)
        total_lines = sum(e["lines"] for e in entries)
        density = (total_errors / total_lines * 100) if total_lines > 0 else 0
        label = "Schema Specification" if condition == "spec" else "Business Logic Auth"
        print(f"  {label}: {density:.1f} errors per 100 lines ({total_errors} errors in {total_lines} lines)")

    # By category breakdown
    print("\n\nCoverage by Requirement Category:")
    print("-" * 60)
    categories = ["authorization", "state_machine", "domain_validity", "cross_object", "referential"]
    for condition in ["spec", "logic"]:
        label = "Schema Spec" if condition == "spec" else "Business Logic"
        print(f"\n  {label}:")
        for cat in categories:
            cat_reqs = []
            for entry in results[condition]:
                cat_reqs.extend([d for d in entry["details"] if d["category"] == cat])
            if cat_reqs:
                covered = sum(1 for r in cat_reqs if r["status"] == "covered")
                total = len(cat_reqs)
                print(f"    {cat:20s}: {covered}/{total} ({covered/total:.0%})")


def save_spec_results(results):
    """Save results to JSON."""
    output = {
        "timestamp": time.time(),
        "model": "gemini-3-flash-preview",
        "results": {
            condition: [
                {k: v for k, v in entry.items() if k != "code"}
                for entry in entries
            ]
            for condition, entries in results.items()
        },
    }
    path = "/Users/boj/PermissionEmbeddedDataObjects/eval_results_spec_errors.json"
    with open(path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to {path}")


if __name__ == "__main__":
    run_spec_error_evaluation(n_trials=3)
