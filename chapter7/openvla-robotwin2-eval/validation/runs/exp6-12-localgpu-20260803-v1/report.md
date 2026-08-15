# Experiment 6-12 OpenVLA + RoboTwin2 evaluation

Official completion: **True**

| Arm | Episodes | Success rate | IID | OOD | Completion p50 / p95 (50 Hz seconds) |
| --- | ---: | ---: | ---: | ---: | ---: |
| chunk_1 | 256 | 0.0 | 0.0 | 0.0 | 4.0 / 4.0 |
| chunk_25 | 256 | 0.1015625 | 0.1015625 | 0.1015625 | 4.0 / 4.0 |

## Controlled comparison

```json
{
  "complete_pairs": 256,
  "chunk_25_wins": 26,
  "chunk_1_wins": 0,
  "ties": 230,
  "mean_paired_success_delta": 0.1015625,
  "unpaired_rows": 0
}
```

## Failure modes

- chunk_1: {"timeout": 256}
- chunk_25: {"timeout": 230}

## Completion audit

- Every direct manuscript gate is supported by real per-episode evidence.
