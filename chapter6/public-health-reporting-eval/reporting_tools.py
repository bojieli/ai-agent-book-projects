"""Deterministic tools over synthetic DHIS2-style aggregate reports."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


INTEGER_FIELDS = {
    "tests",
    "confirmed_cases",
    "deaths",
    "report_expected",
    "report_submitted",
    "stockout_days",
}


class ReportingEnvironment:
    """Small, auditable tool environment backed by a CSV file."""

    def __init__(self, data_path: str | Path) -> None:
        with Path(data_path).open(newline="", encoding="utf-8") as handle:
            self.rows = []
            for raw_row in csv.DictReader(handle):
                row: dict[str, Any] = dict(raw_row)
                for field in INTEGER_FIELDS:
                    raw = row[field]
                    text = str(raw).strip()
                    if not text:
                        row[field] = 0
                        continue
                    # Excel/CSV often writes whole counts as 10.0
                    num = float(text)
                    if not float(num).is_integer():
                        raise ValueError(
                            f"non-integer value for {field}: {raw!r}"
                        )
                    row[field] = int(num)
                self.rows.append(row)

    def _select(self, **filters: str) -> list[dict[str, Any]]:
        rows = [
            row
            for row in self.rows
            if all(row.get(field) == value for field, value in filters.items())
        ]
        if not rows:
            raise ValueError(f"No synthetic rows match {filters}")
        return rows

    def calculate_test_positivity(self, org_unit_id: str, period: str) -> dict[str, Any]:
        rows = self._select(org_unit_id=org_unit_id, period=period)
        tests = sum(row["tests"] for row in rows)
        confirmed = sum(row["confirmed_cases"] for row in rows)
        positivity = round(100 * confirmed / tests, 2) if tests else None
        return {
            "tests": tests,
            "confirmed_cases": confirmed,
            "test_positivity_pct": positivity,
            "evidence": [row["row_id"] for row in rows],
        }

    def calculate_reporting_completeness(
        self, parent_org_unit: str, period: str
    ) -> dict[str, Any]:
        rows = self._select(parent_org_unit=parent_org_unit, period=period)
        expected = sum(row["report_expected"] for row in rows)
        submitted = sum(row["report_submitted"] for row in rows)
        completeness = round(100 * submitted / expected, 2) if expected else None
        return {
            "expected_reports": expected,
            "submitted_reports": submitted,
            "reporting_completeness_pct": completeness,
            "evidence": [row["row_id"] for row in rows],
        }

    def compare_confirmed_cases(
        self, org_unit_id: str, start_period: str, end_period: str
    ) -> dict[str, Any]:
        start_rows = self._select(org_unit_id=org_unit_id, period=start_period)
        end_rows = self._select(org_unit_id=org_unit_id, period=end_period)
        start_cases = sum(row["confirmed_cases"] for row in start_rows)
        end_cases = sum(row["confirmed_cases"] for row in end_rows)
        change = end_cases - start_cases
        percent_change = round(100 * change / start_cases, 2) if start_cases else None
        direction = "increase" if change > 0 else "decrease" if change < 0 else "no change"
        return {
            "start_cases": start_cases,
            "end_cases": end_cases,
            "absolute_change": change,
            "percent_change": percent_change,
            "direction": direction,
            "evidence": [row["row_id"] for row in start_rows + end_rows],
        }

    def find_data_quality_issues(
        self, parent_org_unit: str, period: str
    ) -> dict[str, Any]:
        rows = self._select(parent_org_unit=parent_org_unit, period=period)
        issues: list[dict[str, str]] = []
        for row in rows:
            if row["confirmed_cases"] > row["tests"]:
                issues.append({"row_id": row["row_id"], "code": "confirmed_exceeds_tests"})
            if row["stockout_days"] < 0:
                issues.append({"row_id": row["row_id"], "code": "negative_stockout_days"})
            if not row["report_submitted"] and any(
                row[field] for field in ("tests", "confirmed_cases", "deaths")
            ):
                issues.append({"row_id": row["row_id"], "code": "data_in_unsubmitted_report"})
        return {
            "issue_count": len(issues),
            "issues": issues,
            "evidence": sorted({issue["row_id"] for issue in issues}),
        }

    def review_stockouts(self, parent_org_unit: str, period: str) -> dict[str, Any]:
        rows = self._select(parent_org_unit=parent_org_unit, period=period)
        affected = [row for row in rows if row["stockout_days"] > 0]
        return {
            "facilities_with_stockouts": len(affected),
            "total_stockout_days": sum(row["stockout_days"] for row in affected),
            "facilities": [
                {
                    "org_unit_id": row["org_unit_id"],
                    "stockout_days": row["stockout_days"],
                }
                for row in affected
            ],
            "evidence": [row["row_id"] for row in affected],
        }

    def call(self, tool: str, arguments: dict[str, str]) -> dict[str, Any]:
        allowed_tools = {
            "calculate_test_positivity": self.calculate_test_positivity,
            "calculate_reporting_completeness": self.calculate_reporting_completeness,
            "compare_confirmed_cases": self.compare_confirmed_cases,
            "find_data_quality_issues": self.find_data_quality_issues,
            "review_stockouts": self.review_stockouts,
        }
        try:
            function = allowed_tools[tool]
        except KeyError as exc:
            raise ValueError(f"Unknown reporting tool: {tool}") from exc
        return function(**arguments)
