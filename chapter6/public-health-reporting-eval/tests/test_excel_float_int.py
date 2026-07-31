"""Excel-style whole floats in integer CSV cells must load (10.0 -> 10)."""
import csv
from pathlib import Path

from reporting_tools import ReportingEnvironment


def _write_csv(path: Path, tests_value: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "row_id",
                "org_unit_id",
                "period",
                "parent_org_unit",
                "tests",
                "confirmed_cases",
                "deaths",
                "report_expected",
                "report_submitted",
                "stockout_days",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "row_id": "r1",
                "org_unit_id": "ou1",
                "period": "2024Q1",
                "parent_org_unit": "p1",
                "tests": tests_value,
                "confirmed_cases": "5",
                "deaths": "0",
                "report_expected": "1",
                "report_submitted": "1",
                "stockout_days": "0",
            }
        )


def test_excel_float_tests_field_loads_as_int(tmp_path):
    path = tmp_path / "excel.csv"
    _write_csv(path, "10.0")
    env = ReportingEnvironment(path)
    assert env.rows[0]["tests"] == 10
    assert env.rows[0]["confirmed_cases"] == 5


def test_fractional_tests_still_rejected(tmp_path):
    path = tmp_path / "frac.csv"
    _write_csv(path, "3.5")
    try:
        ReportingEnvironment(path)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "non-integer" in str(e)


def test_blank_still_zero(tmp_path):
    path = tmp_path / "blank.csv"
    _write_csv(path, "")
    env = ReportingEnvironment(path)
    assert env.rows[0]["tests"] == 0


def test_plain_int_unchanged(tmp_path):
    path = tmp_path / "ok.csv"
    _write_csv(path, "12")
    env = ReportingEnvironment(path)
    assert env.rows[0]["tests"] == 12
