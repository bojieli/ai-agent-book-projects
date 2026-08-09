"""
实验 10-2 一键演示。

  python demo.py                       # 完整跑：管理者模式 + 单 Agent 对照
  python demo.py --help                # 查看全部参数
  python demo.py --dry-run             # 离线：只画四 Agent 协作图 + token 预算，不调 API
  python demo.py --model gpt-5.6-luna        # 换用更强的模型
  python demo.py --skip-single         # 只跑管理者模式，跳过单 Agent 对照（更快）
  python demo.py --no-proofreading     # 关闭审校 Agent 与修订闭环
  python demo.py --source-lang 英文 --target-lang 日文     # 换翻译方向
  python demo.py --sample-dir path/to/book --out-dir out  # 换输入书 / 产物目录

流程：
  1) 读入 --sample-dir 下的若干英文短章节（默认 sample_book/）；
  2) 运行【管理者模式】：Glossary / Translation / Proofreading / Manager 四种 Agent 协作，
     并打印四 Agent 协作的实时轨迹；
  3) 运行【单 Agent 模式】作为对照（除非指定 --skip-single）；
  4) 打印对比表：每个 Agent 的上下文 token 消耗、Manager/主上下文峰值、术语一致性。

结论要点：
  - 管理者模式下 Manager 的上下文明显小于单 Agent 的累积上下文（控制上下文膨胀）；
  - 共享术语表让术语在各章保持一致。
"""

import argparse
import glob
import os
import sys

from dotenv import load_dotenv

load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(HERE, "sample_book")
OUT_DIR = os.path.join(HERE, "output")


def parse_args():
    """命令行参数：不带任何参数运行时行为与原版完全一致。"""
    parser = argparse.ArgumentParser(
        prog="demo.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "实验 10-2：书籍翻译 Agent —— 管理者模式（Glossary/Translation/\n"
            "Proofreading/Manager 四种 Agent 协作）vs 单 Agent 模式，\n"
            "对比上下文膨胀与术语表遵从率。"
        ),
        epilog=(
            "示例：\n"
            "  python demo.py --dry-run                 # 离线画 Agent 图 + token 预算，不调 API\n"
            "  python demo.py --skip-single             # 只跑管理者模式\n"
            "  python demo.py --no-proofreading         # 关闭审校 Agent 与修订闭环\n"
            "  python demo.py --sample-dir book --out-dir out --model gpt-5.6-luna\n"
        ),
    )
    io = parser.add_argument_group("输入 / 输出")
    io.add_argument(
        "--sample-dir",
        default=SAMPLE_DIR,
        metavar="DIR",
        help="待翻译书籍目录（读取其中的 *.md 章节，按文件名排序）。默认 sample_book/。",
    )
    io.add_argument(
        "--out-dir",
        default=OUT_DIR,
        metavar="DIR",
        help="产物根目录（术语表 / 各章译文 / 审校报告写入其下的 orchestration|single_agent/）。"
             "默认 output/。",
    )

    lang = parser.add_argument_group("翻译方向")
    lang.add_argument(
        "--source-lang", default="英文", metavar="LANG",
        help="源语言，仅用于提示词措辞。默认 英文。",
    )
    lang.add_argument(
        "--target-lang", default="中文", metavar="LANG",
        help="目标语言，仅用于提示词措辞。默认 中文。"
             "注意：内置的术语一致性 / 遵从率统计针对 英文→中文 调校，改方向仍可翻译，"
             "但该统计表意义有限。",
    )

    agents_grp = parser.add_argument_group("启用哪些 Agent")
    agents_grp.add_argument(
        "--no-glossary", action="store_true",
        help="关闭 Glossary Agent（不做术语抽取，仅保留编辑部指定术语）。默认启用。",
    )
    agents_grp.add_argument(
        "--no-proofreading", action="store_true",
        help="关闭 Proofreading Agent 及 Manager 修订闭环。默认启用。",
    )

    run = parser.add_argument_group("运行方式")
    run.add_argument(
        "--model", default=None, metavar="MODEL",
        help="覆盖使用的模型（等价于设置 OPENAI_MODEL 环境变量）。"
             "默认沿用 OPENAI_MODEL 环境变量，缺省为 gpt-5.6-luna。",
    )
    run.add_argument(
        "--skip-single", action="store_true",
        help="只运行管理者模式，跳过单 Agent 对照组（更快，但不产出核心对比表）。默认关闭。",
    )
    run.add_argument(
        "--dry-run", action="store_true",
        help="离线预演：只打印四 Agent 协作图、Manager 计划、编辑部术语与各 Agent 的 token 预算，"
             "不调用任何 API（无需 OPENAI_API_KEY）。",
    )
    return parser.parse_args()


def load_chapters(sample_dir):
    """按文件名顺序读入 sample_dir/*.md，返回 {章节名: 原文}。"""
    files = sorted(glob.glob(os.path.join(sample_dir, "*.md")))
    chapters = {}
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        # 用文件的一级标题作为章节名，回退到文件名
        name = os.path.splitext(os.path.basename(path))[0]
        for line in text.splitlines():
            if line.startswith("# "):
                name = line[2:].strip()
                break
        chapters[name] = text
    return chapters


def hr(title=""):
    print("\n" + "=" * 72)
    if title:
        print(title)
        print("=" * 72)


def print_agent_table(tracker, title):
    hr(title)
    agg = tracker.by_agent()
    print(f"{'Agent':<14}{'调用次数':>8}{'输入tok':>12}{'输出tok':>12}{'上下文峰值':>12}")
    print("-" * 72)
    for name, a in agg.items():
        print(f"{name:<14}{a['calls']:>8}{a['in']:>12}{a['out']:>12}{a['peak_context']:>12}")
    print("-" * 72)
    print(f"{'合计':<14}{'':>8}{'':>12}{'':>12}  总 token：{tracker.total_tokens()}")


def print_consistency(analysis, label):
    print(f"\n[{label}] 术语一致性：{analysis['consistent_terms']}/{analysis['total_terms']} "
          f"个术语全书统一（{analysis['rate']*100:.0f}%）")
    for r in analysis["results"]:
        flag = "一致" if r["consistent"] else "不一致 <==="
        used = " / ".join(f"{v}({len(chs)}章)" for v, chs in r["by_variant"].items())
        print(f"  - {r['en']:<12} 实际用到：{used}  [{flag}]")


def make_tracer():
    """返回一个把子 Agent 事件缩进打印的 trace(str) 回调，展现 Manager 的实时调度轨迹。"""
    def tracer(msg):
        indent = "" if msg.startswith(("Manager", "Glossary", "Translation",
                                       "Proofreading")) else "  "
        # 已经带前导空格的“计划/子步骤”行原样输出
        print(f"  {indent}{msg}" if not msg.startswith("    ") else f"  {msg}")
    return tracer


def run_dry_run(args):
    """
    离线预演（不调用任何 API）：画出四 Agent 协作图、Manager 计划、编辑部指定术语，
    并用 tiktoken 估算各 Agent 将读到的上下文规模，直观印证“Manager 上下文与书长度基本无关”。
    """
    import agents
    import consistency

    chapters = load_chapters(args.sample_dir)
    if not chapters:
        print(f"错误：{args.sample_dir} 下没有找到任何 .md 章节。", file=sys.stderr)
        sys.exit(1)

    hr(f"实验 10-2 · 离线预演（--dry-run，不调用 API，模型={agents.MODEL}）")
    print(f"待翻译书籍：{args.sample_dir}（{len(chapters)} 章）  翻译方向："
          f"{args.source_lang} → {args.target_lang}")
    print(f"启用 Agent：Manager + " +
          ("Glossary + " if not args.no_glossary else "(Glossary 关闭) ") +
          "Translation" +
          (" + Proofreading" if not args.no_proofreading else " (Proofreading 关闭)"))

    hr("四 Agent 协作图（数据经文件系统流转，Manager 只持有路径）")
    print("""
        ┌─────────────────────── Manager Agent ───────────────────────┐
        │  只存：任务 / 计划 / 调用记录 / 文件索引（绝不存完整译文）      │
        └──┬───────────────┬────────────────────┬────────────────┬─────┘
           │ ①调度          │ ②逐章调度           │ ③调度           │ ④按报告决策
           ▼               ▼                    ▼                ▼
     Glossary Agent   Translation Agent×N   Proofreading Agent  (发回修订)
     读全书→术语表     只读本章+术语表→译文    读全部译文+术语表     命中章节重译
           │               │                    │
           ▼ glossary.json  ▼ chapterN_zh.md      ▼ proofreading_report.json
        ══════════════════ 共享文件系统（out-dir）══════════════════""")

    hr("Manager 执行计划（4 步）")
    for step in agents.ORCHESTRATION_PLAN:
        print(f"  {step}")

    hr("编辑部指定术语（house style，强制写入共享术语表，全书统一）")
    for en, zh in agents.EDITORIAL_MANDATE.items():
        print(f"  {en:<12} → {zh}")

    hr("token 预算预估（tiktoken 离线统计，非真实 API usage）")
    book_text = "\n\n".join(f"# {n}\n{t}" for n, t in chapters.items())
    book_tok = agents.count_tokens(book_text)
    print(f"  Glossary Agent   读全书           ≈ {book_tok} tok")
    per_chapter = []
    for name, text in chapters.items():
        t = agents.count_tokens(text)
        per_chapter.append(t)
        print(f"  Translation Agent 读《{name}》(独立) ≈ {t} tok")
    print(f"  Proofreading Agent 读全部译文       ≈ {sum(per_chapter)} tok（量级同全书）")

    # Manager 上下文预估：任务 + 计划 + 每章一条调用记录 + 文件索引（只有路径）
    import json as _json
    mock_manager = {
        "task": f"把一本{args.source_lang}技术小书翻译成流畅{args.target_lang}，保证术语全书一致。",
        "plan": list(agents.ORCHESTRATION_PLAN),
        "call_log": [{"agent": "Translation", "note": f"翻译 {n}",
                      "output": f"{n}_zh.md", "prompt_tokens": 0, "completion_tokens": 0}
                     for n in chapters],
        "file_index": {n: os.path.join(args.out_dir, "orchestration", f"{n}_zh.md")
                       for n in chapters},
    }
    mgr_tok = agents.count_tokens(_json.dumps(mock_manager, ensure_ascii=False))
    print(f"\n  Manager 上下文（任务/计划/调用记录/文件索引，无正文）≈ {mgr_tok} tok")
    print(f"  对照：单 Agent 累积上下文 ≥ 全书 {book_tok} tok（逐章线性增长，书越长越大）")
    print("\n  关键点：Manager 上下文只随‘章节数’加几行记录，与每章正文长度无关；")
    print("         单 Agent 把全部原文与译文都留在一条对话里，上下文随书长线性膨胀。")

    hr("术语一致性 / 遵从率将统计的术语（见 consistency.py）")
    print("  受追踪术语：" + "、".join(t["en"] for t in consistency.TRACKED_TERMS))
    print("  指定术语（遵从率）：" +
          "、".join(f'{t["en"]}→{t["mandated"]}' for t in consistency.MANDATED_TERMS))
    print("\n离线预演结束。去掉 --dry-run 并设置 OPENAI_API_KEY 即可真正运行四 Agent 协作。")


def main():
    args = parse_args()
    if args.model:
        # 必须在 import agents 之前设置：agents.py 在模块加载时读取
        # OPENAI_MODEL 环境变量来决定使用的模型。
        os.environ["OPENAI_MODEL"] = args.model

    if args.dry_run:
        # 离线路径：不需要 API Key，也不发起任何网络调用。
        run_dry_run(args)
        return

    # 延迟导入，确保上面对 OPENAI_MODEL 的覆盖能在 agents.py 读取环境变量之前生效。
    import agents
    import consistency

    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("OPENROUTER_API_KEY"):
        print("错误：未设置 OPENAI_API_KEY 或 OPENROUTER_API_KEY。请先 `export OPENAI_API_KEY=...`"
              "（或 OPENROUTER_API_KEY）或复制 env.example 为 .env 并填写（见 env.example）。\n"
              "提示：想在不联网、无 Key 的情况下查看四 Agent 协作结构，可运行 "
              "`python demo.py --dry-run`。", file=sys.stderr)
        sys.exit(1)

    chapters = load_chapters(args.sample_dir)
    if not chapters:
        print(f"错误：{args.sample_dir} 下没有找到任何 .md 章节。", file=sys.stderr)
        sys.exit(1)
    print(f"载入 {len(chapters)} 个章节：{list(chapters.keys())}  "
          f"（{args.source_lang} → {args.target_lang}）")

    # ---------------- 管理者模式 ----------------
    hr("【管理者模式】四 Agent 协作实时轨迹")
    orch = agents.run_orchestration(
        chapters, os.path.join(args.out_dir, "orchestration"),
        source_lang=args.source_lang, target_lang=args.target_lang,
        enable_glossary=not args.no_glossary,
        enable_proofreading=not args.no_proofreading,
        trace=make_tracer(),
    )
    print_agent_table(orch["tracker"], "【管理者模式】各 Agent 上下文 token 消耗")
    print(f"\nManager 上下文峰值（只存任务/计划/调用记录/文件索引）：{orch['manager_context_peak']} tokens")
    print(f"术语表（共享文件，各 Translation Agent 引用同一份）：")
    for g in orch["glossary"]:
        print(f"    {g['en']} → {g['zh']}（{g.get('pos','')}）")
    if not args.no_proofreading:
        print(f"审校报告 summary：{orch['report'].get('summary','')[:120]}")

    # ---------------- 单 Agent 模式 ----------------
    if args.skip_single:
        hr("已跳过单 Agent 对照组（--skip-single）")
        print("提示：核心对比表需要单 Agent 数据，去掉 --skip-single 可看到完整对比。")
        print(f"\n产物目录：{args.out_dir}")
        return
    single = agents.run_single_agent(
        chapters, os.path.join(args.out_dir, "single_agent"),
        source_lang=args.source_lang, target_lang=args.target_lang,
    )
    print_agent_table(single["tracker"], "【单 Agent 模式】主上下文 token 消耗")

    # ---------------- 术语一致性对比 ----------------
    hr("术语一致性对比（确定性字符串匹配，非模型打分）")
    orch_cons = consistency.analyze(orch["translations"])
    single_cons = consistency.analyze(single["translations"])
    print_consistency(orch_cons, "管理者模式")
    print_consistency(single_cons, "单 Agent 模式")

    # ---------------- 术语表遵从率对比（核心证据）----------------
    hr("术语表遵从率对比：编辑部指定术语能否贯彻全书")
    orch_adh = consistency.check_adherence(orch["translations"])
    single_adh = consistency.check_adherence(single["translations"])
    print("（管理者模式把指定术语写入共享术语表并强制下发；单 Agent 看不到术语表）\n")
    print(f"{'指定术语':<14}{'规定译法':<10}{'默认译法':<10}"
          f"{'管理者(遵从/出现)':>18}{'单Agent(遵从/出现)':>20}")
    print("-" * 78)
    o_map = {r["en"]: r for r in orch_adh["rows"]}
    s_map = {r["en"]: r for r in single_adh["rows"]}
    for r in orch_adh["rows"]:
        s = s_map.get(r["en"], {"adhered": 0, "total": 0})
        o_cell = f"{r['adhered']}/{r['total']}"
        s_cell = f"{s['adhered']}/{s['total']}"
        print(f"{r['en']:<14}{r['mandated']:<10}{r['default']:<10}"
              f"{o_cell:>18}{s_cell:>20}")
    print("-" * 78)
    print(f"术语表遵从率：管理者模式 {orch_adh['rate']*100:.0f}%  vs  "
          f"单 Agent {single_adh['rate']*100:.0f}%")

    # ---------------- 核心对比表 ----------------
    hr("核心对比表：管理者模式 vs 单 Agent 模式")
    o_tr, s_tr = orch["tracker"], single["tracker"]
    o_mgr_peak = orch["manager_context_peak"]
    # 管理者模式里，若把 Manager 当作 LLM Agent，它也有一次决策调用的上下文峰值
    o_mgr_llm_peak = o_tr.by_agent().get("Manager", {}).get("peak_context", 0)
    s_main_peak = single["main_context_peak"]

    rows = [
        ("主/Manager 上下文峰值(tokens)", o_mgr_peak, s_main_peak),
        ("Manager LLM 决策调用上下文(tokens)", o_mgr_llm_peak, "—"),
        ("全流程总 token 消耗", o_tr.total_tokens(), s_tr.total_tokens()),
        ("术语内部一致率", f"{orch_cons['rate']*100:.0f}%", f"{single_cons['rate']*100:.0f}%"),
        ("指定术语遵从率", f"{orch_adh['rate']*100:.0f}%", f"{single_adh['rate']*100:.0f}%"),
        ("参与 Agent 种类数", len(o_tr.by_agent()), 1),
    ]
    print(f"{'指标':<32}{'管理者模式':>16}{'单 Agent':>16}")
    print("-" * 72)
    for label, a, b in rows:
        print(f"{label:<32}{str(a):>16}{str(b):>16}")
    print("-" * 72)

    if isinstance(s_main_peak, int) and o_mgr_peak and s_main_peak:
        ratio = s_main_peak / o_mgr_peak
        print(f"\n结论：单 Agent 主上下文峰值是管理者模式 Manager 上下文的 "
              f"{ratio:.1f} 倍。")
        print("Manager 只保存任务/计划/调用记录/文件索引，完整译文全部落盘到文件系统，")
        print("因此无论书有多长，Manager 上下文都基本恒定 —— 这就是控制上下文膨胀的关键。")
    print(f"\n产物目录：{args.out_dir}")


if __name__ == "__main__":
    main()
