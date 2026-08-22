import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from gen_star_history import (
    BUCKET_SECONDS,
    absorb,
    add_to_buckets,
    build_series,
    iso,
    new_shard,
    parse_iso_timestamp,
    plan_shards,
    resume_cursor,
)


def page(*starred_at, end_cursor="c", has_next=False):
    return {
        "edges": [{"starredAt": ts} for ts in starred_at],
        "pageInfo": {"endCursor": end_cursor, "hasNextPage": has_next},
    }


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
    """Contract: stargazers with fractional seconds and explicit tz offsets are charted without ValueError."""
    starred = [
        "2026-07-15T10:00:00.123Z",
        "2026-07-15T14:00:00+02:00",  # 12:00 UTC
        "2026-07-16T08:00:00Z",
    ]
    start = datetime(2026, 7, 15, 0, 0, 0, tzinfo=timezone.utc)
    buckets: dict[str, int] = {}
    add_to_buckets(buckets, starred, start, BUCKET_SECONDS)
    history = {
        "start": iso(start),
        "bucket_seconds": BUCKET_SECONDS,
        "total": 3,
        "latest": "2026-07-16T08:00:00Z",
        "buckets": buckets,
    }

    x, y = build_series(history)

    assert len(x) == 4  # anchor + one point per hour that gained stars
    assert len(y) == 4
    assert y[0] == 0
    assert y[-1] == 3


def test_build_series_starts_from_the_stars_predating_the_chart():
    """Contract: stars from before the start date are the curve's baseline, not a jump at the edge."""
    history = {
        "start": "2026-07-15T00:00:00Z",
        "bucket_seconds": BUCKET_SECONDS,
        "total": 150,
        "latest": "2026-07-15T10:30:00Z",
        "buckets": {"2026-07-15T10:00:00Z": 50},
    }

    _, y = build_series(history)

    assert y[0] == 100
    assert y[-1] == 150


def test_absorb_keeps_only_stars_below_the_shard_boundary():
    """Contract: a shard owns [cursor, hi), so a star at hi belongs to the next shard."""
    shard = new_shard("start", hi="2026-07-15T12:00:00Z")

    absorb(shard, page("2026-07-15T11:00:00Z", "2026-07-15T12:00:00Z", has_next=True))

    assert shard["times"] == ["2026-07-15T11:00:00Z"]
    assert shard["done"], "crossing the boundary ends the shard even with more pages available"


def test_absorb_only_trusts_a_cursor_for_a_fully_kept_page():
    """Contract: endCursor points at the last edge, so it is a valid resume point only if that edge was kept."""
    partial = new_shard("start", hi="2026-07-15T12:00:00Z")
    absorb(partial, page("2026-07-15T11:00:00Z", "2026-07-15T13:00:00Z", end_cursor="past-hi"))
    assert partial["tail"] is None

    whole = new_shard("start", hi="2026-07-15T12:00:00Z")
    absorb(whole, page("2026-07-15T11:00:00Z", end_cursor="kept"))
    assert whole["tail"] == ("2026-07-15T11:00:00Z", "kept")


def test_absorb_follows_pagination_until_the_stars_run_out():
    shard = new_shard("start", hi=None)

    absorb(shard, page("2026-07-15T11:00:00Z", end_cursor="next", has_next=True))
    assert not shard["done"]
    assert shard["cursor"] == "next"

    absorb(shard, page("2026-07-15T12:00:00Z", end_cursor="last", has_next=False))
    assert shard["done"]
    assert shard["times"] == ["2026-07-15T11:00:00Z", "2026-07-15T12:00:00Z"]


def test_plan_shards_tiles_the_range_without_gaps_or_overlap():
    """Contract: shard boundaries chain end-to-end so every star is fetched exactly once."""
    lo = datetime(2026, 7, 15, tzinfo=timezone.utc)
    hi = datetime(2026, 7, 25, tzinfo=timezone.utc)

    shards = plan_shards("resume-here", lo, hi, expected=500)

    assert len(shards) == 5
    assert shards[0]["cursor"] == "resume-here", "the first shard resumes from the real cursor"
    assert shards[-1]["hi"] is None, "the last shard stays open so new stars are not missed"
    for earlier, later in zip(shards, shards[1:]):
        # Each shard stops exactly where the next one starts seeking.
        assert earlier["hi"] is not None
        assert later["cursor"].startswith("Y3Vyc29y")


def test_plan_shards_stays_sequential_for_a_small_catch_up():
    shards = plan_shards(
        "resume-here",
        datetime(2026, 7, 15, tzinfo=timezone.utc),
        datetime(2026, 7, 16, tzinfo=timezone.utc),
        expected=40,
    )

    assert len(shards) == 1
    assert shards[0]["cursor"] == "resume-here"
    assert shards[0]["hi"] is None


def test_resume_cursor_is_the_one_next_to_the_newest_star():
    """Contract: the next run resumes after the newest star, whichever shard happened to hold it."""
    shards = [new_shard(None, None) for _ in range(3)]
    shards[0]["tail"] = ("2026-07-15T10:00:00Z", "old")
    shards[1]["tail"] = ("2026-07-17T10:00:00Z", "newest")
    shards[2]["tail"] = None  # an empty trailing range

    assert resume_cursor(shards) == "newest"
    assert resume_cursor([new_shard(None, None)]) is None
