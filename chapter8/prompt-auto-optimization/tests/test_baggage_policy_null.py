import json

from airline_env import _run_tool


def test_baggage_policy_null_cabin():
    # 模型显式传 {"cabin": null}：应回退到经济舱默认，而不是 TypeError
    args = json.loads('{"cabin": null}')
    result = json.loads(_run_tool("get_baggage_policy", args))
    assert result["cabin"] == "经济舱"
    assert result["free_allowance"] == "20kg"


def test_baggage_policy_missing_cabin():
    result = json.loads(_run_tool("get_baggage_policy", {}))
    assert result["cabin"] == "经济舱"
    assert result["free_allowance"] == "20kg"


def test_baggage_policy_business_cabin():
    result = json.loads(_run_tool("get_baggage_policy", {"cabin": "商务舱"}))
    assert result["free_allowance"] == "30kg"
