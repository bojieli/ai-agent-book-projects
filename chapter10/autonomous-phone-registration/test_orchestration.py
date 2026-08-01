import asyncio
from unittest.mock import AsyncMock, patch

import pytest

import demo
from browser import RecoverableFillError
from bus import MessageBus
from models import DecisionRecord, FieldSpec
from orchestration import (
    ComputerAgent,
    initiate_phone_call_agent,
    run_parallel,
    timing_evidence,
)
from voice import ScriptedPhoneChannel


class FakeBrowser:
    def __init__(self):
        self.values = {}
        self.submit_enabled = False

    async def fill(self, field, value):
        await asyncio.sleep(0.05)
        self.values[field.name] = value

    async def submit(self):
        return False


class SubmittingFakeBrowser(FakeBrowser):
    def __init__(self):
        super().__init__()
        self.submit_enabled = True
        self.submit_calls = 0

    async def submit(self):
        self.submit_calls += 1
        return True


class FailingFillBrowser(FakeBrowser):
    def __init__(self):
        super().__init__()
        self.submit_calls = 0

    async def fill(self, field, value):
        raise RecoverableFillError(f"cannot fill {field.name}")

    async def submit(self):
        self.submit_calls += 1
        return True


@pytest.mark.asyncio
async def test_ask_one_fill_one_runs_concurrently_and_reasks_invalid_format():
    fields = [
        FieldSpec("email", "邮箱", "email", format_hint="name@example.com"),
        FieldSpec("birth", "出生日期", "date", format_hint="YYYY-MM-DD"),
    ]
    decision = DecisionRecord(
        page_url="https://example.test/register",
        page_title="Register",
        known_fields=[],
        discovered_fields=fields,
        tool_called="initiate_phone_call_agent",
        purpose="协助填写注册表单",
        required_info=fields,
        rationale_summary="tool call",
        model="test",
        monotonic_seconds=0,
    )
    # First email answer is invalid, forcing format feedback and a real re-ask.
    channel = ScriptedPhoneChannel(["bad", "me@example.com", "2020-01-02"])
    bus = MessageBus()
    browser = FakeBrowser()
    extracted = AsyncMock(side_effect=["bad", "me@example.com", "2020-01-02"])
    agents = initiate_phone_call_agent(
        decision=decision,
        bus=bus,
        channel=channel,
        browser=browser,
        known_values={},
    )
    with patch("orchestration._extract_value", extracted):
        result = await run_parallel(agents, bus)

    assert result["errors"] == []
    assert browser.values == {"email": "me@example.com", "birth": "2020-01-02"}
    assert any(m.type == "format_invalid" for m in bus.history)
    evidence = timing_evidence(bus)
    assert any(c["next_question_before_fill_completed"] for c in evidence["overlap_checks"])


def test_field_validation_handles_email_phone_date_and_page_pattern():
    assert not FieldSpec("e", "email", "email").validate("bad")[0]
    assert FieldSpec("e", "email", "email").validate("a@b.com")[0]
    assert not FieldSpec("d", "date", "date").validate("01/02/2020")[0]
    assert FieldSpec("p", "code", pattern=r"[A-Z]{2}\d{4}").validate("AB1234")[0]


@pytest.mark.asyncio
async def test_live_transport_without_consent_refuses_before_browser_or_audio_creation():
    args = demo.parser().parse_args(["--headless", "--phone-transport", "local"])
    with patch("demo.RegistrationBrowser") as browser_type, patch(
        "demo.LiveMicrophoneChannel"
    ) as audio_type:
        with pytest.raises(SystemExit, match="confirm-consent"):
            await demo.main(args)
    browser_type.assert_not_called()
    audio_type.assert_not_called()


@pytest.mark.asyncio
async def test_unexpected_phone_failure_cancels_peer_and_closes_channel():
    class ExplodingChannel:
        def __init__(self):
            self.closed = False

        async def say(self, _text):
            raise RuntimeError("synthetic transport failure")

        async def listen(self, *, timeout=30):  # pragma: no cover - say fails first
            raise AssertionError(timeout)

        async def close(self):
            self.closed = True

    fields = [FieldSpec("email", "邮箱", "email")]
    decision = DecisionRecord(
        page_url="https://example.test/register",
        page_title="Register",
        known_fields=[],
        discovered_fields=fields,
        tool_called="initiate_phone_call_agent",
        purpose="协助填写注册表单",
        required_info=fields,
        rationale_summary="tool call",
        model="test",
        monotonic_seconds=0,
    )
    bus = MessageBus()
    channel = ExplodingChannel()
    agents = initiate_phone_call_agent(
        decision=decision,
        bus=bus,
        channel=channel,
        browser=FakeBrowser(),
        known_values={},
    )
    with pytest.raises(RuntimeError, match="synthetic transport failure"):
        await asyncio.wait_for(run_parallel(agents, bus), timeout=0.5)
    assert channel.closed is True
    assert not any(
        task.get_name() in {"phone-agent-react-loop", "computer-agent-react-loop"}
        and not task.done()
        for task in asyncio.all_tasks()
    )


@pytest.mark.asyncio
async def test_task_completed_triggers_submission_when_browser_is_opted_in():
    fields = [FieldSpec("email", "邮箱", "email")]
    decision = DecisionRecord(
        page_url="https://example.test/register",
        page_title="Register",
        known_fields=[],
        discovered_fields=fields,
        tool_called="initiate_phone_call_agent",
        purpose="协助填写注册表单",
        required_info=fields,
        rationale_summary="tool call",
        model="test",
        monotonic_seconds=0,
    )
    browser = SubmittingFakeBrowser()
    bus = MessageBus()
    agents = initiate_phone_call_agent(
        decision=decision,
        bus=bus,
        channel=ScriptedPhoneChannel(["me@example.com"]),
        browser=browser,
        known_values={},
    )
    with patch("orchestration._extract_value", AsyncMock(return_value="me@example.com")):
        result = await run_parallel(agents, bus)
    assert result["submitted"] is True
    assert browser.submit_calls == 1


@pytest.mark.asyncio
async def test_computer_fill_error_flows_back_to_phone_and_blocks_submission():
    fields = [FieldSpec("email", "邮箱", "email")]
    decision = DecisionRecord(
        page_url="https://example.test/register",
        page_title="Register",
        known_fields=[],
        discovered_fields=fields,
        tool_called="initiate_phone_call_agent",
        purpose="协助填写注册表单",
        required_info=fields,
        rationale_summary="tool call",
        model="test",
        monotonic_seconds=0,
    )
    browser = FailingFillBrowser()
    channel = ScriptedPhoneChannel(["me@example.com"])
    bus = MessageBus()
    agents = initiate_phone_call_agent(
        decision=decision,
        bus=bus,
        channel=channel,
        browser=browser,
        known_values={},
    )
    with patch("orchestration._extract_value", AsyncMock(return_value="me@example.com")):
        result = await run_parallel(agents, bus)

    assert result["submitted"] is False
    assert browser.submit_calls == 0
    assert agents.phone.browser_feedback == [
        {"field": "email", "error": "cannot fill email"}
    ]
    fill_error = next(message for message in bus.history if message.type == "fill_error")
    assert getattr(fill_error, "_sensitive_keys") == ("error",)
    assert "填写遇到问题" in channel.prompts[-1]


@pytest.mark.asyncio
async def test_malformed_info_collected_fails_before_fill_error_handling():
    bus = MessageBus()
    computer = ComputerAgent(bus, FakeBrowser(), [], {})
    task = asyncio.create_task(computer.run())
    await bus.send(
        "phone_agent",
        "computer_agent",
        "info_collected",
        sensitive_keys=("value",),
        value="secret",
    )

    with pytest.raises(ValueError, match="non-empty field"):
        await task
    assert not any(message.type == "fill_error" for message in bus.history)


@pytest.mark.asyncio
async def test_optional_blank_is_audited_skip_and_never_written_to_browser():
    fields = [
        FieldSpec("email", "邮箱", "email"),
        FieldSpec("birthday", "生日", "text", required=False),
        FieldSpec("address", "地址", "textarea", required=False),
    ]
    decision = DecisionRecord(
        page_url="https://example.test/register",
        page_title="Register",
        known_fields=[],
        discovered_fields=fields,
        tool_called="initiate_phone_call_agent",
        purpose="协助填写注册表单",
        required_info=fields,
        rationale_summary="tool call",
        model="test",
        monotonic_seconds=0,
    )
    browser = FakeBrowser()
    bus = MessageBus()
    agents = initiate_phone_call_agent(
        decision=decision,
        bus=bus,
        channel=ScriptedPhoneChannel(["me@example.com", "", ""]),
        browser=browser,
        known_values={},
    )
    with patch("orchestration._extract_value", AsyncMock(return_value="me@example.com")) as extract:
        result = await run_parallel(agents, bus)

    assert result["errors"] == []
    assert browser.values == {"email": "me@example.com"}
    assert extract.await_count == 1
    skipped = [message for message in bus.history if message.type == "info_skipped"]
    assert [message.payload["field"] for message in skipped] == ["birthday", "address"]
    evidence = timing_evidence(bus)
    assert evidence["expected_overlap_count"] == 1
    assert len(evidence["overlap_checks"]) == 1


class CountryFailBrowser(SubmittingFakeBrowser):
    """Fails only the pre-filled known field, succeeds on the phone-collected one."""

    async def fill(self, field, value):
        if field.name == "country":
            raise RecoverableFillError(f"cannot fill {field.name}")
        await asyncio.sleep(0.05)
        self.values[field.name] = value


@pytest.mark.asyncio
async def test_known_value_fill_error_flows_back_to_phone_and_blocks_submission():
    # A known_values field that fails to pre-fill must surface a fill_error (like
    # the in-dialogue path), so the phone agent reports the failure instead of
    # telling the user registration completed.
    email = FieldSpec("email", "邮箱", "email")
    country = FieldSpec("country", "国家", "text")
    decision = DecisionRecord(
        page_url="https://example.test/register",
        page_title="Register",
        known_fields=[country.name],
        discovered_fields=[email, country],
        tool_called="initiate_phone_call_agent",
        purpose="协助填写注册表单",
        required_info=[email],
        rationale_summary="tool call",
        model="test",
        monotonic_seconds=0,
    )
    browser = CountryFailBrowser()
    channel = ScriptedPhoneChannel(["me@example.com"])
    bus = MessageBus()
    agents = initiate_phone_call_agent(
        decision=decision,
        bus=bus,
        channel=channel,
        browser=browser,
        known_values={"country": "US"},
    )
    with patch("orchestration._extract_value", AsyncMock(return_value="me@example.com")):
        result = await run_parallel(agents, bus)

    assert result["submitted"] is False
    assert browser.submit_calls == 0
    assert {"field": "country", "error": "cannot fill country"} in agents.phone.browser_feedback
    assert any(message.type == "fill_error" for message in bus.history)
    assert "填写遇到问题" in channel.prompts[-1]
