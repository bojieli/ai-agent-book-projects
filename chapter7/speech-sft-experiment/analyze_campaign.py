#!/usr/bin/env python3
"""Build the strict, hash-verified acceptance package for Experiment 7-6."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch
from huggingface_hub import hf_hub_download
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

AST_MODEL = "MIT/ast-finetuned-audioset-10-10-0.4593"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audio_stats(path: Path):
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    rms = float(np.sqrt(np.mean(np.square(y)))) if len(y) else 0.0
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    # Mean + variability is a transparent timbre proxy, not a human quality score.
    embedding = np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1)])
    embedding /= max(float(np.linalg.norm(embedding)), 1e-12)
    return {
        "samples": len(y),
        "sample_rate": sr,
        "seconds": len(y) / sr,
        "rms": rms,
        "embedding": embedding,
    }


def orpheus_analysis(root: Path, manifest):
    result = {}
    failures = []
    for arm in ("base", "adapted"):
        records = [x for x in manifest["audio"] if f"orpheus/{arm}/" in x["path"]]
        stats = []
        for rec in records:
            item = audio_stats(root / rec["path"])
            item.update({"prompt_id": rec["prompt_id"], "path": rec["path"]})
            stats.append(item)
            if item["samples"] < 2400 or item["rms"] < 1e-5:
                failures.append({"track": "orpheus", "arm": arm, "reason": "short_or_silent", **{k: v for k, v in item.items() if k != "embedding"}})
        similarities = []
        for a, b in itertools.combinations(stats, 2):
            similarities.append(
                {
                    "prompt_a": a["prompt_id"],
                    "prompt_b": b["prompt_id"],
                    "cosine": float(np.dot(a["embedding"], b["embedding"])),
                }
            )
        similarities.sort(key=lambda x: x["cosine"])
        if similarities:
            failures.append({"track": "orpheus", "arm": arm, "reason": "lowest_cross_sentence_timbre_proxy", **similarities[0]})
        result[arm] = {
            "audio_count": len(stats),
            "valid_audio_count": sum(x["samples"] >= 2400 and x["rms"] >= 1e-5 for x in stats),
            "mean_pairwise_mfcc_cosine": float(np.mean([x["cosine"] for x in similarities])),
            "min_pairwise_mfcc_cosine": min((x["cosine"] for x in similarities), default=None),
            "pairwise": similarities,
        }
    result["adapted_minus_base_mean_pairwise_mfcc_cosine"] = (
        result["adapted"]["mean_pairwise_mfcc_cosine"] - result["base"]["mean_pairwise_mfcc_cosine"]
    )
    return result, failures


def find_label(model, needle):
    labels = model.config.id2label
    matches = [int(i) for i, label in labels.items() if needle.lower() == label.lower()]
    if not matches:
        matches = [int(i) for i, label in labels.items() if needle.lower() in label.lower()]
    if not matches:
        raise RuntimeError(f"AudioSet label not found: {needle}")
    return matches[0], labels[matches[0]]


def sesame_analysis(root: Path, manifest):
    extractor = AutoFeatureExtractor.from_pretrained(AST_MODEL)
    model = AutoModelForAudioClassification.from_pretrained(AST_MODEL).cuda().eval()
    label_ids = {}
    for tag, needle in {"laugh": "Laughter", "giggle": "Giggle", "sigh": "Sigh"}.items():
        label_ids[tag] = find_label(model, needle)
    scores = []
    failures = []
    for rec in manifest["audio"]:
        path = root / rec["path"]
        y, sr = librosa.load(path, sr=16000, mono=True)
        rms = float(np.sqrt(np.mean(np.square(y)))) if len(y) else 0.0
        inputs = extractor(y, sampling_rate=16000, return_tensors="pt").to("cuda")
        with torch.inference_mode():
            probs = model(**inputs).logits.sigmoid()[0]
        label_id, label_name = label_ids[rec["tag"]]
        row = {
            "arm": "adapted" if "/adapted/" in rec["path"] else "base",
            "pair_id": rec["pair_id"],
            "condition": rec["condition"],
            "tag": rec["tag"],
            "audioset_label": label_name,
            "audioset_score": float(probs[label_id].cpu()),
            "seconds": len(y) / 16000,
            "rms": rms,
            "path": rec["path"],
        }
        scores.append(row)
        if len(y) < 1600 or rms < 1e-5:
            failures.append({"track": "sesame", "reason": "short_or_silent", **row})
    arms = {}
    for arm in ("base", "adapted"):
        pairs = []
        for pair_id in sorted({x["pair_id"] for x in scores if x["arm"] == arm}):
            neutral = next(x for x in scores if x["arm"] == arm and x["pair_id"] == pair_id and x["condition"] == "neutral")
            tagged = next(x for x in scores if x["arm"] == arm and x["pair_id"] == pair_id and x["condition"] == "tagged")
            pair = {
                "pair_id": pair_id,
                "tag": tagged["tag"],
                "neutral_score": neutral["audioset_score"],
                "tagged_score": tagged["audioset_score"],
                "tagged_minus_neutral": tagged["audioset_score"] - neutral["audioset_score"],
            }
            pairs.append(pair)
            if pair["tagged_minus_neutral"] <= 0:
                failures.append({"track": "sesame", "arm": arm, "reason": "tag_did_not_raise_matching_audioset_score", **pair})
        arms[arm] = {
            "audio_count": sum(x["arm"] == arm for x in scores),
            "valid_audio_count": sum(x["arm"] == arm and x["seconds"] >= 0.1 and x["rms"] >= 1e-5 for x in scores),
            "mean_tagged_minus_neutral": float(np.mean([x["tagged_minus_neutral"] for x in pairs])),
            "positive_pair_count": sum(x["tagged_minus_neutral"] > 0 for x in pairs),
            "pairs": pairs,
        }
    result = {
        "classifier": AST_MODEL,
        "labels": {k: {"id": v[0], "name": v[1]} for k, v in label_ids.items()},
        "base": arms["base"],
        "adapted": arms["adapted"],
        "adapted_minus_base_mean_tag_sensitivity": arms["adapted"]["mean_tagged_minus_neutral"] - arms["base"]["mean_tagged_minus_neutral"],
        "scores": scores,
    }
    return result, failures


def verify_remote_adapter(manifest):
    expected = next(
        x for x in manifest["adapter_local_files"] if x["path"].endswith("adapter_model.safetensors")
    )
    repo_id = manifest["adapter_huggingface_repo"].removeprefix("https://huggingface.co/")
    downloaded = Path(
        hf_hub_download(
            repo_id,
            "adapter_model.safetensors",
            revision=manifest["adapter_huggingface_revision"],
        )
    )
    actual = sha256(downloaded)
    return {
        "repository": manifest["adapter_huggingface_repo"],
        "revision": manifest["adapter_huggingface_revision"],
        "expected_sha256": expected["sha256"],
        "downloaded_sha256": actual,
        "verified": actual == expected["sha256"],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", type=Path, required=True)
    args = p.parse_args()
    root = args.run
    orpheus_manifest = json.loads((root / "orpheus_manifest.json").read_text())
    sesame_manifest = json.loads((root / "sesame_manifest.json").read_text())
    orpheus, orpheus_failures = orpheus_analysis(root, orpheus_manifest)
    sesame, sesame_failures = sesame_analysis(root, sesame_manifest)
    adapter_verification = {
        "orpheus": verify_remote_adapter(orpheus_manifest),
        "sesame": verify_remote_adapter(sesame_manifest),
    }

    gates = {
        "orpheus_128_train_examples": orpheus_manifest["train_examples_encoded"] >= 128,
        "orpheus_16_held_out_examples": orpheus_manifest["eval_examples_encoded"] >= 16,
        "orpheus_60_optimizer_steps": orpheus_manifest["optimizer_steps"] >= 60,
        "orpheus_remote_adapter_sha256_verified": adapter_verification["orpheus"]["verified"],
        "orpheus_16_valid_comparison_files": orpheus["base"]["valid_audio_count"] == 8 and orpheus["adapted"]["valid_audio_count"] == 8,
        "sesame_128_train_examples": sesame_manifest["train_examples_preprocessed"] >= 128,
        "sesame_tag_categories_present": all(sesame_manifest["train_category_counts"].get(x, 0) > 0 for x in ("laugh", "giggle", "sigh", "neutral")),
        "sesame_60_optimizer_steps": sesame_manifest["optimizer_steps"] >= 60,
        "sesame_remote_adapter_sha256_verified": adapter_verification["sesame"]["verified"],
        "sesame_24_valid_comparison_files": sesame["base"]["valid_audio_count"] == 12 and sesame["adapted"]["valid_audio_count"] == 12,
    }
    hypotheses = {
        "orpheus_held_out_loss_decreased": orpheus_manifest["post_eval"]["eval_loss"] < orpheus_manifest["pre_eval"]["eval_loss"],
        "orpheus_cross_sentence_timbre_proxy_improved": orpheus["adapted_minus_base_mean_pairwise_mfcc_cosine"] > 0,
        "sesame_held_out_loss_decreased": sesame_manifest["post_eval"]["eval_loss"] < sesame_manifest["pre_eval"]["eval_loss"],
        "sesame_adapted_mean_tag_score_is_positive": sesame["adapted"]["mean_tagged_minus_neutral"] > 0,
        "sesame_tag_sensitivity_improved_over_base": sesame["adapted_minus_base_mean_tag_sensitivity"] > 0,
    }
    analysis = {
        "experiment": "7-6",
        "execution_acceptance": "PASS" if all(gates.values()) else "FAIL",
        "execution_gates": gates,
        "hypothesis_results": hypotheses,
        "quality_claim": "No human naturalness or voice-identity quality claim; automatic metrics are reproducible proxies only.",
        "remote_adapter_verification": adapter_verification,
        "orpheus": orpheus,
        "sesame": sesame,
    }
    (root / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    failures = orpheus_failures + sesame_failures
    (root / "failure_comparisons.json").write_text(json.dumps(failures, indent=2) + "\n")

    inventory = []
    external_blob_names = {"adapter_model.safetensors", "tokenizer.json", "tokenizer_config.json"}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in {"artifact_inventory.json", "REPORT.md"} | external_blob_names:
            inventory.append({"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": sha256(path)})
    for manifest in (orpheus_manifest, sesame_manifest):
        for item in manifest["adapter_local_files"]:
            if Path(item["path"]).name in external_blob_names:
                inventory.append({
                    **item,
                    "storage": "huggingface",
                    "repository": manifest["adapter_huggingface_repo"],
                    "revision": manifest["adapter_huggingface_revision"],
                })
    (root / "artifact_inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")

    gate_lines = "\n".join(f"- {'PASS' if ok else 'FAIL'} — `{name}`" for name, ok in gates.items())
    hypothesis_lines = "\n".join(f"- {'SUPPORTED' if ok else 'NOT SUPPORTED'} — `{name}`" for name, ok in hypotheses.items())
    report = f"""# Experiment 7-6 strict acceptance report

Execution acceptance: **{analysis['execution_acceptance']}**

This run trained two real LoRA adapters on an RTX PRO 6000. It used 128 Orpheus training utterances plus 16 held-out utterances, and {sesame_manifest['train_examples_preprocessed']} stratified Sesame training utterances plus {sesame_manifest['eval_examples_preprocessed']} held-out utterances. Each track completed 60 optimizer updates at effective batch size four. Both adapters are identified by local SHA-256 inventories and public Hugging Face repositories.

## Execution gates

{gate_lines}

## Hypothesis results

{hypothesis_lines}

Execution completion and hypothesis support are intentionally separate. A completed campaign may produce a negative hypothesis result.

## Orpheus result

- Held-out loss: {orpheus_manifest['pre_eval']['eval_loss']:.6f} before → {orpheus_manifest['post_eval']['eval_loss']:.6f} after.
- Mean cross-sentence MFCC-statistic cosine: {orpheus['base']['mean_pairwise_mfcc_cosine']:.6f} base → {orpheus['adapted']['mean_pairwise_mfcc_cosine']:.6f} adapted (Δ {orpheus['adapted_minus_base_mean_pairwise_mfcc_cosine']:+.6f}).
- Eight unseen sentences were generated for each arm with matched seeds. This metric is a timbre-consistency proxy; it is not speaker-verification or a listening-test score.

## Sesame result

- Held-out loss: {sesame_manifest['pre_eval']['eval_loss']:.6f} before → {sesame_manifest['post_eval']['eval_loss']:.6f} after.
- Mean matching AudioSet event-score difference (tagged − neutral): {sesame['base']['mean_tagged_minus_neutral']:+.6f} base → {sesame['adapted']['mean_tagged_minus_neutral']:+.6f} adapted (Δ {sesame['adapted_minus_base_mean_tag_sensitivity']:+.6f}).
- Positive matched pairs: {sesame['base']['positive_pair_count']}/6 base; {sesame['adapted']['positive_pair_count']}/6 adapted.
- Six prompt pairs (laugh, giggle, sigh) were generated per arm with the same seed within each tagged/neutral pair. AudioSet scores are detector proxies, not proof of natural expression.

## Failure retention and limits

`failure_comparisons.json` retains silent/short outputs, each Orpheus arm's least-consistent sentence pair, and every Sesame pair where adding a tag did not raise the matching AudioSet score. `compatibility_failures.json` retains the disabled-source-dataset failure, current Unsloth CSM pad-token rejection, and Transformers bf16 codec merge failure, together with the exact standard-PEFT/float32 fallback. The Sesame held-out loss split contains laugh, sigh, and neutral examples but no giggle examples because all 32 available giggle-tagged rows were allocated to the substantive training split. The campaign does not include blinded human MOS, speaker-verification enrollment, confidence intervals over multiple training seeds, or deployment-scale data. Therefore it makes no claim of perceptual quality or generalization beyond this bounded run.

## Adapter identity

- Orpheus: {orpheus_manifest['adapter_huggingface_repo']}/tree/{orpheus_manifest['adapter_huggingface_revision']}
- Sesame: {sesame_manifest['adapter_huggingface_repo']}/tree/{sesame_manifest['adapter_huggingface_revision']}
- Exact revisions and every retained artifact hash are in `orpheus_manifest.json`, `sesame_manifest.json`, and `artifact_inventory.json`.
"""
    (root / "REPORT.md").write_text(report)


if __name__ == "__main__":
    main()
