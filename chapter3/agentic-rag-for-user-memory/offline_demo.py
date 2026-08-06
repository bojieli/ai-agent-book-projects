#!/usr/bin/env python3
"""实验 3-9 离线演示：智能体化记忆检索 vs. 朴素单次检索

本脚本完全离线运行（不需要 port 4242 检索服务，也不需要任何 LLM API Key），
用来直观展示书中实验 3-9 的核心论点：

  把用户的跨会话对话历史当作知识库、赋予 Agent「多轮迭代检索」能力后，
  它能主动发现单次检索会遗漏的关键信息，从而在「第二层次·多会话检索」
  任务上显著超过朴素的一次性检索（naive recall）。

演示载体是评估集里的 layer2_01_multiple_vehicles 用例：用户在两通不同电话里
分别聊到本田 Accord（已在 Firestone 预约周五保养）和特斯拉 Model 3（未预约）。
当用户问「我要给我的车约个保养，我都约了哪些服务？」时，正确回答必须同时覆盖
两辆车的服务状态——这正是「消歧」所要求的。

检索质量用「决定性证据召回率」度量：一次正确回答依赖若干条决定性事实
（如本田预约确认号 FS-447291、特斯拉作为第二辆车存在），我们统计每种策略
检索到的文本块是否覆盖了这些事实。所有数字都由真实的 BM25 检索计算得出，
不含任何人为编造。
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import Config
from chunker import ConversationChunker
from indexer import MemoryIndexer

console = Console()

# 默认用例及其决定性证据标记（每个标记代表回答必须覆盖的一条事实）。
# 标记只是「用哪个关键词定位承载该事实的文本块」，召回率由真实检索计算。
DEFAULT_TEST_ID = "layer2_01_multiple_vehicles"
DEFAULT_GOLD_MARKERS = {
    "本田已确认预约(FS-447291)": "FS-447291",
    "特斯拉Model 3作为第二辆车存在": "Model 3",
}

# 从检索结果里抽取「车辆实体」用的通用规则：年份+品牌+车型，或品牌+车型。
_ENTITY_PATTERN = re.compile(
    r"\b((?:19|20)\d{2}\s+)?"
    r"(Honda|Toyota|Tesla|Ford|BMW|Audi|Chevrolet|Nissan|Mazda|Subaru|Lexus|Kia|Hyundai)"
    r"(?:\s+[A-Z][a-zA-Z0-9]+){0,2}"
)


def _load_test_case(test_cases_dir: Path, test_id: str) -> Optional[dict]:
    """在 test_cases_dir 下按 test_id 查找并加载 YAML 用例。"""
    for yaml_file in test_cases_dir.rglob("*.yaml"):
        try:
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data and data.get("test_id") == test_id:
            return data
    return None


def _extract_vehicle_entities(texts: List[str], limit: int = 4) -> List[str]:
    """从一批文本里通用地抽取车辆实体短语（不依赖具体用例）。"""
    seen: Dict[str, int] = {}
    for text in texts:
        for match in _ENTITY_PATTERN.finditer(text):
            phrase = re.sub(r"\s+", " ", match.group(0)).strip()
            # 去掉前导年份，聚焦「品牌 车型」，让二次查询更聚焦。
            phrase = re.sub(r"^(?:19|20)\d{2}\s+", "", phrase)
            seen[phrase] = seen.get(phrase, 0) + 1
    # 按出现频次排序，取前 limit 个作为待追查的实体。
    ranked = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)
    return [phrase for phrase, _ in ranked[:limit]]


def _covered_markers(retrieved_texts: List[str], gold_markers: Dict[str, str]) -> Dict[str, bool]:
    """判断每条决定性事实是否被检索到的文本覆盖。"""
    joined = "\n".join(retrieved_texts)
    return {name: (marker in joined) for name, marker in gold_markers.items()}


def naive_retrieval(indexer: MemoryIndexer, question: str, top_k: int) -> List:
    """基线：只用原始问题做一次检索。"""
    return indexer.search(question, top_k=top_k)


def agentic_retrieval(indexer: MemoryIndexer, question: str, top_k: int,
                      max_followups: int, verbose: bool = True) -> Dict:
    """智能体化多轮检索（离线确定性模拟）。

    模拟 Agent 的 ReAct 检索循环，但用规则代替 LLM，从而完全离线：
      1. 用原始问题做首轮检索；
      2. 从首轮结果里发现「还提到了哪些车辆实体」（关键线索）；
      3. 针对每个发现的实体追加一次聚焦查询「<实体> service appointment scheduled」；
      4. 合并所有轮次的结果作为最终检索集合。
    """
    trace: List[Dict] = []

    round1 = indexer.search(question, top_k=top_k)
    retrieved = {r.chunk_id: r for r in round1}
    trace.append({"query": question, "hits": [r.chunk_id for r in round1]})
    if verbose:
        console.print(f"[cyan]  [第1轮] 查询:[/cyan] {question}")
        console.print(f"          命中 {len(round1)} 块: "
                      + ", ".join(f"{r.chunk.conversation_id}#{r.chunk.start_round}-{r.chunk.end_round}"
                                  for r in round1))

    # 从首轮结果里发现车辆实体（关键线索）
    entities = _extract_vehicle_entities([r.chunk.to_text() for r in round1])
    if verbose:
        console.print(f"[cyan]  [评估] 从首轮结果中发现车辆实体:[/cyan] {entities or '（无）'}")

    for entity in entities[:max_followups]:
        followup_query = f"{entity} service appointment scheduled"
        hits = indexer.search(followup_query, top_k=top_k)
        for r in hits:
            retrieved.setdefault(r.chunk_id, r)
        trace.append({"query": followup_query, "hits": [r.chunk_id for r in hits]})
        if verbose:
            console.print(f"[cyan]  [追查] 查询:[/cyan] {followup_query}")
            console.print(f"          命中 {len(hits)} 块: "
                          + ", ".join(f"{r.chunk.conversation_id}#{r.chunk.start_round}-{r.chunk.end_round}"
                                      for r in hits))

    return {"results": list(retrieved.values()), "trace": trace}


def run_demo(args) -> Dict:
    # 强制离线本地 BM25 后端
    config = Config.from_env()
    config.index.retrieval_backend = "local"
    config.chunking.rounds_per_chunk = args.rounds_per_chunk

    test_cases_dir = Path(args.test_cases_dir)
    if not test_cases_dir.is_absolute():
        test_cases_dir = (Path(__file__).parent / test_cases_dir).resolve()

    console.print(Panel.fit(
        "[bold cyan]实验 3-9 离线演示[/bold cyan]\n"
        "智能体化记忆检索 vs. 朴素单次检索（本地 BM25，无需 API / port 4242）",
        border_style="cyan"))

    data = _load_test_case(test_cases_dir, args.test_id)
    if not data:
        console.print(f"[red]找不到用例 {args.test_id}，检索目录: {test_cases_dir}[/red]")
        sys.exit(1)

    question = args.query or data.get("user_question", "")
    gold_markers = DEFAULT_GOLD_MARKERS if args.test_id == DEFAULT_TEST_ID else {}
    if args.gold_marker:
        gold_markers = {m: m for m in args.gold_marker}

    # 分块 + 建索引（离线）
    chunker = ConversationChunker(config.chunking)
    chunks = chunker.chunk_test_case_conversations(data)
    indexer = MemoryIndexer(config.index)
    indexer.add_chunks(chunks)

    # 多会话概览
    sessions = {}
    for c in chunks:
        sessions.setdefault(c.conversation_id, []).append(c)
    console.print(f"\n[bold]用例:[/bold] {data.get('title', args.test_id)}")
    console.print(f"[bold]用户问题:[/bold] {question}")
    console.print(f"[bold]跨会话记忆:[/bold] 共 {len(sessions)} 个历史会话，"
                  f"切分为 {len(chunks)} 个记忆块（每块 {args.rounds_per_chunk} 轮）")
    for conv_id, cs in sessions.items():
        meta = cs[0].metadata
        console.print(f"  • 会话 [magenta]{conv_id}[/magenta]（{meta.get('business', '?')} / "
                      f"{meta.get('department', '?')}）：{len(cs)} 块")

    # 两种策略
    console.print("\n[bold yellow]策略 A · 朴素单次检索（baseline）[/bold yellow]")
    naive_results = naive_retrieval(indexer, question, args.top_k)
    console.print(f"  单次查询命中 {len(naive_results)} 块: "
                  + ", ".join(f"{r.chunk.conversation_id}#{r.chunk.start_round}-{r.chunk.end_round}"
                              for r in naive_results))

    console.print("\n[bold green]策略 B · 智能体化多轮检索（memory-RAG）[/bold green]")
    agentic = agentic_retrieval(indexer, question, args.top_k, args.max_followups)
    agentic_results = agentic["results"]

    # 计算决定性证据召回
    naive_cover = _covered_markers([r.chunk.to_text() for r in naive_results], gold_markers)
    agentic_cover = _covered_markers([r.chunk.to_text() for r in agentic_results], gold_markers)

    def recall(cover: Dict[str, bool]) -> float:
        return (sum(cover.values()) / len(cover)) if cover else 0.0

    # 指标表
    table = Table(title="检索质量对比（决定性证据召回）")
    table.add_column("指标", style="cyan")
    table.add_column("朴素单次检索", justify="center", style="yellow")
    table.add_column("智能体化多轮检索", justify="center", style="green")
    table.add_row("检索查询次数", "1", str(len(agentic["trace"])))
    table.add_row("检索到的记忆块数", str(len(naive_results)), str(len(agentic_results)))
    for name in gold_markers:
        table.add_row(
            f"覆盖事实: {name}",
            "[green]✓[/green]" if naive_cover.get(name) else "[red]✗[/red]",
            "[green]✓[/green]" if agentic_cover.get(name) else "[red]✗[/red]",
        )
    if gold_markers:
        table.add_row("[bold]决定性证据召回率[/bold]",
                      f"[bold]{recall(naive_cover)*100:.0f}%[/bold]",
                      f"[bold]{recall(agentic_cover)*100:.0f}%[/bold]")
        naive_ok = all(naive_cover.values())
        agentic_ok = all(agentic_cover.values())
        table.add_row("能否完整消歧作答",
                      "[green]能[/green]" if naive_ok else "[red]不能[/red]",
                      "[green]能[/green]" if agentic_ok else "[red]不能[/red]")
    console.print()
    console.print(table)

    if gold_markers:
        console.print(Panel(
            "朴素单次检索只发一次查询，命中被「保养预约」这类关键词主导的文本块，"
            "容易漏掉另一辆车的关键信息；智能体化检索从首轮结果里发现「还有第二辆车」，"
            "再对每辆车追加聚焦查询，最终把两辆车的服务状态都取回，"
            "从而在多会话检索任务上超过 naive recall。",
            title="结论", border_style="green"))

    result = {
        "test_id": args.test_id,
        "question": question,
        "num_sessions": len(sessions),
        "num_chunks": len(chunks),
        "top_k": args.top_k,
        "naive": {
            "num_queries": 1,
            "num_retrieved": len(naive_results),
            "coverage": naive_cover,
            "recall": recall(naive_cover),
        },
        "agentic": {
            "num_queries": len(agentic["trace"]),
            "num_retrieved": len(agentic_results),
            "coverage": agentic_cover,
            "recall": recall(agentic_cover),
            "trace": agentic["trace"],
        },
    }

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"\n[green]✓ 结果已写入 {args.output}[/green]")

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="实验 3-9 离线演示：智能体化记忆检索 vs. 朴素单次检索（本地 BM25，无需 API）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--test-id", default=DEFAULT_TEST_ID,
                        help=f"评估集用例 ID（默认: {DEFAULT_TEST_ID}）")
    parser.add_argument("--test-cases-dir", default="../user-memory-evaluation/test_cases",
                        help="评估集 test_cases 目录（默认: ../user-memory-evaluation/test_cases）")
    parser.add_argument("--query", default=None,
                        help="覆盖用例自带的用户问题，指定要检索的问题")
    parser.add_argument("--top-k", type=int, default=3,
                        help="每次检索返回的记忆块数量（默认: 3）")
    parser.add_argument("--rounds-per-chunk", type=int, default=20,
                        help="对话历史分块时每块的轮数（默认: 20）")
    parser.add_argument("--max-followups", type=int, default=4,
                        help="智能体化检索最多追加的聚焦查询数（默认: 4）")
    parser.add_argument("--gold-marker", action="append", default=None,
                        help="自定义决定性证据关键词（可多次指定）；不指定时用内置默认")
    parser.add_argument("--output", default=None,
                        help="将结构化结果写入指定 JSON 文件路径")
    parser.add_argument("--quiet", action="store_true",
                        help="降低日志噪声（只显示 WARNING 及以上）")
    return parser


def main():
    args = build_parser().parse_args()
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    run_demo(args)


if __name__ == "__main__":
    main()
