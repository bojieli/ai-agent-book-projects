# 实验 8-5：由失败轨迹触发 Agent 自我修改

本项目演示实验 8-5 的 Agent 自我修改：生产轨迹显示同一个 `retryable=false` 错误仍被连续调用时，系统应修改 Agent 的重试与熔断控制代码，而不是只在 Prompt 中追加一句“不要重复调用”。

```bash
python demo.py
python -m unittest -v test_evolution.py
```

`python demo.py` 使用确定性生成器，便于检查发布协议。要测试真实 LLM Coding Agent：

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your_api_key_here
python demo.py --generator llm --model gpt-5.6
```

真实模式使用 OpenAI Responses API 读取失败诊断和稳定源码，返回完整候选模块。模型输出仍只能写入 `output/candidate/`；静态编译、失败重放、旧任务回归、发布决定与回滚版本全部由模型外部代码执行。若 LLM 生成了看似合理但破坏旧重试行为的补丁，命令会明确返回 `reject_candidate`。

实验从 `failure_trajectories.json` 聚合重复故障。只有同一模式在多条轨迹中得到支持才形成修改请求；诊断模块将根因定位到 `stable/retry_policy.py`。候选生成器从稳定源码产生最小 diff，但只写入 `output/candidate/`，不会覆盖正在运行的稳定版本。

验证阶段先编译候选代码，再重放原失败轨迹，检查不可重试错误是否立即停止并打开熔断器；随后重测临时超时，确保原有重试与阈值行为没有退化。所有检查通过才生成 `release_to_canary`，否则返回 `reject_candidate`。`release_manifest.json` 记录来源案例、目标文件、代码 diff、检查结果、候选版本和回滚版本。

这里使用确定性补丁生成器保证离线复现；在生产系统中可以换成 Coding Agent，但候选分支、失败重放、旧任务回归、灰度和回滚协议不应交给生成补丁的模型自行绕过。稳定代码、审计日志和批准发布的验证器属于可信根，不在普通自我修改权限之内。
