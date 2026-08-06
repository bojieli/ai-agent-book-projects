#!/usr/bin/env python3
"""Fail-closed instrumentation for a disposable SimpleVLA-RL worktree."""

from __future__ import annotations

import argparse
from pathlib import Path


EPISODE_RECORDER = '''        # Experiment 6-12 instrumentation. This patch is applied only to a
        # disposable worktree; the upstream checkout remains clean. Preserve
        # one row per real RoboTwin2 validation episode so the companion can
        # audit paired seeds, action counts and exact environment rewards.
        evidence_path = os.environ.get("EXP6_12_EPISODE_JSONL")
        if evidence_path:
            def _ints(name, default=-1):
                if name not in data.batch:
                    return [default] * batch_size
                values = data.batch[name].detach().cpu().reshape(batch_size, -1)
                return [int(row[0].item()) for row in values]

            sources = data.non_tensor_batch.get(
                'data_source',
                [self.config.data.task_suite_name] * batch_size,
            )
            trial_ids = _ints('trial_id')
            trial_seeds = _ints('trial_seed')
            finish_steps = _ints('finish_step', 0)
            os.makedirs(os.path.dirname(os.path.abspath(evidence_path)), exist_ok=True)
            with open(evidence_path, "a", encoding="utf-8") as evidence_file:
                for index, complete in enumerate(completes):
                    row = {
                        "schema_version": 1,
                        "experiment": "6-12",
                        "source": "upstream_val_only",
                        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                        "arm": os.environ.get("EXP6_12_ARM"),
                        "upstream_commit": os.environ.get("EXP6_12_UPSTREAM_COMMIT"),
                        "task": self.config.data.task_suite_name,
                        "data_source": str(sources[index]),
                        "trial_id": trial_ids[index],
                        "trial_seed": trial_seeds[index],
                        "success": bool(complete),
                        "finish_action_steps": finish_steps[index],
                        "action_chunk_length": int(self.config.actor_rollout_ref.model.action_chunks_len),
                        "action_dimension": int(self.config.actor_rollout_ref.model.action_token_len),
                        "rgb_views": int(self.config.actor_rollout_ref.rollout.num_images_in_input),
                        "proprioception_enabled": bool(self.config.actor_rollout_ref.rollout.use_proprio),
                    }
                    evidence_file.write(json.dumps(row, ensure_ascii=False) + "\\n")
                evidence_file.flush()
                os.fsync(evidence_file.fileno())
'''

ACTION_PREFIX = '''        # The OpenVLA-OFT checkpoint head is trained to predict 25 actions and
        # always returns that full tensor. For an execution-chunk ablation,
        # the rollout must execute only the configured prefix.
        configured_chunks = int(self.config.action_chunks_len)
        action_dimension = int(self.config.action_token_len)
        if not 1 <= configured_chunks <= actions.shape[1]:
            raise ValueError(
                f"Configured action chunk {configured_chunks} is incompatible "
                f"with model output shape {actions.shape}"
            )
        response_tokens = configured_chunks * action_dimension
        if response.ndim != 2 or response.shape[1] < response_tokens:
            raise ValueError(
                f"Model response shape {tuple(response.shape)} cannot prove "
                f"{configured_chunks} actions x {action_dimension} dimensions"
            )
        actions = actions[:, :configured_chunks, :]
        response = response[:, :response_tokens]
'''


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"{path}: expected exactly one instrumentation anchor")
    path.write_text(text.replace(old, new), encoding="utf-8")


def instrument(upstream: Path) -> None:
    main = upstream / "verl/trainer/main_ppo.py"
    replace_once(main, "import statistics\n", "import statistics\nfrom datetime import datetime, timezone\n")
    anchor = "        reward_format_metrics['all'] = data.batch['acc'].mean().item()\n"
    replace_once(main, anchor, anchor + EPISODE_RECORDER)

    hybrid = upstream / "verl/workers/hybrid_engine/__init__.py"
    replace_once(
        hybrid,
        "# limitations under the License.\n\nfrom verl.utils.import_utils",
        "# limitations under the License.\n\nimport os\n\nfrom verl.utils.import_utils",
    )
    replace_once(
        hybrid,
        "if is_vllm_available():\n",
        'if is_vllm_available() and not os.environ.get("VERL_DISABLE_VLLM_IMPORT"):\n',
    )

    rollout = upstream / "verl/workers/rollout/rob_rollout.py"
    generation_end = "                    temperature=temperature,\n                )\n"
    replace_once(rollout, generation_end, generation_end + ACTION_PREFIX)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream", type=Path)
    args = parser.parse_args()
    instrument(args.upstream.resolve())
    print("Instrumented disposable SimpleVLA-RL worktree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
