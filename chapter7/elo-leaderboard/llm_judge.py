"""
LLM-as-judge pairwise battles with position-bias mitigation.

This is the only battle source that needs network access; `simulate` and
`arena` run fully offline.

Two backends are supported, selected automatically or via ``backend=``:

  * ``anthropic``  – the official ``anthropic`` SDK, using ``ANTHROPIC_API_KEY``
    (the default when that key is present).
  * ``openrouter`` – the OpenAI-compatible ``openai`` SDK pointed at
    ``https://openrouter.ai/api/v1`` with ``OPENROUTER_API_KEY``. Internal
    Claude ids (e.g. ``claude-opus-4-8``) are mapped to their OpenRouter ids
    (``anthropic/claude-opus-4.8``); ids that already contain a ``/`` such as
    ``openai/gpt-5.6-luna`` are passed through untouched. This lets the judge run
    when a direct Anthropic key is missing or invalid.

The two backends are interchangeable: the position-bias swap-and-agree logic and
the A/B/tie response parsing are identical regardless of which one is used.

The book (实验 7-7, 位置偏差 discussion) notes that an LLM judge systematically
favours whichever answer appears in a fixed slot (usually the first). The
standard mitigation, implemented here, is to judge each pair twice with the
answers swapped and only record a winner when both judgements agree; a
disagreement is counted as a tie. This cancels the position bias instead of
letting it leak into the ratings.

The resulting battle list uses the same {'model_a', 'model_b', 'winner'} schema
as the simulated and Chatbot Arena data, so it feeds straight into the Elo /
Bradley-Terry pipeline.
"""
import os
from typing import Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Default candidate roster and judge (Claude models). Kept small because every
# battle costs several API calls (two responses + two swapped judgements).
DEFAULT_CANDIDATE_MODELS = ["claude-opus-4-8", "claude-haiku-4-5"]
DEFAULT_JUDGE_MODEL = "claude-opus-4-8"

DEFAULT_PROMPTS = [
    "用一句话解释什么是 Transformer 的自注意力机制。",
    "Write a haiku about distributed systems.",
    "给出快速排序的时间复杂度，并简要说明最坏情况。",
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Map internal Claude ids -> OpenRouter model ids. Any id already containing a
# '/' (e.g. 'openai/gpt-5.6-luna') is treated as a native OpenRouter id and used
# verbatim; unknown ids are also passed through unchanged.
_OPENROUTER_MODEL_MAP = {
    "claude-opus-4-8": "anthropic/claude-opus-4.8",
    "claude-opus-4-1": "anthropic/claude-opus-4.1",
    "claude-sonnet-4-6": "anthropic/claude-sonnet-4.6",
    "claude-sonnet-4-5": "anthropic/claude-sonnet-4.5",
    "claude-haiku-4-5": "anthropic/claude-haiku-4.5",
}

_JUDGE_SYSTEM = (
    "你是一个严格的评委。用户会给你一个问题和两个候选回答（回答 A 和回答 B）。"
    "请只根据回答质量判断哪个更好，忽略它们出现的顺序。"
    "只输出一个词：A、B 或 tie。"
)


def _to_openrouter_model(model: str) -> str:
    """Translate an internal model id into an OpenRouter model id."""
    if "/" in model:  # already a native OpenRouter id
        return model
    return _OPENROUTER_MODEL_MAP.get(model, model)


class JudgeClient:
    """
    Thin adapter over either the Anthropic SDK or the OpenAI-compatible
    OpenRouter endpoint, exposing a single ``chat()`` method so the rest of the
    module is backend-agnostic.
    """

    def __init__(self, backend: str, impl):
        self.backend = backend
        self.impl = impl

    def chat(self, model: str, user: str, max_tokens: int,
             system: Optional[str] = None) -> str:
        """Send a single-turn chat and return the assistant's text reply."""
        if self.backend == "anthropic":
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": user}],
            }
            if system is not None:
                kwargs["system"] = system
            response = self.impl.messages.create(**kwargs)
            return "".join(
                block.text for block in response.content if block.type == "text"
            ).strip()

        # openrouter (OpenAI-compatible chat.completions)
        messages = []
        if system is not None:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        response = self.impl.chat.completions.create(
            model=_to_openrouter_model(model),
            max_tokens=max_tokens,
            messages=messages,
        )
        return (response.choices[0].message.content or "").strip()


def _resolve_backend(backend: str = "auto") -> str:
    """
    Resolve the effective backend.

    ``auto`` -> ``anthropic`` if ANTHROPIC_API_KEY is set, else ``openrouter``
    if OPENROUTER_API_KEY is set. Raises if neither key is available.
    """
    if backend not in ("anthropic", "openrouter", "auto"):
        raise ValueError(
            f"Unknown judge backend {backend!r}; expected 'anthropic', "
            "'openrouter' or 'auto'."
        )
    if backend != "auto":
        return backend
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENROUTER_API_KEY"):
        return "openrouter"
    raise RuntimeError(
        "No LLM-judge credentials found. Set ANTHROPIC_API_KEY (direct Anthropic) "
        "or OPENROUTER_API_KEY (OpenRouter fallback); or use --source simulate / "
        "--source arena to run the experiment fully offline."
    )


def _get_client(backend: str = "auto") -> JudgeClient:
    """Create a JudgeClient for the resolved backend, with clear errors."""
    backend = _resolve_backend(backend)

    if backend == "anthropic":
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "The 'anthropic' package is required for the anthropic judge "
                "backend. Install it with: pip install anthropic"
            ) from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Set it, or use "
                "--judge-backend openrouter with OPENROUTER_API_KEY, or run "
                "--source simulate / --source arena fully offline."
            )
        return JudgeClient("anthropic", anthropic.Anthropic())

    # backend == "openrouter"
    try:
        import openai
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RuntimeError(
            "The 'openai' package is required for the openrouter judge backend. "
            "Install it with: pip install openai"
        ) from exc
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Set it, or use --judge-backend "
            "anthropic with ANTHROPIC_API_KEY, or run --source simulate / "
            "--source arena fully offline."
        )
    return JudgeClient(
        "openrouter",
        openai.OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=os.environ["OPENROUTER_API_KEY"],
        ),
    )


def generate_response(client: JudgeClient, model: str, prompt: str,
                      max_tokens: int = 1024) -> str:
    """Generate a single model answer for a prompt."""
    return client.chat(model, prompt, max_tokens=max_tokens)


def _judge_once(client: JudgeClient, judge_model: str, prompt: str,
                answer_first: str, answer_second: str) -> str:
    """Ask the judge which slot is better; returns 'first', 'second' or 'tie'."""
    user = (
        f"问题：\n{prompt}\n\n"
        f"回答 A：\n{answer_first}\n\n"
        f"回答 B：\n{answer_second}\n\n"
        "哪个回答更好？只输出 A、B 或 tie。"
    )
    verdict = client.chat(judge_model, user, max_tokens=8, system=_JUDGE_SYSTEM).lower()
    if verdict.startswith("a"):
        return "first"
    if verdict.startswith("b"):
        return "second"
    return "tie"


def judge_pair(client: JudgeClient, judge_model: str, prompt: str,
               answer_a: str, answer_b: str) -> str:
    """
    Judge a pair with position-bias mitigation (swap order, tie on disagreement).

    Returns 'model_a', 'model_b', or 'tie'.
    """
    # First pass: A in slot 1, B in slot 2.
    first_pass = _judge_once(client, judge_model, prompt, answer_a, answer_b)
    # Second pass: swap the slots so B is now in slot 1.
    second_pass = _judge_once(client, judge_model, prompt, answer_b, answer_a)

    # Translate both judgements into "which real model won", then require
    # agreement. Slot 1 in the first pass is A; slot 1 in the second pass is B.
    winner_first = {"first": "model_a", "second": "model_b", "tie": "tie"}[first_pass]
    winner_second = {"first": "model_b", "second": "model_a", "tie": "tie"}[second_pass]

    if winner_first == winner_second:
        return winner_first
    return "tie"  # inconsistent under swap -> position bias, count as tie


def run_llm_battles(candidate_models: Optional[List[str]] = None,
                    prompts: Optional[List[str]] = None,
                    judge_model: str = DEFAULT_JUDGE_MODEL,
                    backend: str = "auto") -> List[dict]:
    """
    Run LLM-judged battles between every model pair over every prompt.

    Args:
        candidate_models: Models to compare (default: DEFAULT_CANDIDATE_MODELS).
        prompts: Prompts to battle on (default: DEFAULT_PROMPTS).
        judge_model: Model used as the judge.
        backend: 'anthropic', 'openrouter', or 'auto' (anthropic if
            ANTHROPIC_API_KEY else openrouter).

    Returns:
        List of battle dicts ({'model_a', 'model_b', 'winner'}).
    """
    candidate_models = candidate_models or DEFAULT_CANDIDATE_MODELS
    prompts = prompts or DEFAULT_PROMPTS
    if len(candidate_models) < 2:
        raise ValueError("Need at least 2 candidate models for LLM-judge battles")

    client = _get_client(backend)
    battles: List[dict] = []

    for prompt in prompts:
        # Cache each model's answer per prompt so it is generated only once.
        answers: Dict[str, str] = {
            model: generate_response(client, model, prompt) for model in candidate_models
        }
        for i, model_a in enumerate(candidate_models):
            for model_b in candidate_models[i + 1:]:
                winner = judge_pair(
                    client, judge_model, prompt, answers[model_a], answers[model_b]
                )
                battles.append(
                    {"model_a": model_a, "model_b": model_b, "winner": winner}
                )

    return battles
