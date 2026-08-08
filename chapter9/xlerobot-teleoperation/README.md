# 实验 9-8：专家控制建立机器人能力上限

这是一个可在本机 GPU 上完成的、非致动的桌面操作上限实验。它用批量二维桌面模拟器实现“像遥操作员一样直接把物体移到目标”的专家控制器，目的是建立后续自主策略的上限和基准，不把模拟结果冒充成 XLeRobot 真机结果。

## 运行

```bash
cd chapter9/xlerobot-teleoperation
python teleop.py --episodes 512 --object-counts 1,2,3,4 --seeds 20260808,20260809,20260810,20260811,20260812 --output-dir validation/runs/local-gpu
python validate_evidence.py validation/runs/local-gpu/evidence.json
```

脚本优先使用 CUDA，其次使用 Apple MPS；默认拒绝 CPU 回退。正式协议使用 5 个随机种子、4 种物体数量和每格 512 个回合，共 10240 个回合，并额外重复一个固定条件检查结果是否一致。`--allow-cpu` 只用于调试，不能作为正文实验结果。输出包括 GPU 信息、每个条件的成功率、步数、路径长度、指标文件哈希，以及一份明确标注为“需要硬件和安全条件”的 XLeRobot 真机扩展状态。

## 观察重点

- 专家控制器在随机物体位置上是否稳定完成所有目标；
- 完成时间和路径长度的分布；
- 这个结果只是“硬件加上一个理想控制者”的上限，不代表自主策略已经达到该水平。

## 真机扩展

XLeRobot 的键盘、Xbox、Joy-Con 和 VR 入口仍由 `upstream.lock.json` 记录，但它们需要真实机械臂、校准、急停和现场观察员。本实验的本地 GPU 验收不会打开串口，也不会执行任何真机动作；只有获得明确授权后，才可另行运行硬件 teleop 复现。
