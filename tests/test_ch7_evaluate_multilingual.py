"""Unit tests for chapter7/MultilingualReasoning/evaluate_multilingual.py."""

from pathlib import Path
import sys

# Ensure chapter7/MultilingualReasoning is in sys.path
ch7_dir = Path(__file__).resolve().parent.parent / "chapter7" / "MultilingualReasoning"
if str(ch7_dir) not in sys.path:
    sys.path.insert(0, str(ch7_dir))

from evaluate_multilingual import (
    MultilingualReasoningEvaluator,
    normalize_language,
    run_evaluation,
)


def test_normalize_language():
    assert normalize_language("en") == "English"
    assert normalize_language("SPANISH") == "Spanish"
    assert normalize_language("fr") == "French"
    assert normalize_language("zh") == "Chinese"
    assert normalize_language("ja") == "Japanese"
    assert normalize_language("German") == "German"


def test_cot_fidelity_scoring():
    evaluator = MultilingualReasoningEvaluator()

    # Chinese CoT fidelity
    zh_cot = "首先计算第一步：因为 2 + 2 = 4，所以结论是 4。"
    assert evaluator.evaluate_cot_fidelity(zh_cot, "Chinese") > 0.8

    # Japanese CoT fidelity (contains Hiragana and CJK)
    ja_cot = "ステップ1：2 + 2 = 4 なので、答えは 4 です。"
    assert evaluator.evaluate_cot_fidelity(ja_cot, "Japanese") > 0.8

    # Spanish CoT fidelity
    es_cot = "Paso 1: Porque 2 + 2 es igual a 4, entonces la respuesta es 4."
    assert evaluator.evaluate_cot_fidelity(es_cot, "Spanish") > 0.5

    # French CoT fidelity
    fr_cot = "Étape 1: Parce que 2 + 2 est égal à 4, donc la réponse est 4."
    assert evaluator.evaluate_cot_fidelity(fr_cot, "French") > 0.5

    # English CoT fidelity
    en_cot = "Step 1: Because 2 + 2 equals 4, therefore the answer is 4."
    assert evaluator.evaluate_cot_fidelity(en_cot, "English") > 0.7

    # Cross-lingual leakage (Chinese text evaluated as English fidelity)
    assert evaluator.evaluate_cot_fidelity(zh_cot, "English") == 0.0


def test_evaluate_accuracy():
    evaluator = MultilingualReasoningEvaluator()

    assert evaluator.evaluate_accuracy("42", "42") == 1.0
    assert evaluator.evaluate_accuracy("42.0", "42") == 1.0
    assert evaluator.evaluate_accuracy("The answer is 42.", "42") == 1.0
    assert evaluator.evaluate_accuracy("Paris", "paris!") == 1.0
    assert evaluator.evaluate_accuracy("Wrong", "42") == 0.0


def test_evaluator_sample_formats():
    evaluator = MultilingualReasoningEvaluator()

    # Mock model returning string with <think> tag
    def string_model(prompt, language="English"):
        return "<think>Step 1: Reasoning here.</think> 42"

    sample = {
        "language": "en",
        "prompt": "What is 40 + 2?",
        "reference_answer": "42",
    }
    res = evaluator.evaluate_sample(string_model, sample)
    assert res["language"] == "English"
    assert res["accuracy"] == 1.0
    assert res["reasoning"] == "Step 1: Reasoning here."
    assert res["predicted_answer"] == "42"

    # Mock model returning dict
    def dict_model(prompt, language="Spanish"):
        return {
            "reasoning": "Paso 1: Razonamiento en español.",
            "answer": "42",
            "token_usage": {"prompt_tokens": 10, "completion_tokens": 20, "reasoning_tokens": 15, "total_tokens": 30},
        }

    sample_es = {
        "target_language": "Spanish",
        "question": "¿Cuánto es 40 + 2?",
        "ground_truth": "42",
    }
    res_es = evaluator.evaluate_sample(dict_model, sample_es)
    assert res_es["language"] == "Spanish"
    assert res_es["accuracy"] == 1.0
    assert res_es["token_usage"]["total_tokens"] == 30


def test_run_evaluation_end_to_end():
    dataset = [
        {"language": "en", "prompt": "What is 2+2?", "reference_answer": "4"},
        {"language": "es", "prompt": "¿Cuánto es 2+2?", "reference_answer": "4"},
        {"language": "fr", "prompt": "Combien font 2+2?", "reference_answer": "4"},
        {"language": "zh", "prompt": "2+2等于多少？", "reference_answer": "4"},
        {"language": "ja", "prompt": "2+2はいくらですか？", "reference_answer": "4"},
    ]

    def mock_multilingual_model(prompt, language="English"):
        responses = {
            "English": "<think>Step 1: Add numbers.</think> 4",
            "Spanish": "<think>Paso 1: Sumar números, entonces es 4.</think> 4",
            "French": "<think>Étape 1: Additionner donc c'est 4.</think> 4",
            "Chinese": "<think>第一步：因为 2+2=4，所以是 4。</think> 4",
            "Japanese": "<think>ステップ1：2+2=4 なので 4 です。</think> 4",
        }
        return responses.get(language, "<think>Step 1</think> 4")

    report = run_evaluation(mock_multilingual_model, dataset)

    assert report["num_samples"] == 5
    assert report["overall_accuracy"] == 1.0
    assert report["overall_cot_fidelity"] > 0.6
    assert report["overall_transfer_efficiency"] == 1.0
    assert "English" in report["by_language"]
    assert "Spanish" in report["by_language"]
    assert "French" in report["by_language"]
    assert "Chinese" in report["by_language"]
    assert "Japanese" in report["by_language"]
    assert report["total_token_usage"]["total_tokens"] > 0


def test_run_evaluation_empty_dataset():
    report = run_evaluation(lambda p: "42", [])
    assert report["num_samples"] == 0
    assert report["overall_accuracy"] == 0.0
    assert report["by_language"] == {}
