"""Null glossary from Glossary Agent must behave like empty list."""

import agents


def test_glossary_agent_null_glossary_like_empty():
    def fake_llm_chat(client, tracker, agent, messages, json_mode=False, note=""):
        tracker.record(agent, 10, 5, note)
        return '{"glossary": null}'

    agents.llm_chat = fake_llm_chat
    assert agents.glossary_agent(None, agents.TokenTracker(), "book") == []


def test_orchestration_tolerates_null_glossary(tmp_path):
    def fake_llm_chat(client, tracker, agent, messages, json_mode=False, note=""):
        tracker.record(agent, 10, 5, note)
        if agent == "Glossary":
            return '{"glossary": null}'
        return "译文"

    agents.get_client = lambda: object()
    agents.llm_chat = fake_llm_chat
    result = agents.run_orchestration(
        {"Chapter 1": "token embedding"},
        str(tmp_path),
        enable_glossary=True,
        enable_proofreading=False,
    )
    assert isinstance(result["glossary"], list)
    for g in result["glossary"]:
        assert isinstance(g["en"], str) and g["en"].strip()
    assert result["translations"]["Chapter 1"] == "译文"
