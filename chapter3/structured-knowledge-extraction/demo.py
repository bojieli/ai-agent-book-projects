"""
实验 3-12 全流程演示：从司法判例中提取隐性知识。

运行：
    python demo.py

依次执行四个阶段：
  阶段 1  自下而上因子发现：让 LLM 自由归纳因子，归并成模块化 schema（核心+各罪名扩展）；
  阶段 2  结构化抽取：用发现的 schema 从每条判例抽取因子（带缓存）；
  阶段 3  聚类 + 层次重要性：把因子向量聚成「案件原型」，算全局与原型内因子重要性；
  阶段 4  对话式建议 Agent：把新案情匹配到最近原型，按重要性追问缺失因子，给出建议。
"""
import json
import os
import sys

import archetypes
import discovery
from advisor_agent import LegalAdvisorAgent
from extractor import extract_dataset, load_dataset


def section(title):
    print("\n" + "=" * 74)
    print(title)
    print("=" * 74)


def main():
    cases = load_dataset()

    # ---------- 阶段 1：自下而上因子发现 ----------
    section("阶段 1 / 自下而上因子发现（LLM 自由归纳 → 模块化 schema）")
    schema = discovery.discover_schema(cases, batch_size=12, use_cache=True)
    discovery.print_schema(schema)

    # ---------- 阶段 2：结构化抽取 ----------
    section("阶段 2 / 结构化抽取（用发现的 schema 抽取每条判例的因子）")
    results = extract_dataset(schema, use_cache=True, verbose=True)
    print("\n抽取样例（前 2 条）:")
    for r in results[:2]:
        print(f"\n[{r['id']}] {r['fact'][:56]}...")
        print(f"  抽取: {json.dumps(r['extracted'], ensure_ascii=False)}")

    # ---------- 阶段 3：聚类 + 层次重要性 ----------
    section("阶段 3 / 聚类成案件原型 + 层次因子重要性")
    model = archetypes.fit(schema, results, save=True)
    archetypes.print_model(model)
    print(f"\n  模型已保存 -> {os.path.join('data', 'archetypes.json')}")

    # ---------- 阶段 4：对话式量刑建议 Agent ----------
    section("阶段 4 / 对话式量刑建议 Agent（匹配最近原型 + 按重要性追问）")
    agent = LegalAdvisorAgent(schema, model)

    user_turn1 = (
        "我朋友之前因为盗窃被判过刑，这次他撬门进了别人家里偷东西，被抓的时候没反抗。"
        "这种情况大概会判多久？"
    )
    print(f"\n用户: {user_turn1}")
    known = agent.extract_known(user_turn1)
    print(f"\nAgent 已识别因子: {json.dumps(known, ensure_ascii=False)}")

    questions = agent.missing_important_questions(known)
    print("\nAgent 追问（按全局因子重要性排序，只问缺失且重要的）:")
    for q in questions[:5]:
        print(f"  - [{q['name_cn']} 重要度{q['importance']:.3f}] {q['question']}")

    user_turn2 = (
        "补充一下：这次偷的东西价值大概 5 万元，事后他没有退赃，"
        "作案时也没带凶器，是他一个人干的，到了法庭上他认罪认罚了。"
    )
    print(f"\n用户: {user_turn2}")
    known2 = agent.extract_known(user_turn1 + " " + user_turn2)
    print(f"\nAgent 更新后的因子: {json.dumps(known2, ensure_ascii=False)}")

    arch, advice = agent.advise(known2)
    print(f"\nAgent 匹配到 原型#{arch['id']}（典型刑期中位 {arch['months']['median']:.0f} 月）")
    print("\nAgent 量刑建议:\n")
    print(advice)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        print(f"启动失败：{exc}", file=sys.stderr)
        sys.exit(1)


