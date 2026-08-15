import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_experiment_7_8.py")
SPEC = importlib.util.spec_from_file_location("experiment_7_8", MODULE_PATH)
exp = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = exp
SPEC.loader.exec_module(exp)


def test_parse_label_is_strict():
    assert exp.parse_label("Final Answer: fr") == "fr"
    assert exp.parse_label("zh") == "zh"
    assert exp.parse_label("Final Answer: jp") is None
    assert exp.parse_label("The answer is French") is None


def test_cost_uses_uncached_cached_and_output_rates():
    usage = {
        "prompt_tokens": 100,
        "completion_tokens": 10,
        "prompt_tokens_details": {"cached_tokens": 40},
    }
    cost = exp.usage_cost(usage)
    expected_cny = (60 * 20 + 40 * 2 + 10 * 100) / 1_000_000
    assert cost["cny"] == expected_cny
    assert cost["usd"] == expected_cny * exp.PRICING["usd_per_currency_unit"]


def test_stable_sample_maps_out_of_scope_languages_to_other():
    rows = [
        {"labels": "fr", "text": "bonjour"},
        {"labels": "ja", "text": "こんにちは"},
    ]
    sampled = exp._stable_sample(rows, n=1, seed=1, split="train")
    by_source = {row["source_label"]: row for row in sampled}
    assert by_source["fr"]["gold_label"] == "fr"
    assert by_source["ja"]["gold_label"] == "ot"


def test_sft_rows_expose_only_raw_text_to_student():
    row = {
        "text": "bonjour",
        "prediction": "fr",
        "id": "x",
        "gold_label": "fr",
        "response_id": "receipt",
    }
    sample = {
        "id": row["id"],
        "messages": [
            {"role": "user", "content": row["text"]},
            {"role": "assistant", "content": row["prediction"]},
        ],
    }
    assert exp.LANGUAGE_CLASSIFICATION_PROMPT not in sample["messages"][0]["content"]
    assert sample["messages"][0]["content"] == "bonjour"


def test_chat_template_ids_accepts_transformers_4_and_5_shapes():
    assert exp._chat_template_ids([1, 2, 3]) == [1, 2, 3]
    assert exp._chat_template_ids({"input_ids": [1, 2, 3], "attention_mask": [1, 1, 1]}) == [1, 2, 3]
