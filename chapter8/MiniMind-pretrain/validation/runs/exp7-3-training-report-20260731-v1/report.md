# Experiment 7-3 retained-training-report audit

## Result

Status: **passed**. The historical report retains 49 outputs across the original and QK-Norm + Muon arms after pretrain, SFT, and DPO. Eight preregistered arm-blind comparisons were judged from raw retained text by an independent ARK model.

| Arm | Fluency | Instruction | Factuality | Overall |
| --- | ---: | ---: | ---: | ---: |
| Original | 3.0000 | 1.7500 | 1.3750 | 2.0417 |
| QK-Norm + Muon | 3.7500 | 3.0000 | 4.1250 | 3.6250 |

Observed blind-judge overall delta: **+1.5833**. Pairwise decisions: {'original': 0, 'qk_norm_muon': 7, 'tie': 1}.

The report's loss claims (3.0 reached at 36 versus 12 reported steps; final loss 2.0 versus 1.7) are retained as author-reported observations, not independently recomputed measurements, because the historical stepwise logs were not preserved.

## Provenance and reproduction boundary

`reproduction_contract.json` freezes the MiniMind source revision, hashes the relevant source files, freezes a dataset revision with the three Git-LFS object hashes and sizes, and records all six future reproduction commands. These pins were selected for future reproduction and are not represented as the exact historical checkout.

Training checkpoints remain local by book policy and are not an acceptance artifact. The accepted artifact is this content-hashed training report, its raw retained outputs, raw independent-judge receipts, and explicit limitations.
