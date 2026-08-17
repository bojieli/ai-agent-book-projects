"""Unit tests for chapter8/MultilingualReasoning/evaluate_multilingual.py."""

from pathlib import Path
import sys
import warnings

# Ensure chapter8/MultilingualReasoning is in sys.path
ch8_dir = Path(__file__).resolve().parent.parent / "chapter8" / "MultilingualReasoning"
if str(ch8_dir) not in sys.path:
    sys.path.insert(0, str(ch8_dir))

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
    assert evaluator.evaluate_accuracy("1042", "42") == 0.0
    assert evaluator.evaluate_accuracy("0", 0) == 1.0

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

    # Test non-falsy zero answer
    sample_zero = {
        "language": "en",
        "prompt": "What is 2 - 2?",
        "reference_answer": 0,
    }
    res_zero = evaluator.evaluate_sample(lambda p: "0", sample_zero)
    assert res_zero["reference_answer"] == "0"
    assert res_zero["accuracy"] == 1.0


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


def test_object_model_and_method_invocations():
    evaluator = MultilingualReasoningEvaluator()

    class CustomOutput:
        def __init__(self):
            self.reasoning = "Step 1: Compute."
            self.answer = "42"
            self.token_usage = {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "reasoning_tokens": 15,
                "total_tokens": 30,
            }

    class GenerateModel:
        def generate(self, prompt, language="English"):
            return CustomOutput()

    class PredictModel:
        def predict(self, prompt):
            return "Reasoning: Simple math\nAnswer: 42"
    sample = {"language": "en", "prompt": "40+2?", "reference_answer": "42"}
    res_gen = evaluator.evaluate_sample(GenerateModel(), sample)
    assert res_gen["accuracy"] == 1.0
    assert res_gen["token_usage"]["total_tokens"] == 30

    res_pred = evaluator.evaluate_sample(PredictModel(), sample)
    assert res_pred["accuracy"] == 1.0


def test_transfer_efficiency_zero_reference():
    evaluator = MultilingualReasoningEvaluator()
    metrics = {
        "English": {"accuracy": 0.0},
        "Spanish": {"accuracy": 0.0},
    }
    eff = evaluator.compute_transfer_efficiency(metrics)
    assert eff["English"] == 0.0
    assert eff["Spanish"] == 0.0


def test_model_exception_and_builtin_callable():
    evaluator = MultilingualReasoningEvaluator()

    def failing_model(prompt):
        raise RuntimeError("Model inference failed")

    dataset = [{"language": "en", "prompt": "test", "reference_answer": "42"}]
    report = evaluator.evaluate(failing_model, dataset)
    assert report["num_samples"] == 1
    assert report["overall_accuracy"] == 0.0
def test_token_usage_object_attributes():
    evaluator = MultilingualReasoningEvaluator()

    class TokenUsageObj:
        def __init__(self, input_tokens=12, output_tokens=24, total_tokens=36):
            self.input_tokens = input_tokens
            self.output_tokens = output_tokens
            self.total_tokens = total_tokens

    class ObjectOutputModel:
        def __init__(self):
            self.token_usage = TokenUsageObj()

        def generate(self, prompt):
            return {"answer": "42", "token_usage": TokenUsageObj(input_tokens=15, output_tokens=30, total_tokens=45)}

    sample = {"language": "en", "prompt": "What is 40+2?", "reference_answer": "42"}
    res = evaluator.evaluate_sample(ObjectOutputModel(), sample)
    assert res["token_usage"]["prompt_tokens"] == 15
    assert res["token_usage"]["completion_tokens"] == 30
    assert res["token_usage"]["total_tokens"] == 45

    # Direct test on compute_token_usage with token usage object
    tu_obj = TokenUsageObj(input_tokens=100, output_tokens=200, total_tokens=300)
    res_direct = evaluator.compute_token_usage("prompt", "reasoning", "answer", model_output=tu_obj)
    assert res_direct["prompt_tokens"] == 100
    assert res_direct["completion_tokens"] == 200
    assert res_direct["total_tokens"] == 300


def test_word_boundary_reference_matching():
    evaluator = MultilingualReasoningEvaluator()
    # Word boundary matching should succeed for full word substring
    assert evaluator.evaluate_accuracy("The answer is Paris.", "Paris") == 1.0
    assert evaluator.evaluate_accuracy("The answer is A", "A") == 1.0
    # Word boundary matching should fail for partial word matching
    assert evaluator.evaluate_accuracy("1042", "42") == 0.0
    assert evaluator.evaluate_accuracy("no", "not paris") == 0.0
    assert evaluator.evaluate_accuracy("apple", "a") == 0.0

def test_invoke_model_inspect_signature():
    evaluator = MultilingualReasoningEvaluator()

    # Function accepting language
    def model_with_lang(prompt, language="English"):
        return f"Response for {language}: {prompt}"

    # Function not accepting language
    def model_without_lang(prompt):
        return f"Response: {prompt}"

    sample = {"language": "Spanish", "prompt": "Hola", "reference_answer": "Hola"}
    res_lang = evaluator.evaluate_sample(model_with_lang, sample)
    assert "Spanish" in res_lang["predicted_answer"]

    res_nolang = evaluator.evaluate_sample(model_without_lang, sample)
    assert "Response: Hola" == res_nolang["predicted_answer"]
def test_zero_answer_handling():
    evaluator = MultilingualReasoningEvaluator()
    sample = {"language": "en", "prompt": "1-1?", "reference_answer": 0}
    model = lambda p: {"answer": 0, "reasoning": "1 minus 1 equals 0"}
    res = evaluator.evaluate_sample(model, sample)
    assert res["predicted_answer"] == "0"
    assert res["reference_answer"] == "0"
    assert res["accuracy"] == 1.0
def test_chinese_cot_fidelity_japanese_kana_penalty():
    evaluator = MultilingualReasoningEvaluator()
    # Chinese CoT containing Japanese kana should be penalized (capped at 0.7)
    cot_with_kana = "第一歩：計算結果、二足す二は四、答案は四。だ"
    score = evaluator.evaluate_cot_fidelity(cot_with_kana, "Chinese")
    assert score == 0.7


def test_transfer_efficiency_none_accuracy():
    evaluator = MultilingualReasoningEvaluator()
    metrics = {
        "English": {"accuracy": None},
        "Spanish": {"accuracy": 0.5},
    }
    eff = evaluator.compute_transfer_efficiency(metrics)
    assert eff["English"] == 0.0
    assert eff["Spanish"] == 1.0


def test_partial_token_usage_reasoning_estimation():
    evaluator = MultilingualReasoningEvaluator()
    tu = {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60}
    res = evaluator.compute_token_usage("prompt", "detailed reasoning step by step", "answer", model_output=tu)
    assert res["prompt_tokens"] == 10
    assert res["completion_tokens"] == 50
    assert res["reasoning_tokens"] > 0
    assert res["total_tokens"] == 60
