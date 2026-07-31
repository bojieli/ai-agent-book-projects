#!/usr/bin/env python3
"""Experiment 10-5: autonomously spawn Phone Agent during real browser use."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
else:
    load_dotenv()

from browser import RegistrationBrowser
from bus import MessageBus
from decision import decide_orchestration
from orchestration import (
    extraction_receipts,
    initiate_phone_call_agent,
    reset_extraction_receipts,
    run_parallel,
    timing_evidence,
)
from voice import LiveMicrophoneChannel, ScriptedPhoneChannel

DEFAULT_URL = "https://demoqa.com/automation-practice-form"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="实验 10-5：Computer Use Agent 自主决定并启动实时 Phone Agent",
    )
    p.add_argument("--url", default=DEFAULT_URL, help="真实注册/资料表单 URL")
    p.add_argument("--known-json", default="{}", help="已在上下文中的字段 JSON（键为表单 name/id）")
    p.add_argument("--headless", action="store_true", help="无界面运行真实 Chromium")
    p.add_argument(
        "--submit", action="store_true", help="明确允许最终点击提交；默认只填不提交，避免副作用"
    )
    p.add_argument(
        "--phone-transport",
        choices=["webrtc", "local", "twilio"],
        default="webrtc",
        help="webrtc=本机浏览器通话（默认）；local=本机麦克风；twilio=可选旧 PSTN 路径",
    )
    p.add_argument(
        "--confirm-consent",
        action="store_true",
        help="确认参与者已授权本次实验电话/麦克风采集；所有真人语音路径均要求",
    )
    p.add_argument("--trace", default="artifacts/message_timeline.json", help="脱敏消息时序输出")
    p.add_argument("--decision-trace", default="artifacts/decision.json", help="Agent 决策记录输出")
    p.add_argument(
        "--raw-decision-request",
        default=None,
        help="写入不含凭据的原始编排请求（必须与 --raw-decision-response 同时使用）",
    )
    p.add_argument(
        "--raw-decision-response",
        default=None,
        help="写入不含凭据的原始编排响应与延迟（必须与 --raw-decision-request 同时使用）",
    )
    p.add_argument(
        "--acceptance-report",
        default="artifacts/acceptance_report.json",
        help="写入机器可读验收门禁",
    )
    p.add_argument(
        "--webrtc-headless",
        action="store_true",
        help="无界面运行 WebRTC 参与者（仅用于安全自动验收）",
    )
    p.add_argument(
        "--webrtc-port", type=int, default=0, help="WebRTC 本地通话页端口；0 表示自动选择空闲端口"
    )
    p.add_argument(
        "--webrtc-answers-json",
        default=None,
        help=(
            "安全自动验收：字段名映射到一个回答或回答数组；回答会先合成语音，"
            "经过真实 WebRTC RTP 音轨，再由 ASR 转录，不会直接注入 Agent"
        ),
    )
    p.add_argument(
        "--scripted-json",
        default=None,
        help="仅用于自动化补充验证：字段名到回答的 JSON；省略则使用真实麦克风 ASR/TTS",
    )
    return p


def _webrtc_answer_plan(raw: str, fields) -> list[str]:
    configured = json.loads(raw)
    if not isinstance(configured, dict):
        raise SystemExit("--webrtc-answers-json 必须是 JSON object")
    answers: list[str] = []
    for field in fields:
        value = configured.get(field.name, configured.get(field.label))
        if value is None:
            raise SystemExit(f"--webrtc-answers-json 缺少字段 {field.name}")
        if isinstance(value, list):
            answers.extend(str(item) for item in value)
        else:
            answers.append(str(value))
    return answers


def _rtp_is_bidirectional(receipt: dict) -> bool:
    flowing = {
        (item.get("side"), item.get("type"))
        for item in receipt.get("audio_rtp", [])
        if int(item.get("packets", 0)) > 0 and int(item.get("bytes", 0)) > 0
    }
    return {
        ("agent", "outbound-rtp"),
        ("agent", "inbound-rtp"),
        ("participant", "outbound-rtp"),
        ("participant", "inbound-rtp"),
    }.issubset(flowing)


async def main(args: argparse.Namespace) -> int:
    known = json.loads(args.known_json)
    if not isinstance(known, dict):
        raise SystemExit("--known-json 必须是 JSON object")
    if args.scripted_json and args.webrtc_answers_json:
        raise SystemExit("--scripted-json 与 --webrtc-answers-json 不能同时使用")
    if not args.scripted_json and not args.confirm_consent:
        raise SystemExit("拒绝电话/音频采集：所有真人语音路径必须显式传入 --confirm-consent")
    reset_extraction_receipts()
    started = time.monotonic()
    bus = MessageBus(args.trace)
    browser = RegistrationBrowser(args.url, headless=args.headless, submit=args.submit)
    channel = None
    try:
        await browser.open()
        fields = await browser.discover_fields()
        title = await browser.title
        print(f"[Computer Agent] 已打开真实页面：{title} ({args.url})")
        print(
            f"[Computer Agent] 发现 {len(fields)} 个可填写字段，其中 {sum(f.required for f in fields)} 个必填"
        )
        decision = await decide_orchestration(
            page_url=args.url,
            page_title=title,
            fields=fields,
            known_values={str(k): str(v) for k, v in known.items()},
            elapsed=started,
            raw_request_path=args.raw_decision_request,
            raw_response_path=args.raw_decision_response,
        )
        decision_path = Path(args.decision_trace)
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        decision_path.write_text(
            json.dumps(decision.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(
            f"[自主决策] tool_called={decision.tool_called}; summary={decision.rationale_summary}"
        )
        if decision.tool_called != "initiate_phone_call_agent":
            print("Computer Agent 自主判断无需启动 Phone Agent；流程保持在当前 Agent。")
            report_path = Path(args.acceptance_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "experiment": "10-5",
                        "overall_status": "not_applicable",
                        "reason": "computer_agent_did_not_spawn_phone_agent",
                        "decision": decision.to_dict(),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return 2

        if args.scripted_json:
            scripted = json.loads(args.scripted_json)
            answers = [str(scripted.get(f.name, "")) for f in decision.required_info]
            channel = ScriptedPhoneChannel(answers)
            print("[验证模式] 使用 scripted channel；它只验证编排，不替代实时语音验收。")
        elif args.phone_transport == "webrtc":
            from webrtc_channel import WebRTCPhoneChannel

            answer_plan = (
                _webrtc_answer_plan(args.webrtc_answers_json, decision.required_info)
                if args.webrtc_answers_json
                else None
            )
            channel = WebRTCPhoneChannel(
                headless=args.webrtc_headless,
                port=args.webrtc_port,
                synthetic_answers=answer_plan,
            )
            await channel.start()
        elif args.phone_transport == "twilio":
            from twilio_channel import TwilioPhoneChannel

            channel = TwilioPhoneChannel()
            await channel.start()
        else:
            channel = LiveMicrophoneChannel()

        spawned = initiate_phone_call_agent(
            decision=decision,
            bus=bus,
            channel=channel,
            browser=browser,
            known_values={str(k): str(v) for k, v in known.items()},
        )
        result = await run_parallel(spawned, bus)
        evidence = timing_evidence(bus)
        await browser.close()
        transport = "scripted" if args.scripted_json else args.phone_transport
        overlap_checks = evidence["overlap_checks"]
        fill_pass = (
            not result["errors"]
            and browser.closed
            and set(result["filled"]) >= {field.name for field in decision.required_info}
        )
        autonomy_pass = bool(
            decision.tool_called == "initiate_phone_call_agent"
            and decision.provider
            and decision.provider_response_id
        )
        expected_overlap_count = len(decision.required_info) - 1
        concurrency_pass = bool(
            len(decision.required_info) >= 2
            and evidence["expected_overlap_count"] == expected_overlap_count
            and len(overlap_checks) == expected_overlap_count
            and all(item["next_question_before_fill_completed"] for item in overlap_checks)
        )
        webrtc_receipt = (
            channel.acceptance_receipt()
            if transport == "webrtc" and hasattr(channel, "acceptance_receipt")
            else None
        )
        webrtc_pass = bool(
            webrtc_receipt
            and webrtc_receipt["offers"] == 1
            and webrtc_receipt["answers"] == 1
            and webrtc_receipt["media_recordings"] >= len(decision.required_info)
            and webrtc_receipt["status"] == "completed"
            and _rtp_is_bidirectional(webrtc_receipt)
        )
        local_audio_pass = bool(
            transport == "local"
            and any("tts_seconds" in item for item in getattr(channel, "latencies", []))
            and any("asr_seconds" in item for item in getattr(channel, "latencies", []))
        )
        submission_pass = bool(args.submit and result["submitted"])
        repeated_questions = [
            message
            for message in bus.history
            if message.type == "question_asked" and int(message.payload.get("attempt", 1)) > 1
        ]
        invalid_events = [message for message in bus.history if message.type == "format_invalid"]
        reask_pass = bool(invalid_events and repeated_questions)
        persisted_trace = (
            Path(args.trace).read_text(encoding="utf-8") if Path(args.trace).exists() else ""
        )
        trace_rows = json.loads(persisted_trace or "[]")
        collected_rows = [row for row in trace_rows if row.get("type") == "info_collected"]
        privacy_pass = bool(
            collected_rows
            and all(row.get("payload", {}).get("value") == "<redacted>" for row in collected_rows)
            and (
                not webrtc_receipt
                or (
                    webrtc_receipt.get("raw_audio_retained") is False
                    and webrtc_receipt.get("transcripts_retained") is False
                )
            )
        )
        live_audio_pass = bool(
            (webrtc_pass or local_audio_pass)
            and getattr(channel, "asr_count", 0) >= len(decision.required_info)
            and getattr(channel, "tts_prompt_count", 0) >= len(decision.required_info) + 2
        )
        overall_pass = bool(
            fill_pass
            and autonomy_pass
            and concurrency_pass
            and webrtc_pass
            and live_audio_pass
            and reask_pass
            and privacy_pass
            and (submission_pass if args.submit else True)
        )
        report = {
            "schema_version": 2,
            "experiment": "10-5",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "transport": transport,
            "synthetic_values_used": bool(
                transport == "scripted" or (webrtc_receipt or {}).get("synthetic_participant")
            ),
            "decision_provider": decision.provider,
            "decision_model": decision.model,
            "page_url": args.url,
            "fields_discovered": len(decision.discovered_fields),
            "required_fields": [field.name for field in decision.required_info],
            "result": result,
            "timing_evidence": evidence,
            "webrtc_receipt": webrtc_receipt,
            "provider_receipts": {
                "decision": {
                    "provider": decision.provider,
                    "model": decision.model,
                    "response_id": decision.provider_response_id,
                    "usage": decision.provider_usage,
                },
                "field_extractions": extraction_receipts(),
                "speech": getattr(channel, "provider_receipts", []),
            },
            "gates": {
                "real_playwright_page_and_fill": {"status": "pass" if fill_pass else "fail"},
                "autonomous_real_llm_tool_call": {"status": "pass" if autonomy_pass else "fail"},
                "ask_one_fill_one_concurrency": {"status": "pass" if concurrency_pass else "fail"},
                "validation_feedback_and_reask": {"status": "pass" if reask_pass else "fail"},
                "privacy_redaction_and_ephemeral_audio": {
                    "status": "pass" if privacy_pass else "fail"
                },
                "browser_resource_cleanup": {"status": "pass" if browser.closed else "fail"},
                "real_form_submission": {
                    "status": "pass"
                    if submission_pass
                    else "not_run"
                    if not args.submit
                    else "fail",
                    "reason": None
                    if submission_pass
                    else "requires explicit --submit authorization"
                    if not args.submit
                    else "submit was authorized but did not complete",
                },
                "real_webrtc_session": {
                    "status": "pass"
                    if webrtc_pass
                    else "not_run"
                    if transport != "webrtc"
                    else "fail",
                    "reason": None
                    if webrtc_pass
                    else "requires a connected offer/answer and bidirectional RTP audio",
                },
                "bidirectional_webrtc_audio_and_real_asr_tts": {
                    "status": "pass"
                    if live_audio_pass
                    else "not_run"
                    if transport == "scripted"
                    else "fail",
                    "reason": None
                    if live_audio_pass
                    else "audio media or provider operations did not complete",
                },
            },
            "overall_status": "pass" if overall_pass else "incomplete",
        }
        report_path = Path(args.acceptance_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            json.dumps(
                {
                    "result": result,
                    "timing_evidence": evidence,
                    "acceptance_report": str(report_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if not result["errors"] else 1
    finally:
        if (
            channel is not None
            and hasattr(channel, "close")
            and not getattr(channel, "closed", False)
        ):
            try:
                await channel.close()
            except Exception as exc:  # noqa: BLE001 - best-effort cleanup must continue
                print(f"[资源清理] phone channel close failed: {type(exc).__name__}: {exc}")
        if not browser.closed:
            await browser.close()
        print(f"[资源清理] browser/context/page closed={browser.closed}")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(parser().parse_args())))
