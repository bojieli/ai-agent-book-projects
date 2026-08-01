"""Phone and Computer Agents plus the autonomous tool dispatcher."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from browser import RecoverableFillError, RegistrationBrowser
from bus import MessageBus
from models import DecisionRecord, FieldSpec
from voice import PhoneChannel


_EXTRACTION_RECEIPTS: List[Dict[str, object]] = []


def reset_extraction_receipts() -> None:
    _EXTRACTION_RECEIPTS.clear()


def extraction_receipts() -> List[Dict[str, object]]:
    """Return value-free provider metadata for experiment provenance."""
    return [dict(item) for item in _EXTRACTION_RECEIPTS]


async def _extract_value(field: FieldSpec, utterance: str) -> str:
    """Use the Phone Agent's LLM to turn a natural spoken answer into one value."""
    from openai import AsyncOpenAI

    clients = []
    if os.getenv("ARK_API_KEY"):
        clients.append((AsyncOpenAI(
            api_key=os.environ["ARK_API_KEY"],
            base_url="https://ark.cn-beijing.volces.com/api/v3",
        ), os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"), "Volcengine ARK"))
    if os.getenv("MOONSHOT_API_KEY"):
        clients.append((AsyncOpenAI(
            api_key=os.environ["MOONSHOT_API_KEY"],
            base_url="https://api.moonshot.cn/v1",
        ), os.getenv("MOONSHOT_MODEL", "kimi-k3"), "Moonshot"))
    if os.getenv("OPENAI_API_KEY"):
        clients.append((AsyncOpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.getenv("OPENAI_BASE_URL") or None,
        ), os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), "OpenAI"))
    if os.getenv("OPENROUTER_API_KEY"):
        client = AsyncOpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
        )
        raw_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        clients.append((client, raw_model if "/" in raw_model else f"openai/{raw_model}", "OpenRouter"))
    if not clients:
        raise RuntimeError("Phone Agent 的语义抽取需要任一已支持文本模型 API Key")

    kwargs = dict(messages=[
            {
                "role": "system",
                "content": (
                    "Extract only the value the user supplied for the requested form field. "
                    "Never infer a missing value. Preserve identifiers exactly, while normalizing "
                    "explicitly spoken email words such as 'at' and 'dot' to symbols and spoken "
                    "number words to digits when the field requires them. Return exactly "
                    "one JSON object with the schema {\"value\": \"the extracted value\"}."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "field": field.label,
                        "type": field.input_type,
                        "format_hint": field.format_hint,
                        "options": field.options,
                        "spoken_answer": utterance,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    last_error = None
    for client, model, provider in clients:
        try:
            model_kwargs = dict(kwargs)
            if "kimi-k3" in model:
                model_kwargs["temperature"] = 1
                model_kwargs["max_tokens"] = 2048
            response = await client.chat.completions.create(model=model, **model_kwargs)
            if not (response.choices[0].message.content or "").strip():
                raise ValueError("模型返回空 content")
            break
        except Exception as exc:
            last_error = exc
            print(f"  [Phone Agent] {provider} 抽取失败，尝试下一端点：{type(exc).__name__}")
    else:
        raise RuntimeError("所有已配置的 Phone Agent 文本端点均失败") from last_error
    data = json.loads(response.choices[0].message.content or "{}")
    usage = getattr(response, "usage", None)
    _EXTRACTION_RECEIPTS.append({
        "operation": "field_value_extraction",
        "provider": provider,
        "model": model,
        "response_id": getattr(response, "id", None),
        "usage": {
            key: int(value)
            for key, value in {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }.items()
            if value is not None
        },
        "transcript_or_value_retained": False,
    })
    return str(data.get("value", "")).strip()


class PhoneAgent:
    def __init__(
        self,
        bus: MessageBus,
        channel: PhoneChannel,
        purpose: str,
        required_info: List[FieldSpec],
        *,
        max_retries: int = 3,
    ):
        self.bus = bus
        self.channel = channel
        self.purpose = purpose
        self.required_info = required_info
        self.max_retries = max_retries
        self.browser_feedback: List[Dict[str, str]] = []
        self.form_ready = asyncio.Event()

    async def _receive_computer_feedback(self):
        """Independent inbound loop: Computer -> Phone is not a write-only channel."""
        while True:
            message = await self.bus.receive("phone_agent")
            if message.type == "fill_error":
                self.browser_feedback.append({
                    "field": str(message.payload.get("field", "")),
                    "error": str(message.payload.get("error", "")),
                })
            elif message.type == "form_ready":
                self.form_ready.set()
                return

    async def run(self) -> None:
        """Run the dialogue and always release its inbound loop/transport."""
        self._feedback_task = None
        try:
            await self._run_dialogue()
        finally:
            if self._feedback_task is not None:
                self._feedback_task.cancel()
                await asyncio.gather(self._feedback_task, return_exceptions=True)
            if hasattr(self.channel, "close") and not getattr(self.channel, "closed", False):
                await self.channel.close()

    async def _run_dialogue(self) -> None:
        feedback_task = asyncio.create_task(
            self._receive_computer_feedback(), name="phone-inbound-computer-messages"
        )
        self._feedback_task = feedback_task
        await self.bus.send(
            "phone_agent", "computer_agent", "call_started",
            purpose=self.purpose,
            fields=[f.name for f in self.required_info],
        )
        await self.channel.say(f"您好，我正在{self.purpose}。我会逐项询问并核对格式。")

        for field in self.required_info:
            accepted = False
            feedback = ""
            for attempt in range(1, self.max_retries + 1):
                question = f"请问您的{field.label}是什么？"
                if field.format_hint:
                    question += f" 格式要求：{field.format_hint}。"
                if feedback:
                    question = f"刚才的回答无法通过校验：{feedback}。{question}"
                await self.bus.send(
                    "phone_agent", "computer_agent", "question_asked",
                    field=field.name,
                    attempt=attempt,
                )
                await self.channel.say(question)
                try:
                    utterance = await self.channel.listen()
                    # An omitted optional answer is a deliberate skip, not a value
                    # to write into a stateful page widget (some date controls react
                    # destructively to programmatic empty-string fills).
                    value = "" if not field.required and not utterance.strip() else await _extract_value(field, utterance)
                except Exception as exc:
                    await self.bus.send(
                        "phone_agent", "computer_agent", "call_failed",
                        field=field.name, reason=f"语音/抽取失败：{type(exc).__name__}",
                    )
                    if hasattr(self.channel, "close"):
                        await self.channel.close()
                    feedback_task.cancel()
                    await asyncio.gather(feedback_task, return_exceptions=True)
                    return
                valid, feedback = field.validate(value)
                if not valid:
                    await self.bus.send(
                        "phone_agent", "computer_agent", "format_invalid",
                        field=field.name,
                        attempt=attempt,
                        reason=feedback,
                    )
                    continue

                if not value and not field.required:
                    await self.bus.send(
                        "phone_agent", "computer_agent", "info_skipped",
                        field=field.name, attempt=attempt, reason="optional_blank",
                    )
                    accepted = True
                    break

                await self.bus.send(
                    "phone_agent",
                    "computer_agent",
                    "info_collected",
                    sensitive_keys=("value",),
                    field=field.name,
                    value=value,
                    attempt=attempt,
                )
                # Deliberately do not await a browser acknowledgement: the next
                # question starts while Computer Agent locates/fills this field.
                accepted = True
                break
            if not accepted:
                await self.bus.send(
                    "phone_agent", "computer_agent", "call_failed",
                    field=field.name,
                    reason="超过格式重问次数",
                )
                await self.channel.say("抱歉，这一项多次未通过格式校验，本次注册已安全暂停。")
                if hasattr(self.channel, "close"):
                    await self.channel.close()
                feedback_task.cancel()
                await asyncio.gather(feedback_task, return_exceptions=True)
                return

        await self.bus.send("phone_agent", "computer_agent", "task_completed")
        # Ask/fill stayed fully concurrent field-by-field; only the final goodbye
        # waits for Computer Agent's aggregate result so browser errors can flow back.
        try:
            await asyncio.wait_for(self.form_ready.wait(), timeout=60)
        except asyncio.TimeoutError:
            self.browser_feedback.append({"field": "form", "error": "电脑端最终确认超时"})
        if self.browser_feedback:
            await self.channel.say("信息已收集，但电脑端填写遇到问题，表单已暂停提交，请稍后查看错误报告。")
        else:
            await self.channel.say("所需信息已经收集并填写完成，电脑端已完成最后确认。")
        if hasattr(self.channel, "close"):
            await self.channel.close()
        feedback_task.cancel()
        await asyncio.gather(feedback_task, return_exceptions=True)


class ComputerAgent:
    def __init__(
        self,
        bus: MessageBus,
        browser: RegistrationBrowser,
        field_specs: List[FieldSpec],
        known_values: Dict[str, str],
    ):
        self.bus = bus
        self.browser = browser
        self.fields = {f.name: f for f in field_specs}
        self.known_values = known_values
        self.filled: List[str] = []
        self.errors: List[Dict[str, str]] = []
        self.submitted = False

    async def _fill(self, name: str, value: str) -> None:
        field = self.fields.get(name)
        if not field:
            raise KeyError(f"页面中不存在字段 {name}")
        await self.browser.fill(field, value)
        self.filled.append(name)
        await self.bus.send("computer_agent", "phone_agent", "field_filled", field=name)

    async def _report_fill_error(self, name: str, exc: RecoverableFillError) -> None:
        """Record one browser failure and forward the shared error envelope."""
        error = {"field": name, "error": str(exc)}
        self.errors.append(error)
        await self.bus.send(
            "computer_agent",
            "phone_agent",
            "fill_error",
            sensitive_keys=("error",),
            **error,
        )

    async def run(self) -> Dict[str, object]:
        for name, value in self.known_values.items():
            if name in self.fields:
                try:
                    await self._fill(name, value)
                except RecoverableFillError as exc:
                    # Mirror the in-dialogue fill path below: surface the failure
                    # to the phone agent (via browser_feedback) so it doesn't tell
                    # the user registration succeeded when a known field failed.
                    await self._report_fill_error(name, exc)

        completed = False
        while not completed:
            # This idle cap must exceed the phone side's worst-case per-question
            # latency (TTS + the channel's own listen window + value extraction).
            # The default WebRTC human listen allows a start timer plus an answer
            # timer (~240s total), so a 120s cap here aborts a live call while the
            # user is still legitimately answering. run_parallel cancels this task
            # the moment the phone task completes or errors, so a larger cap only
            # relaxes the false-abort case.
            message = await self.bus.receive("computer_agent", timeout=600)
            if message.type == "info_collected":
                name = message.payload.get("field")
                value = message.payload.get("value")
                if not isinstance(name, str) or not name:
                    raise ValueError("info_collected requires a non-empty field")
                if not isinstance(value, str):
                    raise ValueError("info_collected requires a string value")
                try:
                    await self._fill(name, value)
                except RecoverableFillError as exc:
                    await self._report_fill_error(name, exc)
            elif message.type == "call_failed":
                self.errors.append({
                    "field": message.payload.get("field", ""),
                    "error": message.payload.get("reason", "Phone Agent failed"),
                })
                completed = True
            elif message.type == "task_completed":
                completed = True
            elif message.type == "info_skipped":
                # Optional blank values require no browser operation. The explicit
                # envelope keeps the two Agents' timelines auditable.
                continue

        if not self.errors:
            self.submitted = await self.browser.submit()
        await self.bus.send(
            "computer_agent", "phone_agent", "form_ready",
            errors=len(self.errors), submitted=self.submitted,
        )
        await self.bus.send(
            "computer_agent", "manager", "registration_finished",
            filled=self.filled,
            submitted=self.submitted,
            errors=self.errors,
        )
        return {
            "filled": self.filled,
            "submitted": self.submitted,
            "errors": self.errors,
        }


@dataclass
class SpawnedAgents:
    phone: PhoneAgent
    computer: ComputerAgent


def initiate_phone_call_agent(
    *,
    decision: DecisionRecord,
    bus: MessageBus,
    channel: PhoneChannel,
    browser: RegistrationBrowser,
    known_values: Dict[str, str],
) -> SpawnedAgents:
    """Tool dispatcher invoked only after the model emits the matching tool call."""
    if decision.tool_called != "initiate_phone_call_agent":
        raise RuntimeError("模型未调用 initiate_phone_call_agent，不能预先创建 Phone Agent")
    if not decision.required_info:
        raise RuntimeError("Phone Agent 工具调用没有任何可映射的页面字段")
    return SpawnedAgents(
        phone=PhoneAgent(bus, channel, decision.purpose, decision.required_info),
        computer=ComputerAgent(bus, browser, decision.discovered_fields, known_values),
    )


async def run_parallel(agents: SpawnedAgents, bus: MessageBus) -> Dict[str, object]:
    phone_task = asyncio.create_task(agents.phone.run(), name="phone-agent-react-loop")
    computer_task = asyncio.create_task(agents.computer.run(), name="computer-agent-react-loop")
    tasks = (phone_task, computer_task)
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        failure = next(
            (task.exception() for task in done if not task.cancelled() and task.exception() is not None),
            None,
        )
        if failure is not None:
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            raise failure
        _phone_result, computer_result = await asyncio.gather(*tasks)
    except BaseException:
        # ``asyncio.gather`` does not cancel a still-running peer when one task
        # raises. A failed audio/browser loop must not leave the other Agent
        # blocked on its inbox, nor leave a PSTN/webhook transport open.
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        channel = agents.phone.channel
        if hasattr(channel, "close") and not getattr(channel, "closed", False):
            await channel.close()
        raise
    finished = await bus.receive("manager", timeout=5)
    assert finished.type == "registration_finished"
    return computer_result


def timing_evidence(bus: MessageBus) -> Dict[str, object]:
    questions = {
        m.payload["field"]: m.monotonic_seconds
        for m in bus.history if m.type == "question_asked" and m.payload.get("attempt") == 1
    }
    collected = {
        m.payload["field"]: m.monotonic_seconds
        for m in bus.history if m.type == "info_collected"
    }
    filled = {
        m.payload["field"]: m.monotonic_seconds
        for m in bus.history if m.type == "field_filled"
    }
    ordered = list(questions)
    overlaps = []
    expected_overlap_count = 0
    for current, next_field in zip(ordered, ordered[1:]):
        if current in collected and current in filled:
            expected_overlap_count += 1
            overlaps.append({
                "field_being_filled": current,
                "next_question": next_field,
                "next_question_before_fill_completed": questions[next_field] < filled[current],
                "next_question_at": questions[next_field],
                "fill_completed_at": filled[current],
            })
    return {
        "question_times": questions,
        "collection_times": collected,
        "fill_times": filled,
        "overlap_checks": overlaps,
        "expected_overlap_count": expected_overlap_count,
        "independent_tasks": ["phone-agent-react-loop", "computer-agent-react-loop"],
    }
