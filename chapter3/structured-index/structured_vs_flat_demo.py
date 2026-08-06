"""
结构化索引 vs 扁平检索：离线对比演示。

本模块不依赖 OpenAI / 向量模型 / 网络，纯 Python + networkx 即可运行。
它用一个手工整理的「Intel x86 SIMD 指令集」小知识库，直观对比两条检索路线：

  * 扁平检索（Flat）：把每个知识点当成互相独立的文本块，按词面相似度打分召回。
    这是传统 RAG「文档分块 + 向量检索」的抽象——只能返回零散片段。
  * 结构化检索（Structured）：
      - GraphRAG 式的实体-关系图：沿关系边做多跳遍历，能回答扁平检索答不了的
        「A 通过什么和 B 相连」这类关系性问题（对应书中「多跳关系推理」）。
      - RAPTOR 式的层次树：把细节聚合成上层摘要，能回答「概述某主题」这类
        需要跨片段综合的宏观问题（对应书中「多层次导航」）。

这段演示对应实验 3-7（structured-index）中「知识表达哲学的对比研究」。
构建真实索引需要调用 LLM（见 main.py build），本演示则把索引结果预先手工写好，
让读者无需 API Key 也能看到「结构化索引到底解决了扁平检索的什么问题」。
"""

import json
import re
from collections import deque
from typing import Dict, List, Optional, Tuple

import networkx as nx


# ---------------------------------------------------------------------------
# 手工整理的小知识库（对应 test_indexing.py 中的 Intel x86 示例文档）
# 每个实体的 description 同时充当「扁平检索的一个文本块」。
# ---------------------------------------------------------------------------

ENTITIES: Dict[str, Dict[str, str]] = {
    "ADDPS": {"type": "instruction",
              "desc": "ADDPS：对打包的单精度浮点数执行并行加法，一次处理四路单精度浮点运算。"},
    "MOVAPS": {"type": "instruction",
               "desc": "MOVAPS：在向量寄存器与对齐内存之间搬运 128 位打包单精度浮点数据。"},
    "VADDPS": {"type": "instruction",
               "desc": "VADDPS：AVX 版本的打包单精度浮点加法，一次处理八路单精度浮点运算。"},
    "CPUID": {"type": "instruction",
              "desc": "CPUID：返回处理器标识与特性信息，用于探测处理器是否支持 SSE、AVX 等扩展。"},
    "SSE": {"type": "extension",
            "desc": "SSE（Streaming SIMD Extensions）：引入 128 位向量寄存器，支持打包单精度浮点并行运算。"},
    "AVX": {"type": "extension",
            "desc": "AVX（Advanced Vector Extensions）：把向量寄存器扩展到 256 位，进一步增强 SIMD 能力。"},
    "XMM": {"type": "register",
            "desc": "XMM0-XMM15：128 位向量寄存器，供 SSE 指令存放打包数据。"},
    "YMM": {"type": "register",
            "desc": "YMM0-YMM15：256 位向量寄存器，供 AVX 指令使用，低 128 位与 XMM 共享。"},
    "CR4.OSFXSR": {"type": "control-bit",
                   "desc": "CR4.OSFXSR：操作系统支持 FXSAVE/FXRSTOR 的控制位，置 1 后才允许使用 SSE 指令。"},
    "CR0.EM": {"type": "control-bit",
               "desc": "CR0.EM：仿真标志位，为 1 时禁用 SIMD，必须清零才能执行 SSE / AVX 指令。"},
}

# 实体-关系三元组（主语, 关系, 宾语），构成 GraphRAG 的知识之网。
TRIPLES: List[Tuple[str, str, str]] = [
    ("ADDPS", "属于", "SSE"),
    ("MOVAPS", "属于", "SSE"),
    ("VADDPS", "属于", "AVX"),
    ("ADDPS", "操作", "XMM"),
    ("VADDPS", "操作", "YMM"),
    ("SSE", "使用寄存器", "XMM"),
    ("AVX", "使用寄存器", "YMM"),
    ("AVX", "扩展自", "SSE"),
    ("SSE", "需要启用", "CR4.OSFXSR"),
    ("AVX", "需要启用", "CR4.OSFXSR"),
    ("SSE", "要求清零", "CR0.EM"),
    ("CPUID", "探测", "SSE"),
    ("CPUID", "探测", "AVX"),
]

# RAPTOR 式层次树：把细粒度叶子聚合为上层摘要（父节点）。
TREE_SUMMARY = {
    "id": "SIMD 指令集综述",
    "summary": ("x86 的 SIMD 指令集自 MMX 起步，SSE 引入 128 位 XMM 向量寄存器并支持打包"
                "单精度浮点运算，AVX 进一步把寄存器扩展到 256 位 YMM，逐代提升单指令多数据"
                "的并行宽度；使用前需通过 CR0/CR4 控制位使能，并可用 CPUID 探测支持情况。"),
    "children": ["ADDPS", "MOVAPS", "VADDPS", "SSE", "AVX", "XMM", "YMM"],
}


# ---------------------------------------------------------------------------
# 扁平检索：把每个实体描述当作独立文本块，按词面相似度（词频余弦）召回。
# 这是「向量检索」在离线场景下的一个确定性替身：无内在结构、只看片段本身。
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """粗粒度分词：ASCII 词（如 ADDPS、CR4、XMM）整体保留，中文按单字切。"""
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    tokens += re.findall(r"[一-鿿]", text)
    return tokens


def _cosine(a: Dict[str, int], b: Dict[str, int]) -> float:
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


class FlatRetriever:
    """按词面相似度召回独立文本块（模拟扁平向量检索）。"""

    def __init__(self, entities: Dict[str, Dict[str, str]]):
        self.docs = {name: e["desc"] for name, e in entities.items()}
        self.types = {name: e["type"] for name, e in entities.items()}
        self._vecs = {name: self._tf(text) for name, text in self.docs.items()}

    @staticmethod
    def _tf(text: str) -> Dict[str, int]:
        vec: Dict[str, int] = {}
        for tok in _tokenize(text):
            vec[tok] = vec.get(tok, 0) + 1
        return vec

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        qvec = self._tf(query)
        scored = [
            {"name": name, "type": self.types[name],
             "desc": self.docs[name], "score": _cosine(qvec, self._vecs[name])}
            for name in self.docs
        ]
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]


# ---------------------------------------------------------------------------
# 结构化检索：基于实体-关系图的多跳遍历（GraphRAG 的核心能力）。
# ---------------------------------------------------------------------------

def build_graph(triples: List[Tuple[str, str, str]]) -> nx.DiGraph:
    g = nx.DiGraph()
    for name, meta in ENTITIES.items():
        g.add_node(name, **meta)
    for src, rel, dst in triples:
        g.add_edge(src, dst, rel=rel)
    return g


def multi_hop_paths(graph: nx.DiGraph, start: str, max_hops: int = 3) -> List[List[Tuple[str, str, str]]]:
    """从 start 出发沿关系边做 BFS，返回所有 <= max_hops 跳的关系路径。

    每条路径是若干 (源实体, 关系, 目标实体) 步骤的列表。这正是扁平检索无法表达的
    「沿关系边遍历」——对应书中「知识图谱天然支持沿关系边遍历，使多跳查询高效可靠」。
    """
    if start not in graph:
        return []
    paths: List[List[Tuple[str, str, str]]] = []
    # 队列元素：(当前节点, 到达该节点的路径)
    queue: deque = deque([(start, [])])
    while queue:
        node, path = queue.popleft()
        if len(path) >= max_hops:
            continue
        for nbr in graph.successors(node):
            step = (node, graph[node][nbr]["rel"], nbr)
            new_path = path + [step]
            paths.append(new_path)
            queue.append((nbr, new_path))
    return paths


def match_entity(graph: nx.DiGraph, query: str) -> Optional[str]:
    """在查询中找出出现的起始实体（按名字最长匹配，确定性）。"""
    q = query.lower()
    hits = [name for name in graph.nodes if name.lower() in q]
    return max(hits, key=len) if hits else None


def format_path(path: List[Tuple[str, str, str]]) -> str:
    if not path:
        return ""
    parts = [path[0][0]]
    for src, rel, dst in path:
        parts.append(f" --{rel}--> {dst}")
    return "".join(parts)


# ---------------------------------------------------------------------------
# 三个演示查询：分别凸显扁平检索的三类短板。
# ---------------------------------------------------------------------------

def demo_multi_hop(flat: FlatRetriever, graph: nx.DiGraph, query: str, top_k: int) -> None:
    print(f"\n【查询 1｜多跳关系推理】{query}")
    print("-- 扁平检索（按词面相似度返回独立片段）--")
    for i, r in enumerate(flat.search(query, top_k), 1):
        print(f"  {i}. [{r['type']}] {r['name']}  (score={r['score']:.3f})")
    print("  ✗ 只能召回词面相近的孤立片段，无法把 ADDPS 与某个控制位「连」起来——"
          "缺少关系，就无法判断哪个控制位是 ADDPS 的答案。")

    print("-- 结构化图检索（沿关系边多跳遍历）--")
    start = match_entity(graph, query)
    paths = multi_hop_paths(graph, start, max_hops=3)
    # 只展示终点为控制位的路径（问题问的是「控制寄存器位」）
    answers = [p for p in paths if graph.nodes[p[-1][2]]["type"] == "control-bit"]
    for p in answers:
        print(f"  {format_path(p)}")
    enable = [p for p in answers if p[-1][1] == "需要启用"]
    if enable:
        target = enable[0][-1][2]
        print(f"  ✓ 答案：{target}（从 {start} 经 {len(enable[0])} 跳可达）")
        print(f"    {graph.nodes[target]['desc']}")


def demo_compare(flat: FlatRetriever, graph: nx.DiGraph, query: str, top_k: int) -> None:
    print(f"\n【查询 2｜跨节点综合对比】{query}")
    print("-- 扁平检索 --")
    for i, r in enumerate(flat.search(query, top_k), 1):
        print(f"  {i}. [{r['type']}] {r['name']}  (score={r['score']:.3f})")
    print("  ✗ SSE 与 AVX 各自的寄存器事实散落在不同片段里，扁平检索把它们分别召回，"
          "却不会主动把「谁用哪种寄存器」对齐成一张对比表。")

    print("-- 结构化图检索（顺着「使用寄存器」边取回两侧事实）--")
    for ext in ("SSE", "AVX"):
        regs = [dst for _, dst, d in graph.out_edges(ext, data=True) if d["rel"] == "使用寄存器"]
        for reg in regs:
            print(f"  {ext} --使用寄存器--> {reg}：{graph.nodes[reg]['desc']}")
    print("  ✓ 沿同一种关系边遍历两个实体，即可直接综合出「SSE=128 位 XMM，AVX=256 位 YMM」的对比。")


def demo_hierarchical(flat: FlatRetriever, query: str, top_k: int) -> None:
    print(f"\n【查询 3｜多层次导航（RAPTOR 层次树）】{query}")
    print("-- 扁平检索 --")
    for i, r in enumerate(flat.search(query, top_k), 1):
        print(f"  {i}. [{r['type']}] {r['name']}  (score={r['score']:.3f})")
    print("  ✗ 召回的是零散的细节片段，过于细碎，答不了「概述」这种需要跨片段综合的宏观问题。")

    print("-- 结构化树检索（返回上层摘要节点）--")
    print(f"  [父节点摘要] {TREE_SUMMARY['id']}")
    print(f"  {TREE_SUMMARY['summary']}")
    print(f"  ✓ 由宏观摘要切入，需要细节时再向下钻取到 {', '.join(TREE_SUMMARY['children'][:4])} 等叶子节点。")


def run_demo(top_k: int = 3, custom_query: Optional[str] = None,
             output: Optional[str] = None) -> Dict:
    """运行离线对比演示；返回结构化结果（便于 --output 落盘）。"""
    flat = FlatRetriever(ENTITIES)
    graph = build_graph(TRIPLES)

    print("=" * 68)
    print("结构化索引 vs 扁平检索 · 离线对比演示（无需 API Key）")
    print(f"知识库：Intel x86 SIMD 指令集  |  实体 {graph.number_of_nodes()} 个，"
          f"关系 {graph.number_of_edges()} 条，层次树 1 棵")
    print("=" * 68)

    if custom_query:
        # 自定义查询：同时给出扁平与图检索两种视角
        print(f"\n【自定义查询】{custom_query}")
        print("-- 扁平检索 --")
        flat_hits = flat.search(custom_query, top_k)
        for i, r in enumerate(flat_hits, 1):
            print(f"  {i}. [{r['type']}] {r['name']}  (score={r['score']:.3f})")
        print("-- 结构化图检索（从查询中识别到的实体多跳遍历）--")
        start = match_entity(graph, custom_query)
        if start is None:
            print("  （未在查询中识别到已知实体，无法进行图遍历）")
            paths = []
        else:
            paths = multi_hop_paths(graph, start, max_hops=3)
            for p in paths:
                print(f"  {format_path(p)}")
        result = {"query": custom_query,
                  "flat": [{"name": r["name"], "score": r["score"]} for r in flat_hits],
                  "graph_start": start,
                  "graph_paths": [format_path(p) for p in paths]}
    else:
        q1 = "运行 ADDPS 指令前，操作系统必须把哪个控制寄存器位置 1？"
        q2 = "SSE 与 AVX 使用的向量寄存器有什么区别？"
        q3 = "概述一下 x86 的 SIMD 指令集"
        demo_multi_hop(flat, graph, q1, top_k)
        demo_compare(flat, graph, q2, top_k)
        demo_hierarchical(flat, q3, top_k)
        start1 = match_entity(graph, q1)
        result = {
            "queries": [q1, q2, q3],
            "multi_hop": {
                "query": q1,
                "start": start1,
                "paths": [format_path(p) for p in multi_hop_paths(graph, start1, 3)
                          if graph.nodes[p[-1][2]]["type"] == "control-bit"],
            },
        }

    print("\n" + "=" * 68)
    print("结论：扁平检索擅长「找到含某信息的片段」，但一旦查询需要跨片段的关系推理或"
          "多层次综合，就必须依赖结构化索引（图 / 层次树）。——对应书中实验 3-7 的核心观点。")
    print("=" * 68)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n结果已写入：{output}")
    return result


if __name__ == "__main__":
    run_demo()
