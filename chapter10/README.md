# 第 10 章 · 多 Agent 协作

> 群体智能高于个体：协作框架、上下文共享/隔离、涌现的「Agent 社会」

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter10.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | [正式 Kimi K3 v3](staged-system-prompt/runs/exp10-1-kimi-k3-20260730-v3/manifest.json)以 30 次真实调用跑通需求→实现→审查→回退→复审→批准，受控真实 lint 缺陷被拒绝并修复，13 项门禁与全部源码/回执/产物 hash 均通过 |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | [同一次真实 Kimi K2.5 + Tavily 验收](multi-role-transfer/validation/runs/exp10-2-kimi-k2.5-tavily-receipts-20260730-v3/manifest.json)在共享历史上完成 `triage → research → data_analysis → writing → triage`：9/9 行为门禁与 6/6 溯源门禁全通过；9 份 Moonshot 原始请求/响应（唯一 response ID/usage）、3 份去凭据 Tavily 原始 HTTP 回执、5 个运行时源码 hash 与 4 个 artifact hash 均由 acceptance/manifest 绑定且复核一致 |
| 10-3 | [book-translation](book-translation/) | ✅ | [正式 ARK v4](book-translation/validation/real_20260730T061500Z_v4/evidence.json)在英文版第 1–2 章的 242,090 字节、23 图、14 代码块上完成 26 单元双臂对照：12/12 门禁、39 份原始裁判回执和 37 个溯源 hash 均通过；Manager 上下文缩小 20.43×、token 减少 6.48×且匿名质量 4.654 > 4.481，但慢 6.57%，宽泛术语一致率与 Markdown 精确保真也出现明确负结果 |
| 10-4 | `use-computer-while-calling/` | 📖 | 本地路径对应固定到 `7d70007…` 的 [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct)：快慢 Agent 通过进程内 `SharedState` 黑板、状态摘要和双向文本队列协作；当前 checkout 缺失，未声称运行 |
| 10-5 | [autonomous-phone-registration](autonomous-phone-registration/) | ✅ | [正式 WebRTC v7](autonomous-phone-registration/validation/runs/exp10-5-webrtc-20260731-v7/manifest.json)用真实 ARK 自主工具调用、Playwright、双向 RTP、本机 TTS/Whisper ASR 和一次 localhost 提交跑通 6 字段注册：无效邮箱触发重问，5/5 问填区间重叠，9/9 门禁、运行时/产物 hash 与脱敏检查全通过；不再要求 PSTN/E.164 |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | [同一次真实验收运行](parallel-web-research/validation/runs/exp10-6-real-receipts-20260730-v2/manifest.json)覆盖 10 站点串并行与 4 会话级联：12/12 门禁通过、实测加速 1.872×、24 份完整浏览器观测、3 份带 response ID/usage 的 ARK 原始响应和 114 条总线事件均由运行时 manifest 绑定；7 个实际源码/输入 hash 与全部 artifact hash 已复核一致，凭据扫描为零 |
| 10-7 | `generative_agents/` | 📖 | 斯坦福「AI 小镇」生成式智能体；本地路径对应固定到 `fe05a71…` 的 `joonspk-research/generative_agents`，当前 checkout 缺失，未声称运行 |
| 10-8 | [voice-werewolf](voice-werewolf/) | 🚧 | 6–8 人、精确角色、真人席位、ASR/TTS/打断、三回合/胜负/策略与隔离门禁均已实现；无授权真人且 Audio API 返回 `insufficient_quota`，真人音频、三回合和策略验收仍未运行，整体 `incomplete` |

## 实验 10-4 / 10-7 外部复现锚点

这两个源码目录在 2026-07-30 当前工作区都**不存在**。同日只读上游审计已经固定不可变提交并核对版本特定入口；该审计只证明源码映射，不证明本书工作区安装、启动或执行过实验。

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

TalkAct `7d70007…` 要求 Python 3.12。该版本不是 WebSocket 桥：`src/cuv/runner.py` 并发运行 fast/slow Agent，二者通过进程内 `SharedState` 黑板共享滚动 digest、transcript/action log，并用 `fast_to_slow` / `slow_to_fast` 文本队列传递 `@slow:`、`ask_user`、`tell_user` 等消息。核对过但未在本次审计执行的入口为：

```bash
cd chapter10/use-computer-while-calling
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
.venv/bin/python envs/app.py
.venv/bin/python bench/run_bench.py \
  --tasks forms-insurance booking-flight webmail-report meeting-helper \
  --conditions duplex strawman --seeds 2
```

Generative Agents `fe05a71…` 的上游测试环境是 Python 3.9.12，需按该提交 README 创建 `reverie/backend_server/utils.py`。前端在 `environment/frontend_server` 运行 `python manage.py runserver`，模拟器在 `reverie/backend_server` 运行 `python reverie.py`；25-Agent 场景选择 `base_the_ville_n25`。该旧版本固定 `openai==0.27.0` 并使用旧模型别名，正式复现前需处理 API 兼容风险，但不能把兼容性修改或单进程启动当作实验完成。

10-4 的验收要求两个 Agent **真实并发**且信息能双向传递。正文允许固定拓扑下的点对点通信，也允许消息总线配合 Manager/协调 Agent；“没有协调器”不是验收条件。10-7 仍需 25 Agent 两天基线、记忆/反思日志、自定义场景与消融对照。仅完成 clone、安装或单个进程启动都不构成正文实验完成。

## 项目类型说明

| 图标 | 类型 | 含义 |
| :--: | --- | --- |
| ✅ | **可独立运行** | 本仓库自带完整代码，配置好 API Key 即可运行 |
| 📖 | **复现指南** | 依赖需自行 `git clone` 的**外部仓库**（训练框架、评测基准等） |
| 🚧 | **进行中** | 实现或实验要求的验收证据尚未完整；可能已有可运行代码，但不得视为完整验收 |
