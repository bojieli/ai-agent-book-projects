"""Feature completeness matrix — every architecture mockable feature must be present."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FEATURES = [
    ("bff_chat_sse", "app.api.bff", "BffApp.post_chat_completions"),
    ("bff_meetings", "app.api.bff", "BffApp.post_meetings"),
    ("bff_hitl", "app.api.bff", "BffApp.post_hitl"),
    ("bff_render", "app.api.bff", "BffApp.post_render"),
    ("bff_admin_skills", "app.api.bff", "BffApp.admin_skills_approve"),
    ("bff_admin_glossary", "app.api.bff", "BffApp.admin_glossary_approve"),
    ("bff_admin_quotas", "app.api.bff", "BffApp.admin_quotas_put"),
    ("bff_admin_usage", "app.api.bff", "BffApp.admin_usage_get"),
    ("bff_internal_transcript", "app.api.bff", "BffApp.internal_transcripts"),
    ("bff_internal_webhook", "app.api.bff", "BffApp.internal_connector_webhook"),
    ("authz", "app.security.authz", "MockAuthZ"),
    ("sop_runner", "app.planes.pipeline.sop_runner", "SopPipelineRunner"),
    ("charts", "app.render.charts", "render_charts"),
    ("hallucination", "app.agents.hallucination", "detect_hallucination"),
    ("capacity_night", "app.ops.capacity", "allow_reindex"),
    ("mcp_server", "app.connectors.mcp_server", "MockMcpServer"),
    ("series_continuum", "app.knowledge.series", "MeetingSeriesStore"),
    ("skill_admin", "app.governance.skill_admin", "SkillAdmin"),
    ("llm_eval", "app.agents.llm_evaluator", "IndependentLLMEvaluator"),
    ("asr", "app.knowledge.asr", "MockAsrService"),
    ("vector", "app.knowledge.vector_mock", "MockHybridIndex"),
    ("jira", "app.connectors.mock_saas", "MockJiraConnector"),
    ("wecom", "app.connectors.mock_saas", "MockWeComClient"),
    ("voice_stub", "app.planes.dialog.voice_stub", "VoiceInterfaceStub"),
    ("negative_runners", "app.eval.negative_runners", "run_negative_catalog"),
    ("mocked_platform", "app.runtime.mocked_platform", "MockedPlatform"),
    ("rag_pipeline", "app.knowledge.rag", "RagPipeline"),
    ("embedding_bge_m3", "app.knowledge.embedding", "get_embedding_provider"),
    ("chunking", "app.knowledge.chunking", "chunk_document"),
    ("grounding", "app.knowledge.grounding", "build_grounded_answer"),
    ("retrieval_quality", "app.eval.retrieval_quality", "run_eval"),
]


def main() -> int:
    import importlib

    failed = []
    for fid, mod, attr in FEATURES:
        try:
            m = importlib.import_module(mod)
            obj = m
            for part in attr.split("."):
                obj = getattr(obj, part)
            print(f"  OK  {fid}")
        except Exception as exc:  # noqa: BLE001
            print(f" FAIL {fid}: {exc}")
            failed.append(fid)
    print(f"\nFeatures {len(FEATURES) - len(failed)}/{len(FEATURES)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
