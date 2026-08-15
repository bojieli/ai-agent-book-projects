# Experiment 7-6: speech SFT acceptance campaign

This directory contains the reproducible local-GPU campaign and its retained
evidence for both speech-training tracks described in the chapter:

- Orpheus cross-sentence voice/timbre consistency
- Sesame CSM control of `<laughs>`, `<giggles>`, and `<sighs>` events

The retained run is `validation/exp7-6-20260804-v1/`. It performed 60 optimizer
updates for each LoRA, used disjoint held-out loss sets, generated matched
base/adapted WAV comparisons, published the full adapters to Hugging Face, and
kept explicit negative comparisons. See the run's `REPORT.md` for results and
limitations.

The retained `compatibility_failures.json` also records the current Unsloth CSM
pad-token rejection and Transformers bf16 codec/text merge mismatch. Sesame was
therefore trained with standard PEFT in float32, without reducing the dataset,
optimizer-step count, or comparison campaign.

## Reproduce

Use a fresh environment because the two upstream notebooks move quickly:

```bash
python3 -m venv --system-site-packages .venv-exp7-6
.venv-exp7-6/bin/pip install -r chapter7/speech-sft-experiment/requirements.txt

.venv-exp7-6/bin/python chapter7/speech-sft-experiment/run_orpheus.py \
  --output chapter7/speech-sft-experiment/validation/my-run

.venv-exp7-6/bin/python chapter7/speech-sft-experiment/run_sesame.py \
  --output chapter7/speech-sft-experiment/validation/my-run

.venv-exp7-6/bin/python chapter7/speech-sft-experiment/analyze_campaign.py \
  --run chapter7/speech-sft-experiment/validation/my-run
```

The runners default to `bojieli/...` adapter repositories. Pass `--hf-repo`
with a repository you can write, or modify the runners to skip publication for
a private local reproduction. `HF_TOKEN` is required for publication.

## Dataset provenance

The upstream notebooks name `MrDragonFox/Elise`. Hugging Face now marks that
dataset disabled. The campaign therefore uses
`maxbsoft/mrdragonfox-elise` at immutable revision
`2cc657c3f94a83df18fcd968b7531ca1a19c7f88`, a public non-disabled mirror of
the 1,195-row Elise corpus. Both manifests record this substitution.

## Interpretation

Execution acceptance and hypothesis support are separate. A run can be
complete while an automatic quality proxy is negative. The MFCC statistic
cosine used for Orpheus is a transparent timbre proxy. The AudioSet detector
scores used for Sesame are event-presence proxies. Neither replaces a blinded
human listening test, MOS, or enrolled-speaker verification, and the report
does not claim perceptual quality from this bounded campaign.
