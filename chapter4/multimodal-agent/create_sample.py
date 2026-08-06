"""
离线样例生成器 (Offline sample generator)

生成一个"含图表的报告"作为多模态样例，用于实验 4-2 对比三种提取范式。
产物同时包含：
  - test_files/sample_chart.png   仅图表（图像模态）
  - test_files/sample_report.pdf  图表 + 文字说明（文档模态，书中的"含图表的 PDF 报告"）

关键设计：图表里的精确数值（如各季度营收）只出现在柱状图上，正文并未逐一写出。
这样在实验中：
  - 原生多模态模式可以直接"看懂"柱子读出数值；
  - 提取为文本模式若用通用描述器转写图像，往往丢失精确数值与空间关系；
从而让三种范式的取舍可被直接测量，而不是靠猜。

本脚本完全离线，不需要任何 API Key。
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # 无界面后端，纯离线出图
import matplotlib.pyplot as plt


# 图表数据：只在柱状图上标注，正文不重复这些精确数字
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]
REVENUE = [120, 150, 95, 180]  # 单位：百万美元 ($M)


def create_chart(output_path: Path) -> Path:
    """用 matplotlib 生成一张柱状图（图像模态样例）。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
    bars = ax.bar(QUARTERS, REVENUE, color=["#4C72B0", "#55A868", "#C44E52", "#8172B3"])

    # 把精确数值标注在柱子顶端——这些信息只存在于图像里
    for bar, value in zip(bars, REVENUE):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 3,
            f"${value}M",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_title("Acme Corp Quarterly Revenue 2024", fontsize=13, fontweight="bold")
    ax.set_ylabel("Revenue (in $M)")
    ax.set_ylim(0, 210)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()

    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def create_report_pdf(chart_path: Path, output_path: Path) -> Path:
    """把图表和一段文字说明组合成一份 PDF 报告（文档模态样例）。"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Image as RLImage,
        )
    except ImportError:
        print("提示：未安装 reportlab，跳过 PDF 生成（pip install reportlab）。")
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()

    # 正文刻意只给出定性描述，不逐一写出各季度精确数值——数值只在图里
    body_text = (
        "This internal report summarizes Acme Corp's revenue performance in 2024. "
        "Overall the year showed healthy growth, with a mid-year dip followed by a "
        "strong recovery in the final quarter. The chart below breaks down revenue "
        "by quarter; management attributes the fourth-quarter surge to the launch of "
        "the new enterprise product line."
    )

    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    story = [
        Paragraph("Acme Corp 2024 Revenue Report", styles["Title"]),
        Spacer(1, 0.4 * cm),
        Paragraph(body_text, styles["BodyText"]),
        Spacer(1, 0.6 * cm),
        RLImage(str(chart_path), width=14 * cm, height=9.3 * cm),
    ]
    doc.build(story)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="离线生成含图表的多模态样例（图像 + PDF 报告），供实验 4-2 使用。无需 API Key。"
    )
    parser.add_argument(
        "--output-dir",
        default="test_files",
        help="样例输出目录（默认：test_files）",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="只生成 PNG 图表，不生成 PDF 报告",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    chart_path = create_chart(out_dir / "sample_chart.png")
    print(f"已生成图表: {chart_path}")

    if not args.no_pdf:
        pdf_path = create_report_pdf(chart_path, out_dir / "sample_report.pdf")
        if pdf_path:
            print(f"已生成报告: {pdf_path}")

    print(
        "\n提示：图表上的精确季度营收只存在于图像中，正文并未逐一写出。\n"
        "可用如下问题对比三种范式（原生 / 提取为文本 / 带工具）：\n"
        '  "Which quarter had the highest revenue, and what was the exact value?"'
    )


if __name__ == "__main__":
    main()
