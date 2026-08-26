from datetime import UTC, datetime

from app.domain.models import CompanyContext, Competitor, NewsItem
from app.graph.nodes.editor import EditorNode
from tests.fakes.fake_llm import FakeLLM


class FailingLLM:
    async def complete(self, system: str, user: str, response_model: object = None) -> object:
        raise ValueError("LLM backend unreachable")


FIXED_TIME = datetime(2026, 1, 2, tzinfo=UTC)


def make_context() -> CompanyContext:
    return CompanyContext(
        source_url="https://acme.example.com",
        domain="B2B SaaS for project management",
        target_audience="small dev teams",
        value_proposition="faster sprint planning",
        keywords=["project management", "saas"],
    )


def make_competitor() -> Competitor:
    return Competitor(name="Rival Inc", url="https://rival.example.com", reason="similar audience")


def make_item() -> NewsItem:
    return NewsItem(
        title="Acme raises Series B",
        url="https://news.example.com/acme",
        source="news.example.com",
        published_at=None,
        snippet="Acme Corp announced a $20M Series B round.",
        related_entity="company",
    )


class TestEditorNode:
    async def test_happy_path_builds_monitoring_brief(self) -> None:
        context = make_context()
        competitors = [make_competitor()]
        items = [make_item()]
        llm = FakeLLM(responses=["# Weekly brief\n\nAcme raised a Series B."])
        node = EditorNode(llm=llm, clock=lambda: FIXED_TIME)

        result = await node(
            {
                "company_context": context,
                "context_extraction_failed": False,
                "competitors": competitors,
                "curated_items": items,
                "category_summaries": {"company": "Acme raised a Series B."},
            }
        )

        brief = result["brief"]
        assert result["editor_failed"] is False
        assert brief.company == context
        assert brief.competitors == competitors
        assert brief.items == items
        assert brief.generated_at == FIXED_TIME
        assert brief.summary_markdown == "# Weekly brief\n\nAcme raised a Series B."

    async def test_skips_when_context_extraction_failed(self) -> None:
        node = EditorNode(llm=FakeLLM(responses=[]))

        result = await node({"company_context": None, "context_extraction_failed": True})

        assert result["brief"] is None
        assert result["editor_failed"] is True

    async def test_llm_exception_falls_back_to_deterministic_markdown(self) -> None:
        context = make_context()
        node = EditorNode(llm=FailingLLM(), clock=lambda: FIXED_TIME)

        result = await node(
            {
                "company_context": context,
                "context_extraction_failed": False,
                "competitors": [],
                "curated_items": [],
                "category_summaries": {"company": "Acme raised a Series B."},
            }
        )

        assert result["editor_failed"] is False
        assert "Acme raised a Series B." in result["brief"].summary_markdown

    async def test_llm_returns_wrong_type_falls_back_to_deterministic_markdown(self) -> None:
        context = make_context()
        llm = FakeLLM(responses=[42])
        node = EditorNode(llm=llm, clock=lambda: FIXED_TIME)

        result = await node(
            {
                "company_context": context,
                "context_extraction_failed": False,
                "competitors": [],
                "curated_items": [],
                "category_summaries": {},
            }
        )

        assert result["editor_failed"] is False
        assert result["brief"].summary_markdown == "# Monitoring Brief\n\nNo summaries available."
