# Experiment 9-9: Gemini Robotics-ER 1.5 XLeRobot Navigation

This is an **external reproduction companion** for XLeRobot + RoboCrew. The authoritative guide is pinned in [`upstream.lock.json`](upstream.lock.json) to XLeRobot commit [`3d14695e40c9c68229c0aacffca6053c75cd3eb6`](https://github.com/Vector-Wangel/XLeRobot/tree/3d14695e40c9c68229c0aacffca6053c75cd3eb6). The companion adds the manuscript's exact model and evidence gates; it does not replace RoboCrew.

Current evidence status: **blocked / incomplete**. A real non-actuating exact-model lookup was attempted with the official SDK and the frame referenced by the pinned XLeRobot guide, but Google rejected the configured `GEMINI_API_KEY` as invalid before model availability could be confirmed. No robot navigation occurred.

## Exact manuscript-to-upstream mapping

| Book requirement | Exact configuration/source | Acceptance evidence |
| --- | --- | --- |
| RoboCrew long-horizon planner | [`LLM_agent.md`](https://github.com/Vector-Wangel/XLeRobot/blob/3d14695e40c9c68229c0aacffca6053c75cd3eb6/docs/en/source/software/getting_started/LLM_agent.md), blob `d336a9e35838267614d31cdb98b9b50d66427f03`; RoboCrew `v0.3.1` commit `c749148f29bd14e61347f9fc3530c343fff0d994`; PyPI wheel SHA-256 `4afbc8ab19ffb61cc0617486408460c80072991434636aff041a1ef87f2abb4f` | Runtime version, direct receipt, raw planner log |
| Gemini Robotics-ER 1.5 | Model ID `gemini-robotics-er-1.5-preview` | Successful API response identifying the exact model |
| Angular scale on camera image | `camera_fov=90` in the RoboCrew runner; saved-frame tool writes a visibly annotated input | Hashed annotated frames from the run |
| Only forward, left, right | `create_move_forward`, `create_turn_left`, `create_turn_right` | Planner log contains no other motion tool |
| “find the kitchen and go there” | Exact task string in [`navigation.py`](navigation.py) | Timestamped decisions and arrival rule |
| 0.5–1 Hz decisions | Measure intervals between planner responses/tool calls | Hashed timing artifact with measured frequency in range |
| Visual semantic reasoning | Record corridor, door, furniture, and kitchen-specific cues | Frame hashes plus concise reasoning summaries |
| Optional wake-word control | RoboCrew `wakeword` mode from the pinned guide | Optional; not required for base completion |

The public [ReadTheDocs page](https://xlerobot.readthedocs.io/en/latest/software/getting_started/LLM_agent.html) is mutable. The pinned page currently demonstrates `gemini-3-flash-preview`; that is **not** the book's Gemini Robotics-ER 1.5. The completion validator rejects the generic model.

## Checkout and preflight

```bash
git clone https://github.com/Vector-Wangel/XLeRobot.git
cd XLeRobot
git checkout --detach 3d14695e40c9c68229c0aacffca6053c75cd3eb6
test "$(git rev-parse HEAD)" = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"

cd ..
git clone https://github.com/Grigorij-Dudnik/RoboCrew.git
git -C RoboCrew fetch origin c749148f29bd14e61347f9fc3530c343fff0d994
git -C RoboCrew checkout --detach c749148f29bd14e61347f9fc3530c343fff0d994
git -C RoboCrew rev-parse HEAD
test "$(git -C RoboCrew rev-parse HEAD)" = "c749148f29bd14e61347f9fc3530c343fff0d994"

python -m pip install \
  'https://files.pythonhosted.org/packages/29/8d/893d6d5cfe8a8e5aac943936ee497934533d882cfd933f609a12a66101c2/robocrew-0.3.1-py3-none-any.whl#sha256=4afbc8ab19ffb61cc0617486408460c80072991434636aff041a1ef87f2abb4f'
export GOOGLE_API_KEY='...'

python /path/to/ai-agent-book/chapter9/gemini-xlerobot-navigation/preflight.py \
  --upstream /path/to/XLeRobot \
  --camera /dev/camera_center \
  --serial-port /dev/arm_right \
  --api-validation /path/to/reference_api/gemini_robotics_er_1_5.json \
  --safety-checklist-complete \
  --output /path/to/preflight.json
```

The Git tag, source commit, `pyproject.toml` blob, PyPI wheel URL, wheel hash, exact model ID, and required navigation key name are recorded together in the lock; the earlier unrelated RoboCrew default-branch commit reported package version `0.3.0` and is intentionally no longer used. The locked navigation key name is `GOOGLE_API_KEY`, matching the guarded physical runner. `plan_saved_frame.py` and the preflight also accept `GEMINI_API_KEY` only for compatibility with the historical non-actuating record. Model availability and access must be confirmed by a real response; possession of an API key is not evidence by itself.

## Safe saved-frame API check

[`plan_saved_frame.py`](plan_saved_frame.py) adds a 90-degree angular scale to an existing RGB frame (or preserves a pinned upstream frame that already has one), declares exactly the three manuscript tools to Gemini Robotics-ER, and saves the model lookup, SDK/model version, timing, raw response/provider error, token usage, and cost status. It accepts `GEMINI_API_KEY` or `GOOGLE_API_KEY`, never prints the credential, never opens a camera, and never executes a returned tool:

```bash
python plan_saved_frame.py \
  --image validation/reference_inputs/xlerobot_llm_guide_frame.jpg \
  --annotated-image validation/reference_api/xlerobot_llm_guide_frame_used.jpg \
  --already-annotated \
  --input-source-url https://github.com/user-attachments/assets/296f6f60-52a4-4fa0-9a77-a113b4868f83 \
  --input-source-commit 3d14695e40c9c68229c0aacffca6053c75cd3eb6 \
  --output validation/reference_api/gemini_robotics_er_1_5_2026-07-29.json
```

If credentials or model access are absent, it writes an honest blocker record. A successful saved-frame plan proves only API/model/tool wiring—not autonomous navigation.

### Current reference-input API validation

- Input: [`validation/reference_inputs/xlerobot_llm_guide_frame.jpg`](validation/reference_inputs/xlerobot_llm_guide_frame.jpg), downloaded from the image URL embedded in the pinned guide; SHA-256 `2dae44dd2dbd9259f9448095f09e064ade50d485e8d0dcab7a3ca2a73435bcc1`.
- Record: [`validation/reference_api/gemini_robotics_er_1_5_2026-07-29.json`](validation/reference_api/gemini_robotics_er_1_5_2026-07-29.json), SHA-256 `31225c7339b189ad4c4e846fc341c84c50375556167b4d1a0f571c16b5caf93f`.
- Requested model: exactly `gemini-robotics-er-1.5-preview`; no fallback.
- SDK: `google-genai 1.56.0`; API-key alias: `GEMINI_API_KEY` (name only; the value is not stored).
- Result: `400 INVALID_ARGUMENT`, reason `API_KEY_INVALID`, after `2511.956 ms`. The failure occurred during exact-model lookup, so model availability remains unconfirmed.
- Token usage and cost: `null`, because authentication failed before a response was generated.
- Scope: upstream-reference-input API validation only. It is explicitly not real-camera or navigation acceptance evidence.

## Guarded physical run

Dry configuration:

```bash
python navigation.py
```

Physical execution is permitted only after all safeguards are real:

```bash
python navigation.py \
  --camera /dev/camera_center \
  --right-arm-wheel-usb /dev/arm_right \
  --execute \
  --authorization-token I_AUTHORIZE_XLEROBOT_MOTION \
  --operator operator-id \
  --robot-calibrated \
  --clear-route \
  --emergency-stop-ready \
  --human-observer-present \
  --receipt evidence/navigation-receipt.json
```

The runner runtime-checks `robocrew==0.3.1`, uses `google_genai:gemini-robotics-er-1.5-preview`, creates exactly the three movement tools, and calls RoboCrew's `agent.go()`. It does not claim success when the agent loop merely returns; arrival, timing, semantic cues, and safety still need direct artifacts.

## Completion gate

Validate a run against [`evidence.schema.json`](evidence.schema.json):

```bash
python validate_evidence.py evidence/run.json
```

Completion requires a locally present, hash-matching navigation receipt, successful exact-model API calls, an angularly annotated real-camera run, exactly three navigation tools, measured 0.5–1 Hz frequency, at least three timestamped decisions, kitchen-specific cues, successful arrival, and hashed video/planner/timing artifacts. Saved-frame planning, mocks, dry configurations, and upstream demo videos are insufficient.

Current blockers: `robocrew==0.3.1` absent, the historically configured `GEMINI_API_KEY` rejected by the provider, exact preview-model availability unconfirmed, `/dev/camera_center` absent, `/dev/arm_right` absent, and no safety attestation. The reference-input call record has `api_call_attempted: true` and `actuation_attempted: false`; the hardware preflight itself makes no API call.
