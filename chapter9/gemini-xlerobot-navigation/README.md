# 实验 9-9：桌面操作规划与逐步检查

本实验把原来的导航任务改成桌面操作规划。RoboCrew 仍然负责高层智能体循环，XLeRobot 仍保留为可选的执行器接入对象；本地验收使用确定性的桌面模拟器，避免把 Gemini API、机械臂或串口可用性误报成实验结果。

## 任务

场景中有红色杯子、黄色纸张、托盘和垃圾盒。规划器需要完成：

```text
抓起红色杯子 → 放入托盘
抓起黄色纸张 → 放入垃圾盒
验证最终状态
```

工具契约只有五个职责明确、权限固定的工具，每次调用只完成一件明确的事：

```text
observe_scene()    pick(object_id)
place(object_id, target_id)
verify_state()     stop()
```

`pick` 和 `place` 在真实 XLeRobot 适配器中必须映射为经过标定、限速、有超时的动作原语；模型不能直接输出任意关节角。契约定义见 `xlerobot_tool_contract.py`。

## 运行

```bash
cd chapter9/gemini-xlerobot-navigation
python desktop_planner.py --episodes 128 --seeds 20260808,20260809,20260810 --failure-probabilities 0.0,0.25,0.5 --output-dir validation/runs/local-gpu
python validate_evidence.py validation/runs/local-gpu/evidence.json
```

正式协议使用 3 个随机种子、0、0.25、0.5 三档“瞬时失败”概率和每格 128 个回合，共 3456 个回合；这里的失败是模拟器人为注入的一次性抓取失败，不是声称真实机械臂的故障率。每个种子都重新训练并测试一个小型动作条件世界模型。脚本比较三种执行方式：

- `open_loop`：一次提交完整动作序列，忽略中途失败；
- `closed_loop`：每个技能后重新观察，失败时重试；
- `predictive`：使用世界模型比较候选技能，再执行并验收。

实验注入一次可恢复的抓取失败，记录各模式的成功率、工具调用次数、恢复次数、世界模型测试误差和完整事件日志。预期现象是开环策略会损失一部分任务，闭环和预测式策略能够恢复。

## XLeRobot/RoboCrew 扩展

真实运行需要将 `TOOL_CONTRACT` 绑定到固定版本的 RoboCrew 工具注册和 XLeRobot 手臂控制器，并增加工作空间、急停、观察员和动作回执门禁。当前仓库的本地 GPU 验收不会调用 Gemini API、打开串口或执行机器人动作；硬件扩展必须单独生成真机证据。
