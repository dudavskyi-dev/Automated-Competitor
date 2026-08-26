from app.domain.models import NewsItem
from app.graph.nodes.briefing import BriefingNode
from tests.fakes.fake_llm import FakeLLM


class FailingLLM:
    async def complete(self, system: str, user: str, response_model: object = None) -> object:
        raise ValueError("LLM backend unreachable")


class PartiallyFailingLLM:
    async def complete(self, system: str, user: str, response_model: object = None) -> object:
        if "Rival" in user:
            raise ValueError("LLM backend unreachable")
        return f"summary of: {user}"


def make_item(
    title: str = "Acme raises Series B",
    url: str = "https://news.example.com/acme",
    related_entity: str = "company",
) -> NewsItem:
    return NewsItem(
        title=title,
        url=url,
        source="news.example.com",
        published_at=None,
        snippet="Acme Corp announced a $20M Series B round.",
        related_entity=related_entity,
    )


class TestBriefingNode:
    async def test_happy_path_summarizes_each_category(self) -> None:
        items = [
            make_item(related_entity="company"),
            make_item(
                title="Industry grows",
                url="https://news.example.com/ind",
                related_entity="industry",
            ),
        ]
        llm = FakeLLM(responses=["company summary", "industry summary"])
        node = BriefingNode(llm=llm)

        result = await node({"curated_items": items})

        assert result["category_summaries"] == {
            "company": "company summary",
            "industry": "industry summary",
        }
        assert result["briefing_failed"] is False

    async def test_empty_curated_items_returns_empty_summaries(self) -> None:
        node = BriefingNode(llm=FakeLLM(responses=[]))

        result = await node({"curated_items": []})

        assert result["category_summaries"] == {}
        assert result["briefing_failed"] is False

    async def test_all_llm_calls_fail_sets_briefing_failed(self) -> None:
        node = BriefingNode(llm=FailingLLM())

        result = await node({"curated_items": [make_item()]})

        assert result["category_summaries"] == {}
        assert result["briefing_failed"] is True

    async def test_partial_llm_failure_keeps_successful_summaries(self) -> None:
        items = [
            make_item(related_entity="company"),
            make_item(
                title="Rival news", url="https://news.example.com/r", related_entity="Rival Inc"
            ),
        ]
        node = BriefingNode(llm=PartiallyFailingLLM())

        result = await node({"curated_items": items})

        assert "company" in result["category_summaries"]
        assert "Rival Inc" not in result["category_summaries"]
        assert result["briefing_failed"] is False
