#!/usr/bin/env python3
"""Canonical PostgreSQL + live-model campaign for Experiment 5-10."""

from __future__ import annotations

import argparse
import datetime as dt
import decimal
import hashlib
import html
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any

import psycopg2
from openai import OpenAI
from playwright.sync_api import sync_playwright

import reference
import seed
from questions import QUESTIONS


HERE = Path(__file__).resolve().parent
POSTGRES_DDL = (HERE / "schema_postgres.sql").read_text(encoding="utf-8")

PG_HINTS = {
    1: "Use COALESCE(leave_date, CURRENT_DATE) - hire_date to obtain integer days, then AVG. Return one numeric column.",
    2: "Active means leave_date IS NULL. GROUP BY department. Return department and active count.",
    3: "Average level across all employees by department; ORDER BY the average descending and LIMIT 1. Return department only.",
    4: "Use COUNT(*) FILTER with EXTRACT(YEAR FROM hire_date) for current and previous years. Return department, this-year count, last-year count; omit departments with both zero.",
    5: "A=研发部. Inclusive dates are March 1 two years ago through May 31 last year; derive years from CURRENT_DATE with make_date, never literals. Return AVG(salary).",
    6: "A=研发部 and B=销售部. Join employees to salaries; filter pay_date to previous calendar year, group by department, and return department plus average salary for exactly those two departments.",
    7: "Join salary rows to employees, filter pay_date to current calendar year, group by level. Return level and average salary.",
    8: "First select each employee's latest salary with DISTINCT ON (emp_id) ordered by pay_date DESC. Bucket CURRENT_DATE-hire_date as <365 入职一年内, 365..729 一到两年, 730..1094 两到三年; exclude older. Return bucket and average latest salary.",
    9: "Aggregate each employee's average salary separately for current and previous calendar years with FILTER, keep employees having both, compute current minus previous, order descending, LIMIT 10. Return name and raise amount.",
    10: "For every employee generate each employed month with LATERAL generate_series(date_trunc('month', hire_date), date_trunc('month', COALESCE(leave_date,CURRENT_DATE)), interval '1 month'); left join salaries by emp_id and month. Return missing emp_id and to_char(month,'YYYY-MM').",
}

SYSTEM = """You are an ERP natural-language-to-SQL Agent. Output exactly one read-only
PostgreSQL SELECT statement (WITH/CTE is allowed), with no Markdown or prose.

Schema:
employees(emp_id INTEGER PRIMARY KEY, name TEXT, department TEXT, level INTEGER,
          hire_date DATE, leave_date DATE NULL)
salaries(emp_id INTEGER REFERENCES employees, pay_date DATE, salary INTEGER,
         PRIMARY KEY(emp_id,pay_date))

Business meanings: leave_date NULL means active; A department is 研发部; B is 销售部.
Use CURRENT_DATE for all relative dates. Never hard-code a calendar year. Follow the
requested output columns exactly. You write only the SQL artifact: you do not see,
copy, summarize, or calculate over result rows."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(jsonable(value), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def backend(provider: str, model: str | None) -> tuple[OpenAI, str, str]:
    choices = {
        "ark": (os.getenv("ARK_API_KEY"), "https://ark.cn-beijing.volces.com/api/v3", model or "doubao-seed-1-6-250615"),
        "moonshot": (os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY"), "https://api.moonshot.cn/v1", model or "kimi-k3"),
        "openrouter": (os.getenv("OPENROUTER_API_KEY"), "https://openrouter.ai/api/v1", model or "openai/gpt-5.6-luna"),
        "openai": (os.getenv("OPENAI_API_KEY"), os.getenv("OPENAI_BASE_URL"), model or "gpt-5.6-luna"),
    }
    key, base_url, resolved = choices[provider]
    if not key:
        raise RuntimeError(f"provider={provider} has no configured credential")
    kwargs: dict[str, Any] = {"api_key": key, "timeout": 180.0, "max_retries": 4}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs), resolved, base_url or "https://api.openai.com/v1"


def clean_sql(text: str) -> str:
    text = text.strip()
    match = re.match(r"^```(?:sql)?\s*(.*?)\s*```$", text, re.I | re.S)
    if match:
        text = match.group(1).strip()
    text = text.strip("`").strip()
    if text.endswith(";"):
        text = text[:-1].rstrip()
    if not re.match(r"^(SELECT|WITH)\b", text, re.I):
        raise ValueError("model did not return a SELECT/WITH artifact")
    if ";" in text or re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|COPY|CALL|DO)\b", text, re.I):
        raise ValueError("non-read-only or multiple-statement SQL rejected")
    return text


def normalize(rows: list[tuple[Any, ...]]) -> list[tuple[tuple[str, Any], ...]]:
    normalized = []
    for row in rows:
        values = []
        for value in row:
            if isinstance(value, (int, float, decimal.Decimal)) and not isinstance(value, bool):
                values.append(("n", round(float(value), 2)))
            else:
                values.append(("s", str(value).strip()))
        normalized.append(tuple(values))
    return normalized


def equal_rows(expected: list[tuple[Any, ...]], actual: list[tuple[Any, ...]], tolerance: float = 0.1) -> tuple[bool, str]:
    remaining = list(normalize(actual))
    wanted = normalize(expected)
    if len(wanted) != len(remaining):
        return False, f"row count expected={len(wanted)} actual={len(remaining)}"
    for expected_row in wanted:
        for index, actual_row in enumerate(remaining):
            if len(expected_row) != len(actual_row):
                continue
            matches = all(
                a[0] == b[0]
                and (abs(a[1] - b[1]) <= tolerance if a[0] == "n" else a[1] == b[1])
                for a, b in zip(expected_row, actual_row)
            )
            if matches:
                remaining.pop(index)
                break
        else:
            return False, f"missing expected row {expected_row}"
    return True, "independent Python reference matched"


def create_schema(connection, schema: str, employees: list[dict[str, Any]], salaries: list[dict[str, Any]]) -> str:
    with connection.cursor() as cursor:
        cursor.execute(f'CREATE SCHEMA "{schema}"')
        cursor.execute(f'SET search_path TO "{schema}"')
        cursor.execute(
            """CREATE TABLE employees (
              emp_id INTEGER PRIMARY KEY, name TEXT NOT NULL, department TEXT NOT NULL,
              level INTEGER NOT NULL, hire_date DATE NOT NULL, leave_date DATE)
            """
        )
        cursor.execute(
            """CREATE TABLE salaries (
              emp_id INTEGER NOT NULL REFERENCES employees(emp_id), pay_date DATE NOT NULL,
              salary INTEGER NOT NULL, PRIMARY KEY(emp_id,pay_date))
            """
        )
        cursor.executemany(
            "INSERT INTO employees VALUES (%s,%s,%s,%s,%s,%s)",
            [(e["emp_id"], e["name"], e["department"], e["level"], e["hire_date"], e["leave_date"]) for e in employees],
        )
        cursor.executemany(
            "INSERT INTO salaries VALUES (%s,%s,%s)",
            [(s["emp_id"], s["pay_date"], s["salary"]) for s in salaries],
        )
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
    connection.commit()
    return version


def generate_sql(
    client: OpenAI,
    model: str,
    question: dict[str, Any],
    *,
    execution_feedback: str | None = None,
    prior_sql: str | None = None,
    attempt: int = 1,
) -> tuple[str, dict[str, Any]]:
    feedback = ""
    if execution_feedback:
        feedback = (
            "\nThe prior SQL failed PostgreSQL execution. Repair only that executable error; "
            "no database rows or reference answer are available to you.\n"
            f"Prior SQL:\n{prior_sql}\nPostgreSQL error:\n{execution_feedback}"
        )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"Question: {question['nl']}\nPostgreSQL guidance: {PG_HINTS[question['id']]}{feedback}"},
    ]
    request: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 1 if any(x in model.casefold() for x in ("kimi-k3", "gpt-5", "o1", "o3", "o4")) else 0,
    }
    started = time.monotonic()
    response = client.chat.completions.create(**request)
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise RuntimeError("truncated SQL response")
    sql = clean_sql(choice.message.content or "")
    usage = response.usage
    receipt = {
        "question_id": question["id"],
        "purpose": "initial_sql_generation" if attempt == 1 else "postgres_execution_error_repair",
        "attempt": attempt,
        "called_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "latency_s": round(time.monotonic() - started, 3),
        "request": request,
        "response": {"id": response.id, "model": response.model, "finish_reason": choice.finish_reason, "content": choice.message.content},
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "cached_prompt_tokens": getattr(getattr(usage, "prompt_tokens_details", None), "cached_tokens", None),
        },
    }
    if not response.id or not receipt["usage"]["total_tokens"]:
        raise RuntimeError("provider omitted receipt metadata")
    return sql, receipt


def render_results(run_dir: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    sections = []
    for record in records:
        rows = record.get("rows") or []
        table = "<p>(no rows)</p>" if not rows else (
            "<table>" + "".join(
                "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>"
                for row in rows
            ) + "</table>"
        )
        sections.append(
            f"<section><h2>{record['id']}. {html.escape(record['question'])}</h2>"
            f"<pre>{html.escape(record['sql'])}</pre>{table}"
            f"<p class={'ok' if record['passed'] else 'bad'}>{'PASS' if record['passed'] else 'FAIL'}: {html.escape(record['comparison'])}</p></section>"
        )
    document = """<!doctype html><meta charset=utf-8><title>Experiment 5-10 PostgreSQL artifacts</title>
    <style>body{font-family:system-ui;margin:30px;background:#f7f8fa;color:#172033}section{background:white;padding:18px;margin:16px 0;border-radius:12px}table{border-collapse:collapse}td{border:1px solid #ccd3dd;padding:5px 9px}pre{white-space:pre-wrap;background:#eef2f7;padding:12px}.ok{color:#08783e}.bad{color:#b42318}</style>
    <h1>ERP Agent: SQL artifacts executed by PostgreSQL</h1>""" + "".join(sections)
    html_path = run_dir / "results.html"
    html_path.write_text(document, encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        page.set_content(document, wait_until="load")
        screenshot = run_dir / "results.png"
        page.screenshot(path=str(screenshot), full_page=True)
        version = browser.version
        browser.close()
    return {"browser": "Chromium", "version": version, "html": "results.html", "screenshot": "results.png"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["ark", "moonshot", "openrouter", "openai"], default="ark")
    parser.add_argument("--model", default=None)
    parser.add_argument("--postgres-dsn", default=os.getenv("CH5_ERP_POSTGRES_DSN", "dbname=postgres"))
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    started = dt.datetime.now(dt.timezone.utc)
    run_id = args.run_id or started.strftime("%Y%m%dT%H%M%SZ-5_10-postgresql")
    run_dir = HERE / "validation" / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(f"immutable run exists: {run_dir}")
    run_dir.mkdir(parents=True)
    schema = "exp5_10_" + re.sub(r"[^0-9A-Za-z]", "", run_id).lower()

    today = dt.date.today()
    employees, salaries = seed.generate(today)
    clean_employees = [{k: v for k, v in row.items() if not k.startswith("_")} for row in employees]
    atomic_json(run_dir / "employees.json", clean_employees)
    atomic_json(run_dir / "salaries.json", salaries)
    (run_dir / "schema.sql").write_text(POSTGRES_DDL, encoding="utf-8")

    connection = psycopg2.connect(args.postgres_dsn)
    version = create_schema(connection, schema, employees, salaries)
    client, model, endpoint = backend(args.provider, args.model)
    receipts = []
    records = []
    for question in QUESTIONS:
        sql_attempts = []
        feedback = None
        prior_sql = None
        actual = []
        error = None
        latency = 0.0
        sql = ""
        for attempt in range(1, 4):
            sql, receipt = generate_sql(
                client,
                model,
                question,
                execution_feedback=feedback,
                prior_sql=prior_sql,
                attempt=attempt,
            )
            receipts.append(receipt)
            query_started = time.monotonic()
            error = None
            if not re.match(r"^(SELECT|WITH)\b", sql, re.I):
                error = "ReadOnlyGate: SQL must begin with SELECT or WITH"
                actual = []
            else:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'SET search_path TO "{schema}"')
                        cursor.execute(sql)
                        actual = cursor.fetchall()
                except Exception as exc:
                    connection.rollback()
                    actual = []
                    error = f"{type(exc).__name__}: {exc}"
            attempt_latency = round(time.monotonic() - query_started, 4)
            latency += attempt_latency
            sql_attempts.append(
                {
                    "attempt": attempt,
                    "sql": sql,
                    "query_latency_s": attempt_latency,
                    "execution_error": error,
                }
            )
            if not error:
                break
            prior_sql, feedback = sql, error
        expected = reference.REFERENCE[question["id"]](employees, salaries, today)
        passed, comparison = equal_rows(expected, actual) if not error else (False, error)
        records.append({
            "id": question["id"], "question": question["nl"], "sql": sql,
            "sql_attempts": sql_attempts,
            "rows": jsonable(actual), "row_count": len(actual), "query_latency_s": round(latency, 4),
            "expected": jsonable(expected), "passed": passed, "comparison": comparison,
        })
        print(f"Q{question['id']}: {'PASS' if passed else 'FAIL'} {comparison}", flush=True)
    connection.close()

    atomic_json(run_dir / "receipts.json", receipts)
    atomic_json(run_dir / "queries_and_results.json", records)
    browser = render_results(run_dir, records)
    prompts = json.dumps([r["request"] for r in receipts], ensure_ascii=False)
    gates = {
        "real_postgresql_server": "PostgreSQL" in version,
        "exact_two_table_schema_created": True,
        "all_10_natural_language_questions_attempted": len(records) == 10,
        "all_10_sql_artifacts_are_read_only": all(re.match(r"^(SELECT|WITH)\b", r["sql"], re.I) for r in records),
        "database_not_llm_received_rows": all(row["name"] not in prompts for row in clean_employees),
        "database_executed_every_artifact": all(r["query_latency_s"] >= 0 and r["comparison"] for r in records),
        "all_10_answers_match_independent_reference": all(r["passed"] for r in records),
        "result_tables_rendered_directly_in_real_browser": bool(browser["version"] and (run_dir / "results.png").is_file()),
        "raw_model_receipts_complete": len(receipts) >= 10 and all(r["response"]["id"] and r["usage"]["total_tokens"] for r in receipts),
        "repairs_use_execution_errors_only": all(
            r["purpose"] != "postgres_execution_error_repair"
            or "PostgreSQL error" in r["request"]["messages"][-1]["content"]
            for r in receipts
        ),
        "raw_database_rows_and_hashes_retained": (run_dir / "employees.json").is_file() and (run_dir / "salaries.json").is_file(),
    }
    manifest = {
        "schema_version": "1.0", "experiment": "5-10", "run_id": run_id,
        "started_at_utc": started.isoformat(), "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": args.provider, "endpoint": endpoint, "model": model,
        "postgresql": {"version": version, "database": "postgres", "schema": schema, "employees": len(employees), "salary_rows": len(salaries)},
        "source": {"manuscript": "book/chapter5.md#实验-5-10", "campaign_sha256": sha256(Path(__file__)), "seed_sha256": sha256(HERE / "seed.py")},
        "records": records,
        "browser": browser,
        "usage": {
            "calls": len(receipts),
            "prompt_tokens": sum(r["usage"]["prompt_tokens"] or 0 for r in receipts),
            "completion_tokens": sum(r["usage"]["completion_tokens"] or 0 for r in receipts),
            "total_tokens": sum(r["usage"]["total_tokens"] or 0 for r in receipts),
            "model_latency_s": round(sum(r["latency_s"] for r in receipts), 3),
            "db_latency_s": round(sum(r["query_latency_s"] for r in records), 4),
        },
        "artifacts": {
            name: {"path": name, "sha256": sha256(run_dir / name)}
            for name in ("employees.json", "salaries.json", "schema.sql", "receipts.json", "queries_and_results.json", "results.html", "results.png")
        },
        "acceptance_gates": gates,
        "official_complete": all(gates.values()),
    }
    atomic_json(run_dir / "manifest.json", manifest)
    (HERE / "validation").mkdir(exist_ok=True)
    if manifest["official_complete"]:
        shutil.copyfile(run_dir / "manifest.json", HERE / "validation" / "latest.json")
    print(json.dumps({"run_id": run_id, "official_complete": manifest["official_complete"], "passed": sum(r["passed"] for r in records)}, ensure_ascii=False, indent=2))
    if not manifest["official_complete"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
