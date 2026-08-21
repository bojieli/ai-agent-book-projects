# 实验 5-7：CAD 代码生成 vs 3D 生成模型（Agent 的两条造物路线）

> 《AI Agent 深入》第 5 章配套实验。同一份自然语言规格，分别走「Agent 写 CAD 代码」与「3D 生成模型」两条路线，程序化测量产物尺寸，再用一次变更请求比较两条路线的修改成本；对照组「生成一盆绿植」展示两条路线适用边界的反转。

← [返回第 5 章目录](../README.md)

## 实验目标

主线任务规格：**法兰盘，外径 80mm，厚度 10mm，4 个均布 M5 安装孔（孔径 5.5mm），孔位圆直径 60mm**。

- **路线 A（代码生成）**：Agent（Kimi `kimi-k2.5`）编写 CadQuery 代码构造零件，本地真实执行，导出 STEP 与 STL。
- **路线 B（生成模型）**：同一规格走 text-to-3D。混元 Hunyuan3D-2.1 官方 Hugging Face Space 只暴露 image-to-3D 端点，故按业界标准两段式：Gemini（`gemini-2.5-flash-image`）由规格文本生成零件产品图 → Hunyuan3D-2.1 公共 Space（`gradio_client` 调 `/shape_generation`，无需密钥）图生 3D，得到 GLB 三角网格。
- **程序化验证**：trimesh 测量两条路线产物的外径、厚度、孔数、孔径、孔位圆直径与安装面平整度，与规格逐项比对。
- **变更请求**：「安装孔从 M5 改为 M6（孔径 6.5mm）」。路线 A 程序化修补 `PARAMS.hole_diameter` 一个参数（0 次 LLM 调用）重新执行；路线 B 只能改提示词整体重新生成，复测其余尺寸是否漂移。
- **对照组**：「一盆绿植」——matplotlib 程序化渲染 vs Gemini 文生图，Kimi 视觉模型（`moonshot-v1-8k-vision-preview`）评审自然度，展示适用边界反转。

## 目录结构

```
cad-vs-diffusion/
├── flange_spec.py        # 规格与变更请求的唯一事实来源
├── measure.py            # trimesh 网格测量（外径/厚度/孔/平整度）
├── llm.py                # Kimi 聊天/视觉调用（带留证）
├── gemini_image.py       # Gemini 原生文生图（带留证）
├── route_a_codegen.py    # 路线 A：LLM 写 CadQuery → 子进程真实执行 → STEP/STL
├── route_b_gen3d.py      # 路线 B：HF 公共 Space Hunyuan3D-2.1 图生 3D
├── control_plant.py      # 对照组：程序化绿植 + Vision 评审
├── receipts.py           # 外部调用留证（参数/响应/时间戳/耗时，绝不含密钥）
├── validate_manifest.py  # manifest 模式校验
├── run_experiment.py     # 主流程
├── test_offline.py       # pytest 离线测试（不打外部 API）
├── tests/fixtures/       # CadQuery 本地生成的法兰 fixture 网格
├── output/               # 产物：源码、STEP/STL/GLB、图片
└── validation/runs/<run_id>/
    ├── manifest.json     # 正式运行清单（哈希、测量、门禁）
    └── receipts/         # 每次外部调用的留证 JSON
```

## 配置与运行

```bash
cd chapter5/cad-vs-diffusion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env   # 填入密钥（见下），并 export 到环境变量
python run_experiment.py
```

环境变量（只从环境读取，代码与 manifest 均不落密钥）：

- `KIMI_API_KEY`（必填）：路线 A 代码生成 + 对照组视觉评审。
- `GEMINI_API_KEY`（必填）：路线 B 的规格→零件图、对照组文生图。
- `DASHSCOPE_API_KEY` / `SILICONFLOW_API_KEY`（可选备选）：本次正式运行中前者返回 401（key 无效）、后者返回 402（余额不足），均未使用，留证见下文。

离线测试（不打外部 API）：

```bash
python -m pytest test_offline.py -q
```

## 正式运行结果摘要

> 正式 run：`exp5-7-cad-vs-diffusion-20260821-015734-v1`，完整数据见
> `validation/runs/exp5-7-cad-vs-diffusion-20260821-015734-v1/manifest.json`
> （SHA-256 前 16 位 `ae7c5fdf685562e5`，全文哈希见 `validation/latest.json`）。
> 10/10 门禁全部通过，9 次外部调用全部留证成功。

### 主线任务：法兰盘尺寸偏差（测量值 vs 规格，单位 mm）

| 尺寸（规格） | 路线 A：CadQuery 代码 | 路线 B：Hunyuan3D-2.1 网格 |
|---|---|---|
| 外径（80） | 80.0（偏差 0.0） | 0.519（偏差 −79.48，−99.4%） |
| 厚度（10） | 10.0（偏差 0.0） | 1.989（偏差 −8.01，−80.1%） |
| 孔数（4） | 4 ✓ | 0 ✗（无通孔） |
| 孔径（5.5） | 5.499（偏差 −0.001） | 无法测量（无孔） |
| 孔位圆直径（60） | 60.0（偏差 0.0） | 无法测量（无孔） |
| 安装面平整度 RMS | 0.0（理想平面） | 0.030（网格单位） |
| 网格 | 水密，2532 面 | 水密，144580 面 |

路线 B 的解读（如实说明）：

- Hunyuan3D 输出是**归一化到任意单位、任意朝向**的三角面片，没有毫米、坐标轴语义。M5 网格的三轴包围盒为 `[0.496, 0.519, 1.989]`——截面直径约 0.5、高约 2，是一个「细高圆柱」，与规格要求的扁平法兰（直径:厚度 = 8:1）**比例完全颠倒**；且 4 个安装孔全部丢失（中截面轮廓无内环）。
- 这不是「测量方法挑错了轴」能解释的：即使允许任意旋转与缩放，该网格也没有孔，长径比也错了约 32 倍。点云渲染见 `output/render_route_b_m5.png`（对比 `output/render_route_a_m5.png`）。
- 输入产品图（Gemini 生成，`output/route_b/flange_m5_input.png`）本身有 4 孔，孔是在 2D→3D 重建阶段丢掉的——图生 3D 模型对「贯穿孔洞」这类拓扑特征基本不可见（背面不可见、重建倾向于封闭凸包）。

路线 A 一次成功：Kimi 生成的 17 行 CadQuery 代码（`output/route_a/flange_m5.py`）全部尺寸在 0.05mm 公差内，唯一的 −0.001mm 孔径偏差来自 STL 三角离散的弦差，STEP 文件则是精确 B-rep。

### 变更请求：M5 → M6（孔径 5.5 → 6.5）

| | 路线 A | 路线 B |
|---|---|---|
| 修改方式 | 程序化修补 `PARAMS.hole_diameter` 一行 | 改提示词，文生图 + 图生 3D 整体重跑 |
| LLM/模型调用 | **0 次**（本地执行 2.1s） | **2 次外部生成**（6.9s + 24.6s） |
| 变更后孔径 | 6.499（偏差 −0.001mm） | 仍无孔，无法测量 |
| 其余尺寸漂移 | 外径 0.0、厚度 0.0、孔位 0.0、孔数不变 | 外径 0.519→1.988（**漂移 +283%**，且法兰轴向从 Z 翻转到 Y）、厚度 −0.0015 |

路线 B 的 M6 重生成（`output/render_route_b_m6.png`）不仅没长出孔，连零件的摆放朝向都变了——生成模型没有「其余部分保持不变」的概念。

### 对照组：一盆绿植（适用边界反转）

任务：`一盆绿植（带花盆的室内观叶植物），写实风格`。

| | 程序化渲染（matplotlib） | 文生图（Gemini） |
|---|---|---|
| 产物 | `output/control/plant_procedural.png` | `output/control/plant_generative.png` |
| 视觉评审自然度（1-10） | **3**（过于简化，缺乏细节和真实感） | **8**（细节丰富，光影效果逼真） |

评审模型（Kimi `moonshot-v1-8k-vision-preview`）结论：文生图「更接近真实世界的一盆绿植」。原文见 manifest `control_group.vision_review`。

**结论**：精确工程对象（法兰盘）——代码生成碾压生成模型（尺寸精确、可参数化修改）；开放性自然内容（绿植）——生成模型碾压代码渲染。两条路线的适用边界正好反转。

## 诚实声明

- 路线 B 的网格由真实外部服务（Hugging Face 公共 Space）生成，原始 GLB 原样保存、原样测量；其尺寸、拓扑（有无孔）、表面质量与规格的差距是实验结论的一部分，未做任何修饰。
- 若公共 Space 排队/限流导致路线 B 失败，manifest 中会标 `status: incomplete` 并附原因，不会用 mock 网格冒充。
- `DASHSCOPE_API_KEY`（401 invalid_api_key）与 `SILICONFLOW_API_KEY`（402 余额不足）在本次运行中不可用，相关探测记录如实保留；视觉评审与文生图改走 Kimi / Gemini。
