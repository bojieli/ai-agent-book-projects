# 实验 1-4：文生图工作流与原生图像生成的对照

对应书稿 `book/chapter1.md` 的「实验 1-4 ★」。

## 实验目标

让同一句口语化中文需求走两条路线，对照观察：

1. **工作流路线中「改写」节点产出的提示词与原始需求的差异**——LLM 在这一节点做的不是智能决策，而是「翻译」：把自然语言适配成文生图模型能消化的输入格式；
2. **两条路线最终图片对原始需求的满足程度**。

需求按口语化程度分两类对照：

- **具体需求**：用户已指定场景、风格或文案细节，考察的是执行的**忠实度**——改写节点会不会弄丢或篡改用户给定的信息；
- **宽泛需求**：用户只给主题不给细节，考察的是改写节点做**场景具象化**带来的信息增益——它替用户想象出的画面，是原生路线直接出图所没有的叙事性，还是多此一举的过度发挥。

测试需求（5 句口语化中文描述，`main.py` 中 `REQUIREMENTS`）：

| 类别 | ID | 需求 |
| --- | --- | --- |
| 具体 | `programmer-overtime` | 帮我画一个周末加班的程序员，风格丧一点 |
| 具体 | `windowsill-plant` | 帮我画一盆放在窗台上的绿植，早晨的阳光刚好照进来 |
| 具体 | `headphone-poster` | 帮我做一张新款降噪耳机的产品海报，主打"深夜独处也清净"这句文案，风格简约高级 |
| 宽泛（主用例） | `agi-programmer` | 帮我画一个 AGI 实现以后程序员的工作场景 |
| 宽泛 | `future-city-morning` | 帮我画一幅"未来城市的早晨"的画 |

## 三条路线的架构

```
工作流路线（workflow）：
  用户需求 ──> [节点 1: 提示词改写, Kimi kimi-k3]
                 输出 SD 风格 JSON：{prompt（逗号分隔英文 tag + 质量词）,
                                      negative_prompt, style_notes}
             ──> [节点 2: 文生图, 通义万相 wan2.2-t2i-flash]
                 输入改写后的 prompt / negative_prompt，输出图片

原生路线 A（native）：
  用户需求 ──> [Gemini gemini-3-pro-image（书稿所称 Nano Banana 2）]
                 一次调用直接输出图片（response_modalities=["IMAGE"]）

原生路线 B（native_gptimage）：
  用户需求 ──> [OpenAI gpt-image-2（GPT-Image 2）]
                 images/generations 接口，一次调用直接出图
```

工作流路线的执行路径是代码写死的（先改写、后生成，见 `pipeline.py` 的
`run_workflow_route`）；两条原生路线都没有改写节点，模型自己理解口语化需求并直接出图。

## 模型选型实录（如实记录）

- **原生路线 A（native）**：**`gemini-3-pro-image`**（书稿所称 Nano Banana 2）——
  ListModels 实测可用，5 句需求全部一次成功（20260821T040450Z 轮）；早期轮次
  `agi-programmer` 偶发内容过滤（候选响应 content 为 None），重跑后恢复，非不可用。
- **原生路线 B（native_gptimage）**：OpenAI **`gpt-image-2`**（GPT-Image 2，
  images/generations 接口）——全部 5 句需求均一次成功。该账户此前 GPT-5.x 因
  `credit_balance_exhausted` 失败过，但图像接口可用。
- **工作流路线生图工具**：实验设计首选 SiliconFlow 托管的 FLUX.1 / Stable Diffusion
  系列，实测 `black-forest-labs/FLUX.1-schnell` 与
  `stabilityai/stable-diffusion-3-5-large` 返回 `Model disabled`；账户余额为 0，
  `Kwai-Kolors/Kolors`、`Tongyi-MAI/Z-Image-Turbo`、`Qwen/Qwen-Image` 均报
  `balance insufficient`；OpenRouter 仅提供视觉理解模型，不支持文本转图像生成。
  改用 **DashScope 国际站通义万相 `wan2.2-t2i-flash`**（经典扩散式文生图模型，接受
  SD 风格提示词与负面提示词，异步任务接口）。注意：该模型服务端会再做一次内部提示词
  扩写（响应中的 `actual_prompt` 字段），已一并留证。
- **改写节点 LLM**：Moonshot **`kimi-k3`**（OpenAI 兼容接口）。
  kimi-k3 只允许 temperature=1（默认值），显式传其他值被 400 拒绝。

## 配置与运行

```bash
# 在仓库根目录
cp chapter1/image-gen-workflow/env.example .env   # 填入各 API Key（或 export 环境变量）

cd chapter1/image-gen-workflow
pip install -r requirements.txt   # google-genai openai requests python-dotenv

# 标准运行：全部 5 句需求 × 4 条路线（workflow/native/native_gemini_pro/native_gptimage）
python main.py

# 只跑某条路线 / 某句需求
python main.py --route workflow
python main.py --route native_gemini_pro
python main.py --requirement windowsill-plant

# 离线测试（不发真实请求）
python -m pytest
```

所需环境变量见 `env.example`：`KIMI_API_KEY`、`DASHSCOPE_API_KEY`、`GEMINI_API_KEY`、
`OPENAI_API_KEY`（`SILICONFLOW_API_KEY` 为首选方案保留，本次未实际使用）。

## 目录与证据

```
image-gen-workflow/
├── config.py        # 环境变量与模型配置
├── pipeline.py      # 改写节点 + 两条路线的编排，每次调用产生 call record
├── evidence.py      # evidence manifest 构建与离线校验
├── main.py          # 正式运行入口
├── tests/           # 离线测试（改写输出结构、manifest 模式、env 一致性）
├── outputs/<run_id>/
│   ├── images/      # 生成的图片
│   └── calls/       # 每次 API 调用的请求/响应 JSON（模型、参数、响应 ID、用量、时间戳）
└── validation/
    ├── latest.json
    └── real_<run_id>/
        ├── evidence.json      # manifest：输入、改写结果、图片相对路径与 SHA-256、模型、用量
        └── evidence.sha256
```

## 正式运行结果摘要

**最终正式运行（run_id=`20260821T040450Z`）**：5 句需求 × 3 条路线共 15 次运行，**15/15 全部成功**，
证据见 `validation/real_20260821T040450Z/evidence.json`（sha256: `7e529a8085d7d90856a2311a8981f5fc0b59531065121ff7eed5b74a1b076783`）。

历史运行（过程留证，均保留）：

- **run_id=`20260821T014302Z`（失败记录）**：kimi-k3 显式传了 temperature=0.3
  被 400 拒绝，改写节点 3 次全部失败；修正后重跑，该次留证保留。
- **run_id=`20260821T014534Z`**：3 句具体需求 × 2 条路线（workflow + native=gemini-3.1-flash-image-preview）
  共 6 次成功。
- **run_id=`20260821T020405Z`**：2 句宽泛需求 × 同上 2 条路线 + gpt-image-2 对照，共 5 次成功。

### 具体需求对照：改写节点对原始需求做了什么

以主用例「帮我画一个周末加班的程序员，风格丧一点」为例，kimi-k3 改写产出：

- **prompt**（节选）：`masterpiece, best quality, ..., exhausted programmer, messy black hair, dark circles under eyes, dead tired eyes, ..., empty dark office at night, weekend overtime, cold blue screen glow, ..., melancholic atmosphere, lonely, gloomy`
- **negative_prompt**（节选）：`lowres, bad anatomy, ..., smiling, cheerful, bright daylight, crowded`
- **style_notes**：把抽象的"丧"具象化为冷蓝屏幕光、黑眼圈死鱼眼、凌乱工位和深夜空无一人的办公室；负面词中排除微笑、明亮色彩等破坏情绪的元素。

可以看到改写做了三件事：**翻译**（中文→英文 tag）、**具象化**（"丧"→ 黑眼圈 /
冷蓝光 / 深夜空办公室，"周末加班"→ weekend overtime + empty office）、**风格决策**
（自作主张选了 anime style——用户并没有指定画风）。负面提示词甚至把 smiling、
cheerful 列为排除项来保住"丧"的情绪，这是原始需求里没有的信息增益。

值得注意：万相服务端对 prompt 又做了一次内部扩写（响应里的 `actual_prompt`
字段，已留证）——托管文生图服务自己也开始内置"改写"这一适配层了。

### 具体需求对照：三条路线的图片对原始需求的满足程度

| 需求 | 工作流路线（改写 + 万相） | 原生路线 A（Nano Banana 2） | 原生路线 B（GPT-Image 2） | 对照结论 |
| --- | --- | --- | --- | --- |
| 周末加班的程序员，丧 | 动漫风插画：深夜空办公室、雨窗、泡面咖啡、神情疲惫，"丧"到位；但动漫画风是改写节点自作主张 | 写实摄影：撑头盯屏、泡面红牛、工位名牌"李明"、CRUSHING BUGS 马克杯，疲惫感更直接 | 写实插画：午夜程序员伏案、深色办公室、蓝屏光，"丧"感准确 | 三者都打中需求；两条原生路线风格更写实，工作流路线多了未授权的动漫决策 |
| 窗台绿植 + 晨光 | 龟背竹陶盆、木质窗台、逆光透叶，晨光氛围准确 | 翠绿多肉摆窗台、晨光洒进来、窗外花园，氛围明亮自然 | 现代室内陈设、宽大落地窗、植物沐浴阳光，晨光强调更足 | 三者均满足需求，细节各有不同 |
| 降噪耳机海报（含指定文案） | 耳机产品图质感高级、深夜蓝氛围对，**但整张图没有任何文案** | 完整海报：指定文案"深夜独处也清净"一字不差渲染为大标题，产品与文案融合自然 | 完整海报：文案准确，产品照+文字排版整齐，黑色背景高级感强 | **两条原生路线均明显更好**——工作流路线在改写时把文案列进 negative_prompt 弄丢了 |

海报用例是最能说明问题的对照：改写节点在 negative_prompt 里排除了 `text, logo`
（其 style_notes 坦言"AI 生成文字易乱码，建议海报文案后期手动添加"）——这是
适配层围绕旧模型能力短板做的合理取舍，但代价是原始需求里"主打这句文案"这个核心
诉求在改写环节就被丢弃了；而原生模型自己能渲染中文文字，一次调用就把文案、产品、
氛围同时做对（仅底部小图误画成入耳式耳机，与主图头戴式不一致，算小瑕疵）。

### 宽泛需求对照：改写节点的场景具象化有没有带来信息增益

主用例「帮我画一个 AGI 实现以后程序员的工作场景」，kimi-k3 的改写把它具象化为
一个**有明确观点的场景**（style_notes 原文：用「程序员悠闲喝咖啡、人形机器人写代码、
全息代码漂浮」的对比画面来具象化 AGI 之后的场景）——与书稿正文预期的
"AGI 之后程序员不需要写代码"的想象同向。三条路线对比：

| 路线 | 画面 | 对"AGI 之后"的表达 |
| --- | --- | --- |
| 工作流（改写 + 万相） | 等距插画风：程序员光着脚翘在键盘上、小机器人侍立一旁、四周全息代码屏漂浮 | **明确**：代码由 AI 写，人闲着监督——改写节点注入的叙事被完整执行 |
| 原生 Nano Banana 2（gemini-3-pro-image） | 写实风科技感场景：程序员与 AI 协作，未来感十足，有明显的技术跨越叙事 | **清晰**：有"人 + AI"协作的叙事感，比早期 Flash 模型更有观点 |
| 原生 GPT-Image 2（gpt-image-2） | 带大段中文标注的概念图解：标题"AGI 驱动的时代，程序员的工作重点从「编写代码」转向「创造价值」"，AGI 协作助手气泡写着"我已经完成了大部分开发工作，请您 Review 一下" | **最强**：几乎是在用图文回答这个问题，叙事性和信息密度都最高 |

第二句「未来城市的早晨」：两条路线都给出了合格的科幻城市全景，改写节点补充的
飞行载具、空中连廊、全息广告牌属于"意料之中"的通用科幻元素；工作流路线成图偏
蓝调暮光（"早晨"感偏弱），Gemini 的日出全景（可见朝阳、通勤人群、绿色植被）的
清晨氛围更准。这一句上两者相当，Gemini 略好。

**宽泛需求的结论（如实）**：改写节点的场景具象化为工作流路线提供了有观点的叙事。
但 Nano Banana 2（gemini-3-pro-image）已能自己做出有叙事感的画面，GPT-Image 2 则直接
产出带文字论证的概念图——工作流路线"改写节点补想象力"的优势，只对更弱的生图模型成立。
改写节点补的始终是模型能力短板，只是这次短板从"听不懂格式"变成了"缺少观点"——最强
的原生模型连观点也能自己补。

哪条路线更贴近用户想要的效果，取决于用户目标：要"一幅好看的插图"，三条路线均合格；
要"对 AGI 之后工作场景的想象与回答"，GPT-Image 2 最强，工作流路线其次，Nano Banana 2
有观点但信息密度略低。

### 已知问题与失败记录

- **早期运行 temperature 参数失败**：给 kimi-k3 显式传 `temperature=0.3` 被 400 拒绝
  （该模型只允许默认值 1），3 次改写全部失败（run_id=`20260821T014302Z`）；
  修正为不传 temperature 后重跑成功。失败记录保留在 `validation/` 对应子目录中。
- **Nano Banana 2 偶发内容过滤**：早期运行中 `agi-programmer` 需求偶发 content=None
  （候选响应被过滤），最终正式运行（`20260821T040450Z`）全部 5 句均一次成功。
  这是非确定性行为，非模型不可用。
- **SiliconFlow / 传统 SD 不可用**：FLUX.1-schnell 与 Stable Diffusion 3.5 均下线
  （Model disabled），账户余额为 0；OpenRouter 仅提供视觉理解模型，不支持文本转图像生成。
  改用通义万相，见「模型选型实录」。
- **GPT-Image 2 全量可用**：5 句需求均一次成功（耗时 30–50s / 次）。
