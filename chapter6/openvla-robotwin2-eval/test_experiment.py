import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("exp612", HERE / "experiment.py")
exp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(exp)


def config():
    return exp.resolve_config(HERE / "config.json")


def row(arm, chunk, source, seed, success=True):
    return {
        "schema_version": 1,
        "experiment": "6-12",
        "source": "upstream_val_only",
        "arm": arm,
        "upstream_commit": config()["expected_upstream_commit"],
        "task": "robotwin2_move_can_pot",
        "data_source": f"robotwin2_move_can_pot_{source}",
        "trial_id": seed,
        "trial_seed": seed,
        "success": success,
        "finish_action_steps": 100,
        "action_chunk_length": chunk,
        "action_dimension": 14,
        "rgb_views": 3,
        "proprioception_enabled": True,
    }


def test_command_is_exact_val_only_three_view_controlled(tmp_path, monkeypatch):
    cfg = config()
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    monkeypatch.setenv(cfg["checkpoint_env"], str(checkpoint))
    command = exp.hydra_command(cfg, "chunk_25", tmp_path, Path(cfg["upstream_path"]))
    joined = " ".join(command)
    assert "trainer.val_only=True" in joined
    assert "trainer.val_before_train=True" in joined
    assert "actor_rollout_ref.model.action_chunks_len=25" in joined
    assert "actor_rollout_ref.model.action_token_len=14" in joined
    assert "+actor_rollout_ref.rollout.action_token_len=14" in joined
    assert "actor_rollout_ref.rollout.num_images_in_input=3" in joined
    assert "actor_rollout_ref.rollout.use_proprio=True" in joined
    assert "data.val_batch_size=8" in joined
    assert "algorithm.adv_estimator=grpo" in joined
    assert "algorithm.kl_ctrl.kl_coef=0.0" in joined


def test_instrumentation_executes_only_the_configured_action_prefix():
    instrumenter = (HERE / "instrument_upstream.py").read_text(encoding="utf-8")
    assert "actions = actions[:, :configured_chunks, :]" in instrumenter
    assert "response = response[:, :response_tokens]" in instrumenter
    assert "response_tokens = configured_chunks * action_dimension" in instrumenter


def test_analysis_refuses_incomplete_or_unclassified_real_evidence(tmp_path):
    cfg = config()
    manifest = {
        "arms": {
            "chunk_1": {"rollout_directory": str(tmp_path / "videos1")},
            "chunk_25": {"rollout_directory": str(tmp_path / "videos25")},
        }
    }
    (tmp_path / "launch_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    for arm, chunk in (("chunk_1", 1), ("chunk_25", 25)):
        arm_dir = tmp_path / arm
        arm_dir.mkdir()
        rows = [row(arm, chunk, "train_iid", 1, success=False)]
        (arm_dir / "episodes.jsonl").write_text("\n".join(json.dumps(item) for item in rows) + "\n", encoding="utf-8")
    report = exp.analyze(cfg, tmp_path, None)
    assert report["strict_completion"]["complete"] is False
    assert any("expected 256 episodes" in error for error in report["strict_completion"]["errors"])
    assert any("failure annotations" in error for error in report["strict_completion"]["errors"])


def test_preflight_never_claims_ready_without_real_hardware(monkeypatch):
    cfg = config()
    monkeypatch.delenv(cfg["checkpoint_env"], raising=False)
    monkeypatch.delenv(cfg["robotwin2_env"], raising=False)
    monkeypatch.setattr(exp, "gpu_inventory", lambda: ([], "no NVIDIA runtime"))
    report = exp.preflight(cfg)
    assert report["ready_for_real_validation"] is False
    assert "pretrained_checkpoint" in report["blocking_checks"]
    assert "robotwin2_checkout" in report["blocking_checks"]
    assert "pinned_robotwin2_commit" in report["blocking_checks"]
    assert "nvidia_gpu_count" in report["blocking_checks"]


def test_distribution_reports_required_completion_percentiles():
    stats = exp.distribution([1.0, 2.0, 3.0, 4.0])
    assert stats["count"] == 4
    assert stats["p50"] == 2.5
    assert stats["p95"] is not None


def test_video_index_excludes_stale_duplicate_outside_process_window(tmp_path):
    name = "step=0--task=move_can_pot_trial_1_seed_1--success=False--ran={}.mp4"
    stale = tmp_path / name.format("stale")
    current = tmp_path / name.format("current")
    stale.write_bytes(b"stale")
    current.write_bytes(b"current")
    os.utime(stale, (100.0, 100.0))
    os.utime(current, (200.0, 200.0))
    index = exp.video_index(
        tmp_path,
        started_at_utc=datetime.fromtimestamp(150, timezone.utc).isoformat(),
        ended_at_utc=datetime.fromtimestamp(250, timezone.utc).isoformat(),
    )
    assert index == {
        ("move_can_pot_trial_1_seed_1", False): [str(current.resolve())]
    }
