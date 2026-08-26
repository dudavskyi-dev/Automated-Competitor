from app.domain.models import NewsItem
from app.graph.nodes.curator import CuratorNode


def make_item(
    title: str = "Acme raises Series B",
    url: str = "https://news.example.com/acme",
    snippet: str = "Acme Corp announced a $20M Series B round.",
    related_entity: str = "company",
) -> NewsItem:
    return NewsItem(
        title=title,
        url=url,
        source="news.example.com",
        published_at=None,
        snippet=snippet,
        related_entity=related_entity,
    )


class TestCuratorNode:
    async def test_deduplicates_by_url_keeping_first_occurrence(self) -> None:
        first = make_item(title="First version")
        duplicate = make_item(title="Duplicate version")
        node = CuratorNode()

        result = await node({"news_items": [first, duplicate]})

        assert result["curated_items"] == [first]

    async def test_filters_out_items_with_empty_title_or_snippet(self) -> None:
        empty_title = make_item(title="   ", url="https://news.example.com/a")
        empty_snippet = make_item(snippet="", url="https://news.example.com/b")
        valid = make_item(url="https://news.example.com/c")
        node = CuratorNode()

        result = await node({"news_items": [empty_title, empty_snippet, valid]})

        assert result["curated_items"] == [valid]

    async def test_empty_input_returns_empty_list(self) -> None:
        node = CuratorNode()

        result = await node({"news_items": []})

        assert result["curated_items"] == []

    async def test_missing_news_items_key_returns_empty_list(self) -> None:
        node = CuratorNode()

        result = await node({})

        assert result["curated_items"] == []
