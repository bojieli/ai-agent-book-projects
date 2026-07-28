"""回归测试：Glossary Agent 返回不合规 JSON 时，run_orchestration 不应崩溃。

覆盖两类模型失误（此前会让整轮管理者模式直接 KeyError/AttributeError）：
  1) glossary 条目缺 en/zh 键、或值为显式 null / 空串 -> 条目被丢弃；
  2) 顶层 JSON 是数组而非对象 -> glossary_agent 返回空表。
不依赖真实 API：llm_chat / get_client 被打桩。
"""

import json

import agents

# 混合各种坏条目的 glossary：错键名 / null / 空串 都应被丢弃，只有合规条目保留。
GLOSSARY_JSON = json.dumps({
    "glossary": [
        {"term": "token", "translation": "词元"},              # 错键名
        {"en": None, "zh": "提示词"},                          # 显式 null
        {"en": "", "zh": "时延"},                              # 空串
        {"en": "attention", "zh": "注意力", "pos": "名词"},     # 合规
    ]
}, ensure_ascii=False)

CHAPTERS = {"Chapter 1: Intro": "# Chapter 1\nSome text about attention."}


def _install_fake_llm(glossary_payload=GLOSSARY_JSON):
    def fake_llm_chat(client, tracker, agent, messages, json_mode=False, note=""):
        tracker.record(agent, 10, 5, note)
        if agent == "Glossary":
            return glossary_payload
        return "译文"
    agents.get_client = lambda: object()
    agents.llm_chat = fake_llm_chat


def test_orchestration_skips_malformed_glossary_entries(tmp_path):
    _install_fake_llm()
    result = agents.run_orchestration(
        CHAPTERS, str(tmp_path), enable_glossary=True, enable_proofreading=False)
    glossary = result["glossary"]
    # 所有存活条目必须是非空 en/zh 字符串（下游 g["en"]/g["zh"] 索引的前提）
    for g in glossary:
        assert isinstance(g["en"], str) and g["en"].strip()
        assert isinstance(g["zh"], str) and g["zh"].strip()
    ens = {g["en"] for g in glossary}
    assert "attention" in ens                       # 合规条目保留
    assert "term" not in ens                        # 错键名条目已丢弃
    for en in agents.EDITORIAL_MANDATE:             # 编辑部指定术语仍会补齐
        assert en in ens
    assert (tmp_path / "glossary.json").exists()    # 产物正常落盘
    assert (tmp_path / "chapter1_zh.md").read_text(encoding="utf-8") == "译文"


def test_glossary_agent_tolerates_json_array():
    _install_fake_llm(glossary_payload='["not", "an", "object"]')
    assert agents.glossary_agent(None, agents.TokenTracker(), "book text") == []


def test_glossary_agent_tolerates_missing_glossary_key():
    _install_fake_llm(glossary_payload='{"terms": []}')
    assert agents.glossary_agent(None, agents.TokenTracker(), "book text") == []
