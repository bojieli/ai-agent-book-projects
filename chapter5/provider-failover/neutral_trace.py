"""模型中立的轨迹格式。

一条跑到一半的 Agent 轨迹里有三样东西：思考、工具调用、工具结果。工具调用和
结果各家结构不同但语义一致，重新渲染即可；思考不行——它可能带着一份只对签发
它的厂商有效的凭证。所以这里把每段思考拆成两个槽位：

* ``text``       明文思考或厂商返回的 summary，换一家模型也能读懂，可以带走；
* ``credential`` 签名或密文（Claude 的 ``signature``、Gemini 的
  ``thoughtSignature``、OpenAI 的 ``encrypted_content``），只对签发者有效。

``native`` 保留厂商原样返回的那一段 payload。中立格式本身用不到它，但“直传臂”
要用它来复现“不做任何转换、直接把上一家的消息搬给下一家”的做法。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

PLAINTEXT = "plaintext"  # 明文思考，无凭证：开源模型的 reasoning_content
SIGNED = "signed"  # 明文思考 + 签名：Claude 的 thinking 块
SUMMARY = "summary"  # 厂商给的思考摘要，正文本身不返回：Gemini 的 thought 部分


@dataclass
class Reasoning:
    """一段思考。``text`` 可移植，``credential`` 不可。"""

    text: str | None
    credential: str | None
    issuer: str  # 签发这段思考的厂商
    kind: str  # PLAINTEXT / SIGNED / SUMMARY

    @property
    def portable_text(self) -> str | None:
        """换一家模型时还能带走的部分。"""
        return self.text


@dataclass
class ToolCall:
    name: str
    arguments: dict
    call_id: str  # 原厂商签发的 id，只作记录；渲染时按目标厂商重铸

    def fingerprint(self) -> str:
        """“工具名 + 参数”指纹，用来数切换之后有没有把已经做过的事重做一遍。"""
        return f"{self.name}({json.dumps(self.arguments, sort_keys=True, ensure_ascii=False)})"


@dataclass
class Step:
    """一步。``role`` 为 user / assistant / tool。"""

    role: str
    text: str | None = None
    reasoning: Reasoning | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: str | None = None  # role == "tool" 时，对应哪次调用
    tool_name: str | None = None
    issuer: str | None = None  # 这一步由哪家模型产生
    native: dict | None = None  # 厂商原样返回的 payload，仅供直传臂使用


@dataclass
class Trace:
    steps: list[Step] = field(default_factory=list)

    def add(self, step: Step) -> Step:
        self.steps.append(step)
        return step

    def user(self, text: str) -> Step:
        return self.add(Step(role="user", text=text))

    def tool_result(self, call_id: str, name: str, content: str) -> Step:
        return self.add(Step(role="tool", text=content, tool_call_id=call_id, tool_name=name))

    def called_fingerprints(self) -> list[str]:
        return [c.fingerprint() for s in self.steps for c in s.tool_calls]

    def repair_orphans(self) -> list[str]:
        """补齐缺结果的工具调用。

        流式请求被切断时，工具调用可能已经进了轨迹而结果还没回来。多数厂商会
        拒绝这种残缺的配对，所以渲染之前先补一条说明性的结果。
        """
        answered = {s.tool_call_id for s in self.steps if s.role == "tool"}
        repaired = []
        for i, step in enumerate(list(self.steps)):
            for call in step.tool_calls:
                if call.call_id in answered:
                    continue
                self.steps.insert(i + 1, Step(role="tool", text="[未返回结果：上一次请求中断]",
                                              tool_call_id=call.call_id, tool_name=call.name))
                repaired.append(call.call_id)
                answered.add(call.call_id)
        return repaired

    def to_json(self) -> dict:
        return {"steps": [asdict(s) for s in self.steps]}
