# Experiment 7-6 — checkpoint-free voice-SFT training report

This companion closes the training-report portion of Experiment 7-6 without
redistributing model checkpoints. It retains immutable executed upstream
Unsloth notebooks, their complete training logs and embedded audio, two real
direct-audio judge calls, exact source/model/data pins, and explicit provenance
limits. It does not reconstruct missing author-local adapters or claim a causal
training improvement that the retained artifacts cannot establish.

## Retained result

The canonical run is
[`exp7-6-training-report-20260731-v1`](validation/runs/exp7-6-training-report-20260731-v1/):

- 358 step-level loss rows: 298 Orpheus and 60 Sesame;
- four exact notebook-embedded WAV files: one Orpheus and three Sesame;
- two real Mistral `voxtral-small-latest` direct-audio calls, with raw
  credential-free requests/responses, response IDs, usage, and latency;
- immutable upstream notebook commit and Git-blob identities;
- exact model, dataset, codec, weight-object, local-source, and requirements
  hashes; and
- the failed first source-audit attempt, retained rather than overwritten.

| Track | Steps | First loss | Final loss | First-20 mean | Last-20 mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| Orpheus | 298 | 5.1138 | 4.4980 | 4.834855 | 4.418115 |
| Sesame | 60 | 4.8070 | 4.7306 | 5.037375 | 4.806100 |

The Orpheus sample received transcript accuracy 5/5 and naturalness 4/5;
the audio judge heard laughter with confidence 0.95. For Sesame's same-text
B/C pair, the judge assigned voice similarity 5/5 and style similarity 5/5.
These are descriptive observations from one deterministic call per track, not
a powered human-listening study.

## Negative result: the manuscript labels are reversed

The executable sources do not support the manuscript's original mapping of
Orpheus to reference-audio cross-sentence consistency and Sesame to
paralinguistic control tags:

- Orpheus serializes SNAC audio tokens and demonstrates textual `<giggle>`,
  `<giggles>`, and `<laugh>` controls. The retained inference path does not
  accept raw reference audio.
- Sesame passes prior audio through CSM conversation context for speaker/style
  conditioning. Its retained training and inference sources do not define a
  `<laugh>`/`<sigh>` control-tag protocol.

Only one Orpheus WAV is retained, so cross-sentence voice consistency cannot be
measured. The three Sesame prompts are untagged, so paralinguistic-tag
controllability cannot be measured. The notebook audio is post-training output
without matched pre-training controls, so no causal SFT gain is claimed.

## Provenance and checkpoint policy

The retained GPU executions are public upstream reference notebooks at
Unsloth commit `154735d14755eaec2cc21b46f743db8f7910d43a`, not reconstructed
author-local runs. Historical author-local adapter, seed, and output identities
were not retained. Model checkpoints remain intentionally undistributed and
are not acceptance artifacts; the report instead freezes the available raw
outputs, loss traces, evaluation receipts, immutable future-reproduction
contract, and all known limits.

## Validate or reproduce

The canonical package validates without a provider credential:

```bash
uv run --frozen python chapter7/voice-sft-training-report/validate_evidence.py
uv run --frozen pytest -q chapter7/voice-sft-training-report/test_training_report_audit.py
```

To produce a new run, configure `MISTRAL_API_KEY` and choose a new run ID. The
runner refuses to overwrite an existing run:

```bash
uv run --frozen python \
  chapter7/voice-sft-training-report/run_training_report_audit.py \
  --run-id exp7-6-training-report-YYYYMMDD-v2
```

`--refresh-manifest` is an offline maintenance operation for the retained
canonical run. It recomputes the source audit, derived report, manifest, and
latest pointer from the already-retained notebooks, WAVs, and raw judge
receipts; it makes no provider call.
