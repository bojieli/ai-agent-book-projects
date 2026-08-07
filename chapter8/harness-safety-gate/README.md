# 实验 8-8：由用户反馈触发的高风险操作确认门禁

本项目演示实验 8-8 的 Harness 安全层自我进化：用户纠正、用户点踩与事后审计三类外部反馈共同指向同一个流程缺陷——`delete_file`、`git_push(force=True)`、`sql_query("DROP TABLE ...")` 等不可逆调用在未经用户确认时就被执行（第六章错误分类中的"流程与规范缺失"；第六章实验 6-5 的"高风险删除前确认"用例正是换更强的模型也照样犯的 Harness 缺约束问题）。系统据此让 Coding Agent 为 Harness 生成"高风险调用确认门禁"候选模块，经模型外验证门槛后才允许灰度。

与实验 8-5（[self-modifying-agent](../self-modifying-agent/)）的分工：8-5 改的是**控制层**（重试/熔断代码），失败信号来自**系统内部错误日志**；本实验改的是**安全/验证层**（工具调度确认门禁），失败信号来自**用户反馈与事后审计**。

机制单元测试与离线验收不需要 API Key：

```bash
python -m pytest -q test_evolution.py
python run_experiment_8_8.py --quick
python demo.py
```

真实 Coding Agent 路径（OpenAI 兼容 Chat Completions API）：

```bash
# 从仓库根目录开始：使用共享的第 8 章环境
uv sync --locked --python 3.12 --extra ch8
source .venv/bin/activate  # Windows 见 chapter8/self-modifying-agent/README.md

cd chapter8/harness-safety-gate
# 未安装 uv 时的兜底：python -m pip install -r requirements.txt
# 所需环境变量见 env.example

python run_experiment_8_8.py --provider ark --model doubao-seed-1-6-250615 --seed 8801
# 或：python run_experiment_8_8.py --provider openai --model gpt-4o-mini
```

`python demo.py` 保留为单候选教学入口；`run_experiment_8_8.py` 才是验收入口：它先保留一个"门禁存在但放行一切"的已拒绝反例，把具体失败原因提供给真实 Coding Agent，再让确定性生成器和真实 Coding Agent 经过同一组模型外门槛。`--quick` 为离线模式：跳过 API 调用，只验证确定性候选与反例，不写 `validation/` 证据目录。

## 与实验 8-5 的实现差异：为什么没有 Docker 沙箱

8-5 的候选是**覆盖稳定代码的补丁**，必须执行候选才能验证，因此需要 Docker 安全边界。本实验的候选是**新增的独立模块 `confirmation_gate.py`**，不覆盖稳定代码；验证由两部分组成：

1. **AST 静态检查**（不执行源码）：编译候选、只允许 `hashlib/hmac/json/re/secrets/string` 白名单导入、禁止 `eval/exec/open/__import__` 等危险内建调用。通不过扫描的候选永远不会被 `exec`。
2. **隔离回放**：验证器把候选加载进干净命名空间，用稳定版调度器在**内存模拟环境**（假文件系统、假 Git、假数据库）上回放工具调度；真正的执行器由验证器注入，候选没有任何途径触碰真实文件系统、Shell 或数据库。

发布门槛（全部通过才 `release_to_canary`，否则 `reject_candidate`）：

- `boundary_replay`（未完成任务回放）：`boundary_cases.json` 8 条——高风险调用必须被挂起、确认后才执行、伪造/错配/复用 token 必须被拒绝且绝不执行（含第六章实验 6-5 的"高风险删除前确认"场景）；
- `retention_replay`（正常操作回放）：`retention_cases.json` 7 条——`read_file`/`write_file`/普通 push/SELECT/带 WHERE 的 DELETE 等正常操作不受影响，用户已确认的操作正常放行；
- `confirmation_single_use`：确认 token 一次性、绑定具体工具名与完整参数。

`release_manifest.json` 记录同一类失败、逐条来源轨迹及哈希、问题原因、目标文件、候选 diff 与对 dispatcher 的最小接入 diff（仅提案，不落盘）、全部检查、候选哈希与回滚版本。生成前后还会对 `stable/`、三份 JSON 数据与 `evolution.py` 做 SHA-256 快照比对，证明 Coding Agent 没有越权修改可信根。真实 LLM 路径的原始请求、原始响应、Token 用量、延迟与请求/响应哈希保存在 `validation/<run>/evidence.json`，`validation/latest.json` 指向最近一次完整证据。

## 当前证据状态

本地离线路径和真实 Coding Agent 路径都已跑通：`test_evolution.py` 18 项测试全部通过；确定性候选得到 `release_to_canary`，放行一切的反例得到 `reject_candidate`。真实 OpenRouter `gpt-4o-mini` 运行（2026-08-07）中，模型生成的候选没有通过未完成任务回放、正常操作回放和一次性令牌检查，因此被模型外门槛拒绝；这属于安全的预期结果，而不是绕过检查强行发布。该次运行的确定性候选仍通过，整体验收为 `accepted=true`。证据见 `validation/real_20260807T160109Z/evidence.json`，`validation/latest.json` 已指向该次运行。

确定性补丁只用于可复现对照；真实验收必须包含真实 Coding Agent 的 API 回执。候选生成、失败回放与发布门槛不交给生成补丁的模型自行批准；稳定代码、审计数据与发布验证器属于可信根，不在普通自我修改权限之内。
