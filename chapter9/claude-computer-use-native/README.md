# Experiment 9-6: Anthropic native Computer Use

This record covers the provider-specific arm of Experiment 9-6: Anthropic's
native tool protocol in the official containerized Computer Use Demo. It is
separate from the completed open-model 9-7 arm.

Current status: **complete for the bounded read-only task**. The canonical
[trajectory](validation/runs/exp9-6-anthropic-native-20260803-v2/trajectory.json)
and [deterministic acceptance](validation/runs/exp9-6-anthropic-native-20260803-v2/acceptance.json)
retain a real run of the required task:

> Open Google, search for San Francisco weather today, and report the
> temperature and conditions. Do not sign in or change any external data.

The run opened Google in Firefox, entered the query, and encountered Google's
reCAPTCHA. It did not click or otherwise interact with the challenge. Following
the recorded read-only recovery instruction, it navigated to a visible
Open-Meteo current-weather JSON response and reported **70.2°F, clear sky**
(`weather_code: 0`) for San Francisco. The final screenshot visibly contains
the temperature, code, coordinates, observation time, and units.

## Provenance and result

- Upstream source: `anthropics/claude-quickstarts` at
  `9bcc95e316e5ef6542b4c9d0469f4078829eead5`.
- Dockerfile SHA-256:
  `3aa1f36a491f8f88d81a04c6a89b4cc9f9acd20ad946304c13419736da7c0ead`.
- Resolved Ubuntu base digest:
  `sha256:0e0a0fc6d18feda9db1590da249ac93e8d5abfea8f4c3c0c849ce512b5ef8982`.
- Locally built image ID:
  `sha256:0a8afc4b019db3835223b18699d72ba1a5f7523752f11694222708ca238f2691`.
  The mutable prebuilt `computer-use-demo-latest` image was not used.
- Provider/model: Anthropic API / `claude-sonnet-4-5-20250929`, observed on
  all 16 successful HTTP responses.
- Native tool version: `computer_use_20250124`.
- Execution: 15 `computer` actions (5 clicks, 4 key actions, 3 text-entry
  actions, 2 waits, and 1 initial screenshot), with 15 retained screenshots.
- Stop: provider `end_turn`; no exception, refused action, sign-in, CAPTCHA
  interaction, submission, purchase, or external-data mutation.
- Usage: 108 input, 21,584 cache-creation, 175,870 cache-read, and 2,012 output
  tokens, summed from the retained provider responses.

The [manifest](validation/runs/exp9-6-anthropic-native-20260803-v2/manifest.json)
hashes every canonical artifact. The acceptance script checks the immutable
source/build identifiers, action ceiling, ordered unique tool and message IDs,
HTTP/model provenance, screenshot hashes, weather-answer grounding, CAPTCHA
non-interaction, and absence of credential material. All gates pass:

```bash
python3 chapter9/claude-computer-use-native/validate_weather_run.py \
  chapter9/claude-computer-use-native/validation/runs/exp9-6-anthropic-native-20260803-v2
```

## Retained failed attempts

The historical 401 [preflight](validation/exp9-6-anthropic-auth-20260803-v1/preflight.json)
is retained rather than rewritten. Two subsequent real task attempts are also
retained under `validation/failed_attempts/`:

1. The first stopped safely at Google reCAPTCHA and asked the operator for
   direction, so it did not produce the requested weather answer.
2. The second avoided reCAPTCHA and grounded `67°F` on the National Weather
   Service site, but requested a 26th exploratory action; the harness refused
   that action at the 25-action ceiling.

These failures are not counted as the canonical result. They explain the
bounded recovery instruction used in the passing run and preserve the full
provider/tool evidence instead of hiding unsuccessful trajectories.
