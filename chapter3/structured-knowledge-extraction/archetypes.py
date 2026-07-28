"""
阶段 3：聚类 + 层次重要性 —— 从结构化因子里发现「案件原型」与「因子重要性层次」。

不做刑期回归（那会得到一个说不清理由的黑箱），而是：
  1. 把每条案例的因子翻译成数值特征向量：
       - 罪名 / 分类因子(如伤害等级) 用 one-hot 开关位（不用 1/2/3，避免暗示大小关系）；
       - 数值因子(金额/人数)取 ln 压缩量纲；是非情节取 0/1。
     （某因子若同时落在 core 与某罪名扩展里，按 key 去重，特征列不重复。）
  2. 标准化后用 KMeans 聚类，k 由轮廓系数(silhouette)自动挑选，得到若干「案件原型」；
  3. 计算两级重要性：
       - 全局重要性：每个因子在原型之间的区分度（簇间方差占比）→ 全局因子重要性排序；
       - 原型内重要性：每个原型相对全局均值最突出的因子 → 定义该原型的关键特征。
     并统计每个原型的刑期分布（均值/中位/区间）作为「数据驱动的判决经验」。

产出 data/archetypes.json（可读、自洽，含标准化参数与簇心），供对话 Agent 直接引用。
"""
import json
import math
import os

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from discovery import all_factors

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MODEL_PATH = os.path.join(DATA_DIR, "archetypes.json")


# --- 特征空间：自描述列名，训练与推理共用 -----------------------------------
def build_columns(schema, results):
    """根据 schema + 抽取结果确定有序特征列（列名自描述其含义）。"""
    factors = all_factors(schema)
    kind = {f["key"]: f["kind"] for f in factors}
    charges = sorted({r["extracted"]["charge"] for r in results})

    cols = [f"charge={c}" for c in charges]
    for f in factors:
        k = f["key"]
        if kind[k] == "numeric":
            cols.append(f"num:{k}")
        elif kind[k] == "bool":
            cols.append(f"bool:{k}")
        else:  # categorical：取值集合来自 schema 与实际数据的并集
            vals = set(f.get("values") or [])
            for r in results:
                v = r["extracted"].get(k)
                if v is not None:
                    vals.add(str(v))
            for v in sorted(vals):
                cols.append(f"cat:{k}={v}")
    return cols


def vectorize(extraction, columns):
    """把一条抽取结果转成特征向量，并返回 known 掩码（该维是否有已知取值）。"""
    charge = extraction.get("charge")
    vec, known = [], []
    for col in columns:
        if col.startswith("charge="):
            vec.append(1.0 if charge == col[len("charge="):] else 0.0)
            known.append(True)  # 罪名一旦判定即视为已知
        elif col.startswith("num:"):
            v = extraction.get(col[len("num:"):])
            vec.append(math.log(v) if v else 0.0)
            known.append(v is not None)
        elif col.startswith("bool:"):
            v = extraction.get(col[len("bool:"):])
            vec.append(1.0 if v else 0.0)
            known.append(v is not None)
        else:  # cat:key=value
            body = col[len("cat:"):]
            key, val = body.split("=", 1)
            v = extraction.get(key)
            vec.append(1.0 if (v is not None and str(v) == val) else 0.0)
            known.append(v is not None)
    return np.array(vec), np.array(known)


def column_label(col, schema):
    """列名 -> 中文可读标签。"""
    name_cn = {f["key"]: f["name_cn"] for f in all_factors(schema)}
    if col.startswith("charge="):
        return "罪名=" + col[len("charge="):]
    if col.startswith("num:"):
        return name_cn.get(col[len("num:"):], col[len("num:"):]) + "(对数)"
    if col.startswith("bool:"):
        k = col[len("bool:"):]
        return name_cn.get(k, k)
    body = col[len("cat:"):]
    key, val = body.split("=", 1)
    return f"{name_cn.get(key, key)}={val}"


# --- 聚类 + 层次重要性 ------------------------------------------------------
def fit(schema, results, k_range=range(2, 5), save=True, verbose=True):
    """在**每个罪名内部**聚类出案件原型（书中：在某罪名内自动聚出典型模式），
    再跨全部原型算全局因子重要性。"""
    columns = build_columns(schema, results)
    X_raw = np.array([vectorize(r["extracted"], columns)[0] for r in results])
    months = np.array([r["label_months"] for r in results], dtype=float)
    charges = np.array([r["extracted"]["charge"] for r in results])
    is_charge_col = np.array([c.startswith("charge=") for c in columns])

    scaler = StandardScaler().fit(X_raw)
    Z = scaler.transform(X_raw)

    archetypes, aid, sils = [], 0, []
    for ch in sorted(set(charges)):
        idx = np.where(charges == ch)[0]
        Zc = Z[idx]
        # 该罪名内用轮廓系数挑 k
        best = None
        for k in k_range:
            if k >= len(idx):
                break
            km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(Zc)
            sil = silhouette_score(Zc, km.labels_)
            if best is None or sil > best[0]:
                best = (sil, k, km)
        if best is None:
            if verbose:
                print(f"    {ch}: n={len(idx)}  样本过少，跳过聚类")
            continue
        sil, k, km = best
        sils.append(sil)
        if verbose:
            print(f"    {ch}: n={len(idx)}  自动选定 k={k}  轮廓系数={sil:.3f}")
        for c in range(k):
            sub = idx[km.labels_ == c]
            z = km.cluster_centers_[c]         # 标准化空间簇心（全维）
            mth = months[sub]
            # 定义性特征：|簇心| 最大的**非罪名**列（罪名在同一罪名内是常量，不算）
            cand = [j for j in np.argsort(-np.abs(z)) if not is_charge_col[j]][:6]
            defining = [{
                "feature": columns[j],
                "label": column_label(columns[j], schema),
                "z": float(z[j]),
                "direction": "高于平均" if z[j] > 0 else "低于平均",
                "typical": _typical_value(columns[j], float(X_raw[sub, j].mean())),
            } for j in cand]
            archetypes.append({
                "id": aid,
                "charge": ch,
                "size": int(len(sub)),
                "months": {"mean": float(mth.mean()), "median": float(np.median(mth)),
                           "min": float(mth.min()), "max": float(mth.max())},
                "defining": defining,
                "centroid_std": z.tolist(),
            })
            aid += 1

    # 全局重要性：跨全部原型的簇间方差占比（簇心加权方差）
    cents = np.array([a["centroid_std"] for a in archetypes])
    sizes = np.array([a["size"] for a in archetypes])
    weights = sizes / sizes.sum()
    between_var = (weights[:, None] * cents ** 2).sum(axis=0)  # 标准化后总均值≈0
    global_importance = [
        {"feature": columns[j], "label": column_label(columns[j], schema),
         "score": float(between_var[j])}
        for j in np.argsort(-between_var)
    ]

    archetypes.sort(key=lambda a: (a["charge"], a["months"]["median"]))

    model = {
        "columns": columns,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "n_archetypes": len(archetypes),
        "silhouette_mean": float(np.mean(sils)),
        "global_importance": global_importance,
        "archetypes": archetypes,
        "n_samples": int(len(results)),
    }
    if save:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(MODEL_PATH, "w", encoding="utf-8") as fh:
            json.dump(model, fh, ensure_ascii=False, indent=2)
    return model


def _typical_value(col, raw_mean):
    """把某列在簇内的原始均值翻译成人话。"""
    if col.startswith("num:"):
        return f"约 {math.exp(raw_mean):,.0f}" if raw_mean else "多为缺失"
    if col.startswith("charge="):
        return f"{raw_mean*100:.0f}% 为该罪名"
    if col.startswith("cat:"):
        return f"{raw_mean*100:.0f}% 命中"
    return f"{raw_mean*100:.0f}% 具备此情节"  # bool


def load_model():
    with open(MODEL_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def nearest_archetype(model, extraction):
    """把一条(可能不完整的)案件匹配到最近的案件原型：先按罪名圈定候选，
    再只在**已知维度**上比距离（避免用缺失维=0 误导匹配）。"""
    vec, known = vectorize(extraction, model["columns"])
    z = (vec - np.array(model["scaler_mean"])) / np.array(model["scaler_scale"])

    charge = extraction.get("charge")
    cands = [a for a in model["archetypes"] if a["charge"] == charge] \
        or model["archetypes"]
    best = None
    for a in cands:
        diff = (np.array(a["centroid_std"]) - z) * known
        d = float(np.linalg.norm(diff))
        if best is None or d < best[1]:
            best = (a, d)
    return best


# --- 打印 -------------------------------------------------------------------
def print_model(model):
    print(f"  样本数={model['n_samples']}  共发现 {model['n_archetypes']} 个案件原型"
          f"（各罪名内聚类，平均轮廓系数={model['silhouette_mean']:.3f}）")
    print("\n  全局因子重要性排序（原型间区分度，越大越是划分原型的关键因子）:")
    for i, item in enumerate(model["global_importance"][:10], 1):
        print(f"    {i:>2}. {item['label']:<22} 区分度={item['score']:.3f}")
    print("\n  案件原型（按罪名 + 典型刑期中位数排序）:")
    for a in model["archetypes"]:
        m = a["months"]
        print(f"\n    ▸ 原型#{a['id']} [{a['charge']}]  规模 {a['size']} 例"
              f"  典型刑期 中位 {m['median']:.0f} 月 / 区间 {m['min']:.0f}~{m['max']:.0f} 月")
        for d in a["defining"][:4]:
            print(f"        · {d['label']:<20} {d['direction']}(z={d['z']:+.2f})  典型：{d['typical']}")
