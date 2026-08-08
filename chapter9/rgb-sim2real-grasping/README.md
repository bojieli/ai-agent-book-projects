# 实验 9-10：RGB 视觉策略的跨环境测试

这是一个可在本地 GPU 上完成的“仿真环境迁移到现实环境”代理实验。它不声称已经在 SO100 真机上完成零样本抓取，而是用可控的 RGB 训练环境和变化后的测试环境，检验训练时扩大画面变化范围是否有助于应对真实相机可能遇到的背景、光照和噪声差异。

## 运行

```bash
cd chapter9/rgb-sim2real-grasping
python pipeline.py --train-size 4096 --test-size 1024 --epochs 10 --seeds 20260808,20260809,20260810 --output-dir validation/runs/local-gpu
python validate_evidence.py validation/runs/local-gpu/evidence.json
```

正式协议使用 3 个随机种子、4 种训练条件、2 种测试环境，每种条件训练 4096 个样本、训练 10 轮。脚本训练相同结构的 RGB 策略：

- `source_clean`：只看固定的训练画面；
- `source_background`：只改变训练背景；
- `source_appearance`：只改变物体外观；
- `source_full`：同时改变背景、外观、光照和噪声。

所有策略都在固定训练画面和两种变化后的测试环境中测试。验收要求固定画面策略在训练环境的准确率超过 0.85，完整随机化策略在两个测试环境的准确率超过 0.65，并且在两个环境都优于固定画面训练。输出包含模型 checkpoint、逐种子逐条件的指标矩阵、训练指标、训练画面/测试画面预览图和 SHA-256。

## 如何解读

这个实验只证明“扩大训练分布可以缓解视觉差距”，不证明仿真已经等价于真实机器人。真机部署仍需相机标定、真实参数测量、急停、观察员和 SO100 硬件；原 `upstream.lock.json` 记录的 LeRobot/ManiSkill 路径作为后续的硬件扩展保留。
