#!/usr/bin/env python3
"""Real Intel SDM RAPTOR-vs-GraphRAG campaign for Experiment 3-7.

This campaign deliberately does not use the hand-authored offline demo.  It
extracts a bounded, pinned set of pages from Intel's current Volume 1 PDF,
builds hierarchical summaries and entity relationships with live Ark calls,
answers concept/detail and relationship/multi-hop questions through both
indexes, and has Moonshot judge the grounded answers.  Every provider call is
checkpointed and reused on restart.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import networkx as nx
import numpy as np
import torch
from openai import OpenAI
from sklearn.cluster import KMeans
from transformers import AutoModel, AutoTokenizer

PROJECT_DIR = Path(__file__).resolve().parent
CHAPTER_DIR = PROJECT_DIR.parent
sys.path.insert(0, str(CHAPTER_DIR))

from experiment_utils import ChatRecorder, sha256_file, write_campaign_evidence  # noqa: E402

ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"
MOONSHOT_ENDPOINT = "https://api.moonshot.cn/v1"
INTEL_URL = "https://cdrdv2.intel.com/v1/dl/getContent/671436"
PAGES = [254, 255, 256, 257, 258, 259, 260, 323, 360, 361, 362, 363, 364, 365]
SEED = 37
QUERIES = [
    {
        "id": "concept_sse_environment",
        "category": "concept-detail",
        "question": "What architectural state and data model define the Intel SSE programming environment?",
        "reference": "SSE adds eight 128-bit XMM0-XMM7 registers and the 32-bit MXCSR control/status register, and operates on packed or scalar single-precision floating-point data; 64-bit mode exposes XMM8-XMM15.",
        "gold_pages": [254, 255, 256, 257],
    },
    {
        "id": "detail_xmm64",
        "category": "concept-detail",
        "question": "In 64-bit mode, which additional XMM registers become accessible and how are they encoded?",
        "reference": "XMM8 through XMM15 become accessible and are selected with REX prefixes.",
        "gold_pages": [255],
    },
    {
        "id": "detail_mxcsr",
        "category": "concept-detail",
        "question": "Which MXCSR bits form the SIMD floating-point rounding-control field?",
        "reference": "MXCSR bits 13 and 14 form the rounding-control (RC) field.",
        "gold_pages": [256],
    },
    {
        "id": "concept_avx_features",
        "category": "concept-detail",
        "question": "What broad capabilities distinguish the AVX programming model described here?",
        "reference": "AVX uses VEX-encoded instructions, extends vector processing including 256-bit YMM state, and adds flexible data fetching, manipulation, and branch-support primitives.",
        "gold_pages": [361, 362, 363],
    },
    {
        "id": "relation_avx_detection",
        "category": "relationship-multi-hop",
        "question": "What complete processor-and-operating-system checks must an application perform before using AVX?",
        "reference": "Check CPUID OSXSAVE bit 27 and AVX bit 28, execute XGETBV with ECX=0, and verify XCR0 bits 2:1 are 11b so both XMM and YMM state are enabled by the OS.",
        "gold_pages": [363, 364],
        "path_hints": ["AVX", "XCR0"],
    },
    {
        "id": "relation_cpuid_insufficient",
        "category": "relationship-multi-hop",
        "question": "Why is CPUID.AVX alone insufficient proof that AVX instructions can execute?",
        "reference": "The operating system must enable XSAVE/XGETBV and XMM/YMM state management in XCR0; otherwise AVX instructions raise #UD even when CPUID.AVX is set.",
        "gold_pages": [323, 363, 364],
        "path_hints": ["CPUID", "YMM"],
    },
    {
        "id": "relation_cr4_xcr0",
        "category": "relationship-multi-hop",
        "question": "How do CR4.OSXSAVE, XGETBV, XCR0, and AVX state availability depend on one another?",
        "reference": "CR4.OSXSAVE enables the XSAVE feature set and application use of XGETBV; XGETBV reads XCR0, whose XMM/YMM bits must be enabled for AVX state and instructions to be available.",
        "gold_pages": [323, 363, 364],
        "path_hints": ["CR4.OSXSAVE", "AVX"],
    },
    {
        "id": "relation_xcr0_ud",
        "category": "relationship-multi-hop",
        "question": "What happens when an XSAVE-enabled feature is not fully enabled in XCR0, and how does that explain AVX #UD behavior?",
        "reference": "Instructions for a feature not fully enabled in XCR0 raise invalid-opcode #UD; AVX likewise #UDs when the OS has not enabled both XMM and YMM state even if the processor advertises AVX.",
        "gold_pages": [323, 364],
        "path_hints": ["XCR0", "#UD"],
    },
]


def parse_json(text: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", text or "")
    if not match:
        raise ValueError("provider response contained no JSON object")
    return json.loads(match.group())


class CachedCalls:
    def __init__(self, client: OpenAI, provider: str, endpoint: str, checkpoint: Path):
        self.recorder = ChatRecorder(client, provider, endpoint)
        self.checkpoint = checkpoint
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        if checkpoint.exists():
            self.recorder.calls = json.loads(checkpoint.read_text(encoding="utf-8"))

    def complete(self, purpose: str, **request: Any) -> str:
        for call in reversed(self.recorder.calls):
            choices = (call.get("response") or {}).get("choices") or []
            if call.get("purpose") == purpose and choices and choices[0].get("finish_reason") != "length":
                return choices[0]["message"]["content"] or ""
        try:
            response = self.recorder.create(purpose=purpose, **request)
            return response.choices[0].message.content or ""
        finally:
            self.checkpoint.write_text(
                json.dumps(self.recorder.calls, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )


class Encoder:
    def __init__(self, name: str):
        self.name = name
        self.tokenizer = AutoTokenizer.from_pretrained(name)
        self.model = AutoModel.from_pretrained(name).eval()

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        values = list(texts)
        batches = []
        for start in range(0, len(values), 16):
            tokens = self.tokenizer(
                values[start : start + 16], padding=True, truncation=True,
                max_length=384, return_tensors="pt",
            )
            with torch.no_grad():
                hidden = self.model(**tokens).last_hidden_state
            mask = tokens["attention_mask"].unsqueeze(-1).float()
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            pooled = torch.nn.functional.normalize(pooled.float(), p=2, dim=1)
            batches.append(pooled.numpy())
        return np.concatenate(batches).astype("float32")


def extract_pages(pdf: Path) -> list[dict[str, Any]]:
    pages = []
    for page in PAGES:
        proc = subprocess.run(
            ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"],
            text=True, capture_output=True, check=True,
        )
        text = proc.stdout.strip()
        pages.append({"page": page, "id": f"physical-page-{page}", "text": text})
    return pages


def chat_json(calls: CachedCalls, purpose: str, model: str, system: str, user: str,
              max_tokens: int = 2400) -> dict[str, Any]:
    return parse_json(
        calls.complete(
            purpose,
            model=model,
            seed=SEED,
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
    )


def build_raptor(pages: list[dict[str, Any]], ark: CachedCalls, model: str,
                 encoder: Encoder) -> list[dict[str, Any]]:
    nodes = []
    for page in pages:
        data = chat_json(
            ark, f"raptor-leaf-summary-page-{page['page']}", model,
            "Summarize Intel technical documentation without adding facts. Return JSON {summary,key_terms}.",
            f"Source physical PDF page {page['page']}:\n{page['text'][:14000]}",
        )
        nodes.append(
            {"id": f"leaf-{page['page']}", "level": 0, "summary": data["summary"],
             "key_terms": data.get("key_terms", []), "source_pages": [page["page"]],
             "children": [], "text_preview": page["text"][:1200]}
        )
    vectors = encoder.encode(node["summary"] for node in nodes)
    labels = KMeans(n_clusters=3, random_state=SEED, n_init=10).fit_predict(vectors)
    parents = []
    for cluster in sorted(set(labels.tolist())):
        children = [node for node, label in zip(nodes, labels) if int(label) == cluster]
        data = chat_json(
            ark, f"raptor-parent-summary-cluster-{cluster}", model,
            "Create a faithful cross-page technical summary. Return JSON {summary,key_relationships}.",
            "\n\n".join(f"PAGES {c['source_pages']}: {c['summary']}" for c in children),
        )
        parents.append(
            {"id": f"parent-{cluster}", "level": 1, "summary": data["summary"],
             "key_relationships": data.get("key_relationships", []),
             "source_pages": sorted({p for c in children for p in c["source_pages"]}),
             "children": [c["id"] for c in children]}
        )
    root_data = chat_json(
        ark, "raptor-root-summary", model,
        "Create the root summary of a technical hierarchy. Return JSON {summary,major_themes}.",
        "\n\n".join(f"PAGES {p['source_pages']}: {p['summary']}" for p in parents),
    )
    root = {
        "id": "root", "level": 2, "summary": root_data["summary"],
        "major_themes": root_data.get("major_themes", []),
        "source_pages": sorted({p for parent in parents for p in parent["source_pages"]}),
        "children": [parent["id"] for parent in parents],
    }
    return nodes + parents + [root]


def entity_key(name: str) -> str:
    return re.sub(r"[^a-z0-9#]+", "_", name.casefold()).strip("_")


def build_graph(pages: list[dict[str, Any]], ark: CachedCalls, model: str,
                encoder: Encoder) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], nx.Graph]:
    entities: dict[str, Any] = {}
    relationships = []
    for page in pages:
        data = chat_json(
            ark, f"graphrag-extract-page-{page['page']}", model,
            (
                "Extract a technical knowledge graph only from the source. Return JSON with entities "
                "[{name,type,description}] and relationships "
                "[{source,target,type,description}]. Preserve exact register/feature names "
                "and explicitly connect prerequisites, state components, instructions and failure outcomes."
                " Select at most 8 high-value entities and 8 explicit relationships per page; "
                "each description must be at most 18 words; avoid aliases and repetition."
            ),
            f"Physical PDF page {page['page']}:\n{page['text'][:9000]}",
            max_tokens=1400,
        )
        for raw in data.get("entities", []):
            name = str(raw.get("name", "")).strip()
            if not name:
                continue
            key = entity_key(name)
            item = entities.setdefault(
                key, {"id": key, "name": name, "type": raw.get("type", "concept"),
                      "descriptions": [], "evidence": [], "source_pages": []},
            )
            if raw.get("description") and raw["description"] not in item["descriptions"]:
                item["descriptions"].append(raw["description"])
            if raw.get("evidence_quote"):
                item["evidence"].append({"page": page["page"], "quote": raw["evidence_quote"]})
            item["source_pages"] = sorted(set(item["source_pages"] + [page["page"]]))
        for raw in data.get("relationships", []):
            source_name = str(raw.get("source", "")).strip()
            target_name = str(raw.get("target", "")).strip()
            if not source_name or not target_name:
                continue
            for name in (source_name, target_name):
                key = entity_key(name)
                entities.setdefault(
                    key, {"id": key, "name": name, "type": "concept", "descriptions": [],
                          "evidence": [], "source_pages": [page["page"]]},
                )
            relationships.append(
                {"source": entity_key(source_name), "target": entity_key(target_name),
                 "type": raw.get("type", "related_to"), "description": raw.get("description", ""),
                 "evidence_quote": raw.get("evidence_quote", ""), "source_page": page["page"]}
            )
    graph = nx.Graph()
    for key, entity in entities.items():
        graph.add_node(key, **entity)
    for rel in relationships:
        graph.add_edge(rel["source"], rel["target"], **rel)
    raw_communities = list(nx.community.greedy_modularity_communities(graph)) if graph.number_of_edges() else []
    raw_communities = sorted(raw_communities, key=len, reverse=True)[:8]
    communities = []
    for idx, members in enumerate(raw_communities):
        member_list = sorted(members)
        sub_relationships = [r for r in relationships if r["source"] in members and r["target"] in members]
        data = chat_json(
            ark, f"graphrag-community-summary-{idx}", model,
            "Summarize this graph community and its technical relationships. Return JSON {summary,key_relationships}.",
            json.dumps(
                {"entities": [entities[m] for m in member_list], "relationships": sub_relationships},
                ensure_ascii=False,
            )[:16000],
        )
        communities.append(
            {"id": f"community-{idx}", "entity_ids": member_list, "summary": data["summary"],
             "key_relationships": data.get("key_relationships", []),
             "source_pages": sorted({p for m in member_list for p in entities[m]["source_pages"]})}
        )
    return entities, relationships, communities, graph


def top_indices(scores: np.ndarray, k: int) -> list[int]:
    return np.argsort(-scores)[: min(k, len(scores))].tolist()


def raptor_context(query: str, nodes: list[dict[str, Any]], encoder: Encoder,
                   matrix: np.ndarray) -> tuple[str, list[int], list[dict[str, Any]]]:
    scores = matrix @ encoder.encode([query])[0]
    selected = [{**nodes[i], "score": float(scores[i])} for i in top_indices(scores, 5)]
    pages = sorted({page for node in selected for page in node["source_pages"]})
    text = "\n\n".join(
        f"NODE {node['id']} LEVEL {node['level']} SOURCE PAGES {node['source_pages']}: {node['summary']}"
        for node in selected
    )
    return text, pages, selected


def resolve_hint(graph: nx.Graph, hint: str) -> str | None:
    needle = hint.casefold()
    for node, attrs in graph.nodes(data=True):
        if needle in attrs.get("name", "").casefold() or needle in node.casefold():
            return node
    return None


def graph_context(query: str, spec: dict[str, Any], entities: dict[str, Any],
                  relationships: list[dict[str, Any]], communities: list[dict[str, Any]],
                  graph: nx.Graph, encoder: Encoder, entity_matrix: np.ndarray,
                  community_matrix: np.ndarray) -> tuple[str, list[int], dict[str, Any]]:
    q = encoder.encode([query])[0]
    entity_ids = list(entities)
    selected_ids = [entity_ids[i] for i in top_indices(entity_matrix @ q, 7)]
    expanded = set(selected_ids)
    for node in selected_ids:
        expanded.update(graph.neighbors(node))
    selected_relationships = [
        rel for rel in relationships if rel["source"] in expanded and rel["target"] in expanded
    ]
    selected_communities = []
    if communities:
        selected_communities = [communities[i] for i in top_indices(community_matrix @ q, 2)]
    pages = sorted(
        {p for node in expanded for p in entities[node]["source_pages"]}
        | {r["source_page"] for r in selected_relationships}
        | {p for c in selected_communities for p in c["source_pages"]}
    )
    paths = []
    hints = spec.get("path_hints") or []
    if len(hints) == 2:
        source, target = resolve_hint(graph, hints[0]), resolve_hint(graph, hints[1])
        if source and target and nx.has_path(graph, source, target):
            path = nx.shortest_path(graph, source, target)
            paths.append(
                {
                    "hints": hints, "nodes": [entities[node]["name"] for node in path],
                    "hops": len(path) - 1,
                    "edges": [graph[path[i]][path[i + 1]] for i in range(len(path) - 1)],
                }
            )
    context = {
        "entities": [entities[node] for node in sorted(expanded)],
        "relationships": selected_relationships,
        "communities": selected_communities,
        "explicit_paths": paths,
    }
    return json.dumps(context, ensure_ascii=False), pages, context


def answer(calls: CachedCalls, purpose: str, model: str, question: str, context: str) -> str:
    return calls.complete(
        purpose,
        model=model,
        seed=SEED,
        temperature=0,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": "Answer only from the retrieved Intel manual evidence. Cite physical PDF pages in brackets. If evidence is incomplete, say so."},
            {"role": "user", "content": f"QUESTION: {question}\n\nRETRIEVED EVIDENCE:\n{context}"},
        ],
    )


def call_totals(calls: list[dict[str, Any]]) -> dict[str, Any]:
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for call in calls:
        for key in usage:
            usage[key] += int((call.get("usage") or {}).get(key) or 0)
    return {"calls": len(calls), "usage": usage, "latency_ms": sum(float(c.get("latency_ms") or 0) for c in calls)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Experiment 3-7 real Intel structured-index campaign")
    parser.add_argument("--pdf", type=Path, default=PROJECT_DIR / "data" / "intel-sdm-volume-1.pdf")
    parser.add_argument("--model", default=os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"))
    parser.add_argument("--judge-model", default=os.getenv("STRUCTURED_INDEX_JUDGE", "moonshot-v1-32k"))
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    args = parser.parse_args()
    ark_key = os.getenv("ARK_API_KEY") or os.getenv("DOUBAO_API_KEY")
    moonshot_key = os.getenv("MOONSHOT_API_KEY")
    if not ark_key or not moonshot_key:
        raise RuntimeError("ARK_API_KEY and MOONSHOT_API_KEY are required")
    if not args.pdf.exists():
        args.pdf.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-L", "--fail", "-o", str(args.pdf), INTEL_URL], check=True)
    source_hash = sha256_file(args.pdf)
    checkpoint = PROJECT_DIR / "validation" / "checkpoints" / f"intel-{source_hash[:12]}"
    ark = CachedCalls(
        OpenAI(api_key=ark_key, base_url=ARK_ENDPOINT, timeout=180, max_retries=3),
        "volcengine-ark", ARK_ENDPOINT, checkpoint / "ark.json",
    )
    judge = CachedCalls(
        OpenAI(api_key=moonshot_key, base_url=MOONSHOT_ENDPOINT, timeout=180, max_retries=3),
        "moonshot", MOONSHOT_ENDPOINT, checkpoint / "moonshot.json",
    )

    pages = extract_pages(args.pdf)
    cover_text = subprocess.run(
        ["pdftotext", "-f", "1", "-l", "1", "-layout", str(args.pdf), "-"],
        text=True, capture_output=True, check=True,
    ).stdout
    encoder_started = time.perf_counter()
    encoder = Encoder(args.embedding_model)
    embedding_identity = {
        "provider": "local Hugging Face transformers", "model": args.embedding_model,
        "class": type(encoder.model).__name__,
        "parameters": sum(p.numel() for p in encoder.model.parameters()),
        "load_latency_ms": round((time.perf_counter() - encoder_started) * 1000, 3),
    }
    raptor_start = time.perf_counter()
    raptor_nodes = build_raptor(pages, ark, args.model, encoder)
    raptor_build_ms = (time.perf_counter() - raptor_start) * 1000
    raptor_matrix = encoder.encode(node["summary"] for node in raptor_nodes)

    graph_start = time.perf_counter()
    entities, relationships, communities, graph = build_graph(pages, ark, args.model, encoder)
    graph_build_ms = (time.perf_counter() - graph_start) * 1000
    entity_ids = list(entities)
    entity_matrix = encoder.encode(
        f"{entities[key]['name']}: {' '.join(entities[key]['descriptions'])}" for key in entity_ids
    )
    community_matrix = encoder.encode(c["summary"] for c in communities) if communities else np.empty((0, entity_matrix.shape[1]))

    results = []
    for spec in QUERIES:
        for method in ("raptor", "graphrag"):
            started = time.perf_counter()
            if method == "raptor":
                context, retrieved_pages, trace = raptor_context(spec["question"], raptor_nodes, encoder, raptor_matrix)
            else:
                context, retrieved_pages, trace = graph_context(
                    spec["question"], spec, entities, relationships, communities, graph,
                    encoder, entity_matrix, community_matrix,
                )
            response = answer(
                ark, f"answer-{method}-{spec['id']}", args.model, spec["question"], context
            )
            gold = set(spec["gold_pages"])
            recall = len(gold & set(retrieved_pages)) / len(gold)
            results.append(
                {"id": f"{method}:{spec['id']}", "method": method, "query_id": spec["id"],
                 "category": spec["category"], "question": spec["question"],
                 "reference": spec["reference"], "gold_pages": spec["gold_pages"],
                 "retrieved_pages": retrieved_pages, "citation_recall": recall,
                 "retrieval_trace": trace, "answer": response,
                 "query_latency_ms": round((time.perf_counter() - started) * 1000, 3)}
            )

    judgement_payload = [
        {k: row[k] for k in ("id", "question", "reference", "answer")} for row in results
    ]
    judgements = chat_json(
        judge, "external-judge-all-answers", args.judge_model,
        "Judge Intel technical answers. Return JSON {items:[{id,score,correct,reason}]}; score 0-4. Require all material conditions and no contradiction.",
        json.dumps(judgement_payload, ensure_ascii=False), max_tokens=3500,
    )["items"]
    judged = {item["id"]: item for item in judgements}
    for row in results:
        row["external_judge"] = judged[row["id"]]

    summary: dict[str, Any] = {}
    for method in ("raptor", "graphrag"):
        summary[method] = {}
        for category in ("concept-detail", "relationship-multi-hop", "overall"):
            selected = [
                row for row in results
                if row["method"] == method and (category == "overall" or row["category"] == category)
            ]
            summary[method][category] = {
                "n": len(selected),
                "mean_citation_recall": sum(r["citation_recall"] for r in selected) / len(selected),
                "mean_judge_score": sum(float(r["external_judge"]["score"]) for r in selected) / len(selected),
                "mean_query_latency_ms": sum(r["query_latency_ms"] for r in selected) / len(selected),
            }
    explicit_paths = [
        path for row in results if row["method"] == "graphrag"
        for path in (row["retrieval_trace"].get("explicit_paths") or [])
    ]
    acceptance = {
        "official_intel_pdf_pinned": args.pdf.stat().st_size > 1_000_000 and "June 2026" in cover_text,
        "bounded_real_pages_extracted": len(pages) == len(PAGES) and all(page["text"] for page in pages),
        "live_hierarchical_leaf_parent_root_summaries": len(raptor_nodes) == len(PAGES) + 4,
        "live_entity_relationship_extraction": len(entities) >= 10 and len(relationships) >= 5,
        "graph_communities_summarized": bool(communities),
        "concept_detail_and_relationship_multihop_sets": {q["category"] for q in QUERIES}
        == {"concept-detail", "relationship-multi-hop"},
        "both_indexes_answered_identical_queries": len(results) == len(QUERIES) * 2,
        "actual_graph_paths_retained": bool(explicit_paths),
        "external_judge_complete": len(judgements) == len(results),
        "raw_live_receipts_checkpointed": ark.checkpoint.exists() and judge.checkpoint.exists(),
    }
    evidence = {
        "status": "passed" if all(acceptance.values()) else "failed",
        "source": {
            "publisher": "Intel Corporation", "url": INTEL_URL,
            "title": "Intel 64 and IA-32 Architectures Software Developer's Manual, Volume 1: Basic Architecture",
            "order_number_revision": "253665-092US", "publication": "June 2026",
            "pdf_path": str(args.pdf.resolve()), "pdf_sha256": source_hash,
            "pdf_bytes": args.pdf.stat().st_size, "physical_pages_selected": PAGES,
            "cover_metadata_text": cover_text, "extracted_pages": pages,
        },
        "providers": {
            "builder_answerer": {"provider": "Volcengine Ark", "endpoint": ARK_ENDPOINT, "model": args.model, "seed": SEED},
            "judge": {"provider": "Moonshot", "endpoint": MOONSHOT_ENDPOINT, "model": args.judge_model, "seed": SEED},
            "embedding": embedding_identity,
        },
        "raptor": {"build_latency_ms": round(raptor_build_ms, 3), "nodes": raptor_nodes,
                   "statistics": {"levels": 3, "leaves": len(PAGES), "parents": 3, "roots": 1}},
        "graphrag": {
            "build_latency_ms": round(graph_build_ms, 3), "entities": entities,
            "relationships": relationships, "communities": communities,
            "statistics": {"entities": len(entities), "relationships": len(relationships),
                           "communities": len(communities), "density": nx.density(graph)},
        },
        "queries": QUERIES, "results": results, "explicit_multi_hop_paths": explicit_paths,
        "call_totals": {"ark": call_totals(ark.recorder.calls), "moonshot": call_totals(judge.recorder.calls)},
        "summary": summary, "acceptance": acceptance,
        "checkpoint_files": [str(ark.checkpoint), str(judge.checkpoint)],
    }
    manifest = write_campaign_evidence(
        PROJECT_DIR, "3-7", evidence,
        receipts=ark.recorder.calls + judge.recorder.calls,
        input_paths=[__file__, args.pdf, PROJECT_DIR / "config.py", PROJECT_DIR / "raptor_indexer.py", PROJECT_DIR / "graphrag_indexer.py"],
    )
    print(json.dumps(summary, indent=2))
    print(json.dumps(acceptance, indent=2))
    print(f"evidence: {manifest['run_dir']}")
    return 0 if all(acceptance.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
