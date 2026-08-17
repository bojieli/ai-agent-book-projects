# 实验 9-5 实现与验收边界

正文验收入口是 `run_experiment_9_5.py`。`workflow_validation_demo.py` 与单元测试只是离线预检，不能替代真实模型、真实 HTTP 页面和真实 Chromium 运行。

## 可信边界

- 站点只监听 `127.0.0.1`，所有订单式副作用均为进程内虚构消息。
- Agent 每一步都真实调用配置的模型；证据只记录 API 请求/响应、端点和密钥环境变量名，不记录密钥值。
- 浏览器是 Playwright Chromium。最终成功读取服务端持久状态渲染出的 `sent-list`，不以点击完成或定位器命中代替任务结果。
- `validation_reset` 是独立 HTTP 请求。没有 reset 的工作流只能保存在候选区。
- `candidate`、`validated`、`invalid` 文件彼此隔离；只有 `validated` 可被意图检索。

## 编译产物

每个 `WorkflowStep` 保存动作类型、参数模板、XPath、CSS 和稳定属性证据，并附动作前与动作后谓词。`Workflow.final_predicates` 检查本次收件人、主题和正文确实出现在已发送列表。`Workflow.parameterize()` 同时替换动作参数和谓词中的占位符，防止第二次回放继续验证首轮字面量。

## 假成功对照

正式 campaign 对相同工作流和页面故障分别运行：

- `validate_state=False`：只要输入和点击没有抛异常便报告成功；
- `validate_state=True`：检查输入值、发送状态、页面状态和最终持久化列表。

“空正文”和“接受但不落库”使动作计数基线产生 100% 假成功，而状态验证组为 0%。页面版本变化则在发送按钮前置检查处停止，后端事件日志证明没有新增 `send_request`。

## 当前实证

`validation/real_20260729T171233Z/evidence.json` 使用 ARK `doubao-seed-1-6-flash-250615`，保存 4 个模型回执和完整浏览器/服务端轨迹。13/13 执行门槛通过；参数化回放 0 次 LLM 调用，探索/回放加速为 1.195 倍。这个数字是本机本次实测，不沿用旧文档中未经证据支持的“3–5 倍”或论文中的“8.5–13 倍”。
