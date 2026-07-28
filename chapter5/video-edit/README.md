# Experiment 5-6: API-Driven Smart Video Editing / 实验 5-6：基于 API 的智能视频剪辑

> Companion lab for *AI Agents in Depth*, Chapter 5 — NL request + multi-scene video → two-step Vision locate → Blender bpy script / ffmpeg cut → Proposer–Reviewer.  
> 《深入理解 AI Agent》配套：自然语言需求 + 多场景视频 → 两步 Vision 定位 → 生成 Blender bpy / ffmpeg 剪辑 → 提议者-审核者。

← [Chapter 5 index / 返回第 5 章目录](../README.md)

---

## English

### Purpose

Given a multi-scene video and one NL request (e.g. “cut out the surfing part”), the Agent locates the target scene, **generates a Blender Python API script**, cuts the clip, and self-reviews.

Three mechanisms in multimedia processing:

1. **Two-step Vision locate**: Proposer cannot “watch” video directly; a **video-analysis sub-agent** uses ffmpeg frame extraction + Vision LLM to find time bounds.
2. **Code generation (Blender Python API)**: Proposer turns the edit plan into a **bpy** script—import / trim / subtitle / speed / render as API calls, run with `blender --background --python edit.py`. Without Blender, scripts still generate; render falls back to ffmpeg (see “edit backends”).
3. **Proposer / Reviewer**: after cut, Reviewer samples key frames with Vision; fail → feedback → iterate.

### Two-step locate

Scanning every frame is slow/expensive → coarse then fine:

- **Coarse**: one frame every **10s**; Vision gets a rough interval (e.g. surfing 20–30s).
- **Fine**: expand the coarse window by one coarse step; one frame every **1s**; Vision returns precise bounds (e.g. 15–29s).

Encapsulated as a **sub-agent**: tens of screenshots live only in the sub-agent’s one-shot context and do not pollute Proposer/Reviewer history. Demo prints token comparison at the end.

### Proposer–Reviewer flow

```
NL request ──► Proposer parses intent (scene + effects)
              │
              ▼
         Video-analysis sub-agent two-step locate ──► [start, end]
              │
              ▼
         Proposer emits Blender bpy script (edit.py) ──► render cut (+ subtitle/slow-mo)
              │                                        Blender if installed else ffmpeg
              ▼
         Reviewer samples start/mid/end frames ──► Vision pass/fail + feedback
              │pass?  no → Proposer adjusts bounds, re-cut (max 3 rounds)
              ▼yes
           final.mp4
```

### Run

```bash
pip install -r requirements.txt
cp env.example .env        # OPENAI_API_KEY (or OPENROUTER_API_KEY fallback)
python demo.py             # default: "把冲浪的部分剪出来" (full pipeline)
python demo.py "把滑雪部分剪出来，并加上字幕 Winter"   # custom request
python demo.py -i my.mp4 -o out.mp4 "把演讲开场剪出来"  # own video + output
python demo.py --backend blender   # force Blender headless (Blender required)
python demo.py --vision-model gpt-5.6-luna  # also --text-model
python demo.py --quick     # coarse sampling + single review round (cheapest Vision)
python demo.py --smoke     # smoke: edit path + bpy script only; no API
python demo.py --help
```

Common flags (see `--help`): `--input/-i`, `--output/-o`, `--backend {auto,blender,ffmpeg}`, `--text-model` / `--vision-model`.

One command runs: generate/read video → two-step locate → bpy cut → review → final. Each run clears `output/` (idempotent). Full path calls Vision many times; use `--smoke` (zero API) or `--quick` first.

### Sample outputs

#### `--smoke` (zero API, reproducible)

Real output of `python demo.py --smoke` (no OpenAI key; needs ffmpeg):

```text
==========================================================================
  冒烟自检 | 剪辑链路 + bpy 脚本生成，不调用任何 API
==========================================================================
[1/3] 生成测试视频 OK：output/source.mp4（场景真值={'hiking': (0, 15), 'surfing': (15, 30), 'skiing': (30, 42), 'cycling': (42, 54)}）
[2/3] 抽帧 OK：output/frames/smoke.png
[3/3] 剪辑+字幕 OK（后端=ffmpeg（未装 Blender，回退））：
  文件: smoke_cut.mp4
  时长: 5.03s
  容器: mov,mp4,m4a,3gp,3g2,mj2
  大小: 121.4 KB
  视频流: h264 1280x720 @ 30/1 fps
  音频流: aac 44100Hz 1ch

已生成 Proposer 的 Blender 脚本：output/edit.py
（这正是书中'生成 Blender Python API 代码'的产物；装好 Blender 后可直接
 `blender --background --python output/edit.py` 无头渲染。）

✓ 冒烟自检通过：剪辑链路正常 + bpy 脚本已生成（未调用 OpenAI）。
```

`output/edit.py` is an executable Blender bpy script (`new_movie`, `frame_offset_start` / `frame_final_duration`, `new_effect(type='TEXT')`, `bpy.ops.render.render`); syntax-checked with `py_compile`.

#### `--quick` (full path, needs API)

Excerpt from `python demo.py --quick` (default surfing request); locate/error/token parts independent of bpy/ffmpeg:

```text
步骤 1 | Proposer 解析自然语言需求
解析结果：目标场景='surfing scene'  特效=[]

步骤 2 | 视频分析子 Agent：两步 Vision 定位（--quick 快速采样）
  [粗粒度] 每 15s 采样 5 帧 → Vision 得区间 [15, 30]s（依据：The word 'SURFING' appears at t=15s and changes at t=30s.）
  [细粒度] 窗口 [0.0, 45.0] 内每 2s 采样 23 帧 → 精确边界 [16.0, 28.0]s
  >>> 最终定位：起 16.0s  止 28.0s
  真值 [15, 30]s → 起点误差 1.0s，终点误差 2.0s（验收要求 ≤ 3s）

步骤 3-4 | Proposer 剪辑 + Reviewer 审查（迭代）
  Proposer 剪出片段 [16.0, 28.0]s，成片时长 12.0s
  Reviewer：pass=... score=... 检查帧=['0.5', '6.0', '11.5']

Token 统计（子 Agent 隔离截图，主上下文不被污染）
  主 Agent（Proposer+Reviewer）：573 tokens
  子 Agent（两步定位截图）    ：2934 tokens
```

Artifacts under `output/`:

| File | Duration | Note |
| --- | --- | --- |
| `source.mp4` | 54.0s | Procedural 4-scene test source |
| `edit_round1.py` | — | Proposer bpy script (portable) |
| `cut_round1.mp4` | 12.0s | Round-1 candidate |
| `final.mp4` | 12.0s | Chosen final (H.264 + AAC, 1280x720@30fps) |

Token stats: tens of screenshots (2934 tok) only in **sub-agent**; main history (~573 tok) almost unpolluted. (Synthetic test shows “SURFING” text, not real surfing—Reviewer may fail on content; real video avoids that.)

### Dependencies

- **ffmpeg / ffprobe** for cuts and frames. `brew install ffmpeg` (macOS) / `apt install ffmpeg` (Ubuntu). Validated on ffmpeg 8.0.
- **OPENAI_API_KEY**: `gpt-5.6-luna` for vision locate/review and text planning (vision model must accept images); or `OPENROUTER_API_KEY` fallback via OpenRouter.

### Adapt / extend

#### Model / provider

All via env (`env.example`); no code change:

- `TEXT_MODEL` (default `gpt-5.6-luna`).
- `VISION_MODEL` must support images (default `gpt-5.6-luna`).
- `OPENAI_BASE_URL` + matching `OPENAI_API_KEY` for compatible endpoints.

```bash
export OPENAI_BASE_URL=https://your-gateway.example.com/v1
export VISION_MODEL=gpt-5.6-luna
export TEXT_MODEL=gpt-5.6-luna
```

`agents.py` `OpenAI()` client reads these lazily via `client()`.

#### Own input video

`make_test_video.py` builds a 54s video with 4 distinct scenes (HIKING green / SURFING blue / SKIING white / CYCLING orange) plus large scene-name and timecode watermarks for Vision reproducibility.

Own video: `python demo.py -i your.mp4 -o out.mp4 "edit request"` (skips test generation; no ground-truth error print).

#### Blender vs ffmpeg (edit backends)

Book uses **Blender Python API (bpy)** on the VSE. First-class here: `blender_editor.generate_bpy_script()` emits real bpy (`new_movie`, frame offsets, `TEXT`/`SPEED` effects, render); `render_with_blender()` runs `blender --background --python edit.py`.

- `--backend blender`: force Blender (`blender --version` required);
- `--backend ffmpeg`: force ffmpeg;
- `--backend auto` (default): bpy if Blender installed, else ffmpeg.

**Always**: Proposer’s bpy script is written to `output/edit_round*.py` (`output/edit.py` under `--smoke`)—core “generate Blender Python API code” artifact. This environment may not have Blender, so render is validated with ffmpeg; bpy is `py_compile`-checked but **not rendered in real Blender** unless you install it and use `--backend blender`.

| | ffmpeg | Blender (bpy) |
| --- | --- | --- |
| Fit | 2D cut/join/subtitle/speed pipelines | 3D scenes, compositing, keyframe anim, particles/camera |
| Ops | single binary, no GUI, CI-friendly | full Blender install; larger/slower |
| When | most “cut a clip + simple effects” | only when 3D/compositing/complex transitions needed |

Two-step Vision + Proposer–Reviewer is decoupled from the execution layer; same edit plan for both backends.

### Files

| File | Role |
| --- | --- |
| `demo.py` | CLI orchestration, self-check, iteration, token stats |
| `agents.py` | `VideoAnalyzerAgent` / `ProposerAgent` / `ReviewerAgent` |
| `blender_editor.py` | **bpy script gen + headless render** (book path) |
| `video_editor.py` | `apply_edit()`; Blender/ffmpeg backends |
| `make_test_video.py` | Procedural 4-scene test video |
| `ffmpeg_utils.py` | Thin ffmpeg/ffprobe wrappers |

`output/` is gitignored.

### Limitations

- Locate accuracy depends on visual distinctness; gradual scene transitions increase boundary error vs solid-color test film.
- Fine step fixed at 1s → boundary precision about ±1s (book acceptance ±3s).
- Slow-mo audio uses `atempo`; extreme ratios hurt quality; complex transitions/multi-track not covered.
- Reviewer samples only start/mid/end; mid-clip glitches can be missed (raise sample density if needed).

---

## 中文

### 目的

用户给一段含多个场景的视频 + 一句自然语言需求（如"把冲浪部分剪出来"），Agent 自动定位目标场景、**生成 Blender Python API 脚本**剪出片段并自我审查。

验证三个核心机制在多媒体处理中的作用：

1. **两步 Vision 定位**：Proposer 无法直接"看懂"视频，于是委托一个**视频分析子 Agent**，
   用 ffmpeg 抽帧 + Vision LLM 读图来定位目标场景的时间边界。
2. **代码生成（Blender Python API）**：Proposer 把剪辑计划翻译成一段调用 **Blender
   Python API（bpy）** 的脚本——导入 / 裁剪 / 字幕 / 变速 / 渲染各对应一个 API 调用，
   用 `blender --background --python edit.py` 无头执行。这正是书中"把视频编辑重构为
   API 调用和代码生成问题"的落地。未装 Blender 时脚本照常生成（代码生成产物），
   实际渲染回退到 ffmpeg（见下文"剪辑后端"）。
3. **提议者-审核者（Proposer / Reviewer）**：Proposer 剪辑后无法自证效果，
   由 Reviewer 抽取成片关键帧、用 Vision LLM 检查是否剪对，不合格则反馈、迭代。

### 两步定位原理

Vision LLM 逐帧扫全片既慢又贵，因此采用"先粗后细"：

- **第一步（粗粒度）**：每 **10 秒**抽一帧，把全片的稀疏截图连同"要找哪个场景"一起
  交给 Vision，得到大致区间（如"冲浪在 20–30s"）。
- **第二步（细粒度）**：在粗区间上下各外扩一个粗间隔，每 **1 秒**抽一帧，
  再问 Vision 精确边界（如"15–29s"）。

把这套抽帧-读图封装成**独立子 Agent**：几十张截图只进入子 Agent 的一次性上下文，
不会污染主 Agent（Proposer/Reviewer）的对话历史。demo 末尾会打印两者的 token 对比。

### 提议者-审核者

```
NL 需求 ──► Proposer 解析意图（目标场景 + 特效）
              │
              ▼
         视频分析子 Agent 两步定位 ──► [start, end]
              │
              ▼
         Proposer 生成 Blender bpy 脚本（edit.py）──► 渲染剪辑（可加字幕/慢动作）
              │                                        装了 Blender 用 bpy，否则回退 ffmpeg
              ▼
         Reviewer 抽首/中/尾关键帧 ──► Vision 检查 pass/fail + 反馈
              │pass?  否 → Proposer 据反馈修正边界，重剪（最多 3 轮）
              ▼是
           输出成片 final.mp4
```

### 运行

```bash
pip install -r requirements.txt
cp env.example .env        # 填入 OPENAI_API_KEY（未配置时设 OPENROUTER_API_KEY 自动改走 OpenRouter）
python demo.py             # 默认需求"把冲浪的部分剪出来"（完整流程）
python demo.py "把滑雪部分剪出来，并加上字幕 Winter"   # 自定义需求
python demo.py -i my.mp4 -o out.mp4 "把演讲开场剪出来"  # 用自己的视频 + 自定义输出
python demo.py --backend blender   # 强制用 Blender Python API 无头渲染（需装 Blender）
python demo.py --vision-model gpt-5.6-luna  # 覆盖模型（也可用 --text-model）
python demo.py --quick     # 快速模式：粗采样 + 单轮审查，Vision 调用最少（省时省钱）
python demo.py --smoke     # 冒烟自检：仅剪辑链路 + 生成 bpy 脚本，不调用任何 API
python demo.py --help      # 查看全部参数
```

常用参数（完整见 `--help`）：`--input/-i` 输入视频、`--output/-o` 成片路径、
`--backend {auto,blender,ffmpeg}` 剪辑后端、`--text-model`/`--vision-model` 覆盖模型。

一条命令即可跑通：生成/读取视频 → 两步定位 → 生成 bpy 脚本剪辑 → 审查 → 输出成片。
每次运行都会清空 `output/`，从干净状态开始（幂等可重复）。完整流程会多次调用
Vision 模型（较慢/耗费额度）；只想验证链路时先跑 `--smoke`（零 API），或用 `--quick`。

### 预期输出示例

#### `--smoke`（零 API，可复现）

以下为 `python demo.py --smoke` 的**真实输出**（无需 OpenAI Key，仅需 ffmpeg）：

```text
==========================================================================
  冒烟自检 | 剪辑链路 + bpy 脚本生成，不调用任何 API
==========================================================================
[1/3] 生成测试视频 OK：output/source.mp4（场景真值={'hiking': (0, 15), 'surfing': (15, 30), 'skiing': (30, 42), 'cycling': (42, 54)}）
[2/3] 抽帧 OK：output/frames/smoke.png
[3/3] 剪辑+字幕 OK（后端=ffmpeg（未装 Blender，回退））：
  文件: smoke_cut.mp4
  时长: 5.03s
  容器: mov,mp4,m4a,3gp,3g2,mj2
  大小: 121.4 KB
  视频流: h264 1280x720 @ 30/1 fps
  音频流: aac 44100Hz 1ch

已生成 Proposer 的 Blender 脚本：output/edit.py
（这正是书中'生成 Blender Python API 代码'的产物；装好 Blender 后可直接
 `blender --background --python output/edit.py` 无头渲染。）

✓ 冒烟自检通过：剪辑链路正常 + bpy 脚本已生成（未调用 OpenAI）。
```

生成的 `output/edit.py` 是一段**可执行的 Blender bpy 脚本**（`new_movie` 导入、
`frame_offset_start`/`frame_final_duration` 裁剪、`new_effect(type='TEXT')` 字幕、
`bpy.ops.render.render` 渲染），本机对其做过 `py_compile` 语法校验。

#### `--quick`（完整链路，需 API）

以下为 `python demo.py --quick`（默认需求"把冲浪的部分剪出来"）的真实节选（定位/误差/
token 部分与剪辑后端无关，故不受 bpy/ffmpeg 后端切换影响）：

```text
步骤 1 | Proposer 解析自然语言需求
解析结果：目标场景='surfing scene'  特效=[]

步骤 2 | 视频分析子 Agent：两步 Vision 定位（--quick 快速采样）
  [粗粒度] 每 15s 采样 5 帧 → Vision 得区间 [15, 30]s（依据：The word 'SURFING' appears at t=15s and changes at t=30s.）
  [细粒度] 窗口 [0.0, 45.0] 内每 2s 采样 23 帧 → 精确边界 [16.0, 28.0]s
  >>> 最终定位：起 16.0s  止 28.0s
  真值 [15, 30]s → 起点误差 1.0s，终点误差 2.0s（验收要求 ≤ 3s）

步骤 3-4 | Proposer 剪辑 + Reviewer 审查（迭代）
  Proposer 剪出片段 [16.0, 28.0]s，成片时长 12.0s
  Reviewer：pass=... score=... 检查帧=['0.5', '6.0', '11.5']

Token 统计（子 Agent 隔离截图，主上下文不被污染）
  主 Agent（Proposer+Reviewer）：573 tokens
  子 Agent（两步定位截图）    ：2934 tokens
```

产物（`output/` 目录，真实文件）：

| 文件 | 时长 | 说明 |
| --- | --- | --- |
| `source.mp4` | 54.0s | 程序化生成的 4 场景测试原片 |
| `edit_round1.py` | — | Proposer 生成的 Blender bpy 脚本（代码生成产物，可换机执行） |
| `cut_round1.mp4` | 12.0s | 第 1 轮剪出的候选片段 |
| `final.mp4` | 12.0s | 采用的成片（H.264 + AAC，1280x720@30fps） |

Token 统计印证了核心结论：几十张截图（2934 tokens）只进入**子 Agent**的一次性
上下文，主 Agent 的对话历史（573 tokens）几乎不受截图污染。
（注：合成测试片仅显示"SURFING"字样而非真实冲浪画面，Reviewer 有时会据此判为
不通过——这正是审核者按画面内容如实反馈的体现；换真实视频即无此现象。）

### 依赖

- **ffmpeg / ffprobe**：本机实际剪辑与抽帧。`brew install ffmpeg`（macOS）/
  `apt install ffmpeg`（Ubuntu）。本项目在 ffmpeg 8.0 上验证通过。
- **OPENAI_API_KEY**：用 `gpt-5.6-luna` 做视觉定位/审查与文本规划（视觉模型须支持图像输入）；未配置时用 `OPENROUTER_API_KEY` 兜底，自动改走 OpenRouter。

### 如何适配 / 扩展

#### 换模型 / 供应商

模型与端点全部通过**环境变量**注入（见 `env.example`），无需改代码：

- `TEXT_MODEL`：规划/边界修正的文本模型（默认 `gpt-5.6-luna`）。
- `VISION_MODEL`：定位/审查的视觉模型，**必须支持图像输入**（默认 `gpt-5.6-luna`）。
- `OPENAI_BASE_URL`：换成任何兼容 OpenAI 协议的端点（自建代理、Azure OpenAI、
  或其他厂商网关），配合对应的 `OPENAI_API_KEY` 即可。

```bash
export OPENAI_BASE_URL=https://your-gateway.example.com/v1
export VISION_MODEL=gpt-5.6-luna       # 例：用当前廉价旗舰视觉模型
export TEXT_MODEL=gpt-5.6-luna
```

`agents.py` 里的 `OpenAI()` 客户端会自动读取上述变量（`client()` 惰性初始化）。

#### 换输入视频

`make_test_video.py` 用 ffmpeg **程序化生成**一段 54s 的视频，含 4 个明显不同的场景
（HIKING 绿 / SURFING 蓝 / SKIING 白 / CYCLING 橙），每段都叠加大号场景名与时间码水印，
让 Vision 仅凭画面就能准确定位——便于复现验收。

换成**你自己的真实视频**：直接 `python demo.py -i 你的.mp4 -o 输出.mp4 "剪辑需求"`
即可（无需改代码）。此时跳过测试片生成，也不再打印定位误差（外部视频无真值）。

#### Blender vs. ffmpeg（剪辑后端）

书中原方案用 **Blender Python API（bpy）** 驱动视频序列编辑器（VSE）完成剪辑。
本项目把它实现为**一等后端**：`blender_editor.generate_bpy_script()` 把剪辑计划翻译成
一段真实可执行的 bpy 脚本（`new_movie` 导入、`frame_offset_start`/`frame_final_duration`
裁剪、`new_effect(type='TEXT'/'SPEED')` 字幕/变速、`bpy.ops.render.render` 渲染），
`render_with_blender()` 再用 `blender --background --python edit.py` 无头执行。

- `--backend blender`：强制走 Blender（需 `blender --version` 可用）；
- `--backend ffmpeg`：强制走 ffmpeg；
- `--backend auto`（默认）：装了 Blender 用 bpy，否则回退 ffmpeg。

**关键点：无论哪个后端，Proposer 生成的 bpy 脚本都会落盘到 `output/edit_round*.py`**
（`--smoke` 下为 `output/edit.py`）——即"生成 Blender Python API 代码"这一核心产物，
可人工核对、也可拷到装了 Blender 的机器上执行。本机未安装 Blender，故本仓库的实际
渲染由 ffmpeg 完成并验证；bpy 脚本已通过 `py_compile` 语法校验，但**未在真实 Blender
上跑过渲染**（装好 Blender 后即可用 `--backend blender` 端到端执行）。两种后端的取舍：

| | ffmpeg | Blender（bpy） |
| --- | --- | --- |
| 定位 | 裁剪/拼接/字幕/变速等 2D 流水线 | 3D 场景、合成、关键帧动画、粒子/摄像机 |
| 上手 | 单二进制、无 GUI、CI 友好 | 需装完整 Blender，体积大、渲染慢 |
| 适用 | 绝大多数"剪一段 + 简单特效"需求 | 需要 3D 合成/复杂转场/图层混合时才值得 |

核心的"两步 Vision 定位 + 提议者-审核者"与执行层解耦，两个后端共用同一份剪辑计划，
`agents.py`/`demo.py` 无需为切换后端改动逻辑。

### 文件

| 文件 | 作用 |
| --- | --- |
| `demo.py` | 一条命令跑通的编排入口（CLI、启动自检、迭代循环、token 统计） |
| `agents.py` | `VideoAnalyzerAgent`（两步定位）/ `ProposerAgent` / `ReviewerAgent` |
| `blender_editor.py` | **Blender bpy 脚本生成 + 无头渲染**（书中原方案，核心实验点） |
| `video_editor.py` | 剪辑执行层：`apply_edit()` 统一入口，调度 Blender/ffmpeg 双后端 |
| `make_test_video.py` | 程序化生成含 4 个场景的测试视频 |
| `ffmpeg_utils.py` | ffmpeg/ffprobe 薄封装（统一错误检查、抽帧、探测时长/流） |

`output/`（生成的视频、截图、成片）已被 `.gitignore` 忽略，避免仓库膨胀。

### 局限

- 定位精度取决于场景在画面上的可辨识度；真实视频若场景过渡渐变，边界误差会大于纯色测试片。
- 细粒度步长固定 1s，边界精度上限即 ±1s 量级（满足书中 ±3s 验收）。
- 慢动作音频用 `atempo` 变速，倍率过大时音质下降；转场/多轨混音等复杂特效未覆盖。
- Reviewer 仅抽首/中/尾三帧，长片段中段的偶发错误可能漏检（可调高抽帧密度）。

---

## Notes / 说明

- Prefer `--smoke` then `--quick` before a full Vision run. / 完整 Vision 前先 `--smoke`，再 `--quick`。
- Commands/code/paths/env vars are identical in both language sections. / 命令、代码、路径与环境变量在中英文两侧保持一致。
