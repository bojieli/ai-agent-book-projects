"""
实验 5-4：基于论文的 PPT 自动生成（提议者-审核者机制）

完整流程：
  1. 从精简论文（paper/sample_paper.md）+ 程序化复现的图表出发；
  2. 【双 Agent】Proposer 生成 slides.md → Slidev 渲染每页 PNG → Reviewer 用 Vision LLM
     看图给出结构化建议 → Proposer 据反馈修订 → 迭代，直到 pass 或达最大轮数；
  3. 【单 Agent 自审】同一个 Agent 生成 → 渲染 → 把自己的截图塞回**同一上下文**自审并修订 → 迭代；
  4. 用同一位“独立评委”（Vision）给两种方案的最终 PPT 打分，公平比较**质量**；
  5. 打印两种方案的**上下文 token 消耗**对比（总量、峰值单次 prompt token）。

运行：python demo.py            # 完整对比（两种方案）
     python demo.py --help     # 查看全部参数
     python demo.py --mode dual --max-rounds 1   # 快速：只跑双 Agent、只出首版
     python demo.py --smoke     # 仅验证 Slidev 渲染链路，不调用任何 LLM
     python demo.py --dry-run   # 离线走通提议者-审核者循环（真实渲染 + 脚本化改稿）
依赖：Node/Slidev（渲染）、OPENAI_API_KEY（gpt-5.6-luna 视觉 + 文本；未配置时可用 OPENROUTER_API_KEY 兜底）。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys

from dotenv import load_dotenv

load_dotenv()

import agents  # noqa: E402  —— 用模块名引用 TEXT_MODEL/VISION_MODEL，便于 CLI 覆盖
from agents import (  # noqa: E402
    Proposer, Reviewer, SelfReviewAgent, TokenMeter, independent_judge,
)
from make_figures import generate_all  # noqa: E402
from paper_source import PAPER, prepare_real_paper  # noqa: E402
from renderer import render_slides  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PAPER_PATH = os.path.join(HERE, "paper", "sample_paper.md")
DEFAULT_OUT_DIR = os.path.join(HERE, "output")
OUT_DIR = DEFAULT_OUT_DIR  # 可被 --out-dir 覆盖（main 内 global 赋值）
MAX_ROUNDS = 3  # 每种方案的最大迭代轮数（首轮 + 最多 2 轮修订）


def banner(title):
    print("\n" + "=" * 74)
    print(f"  {title}")
    print("=" * 74)


def save_text(name, text):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def retain_rendered(pngs, subdir):
    """Copy rendered pixels into the immutable output tree used as evidence."""
    destination = os.path.join(OUT_DIR, "rendered", subdir)
    os.makedirs(destination, exist_ok=True)
    retained = []
    for source in pngs:
        target = os.path.join(destination, os.path.basename(source))
        shutil.copyfile(source, target)
        retained.append(target)
    return retained


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _review_issues(review: dict) -> list:
    """Return issue dicts; null/non-list → []; skip non-dict entries."""
    issues = review.get("issues")
    if issues is None:
        return []
    if not isinstance(issues, list):
        return []
    return [i for i in issues if isinstance(i, dict)]


def summarize_review(review: dict) -> str:
    n_high = sum(1 for x in _review_issues(review) if x.get("severity") == "high")
    n_med = sum(1 for x in _review_issues(review) if x.get("severity") == "medium")
    n_low = sum(1 for x in _review_issues(review) if x.get("severity") == "low")
    return (f"score={review.get('overall_score')} pass={review.get('pass')} "
            f"issues={len(_review_issues(review))} (high={n_high}, med={n_med}, low={n_low})")


# --------------------------------------------------------------------------- #
# 方案 A：提议者-审核者（双 Agent）
# --------------------------------------------------------------------------- #
def run_proposer_reviewer(paper_md, figures, max_rounds=MAX_ROUNDS):
    banner("方案 A：提议者-审核者（双 Agent 分工）")
    proposer_meter = TokenMeter("Proposer(纯文本)")
    reviewer_meter = TokenMeter("Reviewer(每轮只看最新截图)")

    proposer = Proposer(proposer_meter, paper_md, figures)
    reviewer = Reviewer(reviewer_meter)

    history = []  # 每轮的 (score, review)
    slides = proposer.propose()
    final_pngs = None

    for rnd in range(1, max_rounds + 1):
        print(f"\n[双 Agent] 第 {rnd} 轮：Proposer 产出 slides.md（{slides.count(chr(10) + '---' + chr(10)) + 1} 段分隔）")
        md_path = save_text(f"dual_round{rnd}_slides.md", slides)
        pngs = retain_rendered(
            render_slides(slides, f"dual_round{rnd}"), f"dual_round{rnd}"
        )
        final_pngs = pngs
        print(f"  渲染出 {len(pngs)} 页 PNG，例如：{pngs[0]}")

        review = reviewer.review(pngs)
        print(f"  Reviewer(Vision)审查：{summarize_review(review)}")
        # 打印真实的建议 JSON（前几条）
        print("  Reviewer 结构化建议 JSON：")
        print(_indent(json.dumps(review, ensure_ascii=False, indent=2), 4))
        save_text(f"dual_round{rnd}_review.json",
                  json.dumps(review, ensure_ascii=False, indent=2))
        history.append((review.get("overall_score", 0), review))

        blocking = [i for i in _review_issues(review)
                    if i.get("severity") in ("high", "medium")]
        if review.get("pass") and not blocking:
            print("  ✓ Reviewer 判定达标（无 high/medium 问题），提前结束迭代。")
            break
        if rnd == max_rounds:
            break

        print("  → Proposer 接收结构化文字反馈并修订（上下文只增文本，不含图片）")
        slides = proposer.revise(review)

    return {
        "slides": slides,
        "final_pngs": final_pngs,
        "history": history,
        "proposer_meter": proposer_meter,
        "reviewer_meter": reviewer_meter,
    }


# --------------------------------------------------------------------------- #
# 方案 B：单 Agent 自审
# --------------------------------------------------------------------------- #
def run_single_agent(paper_md, figures, max_rounds=MAX_ROUNDS):
    banner("方案 B：单 Agent 自我审查（图片累积在同一上下文）")
    meter = TokenMeter("SingleAgent(自审, 图片累积)")
    agent = SelfReviewAgent(meter, paper_md, figures)

    slides = agent.propose()
    final_pngs = None

    for rnd in range(1, max_rounds + 1):
        print(f"\n[单 Agent] 第 {rnd} 轮：生成/修订 slides.md")
        save_text(f"single_round{rnd}_slides.md", slides)
        pngs = retain_rendered(
            render_slides(slides, f"single_round{rnd}"), f"single_round{rnd}"
        )
        final_pngs = pngs
        print(f"  渲染出 {len(pngs)} 页 PNG")
        print(f"  当前上下文峰值 prompt token = {meter.peak_prompt_tokens}")

        if rnd == max_rounds:
            break
        print("  → 把 %d 张截图塞回同一上下文，Agent 自审并修订（历史图片不清除）" % len(pngs))
        slides = agent.self_review_and_revise(pngs)

    return {"slides": slides, "final_pngs": final_pngs, "meter": meter}


def _indent(text, n):
    pad = " " * n
    return "\n".join(pad + line for line in text.splitlines())


def smoke_test():
    """快速冒烟：只验证 Slidev 渲染链路是否可用，不调用任何 LLM，无需 API Key。"""
    from renderer import render_slides
    banner("Smoke test：仅验证 Slidev 渲染链路（不调用 LLM）")
    demo_md = (
        "---\ntheme: default\n---\n\n"
        "# Smoke Test\n\n渲染链路自检\n\n---\n\n"
        "# 第二页\n\n- Slidev + playwright-chromium 正常\n"
    )
    pngs = render_slides(demo_md, "smoke")
    print(f"✓ 渲染成功，产出 {len(pngs)} 页 PNG：")
    for p in pngs:
        print("  ", p)
    print("Slidev 渲染链路可用。")


# --------------------------------------------------------------------------- #
# 离线 dry-run：不调用任何 LLM，走通提议者-审核者循环的**结构**。
#   - Proposer 的两版稿件是脚本化的（拥挤初稿 → 拆页修订稿），而非 LLM 生成；
#   - 渲染是**真实**的（真的调 Slidev 导出 PNG）；
#   - Reviewer 用**确定性启发式规则**（按每页文字量判定 overcrowded），
#     明确不是 Vision LLM——仅用于离线演示“生成→渲染→审查→修订”的闭环。
# 真实的 Vision 审查请用 `python demo.py`（需 OPENAI_API_KEY）。
# --------------------------------------------------------------------------- #
def _split_paragraphs(paper_md: str) -> list[str]:
    """按空行切出正文段落，剔除标题行与表格/图片，供脚本化排版使用。"""
    paras = []
    for block in re.split(r"\n\s*\n", paper_md):
        block = block.strip()
        if not block or block.startswith("#") or block.startswith("|"):
            continue
        paras.append(re.sub(r"\s+", " ", block))
    return paras


def _paper_title(paper_md: str) -> str:
    m = re.search(r"^#\s+(.+)$", paper_md, re.MULTILINE)
    return m.group(1).strip() if m else "论文演示"


def _dry_first_draft(paper_md: str, figures: dict) -> str:
    """脚本化“拥挤初稿”：把整篇论文压进约 4 页，每页塞多段原文（必然溢出）。"""
    title = _paper_title(paper_md)
    paras = _split_paragraphs(paper_md) or ["（论文正文为空）"]
    fig_names = list(figures.keys())
    # 把段落尽量塞进 3 张内容页
    groups, per = [], max(1, (len(paras) + 2) // 3)
    for i in range(0, len(paras), per):
        groups.append(paras[i:i + per])
    pages = [f"---\ntheme: default\n---\n\n# {title}\n\n自动生成演示（离线 dry-run 初稿）"]
    for gi, g in enumerate(groups[:3]):
        body = "\n\n".join(g)
        img = f"\n\n![]({fig_names[gi]})" if gi < len(fig_names) else ""
        pages.append(f"# 第 {gi + 1} 部分\n\n{body}{img}")
    return "\n\n---\n\n".join(pages) + "\n"


def _dry_revised(paper_md: str, figures: dict) -> str:
    """脚本化“修订稿”：一段一页、要点化，图表单独成页——明显更宽松，可通过启发式。"""
    title = _paper_title(paper_md)
    paras = _split_paragraphs(paper_md) or ["（论文正文为空）"]
    fig_names = list(figures.keys())
    pages = [f"---\ntheme: default\n---\n\n# {title}\n\n自动生成演示（离线 dry-run 修订稿）"]
    for i, para in enumerate(paras):
        # 每页只放一段，且截断到约 220 字，模拟“精简成要点”
        text = para if len(para) <= 220 else para[:210].rstrip() + "……"
        pages.append(f"# 要点 {i + 1}\n\n{text}")
    for name in fig_names:  # 图表各自单独成页，尺寸受控
        pages.append(f"# 图表\n\n<img src=\"{name}\" class=\"h-80 mx-auto\" />")
    return "\n\n---\n\n".join(pages) + "\n"


def _heuristic_review(slides_md: str) -> dict:
    """确定性启发式（非 Vision LLM）：按每页正文字符数判定 overcrowded。"""
    parts = re.split(r"(?m)^---\s*$", slides_md)
    pages, page_no = [], 0
    for part in parts:
        s = part.strip()
        if not s or s.startswith("theme:") or "theme:" in s.split("\n")[0]:
            continue
        pages.append(s)
    issues = []
    for idx, page in enumerate(pages, 1):
        text = re.sub(r"!\[.*?\]\(.*?\)|<img[^>]*>", "", page)  # 不计图片
        n = len(re.sub(r"\s+", "", text))
        if n > 500:
            issues.append({"page": idx, "issue_type": "overcrowded", "severity": "high",
                           "suggestion": f"该页正文约 {n} 字，严重溢出，建议拆成多页并精简为要点。"})
        elif n > 300:
            issues.append({"page": idx, "issue_type": "overcrowded", "severity": "medium",
                           "suggestion": f"该页正文约 {n} 字，偏挤，建议拆页或删减。"})
    blocking = [i for i in issues if i["severity"] in ("high", "medium")]
    score = max(0, 100 - 15 * len(blocking) - 3 * (len(issues) - len(blocking)))
    return {"overall_score": score, "pass": not blocking, "issues": issues,
            "_reviewer": "heuristic (offline, NOT a Vision LLM)"}


def dry_run(paper_path: str):
    """离线走通提议者-审核者循环：真实渲染 + 脚本化改稿 + 启发式审查。"""
    banner("Dry-run：离线演示提议者-审核者循环（真实渲染，脚本化改稿，启发式审查）")
    if not os.path.exists(paper_path):
        print(f"找不到论文文件：{paper_path}")
        sys.exit(1)
    with open(paper_path, encoding="utf-8") as f:
        paper_md = f.read()
    figures = generate_all()
    print(f"论文：{paper_path}（{len(paper_md)} 字符）；已复现图表：{', '.join(figures)}")
    print("注意：本模式不调用任何 LLM。Reviewer 由确定性启发式规则扮演（非 Vision LLM），")
    print("      仅用于离线展示“生成→渲染→审查→修订”的闭环；真实 Vision 审查请用 `python demo.py`。")

    stages = [
        ("拥挤初稿", _dry_first_draft(paper_md, figures)),
        ("拆页修订稿", _dry_revised(paper_md, figures)),
    ]
    last_review = None
    for rnd, (label, slides) in enumerate(stages, 1):
        n_pages = slides.count("\n---\n")  # 页分隔符数量≈页数
        print(f"\n[dry-run] 第 {rnd} 轮：Proposer 产出 slides.md（{label}，约 {n_pages} 页）")
        save_text(f"dryrun_round{rnd}_slides.md", slides)
        pngs = render_slides(slides, f"dryrun_round{rnd}")
        print(f"  渲染出 {len(pngs)} 页 PNG，例如：{pngs[0]}")
        review = _heuristic_review(slides)
        print(f"  Reviewer(启发式)审查：{summarize_review(review)}")
        print("  Reviewer 结构化建议 JSON：")
        print(_indent(json.dumps(review, ensure_ascii=False, indent=2), 4))
        save_text(f"dryrun_round{rnd}_review.json",
                  json.dumps(review, ensure_ascii=False, indent=2))
        last_review = review
        if review["pass"]:
            print("  ✓ Reviewer 判定达标（无 high/medium 问题），闭环结束。")
            break
        if rnd < len(stages):
            print("  → Proposer 接收结构化文字反馈并修订（拆页、精简；此处为脚本化改稿）")

    banner("Dry-run 小结")
    print(f"闭环演示完成：初稿被判定拥挤 → 修订稿 pass={last_review['pass']}"
          f"（启发式打分 {last_review['overall_score']}）。")
    print(f"真实渲染 PNG：slidev_workspace/exports/dryrun_round*/")
    print(f"脚本化 slides.md 与审查 JSON：{OUT_DIR}/dryrun_round*")
    print("真实的 Vision 审查循环（gpt-5.6-luna 看像素）请运行：python demo.py --mode dual --max-rounds 3")


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="demo.py",
        description="实验 5-4：论文 → PPT 自动生成（提议者-审核者 vs 单 Agent 自审对照）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python demo.py                          # 完整对比：两种方案 + 独立评委 + token 对比\n"
            "  python demo.py --mode dual              # 只跑双 Agent（省一半时间/费用）\n"
            "  python demo.py --max-rounds 1           # 每种方案只出首版（最快的真实 LLM 冒烟）\n"
            "  python demo.py --paper my.md --out-dir run1   # 换论文、换输出目录\n"
            "  python demo.py --vision-model gpt-5.6-luna      # 覆盖视觉模型\n"
            "  python demo.py --dry-run                # 离线走通提议者-审核者循环，不调用任何 LLM\n"
            "  python demo.py --smoke                  # 仅验证 Slidev 渲染，不调用任何 LLM\n\n"
            "模型/供应商也可通过环境变量配置（见 env.example）；命令行 --text-model /\n"
            "--vision-model 优先级更高：OPENAI_API_KEY / OPENAI_BASE_URL / TEXT_MODEL / VISION_MODEL"
        ),
    )
    p.add_argument("--paper", metavar="PATH", default=None,
                   help="非正式兼容入口：使用本地 Markdown。省略时使用固定哈希的真实 arXiv PDF；"
                        "本地 Markdown 运行永远不会通过正式实验门禁。")
    p.add_argument("--out-dir", metavar="DIR", default=DEFAULT_OUT_DIR,
                   help="产物输出目录：各轮 slides.md / review.json / comparison_summary.json "
                        "（默认 output/）。渲染 PNG 始终位于 slidev_workspace/exports/。")
    p.add_argument("--text-model", metavar="NAME", default=None,
                   help="Proposer / 单 Agent 文本部分用的模型，覆盖 TEXT_MODEL 环境变量"
                        f"（默认 {agents.TEXT_MODEL}）。")
    p.add_argument("--vision-model", metavar="NAME", default=None,
                   help="Reviewer / 独立评委看图用的模型，必须支持图像输入，覆盖 VISION_MODEL "
                        f"环境变量（默认 {agents.VISION_MODEL}）。")
    p.add_argument(
        "--provider", choices=["auto", "openai", "openrouter", "moonshot", "ark"],
        default="auto", help="文本与 Vision 调用的真实 API 提供商",
    )
    p.add_argument("--mode", choices=["both", "dual", "single"], default="both",
                   help="运行哪种方案：both=两种都跑并对比（默认）；dual=仅提议者-审核者；"
                        "single=仅单 Agent 自审。只跑一种可显著省时省钱。")
    p.add_argument("--max-rounds", type=int, default=MAX_ROUNDS, metavar="N",
                   help=f"每种方案的最大迭代轮数（默认 {MAX_ROUNDS}）。设为 1 即只出首版、"
                        "不修订，是最快的真实运行冒烟。")
    p.add_argument("--dry-run", action="store_true",
                   help="离线演示提议者-审核者循环：真实渲染两版脚本化 slides.md（拥挤初稿→"
                        "拆页修订稿），用启发式规则（非 Vision LLM）扮演 Reviewer，展示"
                        "生成→渲染→审查→修订的闭环结构。不调用任何 LLM，无需 API Key。")
    p.add_argument("--smoke", action="store_true",
                   help="仅验证 Slidev 渲染链路（渲染一个两页 deck），不调用任何 LLM，无需 API Key。")
    return p.parse_args(argv)


def _save_partial_summary(dual, dual_final, single, single_final, source_info, args, judge_meter):
    """单方案运行（--mode dual/single）时，落盘该方案自身的质量与 token 结果。"""
    summary = {
        "experiment": "5-4",
        "official_complete": False,
        "completion": {"campaign_complete": False, "reason": "both comparison arms are required"},
        "provider": args.provider,
        "models": {"text": agents.TEXT_MODEL, "vision": agents.VISION_MODEL},
        "source": source_info,
        "independent_judge": judge_meter.__dict__,
    }
    if dual:
        pm, rm = dual["proposer_meter"], dual["reviewer_meter"]
        summary["dual_agent"] = {
            "iteration_scores": [h[0] for h in dual["history"]],
            "final_quality": dual_final,
            "total_tokens": pm.total_tokens + rm.total_tokens,
            "peak_context_prompt_tokens": max(pm.peak_prompt_tokens, rm.peak_prompt_tokens),
            "proposer_receipts": pm.receipts,
            "reviewer_receipts": rm.receipts,
        }
    if single:
        sm = single["meter"]
        summary["single_agent"] = {
            "final_quality": single_final,
            "total_tokens": sm.total_tokens,
            "peak_context_prompt_tokens": sm.peak_prompt_tokens,
            "receipts": sm.receipts,
        }
    p = save_text("comparison_summary.json", json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n结果已保存：{p}")
    print(f"所有 slides.md / review.json / 渲染 PNG 位于：{OUT_DIR}/ 与 slidev_workspace/exports/")


def main(argv=None):
    global OUT_DIR
    args = parse_args(argv)

    # 输出目录（--out-dir）：所有 save_text 都写到这里
    OUT_DIR = os.path.abspath(args.out_dir)
    os.makedirs(OUT_DIR, exist_ok=True)
    os.environ["PPT_RECEIPT_CHECKPOINT"] = os.path.join(
        OUT_DIR, "receipts.checkpoint.json"
    )
    # 模型覆盖（--text-model / --vision-model 优先于环境变量）
    if args.text_model:
        agents.TEXT_MODEL = args.text_model
    if args.vision_model:
        agents.VISION_MODEL = args.vision_model
    agents.configure_provider(args.provider)

    if args.smoke:
        smoke_test()
        return
    if args.dry_run:
        dry_run(args.paper or DEFAULT_PAPER_PATH)
        return
    if args.max_rounds < 1:
        print("--max-rounds 至少为 1")
        sys.exit(1)
    if args.paper and not os.path.exists(args.paper):
        print(f"找不到论文文件：{args.paper}（用 --paper 指定，或参考默认 paper/sample_paper.md）")
        sys.exit(1)
    provider_keys = {
        "ark": "ARK_API_KEY", "moonshot": "MOONSHOT_API_KEY",
        "openrouter": "OPENROUTER_API_KEY", "openai": "OPENAI_API_KEY",
    }
    required_key = provider_keys.get(args.provider)
    if required_key and not os.environ.get(required_key):
        print(f"请先设置 {required_key}（可参考 env.example）")
        sys.exit(1)
    if args.provider == "auto" and not any(os.environ.get(key) for key in (
        "OPENAI_API_KEY", "OPENROUTER_API_KEY"
    )):
        print("auto provider 需要 OPENAI_API_KEY 或 OPENROUTER_API_KEY")
        sys.exit(1)

    banner("准备：固定真实论文 PDF + 原论文图")
    if args.paper:
        with open(args.paper, encoding="utf-8") as f:
            paper_md = f.read()
        figures = generate_all()
        source_info = {
            "canonical": False,
            "reason": "legacy local Markdown and programmatic figures",
            "paper_path": os.path.abspath(args.paper),
        }
    else:
        prepared = prepare_real_paper(
            OUT_DIR, os.path.join(HERE, "slidev_workspace", "public")
        )
        paper_md = prepared["paper_text"]
        figures = prepared["figures"]
        source_info = {
            "canonical": True,
            "paper": prepared["manifest"]["paper"],
            "paper_text": prepared["manifest"]["paper_text"],
            "visuals": prepared["manifest"]["visuals"],
            "manifest_path": prepared["manifest_path"],
            "pdf_path": prepared["pdf_path"],
        }
    print(f"论文：{PAPER['title']}（提取文本 {len(paper_md)} 字符）")
    print(f"输出目录：{OUT_DIR}")
    print(f"文本模型：{agents.TEXT_MODEL}   视觉模型：{agents.VISION_MODEL}")
    print(f"运行模式：{args.mode}   最大轮数：{args.max_rounds}")
    print("已生成图表：")
    for k, v in figures.items():
        print(f"  {k} -> {v}")

    # 方案 A / 方案 B（--mode 控制跑哪一种；只有 both 才能做跨方案对比）
    dual = run_proposer_reviewer(paper_md, figures, args.max_rounds) \
        if args.mode in ("both", "dual") else None
    single = run_single_agent(paper_md, figures, args.max_rounds) \
        if args.mode in ("both", "single") else None

    # ------- 用同一位独立评委给两种方案的最终 PPT 打分（质量对比，尽量公平） -------
    banner("独立评委：对最终 PPT 打分（同一 Vision rubric）")
    judge_meter = TokenMeter("独立评委(不计入两方案成本)")
    dual_final = independent_judge(dual["final_pngs"], judge_meter) if dual else None
    single_final = independent_judge(single["final_pngs"], judge_meter) if single else None
    if dual_final:
        print(f"方案 A（双 Agent）最终质量：{summarize_review(dual_final)}")
    if single_final:
        print(f"方案 B（单 Agent）最终质量：{summarize_review(single_final)}")

    if not (dual and single):
        # 单方案运行：跳过跨方案的 token 对比，仅落盘已有结果
        _save_partial_summary(
            dual, dual_final, single, single_final, source_info, args, judge_meter
        )
        return

    # ------- 迭代改善情况（双 Agent） -------
    banner("迭代质量改善（方案 A：提议者-审核者）")
    scores = [h[0] for h in dual["history"]]
    if len(scores) >= 2:
        print(f"Reviewer 打分随迭代变化：{scores}  "
              f"（{'↑ 改善' if scores[-1] >= scores[0] else '↓'} {scores[-1] - scores[0]:+d}）")
    else:
        print(f"仅 1 轮即达标，Reviewer 打分：{scores}")

    # ------- 上下文 token 消耗对比 -------
    banner("上下文 Token 消耗对比：单 Agent 自审 vs 提议者-审核者")
    pm, rm, sm = dual["proposer_meter"], dual["reviewer_meter"], single["meter"]
    dual_total = pm.total_tokens + rm.total_tokens
    dual_peak = max(pm.peak_prompt_tokens, rm.peak_prompt_tokens)

    def row(label, calls, prompt, completion, total, peak):
        print(f"  {label:<34} calls={calls:<3} prompt={prompt:<8} "
              f"completion={completion:<7} total={total:<8} peak_ctx={peak}")

    print("双 Agent（方案 A）拆分：")
    row(pm.name, pm.calls, pm.prompt_tokens, pm.completion_tokens, pm.total_tokens, pm.peak_prompt_tokens)
    row(rm.name, rm.calls, rm.prompt_tokens, rm.completion_tokens, rm.total_tokens, rm.peak_prompt_tokens)
    print("-" * 74)
    row("【方案 A 合计】", pm.calls + rm.calls, pm.prompt_tokens + rm.prompt_tokens,
        pm.completion_tokens + rm.completion_tokens, dual_total, dual_peak)
    row("【方案 B 单Agent自审】", sm.calls, sm.prompt_tokens, sm.completion_tokens,
        sm.total_tokens, sm.peak_prompt_tokens)
    print("-" * 74)
    print(f"每次调用的 prompt token 序列：")
    print(f"  方案A Proposer : {pm.per_call_prompt}")
    print(f"  方案A Reviewer : {rm.per_call_prompt}   ← 每轮独立、只看最新截图，不随迭代累积")
    print(f"  方案B 单Agent  : {sm.per_call_prompt}   ← 图片累积在同一上下文，峰值随迭代上升")
    print()
    print(f"关键结论：")
    print(f"  · 上下文峰值（单次 prompt token，决定是否撑爆上下文窗口）：")
    print(f"      方案 A = {dual_peak}   方案 B = {sm.peak_prompt_tokens}   "
          f"（B/A = {sm.peak_prompt_tokens / max(dual_peak,1):.2f}x）")
    print(f"  · Proposer 全程不看图片，其峰值仅 {pm.peak_prompt_tokens} token（纯文本反馈）。")
    print(f"  · 方案 B 因图片在同一上下文累积，峰值最高；页数越多、迭代越多，差距越大。")

    # 汇总落盘
    visual_names = [visual["filename"] for visual in source_info.get("visuals", [])]
    receipts = pm.receipts + rm.receipts + sm.receipts + judge_meter.receipts
    receipts_path = save_text(
        "receipts.json", json.dumps(receipts, ensure_ascii=False, indent=2)
    )
    gates = {
        "pinned_real_academic_pdf": bool(
            source_info.get("canonical")
            and source_info.get("paper", {}).get("observed_pdf_sha256") == PAPER["pdf_sha256"]
        ),
        "three_original_pdf_visuals": bool(
            len(visual_names) >= 3
            and all(v["sha256"] == v["public_copy_sha256"] for v in source_info.get("visuals", []))
        ),
        "both_final_decks_reference_every_source_visual": bool(
            visual_names
            and all(name in dual["slides"] and name in single["slides"] for name in visual_names)
        ),
        "both_final_decks_have_10_to_20_rendered_pages": bool(
            10 <= len(dual["final_pngs"]) <= 20
            and 10 <= len(single["final_pngs"]) <= 20
        ),
        "real_slidev_rendered_every_final_page": bool(
            all(os.path.exists(path) and os.path.getsize(path) > 0
                for path in dual["final_pngs"] + single["final_pngs"])
        ),
        "proposer_reviewer_and_self_review_both_run": bool(
            dual["history"] and sm.calls >= 2
        ),
        "same_independent_vision_judge_scored_both": bool(
            dual_final and single_final and judge_meter.calls == 2
        ),
        # The manuscript acceptance criterion is about the rendered result,
        # not merely about having exercised the review mechanism.  A run with
        # 10--20 pages and real Vision receipts is still incomplete when the
        # independent pixel-level judge reports blocking layout/overflow
        # defects in the proposer--reviewer deck.
        "dual_final_deck_passes_visual_acceptance": bool(
            dual_final and dual_final.get("pass") is True
        ),
        "real_api_receipts_complete": bool(
            receipts
            and all(r.get("response", {}).get("id")
                    and r.get("usage", {}).get("total_tokens")
                    and r.get("latency_s") is not None
                    for r in receipts)
        ),
    }
    summary = {
        "schema_version": "2.0",
        "experiment": "5-4",
        "provider": args.provider,
        "source": source_info,
        "models": {"text": agents.TEXT_MODEL, "vision": agents.VISION_MODEL},
        "dual_agent": {
            "iteration_scores": scores,
            "final_quality": dual_final,
            "proposer_tokens": pm.__dict__,
            "reviewer_tokens": rm.__dict__,
            "total_tokens": dual_total,
            "peak_context_prompt_tokens": dual_peak,
        },
        "single_agent": {
            "final_quality": single_final,
            "tokens": sm.__dict__,
            "total_tokens": sm.total_tokens,
            "peak_context_prompt_tokens": sm.peak_prompt_tokens,
        },
        "independent_judge": judge_meter.__dict__,
        "artifact_hashes": {
            "dual_final_pngs": {os.path.basename(p): file_sha256(p) for p in dual["final_pngs"]},
            "single_final_pngs": {os.path.basename(p): file_sha256(p) for p in single["final_pngs"]},
            "raw_receipts": file_sha256(receipts_path),
        },
        "completion": {"gates": gates, "campaign_complete": all(gates.values())},
        "official_complete": all(gates.values()),
        "observed_hypothesis": {
            "dual_quality_minus_single": (
                dual_final.get("overall_score", 0) - single_final.get("overall_score", 0)
            ),
            "dual_peak_context": dual_peak,
            "single_peak_context": sm.peak_prompt_tokens,
            "note": "Hypothesis outcome is reported separately from execution completion.",
        },
    }
    p = save_text("comparison_summary.json", json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n完整对比已保存：{p}")
    print(f"所有 slides.md / review.json / 渲染 PNG 位于：{OUT_DIR}/ 与 slidev_workspace/exports/")


if __name__ == "__main__":
    main()
