import json

from run_experiment import normalize_tool_call, parse_tool_calls, sha256_text


def test_parse_multiple_raw_tool_calls():
    raw = (
        '<tool_call>\n{"name":"get_current_time","arguments":{"city":"Vancouver"}}\n</tool_call>'
        '<tool_call>\n{"name":"get_weather","arguments":{"city":"Vancouver"}}\n</tool_call>'
    )
    calls = parse_tool_calls(raw)
    assert [item["name"] for item in calls] == ["get_current_time", "get_weather"]


def test_normalize_small_model_city_arguments():
    time_call = normalize_tool_call(
        {"name": "get_current_time", "arguments": {"city": "Vancouver"}}
    )
    weather_call = normalize_tool_call(
        {"name": "get_weather", "arguments": {"city": "Vancouver"}}
    )
    assert time_call == {
        "name": "get_current_time",
        "arguments": {"timezone": "America/Vancouver"},
    }
    assert weather_call == {
        "name": "get_current_temperature",
        "arguments": {"location": "Vancouver, Canada", "unit": "celsius"},
    }


def test_normalize_does_not_hide_an_explicitly_wrong_timezone():
    call = normalize_tool_call(
        {"name": "get_current_time", "arguments": {"timezone": "America/New_York"}}
    )
    assert call["arguments"]["timezone"] == "America/New_York"


def test_protocol_is_valid_json_and_hashable():
    raw = b'{"experiment_id":"2-1"}'
    assert json.loads(raw)["experiment_id"] == "2-1"
    assert len(sha256_text(raw.decode())) == 64
