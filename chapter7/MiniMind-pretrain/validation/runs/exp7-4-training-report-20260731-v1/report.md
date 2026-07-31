# Experiment 7-4 retained-training-report audit

## Result

Status: **passed**. The historical report retains 64 image descriptions across 8 configurations and the same 8 images. Each image was inspected by a real image-capable ARK judge together with all eight arm-blind captions.

| Configuration | Grounding | Hallucination control | Coverage | Specificity | Overall | Best count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| without_muon_sft | 2.1250 | 1.3750 | 2.3750 | 1.7500 | 1.9062 | 1 |
| without_muon_pretrained | 1.8750 | 2.6250 | 1.5000 | 0.8750 | 1.7188 | 1 |
| muon_from_dpo_sft | 1.3750 | 1.1250 | 1.8750 | 1.7500 | 1.5312 | 2 |
| muon_from_sft_pretrained | 1.8750 | 2.0000 | 1.3750 | 0.8750 | 1.5312 | 2 |
| muon_from_sft_sft | 1.2500 | 1.1250 | 1.5000 | 1.2500 | 1.2812 | 1 |
| muon_from_pretrain_sft | 1.1250 | 0.5000 | 1.3750 | 1.1250 | 1.0312 | 0 |
| muon_from_dpo_pretrained | 1.0000 | 1.5000 | 0.8750 | 0.3750 | 0.9375 | 0 |
| muon_from_pretrain_pretrained | 0.7500 | 1.3750 | 0.7500 | 0.6250 | 0.8750 | 1 |

The highest descriptive judge mean was **without_muon_sft** at **1.9062**. Averaged across all four base configurations, full VLM SFT changed the score by **+0.1718** versus projection-only pretraining.

The isolated report comparison pairs original/SFT-base against QK-Norm+Muon/SFT-base at each VLM stage. QK-Norm and Muon still change together, so no Muon-only causal claim is made. All author-written qualitative claims remain historical observations rather than pass/fail gates.

## Provenance and reproduction boundary

`reproduction_contract.json` freezes separate pre-QK-Norm and QK-Norm+Muon MiniMind-V revisions, the corresponding base-LLM revisions, script-compatible VLM dataset Git-LFS objects, the CLIP weight object, all eight evaluation-image hashes, and future commands. These pins are not misrepresented as the historical checkout.

Training checkpoints remain local by book policy and are not acceptance artifacts. The accepted artifact is this content-hashed report, all 64 retained outputs, eight raw image-aware judge receipts, and explicit limitations.
