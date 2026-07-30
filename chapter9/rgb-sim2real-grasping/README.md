# Experiment 9-10: Zero-Shot RGB Sim2Real Grasping

This directory is an **external reproduction companion** for [`StoneT2000/lerobot-sim2real`](https://github.com/StoneT2000/lerobot-sim2real). The authoritative source and tutorial are locked in [`upstream.lock.json`](upstream.lock.json) to commit [`87d6c1d969f6e0ca4dc5697940804e231118a63a`](https://github.com/StoneT2000/lerobot-sim2real/tree/87d6c1d969f6e0ca4dc5697940804e231118a63a).

Current evidence status: **blocked / incomplete**. No local ManiSkill environment, PPO checkpoint, >90% evaluation, or real deployment exists. A host audit verified upstream inputs and analyzed the pinned real SO-100 system-identification capture, but reference images are not relabeled as local results.

## Five exact manuscript stages

| Stage | Pinned upstream entrypoint | Robot actuation? | Manuscript acceptance gate |
| --- | --- | :---: | --- |
| 1. Environment alignment | `record_reset_distribution.py`; `camera_alignment.py` | **Potentially yes.** The pinned script connects the robot and calls `real_env.reset()`. | Hashed sim config, real frame, overlay, measured alignment error, and full physical safety gate |
| 2. Background replacement | `capture_background_image.py`; `greenscreen_overlay_path` in `env_config.json` | No commanded motion: the pinned script connects the robot and disables torque. Physical robot/camera access is still required. | Hashed empty-scene background, configured JSON, and rendered composite |
| 3. Domain randomization | ManiSkill environment with `domain_randomization=True`; `record_reset_distribution.py` | No | Robot color, object texture, lighting, camera FOV, and calibrated physical ranges; reset-distribution media |
| 4. RGB-only PPO | `train_ppo_rgb.py` | No | RGB-only PPO checkpoint and direct evaluation success rate `>0.90` |
| 5. Zero-shot real deployment | `eval_ppo_rgb.py` | **Yes** | No real fine-tuning, guarded 15 Hz trials, at least one successful grasp, uncut video |

The five-stage track is not wholly “hardware-only”: stages 3–4 can run on a suitable GPU server, while stages 1–2 consume physical real-scene inputs. In the exact pinned implementation, stage 1 can actuate during reset and stage 2 connects hardware but explicitly disables torque. Stage 5 is the actual zero-shot policy deployment. Offline analysis of previously captured stage-1/2 inputs is safe, but it is not the exact live upstream alignment/capture run.

Pinned tutorial: [`zero_shot_rgb_sim2real.md`](https://github.com/StoneT2000/lerobot-sim2real/blob/87d6c1d969f6e0ca4dc5697940804e231118a63a/docs/zero_shot_rgb_sim2real.md), blob `844d113a726d7c3c8494700496591a2604f742e0`.

## Checkout and install

```bash
git clone https://github.com/StoneT2000/lerobot-sim2real.git
cd lerobot-sim2real
git checkout --detach 87d6c1d969f6e0ca4dc5697940804e231118a63a
test "$(git rev-parse HEAD)" = "87d6c1d969f6e0ca4dc5697940804e231118a63a"

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

The pinned setup declares mutable `mani_skill_nightly` rather than a specific build. Record `pip freeze`, GPU model, driver, CUDA, PyTorch, and ManiSkill versions with the run. The upstream tutorial requires an NVIDIA GPU with at least 8 GB VRAM; Apple MPS is not a verified substitute for this pinned CUDA workflow.

## Exact upstream commands

Start from a copied and reviewed `env_config.json`; do not overwrite the pinned source record.

Stage 1—render the spawn distribution, then align the real camera. The second command is hardware-capable: apply the same calibration, authorization, clear-workspace, E-stop, and observer gate used for stage 5 before running it.

```bash
python lerobot_sim2real/scripts/record_reset_distribution.py \
  --env-id SO100GraspCube-v1 \
  --env-kwargs-json-path env_config.json

python lerobot_sim2real/scripts/camera_alignment.py \
  --env-id SO100GraspCube-v1 \
  --env-kwargs-json-path env_config.json
```

Stage 2—capture the empty real background and set `greenscreen_overlay_path` to the resulting file:

```bash
python lerobot_sim2real/scripts/capture_background_image.py \
  --env-id SO100GraspCube-v1 \
  --env-kwargs-json-path env_config.json \
  --out greenscreen.png
```

Run alignment again after configuring the greenscreen to verify the composite.

Stage 3—configure measured randomization ranges, including the manuscript's visual categories and physical parameters, then regenerate randomized resets. The pinned `system_id_so100.npy` is a real upstream dynamics capture; it does not by itself prove that the local training ranges were calibrated.

Stage 4—use the tutorial's RGB PPO configuration:

```bash
seed=3
python lerobot_sim2real/scripts/train_ppo_rgb.py \
  --env-id SO100GraspCube-v1 \
  --env-kwargs-json-path env_config.json \
  --ppo.seed="$seed" \
  --ppo.num_envs=1024 \
  --ppo.num-steps=16 \
  --ppo.update_epochs=8 \
  --ppo.num_minibatches=32 \
  --ppo.total_timesteps=100_000_000 \
  --ppo.gamma=0.9 \
  --ppo.num_eval_envs=16 \
  --ppo.num-eval-steps=64 \
  --ppo.no-partial-reset \
  --ppo.exp-name="ppo-SO100GraspCube-v1-rgb-${seed}" \
  --ppo.track \
  --ppo.wandb_project_name SO100-ManiSkill
```

Do not advance to stage 5 until direct evaluation exceeds `0.90` and the exact checkpoint and metrics are hashed.

Stage 5—physical deployment, only with explicit authority and the upstream's safer first-run controls:

```bash
python lerobot_sim2real/scripts/eval_ppo_rgb.py \
  --env_id SO100GraspCube-v1 \
  --env-kwargs-json-path env_config.json \
  --checkpoint /path/to/ckpt.pt \
  --no-continuous-eval \
  --control-freq 15
```

The operator must verify motor calibration, cube/spawn bounds, a clear workspace, E-stop or torque-disable path, and a human observer. Remain ready to press Ctrl-C. Never remove `--no-continuous-eval` for the first acceptance run.

## Host audit versus acceptance evidence

[`pipeline.py`](pipeline.py) is deliberately an **audit/blocker recorder**, not a substitute simulator. It verifies pinned blobs, inspects upstream reference media, analyzes a hash-verified `system_id_so100.npy`, and records exact import/resource failures. Its output cannot satisfy [`evidence.schema.json`](evidence.schema.json).

The current audit is [`validation/host_execution_2026-07-29.json`](validation/host_execution_2026-07-29.json). It records:

- source-integrity pass at the pinned commit;
- upstream alignment and greenscreen images verified only as reference assets;
- 139×6 upstream real-dynamics samples analyzed, with lag reported only in samples because timestamps are absent;
- no importable ManiSkill, no NVIDIA runtime, no RGB PPO checkpoint, and no measured simulation success rate;
- `actuation_attempted: false`.

Run a stage-aware non-actuating preflight with:

```bash
python preflight.py \
  --upstream /path/to/lerobot-sim2real \
  --camera /dev/video0 \
  --robot-port /dev/ttyACM0 \
  --real-frame /path/to/real-frame.png \
  --greenscreen /path/to/greenscreen.png \
  --checkpoint /path/to/ckpt.pt \
  --hardware-run-authorized \
  --safety-checklist-complete
```

## Completion gate

```bash
python validate_evidence.py evidence/run.json
```

Completion requires all five stages, real inputs and local hashes, explicit randomization categories and real calibration measurements, RGB-only PPO with direct simulation success `>0.90`, a zero-shot stage-5 run with no fine-tuning, first-run step confirmation at 15 Hz, calibrated safety state, at least one successful physical grasp, and locally present hash-matching artifacts from every stage. Upstream screenshots, tutorial curves/video, source inspection, schema examples, and blocker audits cannot pass.
