from app.domain.models import CompanyContext, Competitor
from app.graph.nodes.news_fetcher import NewsFetcherNode
from app.ports.search import SearchResult
from tests.fakes.fake_search import FakeSearch


class FailingSearch:
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raise ConnectionError("search backend unreachable")


class PartiallyFailingSearch:
    def __init__(self, results: dict[str, list[SearchResult]]) -> None:
        self._results = results

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if query not in self._results:
            raise ConnectionError("search backend unreachable")
        return self._results[query]


def make_context() -> CompanyContext:
    return CompanyContext(
        source_url="https://acme.example.com",
        domain="B2B SaaS for project management",
        target_audience="small dev teams",
        value_proposition="faster sprint planning",
        keywords=["project management", "saas"],
    )


def make_competitor(name: str = "Rival Inc") -> Competitor:
    return Competitor(name=name, url="https://rival.example.com", reason="similar audience")


class TestNewsFetcherNode:
    async def test_happy_path_fans_out_and_tags_entities(self) -> None:
        context = make_context()
        competitor = make_competitor()
        results = {
            "project management saas news": [
                SearchResult(title="Acme news", url="https://news.example.com/acme", snippet="s")
            ],
            "Rival Inc news": [
                SearchResult(title="Rival news", url="https://news.example.com/rival", snippet="s")
            ],
            "B2B SaaS for project management industry news": [
                SearchResult(title="Industry news", url="https://news.example.com/ind", snippet="s")
            ],
        }
        search = FakeSearch(results=results)
        node = NewsFetcherNode(search=search)

        result = await node(
            {
                "company_context": context,
                "context_extraction_failed": False,
                "competitors": [competitor],
            }
        )

        items = result["news_items"]
        assert result["news_fetching_failed"] is False
        assert {item.related_entity for item in items} == {"company", "Rival Inc", "industry"}
        assert len(items) == 3

    async def test_skips_when_context_extraction_failed(self) -> None:
        search = FakeSearch()
        node = NewsFetcherNode(search=search)

        result = await node({"company_context": None, "context_extraction_failed": True})

        assert result["news_items"] == []
        assert result["news_fetching_failed"] is True

    async def test_all_queries_fail_sets_fetching_failed(self) -> None:
        node = NewsFetcherNode(search=FailingSearch())

        result = await node(
            {
                "company_context": make_context(),
                "context_extraction_failed": False,
                "competitors": [],
            }
        )

        assert result["news_items"] == []
        assert result["news_fetching_failed"] is True

    async def test_partial_failure_still_returns_available_items(self) -> None:
        context = make_context()
        results = {
            "project management saas news": [
                SearchResult(title="Acme news", url="https://news.example.com/acme", snippet="s")
            ],
        }
        search = PartiallyFailingSearch(results=results)
        node = NewsFetcherNode(search=search)

        result = await node(
            {"company_context": context, "context_extraction_failed": False, "competitors": []}
        )

        assert result["news_fetching_failed"] is False
        assert len(result["news_items"]) == 1
        assert result["news_items"][0].related_entity == "company"
