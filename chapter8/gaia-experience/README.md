# 实验 8-2：从 GAIA 轨迹提炼经验知识文档

本项目对应第八章“将经验沉淀为知识”。新版实验不再把一条成功轨迹压缩成 JSON 后直接做 RAG，而是先依据环境结果把轨迹标为成功、部分成功或失败，再比较同一任务族的多条路径，最后生成可检索的 Markdown 经验文档。

核心实验完全离线：

```bash
python demo_documents.py
python -m unittest -v test_experience_documents.py
```

真实 LLM 提取路径会逐条读取已评价运行，用模型生成候选的适用条件、策略、误区与例外，再由同一个跨轨迹支持度规则决定哪些内容能进入正式文档：

```bash
pip install -r requirements-lite.txt
export OPENAI_API_KEY=your_api_key_here
python demo_documents.py --extractor llm --model gpt-5.6
```

该命令会真实调用 OpenAI Responses API，并产生 API 费用。LLM 只负责提出候选归纳，`environment_score`、两条轨迹支持门槛、来源记录和迁移评估仍由程序控制。若要在完整 GAIA 环境中采集真实轨迹，再安装主 `requirements.txt` 与 AWorld。

运行后，`output/experience_documents/` 会生成两份教学样例文档。每份文档都包含适用场景、推荐策略、常见误区、例外条件、来源轨迹和最近验证时间。推荐策略至少需要两条非失败轨迹支持，因此一次偶然成功不会直接升级为正式知识；失败和部分成功轨迹则用于提炼排除性知识。

`demo_documents.py` 同时比较三种条件：无经验、直接检索单条轨迹摘要、检索跨轨迹知识文档。报告包含迁移成功率、检索文本开销和负迁移率。这里使用可解释的规则化指标保证离线复现；在完整 GAIA 实验中，应替换为实际任务成功率、Token/延迟统计，以及使用错误经验后产生的性能下降。

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `experience_documents.py` | 结果标注、跨轨迹归纳、Markdown 生成、检索与三基线评估 |
| `sample_trajectories.json` | 含成功、部分成功和失败的教学轨迹及迁移任务 |
| `demo_documents.py` | 无 API Key 的主实验入口 |
| `llm_extractor.py` | 调用真实 LLM，从已评价运行提出结构化经验候选 |
| `test_experience_documents.py` | 对结果分级、证据来源、文档生成和迁移效果的测试 |
| `run_with_experience.py` | 基于 AWorld 运行真实 GAIA 任务的扩展入口 |
| `experience_agent.py` / `trajectory_summarizer.py` | 旧版单轨迹捕获与摘要适配器，用于把 AWorld 输出转换为学习证据 |
| `AWorld/` | 上游框架副本，本实验不修改 |

## 接入真实 GAIA 轨迹

先用 `run_with_experience.py` 保存原始轨迹和任务评分，再将每条运行转换为以下最小记录：

```json
{
  "id": "task-and-run-id",
  "task_family": "web_research",
  "capabilities": ["search", "source_verification"],
  "question": "...",
  "environment_score": 0.75,
  "applies_when": ["..."],
  "observed_strategies": ["..."],
  "mistakes": ["..."],
  "exceptions": ["..."]
}
```

`environment_score` 必须来自 GAIA 答案验证或其他外部验证器，不能由总结模型自行断言。能力聚类、策略候选与误区可以由 LLM 辅助提取，但生成文档时仍要保留原始轨迹 ID，以便回查和重新验证。

旧的 `--learning-mode` 仍可用于捕获 AWorld 成功轨迹，但它只构成证据采集基线，不再代表本章所说的完整经验学习方法。正式对照应在互不重叠的学习集和迁移集上完成，避免把同一 GAIA 题目的答案作为经验注入评测。
