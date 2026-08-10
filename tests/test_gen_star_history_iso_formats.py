import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from gen_star_history import build_series, parse_iso_timestamp


def test_parse_iso_timestamp_supports_various_iso_formats():
    """Contract: parse_iso_timestamp parses standard ISO 8601 strings into UTC datetimes."""
    timestamps = [
        "2026-07-15T12:34:56Z",
        "2026-07-15T12:34:56.789Z",
        "2026-07-15T12:34:56.123456Z",
        "2026-07-15T12:34:56+02:00",
        "2026-07-15T12:34:56-05:00",
        "2026-07-15T12:34:56",
        "2026-07-15",
    ]
    for ts in timestamps:
        dt = parse_iso_timestamp(ts)
        assert isinstance(dt, datetime)
        assert dt.tzinfo == timezone.utc


def test_build_series_handles_fractional_and_timezone_iso_strings():
    """Contract: build_series parses stargazers with fractional seconds and explicit tz offsets without ValueError."""
    starred = [
        "2026-07-15T10:00:00.123Z",
        "2026-07-15T14:00:00+02:00",
        "2026-07-16T08:00:00Z",
    ]
    start = datetime(2026, 7, 15, 0, 0, 0, tzinfo=timezone.utc)
    x, y = build_series(starred, start)

    assert len(x) == 4  # anchor + 3 points
    assert len(y) == 4
    assert y[0] == 0
    assert y[-1] == 3
