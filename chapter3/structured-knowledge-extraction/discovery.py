"""
阶段 1：自下而上的因子发现（bottom-up factor discovery）。

不预先定义任何僵化的数据模式，而是：
  1. 把判例文本分批喂给 LLM，让它**自由列出**每一批案例中所有可能影响判决的因素；
  2. 汇总各批发现的原始因子，再用一次 LLM 调用做**归并与规范化**，产出一个
     「模块化数据模式」：
        - core        —— 适用于所有罪名的通用因子（自首、赔偿、认罪、前科……）；
        - extensions  —— 各罪名特有的扩展因子（盗窃→涉案金额/入户；伤害→伤害等级……）。

产出的 schema 落盘到 data/schema.json，供后续抽取 / 聚类 / 对话三段复用。
schema 里每个因子含：key（英文）、name_cn、kind(numeric/bool/categorical)、
values(categorical 取值)、direction(aggravating/mitigating/neutral)、question(引导性追问)。
"""
import json
import os

from config import MODEL, get_client

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SCHEMA_PATH = os.path.join(DATA_DIR, "schema.json")

_BATCH_SYS = """你是协助司法数据分析的专家。下面给你若干条刑事判决书的「事实」段落。
请你**自由归纳**出其中所有可能影响法院量刑/判决的因素（不要局限于任何预设清单）。
对每个因素给出：
  - key: 简短英文 snake_case 标识
  - name_cn: 中文名
  - charge: 该因素主要适用的罪名（若各类案件通用则填 "通用"）
  - kind: numeric（数值，如金额/人数）| bool（是非情节）| categorical（多取值，如伤害等级）
  - values: 若 kind 为 categorical，列出观察到的取值数组；否则为空数组
只输出 JSON：{"factors": [ {factor...}, ... ]}"""

_CONSOLIDATE_SYS = """你是司法数据建模专家。下面是从多批判例中分别发现的**原始因子清单**
（可能有重复、同义、命名不一致）。请把它们**归并、去重、规范化**成一个模块化数据模式：
  - core: 适用于所有罪名的通用因子（如自首、赔偿谅解、认罪认罚、前科累犯）
  - extensions: 一个对象，键为罪名（如 "盗窃罪"/"故意伤害罪"/"诈骗罪"），值为该罪名特有的因子数组
规范化要求：
  - 合并同义因子（如"自首/主动投案"、"认罪认罚/认罪/如实供述"、"赔偿/退赔/退赃"、
    "累犯/前科"、同一罪名下的"涉案金额/物品价值/诈骗金额"只保留一个），
    每组只保留一个最清晰的 key 与中文名；
  - 剔除与量刑无实质关系的因素（如被告人性别、案发地点这类描述性信息）;
  - "是否否认指控/辩称正当防卫"这类与"认罪认罚"互为反面的，不要重复保留。
每个因子输出字段：
  key, name_cn, kind(numeric|bool|categorical), values(categorical 的取值数组，否则[]),
  direction(aggravating 从重 | mitigating 从轻 | neutral 中性),
  question(当该因子缺失时，向当事人提出的一句中文引导性问题)
只输出 JSON：{"core": [...], "extensions": {"罪名": [...], ...}}"""


def _chat_json(client, system, user):
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except json.JSONDecodeError:
        return {}


def discover_schema(cases, batch_size=12, use_cache=True, verbose=True):
    """自下而上发现因子并归并成模块化 schema。带磁盘缓存（避免重复花钱）。"""
    if use_cache and os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, encoding="utf-8") as fh:
            if verbose:
                print(f"  命中缓存 schema -> {SCHEMA_PATH}")
            return json.load(fh)

    client = get_client()

    # --- 第 1 步：分批自由发现 ---
    raw_factors = []
    for start in range(0, len(cases), batch_size):
        batch = cases[start:start + batch_size]
        facts = "\n\n".join(f"[案例{start + j + 1}]（{c['charge']}）{c['fact']}"
                            for j, c in enumerate(batch))
        out = _chat_json(client, _BATCH_SYS, facts)
        got = out.get("factors", [])
        raw_factors.extend(got)
        if verbose:
            print(f"  批次 {start // batch_size + 1}：发现 {len(got)} 个候选因子")

    # --- 第 2 步：归并 / 规范化成模块化 schema ---
    if verbose:
        print(f"  汇总 {len(raw_factors)} 个原始因子，做归并与规范化 ...")
    schema = _chat_json(client, _CONSOLIDATE_SYS,
                        "原始因子清单：\n" + json.dumps(raw_factors, ensure_ascii=False))
    schema.setdefault("core", [])
    schema.setdefault("extensions", {})

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SCHEMA_PATH, "w", encoding="utf-8") as fh:
        json.dump(schema, fh, ensure_ascii=False, indent=2)
    if verbose:
        print(f"  发现的模块化 schema 已保存 -> {SCHEMA_PATH}")
    return schema


# --- schema 便捷访问 ---------------------------------------------------------
def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def factors_for_charge(schema, charge):
    """返回某罪名适用的因子列表：核心通用因子 + 该罪名扩展因子（按 key 去重）。"""
    seen, out = set(), []
    for f in schema.get("core", []) + schema.get("extensions", {}).get(charge, []):
        if f["key"] in seen:  # 去重：某因子同时落在 core 和扩展里时只保留一次
            continue
        seen.add(f["key"])
        out.append(f)
    return out


def all_factors(schema):
    """全部因子（core + 所有扩展），按 key 去重。"""
    seen, out = set(), []
    lists = [schema.get("core", [])] + list(schema.get("extensions", {}).values())
    for lst in lists:
        for f in lst:
            if f["key"] in seen:
                continue
            seen.add(f["key"])
            out.append(f)
    return out


def print_schema(schema):
    print("  核心通用因子 (core):")
    for f in schema.get("core", []):
        vals = f"={f['values']}" if f.get("values") else ""
        print(f"    - {f['key']:<16} {f['name_cn']}  [{f['kind']}{vals}] {f.get('direction','')}")
    for charge, lst in schema.get("extensions", {}).items():
        print(f"  扩展因子 · {charge}:")
        for f in lst:
            vals = f"={f['values']}" if f.get("values") else ""
            print(f"    - {f['key']:<16} {f['name_cn']}  [{f['kind']}{vals}] {f.get('direction','')}")
