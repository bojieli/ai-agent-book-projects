"""回归测试：LLM 思考阶段返回 content=None 时不应在 .strip() 处崩溃。

某些模型在截断/拒答时 message.content 为 None；此前
CascadedSpeechModel.think 会以 AttributeError 中断整条级联流水线，
现在与项目里其它调用点一样用空串兜底。不依赖真实 API：客户端为假对象。
"""

import sys
from types import ModuleType, SimpleNamespace

try:
    import openai  # noqa: F401
except ImportError:
    sys.modules["openai"] = ModuleType("openai")
    sys.modules["openai"].OpenAI = object

from speech_model import CascadedSpeechModel


def _client_returning(content):
    msg = SimpleNamespace(content=content)
    completions = SimpleNamespace(
        create=lambda **kw: SimpleNamespace(choices=[SimpleNamespace(message=msg)]))
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


def test_think_tolerates_none_content():
    model = CascadedSpeechModel(client=None, llm_client=_client_returning(None))
    stage = model.think("还剩多少钱？")
    assert stage.text == ""


def test_think_normal_content_unchanged():
    model = CascadedSpeechModel(client=None, llm_client=_client_returning(" 还剩 3 元。 "))
    stage = model.think("还剩多少钱？")
    assert stage.text == "还剩 3 元。"
