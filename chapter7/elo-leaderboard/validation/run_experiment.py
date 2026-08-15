"""Run the complete, evidence-producing Experiment 6-6 campaign.

The public Arena file is deliberately not copied into git.  A canonical run
binds the exact input by URL, size, record count, and SHA-256, then retains all
derived tables, visualizations, the D3 history animation, and a manifest that
hashes every output and the source used to create it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import kendalltau, spearmanr

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
sys.path.insert(0, str(PROJECT))

from animation import create_simple_animation
from bradley_terry import compute_bradley_terry_leaderboard
from optimized_elo import (
    NumpyEloRatingSystem,
    process_elo_updates_vectorized,
)

DATASET_URL = (
    "https://storage.googleapis.com/arena_external_data/public/"
    "clean_battle_20240814_public.json"
)
REQUIRED_COLUMNS = ["model_a", "model_b", "winner", "tstamp", "anony", "turn"]
ALLOWED_OUTCOMES = {"model_a", "model_b", "tie", "tie (bothbad)"}


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def json_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def load_and_filter(path: Path, max_records: int) -> tuple[pd.DataFrame, dict[str, Any]]:
    started = time.perf_counter()
    raw = pd.read_json(path)
    missing = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing:
        raise ValueError(f"Arena input is missing columns: {missing}")

    source_records = len(raw)
    frame = raw[REQUIRED_COLUMNS + (["dedup_tag"] if "dedup_tag" in raw else [])].copy()
    del raw
    frame = frame[frame["anony"].eq(True) & frame["turn"].ge(1)]
    if "dedup_tag" in frame:
        sampled = frame["dedup_tag"].map(
            lambda value: bool(value.get("sampled", False)) if isinstance(value, dict) else False
        )
        frame = frame[sampled]
    frame = frame[frame["winner"].isin(ALLOWED_OUTCOMES)]
    frame = frame.sort_values("tstamp", kind="stable").reset_index(drop=True)
    if max_records:
        frame = frame.head(max_records).copy()
    if frame.empty:
        raise ValueError("Arena filtering produced no accepted blind votes")

    metadata = {
        "source_records": source_records,
        "accepted_records": len(frame),
        "model_count": len(set(frame["model_a"]) | set(frame["model_b"])),
        "start_utc": datetime.fromtimestamp(float(frame["tstamp"].min()), timezone.utc).isoformat(),
        "end_utc": datetime.fromtimestamp(float(frame["tstamp"].max()), timezone.utc).isoformat(),
        "outcomes": {str(k): int(v) for k, v in frame["winner"].value_counts().items()},
        "load_filter_seconds": round(time.perf_counter() - started, 3),
        "bounded_test_run": bool(max_records),
    }
    return frame, metadata


def online_elo_and_history(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, NumpyEloRatingSystem, float]:
    started = time.perf_counter()
    system = NumpyEloRatingSystem(initial_rating=1000.0, k_factor=4.0)
    model_a, model_b, outcomes = system._prepare_data(frame)

    months = (
        pd.to_datetime(frame["tstamp"], unit="s", utc=True)
        .dt.tz_localize(None)
        .dt.to_period("M")
    )
    boundaries = np.flatnonzero(months.to_numpy()[1:] != months.to_numpy()[:-1]) + 1
    boundaries = np.append(boundaries, len(frame))
    start = 0
    history_rows: list[dict[str, Any]] = []
    for stop in boundaries:
        process_elo_updates_vectorized(
            system.ratings,
            model_a[start:stop],
            model_b[start:stop],
            outcomes[start:stop],
            system.k_factor,
            system.match_counts,
            system.win_counts,
        )
        snapshot = system.get_leaderboard()
        date = pd.to_datetime(float(frame.iloc[stop - 1]["tstamp"]), unit="s", utc=True)
        for rank, (model, rating, matches, wins) in enumerate(snapshot, 1):
            history_rows.append(
                {
                    "date": date.tz_localize(None),
                    "model": model,
                    "rating": rating,
                    "rank": rank,
                    "matches": matches,
                    "wins": wins,
                }
            )
        start = int(stop)

    leaderboard = pd.DataFrame(
        system.get_leaderboard(), columns=["model", "rating", "matches", "wins"]
    )
    leaderboard.insert(0, "rank", range(1, len(leaderboard) + 1))
    history = pd.DataFrame(history_rows)
    return leaderboard, history, system, round(time.perf_counter() - started, 3)


def rank_comparison(online: pd.DataFrame, official_method: pd.DataFrame) -> dict[str, Any]:
    online_rank = online.set_index("model")["rank"]
    official = official_method.sort_values("rating", ascending=False).reset_index(drop=True)
    official["rank"] = np.arange(1, len(official) + 1)
    official_rank = official.set_index("model")["rank"]
    common = sorted(set(online_rank.index) & set(official_rank.index))
    rho = spearmanr(online_rank.loc[common], official_rank.loc[common]).statistic
    tau = kendalltau(online_rank.loc[common], official_rank.loc[common]).statistic
    online_top = online.nsmallest(20, "rank")["model"].tolist()
    official_top = official.nsmallest(20, "rank")["model"].tolist()
    return {
        "comparison_target": "Bradley-Terry MLE reconstruction used by Chatbot Arena",
        "claim_boundary": (
            "This is a same-snapshot reconstruction of the official method, not a scrape of "
            "the mutable live leaderboard. Scores need not match the live service."
        ),
        "common_models": len(common),
        "spearman_rank_correlation": round(float(rho), 6),
        "kendall_rank_correlation": round(float(tau), 6),
        "top_20_overlap": len(set(online_top) & set(official_top)),
        "online_top_20": online_top,
        "official_method_top_20": official_top,
    }


def empirical_matrix(frame: pd.DataFrame, models: list[str]) -> pd.DataFrame:
    subset = frame[frame["model_a"].isin(models) & frame["model_b"].isin(models)].copy()
    rows: list[tuple[str, str, float]] = []
    for a, b, winner in subset[["model_a", "model_b", "winner"]].itertuples(index=False):
        score = 1.0 if winner == "model_a" else 0.0 if winner == "model_b" else 0.5
        rows.append((a, b, score))
        rows.append((b, a, 1.0 - score))
    scored = pd.DataFrame(rows, columns=["model", "opponent", "score"])
    matrix = scored.pivot_table(index="model", columns="opponent", values="score", aggfunc="mean")
    matrix = matrix.reindex(index=models, columns=models)
    np.fill_diagonal(matrix.values, 0.5)
    return matrix


def plot_artifacts(
    out: Path,
    online: pd.DataFrame,
    history: pd.DataFrame,
    empirical: pd.DataFrame,
) -> None:
    top = online.head(20).sort_values("rating")
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.barh(top["model"], top["rating"], color="#3b82f6")
    ax.set_title("Experiment 6-6: Online Elo leaderboard")
    ax.set_xlabel("Elo rating (K=4, chronological)")
    fig.tight_layout()
    fig.savefig(out / "leaderboard.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(13, 11))
    sns.heatmap(empirical, cmap="RdYlGn", center=0.5, vmin=0, vmax=1, ax=ax)
    ax.set_title("Empirical pairwise win rate — final online-Elo top 20")
    fig.tight_layout()
    fig.savefig(out / "win_rate_matrix.png", dpi=180)
    plt.close(fig)

    top_models = online.head(10)["model"].tolist()
    fig, ax = plt.subplots(figsize=(13, 7))
    for model in top_models:
        values = history[history["model"].eq(model)].sort_values("date")
        ax.plot(values["date"], values["rating"], label=model, linewidth=1.8)
    ax.set_title("Monthly online-Elo evolution — final top 10")
    ax.set_ylabel("Elo rating")
    ax.legend(fontsize=7, ncol=2)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out / "rating_history.png", dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Downloaded public Arena JSON")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--bootstrap-rounds", type=int, default=20)
    parser.add_argument("--max-records", type=int, default=0, help="Noncanonical bounded test only")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    input_path = args.input.resolve()
    if not input_path.is_file():
        raise SystemExit(f"Arena input not found: {input_path}")

    run_started = time.perf_counter()
    input_hash = sha256_file(input_path)
    frame, dataset = load_and_filter(input_path, args.max_records)
    online, history, online_system, online_seconds = online_elo_and_history(frame)

    bt_started = time.perf_counter()
    official_method = compute_bradley_terry_leaderboard(
        frame[["model_a", "model_b", "winner"]],
        bootstrap_rounds=args.bootstrap_rounds,
    )
    bt_seconds = round(time.perf_counter() - bt_started, 3)
    official_method = official_method.sort_values("rating", ascending=False).reset_index(drop=True)
    official_method.insert(0, "rank", range(1, len(official_method) + 1))

    comparison = rank_comparison(online, official_method)
    top_models = online.head(20)["model"].tolist()
    empirical = empirical_matrix(frame, top_models)
    predicted = pd.DataFrame(
        {
            opponent: {
                model: online_system.calculate_win_probability(model, opponent)
                for model in top_models
            }
            for opponent in top_models
        }
    ).reindex(index=top_models, columns=top_models)

    write_json(args.output_dir / "online_elo.json", json_records(online))
    write_json(args.output_dir / "bradley_terry.json", json_records(official_method))
    write_json(
        args.output_dir / "win_rate_matrix.json",
        {
            "models": top_models,
            "empirical": empirical.where(pd.notna(empirical), None).to_dict(orient="index"),
            "online_elo_predicted": predicted.to_dict(orient="index"),
        },
    )
    write_json(args.output_dir / "rating_history.json", json_records(history))
    plot_artifacts(args.output_dir, online, history, empirical)
    create_simple_animation(history, str(args.output_dir / "leaderboard_animation.html"), top_n=15)

    gates = {
        "official_public_arena_snapshot_hashed": not args.max_records,
        "millions_of_blind_votes_loaded": dataset["source_records"] >= 1_000_000,
        "chronological_online_elo_k4_completed": len(online) == dataset["model_count"],
        "bradley_terry_official_method_completed": len(official_method) == dataset["model_count"],
        "online_vs_official_method_rank_agreement_observed": (
            comparison["spearman_rank_correlation"] >= 0.70
            and comparison["top_20_overlap"] >= 10
        ),
        "pairwise_empirical_and_predicted_matrix_saved": len(empirical) == 20,
        "monthly_history_saved": history["date"].nunique() >= 2,
        "d3_animation_saved": (args.output_dir / "leaderboard_animation.html").is_file(),
        "static_visualizations_saved": all(
            (args.output_dir / name).is_file()
            for name in ["leaderboard.png", "win_rate_matrix.png", "rating_history.png"]
        ),
    }
    accepted = all(gates.values())
    summary = {
        "schema_version": 1,
        "experiment": "6-6",
        "status": "passed" if accepted else "noncanonical_test",
        "official_complete": accepted,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "url": DATASET_URL,
            "path_recorded_as": input_path.name,
            "bytes": input_path.stat().st_size,
            "sha256": input_hash,
            **dataset,
        },
        "protocol": {
            "online_elo": "initial=1000, K=4, stable chronological order",
            "official_method": "Bradley-Terry maximum-likelihood reconstruction",
            "history_interval": "monthly cumulative snapshots",
            "bootstrap_rounds": args.bootstrap_rounds,
            "bootstrap_random_seed": 0,
        },
        "results": {
            "online_top_20": json_records(online.head(20)),
            "official_method_top_20": json_records(official_method.head(20)),
            "rank_comparison": comparison,
        },
        "timing_seconds": {
            "online_and_history": online_seconds,
            "bradley_terry": bt_seconds,
            "total": round(time.perf_counter() - run_started, 3),
        },
        "gates": gates,
    }
    write_json(args.output_dir / "summary.json", summary)

    artifact_names = [
        "online_elo.json",
        "bradley_terry.json",
        "win_rate_matrix.json",
        "rating_history.json",
        "leaderboard.png",
        "win_rate_matrix.png",
        "rating_history.png",
        "leaderboard_animation.html",
        "summary.json",
    ]
    source_names = [
        "animation.py",
        "bradley_terry.py",
        "optimized_elo.py",
        "validation/run_experiment.py",
        "validation/validate_evidence.py",
    ]
    manifest = {
        "schema_version": 1,
        "experiment": "6-6",
        "status": summary["status"],
        "official_complete": accepted,
        "input": {
            "url": DATASET_URL,
            "filename": input_path.name,
            "bytes": input_path.stat().st_size,
            "sha256": input_hash,
        },
        "artifacts": {
            name: {"bytes": (args.output_dir / name).stat().st_size, "sha256": sha256_file(args.output_dir / name)}
            for name in artifact_names
        },
        "sources": {
            name: sha256_file(PROJECT / name)
            for name in source_names
        },
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "gates": gates,
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "output": str(args.output_dir)}, indent=2))
    if not accepted:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
