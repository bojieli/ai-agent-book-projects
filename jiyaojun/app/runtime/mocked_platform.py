"""Wire mock SaaS + ASR + vector + LLM evaluator for demos/tests."""

from __future__ import annotations

from pathlib import Path

from app.agents.llm_evaluator import IndependentLLMEvaluator, MockLLMClient
from app.connectors.mock_saas import MockJiraConnector, MockWeComClient
from app.connectors.persistent_defect import PersistentDefectConnector
from app.knowledge.asr import MockAsrService
from app.knowledge.vector_mock import MockHybridIndex, VectorDoc
from app.runtime.full import FullRuntime


class MockedPlatform:
    """All remaining external systems as mocks — drop-in for real later."""

    def __init__(self, root: Path, data_dir: Path | None = None) -> None:
        self.root = root
        data = data_dir or (root / "data" / "mock_platform")
        data.mkdir(parents=True, exist_ok=True)
        self.runtime = FullRuntime(root)
        self.runtime.store = __import__(
            "app.store.meetings", fromlist=["MeetingStore"]
        ).MeetingStore(data / "meetings.json")
        from app.schedule.service import ScheduleService

        self.runtime.schedule = ScheduleService(
            self.runtime.store, self.runtime.calendar, self.runtime.events
        )

        self.defect = PersistentDefectConnector(data / "defects.json")
        self.jira = MockJiraConnector(self.defect)
        self.runtime.runtime.register(self.defect)
        self.runtime.runtime.register(self.jira)
        self.runtime.defect = self.defect
        from app.connectors.work_embed import WorkEmbedService

        self.runtime.work_embed = WorkEmbedService(
            self.runtime.runtime, self.runtime.events
        )

        self.wecom = MockWeComClient()
        self.asr = MockAsrService()
        from app.knowledge import KnowledgePlane, RagPipeline, BgeM3ShimProvider

        self.vectors = MockHybridIndex()  # legacy helper index
        self.knowledge = KnowledgePlane(RagPipeline(BgeM3ShimProvider()))
        self.knowledge.seed_demo()
        self.rag = self.knowledge.rag
        self.vectors.upsert(
            VectorDoc(
                "doc_timeout",
                "eng",
                "internal",
                ["u_pm", "u_dev_a"],
                "接口超时与重试约定文档",
            )
        )
        self.vectors.upsert(
            VectorDoc(
                "doc_hr_sealed",
                "hr",
                "critical",
                ["u_hrbp"],
                "绩效校准密封材料",
                write_class="sealed",
            )
        )
        self.llm_eval = IndependentLLMEvaluator(MockLLMClient())

    def deliver_via_wecom(self, meeting_id: str, users: list[str], md: str) -> dict:
        return self.wecom.send_markdown(touser=users, content=md, meeting_id=meeting_id)
