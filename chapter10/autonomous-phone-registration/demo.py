#!/usr/bin/env python3
"""Experiment 10-5: autonomously spawn Phone Agent during real browser use."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from browser import RegistrationBrowser
from bus import MessageBus
from decision import decide_orchestration
from orchestration import initiate_phone_call_agent, run_parallel, timing_evidence
from voice import LiveMicrophoneChannel, ScriptedPhoneChannel


DEFAULT_URL = "https://demoqa.com/automation-practice-form"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="实验 10-5：Computer Use Agent 自主决定并启动实时 Phone Agent",
    )
    p.add_argument("--url", default=DEFAULT_URL, help="真实注册/资料表单 URL")
    p.add_argument("--known-json", default="{}", help="已在上下文中的字段 JSON（键为表单 name/id）")
    p.add_argument("--headless", action="store_true", help="无界面运行真实 Chromium")
    p.add_argument("--submit", action="store_true", help="明确允许最终点击提交；默认只填不提交，避免副作用")
    p.add_argument("--phone-transport", choices=["twilio", "local"], default="twilio",
                   help="twilio=真实 PSTN 电话（验收路径，默认）；local=本机麦克风开发路径")
    p.add_argument("--confirm-consent", action="store_true",
                   help="确认参与者已授权本次实验电话/麦克风采集；所有真人语音路径均要求")
    p.add_argument("--trace", default="artifacts/message_timeline.json", help="脱敏消息时序输出")
    p.add_argument("--decision-trace", default="artifacts/decision.json", help="Agent 决策记录输出")
    p.add_argument("--acceptance-report", default="artifacts/acceptance_report.json",
                   help="写入机器可读验收门禁；scripted/local 不会被标记为 PSTN 通过")
    p.add_argument(
        "--scripted-json",
        default=None,
        help="仅用于自动化补充验证：字段名到回答的 JSON；省略则使用真实麦克风 ASR/TTS",
    )
    return p


async def main(args: argparse.Namespace) -> int:
    known = json.loads(args.known_json)
    if not isinstance(known, dict):
        raise SystemExit("--known-json 必须是 JSON object")
    if not args.scripted_json and not args.confirm_consent:
        raise SystemExit("拒绝电话/音频采集：所有真人语音路径必须显式传入 --confirm-consent")
    started = time.monotonic()
    bus = MessageBus(args.trace)
    browser = RegistrationBrowser(args.url, headless=args.headless, submit=args.submit)
    channel = None
    try:
        await browser.open()
        fields = await browser.discover_fields()
        title = await browser.title
        print(f"[Computer Agent] 已打开真实页面：{title} ({args.url})")
        print(f"[Computer Agent] 发现 {len(fields)} 个可填写字段，其中 {sum(f.required for f in fields)} 个必填")
        decision = await decide_orchestration(
            page_url=args.url,
            page_title=title,
            fields=fields,
            known_values={str(k): str(v) for k, v in known.items()},
            elapsed=started,
        )
        decision_path = Path(args.decision_trace)
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        decision_path.write_text(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[自主决策] tool_called={decision.tool_called}; summary={decision.rationale_summary}")
        if decision.tool_called != "initiate_phone_call_agent":
            print("Computer Agent 自主判断无需启动 Phone Agent；流程保持在当前 Agent。")
            report_path = Path(args.acceptance_report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps({
                "schema_version": 1,
                "experiment": "10-5",
                "overall_status": "not_applicable",
                "reason": "computer_agent_did_not_spawn_phone_agent",
                "decision": decision.to_dict(),
            }, ensure_ascii=False, indent=2), encoding="utf-8")
            return 2

        if args.scripted_json:
            scripted = json.loads(args.scripted_json)
            answers = [str(scripted.get(f.name, "")) for f in decision.required_info]
            channel = ScriptedPhoneChannel(answers)
            print("[验证模式] 使用 scripted channel；它只验证编排，不替代实时语音验收。")
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
        core_pass = (
            not result["errors"]
            and browser.closed
            and decision.tool_called == "initiate_phone_call_agent"
            and len(overlap_checks) == evidence["expected_overlap_count"]
            and all(item["next_question_before_fill_completed"] for item in overlap_checks)
        )
        pstn_pass = bool(
            transport == "twilio"
            and getattr(channel, "call_sid", None)
            and getattr(channel, "asr_count", 0) >= len(decision.required_info)
            and getattr(channel, "tts_prompt_count", 0) >= 1
            and getattr(channel, "call_status", "") == "completed"
        )
        local_audio_pass = bool(
            transport == "local"
            and any("tts_seconds" in item for item in getattr(channel, "latencies", []))
            and any("asr_seconds" in item for item in getattr(channel, "latencies", []))
        )
        submission_pass = bool(args.submit and result["submitted"])
        report = {
            "schema_version": 1,
            "experiment": "10-5",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "transport": transport,
            "synthetic_values_used": transport == "scripted",
            "decision_provider": decision.provider,
            "decision_model": decision.model,
            "page_url": args.url,
            "fields_discovered": len(decision.discovered_fields),
            "required_fields": [field.name for field in decision.required_info],
            "result": result,
            "timing_evidence": evidence,
            "gates": {
                "real_playwright_page_and_fill": {"status": "pass" if core_pass else "fail"},
                "autonomous_real_llm_tool_call": {"status": "pass" if decision.tool_called else "fail"},
                "ask_one_fill_one_concurrency": {"status": "pass" if core_pass else "fail"},
                "browser_resource_cleanup": {"status": "pass" if browser.closed else "fail"},
                "real_form_submission": {
                    "status": "pass" if submission_pass else "not_run" if not args.submit else "fail",
                    "reason": None if submission_pass else "requires explicit --submit authorization" if not args.submit else "submit was authorized but did not complete",
                },
                "real_pstn_call": {
                    "status": "pass" if pstn_pass else "not_run" if transport != "twilio" else "fail",
                    "reason": None if pstn_pass else "requires authorized consenting endpoint and completed Twilio call",
                },
                "real_audio_asr_tts": {
                    "status": "pass" if (pstn_pass or local_audio_pass) else "not_run" if transport == "scripted" else "fail",
                    "reason": None if (pstn_pass or local_audio_pass) else "scripted transport is non-acceptance" if transport == "scripted" else "audio calls did not complete",
                },
            },
            "overall_status": "pass" if core_pass and pstn_pass and submission_pass else "incomplete",
        }
        report_path = Path(args.acceptance_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"result": result, "timing_evidence": evidence, "acceptance_report": str(report_path)}, ensure_ascii=False, indent=2))
        return 0 if not result["errors"] else 1
    finally:
        if channel is not None and hasattr(channel, "close") and not getattr(channel, "closed", False):
            try:
                await channel.close()
            except Exception as exc:
                print(f"[资源清理] phone channel close failed: {type(exc).__name__}: {exc}")
        if not browser.closed:
            await browser.close()
        print(f"[资源清理] browser/context/page closed={browser.closed}")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(parser().parse_args())))
