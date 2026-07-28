# Experiment 5-8: Production Log Diagnosis / 实验 5-8：生产日志的智能诊断系统

> Companion lab for *AI Agents in Depth*, Chapter 5 — diagnose trajectories + architecture + PRD → structured report → regression tests → replay → (mock) GitHub Issues.  
> 《深入理解 AI Agent》第 5 章：诊断 Agent 读轨迹/架构/PRD，定位根因、生成回归测试、重放验证，并（mock）对接 GitHub。

← [Chapter 5 index / 返回第 5 章目录](../README.md)

---

## English

### Purpose

Production Agents emit large **trajectory logs**. Finding issues, root causes, and building regression tests is expensive. This lab automates:

**Read trajectory set + architecture + PRD → locate issues, structured report → generate regression cases → replay framework executes for real → (mock) GitHub Issues via MCP.**

### Diagnosis pipeline

```
data/trajectories.jsonl  (production trajectories with known issues)
data/architecture.md     (system architecture)          ┐
data/PRD.md              (product requirements)          ├─► [LLM] diagnose()      structured issue report
                                             ┘        │
                                                      ▼
                                            [LLM] gen_test_cases()   regression cases (trajectory IDs + turns)
                                                      │
                                                      ▼
                                            replay.py replay framework
                                              (A) unfixed SUT → FAIL (reproduce bug)
                                              (B) fixed SUT → PASS (verify fix)
                                                      │
                                                      ▼
                                            github_mcp.py  (mock) print/write GitHub Issues
```

- `diagnoser.py`: diagnosis Agent; two real OpenAI calls (default gpt-5.6-luna, JSON mode).
- `sut.py`: **deterministic** system-under-test simulator. `fixed=False` reproduces bugs; `fixed=True` fixed behavior.
- `replay.py`: regression replay. Trajectory input → replay `sut` → evaluate asserts on new trajectory (4 built-in assert DSL kinds).
- `github_mcp.py`: GitHub Issue create; default mock (print + `output/github_issues.json`).

### Seeded known issues (Agent should find)

| Trajectory | Issue | PRD violated | Module |
|------|------|----------|----------|
| T-1001 / T-1002 | Skipped mandatory `verify_refund_eligibility` before refund | R1 (P0) | order_service |
| T-1002 | `process_refund` **repeated failures**, no backoff, false success | R2 (P0) | payment_service |
| T-1003 | `check_stock` latency 8300ms **timeout without degrade** | R3 (P1) | inventory_service |
| T-1004 | Healthy trajectory (control) | — | — |

### Run

```bash
pip install -r requirements.txt
cp env.example .env      # OPENAI_API_KEY (default gpt-5.6-luna); or OPENROUTER_API_KEY
python demo.py           # full pipeline (two real LLM calls)
```

`demo.py` once: read trajectories → diagnosis report → regression cases → replay pass/fail → (mock) GitHub Issue.

Common flags (`python demo.py -h`):

- `--smoke`: **no-API smoke**—skip LLM; built-in diagnosis + replay + GitHub mock only (exit 0 if green). CI / no key.
- `--model gpt-5.6`: override model (same as `OPENAI_MODEL`).
- `--data-dir DIR`: input dir with `trajectories.jsonl` + `architecture.md` + `PRD.md` (default `data/`).
- `--output FILE`: mock Issue write path (default `output/github_issues.json`).
- `--create-issue`: **real** Issues via MCP (`GITHUB_TOKEN` + `GITHUB_REPO`; falls back to mock if missing).
- `--no-github`: skip step 4.

### Sample real output (excerpt)

Diagnosis found all 3 seeded issue classes:

```
[问题 1] 未进行退款资格校验
  优先级 : P0    模块: order_service    PRD: R1
  轨迹   : ['T-1001', 'T-1002']  关键轮次: [3]
[问题 2] 支付重试机制未正确实现
  优先级 : P0    模块: payment_service    PRD: R2
[问题 3] 库存查询延迟未降级处理
  优先级 : P1    模块: inventory_service    PRD: R3
```

Replay **actually runs** cases (reproduce then verify fix):

```
(A) 对『线上未修复』系统重放 —— 期望复现 bug（FAIL）
    [FAIL] RT-001 (T-1001)  工具 verify_refund_eligibility 缺失
    [FAIL] RT-002 (T-1002)  process_refund 调用 3 次, 失败 3 次, 末次失败
    [FAIL] RT-003 (T-1003)  check_stock 最大延迟 8300ms, 阈值 5000ms
(B) 对『修复后』系统重放 —— 期望修复被验证（PASS）
    [PASS] RT-001 (T-1001)  工具 verify_refund_eligibility 出现
    [PASS] RT-002 (T-1002)  process_refund 调用 2 次, 失败 1 次, 末次成功
    [PASS] RT-003 (T-1003)  check_stock 最大延迟 400ms, 阈值 5000ms
  小结：复现 bug 3/3 条；修复后通过 3/3 条。
```

Mock Issue example written to `output/github_issues.json`:

```
title  : [P0][order_service] 未进行退款资格校验
labels : ['module:order_service', 'priority:critical', 'auto-diagnosis']
body   : ## 问题描述 ... ## 关联回归测试用例 - RT-001 (轨迹 T-1001 第 3 轮) ...
```

### Regression assert DSL (built into replay)

Generated cases must use one of:

- `step_present` `{tool}`: tool must appear (e.g. mandatory pre-check).
- `tool_succeeds` `{tool}`: tool eventually succeeds; no “many fails then fake success”.
- `latency_under` `{tool, threshold_ms}`: single-call latency under threshold.
- `final_status_is` `{value}`: final task status equals value.

### Adapt / extend

- **Model**: `OPENAI_MODEL` or `python demo.py --model <name>`. Default `gpt-5.6-luna`, JSON mode.
- **Provider**: official `openai` SDK + `OPENAI_BASE_URL` + provider key/model, e.g.:

  ```bash
  export OPENAI_BASE_URL=https://api.moonshot.cn/v1
  export OPENAI_API_KEY=sk-...
  export OPENAI_MODEL=kimi-k3
  python demo.py
  ```

- **Logs**: replace `data/trajectories.jsonl` (`trajectory_id / task / task_input / turns[] / final_status`; turns with `module/tool/input/output/status/latency_ms`); update `architecture.md` / `PRD.md`. Adjust `sut.py` / `replay.py` if fields differ.
- **Real GitHub MCP**: next section; `GITHUB_TOKEN` + `GITHUB_REPO` + `--create-issue`.

### Real GitHub MCP (token required; default mock)

Default is mock; `--create-issue` goes live. Implementation in `github_mcp._create_issues_via_mcp()`: MCP client (`mcp` SDK, stdio) to official GitHub MCP Server, `create_issue` with `build_issue()` fields.

1. GitHub PAT with `repo` → `.env` `GITHUB_TOKEN`; set `GITHUB_REPO=owner/repo`.
2. Machine can start official GitHub MCP Server (default Docker `ghcr.io/github/github-mcp-server`); override with `GITHUB_MCP_COMMAND` (token as `GITHUB_PERSONAL_ACCESS_TOKEN`).
3. `pip install mcp` (this path only).
4. `python demo.py --create-issue`. Missing token/repo → tip + mock fallback.

### Limitations

- `sut.py` is a **deterministic sim** so replay can truly pass/fail; real systems need real stubs/replay.
- Diagnosis quality depends on LLM. gpt-5.6-luna stably finds R1/R2/R3 on this data; it often splits R1 across T-1001 and T-1002 (4 issues vs 3 merged). For payment retry asserts it may choose `final_status_is:failed` instead of `tool_succeeds` (fixed SUT ends success → FAIL after fix, e.g. 3/4). Tool names sometimes get module prefixes incompatible with bare-name matching (further fails). `--smoke` built-in cases are deterministic 3/3.
- GitHub create is mock unless `--create-issue` with token + repo + MCP server.
- Trajectory schema is simplified vs production (tokens, sub-agent trees, etc.).

---

## 中文

### 目的

生产环境的 Agent 会产生大量**轨迹日志**（trajectory）。从中识别问题、定位根因、构建回归测试成本很高。
本实验让一个诊断 Agent 自动完成这条流水线：

**读轨迹集合 + 架构文档 + PRD → 定位问题、生成结构化报告 → 生成回归测试用例 → 重放框架真正执行验证 → (mock) 通过 MCP 对接 GitHub 创建 Issue。**

### 诊断流水线

```
data/trajectories.jsonl  (含已知问题的生产轨迹)
data/architecture.md     (系统架构)          ┐
data/PRD.md              (产品需求)          ├─► [LLM] diagnose()      结构化问题报告(优先级/模块/描述/建议)
                                             ┘        │
                                                      ▼
                                            [LLM] gen_test_cases()   回归测试用例(引用轨迹ID+交互轮次)
                                                      │
                                                      ▼
                                            replay.py 重放框架  ── 对同一输入重放被测系统并断言
                                              (A) 未修复系统 → FAIL(复现bug)
                                              (B) 修复后系统 → PASS(验证修复)
                                                      │
                                                      ▼
                                            github_mcp.py  (mock) 渲染并打印/落盘 GitHub Issue
```

- `diagnoser.py`：诊断 Agent，两次真实调用 OpenAI（默认 gpt-5.6-luna，JSON 模式）。
- `sut.py`：被测系统的**确定性仿真器**。`fixed=False` 复现线上 bug，`fixed=True` 模拟修复后行为。
- `replay.py`：回归测试重放框架。取轨迹输入 → 重放 `sut` → 在新轨迹上求值断言（内置 4 种断言 DSL）。
- `github_mcp.py`：GitHub Issue 创建，默认 mock（打印 + 写 `output/github_issues.json`）。

### 预置的已知问题（Agent 应能定位）

| 轨迹 | 问题 | 违反 PRD | 定位模块 |
|------|------|----------|----------|
| T-1001 / T-1002 | 退款前**跳过**了强制的 `verify_refund_eligibility` 校验 | R1 (P0) | order_service |
| T-1002 | `process_refund` **反复失败**、无退避、且最终误报成功 | R2 (P0) | payment_service |
| T-1003 | `check_stock` 延迟 8300ms **超时未降级** | R3 (P1) | inventory_service |
| T-1004 | 正常轨迹（对照组，无问题） | — | — |

### 运行

```bash
pip install -r requirements.txt
cp env.example .env      # 填入 OPENAI_API_KEY（模型默认 gpt-5.6-luna）；未配置时设 OPENROUTER_API_KEY 自动改走 OpenRouter
python demo.py           # 完整流程（两次真实 LLM 调用）
```

`demo.py` 一次跑完：读轨迹 → 诊断报告 → 回归测试用例 → 重放执行(通过/失败) → (mock) GitHub Issue。

常用参数（`python demo.py -h` 查看全部）：

- `--smoke`：**免 API 快速自检**，跳过 LLM，用内置诊断结果仅跑重放框架 + GitHub mock，验证管道是否端到端连通（全绿退出码 0）。适合无 Key 环境或 CI。
- `--model gpt-5.6`：临时覆盖模型（等价于设置 `OPENAI_MODEL`）。
- `--data-dir DIR`：换用自己的输入目录（需含 `trajectories.jsonl` + `architecture.md` + `PRD.md`，默认 `data/`）。
- `--output FILE`：mock GitHub Issue 的落盘路径（默认 `output/github_issues.json`）。
- `--create-issue`：**经 MCP 在真实仓库创建 Issue**（需 `GITHUB_TOKEN` + `GITHUB_REPO`，见下节；缺失时自动回退 mock）。
- `--no-github`：跳过步骤 4，不生成 GitHub Issue。

### 真实运行输出（节选）

诊断阶段，Agent 定位到全部 3 个预置问题：

```
[问题 1] 未进行退款资格校验
  优先级 : P0    模块: order_service    PRD: R1
  轨迹   : ['T-1001', 'T-1002']  关键轮次: [3]
[问题 2] 支付重试机制未正确实现
  优先级 : P0    模块: payment_service    PRD: R2
[问题 3] 库存查询延迟未降级处理
  优先级 : P1    模块: inventory_service    PRD: R3
```

回归测试用例被重放框架**真正执行**（先复现 bug、再验证修复）：

```
(A) 对『线上未修复』系统重放 —— 期望复现 bug（FAIL）
    [FAIL] RT-001 (T-1001)  工具 verify_refund_eligibility 缺失
    [FAIL] RT-002 (T-1002)  process_refund 调用 3 次, 失败 3 次, 末次失败
    [FAIL] RT-003 (T-1003)  check_stock 最大延迟 8300ms, 阈值 5000ms
(B) 对『修复后』系统重放 —— 期望修复被验证（PASS）
    [PASS] RT-001 (T-1001)  工具 verify_refund_eligibility 出现
    [PASS] RT-002 (T-1002)  process_refund 调用 2 次, 失败 1 次, 末次成功
    [PASS] RT-003 (T-1003)  check_stock 最大延迟 400ms, 阈值 5000ms
  小结：复现 bug 3/3 条；修复后通过 3/3 条。
```

mock GitHub Issue 打印并写入 `output/github_issues.json`，示例：

```
title  : [P0][order_service] 未进行退款资格校验
labels : ['module:order_service', 'priority:critical', 'auto-diagnosis']
body   : ## 问题描述 ... ## 关联回归测试用例 - RT-001 (轨迹 T-1001 第 3 轮) ...
```

### 回归测试断言 DSL（replay 框架内置）

Agent 生成的测试用例须使用以下断言之一，框架可自动求值：

- `step_present` `{tool}`：某工具必须出现（如强制前置校验）。
- `tool_succeeds` `{tool}`：某工具最终成功、且不存在"多次失败后误报成功"。
- `latency_under` `{tool, threshold_ms}`：某工具单次延迟低于阈值。
- `final_status_is` `{value}`：任务最终状态等于给定值。

### 如何适配/扩展

- **换模型**：设置 `OPENAI_MODEL`（或 `python demo.py --model <名称>`）。`diagnoser.py` 默认 `gpt-5.6-luna`，均走 JSON 模式；更强模型对复杂/隐性问题更稳。
- **换供应商**：本项目用官方 `openai` SDK，只需再设 `OPENAI_BASE_URL` 指向兼容 OpenAI 接口的服务（如 Moonshot / 火山方舟 / 本地 vLLM），配合该供应商的 `OPENAI_API_KEY` 与 `OPENAI_MODEL` 即可，无需改代码。例如：
  ```bash
  export OPENAI_BASE_URL=https://api.moonshot.cn/v1
  export OPENAI_API_KEY=sk-...          # 该供应商的 Key
  export OPENAI_MODEL=kimi-k3
  python demo.py
  ```
- **换日志**：把你自己的生产轨迹按 `data/trajectories.jsonl` 的结构（`trajectory_id / task / task_input / turns[] / final_status`，`turns` 内含 `module/tool/input/output/status/latency_ms`）落盘替换即可；同时更新 `data/architecture.md` 与 `data/PRD.md` 作为诊断依据。若轨迹字段不同，`sut.py`（重放桩）与 `replay.py`（断言求值）按新字段小幅调整。
- **接入真实 GitHub MCP**：见下一节，通过 `GITHUB_TOKEN` + `GITHUB_REPO` + `--create-issue` 把 `mock=False` 接通。

### 接入真实 GitHub MCP（需 token，默认 mock）

本实验默认 mock，`--create-issue` 才会真正联网。真实创建的实现已内置在
`github_mcp._create_issues_via_mcp()`：通过 MCP 客户端（`mcp` SDK，stdio）连接官方
GitHub MCP Server，逐个调用其 `create_issue` 工具，传入 `build_issue()` 生成的
`title / body / labels / assignees`。启用步骤：

1. 准备一个 GitHub Personal Access Token（`repo` 权限），写入 `.env` 的 `GITHUB_TOKEN`；
   并设置目标仓库 `GITHUB_REPO=owner/repo`。
2. 确保本机可启动官方 GitHub MCP Server。默认启动命令用官方 Docker 镜像
   `ghcr.io/github/github-mcp-server`；可用 `GITHUB_MCP_COMMAND` 覆盖为任意暴露
   `create_issue` 工具的 MCP Server（token 经 `GITHUB_PERSONAL_ACCESS_TOKEN` 注入其环境）。
3. `pip install mcp`（仅此路径需要；mock/自检不需要）。
4. 运行 `python demo.py --create-issue`。缺少 `GITHUB_TOKEN` / `GITHUB_REPO` 时会打印提示并
   自动回退 mock，避免误联网。

### 局限

- 被测系统 `sut.py` 是**确定性仿真**，用于让回归测试可真正重放、给出稳定的通过/失败；真实场景下重放需对接实际系统或录制/回放的依赖桩。
- 诊断质量取决于 LLM；gpt-5.6-luna 在本数据集能稳定定位全部 3 类预置问题（R1 校验缺失 / R2 重试误报 / R3 延迟未降级），步骤 1 诊断稳定；但它倾向把 R1「校验缺失」按 T-1001、T-1002 各报一条，故常输出 4 条问题（而非上文示例合并成的 3 条）。步骤 2 生成断言时，它稳定地为「支付重试」问题选用 `final_status_is:failed`（两次实跑均如此）而非上文示例的 `tool_succeeds`——因修复后的被测系统会重试成功（final_status=success），该断言在修复后重放中判 FAIL，使修复后通过数降为 3/4 而非满绿。此外它偶尔给 `step_present`/`latency_under` 的工具名加上模块前缀（如 `order_service.verify_refund_eligibility`），与重放框架按裸工具名匹配不符，会进一步压低修复后通过数（两次实跑分别得到 3/4 与 0/4）。`--smoke` 内置用例则确定性给出 3/3。
- GitHub 创建默认 mock，不联网；`--create-issue` 才经真实 MCP Server 联网创建（需 token + repo + 可用的 GitHub MCP Server）。
- 轨迹格式为简化示意，生产环境轨迹字段更丰富（token 用量、子 Agent 调用树等）。

---

## Notes / 说明

- Prefer `--smoke` without a key. / 无 Key 优先 `--smoke`。
- Commands/code/paths/env vars are identical in both language sections. / 命令、代码、路径与环境变量在中英文两侧保持一致。
