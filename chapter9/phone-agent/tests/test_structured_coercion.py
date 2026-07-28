"""回归测试：通话结构化结果类型异常时，make_phone_call 不应崩溃。

覆盖两类模型失误（此前会让 record 组装阶段 AttributeError/ValueError）：
  1) 结构化输出是 JSON 数组而非对象 -> 归一化为空 dict，走默认值；
  2) key_fields 是数组而非对象 -> 归一化为 {}。
不依赖真实 API：_run_dialog / _chat 被打桩。
"""

import sys
from types import ModuleType

try:
    import openai  # noqa: F401
except ImportError:
    sys.modules["openai"] = ModuleType("openai")
    sys.modules["openai"].OpenAI = object

import pine_voice

pine_voice._run_dialog = lambda *a, **k: [{"speaker": "被叫方", "text": "您好"}]


def test_json_array_structured_output_falls_back_to_defaults():
    pine_voice._chat = lambda *a, **k: '[{"goal_achieved": true}]'
    record = pine_voice.make_phone_call("10010", "查询账单")
    assert record["goal_achieved"] is False
    assert record["summary"] == ""
    assert record["key_fields"] == {}
    assert record["status"] == "completed"


def test_non_dict_key_fields_coerced_to_empty_dict():
    pine_voice._chat = lambda *a, **k: (
        '{"goal_achieved": true, "summary": "s", "key_fields": ["确认号", "金额"],'
        ' "follow_up_needed": false, "follow_up_reason": ""}')
    record = pine_voice.make_phone_call("10010", "查询账单")
    assert record["goal_achieved"] is True
    assert record["key_fields"] == {}


def test_wellformed_structured_output_unchanged():
    pine_voice._chat = lambda *a, **k: (
        '{"goal_achieved": true, "summary": "已受理", '
        '"key_fields": {"确认号": "PC123"}, '
        '"follow_up_needed": false, "follow_up_reason": ""}')
    record = pine_voice.make_phone_call("10010", "查询账单")
    assert record["goal_achieved"] is True
    assert record["summary"] == "已受理"
    assert record["key_fields"] == {"确认号": "PC123"}
