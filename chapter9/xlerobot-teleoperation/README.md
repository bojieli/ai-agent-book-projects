# Experiment 9-8: XLeRobot Teleoperation

This directory is an **external reproduction companion**, not a local reimplementation and not evidence that a robot was operated. The authoritative implementation is XLeRobot. The source is locked in [`upstream.lock.json`](upstream.lock.json) to commit [`3d14695e40c9c68229c0aacffca6053c75cd3eb6`](https://github.com/Vector-Wangel/XLeRobot/tree/3d14695e40c9c68229c0aacffca6053c75cd3eb6).

Current evidence status: **blocked / incomplete**. Source integrity and a non-actuating preflight were verified on 2026-07-29, but no physical teleoperation mode or book task was executed.

## Exact manuscript-to-upstream mapping

| Book requirement | Pinned authoritative source | Acceptance evidence |
| --- | --- | --- |
| Keyboard teleoperation | [`4_xlerobot_teleop_keyboard.py`](https://github.com/Vector-Wangel/XLeRobot/blob/3d14695e40c9c68229c0aacffca6053c75cd3eb6/software/examples/4_xlerobot_teleop_keyboard.py), blob `efbe076dfbda3c6280fa54f0eb5bca1a12518a0d` | Direct launcher receipt, video, latency, precision, and quality measurements |
| Xbox controller | [`5_xlerobot_teleop_xbox.py`](https://github.com/Vector-Wangel/XLeRobot/blob/3d14695e40c9c68229c0aacffca6053c75cd3eb6/software/examples/5_xlerobot_teleop_xbox.py), blob `de7bc17d570167e58b15e38c06c0fa23af74632a` | Same |
| Switch Joy-Con | [`7_xlerobot_teleop_joycon.py`](https://github.com/Vector-Wangel/XLeRobot/blob/3d14695e40c9c68229c0aacffca6053c75cd3eb6/software/examples/7_xlerobot_teleop_joycon.py), blob `21a48258d22b1fc002f63555a2f3dc2950bdfb24` | Same |
| VR headset | [`8_xlerobot_teleop_vr.py`](https://github.com/Vector-Wangel/XLeRobot/blob/3d14695e40c9c68229c0aacffca6053c75cd3eb6/software/examples/8_xlerobot_teleop_vr.py), blob `315bb81f13a37746de0f329e3ba11240a2230806` | Same; treat as experimental until a real run succeeds |
| Pick, place, and wipe | Operator performs all three tasks across the campaign | Attempts, successes, success definitions, and uncut media |
| Observe latency, precision, and completion quality | Companion evidence schema | Per-mode latency samples, positional-error measurements, 1–5 quality score |

Pinned guide: [`XLeRobot_teleop.md`](https://github.com/Vector-Wangel/XLeRobot/blob/3d14695e40c9c68229c0aacffca6053c75cd3eb6/docs/en/source/software/getting_started/XLeRobot_teleop.md), blob `3992358282ff54cfce8d90a525e784aedcf045f7`. The public [ReadTheDocs page](https://xlerobot.readthedocs.io/en/latest/software/getting_started/XLeRobot_teleop.html) is useful for browsing but is mutable.

The pinned guide still says official real-robot VR code is “coming soon,” while the pinned repository contains a VR entrypoint. This companion records both facts and does not promote source presence to successful VR acceptance.

## Checkout and verify

```bash
git clone https://github.com/Vector-Wangel/XLeRobot.git
cd XLeRobot
git checkout --detach 3d14695e40c9c68229c0aacffca6053c75cd3eb6
test "$(git rev-parse HEAD)" = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"

python /path/to/ai-agent-book/chapter9/xlerobot-teleoperation/preflight.py \
  --upstream "$PWD" \
  --serial-port /dev/ttyACM0 \
  --serial-port /dev/ttyACM1 \
  --safety-checklist-complete \
  --output /path/to/preflight.json
```

The upstream [software installation page at the pinned commit](https://github.com/Vector-Wangel/XLeRobot/blob/3d14695e40c9c68229c0aacffca6053c75cd3eb6/docs/en/source/software/getting_started/install.md) requires an editable LeRobot installation and moving XLeRobot's robot, kinematics, and examples into that checkout. It does not pin a LeRobot revision, so record the LeRobot commit in the run notes; this is an upstream reproducibility limitation.

Joy-Con additionally requires the upstream `joycon-robotics` installation described in the guide. VR requires the pinned XLeRobot VR support and headset setup. Verify each controller without torque before moving the robot.

## Guarded execution

Dry configuration—safe and non-actuating:

```bash
python teleop.py --upstream /path/to/XLeRobot --mode keyboard
```

The four authoritative modes are selected with `--mode keyboard`, `xbox`, `joycon`, or `vr`. A physical run is intentionally verbose and fail-closed:

```bash
python teleop.py \
  --upstream /path/to/XLeRobot \
  --mode keyboard \
  --execute \
  --authorization-token I_AUTHORIZE_XLEROBOT_TELEOPERATION \
  --operator operator-id \
  --robot-calibrated \
  --clear-workspace \
  --emergency-stop-ready \
  --human-observer-present \
  --receipt evidence/keyboard/receipt.json
```

This launches the pinned upstream file; it does not reproduce its control logic locally. Repeat separately for every mode. Record controller-input and observed-motion timestamps with an external synchronized camera/logger, measure positional error against fixed targets, and preserve uncut task video. A process receipt alone is not task evidence.

## Safety boundary

Do not use `--execute` unless the operator has explicit authority, the motors and zero positions are calibrated, the robot is secured in a clear workspace, an E-stop or immediate torque-disable path is ready, and a second human observer is present. Begin at low speed with no fragile objects or people in reach. The operator remains responsible for the physical system.

## Evidence and completion gate

Create evidence conforming to [`evidence.schema.json`](evidence.schema.json), then run:

```bash
python validate_evidence.py evidence/run.json
```

`complete` requires all four modes, all three task categories, real latency/precision/quality measurements, hashed receipts from `teleop.py`, and locally present hashed video and measurement artifacts. Mocks, simulation, upstream demo videos, dry runs, and [`evidence.blocked.example.json`](evidence.blocked.example.json) cannot pass the completion branch.

Current blockers from the saved 2026-07-29 host preflight are: no importable `lerobot`, no importable `joyconrobotics`, no serial devices supplied, and no safety attestation. `actuation_attempted` was `false`.
