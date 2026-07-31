import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("user_request", "expected_destination"),
    [
        ("我想订一张去上海的机票", "上海"),
        ("我想订一张去上海的往返机票", "上海"),
        ("我想订一张去上海往返的机票", "上海"),
        ("我想订一张去上海往返机票", "上海"),
        ("我想订一张去广州的单程机票", "广州"),
        ("我想订一张去广州单程的票", "广州"),
        ("我想订一张去广州单程机票", "广州"),
        ("我想订一张去深圳的航班", "深圳"),
        ("我想订一张去深圳往返的航班", "深圳"),
        ("我想订一张去杭州单程的票", "杭州"),
    ],
    ids=[
        "simple-jipiao",
        "round-trip-with-de-before",
        "round-trip-with-de-after",
        "round-trip-without-de",
        "one-way-with-de-before",
        "one-way-with-de-after",
        "one-way-without-de",
        "hangban-simple",
        "hangban-round-trip",
        "piao-one-way",
    ],
)
def test_offline_cli_extracts_only_the_destination(user_request, expected_destination, tmp_path):
    """Trip-type modifiers must not become part of the submitted destination."""
    demo = Path(__file__).with_name("demo.py")
    output_html = tmp_path / "form.html"
    result = subprocess.run(
        [
            sys.executable,
            str(demo),
            "--offline",
            "--request",
            user_request,
            "--output",
            str(output_html),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert f'"destination_city": "{expected_destination}"' in result.stdout
    assert f"已收到您的订票信息：上海 → {expected_destination}，出发日期" in result.stdout
    form_html_content = output_html.read_text(encoding="utf-8")
    assert f'"destination_city": "{expected_destination}"' in form_html_content
