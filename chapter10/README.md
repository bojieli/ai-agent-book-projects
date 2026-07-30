# 第 10 章 · 多 Agent 协作

> 群体智能高于个体：协作框架、上下文共享/隔离、涌现的「Agent 社会」

← [返回主目录](../README.md) · 📖 [读本章正文](../book/chapter10.md)

## 配套项目

| 编号 | 项目 | 类型 | 一句话说明 |
| :--: | --- | :--: | --- |
| 10-1 | [staged-system-prompt](staged-system-prompt/) | ✅ | 同一 Coding Agent 在需求澄清/实现/审查三阶段加载不同提示词与工具集，对话历史跨阶段共享，审查不通过可回退 |
| 10-2 | [multi-role-transfer](multi-role-transfer/) | ✅ | 共享上下文下的链式 handoff：多角色各有独立提示词与工具，通过 `transfer_to_agent` 自主切换 |
| 10-3 | [book-translation](book-translation/) | 🚧 | 四角色管理者模式及单 Agent 对照已有真实模型小样本结果；仍需按正文使用含大量插图和代码的技术书，并完整比较质量、效率和资源消耗 |
| 10-4 | `use-computer-while-calling/` | 📖 | 本地路径对应固定到 `7d70007…` 的 [19PINE-AI/TalkAct](https://github.com/19PINE-AI/TalkAct)：快慢 Agent 通过进程内 `SharedState` 黑板、状态摘要和双向文本队列协作；当前 checkout 缺失，未声称运行 |
| 10-5 | [autonomous-phone-registration](autonomous-phone-registration/) | 🚧 | 真实 Playwright 表单与真实 LLM 自主触发 Phone Agent；校验、重问、双向并行、脱敏时序和选择性提交已实现并验证，但 PSTN/真人音频因无授权参与者仍为 `not_run`，整体验收 `incomplete` |
| 10-6 | [parallel-web-research](parallel-web-research/) | ✅ | N 个独立 Playwright 浏览器会话并行搜索真实大学网站，真实 LLM 证据抽取；状态监控、超时/错误隔离、单次结算、级联终止 ack、资源审计及同站串并行实测齐全 |
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
