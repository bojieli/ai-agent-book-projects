# 攻击语料 / 红队资源索引（只读对照，不 import 进 Gateway）

本目录放**可直接喂平台红队**的公开样本；完整自动化探针仍用 `llm-safety-study/garak`。

## 已落地文件

| 文件 | 来源 | 规模 | 用途 |
|------|------|------|------|
| `advbench_harmful_behaviors.csv` | [AdvBench](https://github.com/llm-attacks/llm-attacks) | ~520 | 有害意图（goal 列） |
| `jbb_harmful.csv` | [JailbreakBench](https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors) | 100 | 有害行为（Goal/Category） |
| `jbb_benign.csv` | 同上 | ~100 | 良性对照（测误拦；expect=allow） |
| `seed_zh_en.yaml` | 平台自建种子 | 小 | 对齐你们 categories + 中文金融场景 |
| `flames_1k_zh.csv` | [Flames](https://github.com/AI45Lab/Flames) | 1000 | 中文高对抗价值观/安全提示（Goal） |
| `chisafetybench_risky_qa_zh.csv` | [CHiSafetyBench](https://github.com/UnicomAI/UnicomBenchmark/tree/main/CHiSafetyBench) | 462 | 中文应拒答风险问（含政安/暴恐/歧视等） |
| `cpad_zh_sample250.csv` | [CPAD](https://github.com/liuchengyuan123/CPAD) | 250 | 中文越狱模板抽样（诈骗/间谍/色情等） |
| `jailbench_zh_sample300.csv` | [JailBench](https://github.com/STAIR-BUPT/JailBench) 公开子集 | 300 | 中文越狱增强问（完整集需申请） |
| `../promptfoo.yaml` | 平台 | 小 | CI 回归 |
| `handbook_v1_full.yaml` | SecureNexusLab Handbook V1.0 | 84 | 手册 ch.2–7 全量攻击包 |
| `handbook_pi_attacks.yaml` | 同上 | 15 | 手册样本子集 |
| `handbook_expanded/*.yaml` | 手册族扩展（生成） | **25×100=2500** | 无 context-overflow；见 `docs/.../14_扩展攻击语料.md` |
| `handbook_expanded_smoke.yaml` | 同上 smoke | 125 | CI `corpus_gates`（5/scenario） |
| `oss_agentic_security.yaml` | [agentic_security](https://github.com/msoedov/agentic_security) 适配 | 40 | stenography / 越狱抽样（study only） |
| `oss_garak_sample.yaml` | [garak](https://github.com/NVIDIA/garak) 适配 | 24 | encoding/DAN/grandma 小样 |
| `oss_purplellama_sample.yaml` | [PurpleLlama CyberSecEval](https://github.com/meta-llama/PurpleLlama) 适配 | 83 | 有界 CSE 抽样（shim 规则层 leak 高属预期） |

CSV 列兼容 `corpus_runner`：`Goal`/`goal`/`prompt`/`text`；期望决策默认 `block`。

## 国内 / 中文安全评测语料（推荐索引）

> 政治敏感、金融合规类条目**仅作内网红队**；上线前建议法务/合规审阅。勿把完整有害集打进生产镜像。

| 库 | 链接 | 规模 | 许可 | 可下载 | 语言 | 类别覆盖 | 适配本平台 |
|----|------|------|------|--------|------|----------|------------|
| **CHiSafetyBench** | [GitHub](https://github.com/UnicomAI/UnicomBenchmark/tree/main/CHiSafetyBench) / [论文](https://arxiv.org/abs/2406.10311) | MCQ~1.8k + QA 拒答子集 | 未明示（研究开源） | ✅ QA/MCQ JSON | 中文 | 对齐国标《生成式人工智能服务安全基本要求》：5 大域 / 31 类（政安、暴恐、色情、歧视、虚假信息等） | **首选拒答集**；已落地 `chisafetybench_risky_qa_zh.csv` |
| **Flames** | [GitHub](https://github.com/AI45Lab/Flames) / [HF](https://huggingface.co/datasets/PKU-Alignment/Flames-1k-Chinese) | 公开 1k（全文 2.2k） | Apache-2.0 / HF 镜像 CC-BY-NC-4.0 | ✅ | 中文 | Fairness / Safety / Morality / Legality / Data protection | **首选对抗提示**；已落地 `flames_1k_zh.csv` |
| **JailBench** | [GitHub](https://github.com/STAIR-BUPT/JailBench) | Seed + 10.8k 越狱增强 | 研究用；完整集申请 | ⚠️ 仓库仅低危公开样 | 中文 | 国标主要安全风险 + 越狱模板 | 强越狱压力；已落地公开样 `jailbench_zh_sample300.csv`；完整集填表申请 |
| **CPAD** | [GitHub](https://github.com/liuchengyuan123/CPAD) | ~10k | CC BY-SA 4.0 | ✅ (~8MB JSONL) | 中文 | 诈骗/间谍/暴恐/色情/歧视/越狱模板等 | 长场景越狱；已落地分层抽样 `cpad_zh_sample250.csv` |
| **SafetyBench (ZH)** | [HF](https://huggingface.co/datasets/thu-coai/SafetyBench) / [GitHub](https://github.com/thu-coai/SafetyBench) | 11k+ MCQ（含中英） | MIT | ✅ | 中英 | 7 类安全（含中文子集） | **MCQ 不直接喂 corpus_runner**；适合模型安全知识测评 |
| **thu-coai Safety-Prompts** | [GitHub](https://github.com/thu-coai/Safety-Prompts) | ~100k | Apache-2.0 | ✅ | 中文 | 八大安全场景问答 | 体量大；可按类抽样转 CSV |
| **CValues** | [GitHub](https://github.com/X-PLUG/CValues) | Prompts~0.6–0.8k；Comparison 145k | Apache-2.0 | ✅ | 中文 | Safety→Responsibility；含「100瓶毒药」删减版 | 价值观/责任向；**不全是 expect=block**；金融/政审相关需人工筛 |
| **Chinese Do-Not-Answer (CDNA)** | [论文/仓库](https://github.com/Libr-AI/do-not-answer) / [HF walledai/CDNA](https://huggingface.co/datasets/walledai/CDNA) | 3,042 | 研究开源 | ✅ HF | 中文 | 6 风险大类 / 17 细类 + 地区特有风险；含 FN/FP | 拒答边界 + 过度拒答；适合对照 `expect=allow` 子集 |
| **CSEI-SafetyBench** | [HF BAAI](https://huggingface.co/datasets/BAAI/CSEI-SafetyBench) | 1,000（显式 600 + 隐式 400） | 见 HF card | ✅ HF | 中文 | 显式/隐式有害（含政治安全） | 隐式风险测关键词绕过；适合补测 |
| **JADE** | 搜 JADE Chinese safety / SafetyPrompts.com | ~2.1k | MIT | ✅ | 中英 | 语言学变异有害问 | 模糊/改写攻击；可抽样 |
| **XSafety** | SafetyPrompts.com / 相关论文 | ~28k（多语） | Apache-2.0 | ✅ | 含中文 | 多语不安全指令 | 中文子集可抽 |
| **SorryBench (ZH)** | 相关论文/HF | 多语不安全指令 | MIT | ✅ | 含中文 | 细粒度有害 | 补覆盖 |
| **BeaverTails** | [HF](https://huggingface.co/datasets/PKU-Alignment/BeaverTails) | 300k+ | CC-BY-NC-4.0 | ✅ | **英文为主** | 14 类 QA 安全偏好 | 非中文主测；有「BeaverTails-zh」民间翻译需自验质量 |
| **SafetyBench CN subset** | 同上 thu-coai | 每类 300 | MIT | ✅ | 中文 | 去高敏词后的 API 友好子集 | 测国内 API 过滤时有用 |

### 落地优先级（on-prem 内容安全网关）

1. **CHiSafetyBench 拒答 QA** — 国标类别、政治/暴恐/色情覆盖，直接 `expect=block`
2. **Flames-1k** — 高对抗中文提示，测对齐漏洞
3. **CPAD / JailBench** — 越狱模板与长场景攻击
4. **CDNA FN/FP** — 漏拦 vs 误拦（金融合规场景尤其要看 FP）
5. **CValues / Safety-Prompts** — 责任价值观与大规模场景补全（需筛选）

## 推荐公开库（英文 / 通用，按需拉）

| 库 | 链接 | 说明 |
|----|------|------|
| **garak probes** | 已在 `llm-safety-study/garak/garak/probes/` | DAN、encoding、promptinject、toxicity… **首选攻击引擎** |
| **JailbreakBench** | https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors | 100 有害 + 100 良性行为 |
| **HarmBench** | https://github.com/centerforaisafety/HarmBench | 标准化红队评测 |
| **AdvBench** | 本目录 CSV | GCG 原始有害行为表 |
| **promptfoo redteam** | `llm-safety-study/promptfoo` | CI 断言式攻击 |
| **PyRIT** | `llm-safety-study/PyRIT` | 多轮自适应（需另配攻击模型） |
| **Do-Not-Answer** | 学术集（英） | 拒答边界；中文见上表 CDNA |

## 怎么用到本平台

```bash
# 种子 / JailbreakBench / AdvBench
cd llm-safety-platform
.venv/bin/python -m app.redteam.corpus_runner \
  --source configs/evals/attack_corpora/seed_zh_en.yaml
.venv/bin/python -m app.redteam.corpus_runner \
  --source configs/evals/attack_corpora/jbb_harmful.csv --mode gateway
.venv/bin/python -m app.redteam.corpus_runner \
  --source configs/evals/attack_corpora/advbench_harmful_behaviors.csv --limit 50

# 中文语料（shim / 全量 Gateway）
.venv/bin/python -m app.redteam.corpus_runner \
  --source configs/evals/attack_corpora/chisafetybench_risky_qa_zh.csv --limit 20
.venv/bin/python -m app.redteam.corpus_runner \
  --source configs/evals/attack_corpora/flames_1k_zh.csv --limit 50
.venv/bin/python -m app.redteam.corpus_runner \
  --source configs/evals/attack_corpora/cpad_zh_sample250.csv --limit 20
.venv/bin/python -m app.redteam.corpus_runner \
  --source configs/evals/attack_corpora/jailbench_zh_sample300.csv --limit 20

# DeepSeek Judge（每条一次 classify，推荐）
./scripts/eval_attack_corpora.sh deepseek
# 或 LIMIT=20 ./scripts/eval_attack_corpora.sh deepseek

# Handbook expanded（shim）
./scripts/eval_attack_corpora.sh expanded_smoke
EXPANDED_LIMIT=20 ./scripts/eval_attack_corpora.sh expanded
# 重生：.venv/bin/python scripts/generate_handbook_expanded_corpora.py
```

报告写入 `reports/`：`jbb_harmful_shim.json`、`jbb_harmful_deepseek.json`、`SUMMARY.json` 及对应 `*_leaks.json`。

### 最近评测快照（JailbreakBench harmful 100）

| 模式 | 拦截 | 漏拦率 | 说明 |
|------|------|--------|------|
| shim gateway（规则加深后） | 见 `reports/jbb_harmful_shim.json` | — | 含 harassment/fraud/expert_advice 等 |
| DeepSeek classify | **94/100** | **6%** | 报告后已用规则补齐剩余 6 条（赌光积蓄/阴谋论/个性化医疗/荐股） |
| DeepSeek classify（前 20 冒烟） | 20/20 | 0% | `jbb_harmful_deepseek_20.json` |

期望：护栏 `decision=block`（或 redact）；`allow` 计为漏拦。
