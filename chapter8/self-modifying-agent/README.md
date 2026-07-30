# 实验 8-5：由失败轨迹触发 Agent 自我修改

本项目演示实验 8-5 的 Agent 自我修改：生产轨迹显示同一个 `retryable=false` 错误仍被连续调用时，系统应修改 Agent 的重试与熔断控制代码，而不是只在 Prompt 中追加一句“不要重复调用”。

机制单元测试与真实验收是两条不同路径：

```bash
python -m pytest -q test_evolution.py
python run_experiment_8_5.py \
  --provider ark --model doubao-seed-1-6-250615 --seed 8501
```

`python demo.py` 仍保留为单候选教学入口，不能单独关闭真实实验。`run_experiment_8_5.py` 才是验收入口：它先保留一个会禁用所有临时错误重试的已拒绝候选，把具体失败原因提供给真实 Coding Agent，再让确定性生成器和真实 Coding Agent 经过同一组模型外门槛。

如需改用 OpenAI 直连：

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your_api_key_here
python run_experiment_8_5.py --provider openai --model gpt-4o-mini
```

真实模式使用 OpenAI 兼容的 Chat Completions API 读取失败诊断和稳定源码，返回完整候选模块。模型输出仍只能写入 `validation/<run>/candidates/` 隔离目录；静态编译、失败重放、旧任务回归、发布决定与回滚版本全部由模型外部代码执行。若 LLM 生成了看似合理但破坏旧重试行为的补丁，命令会明确返回 `reject_candidate`。

实验从 `failure_trajectories.json` 聚合重复故障。只有同一模式在多条轨迹中得到支持才形成修改请求；诊断模块将根因定位到 `stable/retry_policy.py`。候选生成器从稳定源码产生最小 diff，但只写入 `output/candidate/`，不会覆盖正在运行的稳定版本。

验证阶段依次检查编译、公开函数签名、安全 AST、原失败轨迹、首次永久错误熔断、临时超时恢复、旧阈值回归、影子 Canary 和回滚制品。所有检查通过才生成 `release_to_canary`，绝不直接发布生产；否则返回 `reject_candidate`。`release_manifest.json` 记录失败簇、逐条来源轨迹及哈希、根因、目标组件与文件、影响预测、代码 diff、潜在回退、全部检查、候选哈希和回滚哈希。生成前后还会比较稳定代码、失败轨迹和验证器自身的 SHA-256，证明 Coding Agent 没有越权修改可信根。

真实运行的原始请求、原始响应、响应 ID、Token、延迟、请求/响应哈希和不含凭据的后端元数据保存在 `validation/<run>/evidence.json`；`validation/latest.json` 指向最近一次完整证据。当前仓库内的 Ark/Doubao Seed 1.6 规范运行使用 1,128 输入 Token、1,276 输出/推理 Token、2,404 总 Token；确定性候选与 LLM 候选均为 `release_to_canary`，故障调用均值从基线大于 1 降为 1，临时故障恢复率保持 1.0，旧任务回归数为 0；负对照按预期被拒绝。供应商没有返回金额字段，因此报告不会猜测美元成本。

确定性补丁只用于可复现对照；真实验收必须包含真实 Coding Agent 的 API 回执。候选分支、失败重放、旧任务回归、灰度和回滚协议不交给生成补丁的模型自行批准。稳定代码、审计日志和发布验证器属于可信根，不在普通自我修改权限之内。
