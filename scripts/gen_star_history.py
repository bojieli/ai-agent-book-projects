#!/usr/bin/env python3
"""Render this repo's star history as PNG images (light + dark variants).

Star timestamps come from the GitHub GraphQL API and are kept in a small
committed data file (see DATA_FILE) as per-hour counts, so each run only has
to fetch the stars added since the previous one. Output:
assets/star-history-{light,dark}.png

Usage:
    python scripts/gen_star_history.py [--repo owner/name] [--start-date YYYY-MM-DD]
                                       [--out-dir DIR] [--rebuild] [--offline]

Auth: set GITHUB_TOKEN (or GH_TOKEN, or have an authenticated `gh` CLI).
The GraphQL API requires a token, so --offline is the only way to redraw
without one.

Why GraphQL and not REST: /repos/{repo}/stargazers refuses to paginate past
40,000 stargazers (HTTP 422), which this repo passed in August 2026.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from matplotlib.ticker import FuncFormatter

REPO = "bojieli/ai-agent-book"
START_DATE = "2026-07-15"  # UTC; stars before this date are excluded
DATA_FILE = Path(__file__).with_name("star-history-data.json")

GRAPHQL_URL = "https://api.github.com/graphql"
# Stars are stored as counts per bucket rather than as individual timestamps:
# one hour is ~2px wide on the rendered chart, so the curve is unchanged while
# the data file stays small enough to commit and diff.
BUCKET_SECONDS = 3600
# A rebuild walks the whole history, so it fans out over disjoint time ranges.
# One request carries several pages as aliased fields, which costs barely more
# than a single page.
PAGES_PER_REQUEST = 10
REBUILD_WORKERS = 6
STARS_PER_SHARD = 100
MAX_SHARDS = 1024
# Below this, following cursors one page at a time is quick enough that it is
# not worth leaning on synthesized cursors.
SHARD_THRESHOLD = 2000

ACCENT = "#f5a623"  # warm amber, reads well on both light and dark

THEMES = {
    "light": dict(bg="#ffffff", text="#1f2328", subtext="#6a737d", grid="#dfe3e8"),
    "dark": dict(bg="#0d1117", text="#e6edf3", subtext="#8b949e", grid="#272d35"),
}

# Upper bound on x-axis labels. The real guarantee comes from measuring the
# rendered labels (see thin_xticklabels); this just keeps the tick step sane.
MAX_XTICKS = 12
DAY_STEPS = (1, 2, 3, 7, 14)  # days between ticks
MONTH_STEPS = (1, 2, 3, 6)
YEAR_STEPS = (1, 2, 5, 10)


def get_token() -> str | None:
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if token := os.environ.get(var, "").strip():
            return token
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=10
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return None


def parse_iso_timestamp(s: str) -> datetime:
    """Parse ISO-8601 timestamps (including fractional seconds and offsets) into UTC."""
    s = s.strip()
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def iso(dt: datetime) -> str:
    """The exact spelling GitHub uses, so timestamps compare correctly as strings."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# GraphQL plumbing
# --------------------------------------------------------------------------


class GraphQLError(RuntimeError):
    pass


def graphql(query: str, variables: dict, token: str, retries: int = 4) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "gen-star-history",
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(GRAPHQL_URL, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.load(resp)
            if errors := payload.get("errors"):
                raise GraphQLError("; ".join(e.get("message", str(e)) for e in errors))
            return payload["data"]
        except Exception as exc:
            if attempt == retries - 1:
                raise
            # Secondary rate limits want a longer pause than a transient blip.
            throttled = isinstance(exc, urllib.error.HTTPError) and exc.code in (403, 429)
            wait = (10 if throttled else 2) * 2**attempt
            print(f"request failed ({exc}); retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)
    raise AssertionError("unreachable")


def repo_summary(repo: str, token: str) -> tuple[int, datetime]:
    owner, name = repo.split("/", 1)
    data = graphql(
        "query($owner:String!,$name:String!){repository(owner:$owner,name:$name)"
        "{stargazerCount createdAt}}",
        {"owner": owner, "name": name},
        token,
    )
    node = data["repository"]
    return node["stargazerCount"], parse_iso_timestamp(node["createdAt"])


def page_query(pages: int) -> str:
    """One query fetching `pages` stargazer pages, each from its own cursor."""
    args = ",".join(f"$c{i}:String" for i in range(pages))
    fields = " ".join(
        f"p{i}:repository(owner:$owner,name:$name)"
        f"{{stargazers(first:100,orderBy:{{field:STARRED_AT,direction:ASC}},after:$c{i})"
        f"{{pageInfo{{endCursor hasNextPage}} edges{{starredAt}}}}}}"
        for i in range(pages)
    )
    return f"query($owner:String!,$name:String!,{args}){{{fields}}}"


def cursor_at(dt: datetime) -> str:
    """A stargazer cursor positioned just before `dt`.

    GitHub's stargazer cursors are keyset positions -- base64 of
    ``cursor:v2:`` plus a msgpack ``[starredAt, user_id]`` pair -- so one can
    be synthesized to seek straight to a point in time instead of paging there.
    That is undocumented, hence probe_cursor_synthesis() below; only --rebuild
    depends on it, and it falls back to plain sequential paging.
    """
    stamp = iso(dt)
    packed = b"\x92" + bytes([0xA0 + len(stamp)]) + stamp.encode() + b"\xce" + struct.pack(">I", 0)
    return base64.b64encode(b"cursor:v2:" + packed).decode()


def probe_cursor_synthesis(repo: str, at: datetime, token: str) -> bool:
    """Check that a synthesized cursor really seeks to `at` before relying on it."""
    owner, name = repo.split("/", 1)
    try:
        data = graphql(page_query(1), {"owner": owner, "name": name, "c0": cursor_at(at)}, token)
        edges = data["p0"]["stargazers"]["edges"]
    except Exception as exc:
        print(f"cursor synthesis unavailable ({exc})", file=sys.stderr)
        return False
    # A cursor GitHub does not understand would restart from the oldest star.
    return bool(edges) and edges[0]["starredAt"] >= iso(at)


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------


def new_shard(cursor: str | None, hi: str | None) -> dict:
    """A half-open [cursor, hi) slice of the stargazer list, paged independently."""
    return {"cursor": cursor, "hi": hi, "times": [], "tail": None, "done": False}


def absorb(shard: dict, conn: dict) -> None:
    edges = conn["edges"]
    if not edges:
        shard["done"] = True
        return
    overflowed = False
    for edge in edges:
        starred_at = edge["starredAt"]
        if shard["hi"] is not None and starred_at >= shard["hi"]:
            overflowed = True
            break
        shard["times"].append(starred_at)
    page = conn["pageInfo"]
    if not overflowed and shard["times"]:
        # Only meaningful when the whole page was kept: endCursor points at the
        # last edge, which is then also the last star this shard accepted.
        shard["tail"] = (shard["times"][-1], page["endCursor"])
    if overflowed or not page["hasNextPage"]:
        shard["done"] = True
    else:
        shard["cursor"] = page["endCursor"]


def run_shards(repo: str, shards: list[dict], token: str, *, pages: int, workers: int) -> None:
    owner, name = repo.split("/", 1)

    def run_group(group: list[dict]) -> None:
        variables = {"owner": owner, "name": name}
        variables.update({f"c{i}": s["cursor"] for i, s in enumerate(group)})
        data = graphql(page_query(len(group)), variables, token)
        for i, shard in enumerate(group):
            absorb(shard, data[f"p{i}"]["stargazers"])

    pending = [s for s in shards if not s["done"]]
    while pending:
        groups = [pending[i : i + pages] for i in range(0, len(pending), pages)]
        if workers > 1 and len(groups) > 1:
            with ThreadPoolExecutor(min(workers, len(groups))) as pool:
                list(pool.map(run_group, groups))
        else:
            for group in groups:
                run_group(group)
        fetched = sum(len(s["times"]) for s in shards)
        print(f"\rfetched {fetched} stars...", end="", file=sys.stderr)
        pending = [s for s in pending if not s["done"]]
    print(file=sys.stderr)


def resume_cursor(shards: list[dict]) -> str | None:
    """Cursor of the newest star seen, to resume from on the next run.

    The page holding the newest star can never have overflowed its shard --
    nothing sorts after it -- so that shard's tail is always recorded.
    """
    tails = [s["tail"] for s in shards if s["tail"]]
    return max(tails)[1] if tails else None


def plan_shards(cursor: str | None, lo: datetime, hi: datetime, expected: int) -> list[dict]:
    """Cut the stars between `lo` and `hi` into ranges that can be paged in parallel.

    The first range resumes from `cursor` itself -- a real cursor, so the
    boundary against already-counted stars is exact -- and the rest seek to a
    timestamp. Ranges are half-open, so no star is counted twice.
    """
    count = max(1, min(MAX_SHARDS, -(-expected // STARS_PER_SHARD)))
    if count == 1:
        return [new_shard(cursor, None)]
    step = (hi - lo) / count
    edges = [lo + step * i for i in range(1, count)]
    shards = [new_shard(cursor, iso(edges[0]))]
    for i, edge in enumerate(edges):
        shards.append(new_shard(cursor_at(edge), iso(edges[i + 1]) if i + 1 < len(edges) else None))
    return shards


def fetch_forward(
    repo: str, token: str, *, cursor: str | None, lo: datetime, expected: int, what: str
) -> list[dict]:
    """Every star after `cursor` (None for the whole history).

    Paging is sequential -- plain, documented cursor following -- unless there
    is enough to fetch that fanning out over synthesized time ranges is worth
    the extra machinery.
    """
    hi = datetime.now(timezone.utc)
    if expected >= SHARD_THRESHOLD and probe_cursor_synthesis(repo, lo + (hi - lo) / 2, token):
        shards = plan_shards(cursor, lo, hi, expected)
        print(f"{what} over {len(shards)} ranges...", file=sys.stderr)
        run_shards(repo, shards, token, pages=PAGES_PER_REQUEST, workers=REBUILD_WORKERS)
        return shards

    print(f"{what} one page at a time...", file=sys.stderr)
    shards = [new_shard(cursor, None)]
    run_shards(repo, shards, token, pages=1, workers=1)
    return shards


# --------------------------------------------------------------------------
# Stored history
# --------------------------------------------------------------------------


def bucket_key(starred_at: str, bucket_seconds: int) -> str:
    epoch = int(parse_iso_timestamp(starred_at).timestamp())
    floored = epoch - epoch % bucket_seconds
    return iso(datetime.fromtimestamp(floored, tz=timezone.utc))


def add_to_buckets(buckets: dict[str, int], times: list[str], start: datetime, bucket_seconds: int) -> None:
    cutoff = iso(start)
    for starred_at in times:
        if starred_at < cutoff:
            continue
        key = bucket_key(starred_at, bucket_seconds)
        buckets[key] = buckets.get(key, 0) + 1


def save_history(history: dict) -> None:
    ordered = {
        "repo": history["repo"],
        "start": history["start"],
        "bucket_seconds": history["bucket_seconds"],
        "total": history["total"],
        "before_start": history["before_start"],
        "latest": history["latest"],
        "cursor": history["cursor"],
        "buckets": dict(sorted(history["buckets"].items())),
    }
    # One bucket per line keeps the daily commit diff to the lines that changed.
    body = json.dumps(ordered, indent=1)
    DATA_FILE.write_text(body + "\n")


def load_history(repo: str, start: datetime) -> dict | None:
    if not DATA_FILE.exists():
        return None
    history = json.loads(DATA_FILE.read_text())
    stale = (
        history.get("repo") != repo
        or history.get("start") != iso(start)
        or history.get("bucket_seconds") != BUCKET_SECONDS
        or not history.get("cursor")
    )
    if stale:
        print("stored history does not match the requested chart; rebuilding", file=sys.stderr)
        return None
    return history


def rebuild(repo: str, start: datetime, count: int, created_at: datetime, token: str) -> dict:
    shards = fetch_forward(
        repo, token, cursor=None, lo=created_at, expected=count, what="rebuilding"
    )
    times = sorted(t for shard in shards for t in shard["times"])
    # Stars keep arriving mid-fetch, so this only has to be close; a real gap
    # means the time ranges did not tile the history and cannot be trusted.
    if len(shards) > 1 and abs(len(times) - count) > max(25, count // 1000):
        print(
            f"fanned-out fetch got {len(times)} stars but the repo has {count}; "
            "retrying one page at a time",
            file=sys.stderr,
        )
        shards = [new_shard(None, None)]
        run_shards(repo, shards, token, pages=1, workers=1)
        times = sorted(shards[0]["times"])
    if not times:
        raise SystemExit(f"{repo} has no stargazers to chart")
    buckets: dict[str, int] = {}
    add_to_buckets(buckets, times, start, BUCKET_SECONDS)
    return {
        "repo": repo,
        "start": iso(start),
        "bucket_seconds": BUCKET_SECONDS,
        "total": len(times),
        "before_start": len(times) - sum(buckets.values()),
        "latest": times[-1],
        "cursor": resume_cursor(shards),
        "buckets": buckets,
    }


def update(repo: str, start: datetime, count: int, created_at: datetime, token: str) -> dict:
    history = load_history(repo, start)
    if history is None:
        return rebuild(repo, start, count, created_at, token)

    shards = fetch_forward(
        repo,
        token,
        cursor=history["cursor"],
        lo=parse_iso_timestamp(history["latest"]),
        expected=max(0, count - history["total"]),
        what="updating",
    )
    times = sorted(t for shard in shards for t in shard["times"])
    if times:
        add_to_buckets(history["buckets"], times, start, BUCKET_SECONDS)
        history["latest"] = times[-1]
        history["cursor"] = resume_cursor(shards) or history["cursor"]
    history["total"] = count

    # Unstarring silently invalidates counts we recorded earlier. Small drifts
    # are absorbed by the pre-START_DATE base (a rounding error against 40k
    # stars); a large one means the stored buckets are worth re-deriving.
    base = count - sum(history["buckets"].values())
    if base < 0 or abs(base - history["before_start"]) > max(50, count // 1000):
        print(f"stored history drifted from the live count ({count}); rebuilding", file=sys.stderr)
        return rebuild(repo, start, count, created_at, token)
    return history


def build_series(history: dict) -> tuple[np.ndarray, np.ndarray]:
    """Cumulative star count over time, anchored at the chart's start date."""
    start = parse_iso_timestamp(history["start"])
    latest = parse_iso_timestamp(history["latest"])
    step = timedelta(seconds=history["bucket_seconds"])
    running = max(0, history["total"] - sum(history["buckets"].values()))

    x = [mdates.date2num(start)]
    y = [running]
    for key in sorted(history["buckets"]):
        running += history["buckets"][key]
        # A bucket's stars are all in by the time it ends -- except the newest
        # bucket, which is still open.
        edge = min(parse_iso_timestamp(key) + step, latest)
        x.append(mdates.date2num(edge))
        y.append(running)
    return np.array(x), np.array(y)


# --------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------


def pick_xticks(x0: float, x1: float) -> tuple[list[float], str]:
    """Evenly spaced x tick positions plus a date format for the given span.

    Ticks are anchored at the newest date and step backwards, so the latest
    day is always labeled. The granularity coarsens from days to months to
    years as the history grows, keeping the label count at or below
    MAX_XTICKS instead of drawing one tick per day forever.
    """
    start = mdates.num2date(x0)
    end = mdates.num2date(x1)
    span_days = x1 - x0

    for step in DAY_STEPS:
        if span_days / step <= MAX_XTICKS:
            anchor = end.replace(hour=0, minute=0, second=0, microsecond=0)
            ticks = []
            while (num := mdates.date2num(anchor)) >= x0:
                ticks.append(num)
                anchor -= timedelta(days=step)
            fmt = "%b %-d" if start.year == end.year else "%b %-d, %Y"
            return sorted(ticks), fmt

    span_months = (end.year - start.year) * 12 + end.month - start.month
    for step in MONTH_STEPS:
        if span_months / step <= MAX_XTICKS:
            # Month starts read better than an offset from "today" here.
            year, month = end.year, end.month
            ticks = []
            while (num := mdates.date2num(end.replace(
                year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0
            ))) >= x0:
                ticks.append(num)
                month -= step
                while month < 1:
                    month += 12
                    year -= 1
            fmt = "%b %Y" if start.year != end.year else "%b"
            return sorted(ticks), fmt

    # Year granularity is the coarsest fallback, so widen the step as far as
    # needed rather than giving up and returning a crowded axis.
    span_years = end.year - start.year
    step = next(
        (s for s in YEAR_STEPS if span_years / s <= MAX_XTICKS),
        max(1, -(-span_years // MAX_XTICKS)),
    )
    year = end.year
    ticks = []
    while (num := mdates.date2num(end.replace(
        year=year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    ))) >= x0:
        ticks.append(num)
        year -= step
    return sorted(ticks), "%Y"


def thin_xticklabels(fig, ax, min_gap: float = 14.0) -> None:
    """Drop every n-th label until neighbours no longer crowd each other.

    pick_xticks bounds the tick *count*, but whether the labels actually fit
    depends on the rendered text width and figure size, so measure the drawn
    labels and thin from the right (keeping the newest date) until every pair
    is at least `min_gap` pixels apart.
    """
    ticks = list(ax.get_xticks())
    for keep in range(1, max(len(ticks), 1) + 1):
        kept = ticks[::-1][::keep][::-1]
        ax.set_xticks(kept)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        boxes = [
            lbl.get_window_extent(renderer=renderer)
            for lbl in ax.get_xticklabels()
            if lbl.get_text()
        ]
        if all(
            nxt.x0 - cur.x1 >= min_gap for cur, nxt in zip(boxes, boxes[1:])
        ):
            return


def draw(x: np.ndarray, y: np.ndarray, repo: str, theme_name: str, theme: dict, out: Path) -> None:
    bg, text, subtext, grid = theme["bg"], theme["text"], theme["subtext"], theme["grid"]

    fig, ax = plt.subplots(figsize=(12, 6.2), dpi=200)
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    fig.subplots_adjust(left=0.075, right=0.97, top=0.80, bottom=0.10)

    ax.set_ylim(0, y.max() * 1.10)
    ax.set_xlim(x[0], x[-1] + (x[-1] - x[0]) * 0.03)

    # Gradient fill under the curve: accent fading from top to transparent.
    r, g, b, _ = to_rgba(ACCENT)
    fade = LinearSegmentedColormap.from_list("fade", [(r, g, b, 0.0), (r, g, b, 0.35)])
    grad = np.linspace(0, 1, 256).reshape(-1, 1)
    im = ax.imshow(
        grad,
        aspect="auto",
        cmap=fade,
        origin="lower",
        extent=[ax.get_xlim()[0], ax.get_xlim()[1], 0, ax.get_ylim()[1]],
        zorder=1,
    )
    xs = np.concatenate([[x[0]], x, [x[-1]]])
    ys = np.concatenate([[0.0], y, [0.0]])
    (clip,) = ax.fill(xs, ys, alpha=0, zorder=1)
    im.set_clip_path(clip)

    # Glow underlay + main line.
    ax.plot(x, y, color=ACCENT, linewidth=7, alpha=0.10, solid_capstyle="round", zorder=2)
    ax.plot(x, y, color=ACCENT, linewidth=2.6, solid_capstyle="round", zorder=3)

    # Latest value: end dot + bold annotation.
    ax.scatter([x[-1]], [y[-1]], s=70, color=ACCENT, edgecolor=bg, linewidth=2.2, zorder=4)
    ax.annotate(
        f"{int(y[-1]):,} stars",
        xy=(x[-1], y[-1]),
        xytext=(-6, 14),
        textcoords="offset points",
        ha="right",
        fontsize=16,
        fontweight="bold",
        color=text,
    )

    # Titles.
    fig.text(0.075, 0.93, "Star History", fontsize=22, fontweight="bold", color=text)
    fig.text(0.075, 0.862, repo, fontsize=12.5, color=subtext)

    # Grid, spines, ticks.
    ax.yaxis.grid(True, color=grid, linewidth=0.9, linestyle=(0, (5, 4)))
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(grid)
    ax.tick_params(axis="both", length=0, labelsize=11.5, colors=subtext, pad=8)
    ticks, date_fmt = pick_xticks(*ax.get_xlim())
    ax.set_xticks(ticks)
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_fmt))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{int(v):,}"))
    thin_xticklabels(fig, ax)

    fig.savefig(out, facecolor=bg, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=REPO)
    parser.add_argument("--start-date", default=START_DATE)
    parser.add_argument("--out-dir", default="assets")
    parser.add_argument(
        "--rebuild", action="store_true", help="re-fetch the whole history instead of resuming"
    )
    parser.add_argument(
        "--offline", action="store_true", help="redraw from the stored history without any requests"
    )
    args = parser.parse_args()

    start = parse_iso_timestamp(args.start_date)

    if args.offline:
        history = load_history(args.repo, start)
        if history is None:
            raise SystemExit(f"--offline needs an up-to-date {DATA_FILE}")
    else:
        token = get_token()
        if not token:
            raise SystemExit("the GitHub GraphQL API needs a token; set GITHUB_TOKEN")
        count, created_at = repo_summary(args.repo, token)
        if args.rebuild:
            history = rebuild(args.repo, start, count, created_at, token)
        else:
            history = update(args.repo, start, count, created_at, token)
        save_history(history)

    x, y = build_series(history)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, theme in THEMES.items():
        draw(x, y, args.repo, name, theme, out_dir / f"star-history-{name}.png")


if __name__ == "__main__":
    main()
