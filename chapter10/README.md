# 第 10 章 · 多 Agent 协作

> 群体智能高于个体：协作框架、上下文共享/隔离、涌现的「Agent 社会」

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter10.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | [正式 Kimi K3 v3](staged-system-prompt/runs/exp10-1-kimi-k3-20260730-v3/manifest.json)以 30 次真实调用跑通需求→实现→审查→回退→复审→批准，受控真实 lint 缺陷被拒绝并修复，13 项门禁与全部源码/回执/产物 hash 均通过 |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | [同一次真实 Kimi K2.5 + Tavily 验收](multi-role-transfer/validation/runs/exp10-2-kimi-k2.5-tavily-receipts-20260730-v3/manifest.json)在共享历史上完成 `triage → research → data_analysis → writing → triage`：9/9 行为门禁与 6/6 溯源门禁全通过；9 份 Moonshot 原始请求/响应（唯一 response ID/usage）、3 份去凭据 Tavily 原始 HTTP 回执、5 个运行时源码 hash 与 4 个 artifact hash 均由 acceptance/manifest 绑定且复核一致 |
| 10-3 | [book-translation](book-translation/) | ✅ | [正式 ARK v4](book-translation/validation/real_20260730T061500Z_v4/evidence.json)在英文版第 1–2 章的 242,090 字节、23 图、14 代码块上完成 26 单元双臂对照：12/12 门禁、39 份原始裁判回执和 37 个溯源 hash 均通过；Manager 上下文缩小 20.43×、token 减少 6.48×且匿名质量 4.654 > 4.481，但慢 6.57%，宽泛术语一致率与 Markdown 精确保真也出现明确负结果 |
| 10-4 | [TalkAct 复现记录](talkact-reproduction/) + `use-computer-while-calling/` | 📖 | [Anthropic-caller 正式运行](talkact-reproduction/validation/runs/exp10-4-talkact-anthropic-caller-20260803-v2/acceptance.json)保留 16/16 局并通过 17/17 门禁：两臂任务成功率均为 1.0；duplex 语音延迟中位数 2.32 秒，对照为 12.52 秒（改善 5.40×），但对照的探针正确率更高且平均总耗时更低。因 Gemini 凭据无效，本次使用源码支持的 Anthropic Sonnet caller override，结果不得与上游默认 Gemini-caller 配置静默合并 |
| 10-5 | [autonomous-phone-registration](autonomous-phone-registration/) | ✅ | [正式 WebRTC raw-v4](autonomous-phone-registration/validation/runs/exp10-5-webrtc-raw-20260731-v4/manifest.json)用真实 ARK 自主工具调用、Playwright、双向 RTP、本机 TTS/Whisper ASR 和一次 localhost 提交跑通 6 字段注册：9/9 行为门禁通过；不含凭据的原始 ARK 请求/响应保留 `tool_choice=auto`、工具参数、ID/model/usage/延迟，独立 validator 重算全部源码/输入/产物 hash 并证明原始参数与 decision 精确一致，8/8 溯源检查及四类篡改测试通过；不再要求 PSTN/E.164 |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | [同一次真实验收运行](parallel-web-research/validation/runs/exp10-6-real-receipts-20260730-v2/manifest.json)覆盖 10 站点串并行与 4 会话级联：12/12 门禁通过、实测加速 1.872×、24 份完整浏览器观测、3 份带 response ID/usage 的 ARK 原始响应和 114 条总线事件均由运行时 manifest 绑定；7 个实际源码/输入 hash 与全部 artifact hash 已复核一致，凭据扫描为零 |
| 10-7 | [Generative Agents 正式复现](generative-agents/) + `generative_agents/` | 📖 | [Qwen 3.7 Flash 正式运行](generative-agents/validation/runs/exp10-7-qwen37flash-20260804-v1/acceptance.json)完成三组各 25 Agent、17,280 步、两个虚拟日的完整社会实验；148,856 份真实 provider 回执零逻辑错误，14/14 门禁通过。自定义气候韧性工作坊未扩散出发起人，是保留的负结果；关闭反思后证据关联反思为零，四项盲评可信度均下降 |
| 10-8 | [voice-werewolf](voice-werewolf/) | ✅ | [同一次 v11 真实验收](voice-werewolf/validation/runs/exp10-8-simulated-user-openrouter-20260803-v11/acceptance_report.json)完成 3 个昼夜投票循环、6 次 LLM 工具→macOS `say`→OpenRouter 原生音频 ASR 回环、信息隔离和规则胜负；四项策略门禁全通过，13 个唯一响应 ID、1,650 音频 token、27 个非空 TTS 事件、动作历史和裁判溯源均保留，独立验证复核 6/6 音频动作边界 |

## 实验 10-4 / 10-7 外部复现锚点

这两个源码目录不随本书 vendoring。10-4 在 2026-08-03 临时 checkout 中固定并核对不可变提交，随后完成依赖安装、环境启动与 16 局正式基准。默认 Gemini 模拟来电者凭据无效，因此依照源码支持的 `CUV_USER_MODEL` 覆盖为 Anthropic Sonnet；该同族 caller 偏差、完整结果和局限均记录在[复现报告](talkact-reproduction/)中。10-7 也在临时、干净且固定到精确提交的 checkout 上完成；本仓库保留运行器、全部最终状态、逐步 movement、记忆、原始回执、盲评与 hash manifest，而不 vendoring 上游源码。

| 实验 | 权威上游 | 精确本地路径 | 固定提交与已核对入口 |
| :--: | --- | --- | --- |
| 10-4 | [`19PINE-AI/TalkAct`](https://github.com/19PINE-AI/TalkAct) | `chapter10/use-computer-while-calling` | `7d70007f72d45ddfc1a14e8e229b6d444e4919a2`；环境 `envs/app.py`，对照基准 `bench/run_bench.py` |
| 10-7 | [`joonspk-research/generative_agents`](https://github.com/joonspk-research/generative_agents) | `chapter10/generative_agents` | `fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4`；Django 前端 `environment/frontend_server/manage.py`，模拟器 `reverie/backend_server/reverie.py` |

从本书仓库根目录获取并核验固定源码：

```bash
git clone https://github.com/19PINE-AI/TalkAct.git chapter10/use-computer-while-calling
git -C chapter10/use-computer-while-calling fetch origin 7d70007f72d45ddfc1a14e8e229b6d444e4919a2
git -C chapter10/use-computer-while-calling checkout --detach 7d70007f72d45ddfc1a14e8e229b6d444e4919a2
git -C chapter10/use-computer-while-calling rev-parse HEAD
test "$(git -C chapter10/use-computer-while-calling rev-parse HEAD)" = "7d70007f72d45ddfc1a14e8e229b6d444e4919a2"

git clone https://github.com/joonspk-research/generative_agents.git chapter10/generative_agents
git -C chapter10/generative_agents fetch origin fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4
git -C chapter10/generative_agents checkout --detach fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4
git -C chapter10/generative_agents rev-parse HEAD
test "$(git -C chapter10/generative_agents rev-parse HEAD)" = "fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4"
```

TalkAct `7d70007…` 要求 Python 3.12。该版本不是 WebSocket 桥：`src/cuv/runner.py` 并发运行 fast/slow Agent，二者通过进程内 `SharedState` 黑板共享滚动 digest、transcript/action log，并用 `fast_to_slow` / `slow_to_fast` 文本队列传递 `@slow:`、`ask_user`、`tell_user` 等消息。本次正式运行使用的入口为：

```bash
cd chapter10/use-computer-while-calling
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
.venv/bin/python envs/app.py
CUV_USER_MODEL=claude-sonnet-4-5-20250929 .venv/bin/python bench/run_bench.py \
  --tasks forms-insurance booking-flight webmail-report meeting-helper \
  --conditions duplex strawman --seeds 2
```

Generative Agents `fe05a71…` 的上游测试环境是 Python 3.9.12，需按该提交 README 创建 `reverie/backend_server/utils.py`。前端在 `environment/frontend_server` 运行 `python manage.py runserver`，模拟器在 `reverie/backend_server` 运行 `python reverie.py`；25-Agent 场景选择 `base_the_ville_n25`。正式复现通过运行时适配层把旧 `openai==0.27.0` 调用映射到 Qwen 3.7 Flash 与 `text-embedding-v4`，没有修改固定上游 checkout；每组按 360 步持久化检查点并可恢复。

10-4 的验收要求两个 Agent **真实并发**且信息能双向传递。正式证据保留 39 次 fast→slow relay、33 次 slow→fast 事件和 91 个延迟样本；17 项 validator 门禁全部通过。正文允许固定拓扑下的点对点通信，也允许消息总线配合 Manager/协调 Agent；“没有协调器”不是验收条件。10-7 的三组完整运行均精确结束于 `February 15, 2023, 00:00:00`；关闭反思组新建的证据关联反思为零，基线在 25 人盲评中以 17:8 获偏好且四项均分更高。自定义事件只留在 Isabella 的记忆中，没有扩散，按预注册规则作为完整负结果保留。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 实现或实验要求的验收证据尚未完整；可能已有可运行代码，但不得视为完整验收 |
