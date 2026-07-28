## English

# CoT Distillation: Collecting SFT Data from Frontier Cloud Models

This experiment builds a small, auditable pipeline for collecting chain-of-thought supervised fine-tuning data from teacher models. It supports OpenAI-compatible endpoints, Anthropic, and OpenRouter, validates generated answers, and writes accepted samples as JSONL.

## Method

The pipeline loads problems, asks a selected teacher model to produce worked solutions, extracts the final answer, and keeps only samples that pass answer validation. The output can then be used as SFT data for a smaller student model.

## Choosing a teacher model

The default does not have to be a closed-source model. A strong open model served through an OpenAI-compatible endpoint is often cheaper, easier to reproduce, and sufficient for data collection. Closed models remain useful as comparison teachers.

## Run

```bash
pip install -r requirements.txt
cp env.example .env

# Small smoke test with two problems
python collect.py --limit 2

# Collect the full set of 24 AIME problems
python collect.py

# Inspect dataset statistics
python stats.py output/sft_data.jsonl
```

Provider, model, concurrency, retry, and output settings can be configured through command-line arguments and environment variables. See `python collect.py --help` for the complete list.

## Output

Each accepted JSONL row contains the problem, messages, teacher metadata, extracted answer, reference answer, and validation result. Failed or invalid generations are recorded separately so collection runs remain auditable.

## AIME comparison

The included notes compare three teachers over 24 AIME problems, covering answer accuracy, accepted sample counts, token use, latency, and estimated cost. Results depend on model versions and provider conditions, so rerun the experiment before making a production choice.

## Archived simple Chinese problems

Earlier easy Chinese arithmetic samples are retained as historical artifacts. They are useful for smoke testing but are not a meaningful reasoning benchmark.

---

## 中文

# CoT 蒸馏：从前沿云模型采集 SFT 数据

配套书中**实验 7-9（思维链蒸馏）**。SFT 的第一步是拿到高质量示范数据，而获取
SFT 数据最高效的方式就是**蒸馏前沿模型**：通过大规模 API 调用，把教师模型的
"思考 + 答案"轨迹采集下来，经规则验证器过滤后作为学生模型的训练数据
（DeepSeek-R1 蒸馏小模型走的就是这条路线）。

## 方法

三步流程（对应实验 7-9 的第一步"采集轨迹"）：

1. **采样任务**：`problems.jsonl` 内置 24 道 AIME 真题（1986–2024 年，按题号
   难度分层抽样：P1–5/P6–10/P11–15 各 8 道，已剔除含图形的题），答案是
   0–999 的整数，可以用规则验证器自动判对错。`problems_zh.jsonl` 另附 24 道
   简单中文数学题（鸡兔同笼、工程问题等），适合低成本冒烟测试。
2. **采集轨迹**：`generate_data.py` 通过 OpenRouter 调用教师模型
   （默认 `anthropic/claude-opus-4.8`），开启 `reasoning` 参数获取思维链。
   注意：Claude API 返回的是 **summarized thinking**（由单独的摘要模型改写，
   逐 token 的原始思维链只存在于加密的 `signature` 字段中，API 不暴露），
   且模型越新摘要越激进（见文末实测）。若需要逐 token 原文，
   推荐直接用开放模型原生 API，例如 Kimi K3（见下文对照实验的运行参数）。
3. **验证过滤**：用规则验证器核对 `Final Answer` 数值，只保留答对的轨迹，
   写成 `问题 → <think>思考</think> + 最终答案` 的 messages 格式 SFT 数据。
   错误的思考过程会被学生一并模仿，所以这一步不能省。

## 教师模型怎么选：默认开源 SOTA，不必盯着闭源

对绝大多数做后训练的人来说，**不需要**去蒸馏闭源模型的思维链。当前最先进的
开源模型（DeepSeek V4、Kimi K3、GLM 5.2 等）与 SOTA 闭源模型的差距并没有
想象中大；如果你要后训练的是 200B 及以下规模的模型，用开源 SOTA 模型当教师
已经完全够用——教师的水平只需要"明显高于学生"，不需要"全球第一"。

本目录保留 Claude 的采集结果，目的是做一个对照：**闭源 API 的
summarized thinking 和开源模型的原始思维链，作为 SFT 数据到底有什么差别**。

> 合规说明：本实验只使用各厂商官方 API 提供的 reasoning/thinking 能力获取思维链
> （Claude 在 API 中返回 summarized thinking，Kimi K3、DeepSeek 等开放模型直接
> 返回原始思维链），不涉及任何绕过厂商安全机制的手段。对闭源模型，
> 蒸馏产物的使用需遵守对应服务商的条款。

## 运行

```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY=sk-or-...

# 小规模冒烟（2 道题）
python generate_data.py --max_problems 2 \
  --sft_output /tmp/smoke_sft.jsonl --raw_output /tmp/smoke_raw.jsonl

# 全量采集（24 道 AIME 题；Opus 4.8 输出约 4 万 token，Kimi K3 约 6 万）
python generate_data.py

# 数据统计
python analyze_data.py
```

常用参数：`--model` 换教师模型、`--base_url`/`--api_key_env` 换端点、
`--reasoning_effort`（Opus 4.8 等自适应思考模型）与 `--reasoning_max_tokens`
（Sonnet 4.5 等手动预算模型）控制思维链、`--concurrency` 并发数、
`--max_retries` 失败重试次数（重试时自动升温换取不同轨迹）、
`--request_timeout` 单请求硬超时（采集长思考模型时必备，见文末工程教训）。

## 输出

| 文件 | 内容 |
| --- | --- |
| `data/sft_cot_distill_aime.jsonl` | Claude Opus 4.8 的 SFT 训练数据（messages 格式，思维链包在 `<think>` 标签内） |
| `data/sft_cot_distill_aime_kimi_k3.jsonl` | Kimi K3 的 SFT 训练数据 |
| `data/raw_trajectories_*.jsonl` | 全部原始轨迹（含未通过验证的），用于分析教师错误模式 |
| `data/*_zh*.jsonl` | 中文简单题（`problems_zh.jsonl`）的归档采集结果 |

## AIME 实测：三位教师的对照（24 题）

| | Claude Sonnet 4.5 | Claude Opus 4.8 | Kimi K3 |
| --- | --- | --- | --- |
| 验证通过率 | 22/24 | 24/24 | 23/24 |
| 思维链性质 | 摘要，近 1:1 保真 | 摘要，激进压缩 | 原始思维链直出 |
| 原始/可见 token 比（精确对账） | 1.03–1.09 | **2.41** | **1.007** |
| 可见思维链规模 | 中位 6.2k 字符 | 均值 536 token | 均值 2.5k token |
| 无思维链的题 | 0 | 3（自适应思考跳过） | 0 |
| `reasoning_tokens` 字段可信度 | 虚低至 55%–75%（OpenRouter 侧） | 同样虚低 | 准确（1.001） |

token 对账方法：用模型自身 tokenizer（`max_tokens=1` 探针读 `prompt_tokens`）
数出可见思维链与正文的 token 数，`completion_tokens − 正文 token` 即为计费的
原始思考量。OpenRouter 返回的 `reasoning_tokens` 详情字段对 Claude 系统性虚低，
做成本核算时不可直接采信。

三个对后训练有直接意义的观察：

1. **模型越新，思维链围墙越高。** 同是 Claude，Sonnet 4.5 的摘要还接近逐字，
   Opus 4.8 已压到不足一半、且 3 道题完全不给思维链。思维链透明度在持续收紧。
2. **教师能力 ≠ 可蒸馏性。** Opus 4.8 答对率最高，给出的蒸馏材料却最差
   （摘要稀疏、截断、缺失）；Kimi K3 少对 1 题，但每条轨迹都是完整原文。
   选教师要同时看"会不会做"和"给不给看"。
3. **原始思维链含元噪声。** Kimi K3 的原文里有英文元思考、输出格式纠结
   （曾在简单题上用 700+ token 争论该写 `16` 还是 `16%`）、中途自我打断。
   答案验证器滤不掉这类噪声，用它做 SFT 前值得加一道清洗或重写。

工程教训（也是书中"数据管线健壮性"的实例）：Kimi K3 在个别 AIME 题上思考
超过 15 分钟（aime-2016-9-I 三次尝试均超 900 秒，最终放弃该题），且
Moonshot 端会出现"停止发送但不关闭连接"的半开状态。采集 pipeline 必须：
每题完成即落盘（本脚本增量写入 `raw_trajectories`）、用 `asyncio.wait_for`
做硬超时（httpx 读超时对半开连接无效）、失败可重试。

## 中文简单题归档结果

`problems_zh.jsonl`（24 道中学数学题）上两位教师均 24/24 通过，思维链短
（Claude 摘要均值约 290 字符，Kimi 原文均值约 165 token），适合几分钟、
几分钱成本验证 pipeline 是否工作，再切换到 AIME 或自己的目标分布。

规模化的做法是把 `problems.jsonl` 换成目标分布的题目来源（如 GSM8K、MATH
训练集），提高并发，并按书中"数据质量三维度"控制覆盖面、多样性与标注准确性。
