# 实验 9-2：WebRTC 电话 Agent

本实验把“电话”定义为一个用户主动加入的实时语音会话，而不是 PSTN 号码。运行本地服务后，用户在浏览器中授权麦克风；浏览器通过标准 WebRTC SDP/ICE 与本地 `aiortc` peer 建连，发送麦克风 RTP、接收服务端连接音轨 RTP，并通过 WebRTC data channel 传递 Agent 与用户回合。**不需要 E.164 号码、Pine 账号、电话运营商或实时语音 API 账户。**

浏览器把 SDP offer 交给本地 FastAPI 服务，服务端的 [`aiortc`](https://aiortc.readthedocs.io/) peer 返回 SDP answer 并终止媒体会话。Agent 文本通过同一 peer connection 的 data channel 到达浏览器，再由浏览器 `speechSynthesis` 发声；用户可使用浏览器 speech recognition 说出一个回合，也可用文字输入作为无障碍回退。文字回退不会绕过传输门禁：麦克风音轨和双向 RTP 仍须真实存在，服务端也必须实际消费收到的音频帧。

## 直接调用与 ReAct 对照

两组使用完全相同的 WebRTC 媒体和 `complete_task` 结果工具，差别只在规划层：

| 组别 | 调用者输入 | Agent 行为 |
| --- | --- | --- |
| 直接组（control） | 姓名、目标、上下文、指令四项都必须填全 | 原样构造实时会话 |
| ReAct 组（treatment） | 只给一段可能缺信息的自然语言任务 | ReAct 规划器记录 observation/reason/action 摘要，识别缺失字段，在语音通话中询问、复述并确认 |

`complete_task` 只保存用户在本次会话中明确确认的字段。实验不会声称真正修改了诊所、餐厅或账户等外部系统。

## 安装和运行

```bash
# 仓库根目录；uv.lock 固定 Python 依赖
uv sync --locked --python 3.12 --extra ch9 --extra dev

cd chapter9/phone-agent
cp env.example .env
# 无需 API key；如需用托管模型替换本地规划器，可选填一个 provider key

# ReAct：输入一段自然语言任务，浏览器自动打开
uv run --extra ch9 python demo.py \
  --task "Call me to arrange a dental checkup; ask for the missing time and confirmation code"

# 直接组：四个参数必须全部给出
uv run --extra ch9 python direct_call.py \
  --name "Jane Doe" \
  --goal "Confirm a dental-checkup time" \
  --context "Tuesday 2pm to 4pm is available" \
  --instructions "Ask for one time and confirmation code, repeat both, then save them"
```

也可以只运行 `uv run --extra ch9 uvicorn webrtc_app:app --host 127.0.0.1 --port 8765`，再打开 <http://127.0.0.1:8765>，在同一个界面切换两组。`localhost` 可直接使用浏览器麦克风；如果将页面部署到其他主机，必须配置 HTTPS 才能使用 `getUserMedia`。

界面提供语音识别和文字回合两种输入；自动验收用文字回合避免把浏览器 speech-recognition 服务变成外部依赖，但音频轨没有被替换。每通验收会话仍必须同时满足 offer/answer、ICE、data channel、浏览器麦克风轨、远端音频轨、双向 audio RTP packet/byte 大于零，以及服务端已消费麦克风 audio frame。

## 自动化验收和证据

`run_acceptance.py` 启动本地服务和系统 Chrome 的测试麦克风，分别跑一通直接组和 ReAct 组的**真实 browser-to-aiortc WebRTC 会话**。Canonical run 固定使用仓库内的 ReAct 缺失字段规划器和确认字段解析器，因此不依赖任何 provider 可用性；如果设置了可用的 `OPENAI_API_KEY` 或 `OPENROUTER_API_KEY`，交互运行可选择托管规划/对话模型。脚本拒绝把 mock、单元测试或只有 SDP 的预检算作完成；每组都必须收发 audio RTP、留下双向 transcript、调用 `complete_task` 并通过全部门禁。

```bash
uv run --extra ch9 --extra dev python run_acceptance.py

# 复核仓库保存的 canonical run（源文件与结果均按 SHA-256 校验）
uv run --extra ch9 python verify_acceptance.py \
  validation/runs/exp9-2-webrtc-20260731

uv run --extra ch9 --extra dev pytest -q
```

Canonical 结果位于 [`validation/runs/exp9-2-webrtc-20260731/`](validation/runs/exp9-2-webrtc-20260731/)；`manifest.json` 固定运行环境、Chrome 二进制、规划器/解析器、源码和结果 hash，`direct.json` / `react.json` 保存各自完整媒体门禁与结构化结果，`comparison.json` 保存两组差异。记录不包含 API key。

---

## English

Experiment 9-2 now calls the consenting user in a local browser instead of dialing the PSTN. The browser sends microphone RTP and receives a server audio track over a real browser-to-aiortc peer connection; agent/user turns share that peer connection's data channel and browser speech synthesis renders agent speech. No E.164 number, telephony account, or hosted realtime-media account is required.

The direct control requires name, goal, context, and instructions. The ReAct treatment accepts one incomplete natural-language task, identifies missing facts, gathers and confirms them in the call, and invokes the same local `complete_task` tool. Run `demo.py` or `direct_call.py` as shown above. Hosted text planning is optional; the canonical path is dependency-free.
