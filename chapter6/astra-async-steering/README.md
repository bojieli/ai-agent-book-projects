# 实验 6-3：模型原生异步与回合中途引导

← [第六章实验目录](../README.md) · [第六章正文](../../book/chapter6.md)

2026-09-05，使用真实 OpenAI Responses WebSocket API 完成五组、每组三次运行，**15/15 达到各自验收条件**。其中 12 次验证 Astra 的行为，3 次验证 `gpt-5.6-sol` 明确拒绝 steering。场地数据、工具延迟与用户更新由本地脚本控制；模型响应和服务端事件均来自真实 API。

本实验接续实验 6-1 的事件队列和实验 6-2 的同步接口兼容方案。它验证的是模型和 API 的原生能力，不需要开发者先训练一个新模型。

正文编号调整为 6-3；2026-09-05 的运行记录及源码快照保留当时的 `exp6-14-*` 标识和哈希，以下复核命令继续使用这些归档路径。

## 任务与实验变量

为一次模拟会议选择满足人数与预算的最便宜场地，初始预算为 2000、人数为 20。

| 场地 | 价格 | 容量 | 初始要求 | 更新后的要求 |
| --- | ---: | ---: | --- | --- |
| A | 1800 | 30 | 选择 A | 超预算 |
| B | 900 | 12 | 容量不足 | 选择 B |
| C | 600 | 8 | 容量不足 | 容量不足 |

`lookup_venues` 等待 8 秒后返回这张表和一个新生成的随机 `receipt`。工具调用前的提示词不包含该回执，最终答案必须正确引用它，并标明 `source: demo`。只有 steering 组会收到两条更新：预算改为 1000，人数改为 10。两条都生效时应选择 B。

| 组别 | 模型与设置 | 触发条件 | 验收重点 |
| --- | --- | --- | --- |
| `sync` | Astra，`async: false` | 完整调用项到达后执行查询 | 工具结果到达前没有后续文本；最终选择 A |
| `async` | Astra，`async: true` | 同上 | 工具执行期间继续输出独立准备清单；最终选择 A |
| `steer_reasoning` | Astra，无工具，表格直接放入输入 | 收到 reasoning 的 `response.output_item.added` 后发送 `response.steer` | 原 response 尚未结束；更新被 accepted；自动续接，最终选择 B |
| `async_steer` | Astra，`async: true` | 工具任务已启动、结果尚未完成时发送 steering | 两条更新同时生效；工具只执行一次；真实结果仍用原始 `call_id` 归还，最终选择 B |
| `unsupported_steer` | `gpt-5.6-sol` | 收到 `response.created` 后发送相同更新 | 返回该请求对应的 `steering_not_supported`，其他错误不算通过 |

`sync` / `async` 是同模型对照：模型、任务、提示词、`reasoning.effort: low`、`parallel_tool_calls: false` 都相同，只改变工具定义的 `async`。无工具的推理组使用 `medium`，以观察 reasoning 项的生命周期；它不是与前两组等任务的耗时对照。每组固定运行三次，不以成功重试替换失败样本。

## 运行与离线复核

需要 Python 3.11 或更高版本，以及能访问相应模型且有可用余额的 OpenAI API 项目。脚本读取环境中的 `OPENAI_API_KEY`，直连 `wss://api.openai.com/v1/responses`。

```bash
cd chapter6/astra-async-steering
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# 先在当前终端配置 OPENAI_API_KEY，再运行全部五组。
python experiment.py --repeats 3

# 也可以只运行单组；此时不能把结果称为完整五组实验。
python experiment.py --arms async_steer --repeats 1
```

使用固定版本 `websockets==15.0.1` 直接发送文档定义的 JSON 事件，因此不要求本机 OpenAI SDK 已更新到包含 `response.steer` 的版本。正式运行使用 Python 3.11.4。模型请求 ID 和返回的模型 ID 分别记录；模型别名仍可能随服务端更新，固定脚本不等于固定模型权重。

无需 API Key 即可复核已保存的正式运行：

```bash
python experiment.py --replay validation/runs/exp6-14-20260905-formal
python test_judging.py
python summarize.py validation/runs/exp6-14-20260905-formal \
  --out validation/summary.json
```

第一条核对 manifest 中列出的 SHA-256，并从原始事件重新计算每项验收，与保存的判定逐项比较。第二条运行 10 项验收测试：以真实预实验轨迹为基础，故意制造仅 accepted 而没有续接、错误 call ID、重复提交、虚构回执、遗漏预算更新、错误模型、余额不足冒充能力拒绝、使用旧 parent、缺少重叠输出等情况，确认它们不会被误判成功。第三条重新生成[结构化汇总](validation/summary.json)，并额外检查 steering 是否确实发生在可观察的 reasoning 项开始与完成之间。

## 正式实测结果

正式运行：[exp6-14-20260905-formal](validation/runs/exp6-14-20260905-formal/manifest.json)，UTC 2026-09-05 14:17:03–14:19:30。实际返回模型为 `gpt-6-astra` 和 `gpt-5.6-sol`，没有替换模型或使用代理网关。

| 组别 | 验收通过 | 关键观测 | 端到端耗时中位数 |
| --- | ---: | --- | ---: |
| 同步工具 | 3/3 | 0/3 在工具完成前输出独立清单，最终均选 A | 12.583 秒 |
| 原生异步工具 | 3/3 | 3/3 在工具执行期间输出独立清单，最终均选 A | 12.684 秒 |
| reasoning 期间 steering | 3/3 | 3/3 原 response 以 `incomplete(reason=steered)` 结束，自动续接并选 B | 8.107 秒 |
| 异步工具挂起时 steering | 3/3 | 3/3 原 response 正常完成后自动续接，随后接收原调用结果并选 B | 12.575 秒 |
| 旧模型负对照 | 3/3 | 3/3 返回 `steering_not_supported` | 不作为任务完成时间 |

九次带工具的运行均只有一次工具调用、一次本地执行和一次真实结果提交；最终回执全部匹配。六次 Astra steering 的最终答案都同时采用预算 1000 和人数 10。reasoning 组的三次 steering 均落在同一个 reasoning 项的开始与完成事件之间，而非等其完成后再追加下一轮用户输入。

**这次没有显示最终完成更快。** 同步和异步两组的耗时中位数接近；异步组在等待数据期间先完成了独立工作。其余组的任务、推理设置和 response 数量不同，不能把表中耗时直接当作性能排名。时间戳来自客户端单调时钟，网络缓冲可能使连续事件几乎同时到达，不能用毫秒级事件间隔推断服务端实际解码速度。

服务端报告的正式 Astra token 用量合计为输入 11,616、输出 1,655，包含已中断 response 报告的用量。负对照没有报告 usage，汇总中的零表示“没有报告值可相加”，不代表已证实免费；预实验也未计入上述用量。

## 一次真实时间线

以下对应[第一次工具挂起时 steering 的完整事件](validation/runs/exp6-14-20260905-formal/01-async_steer/events.jsonl)。表中将三个实际 response ID 缩写为 R1/R2/R3，秒数从该实验单元的客户端启动时刻起算。

| 秒 | 事件 | 含义 |
| ---: | --- | --- |
| 1.001 | `response.created`：R1 | 原任务开始 |
| 2.886 | 本地 `tool.started`，随后发送 `response.steer` | 查询已在后台运行，预算/人数更新进入同一连接 |
| 3.127 | `response.steer.accepted` | 服务端接收更新；还不能据此宣布已生效 |
| 3.628 | R1 `response.completed` | 原 response 正常完成；steering 不必总产生 incomplete |
| 3.689 | 自动 `response.created`：R2，parent 为 R1 | 客户端没有重新发起模型请求 |
| 5.076 | R2 `response.completed` | 已处理更新，仍等待真实场地数据 |
| 10.886 | 本地 `tool.ready` | 8 秒查询完成，生成真实回执 |
| 10.887 | 客户端 `response.create` | 使用原始工具 `call_id`，parent 指向最新 R2 |
| 11.196 | `response.created`：R3 | 接收工具数据并接续任务 |
| 12.575 | R3 `response.completed` | 同时满足新预算、新人数与真实回执，选 B |

另见[第一次 reasoning 期间 steering 的事件](validation/runs/exp6-14-20260905-formal/01-steer_reasoning/events.jsonl)：reasoning 项在 2.190 秒开始，随后发送更新，3.824 秒收到 `incomplete(reason=steered)`，3.950 秒自动创建后继 response，7.763 秒完成最终答案。

## 协议边界与证据范围

运行器有一个 WebSocket 读取循环，以及独立的本地工具任务。读取循环持续记录服务端事件；工具结果就绪后进入本地队列。若当前 response 仍在运行，结果留待后续 `response.create` 提交。已经 accepted 的 steering 由服务端拥有其接续权：客户端等待自动后继 response，或等待 `response.steer.pending` 指明所需输入，避免重复发起续接。

`response.steer` 承载用户消息；`function_call_output` 承载工具结果。把工具结果改写成一条用户消息，会丢失原始调用的协议归属，本实验不采用这种方式。脚本模拟了两条用户更新，不代表第三方邮件、Webhook 或任意 event 都能直接作为有用户权限的 steering 输入。

本次实测覆盖 function 工具、文本用户消息和单 Agent 会话。没有测 custom 工具、多工具乱序返回、长期任务、取消副作用、断线恢复、自动 compaction，以及 `response.steer.pending` 分支；六次 Astra steering 都直接产生了自动 continuation，没有 pending 事件。实现保留了文档要求的 pending 处理路径，其端到端行为仍需独立场景验证。公开 reasoning 项的开始/完成事件证明了可观察的注入时机，不能揭示或证明隐藏推理 token 的逐字保留，也不能据此推断模型采用了何种训练方法。

## 文件与运行来源

- [experiment.py](experiment.py)：实验控制、真实 API 调用、逐事件保存、自动验收和离线重判。
- [test_judging.py](test_judging.py)：基于真实预实验的 10 项反例测试。
- [summarize.py](summarize.py)：校验原始记录后生成汇总和 reasoning 时间窗审计。
- [validation/summary.json](validation/summary.json)：正式 15 次运行的派生汇总，记录原始 manifest 与汇总脚本哈希。
- [正式 manifest](validation/runs/exp6-14-20260905-formal/manifest.json)：逐次结果、环境版本和证据哈希。每个单元保存 `events.jsonl` 与 `acceptance.json`；`source/` 保存当次实验脚本、测试脚本和依赖版本。
- [第一次预实验](validation/runs/pilot-20260905-v1/manifest.json)：保留余额不足与一次连接失败，全部未通过，不计入正式结果。
- [余额恢复后的预实验](validation/runs/pilot-20260905-v2/manifest.json)：五组各一次通过，用作验收反例测试的原始轨迹，不混入正式统计。

预实验使用当时版本的判据；要逐项重判旧回执，使用其 `source/experiment.py --replay <运行目录>`，以免把后续增加的检查误作原始验收。正式运行与当前主脚本的判据相同。

## 官方依据（2026-09-05 核对）

- [Using GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model)：两项能力已公开提供，以及模型名 `gpt-6-astra`。
- [Async tool calling](https://developers.openai.com/api/docs/guides/async-tool-calling)：function/custom 工具的 `async: true`、应用执行职责、原始 `call_id`、后续结果归还与兼容范围。
- [Mid-turn steering](https://developers.openai.com/api/docs/guides/steering)：同连接 `response.steer`、accepted/自动 continuation/pending 事件流，以及 GPT-5.6 及更早模型不支持 steering。
- [Responses WebSocket events](https://developers.openai.com/api/reference/resources/responses/websocket-events#response.steer)：steering 只接受受支持的用户消息，及 conversation、自动 compaction 等请求组合的限制。
- [WebSocket mode](https://developers.openai.com/api/docs/guides/websocket-mode)：`previous_response_id`、增量输入、同连接状态与恢复语义。
