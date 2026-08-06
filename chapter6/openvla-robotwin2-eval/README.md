# 实验 6-12：OpenVLA + RoboTwin2 具身智能评估

本目录是第六章实验 6-12 的严格复现实验，不把论文数字、历史视频或命令 dry-run 当作本机结果。实验直接调用固定 commit 的 SimpleVLA-RL 上游 `trainer.val_only=True` 路径，在 `move_can_pot` 的同一组 IID/OOD 种子上对比 action chunk 1 与 25。

## 正式结果

正式单卡运行 `exp6-12-localgpu-20260803-v1` 已完成两个 arm 各 128 IID +
128 OOD episodes，并通过严格验收。`chunk_1` 为 0/256；`chunk_25` 为
26/256（IID 13/128、OOD 13/128），配对成功率提高 10.15625 个百分点。
这是一项完整的负面/低成功率结果，不把实验完成误写成模型表现良好。其余
486 个失败均在 200 action steps 上限结束，逐项绑定同次进程窗口内的 MP4 并
标为 `timeout`。汇总、逐 episode 记录、注释、运行身份以及 512 个外部视频
的内容哈希见 [`validation/runs/exp6-12-localgpu-20260803-v1/`](validation/runs/exp6-12-localgpu-20260803-v1/)。

## 来源、版本与所有权边界

本实验所调用的上游训练/评估实现是 [`PRIME-RL/SimpleVLA-RL`](https://github.com/PRIME-RL/SimpleVLA-RL/tree/7c51662df27b586f9e8a1ab35fcf849f2b8852f9)，固定提交为 `7c51662df27b586f9e8a1ab35fcf849f2b8852f9`，本地路径为 `chapter7/SimpleVLA-RL/SimpleVLA-RL`。

本目录中的 `experiment.py`、`config.json`、`task_config_exp6_12_three_view.yml` 和 `instrument_upstream.py` 是**本书自有的编排、协议与观测插桩**，不是 OpenVLA-OFT、RoboTwin2 或 SimpleVLA-RL 上游源码。它们使本书能够检查三视角、种子、episode 证据与严格完成门禁，但不会提供下列外部运行输入：

- 真实 OpenVLA-OFT checkpoint（应记录模型身份、revision 与文件哈希）
- 真实 RoboTwin2 checkout 及其明确 revision
- RoboTwin2 simulator、assets、系统库和可运行的 Linux/CUDA 环境
- 至少一张显存足以容纳 7B checkpoint 的兼容 NVIDIA GPU；多卡可提高吞吐，但不是 `val_only` 语义门禁

固定 SimpleVLA-RL checkout **不等于**上述依赖已经随仓库提供，也不能据此宣称 OpenVLA-OFT/RoboTwin2 运行栈已被完整固定。

## 与正文逐项对应

| 正文要求 | 本目录的直接证据 |
| --- | --- |
| OpenVLA / OpenVLA-OFT 架构 | 固定上游 commit、真实预训练 checkpoint 与上游生成路径写入 preflight/launch manifest |
| RoboTwin2 环境 | 要求真实 `ROBOTWIN2_PATH`，由上游安装脚本装入一次性 worktree，不修改干净 checkout |
| 三视角 RGB + 14 维关节状态 | 专用 task config 开启头部和左右腕部相机；launch 强制 `num_images_in_input=3` 和 `use_proprio=True` |
| 14 维动作 | launch 与逐 episode 证据同时校验 `action_token_len=14` |
| `move_can_pot` 随机化和空间约束 | preflight 直接检查真实任务实现、随机化配置与 OOD seed inventory |
| 运行预训练模型评估 | 两个 arm 都走上游 `val_only=True`，每 arm 包含 128 IID + 128 OOD episodes |
| 成功率 | 只接受 RoboTwin2 `eval_success` 经 reward manager 记录的布尔结果 |
| 完成时间 | 记录每条轨迹的 action steps，并按上游 50 Hz 控制频率报告 mean/std/min/p50/p95/max；不把 MP4 播放时长冒充执行时间 |
| 失败模式 | 每个失败 episode 必须有受控标签、具体观察证据和对应 rollout 视频，未分类即不完成 |
| 动作分块影响 | 相同任务、模型、IID/OOD seeds 下配对比较 chunk 1 与 chunk 25；由于 checkpoint head 固定预测 25 个动作，插桩在执行前显式截取配置长度的动作前缀与对应 action tokens |

当前上游默认脚本只设置一张 head-camera 图像；这不足以证明正文所述三视角观察空间。本实验的专用配置显式开启左右腕部相机，并把三张图送入上游已有的三视角分支。

## 运行

需要 Linux、兼容 NVIDIA GPU、RoboTwin2 checkout 和真实预训练 OpenVLA-OFT checkpoint：

```bash
export ROBOTWIN2_PATH=/abs/path/to/RoboTwin2
export OPENVLA_CHECKPOINT=/abs/path/to/openvla-oft-robotwin2-checkpoint
# 可选；默认使用上游 align.json
export SIMPLEVLA_ALIGN_PATH=/abs/path/to/align.json

python experiment.py preflight
python experiment.py prepare --run-dir runs/move-can-pot-real
python experiment.py launch --run-dir runs/move-can-pot-real --arm all
python experiment.py analyze \
  --run-dir runs/move-can-pot-real \
  --failure-annotations runs/move-can-pot-real/failure_annotations.json
```

正式运行完成后生成并复核可提交的证据包：

```bash
python finalize_evidence.py finalize
python finalize_evidence.py verify
```

checkpoint 与 512 个 MP4 不随 Git 分发；manifest 保存其不可变身份与 hash。
`verify` 在 clean clone 中复核所有提交内的源码和证据文件，并检查 manifest
确实绑定 512 个视频身份，而不会把缺少大体积外部媒体误报为重新执行成功。

`prepare` 创建 detached、一次性的 instrumented git worktree，在那里安装 RoboTwin2 和 episode recorder；`chapter7/SimpleVLA-RL/SimpleVLA-RL` 本身保持干净。两个真实 arm 的完整命令、环境、commit 和输出路径保存在 `launch_manifest.json`。

失败注释以 `arm|data_source|trial_seed` 为键，例如：

```json
{
  "chunk_25|robotwin2_move_can_pot_eval_ood|100100123": {
    "failure_mode": "placement_position_error",
    "evidence": "Rollout final frame shows the can released 0.11 m beyond the allowed x/y target tolerance."
  }
}
```

可用失败类型由 `config.json` 固定。缺视频、缺注释、少一个 seed、非上游 `val_only` 数据、维度不符、任一进程失败，都会让 `strict_completion.complete` 保持 `false`。

## 当前执行主机

当前主机提供一张 96 GiB NVIDIA RTX PRO 6000 Blackwell。实验保持 128 IID + 128 OOD、三视角、14 维状态/动作、视频和失败注释等全部语义门禁，仅把上游为训练吞吐设置的八卡资源参数调整为单卡 `val_only` 推理；运行清单会记录 GPU、driver、checkpoint revision 和每个 episode 的直接证据。
