# 实验 9-2：Pine Voice 真实电话 Agent

本项目默认调用官方 [`pine-voice`](https://pypi.org/project/pine-voice/) SDK 和真实电话网络，不再用 LLM 扮演被叫方。上层 ReAct Agent 会确定被叫号码、企业名称、目标、上下文与回退策略；公共企业缺少号码时可调用 OpenAI `web_search` 查找官方网站，私人号码缺失时会向用户追问。通话结束后，Pine 返回真实 transcript，Agent 再从中抽取预约时间、确认号等关键字段并汇报。

## 安装与凭证

```bash
# From the repository root: use the shared Chapter 9 core environment
uv sync --locked --python 3.12 --extra ch9

# Activate it before changing directories:
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd: .venv\Scripts\activate.bat

# pip fallback when uv is not installed:
# python -m pip install -e ".[ch9]"

cd chapter9/phone-agent

# Single-project compatibility path, still supported during migration:
# python -m pip install -r requirements.txt

cp env.example .env
```

`.env` 必须包含 `PINE_ACCESS_TOKEN`、`PINE_USER_ID` 以及用于 ReAct/结构化提取的 `OPENAI_API_KEY`。Pine 账号可通过 SDK 的 `PineVoice.auth.request_code()` / `verify_code()` 获取凭证。号码必须采用 E.164 格式；当前 SDK 支持 +1、+44、+61、+64、+65、+353、+852，且电话 Agent 只说英语。请只拨打自己或明确获准测试的号码。

## 验收：直接 API 与 ReAct 对照

直接调用要求调用者预先填全每个参数：

```bash
python direct_call.py \
  --phone +14155551234 \
  --name "Dr Smith Office" \
  --goal "Book a cleaning Tuesday at 3pm" \
  --context "Patient Jane Doe" \
  --instructions "If 3pm is unavailable, ask for 2-4pm; confirm date, time, dentist and confirmation number"
```

ReAct 路径只接收自然语言任务，自主规划参数、需要时搜索或追问，并读取真实通话记录：

```bash
python demo.py \
  --task "Call Dr Smith Office and book a cleaning Tuesday afternoon for Jane Doe" \
  --phone +14155551234
```

输出包含真实 `call_id`、状态、通话时长、credits、逐轮 transcript、`goal_achieved`、`key_fields` 和最终用户汇报。官方 SDK 通过 SSE 等待最终结果，失败时自动退回轮询；电话可能持续数分钟。

## 测试双（不计作实验结果）

`python demo.py --dry-run` 会显式选用 `test_double.py`，仅用于测试 ReAct 数据契约；它不会访问电话网络，不能作为实验 9-2 的验收证据。默认路径没有 mock fallback。

```bash
pytest -q
```

单元测试验证真实 SDK 的参数形状、结果归一化和 E.164 防护。真实拨号验收还需要有效 Pine 凭证及获准拨打的测试号码。

2026-07-29 已使用本机现有 Pine 配置向真实 gateway 做无副作用的不存在-call 查询；gateway 返回 `CallError: Call not found` 而非认证错误，证明凭证和 SDK/gateway 链路有效。脱敏记录见 `validation/credential_check.json`。由于工作区没有提供一个明确获准拨打的 E.164 测试号码，本次没有擅自发起电话；这项记录不能替代“成功拨打测试电话”的最终验收。

---

## English

The default path uses the official `pine-voice` SDK and the real telephone network. `direct_call.py` is the fixed-parameter control; `demo.py` is the ReAct treatment, including live public-business phone lookup, clarification, real calling, transcript fact extraction, and a user report. `--dry-run` is an explicit test double and never counts as experiment evidence. Configure `PINE_ACCESS_TOKEN`, `PINE_USER_ID`, and `OPENAI_API_KEY`, use an authorized E.164 test number, and follow the commands above.
