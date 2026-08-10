"""Multilingual Reasoning Evaluator for AI Agent Book (Chapter 7).

Evaluates LLM reasoning models across multiple languages (English, Spanish,
French, Chinese, Japanese) measuring CoT language fidelity, task accuracy,
token usage, and cross-lingual transfer efficiency.
"""

from __future__ import annotations

import inspect
import math
import re
import statistics
import warnings
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

LANG_MAP: dict[str, str] = {
    "en": "English",
    "english": "English",
    "es": "Spanish",
    "spanish": "Spanish",
    "fr": "French",
    "french": "French",
    "zh": "Chinese",
    "chinese": "Chinese",
    "zh-cn": "Chinese",
    "zh-tw": "Chinese",
    "ja": "Japanese",
    "japanese": "Japanese",
    "de": "German",
    "german": "German",
    "it": "Italian",
    "italian": "Italian",
    "pt": "Portuguese",
    "portuguese": "Portuguese",
    "ru": "Russian",
    "russian": "Russian",
    "ko": "Korean",
    "korean": "Korean",
    "ar": "Arabic",
    "arabic": "Arabic",
    "hi": "Hindi",
    "hindi": "Hindi",
    "nl": "Dutch",
    "dutch": "Dutch",
    "tr": "Turkish",
    "turkish": "Turkish",
}

# Regex patterns for script detection
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
HIRAGANA_RE = re.compile(r"[\u3040-\u309f]")
KATAKANA_RE = re.compile(r"[\u30a0-\u30ff]")
SPANISH_SPECIAL_RE = re.compile(r"[áéíóúüñÁÉÍÓÚÜÑ¿¡]")
FRENCH_SPECIAL_RE = re.compile(r"[éèêëàâùûçôîïÉÈÊËÀÂÙÛÇÔÎÏ]")

SPANISH_WORDS = {
    "el", "la", "los", "las", "un", "una", "de", "en", "que", "es", "por", "para",
    "con", "del", "al", "como", "más", "mas", "pero", "sus", "porque", "entonces",
    "paso", "respuesta", "solucion", "solución", "por lo tanto", "primero", "luego"
}

FRENCH_WORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "en", "et", "est", "que",
    "qui", "pour", "dans", "ce", "sur", "avec", "plus", "par", "mais", "donc",
    "parce que", "alors", "etape", "étape", "reponse", "réponse", "solution", "premièrement"
}

ENGLISH_WORDS = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "it", "for",
    "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his",
    "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my",
    "one", "all", "would", "there", "their", "what", "so", "up", "out", "if",
    "about", "who", "get", "which", "go", "me", "when", "make", "can", "like",
    "time", "no", "just", "him", "know", "take", "people", "into", "year",
    "your", "good", "some", "could", "them", "see", "other", "than", "then",
    "now", "look", "only", "come", "its", "over", "think", "also", "back",
    "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most",
    "us", "therefore", "step", "reasoning", "solution", "answer", "equals",
    "is", "plus", "minus", "times", "divided", "equal", "result"
}


def normalize_language(lang: str) -> str:
    """Normalize language identifier string to canonical English name."""
    cleaned = str(lang).strip().lower()
    canonical = LANG_MAP.get(cleaned)
    if canonical is not None:
        return canonical
    # Unknown language: title-case for consistent multi-word names and warn
    # so callers notice silent filtering in evaluate().
    title_cased = cleaned.title()
    warnings.warn(
        f"Unrecognized language identifier {lang!r}; normalized to {title_cased!r}. "
        f"Add it to LANG_MAP for reliable matching.",
        stacklevel=2,
    )
    return title_cased


def estimate_tokens(text: str) -> int:
    """Estimate token count for a string if exact count is unavailable."""
    if not text:
        return 0
    cjk_count = len(CJK_RE.findall(text)) + len(HIRAGANA_RE.findall(text)) + len(KATAKANA_RE.findall(text))
    non_cjk_text = CJK_RE.sub(" ", HIRAGANA_RE.sub(" ", KATAKANA_RE.sub(" ", text)))
    words = non_cjk_text.split()
    # ~1.3 tokens per word for Latin scripts, ~1.5 tokens per character for CJK/Kana
    return max(1, int(len(words) * 1.3 + cjk_count * 1.5))
def _extract_token_counts(tu: Any) -> Optional[dict[str, Optional[int]]]:
    if tu is None:
        return None

    def get_val(key1: str, key2: Optional[str] = None) -> Optional[int]:
        val = None
        if isinstance(tu, dict):
            val = tu.get(key1)
            if val is None and key2:
                val = tu.get(key2)
        else:
            val = getattr(tu, key1, None)
            if val is None and key2:
                val = getattr(tu, key2, None)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        return None

    p_tok = get_val("prompt_tokens", "input_tokens")
    c_tok = get_val("completion_tokens", "output_tokens")
    r_tok = get_val("reasoning_tokens")
    t_tok = get_val("total_tokens")

    if any(x is not None for x in (p_tok, c_tok, r_tok, t_tok)):
        return {
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "reasoning_tokens": r_tok,
            "total_tokens": t_tok,
        }
    return None


def _accepts_language(fn: Any) -> bool:
    try:
        sig = inspect.signature(fn)
        for param in sig.parameters.values():
            if param.name == "language" or param.kind == inspect.Parameter.VAR_KEYWORD:
                return True
        return False
    except (ValueError, TypeError):
        return False


class MultilingualReasoningEvaluator:
    """Evaluates reasoning LLMs across multiple languages.

    Computes:
    - CoT Language Fidelity Score: Consistency of reasoning steps with target language.
    - Task Accuracy: Correctness of final generated answers.
    - Token Usage: Breakdown of prompt, completion, and reasoning token costs.
    - Cross-Lingual Transfer Efficiency: Relative performance across non-English languages.
    """

    def __init__(self, target_languages: Optional[Sequence[str]] = None) -> None:
        if target_languages is None:
            self.target_languages = ["English", "Spanish", "French", "Chinese", "Japanese"]
        else:
            self.target_languages = [normalize_language(lang) for lang in target_languages]

    def evaluate_cot_fidelity(self, cot_text: str, target_language: str) -> float:
        """Calculate language fidelity score (0.0 - 1.0) for Chain-of-Thought text."""
        if not cot_text or not cot_text.strip():
            return 0.0

        lang = normalize_language(target_language)
        text = cot_text.strip()
        non_space_chars = len(re.sub(r"\s+", "", text))
        if non_space_chars == 0:
            return 0.0

        cjk_count = len(CJK_RE.findall(text))
        hiragana_count = len(HIRAGANA_RE.findall(text))
        katakana_count = len(KATAKANA_RE.findall(text))
        kana_count = hiragana_count + katakana_count

        if lang == "Chinese":
            if kana_count > 0:
                cjk_ratio = cjk_count / non_space_chars
                return max(0.0, min(1.0, cjk_ratio / 0.3) * 0.7)
            cjk_ratio = cjk_count / non_space_chars
            return min(1.0, cjk_ratio / 0.35)

        if lang == "Japanese":
            if kana_count > 0:
                j_ratio = (kana_count + cjk_count) / non_space_chars
                return min(1.0, j_ratio / 0.35)
            if cjk_count > 0:
                return 0.4
            return 0.0

        # For European / Latin languages, CJK/Kana script implies cross-lingual leakage
        if cjk_count > 0 or kana_count > 0:
            return 0.0

        words = [w.lower() for w in re.findall(r"\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑàâäèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ]+\b", text)]
        total_words = len(words)
        if total_words == 0:
            return 1.0 if any(c.isalnum() for c in text) else 0.0

        if lang == "Spanish":
            special_count = len(SPANISH_SPECIAL_RE.findall(text))
            spanish_word_matches = sum(1 for w in words if w in SPANISH_WORDS)
            score = (special_count * 2 + spanish_word_matches) / max(1, total_words)
            return min(1.0, max(0.2, score * 3.0))

        if lang == "French":
            special_count = len(FRENCH_SPECIAL_RE.findall(text))
            french_word_matches = sum(1 for w in words if w in FRENCH_WORDS)
            score = (special_count * 2 + french_word_matches) / max(1, total_words)
            return min(1.0, max(0.2, score * 3.0))

        if lang == "English":
            english_word_matches = sum(1 for w in words if w in ENGLISH_WORDS)
            french_special = len(FRENCH_SPECIAL_RE.findall(text))
            spanish_special = len(SPANISH_SPECIAL_RE.findall(text))
            penalty = (french_special + spanish_special) * 0.1
            match_ratio = english_word_matches / max(1, total_words)
            score = match_ratio * 1.8 - penalty
            return min(1.0, max(0.0, score))
        return 0.5

    def evaluate_accuracy(self, predicted_answer: str, reference_answer: str) -> float:
        """Determine task accuracy (1.0 for match, 0.0 for mismatch)."""
        pred = str(predicted_answer if predicted_answer is not None else "").strip().lower()
        ref = str(reference_answer if reference_answer is not None else "").strip().lower()

        if not pred or not ref:
            return 0.0

        if pred == ref:
            return 1.0

        # Strip common trailing punctuation
        pred_clean = re.sub(r"[.,;!\?]+$", "", pred)
        ref_clean = re.sub(r"[.,;!\?]+$", "", ref)
        if pred_clean == ref_clean:
            return 1.0

        # Try numeric comparison
        pred_nums = re.findall(r"[-+]?\d*\.?\d+", pred)
        ref_nums = re.findall(r"[-+]?\d*\.?\d+", ref)
        if pred_nums and ref_nums:
            try:
                p_val = float(pred_nums[-1])
                r_val = float(ref_nums[-1])
                if math.isclose(p_val, r_val, rel_tol=1e-4, abs_tol=1e-4):
                    return 1.0
            except ValueError:
                pass

        # Substring matching for references with word boundaries
        target_ref = ref_clean if ref_clean else ref
        if target_ref:
            # \b word boundaries don't work for CJK characters; use direct
            # containment for non-ASCII references, and \b for Latin text.
            if re.search(r"[^\x00-\x7f]", target_ref):
                if target_ref in pred_clean or target_ref in pred:
                    return 1.0
            else:
                pattern = r"\b" + re.escape(target_ref) + r"\b"
                if re.search(pattern, pred_clean) or re.search(pattern, pred):
                    return 1.0
        return 0.0

    def compute_token_usage(
        self, prompt: str, reasoning: str, answer: str, model_output: Any = None
    ) -> dict[str, int]:
        """Extract or estimate prompt, completion, reasoning, and total token usage."""
        tu = None
        if isinstance(model_output, dict):
            if "token_usage" in model_output and model_output["token_usage"] is not None:
                tu = model_output["token_usage"]
            else:
                tu = model_output
        elif model_output is not None:
            if hasattr(model_output, "token_usage") and getattr(model_output, "token_usage") is not None:
                tu = getattr(model_output, "token_usage")
            else:
                tu = model_output

        extracted = _extract_token_counts(tu)
        if extracted is not None:
            r_tok = extracted["reasoning_tokens"] if extracted["reasoning_tokens"] is not None else estimate_tokens(reasoning)
            p_tok = extracted["prompt_tokens"] if extracted["prompt_tokens"] is not None else estimate_tokens(prompt)
            c_tok = extracted["completion_tokens"] if extracted["completion_tokens"] is not None else (r_tok + estimate_tokens(answer))
            t_tok = extracted["total_tokens"] if extracted["total_tokens"] is not None else (p_tok + c_tok)
            return {
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "reasoning_tokens": r_tok,
                "total_tokens": t_tok,
            }

        p_tok = estimate_tokens(prompt)
        r_tok = estimate_tokens(reasoning)
        a_tok = estimate_tokens(answer)
        c_tok = r_tok + a_tok
        t_tok = p_tok + c_tok
        return {
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "reasoning_tokens": r_tok,
            "total_tokens": t_tok,
        }

    def _parse_model_output(self, raw_output: Any) -> tuple[str, str, Any]:
        """Parse raw model output into reasoning CoT, final answer, and token metadata."""
        if isinstance(raw_output, dict):
            reasoning = ""
            for k in ("reasoning", "cot", "thinking"):
                if k in raw_output and raw_output[k] is not None:
                    reasoning = str(raw_output[k])
                    break
            answer = ""
            for k in ("answer", "response", "predicted_answer"):
                if k in raw_output and raw_output[k] is not None:
                    answer = str(raw_output[k])
                    break
            tu = raw_output.get("token_usage")
            return reasoning, answer, tu

        if hasattr(raw_output, "reasoning") or hasattr(raw_output, "answer") or hasattr(raw_output, "cot") or hasattr(raw_output, "response") or hasattr(raw_output, "predicted_answer"):
            reasoning = ""
            for attr in ("reasoning", "cot", "thinking"):
                if hasattr(raw_output, attr) and getattr(raw_output, attr) is not None:
                    reasoning = str(getattr(raw_output, attr))
                    break
            answer = ""
            for attr in ("answer", "response", "predicted_answer"):
                if hasattr(raw_output, attr) and getattr(raw_output, attr) is not None:
                    answer = str(getattr(raw_output, attr))
                    break
            tu = getattr(raw_output, "token_usage", None)
            return reasoning, answer, tu

        text = str(raw_output or "").strip()

        # Handle <think>...</think> tags
        if "<think>" in text and "</think>" in text:
            parts = text.split("</think>", 1)
            reasoning = parts[0].replace("<think>", "").strip()
            answer = parts[1].strip()
            return reasoning, answer, {}

        # Handle Reasoning: / Answer: markers
        if "reasoning:" in text.lower() and "answer:" in text.lower():
            r_idx = text.lower().find("reasoning:")
            a_idx = text.lower().find("answer:")
            if r_idx < a_idx:
                reasoning = text[r_idx + 10 : a_idx].strip()
                answer = text[a_idx + 7 :].strip()
                return reasoning, answer, {}

        # If line breaks exist, treat first part as reasoning and last line as answer
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if len(lines) > 1:
            reasoning = "\n".join(lines[:-1])
            answer = lines[-1]
            return reasoning, answer, {}

        return text, text, {}


    def _invoke_model(self, model: Any, prompt: str, language: str) -> Any:
        """Call model using appropriate signature (generate, predict, or call)."""
        if callable(model):
            if _accepts_language(model):
                return model(prompt, language=language)
            return model(prompt)

        if hasattr(model, "generate") and callable(model.generate):
            if _accepts_language(model.generate):
                return model.generate(prompt, language=language)
            return model.generate(prompt)

        if hasattr(model, "predict") and callable(model.predict):
            if _accepts_language(model.predict):
                return model.predict(prompt, language=language)
            return model.predict(prompt)

        raise ValueError(f"Model object {type(model)} is not callable and lacks generate/predict methods.")

    def evaluate_sample(self, model: Any, sample: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a single dataset sample."""
        lang_raw = None
        for k in ("language", "target_language", "lang"):
            if k in sample and sample[k] is not None:
                lang_raw = sample[k]
                break
        language = normalize_language(str(lang_raw) if lang_raw is not None else "English")

        prompt = ""
        for k in ("prompt", "question", "input"):
            if k in sample and sample[k] is not None:
                prompt = str(sample[k])
                break

        reference_answer = ""
        for k in ("reference_answer", "expected_answer", "ground_truth", "target", "answer"):
            if k in sample and sample[k] is not None:
                reference_answer = str(sample[k])
                break

        raw_output = self._invoke_model(model, prompt, language)
        reasoning, answer, tu_raw = self._parse_model_output(raw_output)

        cot_fidelity = self.evaluate_cot_fidelity(reasoning, language)
        accuracy = self.evaluate_accuracy(answer, reference_answer)
        token_usage = self.compute_token_usage(prompt, reasoning, answer, tu_raw or raw_output)

        return {
            "language": language,
            "prompt": prompt,
            "reference_answer": reference_answer,
            "reasoning": reasoning,
            "predicted_answer": answer,
            "cot_fidelity": cot_fidelity,
            "accuracy": accuracy,
            "token_usage": token_usage,
        }

    def compute_transfer_efficiency(self, by_language_metrics: dict[str, dict[str, Any]]) -> dict[str, float]:
        """Calculate cross-lingual transfer efficiency relative to English.

        If English accuracy is missing or zero, the highest per-language accuracy
        becomes the reference. If no positive reference exists, efficiency is 0.0.
        """
        raw_eng = by_language_metrics.get("English") if isinstance(by_language_metrics.get("English"), dict) else {}
        english_acc = (raw_eng.get("accuracy") or 0.0) if raw_eng else 0.0
        positive_accs = [
            m["accuracy"]
            for m in by_language_metrics.values()
            if isinstance(m, dict) and m.get("accuracy") is not None and m.get("accuracy", 0.0) > 0
        ]
        reference_acc = english_acc if english_acc > 0 else (max(positive_accs) if positive_accs else 0.0)

        efficiencies: dict[str, float] = {}
        for lang, metrics in by_language_metrics.items():
            acc = (metrics.get("accuracy") or 0.0) if isinstance(metrics, dict) else 0.0
            if reference_acc > 0:
                efficiencies[lang] = round(acc / reference_acc, 4)
            else:
                efficiencies[lang] = 0.0

        return efficiencies

    def evaluate(self, model: Any, dataset: Sequence[dict[str, Any]]) -> dict[str, Any]:
        """Evaluate model on dataset and compile comprehensive report."""
        def _empty_report() -> dict[str, Any]:
            return {
                "overall_accuracy": 0.0,
                "overall_cot_fidelity": 0.0,
                "overall_transfer_efficiency": 0.0,
                "total_token_usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_tokens": 0,
                },
                "by_language": {},
                "num_samples": 0,
            }

        if not dataset:
            return _empty_report()

        if self.target_languages:
            target_langs = set(self.target_languages)
            dataset = [
                s for s in dataset
                if normalize_language(
                    s.get("language") or s.get("target_language") or s.get("lang") or "English"
                ) in target_langs
            ]

        if not dataset:
            return _empty_report()

        sample_results = []
        for sample in dataset:
            try:
                sample_results.append(self.evaluate_sample(model, sample))
            except Exception as e:
                lang_raw = sample.get("language") or sample.get("target_language") or sample.get("lang") or "English"
                sample_results.append({
                    "language": normalize_language(str(lang_raw)),
                    "prompt": str(sample.get("prompt") or sample.get("question") or sample.get("input") or ""),
                    "reference_answer": str(sample.get("reference_answer") or sample.get("expected_answer") or ""),
                    "reasoning": "",
                    "predicted_answer": "",
                    "cot_fidelity": 0.0,
                    "accuracy": 0.0,
                    "error": str(e),
                    "token_usage": {"prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0, "total_tokens": 0},
                })

        if not sample_results:
            return _empty_report()
        by_lang_samples: dict[str, list[dict[str, Any]]] = {}
        for res in sample_results:
            lang = res["language"]
            by_lang_samples.setdefault(lang, []).append(res)

        by_language_metrics: dict[str, dict[str, Any]] = {}
        tot_p_tokens = 0
        tot_c_tokens = 0
        tot_r_tokens = 0
        tot_t_tokens = 0

        for lang, samples in by_lang_samples.items():
            cnt = len(samples)
            acc = sum(s["accuracy"] for s in samples) / cnt
            fid = sum(s["cot_fidelity"] for s in samples) / cnt

            p_tok = sum(s["token_usage"]["prompt_tokens"] for s in samples)
            c_tok = sum(s["token_usage"]["completion_tokens"] for s in samples)
            r_tok = sum(s["token_usage"]["reasoning_tokens"] for s in samples)
            t_tok = sum(s["token_usage"]["total_tokens"] for s in samples)

            tot_p_tokens += p_tok
            tot_c_tokens += c_tok
            tot_r_tokens += r_tok
            tot_t_tokens += t_tok

            by_language_metrics[lang] = {
                "sample_count": cnt,
                "accuracy": round(acc, 4),
                "cot_fidelity": round(fid, 4),
                "token_usage": {
                    "prompt_tokens": p_tok,
                    "completion_tokens": c_tok,
                    "reasoning_tokens": r_tok,
                    "total_tokens": t_tok,
                },
            }

        transfer_efficiencies = self.compute_transfer_efficiency(by_language_metrics)
        for lang, eff in transfer_efficiencies.items():
            by_language_metrics[lang]["transfer_efficiency"] = eff

        non_english_effs = [
            eff for lang, eff in transfer_efficiencies.items() if lang != "English"
        ]
        overall_transfer_eff = (
            round(sum(non_english_effs) / len(non_english_effs), 4)
            if non_english_effs
            else 1.0
        )

        overall_accuracy = round(sum(s["accuracy"] for s in sample_results) / len(sample_results), 4)
        overall_fidelity = round(sum(s["cot_fidelity"] for s in sample_results) / len(sample_results), 4)

        return {
            "overall_accuracy": overall_accuracy,
            "overall_cot_fidelity": overall_fidelity,
            "overall_transfer_efficiency": overall_transfer_eff,
            "total_token_usage": {
                "prompt_tokens": tot_p_tokens,
                "completion_tokens": tot_c_tokens,
                "reasoning_tokens": tot_r_tokens,
                "total_tokens": tot_t_tokens,
            },
            "by_language": by_language_metrics,
            "num_samples": len(sample_results),
        }


def run_evaluation(
    model: Any, dataset: Sequence[dict[str, Any]], target_languages: Optional[Sequence[str]] = None
) -> dict[str, Any]:
    """Entrypoint function to run multilingual reasoning evaluation."""
    evaluator = MultilingualReasoningEvaluator(target_languages=target_languages)
    return evaluator.evaluate(model, dataset)
