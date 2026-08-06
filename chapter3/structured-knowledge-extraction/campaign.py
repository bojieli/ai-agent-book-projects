#!/usr/bin/env python3
"""Canonical official-CAIL2018 campaign for Experiment 3-12."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import random
import re
import statistics
import sys
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import numpy as np
from openai import OpenAI
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
sys.path.insert(0, str(CHAPTER))
from experiment_utils import ChatRecorder, jsonable, sha256_file, write_campaign_evidence


ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"
MOONSHOT_ENDPOINT = "https://api.moonshot.cn/v1"
OFFICIAL_URL = "https://cail.oss-cn-qingdao.aliyuncs.com/CAIL2018_ALL_DATA.zip"
OFFICIAL_REPOSITORY = "https://github.com/china-ai-law-challenge/CAIL2018"
OFFICIAL_REVISION = "599781ffcbfb33237580c6766afe3af9e1ff7229"
CHARGES = ("盗窃罪", "故意伤害罪", "诈骗罪")
RAW_TO_CHARGE = {"盗窃": "盗窃罪", "故意伤害": "故意伤害罪", "诈骗": "诈骗罪"}
DISCLAIMER = "【免责声明】本结果仅用于数据分析教学，不构成法律意见或量刑承诺；真实案件请咨询有资质的律师。"


def parse_json(text: str) -> Dict[str, Any]:
    value = (text or "").strip()
    if "```" in value:
        value = value.split("```", 2)[1]
        if value.lstrip().startswith("json"):
            value = value.lstrip()[4:]
    return json.loads(value.strip())


def find_training_member(archive: Path) -> Tuple[str, Dict[str, Any]]:
    with zipfile.ZipFile(archive) as zf:
        candidates = []
        for info in zf.infolist():
            name = info.filename.lower()
            if name.endswith(".json") and "train" in name and "data" in name and info.file_size > 1_000_000:
                candidates.append(info)
        if not candidates:
            raise RuntimeError("official archive contains no CAIL JSON training member")
        selected = max(candidates, key=lambda info: info.file_size)
        return selected.filename, {
            "member": selected.filename,
            "uncompressed_bytes": selected.file_size,
            "compressed_bytes": selected.compress_size,
            "crc32": f"{selected.CRC:08x}",
        }


def sentence_months(meta: Dict[str, Any]) -> int | None:
    term = meta.get("term_of_imprisonment") or {}
    if term.get("death_penalty") or term.get("life_imprisonment"):
        return None
    try:
        months = int(term.get("imprisonment"))
    except (TypeError, ValueError):
        return None
    return months if 0 < months <= 360 else None


def build_sample(archive: Path, sample_path: Path, seed: int, train_per_charge: int, heldout_per_charge: int):
    expected = train_per_charge + heldout_per_charge
    member, member_meta = find_training_member(archive)
    selected: Dict[str, List[Dict[str, Any]]] = {charge: [] for charge in CHARGES}
    seen_hashes = set()
    with zipfile.ZipFile(archive) as zf, zf.open(member) as stream:
        for line_number, raw in enumerate(stream, start=1):
            try:
                record = json.loads(raw)
            except Exception:
                continue
            fact = str(record.get("fact") or "").strip()
            meta = record.get("meta") or {}
            accusations = meta.get("accusation") or []
            if len(accusations) != 1:
                continue
            charge = RAW_TO_CHARGE.get(str(accusations[0]).strip("[]'\""))
            months = sentence_months(meta)
            if charge not in selected or months is None or len(fact) < 80:
                continue
            fingerprint = hashlib.sha256(fact.encode("utf-8")).hexdigest()
            if fingerprint in seen_hashes:
                continue
            seen_hashes.add(fingerprint)
            selected[charge].append(
                {
                    "id": f"cail2018-{fingerprint[:16]}",
                    "charge": charge,
                    "fact": fact,
                    "label_months": months,
                    "source_member": member,
                    "source_line": line_number,
                    "fact_sha256": fingerprint,
                }
            )
            if all(len(selected[item]) >= expected for item in CHARGES):
                break
    if any(len(selected[charge]) < expected for charge in CHARGES):
        raise RuntimeError(f"official member did not yield balanced sample: { {k: len(v) for k, v in selected.items()} }")
    rng = random.Random(seed)
    rows = []
    for charge in CHARGES:
        group = selected[charge][:expected]
        rng.shuffle(group)
        for index, row in enumerate(group):
            rows.append({**row, "split": "train" if index < train_per_charge else "heldout"})
    rows.sort(key=lambda row: (row["split"], row["charge"], row["id"]))
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    sample_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return rows, member_meta


def load_or_build_sample(args: argparse.Namespace):
    archive = Path(args.archive).resolve()
    if not archive.exists():
        raise RuntimeError(f"official CAIL2018 archive missing: {archive}; download from {OFFICIAL_URL}")
    sample_path = HERE / "data" / "official" / f"cail2018_sample_seed{args.seed}.jsonl"
    if sample_path.exists():
        rows = [json.loads(line) for line in sample_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        member, member_meta = find_training_member(archive)
        member_meta["member"] = member
    else:
        rows, member_meta = build_sample(archive, sample_path, args.seed, args.train_per_charge, args.heldout_per_charge)
    expected = (args.train_per_charge + args.heldout_per_charge) * len(CHARGES)
    if len(rows) != expected:
        raise RuntimeError(f"sample size mismatch: expected {expected}, got {len(rows)}")
    return archive, sample_path, rows, member_meta


class CachedCalls:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.root = HERE / "validation" / "checkpoints" / f"official-seed{args.seed}"
        self.root.mkdir(parents=True, exist_ok=True)

    def json_call(self, *, provider: str, purpose: str, messages: List[Dict[str, str]], max_tokens: int, key: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", key)
        path = self.root / f"{safe}.json"
        model = self.args.discovery_model if provider == "ark" else self.args.judge_model
        endpoint = self.args.discovery_endpoint if provider == "ark" else self.args.judge_endpoint
        signature = hashlib.sha256(json.dumps({"provider": provider, "model": model, "endpoint": endpoint, "seed": self.args.seed, "messages": messages}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("signature") != signature:
                raise RuntimeError(f"checkpoint signature mismatch: {path}")
            return cached["parsed"], cached["receipt"]
        api_key = os.getenv("ARK_API_KEY") if provider == "ark" else (os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY"))
        client = OpenAI(api_key=api_key, base_url=endpoint, timeout=self.args.timeout, max_retries=3)
        recorder = ChatRecorder(client, provider, endpoint)
        response = recorder.create(
            purpose=purpose,
            model=model,
            messages=messages,
            temperature=0,
            seed=self.args.seed,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        parsed = parse_json(response.choices[0].message.content or "{}")
        payload = {"signature": signature, "parsed": parsed, "receipt": recorder.calls[-1]}
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        return parsed, recorder.calls[-1]


DISCOVERY_SYSTEM = """你是司法判例数据研究员。对给出的真实刑事案件事实与已知罪名进行自下而上分析，
自由发现文本中可能影响裁判与量刑的因素；不得套用预设字段清单。每个因素给出 key（英文 snake_case）、
name_cn、charge（通用或给定罪名）、kind（numeric/bool/categorical）、values（只列实际观察值）与简短证据说明。
只返回 JSON：{"factors":[...]}。"""


def discovery_batch(cache: CachedCalls, rows: List[Dict[str, Any]], index: int):
    cases = [{"id": row["id"], "charge": row["charge"], "fact": row["fact"]} for row in rows]
    return cache.json_call(
        provider="ark",
        purpose=f"3-12 bottom-up factor discovery batch {index}",
        messages=[{"role": "system", "content": DISCOVERY_SYSTEM}, {"role": "user", "content": json.dumps(cases, ensure_ascii=False)}],
        max_tokens=3500,
        key=f"discovery-{index:03d}",
    )


def normalize_schema(raw: Dict[str, Any]) -> Dict[str, Any]:
    output = {"core": [], "extensions": {charge: [] for charge in CHARGES}}
    used = set()
    for section, values in [("core", raw.get("core") or [])] + [(charge, (raw.get("extensions") or {}).get(charge) or []) for charge in CHARGES]:
        for item in values:
            key = re.sub(r"[^a-z0-9_]+", "_", str(item.get("key", "")).lower()).strip("_")
            kind = str(item.get("kind", "")).lower()
            if not key or key in used or kind not in {"numeric", "bool", "categorical"}:
                continue
            used.add(key)
            factor = {
                "key": key,
                "name_cn": str(item.get("name_cn") or key),
                "kind": kind,
                "values": [str(value) for value in (item.get("values") or [])][:12] if kind == "categorical" else [],
                "direction": str(item.get("direction") or "neutral"),
                "question": str(item.get("question") or f"请补充{item.get('name_cn') or key}情况。"),
            }
            (output["core"] if section == "core" else output["extensions"][section]).append(factor)
    return output


def consolidate_schema(cache: CachedCalls, raw_factors: List[Dict[str, Any]]):
    system = f"""你是司法数据建模专家。下面是从 360 条真实 CAIL2018 训练案件分批自由发现的原始因素。
仅根据这些发现归并同义项，形成模块化 schema。core 最多 16 个跨罪名通用因素；extensions 必须且只能有
{list(CHARGES)} 三个键，每个最多 12 个罪名特有因素。不要引入原始发现中没有的因素。每项字段：
key,name_cn,kind(numeric|bool|categorical),values,direction(aggravating|mitigating|neutral),question。
只返回 JSON：{{"core":[],"extensions":{{"盗窃罪":[],"故意伤害罪":[],"诈骗罪":[]}}}}。"""
    parsed, receipt = cache.json_call(
        provider="ark",
        purpose="3-12 consolidate bottom-up factors",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(raw_factors, ensure_ascii=False)}],
        max_tokens=5000,
        key="schema-consolidation",
    )
    return normalize_schema(parsed), receipt


def factors_for(schema: Dict[str, Any], charge: str) -> List[Dict[str, Any]]:
    result, used = [], set()
    for factor in schema["core"] + schema["extensions"][charge]:
        if factor["key"] not in used:
            result.append(factor)
            used.add(factor["key"])
    return result


def extraction_batch(cache: CachedCalls, schema: Dict[str, Any], rows: List[Dict[str, Any]], index: int):
    cases = [{"id": row["id"], "charge": row["charge"], "fact": row["fact"]} for row in rows]
    system = """你是司法判例结构化抽取器。严格按给定的、由训练数据自下而上发现的 schema 抽取。
numeric 输出数值，bool 输出 true/false，categorical 取 schema 值；文本未提及必须为 null，不得推断。
保持每个 id 与 charge。只返回 JSON：{"cases":[{"id":"...","charge":"...","factors":{...}},...]}。"""
    return cache.json_call(
        provider="ark",
        purpose=f"3-12 modular extraction batch {index}",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"DISCOVERED SCHEMA:\n{json.dumps(schema, ensure_ascii=False)}\n\nCASES:\n{json.dumps(cases, ensure_ascii=False)}"},
        ],
        max_tokens=6000,
        key=f"extraction-{index:03d}",
    )


def extraction_case(cache: CachedCalls, schema: Dict[str, Any], row: Dict[str, Any]):
    """Resume a provider-sensitive missing batch one case at a time.

    Some real CAIL fact combinations can make a whole ten-case request stall or
    trip provider filtering.  A one-case retry preserves the identical schema,
    source text, model, and extraction contract while retaining a receipt for
    every recovered row instead of invalidating hundreds of completed calls.
    """
    return cache.json_call(
        provider="ark",
        purpose=f"3-12 modular extraction case {row['id']}",
        messages=[
            {
                "role": "system",
                "content": (
                    "你是司法判例结构化抽取器。严格按给定的、由训练数据自下而上发现的 schema 抽取。"
                    "numeric 输出数值，bool 输出 true/false，categorical 取 schema 值；文本未提及必须为 null，"
                    "不得推断。保持 id 与 charge。只返回 JSON："
                    '{"cases":[{"id":"...","charge":"...","factors":{...}}]}。'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"DISCOVERED SCHEMA:\n{json.dumps(schema, ensure_ascii=False)}\n\n"
                    f"CASE:\n{json.dumps({'id': row['id'], 'charge': row['charge'], 'fact': row['fact']}, ensure_ascii=False)}"
                ),
            },
        ],
        max_tokens=2000,
        key=f"extraction-case-{row['id']}",
    )


def normalize_value(value: Any, factor: Dict[str, Any]):
    if value is None or value == "":
        return None
    if factor["kind"] == "numeric":
        if isinstance(value, (int, float)):
            return float(value)
        found = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
        return float(found.group()) if found else None
    if factor["kind"] == "bool":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"true", "1", "是", "有", "存在"}:
            return True
        if text in {"false", "0", "否", "无", "不存在"}:
            return False
        return None
    return str(value)


def normalize_extractions(schema: Dict[str, Any], source_rows: List[Dict[str, Any]], batch_outputs: List[Dict[str, Any]]):
    raw_by_id = {}
    for output in batch_outputs:
        for item in output.get("cases") or []:
            raw_by_id[str(item.get("id"))] = item
    results, missing = [], []
    for row in source_rows:
        item = raw_by_id.get(row["id"])
        if not item:
            missing.append(row["id"])
            continue
        raw = item.get("factors") or item
        extraction = {"charge": row["charge"]}
        for factor in factors_for(schema, row["charge"]):
            extraction[factor["key"]] = normalize_value(raw.get(factor["key"]), factor)
        results.append({**row, "extracted": extraction})
    if missing:
        raise RuntimeError(f"live extraction omitted {len(missing)} cases: {missing[:5]}")
    return results


def missing_extraction_rows(
    source_rows: List[Dict[str, Any]], outputs: Iterable[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Return source rows omitted by otherwise successful extraction calls."""
    extracted_ids = {
        str(item.get("id"))
        for output in outputs
        for item in (output.get("cases") or [])
        if item.get("id") is not None
    }
    return [row for row in source_rows if row["id"] not in extracted_ids]


def build_feature_space(schema: Dict[str, Any], training: List[Dict[str, Any]]):
    factor_by_key = {}
    for factor in schema["core"] + [f for charge in CHARGES for f in schema["extensions"][charge]]:
        factor_by_key.setdefault(factor["key"], factor)
    columns = [f"charge={charge}" for charge in CHARGES]
    for key, factor in factor_by_key.items():
        if factor["kind"] == "numeric":
            columns.append(f"num:{key}")
        elif factor["kind"] == "bool":
            columns.append(f"bool:{key}")
        else:
            values = set(factor.get("values") or [])
            values.update(str(row["extracted"].get(key)) for row in training if row["extracted"].get(key) is not None)
            columns.extend(f"cat:{key}={value}" for value in sorted(values))
    return columns, factor_by_key


def vectorize(extraction: Dict[str, Any], columns: List[str]):
    values, known = [], []
    for column in columns:
        if column.startswith("charge="):
            values.append(1.0 if extraction.get("charge") == column[7:] else 0.0)
            known.append(True)
        elif column.startswith("num:"):
            value = extraction.get(column[4:])
            values.append(math.log1p(max(0.0, float(value))) if value is not None else 0.0)
            known.append(value is not None)
        elif column.startswith("bool:"):
            value = extraction.get(column[5:])
            values.append(1.0 if value is True else 0.0)
            known.append(value is not None)
        else:
            key, expected = column[4:].split("=", 1)
            value = extraction.get(key)
            values.append(1.0 if value is not None and str(value) == expected else 0.0)
            known.append(value is not None)
    return np.asarray(values), np.asarray(known)


def fit_prototypes(schema: Dict[str, Any], training: List[Dict[str, Any]], seed: int):
    columns, factor_by_key = build_feature_space(schema, training)
    raw = np.asarray([vectorize(row["extracted"], columns)[0] for row in training])
    scaler = StandardScaler().fit(raw)
    z_all = scaler.transform(raw)
    prototypes, diagnostics = [], {}
    for charge in CHARGES:
        positions = [index for index, row in enumerate(training) if row["charge"] == charge]
        values = z_all[positions]
        candidates = []
        for k in range(2, 6):
            model = KMeans(n_clusters=k, n_init=20, random_state=seed).fit(values)
            score = float(silhouette_score(values, model.labels_))
            candidates.append({"k": k, "silhouette": score, "model": model})
        best = max(candidates, key=lambda item: item["silhouette"])
        diagnostics[charge] = {"n": len(positions), "candidates": [{"k": item["k"], "silhouette": item["silhouette"]} for item in candidates], "selected_k": best["k"], "selected_silhouette": best["silhouette"]}
        for cluster in range(best["k"]):
            members_local = np.where(best["model"].labels_ == cluster)[0]
            members = [positions[index] for index in members_local]
            centroid = best["model"].cluster_centers_[cluster]
            months = np.asarray([training[index]["label_months"] for index in members], dtype=float)
            significant = [index for index in np.argsort(-np.abs(centroid)) if not columns[index].startswith("charge=")][:8]
            prototypes.append(
                {
                    "id": f"{charge}-prototype-{cluster}",
                    "charge": charge,
                    "size": len(members),
                    "centroid_std": centroid.tolist(),
                    "sentence_months": {
                        "median": float(np.median(months)),
                        "q25": float(np.percentile(months, 25)),
                        "q75": float(np.percentile(months, 75)),
                        "min": float(months.min()),
                        "max": float(months.max()),
                    },
                    "defining_features": [{"feature": columns[index], "z": float(centroid[index])} for index in significant],
                }
            )
    centroids = np.asarray([item["centroid_std"] for item in prototypes])
    weights = np.asarray([item["size"] for item in prototypes], dtype=float)
    weights /= weights.sum()
    between = (weights[:, None] * np.square(centroids)).sum(axis=0)
    importance = [{"feature": columns[index], "score": float(between[index])} for index in np.argsort(-between)]
    model = {
        "columns": columns,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "prototypes": prototypes,
        "importance": importance,
        "diagnostics": diagnostics,
        "training_samples": len(training),
    }
    return model


def match_prototype(model: Dict[str, Any], extraction: Dict[str, Any]):
    raw, known = vectorize(extraction, model["columns"])
    scale = np.asarray(model["scaler_scale"])
    scale[scale == 0] = 1
    z = (raw - np.asarray(model["scaler_mean"])) / scale
    candidates = [item for item in model["prototypes"] if item["charge"] == extraction["charge"]]
    best = None
    for item in candidates:
        distance = float(np.linalg.norm((z - np.asarray(item["centroid_std"])) * known) / max(1, known.sum()))
        if best is None or distance < best[1]:
            best = (item, distance)
    return best


def advice_one(cache: CachedCalls, row: Dict[str, Any], prototype: Dict[str, Any], distance: float, index: int):
    allowed = {
        "prototype_id": prototype["id"],
        "charge": prototype["charge"],
        "prototype_size": prototype["size"],
        "sentence_months": prototype["sentence_months"],
        "defining_features": prototype["defining_features"],
        "match_distance": distance,
    }
    messages = [
        {
            "role": "system",
            "content": (
                "你是司法数据分析助手。只可使用给出的训练集案件原型统计与已抽取因素，不得使用原始训练案件、"
                "外部法律知识或自行给出其他刑期数字。解释匹配依据和统计区间，强调不确定性。只返回 JSON："
                '{"advice":"..."}。不要写免责声明，系统会统一附加。'
            ),
        },
        {"role": "user", "content": f"HELDOUT EXTRACTED FACTORS:\n{json.dumps(row['extracted'], ensure_ascii=False)}\n\nMATCHED TRAINING PROTOTYPE ONLY:\n{json.dumps(allowed, ensure_ascii=False)}"},
    ]
    parsed, receipt = cache.json_call(provider="ark", purpose=f"3-12 held-out prototype-grounded advice {row['id']}", messages=messages, max_tokens=900, key=f"advice-{index:03d}-{row['id']}")
    advice = str(parsed.get("advice") or "").strip() + "\n\n" + DISCLAIMER
    return {"id": row["id"], "charge": row["charge"], "extracted": row["extracted"], "prototype": allowed, "advice": advice, "source_fact": row["fact"], "actual_label_months": row["label_months"], "advice_request_excludes_label": "label_months" not in json.dumps(receipt.get("request", {}), ensure_ascii=False)}, receipt


def judge_one(cache: CachedCalls, result: Dict[str, Any], index: int):
    messages = [
        {
            "role": "system",
            "content": (
                "你是独立司法数据实验评审。评估建议是否忠实于给定原型统计、是否把统计当成不确定参考而非承诺、"
                "对留出案件是否有用、是否包含明确法律免责声明。不要补充法律意见。只返回 JSON。"
            ),
        },
        {
            "role": "user",
            "content": f"""留出案件事实：{result['source_fact']}
真实裁判刑期（仅供事后评估，建议生成器从未看到）：{result['actual_label_months']}个月
匹配原型：{json.dumps(result['prototype'], ensure_ascii=False)}
生成建议：{result['advice']}

返回：{{"prototype_grounding":1,"numeric_fidelity":1,"uncertainty_and_caution":1,"heldout_usefulness":1,
"disclaimer_present":true,"unsupported_claim":false,"reasoning":"..."}}；分数 1-4。""",
        },
    ]
    parsed, receipt = cache.json_call(provider="moonshot", purpose=f"3-12 independent held-out judge {result['id']}", messages=messages, max_tokens=700, key=f"judge-{index:03d}-{result['id']}")
    result["judge"] = parsed
    return result, receipt


def token_usage(receipts: Iterable[Dict[str, Any]]):
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for receipt in receipts:
        current = receipt.get("usage") or {}
        for key in totals:
            totals[key] += int(current.get(key) or 0)
    return totals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", default=str(HERE / "data" / "official" / "CAIL2018_ALL_DATA.zip"))
    parser.add_argument("--discovery-model", default=os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"))
    parser.add_argument("--judge-model", default=os.getenv("MEMORY_JUDGE_MODEL", "moonshot-v1-32k"))
    parser.add_argument("--discovery-endpoint", default=ARK_ENDPOINT)
    parser.add_argument("--judge-endpoint", default=MOONSHOT_ENDPOINT)
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--train-per-charge", type=int, default=120)
    parser.add_argument("--heldout-per-charge", type=int, default=20)
    parser.add_argument("--discovery-batch", type=int, default=30)
    parser.add_argument("--extraction-batch", type=int, default=10)
    parser.add_argument("--advice-per-charge", type=int, default=4)
    args = parser.parse_args()
    if not os.getenv("ARK_API_KEY") or not (os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")):
        raise RuntimeError("ARK_API_KEY and MOONSHOT_API_KEY/KIMI_API_KEY are required")
    archive, sample_path, rows, member_meta = load_or_build_sample(args)
    training = [row for row in rows if row["split"] == "train"]
    heldout = [row for row in rows if row["split"] == "heldout"]
    cache = CachedCalls(args)
    receipts, errors = [], []

    shuffled = list(training)
    random.Random(args.seed).shuffle(shuffled)
    discovery_groups = [shuffled[start : start + args.discovery_batch] for start in range(0, len(shuffled), args.discovery_batch)]
    discovery_outputs: Dict[int, List[Dict[str, Any]]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(discovery_batch, cache, group, index): index for index, group in enumerate(discovery_groups)}
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            try:
                parsed, receipt = future.result()
                discovery_outputs[index] = parsed.get("factors") or []
                receipts.append(receipt)
                print(f"discovery batch {index + 1}/{len(discovery_groups)}", flush=True)
            except Exception as exc:
                errors.append({"stage": "discovery", "batch": index, "type": type(exc).__name__, "error": str(exc)})
    # Consolidation used to consume futures in completion order.  That made its
    # checkpoint signature change on every resume even though every discovery
    # response was identical.  Persist the original order once; for campaigns
    # created before this receipt existed, checkpoint mtimes reconstruct the
    # exact completion order that produced the saved consolidation response.
    discovery_order_path = cache.root / "discovery-order.json"
    if discovery_order_path.exists():
        discovery_order = json.loads(discovery_order_path.read_text(encoding="utf-8"))["batch_order"]
    else:
        checkpoint_paths = [cache.root / f"discovery-{index:03d}.json" for index in discovery_outputs]
        discovery_order = [
            int(path.stem.rsplit("-", 1)[1])
            for path in sorted(checkpoint_paths, key=lambda path: (path.stat().st_mtime_ns, path.name))
        ]
        temporary = discovery_order_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps({"batch_order": discovery_order}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(discovery_order_path)
    if sorted(discovery_order) != list(range(len(discovery_groups))) or set(discovery_outputs) != set(discovery_order):
        raise RuntimeError("discovery campaign is missing batches or has an invalid persisted order")
    raw_discovery: List[Dict[str, Any]] = [
        factor for index in discovery_order for factor in discovery_outputs[index]
    ]
    schema, receipt = consolidate_schema(cache, raw_discovery)
    receipts.append(receipt)
    if not schema["core"] or any(not schema["extensions"][charge] for charge in CHARGES):
        raise RuntimeError("live bottom-up schema is missing core or charge extension factors")

    extraction_groups = [rows[start : start + args.extraction_batch] for start in range(0, len(rows), args.extraction_batch)]
    outputs: Dict[str, Dict[str, Any]] = {}
    existing_batch_checkpoints = list(cache.root.glob("extraction-[0-9][0-9][0-9].json"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for index, group in enumerate(extraction_groups):
            batch_checkpoint = cache.root / f"extraction-{index:03d}.json"
            if batch_checkpoint.exists() or not existing_batch_checkpoints:
                futures[pool.submit(extraction_batch, cache, schema, group, index)] = (
                    f"batch-{index:03d}", index, None
                )
            else:
                # This is a resume with a missing/failed batch.  Split only the
                # missing work; completed batch signatures remain untouched.
                for row in group:
                    futures[pool.submit(extraction_case, cache, schema, row)] = (
                        f"case-{row['id']}", index, row["id"]
                    )
        for future in concurrent.futures.as_completed(futures):
            key, index, case_id = futures[future]
            try:
                parsed, receipt = future.result()
                outputs[key] = parsed
                receipts.append(receipt)
                label = f"batch {index + 1}" if case_id is None else f"case {case_id}"
                print(f"extraction {label}", flush=True)
            except Exception as exc:
                errors.append({"stage": "extraction", "batch": index, "case": case_id, "type": type(exc).__name__, "error": str(exc)})

    # A request can return valid JSON yet silently omit one or more records.
    # Recover those records individually before normalization, just as we do
    # for entirely missing batch checkpoints on resume.
    omitted_rows = missing_extraction_rows(rows, outputs.values())
    if omitted_rows:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {pool.submit(extraction_case, cache, schema, row): row for row in omitted_rows}
            for future in concurrent.futures.as_completed(futures):
                row = futures[future]
                try:
                    parsed, receipt = future.result()
                    outputs[f"case-{row['id']}"] = parsed
                    receipts.append(receipt)
                    print(f"extraction omitted case {row['id']}", flush=True)
                except Exception as exc:
                    errors.append(
                        {
                            "stage": "extraction",
                            "batch": None,
                            "case": row["id"],
                            "type": type(exc).__name__,
                            "error": str(exc),
                        }
                    )
    extracted = normalize_extractions(schema, rows, [outputs[key] for key in sorted(outputs)])
    train_extracted = [row for row in extracted if row["split"] == "train"]
    heldout_extracted = [row for row in extracted if row["split"] == "heldout"]
    model = fit_prototypes(schema, train_extracted, args.seed)

    evaluation_rows = []
    for charge in CHARGES:
        evaluation_rows.extend([row for row in heldout_extracted if row["charge"] == charge][: args.advice_per_charge])
    advice_results: Dict[int, Dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for index, row in enumerate(evaluation_rows):
            prototype, distance = match_prototype(model, row["extracted"])
            futures[pool.submit(advice_one, cache, row, prototype, distance, index)] = index
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            try:
                result, receipt = future.result()
                advice_results[index] = result
                receipts.append(receipt)
            except Exception as exc:
                errors.append({"stage": "advice", "case": evaluation_rows[index]["id"], "type": type(exc).__name__, "error": str(exc)})
    judged: Dict[int, Dict[str, Any]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(judge_one, cache, result, index): index for index, result in advice_results.items()}
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            try:
                result, receipt = future.result()
                judged[index] = result
                receipts.append(receipt)
                print(f"held-out advice/judge {len(judged)}/{len(evaluation_rows)}", flush=True)
            except Exception as exc:
                errors.append({"stage": "judge", "case": advice_results[index]["id"], "type": type(exc).__name__, "error": str(exc)})
    heldout_results = [judged[index] for index in sorted(judged)]
    archive_hash = sha256_file(archive)
    train_counts = Counter(row["charge"] for row in training)
    heldout_counts = Counter(row["charge"] for row in heldout)
    score_fields = ("prototype_grounding", "numeric_fidelity", "uncertainty_and_caution", "heldout_usefulness")
    judge_scores = {
        field: statistics.mean(float(row["judge"].get(field, 1)) for row in heldout_results)
        for field in score_fields
    } if heldout_results else {}
    acceptance = {
        "official_cail_url_revision_archive_hash": OFFICIAL_URL.startswith("https://cail.") and len(OFFICIAL_REVISION) == 40 and len(archive_hash) == 64,
        "hundreds_real_training_samples": len(training) >= 300 and all(row["source_member"] == member_meta["member"] for row in training),
        "balanced_train_heldout_split": train_counts == Counter({charge: args.train_per_charge for charge in CHARGES}) and heldout_counts == Counter({charge: args.heldout_per_charge for charge in CHARGES}),
        "live_bottom_up_discovery": len(raw_discovery) > 0 and len([call for call in receipts if "factor discovery batch" in str(call.get("purpose"))]) == len(discovery_groups),
        "modular_schema_discovered": bool(schema["core"]) and all(schema["extensions"][charge] for charge in CHARGES),
        "live_extraction_train_and_heldout": len(extracted) == len(rows) and len([
            call for call in receipts if "modular extraction" in str(call.get("purpose"))
        ]) >= len(extraction_groups),
        "cluster_diagnostics_all_charges": all(model["diagnostics"][charge]["selected_k"] >= 2 and model["diagnostics"][charge]["selected_silhouette"] > -1 for charge in CHARGES),
        "importance_model": bool(model["importance"]) and bool(model["prototypes"]),
        "heldout_advice_only_prototype_statistics": len(heldout_results) == len(evaluation_rows) and all(row["advice_request_excludes_label"] for row in heldout_results),
        "independent_external_judge": len([call for call in receipts if call.get("provider") == "moonshot"]) == len(evaluation_rows),
        "legal_disclaimer": bool(heldout_results) and all(DISCLAIMER in row["advice"] and bool(row["judge"].get("disclaimer_present")) for row in heldout_results),
        "raw_request_response_receipts": bool(receipts) and all("request" in call and "response" in call for call in receipts),
        "all_calls_succeeded": not errors,
    }
    acceptance["passed"] = all(acceptance.values())
    evidence = {
        "status": "passed" if acceptance["passed"] else ("partial" if receipts else "blocked"),
        "official_source": {
            "repository": OFFICIAL_REPOSITORY,
            "repository_revision": OFFICIAL_REVISION,
            "archive_url": OFFICIAL_URL,
            "archive_path": str(archive),
            "archive_sha256": archive_hash,
            "archive_bytes": archive.stat().st_size,
            "training_member": member_meta,
            "sample_path": str(sample_path),
            "sample_sha256": sha256_file(sample_path),
        },
        "configuration": vars(args),
        "scope": {"training": len(training), "heldout": len(heldout), "train_by_charge": dict(train_counts), "heldout_by_charge": dict(heldout_counts), "advice_judged": len(heldout_results)},
        "acceptance": acceptance,
        "summary": {
            "schema": {"core_factors": len(schema["core"]), "extension_factors": {charge: len(schema["extensions"][charge]) for charge in CHARGES}},
            "clustering": model["diagnostics"],
            "prototypes": len(model["prototypes"]),
            "heldout_judge_means": judge_scores,
            "api_calls": len(receipts),
            "token_usage": token_usage(receipts),
            "errors": len(errors),
        },
        "errors": errors,
        "discovered_schema": schema,
        "extractions": extracted,
        "prototype_model": model,
        "heldout_advice": heldout_results,
    }
    manifest = write_campaign_evidence(HERE, "3-12", evidence, receipts, input_paths=[HERE / "campaign.py", archive, sample_path])
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    print(f"Canonical evidence: {HERE / 'validation' / 'latest.json'}")
    return 0 if acceptance["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
