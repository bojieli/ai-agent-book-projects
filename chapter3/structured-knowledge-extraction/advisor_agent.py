"""
阶段 4：对话式量刑建议 Agent。

把「案件原型 + 层次因子重要性」当决策逻辑来用：
  1. 从用户口语描述里抽取已知因子（复用抽取器，含罪名判定）；
  2. 按**全局因子重要性顺序**，找出仍缺失、但很重要的因子，生成引导性追问；
  3. 信息补全后，把案件**匹配到最近的案件原型**；
  4. 用 LLM 把该原型的统计数据（典型刑期区间、定义性关键因子）组织成一段
     有判例支持、可解释的中文建议（附法律免责声明）。

所有刑期数字都来自原型统计，LLM 只负责"把数字讲清楚"，不自行编造。
"""
from config import MODEL, get_client
from archetypes import nearest_archetype
from discovery import all_factors

DISCLAIMER = (
    "【免责声明】本回答由教学实验中的统计模型自动生成，仅用于演示"
    "『从结构化数据中提取隐性知识』这一技术，不构成任何法律意见。真实案件量刑受"
    "法律条文、司法解释、地域与具体情节等大量因素影响，请务必咨询专业律师。"
)


class LegalAdvisorAgent:
    def __init__(self, schema, model):
        self.schema = schema
        self.model = model  # archetypes.fit() 产出的模型
        self.client = get_client()
        self._factor = {f["key"]: f for f in all_factors(schema)}

    # --- 步骤 1：抽取已知因子 ---
    def extract_known(self, case_text):
        from extractor import extract_one
        return extract_one(case_text, schema=self.schema, client=self.client)

    # --- 步骤 2：按全局重要性顺序，追问缺失的重要因子 ---
    def missing_important_questions(self, known):
        questions, asked = [], set()
        for item in self.model["global_importance"]:
            col = item["feature"]
            # 从列名解析出因子 key（跳过罪名维——已判定）
            if col.startswith("charge="):
                continue
            key = col.split(":", 1)[1].split("=", 1)[0]
            if key in asked or key not in known:
                continue
            if known.get(key) is None:  # 该因子适用于本罪名但用户尚未提供
                f = self._factor.get(key, {})
                questions.append({
                    "factor": key,
                    "name_cn": f.get("name_cn", key),
                    "importance": item["score"],
                    "question": f.get("question") or f"请补充：{f.get('name_cn', key)}？",
                })
                asked.add(key)
        return questions

    # --- 步骤 3+4：匹配最近原型并给出建议 ---
    def advise(self, known):
        matched = nearest_archetype(self.model, known)
        # fit() can return n_archetypes=0 when every charge has too few samples to cluster.
        if matched is None:
            raise ValueError("模型中没有可用案件原型，无法给出量刑建议（样本过少无法聚类）")
        arch, dist = matched
        m = arch["months"]
        defining = "；".join(
            f"{d['label']}（{d['direction']}，典型 {d['typical']}）"
            for d in arch["defining"][:4]
        )
        evidence = (
            f"- 命中案件原型 #{arch['id']}（{arch['charge']}，该原型含 {arch['size']} 例），"
            f"匹配距离 {dist:.2f}\n"
            f"- 该原型典型刑期：中位 {m['median']:.0f} 个月，区间 {m['min']:.0f}~{m['max']:.0f} 个月\n"
            f"- 定义该原型的关键因子：{defining}"
        )
        known_desc = self._describe_known(known)

        system = (
            "你是一名严谨的司法数据分析助手。下面给出一个数据驱动模型把某案件匹配到的"
            "『案件原型』及其统计数据（数字均来自模型，不得改动）。请用中文写一段 160 字"
            "以内、条理清晰的量刑参考：先说明命中的原型及其典型刑期区间，再点明本案与该"
            "原型共有的关键因子如何影响结果。不要编造模型未给出的数字，不要给确定性承诺，"
            "不要重复免责声明（系统会另附）。"
        )
        user = f"本案已知因子：\n{known_desc}\n\n模型匹配依据：\n{evidence}"
        resp = self.client.chat.completions.create(
            model=MODEL, temperature=0.3,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return arch, resp.choices[0].message.content.strip() + "\n\n" + DISCLAIMER

    def _describe_known(self, known):
        parts = [f"罪名：{known.get('charge')}"]
        for key, v in known.items():
            if key == "charge":
                continue
            f = self._factor.get(key, {})
            if v is None:
                tag = "未知"
            elif isinstance(v, bool):
                tag = "是" if v else "否"
            else:
                tag = str(v)
            parts.append(f"{f.get('name_cn', key)}：{tag}")
        return "\n".join("  " + p for p in parts)
