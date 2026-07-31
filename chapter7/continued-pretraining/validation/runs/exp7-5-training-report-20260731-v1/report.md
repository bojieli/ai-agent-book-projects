# Experiment 7-5 retained-training-report audit

## Result

Status: **passed**. The historical RTX 4090 report contains all five prompts across the baseline, continued-pretrained, and instruction-tuned stages. An independent stage-blind ARK judge scored the exact 15 retained outputs.

| Stage | Korean mean (0-5) | English mean (0-5) |
| --- | ---: | ---: |
| baseline | 1.6667 | 5.0000 |
| pretrained | 1.3333 | 3.1667 |
| finetuned | 3.4444 | 4.1667 |

Observed Korean gain, final minus baseline: **+1.7777**.
Observed English drop, baseline minus final: **+0.8333** (declared tolerance: 1.0).
The final English score is within the declared tolerance.

## Material negative result

The final model's Korean is more fluent, but the kimchi answer remains factually unsafe. The blind judge identified: 채소를 삶는다는 잘못된 설명 (전통 김치는 채소를 소금에 절이는 과정을 거침); 간장 소스로 설명하는 잘못 (김치 양념은 간장이 아닌 고추가루, 젓갈 등으로 만듦)

## Provenance boundary

The raw terminal report records the historical GPU/software identity and generated text, but not adapter hashes, the exact resolved upstream commits, or the sampling seed. The immutable Hugging Face revisions in `reproduction_contract.json` were selected on 2026-07-31 for future reproduction and are not represented as the historical revisions.

Checkpoints are intentionally local and are not an acceptance artifact. The accepted book artifact is this reproducible, evidence-backed training report.
