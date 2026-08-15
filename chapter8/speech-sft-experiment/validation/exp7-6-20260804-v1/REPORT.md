# Experiment 7-6 strict acceptance report

Execution acceptance: **PASS**

This run trained two real LoRA adapters on an RTX PRO 6000. It used 128 Orpheus training utterances plus 16 held-out utterances, and 168 stratified Sesame training utterances plus 24 held-out utterances. Each track completed 60 optimizer updates at effective batch size four. Both adapters are identified by local SHA-256 inventories and public Hugging Face repositories.

## Execution gates

- PASS — `orpheus_128_train_examples`
- PASS — `orpheus_16_held_out_examples`
- PASS — `orpheus_60_optimizer_steps`
- PASS — `orpheus_remote_adapter_sha256_verified`
- PASS — `orpheus_16_valid_comparison_files`
- PASS — `sesame_128_train_examples`
- PASS — `sesame_tag_categories_present`
- PASS — `sesame_60_optimizer_steps`
- PASS — `sesame_remote_adapter_sha256_verified`
- PASS — `sesame_24_valid_comparison_files`

## Hypothesis results

- SUPPORTED — `orpheus_held_out_loss_decreased`
- NOT SUPPORTED — `orpheus_cross_sentence_timbre_proxy_improved`
- SUPPORTED — `sesame_held_out_loss_decreased`
- SUPPORTED — `sesame_adapted_mean_tag_score_is_positive`
- SUPPORTED — `sesame_tag_sensitivity_improved_over_base`

Execution completion and hypothesis support are intentionally separate. A completed campaign may produce a negative hypothesis result.

## Orpheus result

- Held-out loss: 5.237792 before → 4.865821 after.
- Mean cross-sentence MFCC-statistic cosine: 0.988627 base → 0.986702 adapted (Δ -0.001924).
- Eight unseen sentences were generated for each arm with matched seeds. This metric is a timbre-consistency proxy; it is not speaker-verification or a listening-test score.

## Sesame result

- Held-out loss: 128.230759 before → 124.342400 after.
- Mean matching AudioSet event-score difference (tagged − neutral): +0.000131 base → +0.001097 adapted (Δ +0.000966).
- Positive matched pairs: 3/6 base; 4/6 adapted.
- Six prompt pairs (laugh, giggle, sigh) were generated per arm with the same seed within each tagged/neutral pair. AudioSet scores are detector proxies, not proof of natural expression.

## Failure retention and limits

`failure_comparisons.json` retains silent/short outputs, each Orpheus arm's least-consistent sentence pair, and every Sesame pair where adding a tag did not raise the matching AudioSet score. `compatibility_failures.json` retains the disabled-source-dataset failure, current Unsloth CSM pad-token rejection, and Transformers bf16 codec merge failure, together with the exact standard-PEFT/float32 fallback. The Sesame held-out loss split contains laugh, sigh, and neutral examples but no giggle examples because all 32 available giggle-tagged rows were allocated to the substantive training split. The campaign does not include blinded human MOS, speaker-verification enrollment, confidence intervals over multiple training seeds, or deployment-scale data. Therefore it makes no claim of perceptual quality or generalization beyond this bounded run.

## Adapter identity

- Orpheus: https://huggingface.co/bojieli/exp7-6-orpheus-elise-lora/tree/536092e9479fa1717e2b8f9cc1be52728b273e95
- Sesame: https://huggingface.co/bojieli/exp7-6-sesame-elise-tags-lora/tree/f2e042be0f38d6078976ef7e16cf49b91097f756
- Exact revisions and every retained artifact hash are in `orpheus_manifest.json`, `sesame_manifest.json`, and `artifact_inventory.json`.
