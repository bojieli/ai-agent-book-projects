# Experiment 7-10: AdaptThink training report

This report records the historical AdaptThink 1.5B, δ=0.05 training run used by
the book. It is a training report, not a fresh local reproduction. In accordance
with the book's distribution policy, model checkpoints are not distributed.

## Public runs

- Main training run: [`wubbn5tj`](https://wandb.ai/bojieli-pine-ai/adapt_think_verl/runs/wubbn5tj)
- Baseline-only run: [`dblyx7cm`](https://wandb.ai/bojieli-pine-ai/adapt_think_verl/runs/dblyx7cm)
- W&B project: [`bojieli-pine-ai/adapt_think_verl`](https://wandb.ai/bojieli-pine-ai/adapt_think_verl)

The main run contains 411 training-history rows for steps 0–410 and 42
validation rows at step 0 and every 10 steps through step 410. The baseline run
contains the same step-0 validation metrics as the main run.

## Training configuration

| Item | Recorded value |
| --- | --- |
| Base model | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` |
| Historical source commit | `9e588202ff56fe93cdbe49f5594cf895f7d6b7c2` |
| Hardware | 8 × NVIDIA H100 80GB HBM3 |
| Runtime environment | CUDA 12.6, Python 3.13.7 |
| Training data | DeepScaler |
| Batch size | 128 |
| Rollouts per prompt | 16 |
| Prompt / response limit | 1,024 / 16,384 tokens |
| NoThinking response limit | 4,096 tokens |
| Learning rate | `2e-6` |
| NoThinking bonus δ | 0.05 |
| Save / validation interval | Every 10 steps |
| Configured schedule | 10 epochs, 3,140 optimizer steps |
| Selected report point | Step 300, approximately 28.37 hours |
| Last retained point | Step 410, approximately 36.92 hours |
| Final W&B state | `crashed` |

The run therefore did not finish its configured ten-epoch schedule. The crash
occurred after the selected step-300 report point.

## Step-300 result

The book uses step 300 as the comparison point. Accuracy and response length are
the aggregate validation metrics logged by the main W&B run.

| Dataset | Accuracy, step 0 | Accuracy, step 300 | Change | Mean response length, step 0 | Mean response length, step 300 | Reduction | NoThinking at step 300 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GSM8K | 0.79681577 | 0.81880212 | +2.1986 pp | 1,025.2350 | 477.3275 | 53.44% | 84.15% |
| MATH500 | 0.81000000 | 0.81800000 | +0.8000 pp | 4,911.4600 | 1,576.6220 | 67.90% | 83.80% |
| AIME2024 mean@16 | 0.31458333 | 0.31041667 | -0.4167 pp | 12,119.5063 | 6,402.2271 | 47.17% | 56.25% |

Mean response length fell substantially on all three datasets. Accuracy improved
on GSM8K and MATH500 but declined slightly on AIME2024, so this run does not
support a claim of uniform accuracy improvement.

### Conditional step-300 aggregates

| Dataset | NoThinking accuracy | Thinking accuracy | NoThinking response length | Thinking response length |
| --- | ---: | ---: | ---: | ---: |
| GSM8K | 0.81621622 | 0.83253589 | 359.6414 | 1,102.3589 |
| MATH500 | 0.82338902 | 0.79012346 | 1,089.7446 | 4,095.1605 |
| AIME2024 mean@16 | 0.28680561 | 0.40963620 | 4,392.5965 | 8,927.4171 |

The lower NoThinking rate on AIME2024 is consistent with difficulty-sensitive
routing at the dataset level. Aggregate metrics do not prove that the model chose
the correct mode for every individual problem.

## Later retained telemetry

Step 410 is shown separately because it is not the book's selected checkpoint.

| Dataset | Accuracy at step 410 | Mean response length | NoThinking ratio |
| --- | ---: | ---: | ---: |
| GSM8K | 0.818044 | 464.56 | 82.03% |
| MATH500 | 0.852000 | 1,481.91 | 74.80% |
| AIME2024 mean@16 | 0.318750 | 5,873.74 | 49.79% |

## Evaluation protocol represented by the logs

- Maximum response length: 16,384 tokens.
- Sampling temperature: 0.6; top-p: 0.95.
- GSM8K and MATH500 use one sampled response per problem.
- AIME2024 uses 16 sampled responses per problem and reports mean@16.
- Answers are graded using the project's boxed-answer rule-based grader.

These are in-training validation metrics. They are not results from a separately
retained post-conversion evaluation run.

## Checkpoint and provenance boundary

The step-300 history includes a checkpoint-save timing event, but the checkpoint
is not distributed with the book. There is also no public receipt showing that
this historical checkpoint was converted and evaluated by `run_eval_verl_hf.sh`,
and no retained MMLU rerun.

The W&B main run records source commit
`9e588202ff56fe93cdbe49f5594cf895f7d6b7c2`. The repository's future
reproduction instructions pin its direct child
`0033ad172dd53ac64004b763477407014f21b838`; the preprocessing, training, and
evaluation entrypoints are unchanged between those commits.

One manual correction is required for a future train-to-evaluate run. The
training script interpolates an undefined `adapt_think_max_response_length` into
the experiment name, producing a `-fl-` path segment. The evaluation script
instead expects `-fl4096` and a different checkpoint directory layout.

## Limitations

- This is one historical run, not a multi-seed replication.
- No per-example step-300 predictions, RNG state, or complete main-run stdout was
  retained.
- GSM8K and MATH500 use stochastic single-sample validation.
- No confidence intervals or statistical-significance claims are provided.
- Checkpoint selection and reporting use the same validation suites.
- The results support a descriptive account of the logged run, not a causal or
  universal claim about difficulty awareness.

Within those boundaries, Experiment 7-10 is complete as a checkpoint-free
training report.
