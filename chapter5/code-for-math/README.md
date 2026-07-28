# Experiment 5-1: Code Tools for Math / 实验 5-1：用代码生成工具提升数学解题能力

> Companion lab for *AI Agents in Depth*, Chapter 5 — same model, same problem set: pure CoT vs code-assisted solving in a Python sandbox (sympy/numpy/scipy).  
> 《深入理解 AI Agent》第 5 章配套实验（★★）：同模型同题集对比「纯思维链」与「代码辅助」，后者在沙箱执行 sympy/numpy/scipy。

← [Chapter 5 index / 返回第 5 章目录](../README.md)

---

## English

### Purpose

Large models often fail at “mental arithmetic” on large numbers, enumeration, and factorization—not because they lack the method, but because they miscalculate. This lab runs the **same model** (default `gpt-5.6-luna`) on the **same problems** in two modes:

- **Pure CoT**: natural-language step-by-step reasoning only; no code.
- **Code-assisted**: formalize the problem as Python (sympy, numpy, scipy), call `run_python` via function calling in a **subprocess sandbox**, and use exact results instead of mental math.

### How it works

```
Problem ──► Model
              │  Pure CoT: natural-language reasoning ──► final answer (error-prone)
              │
              └─ Code-assisted: generate Python
                           │  function calling
                           ▼
                     run_python tool (subprocess sandbox; sympy/numpy/scipy; timeout)
                           │  stdout
                           ▼
                     Model continues from exact results ──► final answer (more accurate)
```

- Tools are exposed via OpenAI **function calling**; the model decides when and what to code.
- The sandbox is `run_python()` in `sandbox.py`: write code to a temp file, run in a subprocess with a 20s timeout so crashes/loops do not take down the parent. `sympy` / `numpy` / `scipy` are pre-imported.
- Problems live in `problems.json`: 11 AIME-style contest problems with **integer answers, offline-validated by brute force**, covering number theory, modular arithmetic, Diophantine equations, generating functions, prime factorization, lattice points, etc. Each item also has a reference `solution` for offline self-check.

### Offline self-check (no API key)

To verify the sandbox + ground-truth pipeline without an API key:

```bash
pip install -r requirements.txt
python demo.py --selfcheck        # run each problem's reference solution in the sandbox; score vs truth
```

It runs the reference solutions from `problems.json` in the subprocess sandbox, extracts integer outputs, and compares to ground truth—demonstrating “write code → sandbox → score by truth” and checking the dataset itself. Exit code 0 when all hit. Real output (11/11 pass):

```
题号   考点                             真值      沙箱输出
--------------------------------------------------------
1    number theory (inclusion-exclusion)    925       925   ✓
2    modular exponentiation        216       216   ✓
...
11   lattice points               1245      1245   ✓
--------------------------------------------------------
参考解命中真值：11/11
```

### Run the comparison (API key required)

```bash
cp env.example .env   # or export OPENAI_API_KEY=...
export OPENAI_API_KEY=sk-...      # also supports MOONSHOT_API_KEY / ARK_API_KEY

python demo.py                    # full comparison (code vs cot)
python demo.py --verbose          # also print generated code and sandbox results
python demo.py --limit 3          # first 3 problems only (cheaper debug)
python demo.py --mode code        # code-assisted only
python demo.py --mode cot         # pure CoT only
python demo.py --model gpt-5.6-luna   # override model (same as MODEL env)
python demo.py --output result.json   # write per-problem results + summary JSON
python demo.py --problems mine.json   # custom problem bank
```

Full flags: `python demo.py --help`. Common switches:

| Flag | Description |
| --- | --- |
| `--mode {both,code,cot}` | Solve mode; default `both` (run both and compare) |
| `--selfcheck` | Offline self-check; sandbox reference solutions only; no API key |
| `--model NAME` | Override model (higher priority than `MODEL`) |
| `--problems PATH` | Problem bank JSON; default `problems.json` |
| `--limit N` | First N problems only |
| `--output PATH` | Write per-problem results to JSON |
| `--verbose` | Print generated code and sandbox results |

Env vars: `OPENAI_API_KEY` (or `MOONSHOT_API_KEY` / `ARK_API_KEY`), `OPENAI_BASE_URL` (compatible endpoint), `MODEL` (default `gpt-5.6-luna`).

**OpenRouter fallback**: if no direct key is set but `OPENROUTER_API_KEY` is, traffic goes through OpenRouter (model mapping: `gpt-*` → `openai/*`, others → `openai/gpt-5.6-luna`). Default `gpt-5.6-luna` is gpt-5.x and needs org verification on direct OpenAI, so with `OPENROUTER_API_KEY` set, OpenRouter is preferred (`openai/gpt-5.6-luna`).

### Sample results / takeaway

Real run of `gpt-5.6-luna` (11 problems; reasoning model default `temperature=1`), excerpt:

```
题号   考点                             真值     CoT预测          代码预测
------------------------------------------------------------------------------
2    modular exponentiation        216       216   ✓       216   ✓
6    sum of two squares            330       306   ✗       330   ✓
7    prime factorization           661       661   ✓       661   ✓
10   factorials and modular arithmetic    313       313   ✓       313   ✓
11   lattice points               1245      1245   ✓      1245   ✓
------------------------------------------------------------------------------
准确率                                  10/11 =   91%     11/11 =  100%
```

| Mode | Accuracy (this run) |
| --- | --- |
| Pure CoT | 10 / 11 (≈ 91%) |
| Code-assisted | 11 / 11 (100%) |

**Code-assisted accuracy is stably at least as good as pure CoT.** Strong reasoners like `gpt-5.6-luna` already score high on pure CoT, but still slip on heavy enumeration / boundary-sensitive items—here problem 6 (“sum of two squares” counting under \(x^2+y^2 < 400\)-style bounds): CoT miscounted to 306 instead of 330. Code-assisted hands that enumeration to sympy/numpy and reaches a full score.

> **Stronger models narrow the gap; the direction stays the same.** On weaker models, pure CoT fails more often on large modular arithmetic, factorial modular sums, lattice counting, perfect-square checks, etc., and the code-assisted lead grows. Code-assisted is not magic: weak models can emit “right idea, wrong details” enumeration code, and the sandbox then executes a buggy program. Across model strengths, “code-assisted ≥ pure CoT, often much higher” holds.

> **Another model ↔ harness tradeoff.** Measured on both weak and strong models: weaker `gpt-4o-mini` pure CoT 6/11 vs code-assisted 8/11 (**+2**); stronger `gpt-5.6-luna` pure CoT 10/11 vs code-assisted 11/11 (**+1**, only the hardest enumeration left for code). If pure thinking ever fully solves the set, code gains can collapse to 0 (as in sister lab `code-for-logic`). **How thick the harness should be depends on the model’s capability boundary.**

### Adapt / extend

- **Model / provider**: set `MODEL` (e.g. `MODEL=gpt-5.6-luna`, `MODEL=claude-opus-4.8`); set `MOONSHOT_API_KEY` (Kimi) or `ARK_API_KEY` (Doubao), or point `OPENAI_BASE_URL` at any OpenAI-compatible endpoint.
- **Problem bank**: edit `problems.json` with `question` / `answer` (integer) / `topic` and a `solution` that prints the answer. After adding items, run `python demo.py --selfcheck` so reference solutions produce ground truth in the sandbox.
- **Sandbox libraries**: extend `PREAMBLE` in `sandbox.py` and update `requirements.txt`.

### Limitations

- Teaching-grade sandbox (subprocess + timeout + temp dir), **not a security boundary**; production needs containers / gVisor / network-isolated sandboxes.
- Accuracy still depends on model quality: small models can write buggy code; code assistance reduces but does not eliminate errors.
- Answer extraction expects `FINAL ANSWER: <integer>`; non-integer / multi-value answers need changes to `extract_answer` and scoring.

### Files

| File | Role |
| --- | --- |
| `demo.py` | Main: comparison + function-calling loop + results table + `--selfcheck` |
| `sandbox.py` | Subprocess Python sandbox (`run_python`, timeout, math libs) |
| `problems.json` | 11 contest problems (stem + validated integer truth + topic + reference `solution`) |
| `requirements.txt` | Dependencies |
| `env.example` | Env var sample |

---

## 中文

### 目的

大模型「心算」大数、枚举、因式分解时极易出错——不是不会方法，而是算错。
本实验让同一个模型（默认 `gpt-5.6-luna`）在同一组题上跑两种模式，直接对比：

- **纯 CoT**：只能用自然语言一步步推理，禁止写代码；
- **代码辅助**：把题目形式化为 Python（sympy 符号计算、numpy 矩阵、scipy 数值求解），
  通过 function calling 调用 `run_python` 工具在**子进程沙箱**里执行，用精确结果替代心算。

### 原理

```
题目 ──► 模型
          │  纯 CoT：直接自然语言推理 ─────────────► 最终答案（易算错）
          │
          └─ 代码辅助：生成 Python 代码
                       │  function calling
                       ▼
                 run_python 工具（子进程沙箱，预装 sympy/numpy/scipy，超时保护）
                       │  返回 stdout
                       ▼
                 模型基于精确结果继续推理 ──────────► 最终答案（更准）
```

- 工具用 OpenAI **function calling** 暴露：模型自主决定何时写代码、写什么代码。
- 沙箱是 `sandbox.py` 里的 `run_python()`：把代码写入临时文件，用子进程执行，
  带 20 秒超时，崩溃/死循环不影响主进程。预导入了 `sympy / numpy / scipy`。
- 题目在 `problems.json`：11 道 AIME 风格竞赛题，**答案均为整数、已用暴力枚举离线校验**，
  覆盖数论、模运算、丢番图方程、生成函数、素因子分解、格点计数等。每题还附带一段
  `solution` 参考解代码，用于离线自检（见下）。

### 离线自检（无需 API key）

想验证「沙箱 + 题库真值」这条链路是否可用、但手头没有 API key？跑：

```bash
pip install -r requirements.txt
python demo.py --selfcheck        # 在沙箱中执行每题的参考解，按真值判分
```

它会对每道题执行 `problems.json` 里附带的参考解，在子进程沙箱中运行，抽取整数输出
与真值比对——这既演示了「写代码 → 沙箱执行 → 按真值判分」的核心机制，也自检了题库
真值本身。全部命中时退出码为 0。真实输出（11/11 全部通过）：

```
题号   考点                             真值      沙箱输出
--------------------------------------------------------
1    number theory (inclusion-exclusion)    925       925   ✓
2    modular exponentiation        216       216   ✓
...
11   lattice points               1245      1245   ✓
--------------------------------------------------------
参考解命中真值：11/11
```

### 运行对照实验（需要 API key）

```bash
cp env.example .env   # 或直接 export OPENAI_API_KEY=...
export OPENAI_API_KEY=sk-...      # 也支持 MOONSHOT_API_KEY / ARK_API_KEY

python demo.py                    # 跑完整对照实验（code 与 cot 两种模式）
python demo.py --verbose          # 额外打印模型生成的代码与执行结果
python demo.py --limit 3          # 只跑前 3 题（省钱调试）
python demo.py --mode code        # 只跑代码辅助模式
python demo.py --mode cot         # 只跑纯思维链模式
python demo.py --model gpt-5.6-luna   # 覆盖模型名（等价于设 MODEL 环境变量）
python demo.py --output result.json   # 把逐题结果与汇总写入 JSON
python demo.py --problems mine.json   # 换用自定义题库
```

完整参数见 `python demo.py --help`。常用开关：

| 参数 | 说明 |
| --- | --- |
| `--mode {both,code,cot}` | 求解模式，默认 `both`（两种都跑并对照） |
| `--selfcheck` | 离线自检，只跑沙箱参考解，无需 API key |
| `--model 名称` | 覆盖模型名（优先级高于 `MODEL` 环境变量） |
| `--problems 路径` | 题库 JSON 路径，默认 `problems.json` |
| `--limit N` | 只跑前 N 题 |
| `--output 路径` | 把逐题结果写入 JSON 文件 |
| `--verbose` | 打印生成的代码与沙箱执行结果 |

可用环境变量：`OPENAI_API_KEY`（或 `MOONSHOT_API_KEY` / `ARK_API_KEY`）、
`OPENAI_BASE_URL`（切换兼容端点）、`MODEL`（默认 `gpt-5.6-luna`）。

**通用 OpenRouter 兜底**：未配置任何直连 key 时，只要设置了 `OPENROUTER_API_KEY`
即可自动改走 OpenRouter（模型名自动映射：`gpt-*` → `openai/*`，其它 → `openai/gpt-5.6-luna`）。
另外默认模型 `gpt-5.6-luna` 属于 gpt-5.x，直连 OpenAI 调用它需要组织实名认证，
因此只要设置了 `OPENROUTER_API_KEY` 就会优先走 OpenRouter（route `openai/gpt-5.6-luna`）。

### 预期输出示例 / 结论

真实跑 `gpt-5.6-luna`（11 题，reasoning 模型默认 `temperature=1`）的一次逐题结果节选：

```
题号   考点                             真值     CoT预测          代码预测
------------------------------------------------------------------------------
2    modular exponentiation        216       216   ✓       216   ✓
6    sum of two squares            330       306   ✗       330   ✓
7    prime factorization           661       661   ✓       661   ✓
10   factorials and modular arithmetic    313       313   ✓       313   ✓
11   lattice points               1245      1245   ✓      1245   ✓
------------------------------------------------------------------------------
准确率                                  10/11 =   91%     11/11 =  100%
```

| 模式 | 准确率（本次实测） |
| --- | --- |
| 纯 CoT | 10 / 11（≈ 91%） |
| 代码辅助 | 11 / 11（100%） |

**代码辅助模式准确率稳定地不低于纯 CoT。** `gpt-5.6-luna` 这类强推理模型的纯 CoT 已经相当准，
但在需要大量枚举 / 边界易错的题上仍会翻车——本次唯一漏掉的是第 6 题「两平方和计数」
（x²+y²<400 之类的表示计数，CoT 心算边界算错，给出 306 而非 330）。代码辅助把这类
枚举交给 sympy/numpy 精确执行，把这道题也补齐，达到满分。

> **强模型让差距收窄，但方向不变。** 换成更弱的小模型，纯 CoT 会在
> 更多需要大数运算 / 大量枚举的题上出错（大数取模、100! 累加取模、格点计数、完全平方判定等），
> 代码辅助的领先幅度会明显更大；而代码辅助也并非绝对万能：弱模型偶尔会写出「思路对、细节错」
> 的枚举代码，此时精确执行的是一段有 bug 的代码。无论模型强弱，「代码辅助不低于、通常显著高于
> 纯 CoT」这一结论都稳定成立。

> **这正是「模型 ↔ 脚手架（harness）此消彼长」的又一例证。** 本实验在强弱两个模型上都实测过：
> 较弱模型 `gpt-4o-mini` 纯 CoT 6/11、代码辅助 8/11，代码这层脚手架把差距拉开 **+2 题**；换成强推理模型
> `gpt-5.6-luna`，纯 CoT 自己就升到 10/11、代码辅助 11/11，差距收窄到 **+1 题**（只剩最难的枚举题「两平方和计数」需要代码兜底）。
> 模型越强，代码能替它补的越少；若再强到纯思考也能全解，代码辅助的增益就会像姊妹实验 `code-for-logic` 那样收敛到 0。
> **脚手架该做多厚，取决于你手上模型的能力边界**——这也是评估一项 Agent 技术时容易被忽视的前提。

### 如何适配 / 扩展

- **换模型 / 供应商**：设 `MODEL` 环境变量即可换模型（如 `MODEL=gpt-5.6-luna`、`MODEL=claude-opus-4.8`）；
  换供应商则设 `MOONSHOT_API_KEY`（自动切 Kimi）或 `ARK_API_KEY`（自动切豆包），
  或用 `OPENAI_BASE_URL` 指向任意兼容 OpenAI 协议的端点。更强模型能把偶发的 bug 代码补齐。
- **换题库**：编辑 `problems.json`，每题给出 `question` / `answer`（整数）/ `topic`，
  并附一段 `solution`（打印答案的 Python 参考解）。建议新增题目时像现有题一样**先用
  `python demo.py --selfcheck` 让参考解在沙箱里跑出真值**，避免答案本身出错。
- **换沙箱能力**：`sandbox.py` 的 `PREAMBLE` 预导入 sympy/numpy/scipy；要支持更多库
  就在此追加 import 并同步更新 `requirements.txt`。

### 局限

- 沙箱是教学级实现（子进程 + 超时 + 临时目录），**不是安全隔离边界**；生产环境应换成
  容器 / gVisor / 无网络的强隔离沙箱。
- 准确率依赖模型质量：小模型仍可能写出有 bug 的代码（见上），代码辅助降低但不消除错误。
- 答案抽取按 `FINAL ANSWER: <整数>` 解析，仅支持整数型答案；非整数 / 多值答案需改
  `extract_answer` 与判分逻辑。

### 文件

| 文件 | 说明 |
| --- | --- |
| `demo.py` | 主程序：对照实验 + function calling 循环 + 结果表 + 离线自检（`--selfcheck`） |
| `sandbox.py` | 子进程 Python 沙箱（`run_python`，超时保护，预装数学库） |
| `problems.json` | 11 道竞赛题（题面 + 已校验的整数真值 + 考点 + 参考解 `solution`） |
| `requirements.txt` | 依赖 |
| `env.example` | 环境变量样例 |

---

## Notes / 说明

- Prefer `--selfcheck` first if you have no API key. / 无 API Key 时先跑 `--selfcheck`。
- Code/commands/paths/env vars are identical in both language sections. / 命令、代码、路径与环境变量在中英文两侧保持一致。
