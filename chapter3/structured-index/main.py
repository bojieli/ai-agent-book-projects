"""
结构化索引工具的主入口：构建 / 查询 RAPTOR 与 GraphRAG 索引，或运行离线对比演示。

说明：RAPTOR、GraphRAG 的**索引构建**需要调用 LLM（实体抽取、递归摘要），因此
build / query 依赖 OPENAI_API_KEY 及相应重型依赖（umap、sentence-transformers 等）。
若只想直观理解「结构化索引解决了扁平检索的什么问题」，可运行无需 API 的 `demo` 子命令。
"""

import argparse
import asyncio
from pathlib import Path
import json
import sys

from loguru import logger


async def build_indexes(file_path: Path, index_type: str = "both",
                        output: str = None):
    """Build RAPTOR and/or GraphRAG indexes from a document."""
    # 重型依赖延迟导入：保证 --help / demo 在缺少 umap 等依赖时仍可用
    from config import get_raptor_config, get_graphrag_config
    from raptor_indexer import RaptorIndexer
    from graphrag_indexer import GraphRAGIndexer
    from document_processor import DocumentProcessor

    logger.info(f"Building {index_type} index(es) from {file_path}")

    # Process document
    processor = DocumentProcessor()
    text = await processor.process_file(file_path)
    logger.info(f"Processed document: {len(text)} characters")

    all_stats = {}

    # Build RAPTOR index
    if index_type in ["raptor", "both"]:
        logger.info("Building RAPTOR tree index...")
        raptor_config = get_raptor_config()
        raptor = RaptorIndexer(raptor_config)
        raptor.build_index(text)
        raptor.save_index()
        stats = raptor.get_tree_statistics()
        all_stats["raptor"] = stats
        logger.info(f"RAPTOR index built: {stats}")

    # Build GraphRAG index
    if index_type in ["graphrag", "both"]:
        logger.info("Building GraphRAG knowledge graph...")
        graphrag_config = get_graphrag_config()
        graphrag = GraphRAGIndexer(graphrag_config)
        graphrag.build_knowledge_graph(text)
        graphrag.detect_communities()
        graphrag.hierarchical_summarization()
        graphrag.save_index()
        stats = graphrag.get_graph_statistics()
        all_stats["graphrag"] = stats
        logger.info(f"GraphRAG index built: {stats}")

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(all_stats, f, ensure_ascii=False, indent=2)
        logger.info(f"索引统计已写入：{output}")

    logger.info("Indexing complete!")


async def query_indexes(query: str, index_type: str = "both", top_k: int = 5,
                        multi_hop: int = 0):
    """Query RAPTOR and/or GraphRAG indexes."""
    from config import get_raptor_config, get_graphrag_config
    from raptor_indexer import RaptorIndexer
    from graphrag_indexer import GraphRAGIndexer

    results = {}

    # Query RAPTOR
    if index_type in ["raptor", "both"]:
        try:
            raptor_config = get_raptor_config()
            raptor = RaptorIndexer(raptor_config)
            raptor.load_index()
            raptor_results = raptor.search(query, top_k)
            results["raptor"] = raptor_results
            logger.info(f"RAPTOR returned {len(raptor_results)} results")
        except Exception as e:
            logger.error(f"Error querying RAPTOR: {e}")

    # Query GraphRAG
    if index_type in ["graphrag", "both"]:
        try:
            graphrag_config = get_graphrag_config()
            graphrag = GraphRAGIndexer(graphrag_config)
            graphrag.load_index()
            graphrag_results = graphrag.search(query, top_k)
            results["graphrag"] = graphrag_results
            logger.info(f"GraphRAG returned {len(graphrag_results)} results")

            # 多跳关系检索：以召回的最佳实体为起点，沿关系边遍历
            if multi_hop > 0 and graphrag_results:
                start = next((r.get("name") for r in graphrag_results
                              if r.get("type") == "entity"), None)
                if start:
                    paths = graphrag.multi_hop_search(start, max_hops=multi_hop)
                    results["graphrag_multi_hop"] = paths
                    logger.info(f"GraphRAG multi-hop from '{start}' "
                                f"returned {len(paths)} paths")
        except Exception as e:
            logger.error(f"Error querying GraphRAG: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="结构化索引工具：在统一框架下构建并查询 RAPTOR（树状层次）与 "
                    "GraphRAG（实体关系图）索引，对应本书实验 3-7。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="要执行的子命令")

    # Build command
    build_parser = subparsers.add_parser(
        "build", help="从文档构建结构化索引（需要 OPENAI_API_KEY）")
    build_parser.add_argument("file", type=str,
                              help="待索引的文档路径（支持 .pdf/.txt/.md/.html）")
    build_parser.add_argument("--type", choices=["raptor", "graphrag", "both"],
                              default="both", help="要构建的索引类型（默认 both）")
    build_parser.add_argument("--output", type=str, default=None,
                              help="将索引统计信息写入指定 JSON 文件")

    # Query command
    query_parser = subparsers.add_parser(
        "query", help="查询已构建的索引（需要 OPENAI_API_KEY 及已有索引）")
    query_parser.add_argument("query", type=str, help="检索查询语句")
    query_parser.add_argument("--type", choices=["raptor", "graphrag", "both"],
                              default="both", help="要查询的索引类型（默认 both）")
    query_parser.add_argument("--top-k", type=int, default=5,
                              help="返回结果条数（默认 5）")
    query_parser.add_argument("--multi-hop", type=int, default=0, metavar="N",
                              help="对 GraphRAG 额外执行 N 跳关系遍历（0 表示关闭）")
    query_parser.add_argument("--output", type=str, default=None,
                              help="将查询结果写入指定 JSON 文件")

    # Demo command（离线，无需 API）
    demo_parser = subparsers.add_parser(
        "demo", help="离线对比演示：结构化索引 vs 扁平检索（无需 API Key）")
    demo_parser.add_argument("--query", type=str, default=None,
                             help="自定义查询；缺省时运行内置的三组对比查询")
    demo_parser.add_argument("--top-k", type=int, default=3,
                             help="扁平检索展示的结果条数（默认 3）")
    demo_parser.add_argument("--output", type=str, default=None,
                             help="将演示结果写入指定 JSON 文件")

    # Server command
    subparsers.add_parser("serve", help="启动 HTTP API 服务")

    args = parser.parse_args()

    if args.command == "build":
        asyncio.run(build_indexes(Path(args.file), args.type, args.output))
    elif args.command == "query":
        results = asyncio.run(query_indexes(args.query, args.type, args.top_k,
                                            args.multi_hop))

        # Display results
        for index_type, index_results in results.items():
            print(f"\n{index_type.upper()} Results:")
            print("-" * 50)
            if index_type == "graphrag_multi_hop":
                for i, r in enumerate(index_results, 1):
                    chain = r["path"][0]["source"]
                    for step in r["path"]:
                        chain += f" --{step['relation']}--> {step['target']}"
                    print(f"\n{i}. [{r['hops']} 跳] {chain}")
                continue
            for i, result in enumerate(index_results, 1):
                print(f"\n{i}. Score: {result.get('score', 'N/A'):.3f}")
                if 'summary' in result:
                    print(f"   Summary: {result['summary'][:200]}...")
                elif 'description' in result:
                    print(f"   Description: {result['description'][:200]}...")
                if 'level' in result:
                    print(f"   Level: {result['level']}")

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n查询结果已写入：{args.output}")
    elif args.command == "demo":
        from structured_vs_flat_demo import run_demo
        run_demo(top_k=args.top_k, custom_query=args.query, output=args.output)
    elif args.command == "serve":
        from api_service import run_server
        run_server()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
