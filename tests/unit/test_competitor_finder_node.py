from app.domain.models import CompanyContext, Competitor
from app.graph.nodes.competitor_finder import CompetitorFinderNode, _CompetitorListResponse
from app.ports.search import SearchResult
from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_search import FakeSearch


class FailingSearch:
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raise ConnectionError("search backend unreachable")


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


class TestCompetitorFinderNode:
    async def test_happy_path_sets_competitors(self) -> None:
        context = make_context()
        search_results = [
            SearchResult(title="Rival Inc", url="https://rival.example.com", snippet="a rival")
        ]
        competitors = [make_competitor()]
        search = FakeSearch(results={"project management saas competitors": search_results})
        llm = FakeLLM(responses=[_CompetitorListResponse(competitors=competitors)])
        node = CompetitorFinderNode(search=search, llm=llm)

        result = await node({"company_context": context, "context_extraction_failed": False})

        assert result["competitors"] == competitors
        assert result["competitor_finding_failed"] is False
        assert search.calls == ["project management saas competitors"]

    async def test_skips_when_context_extraction_failed(self) -> None:
        search = FakeSearch()
        llm = FakeLLM(responses=[])
        node = CompetitorFinderNode(search=search, llm=llm)

        result = await node({"company_context": None, "context_extraction_failed": True})

        assert result["competitors"] == []
        assert result["competitor_finding_failed"] is True
        assert search.calls == []

    async def test_search_exception_sets_finding_failed(self) -> None:
        llm = FakeLLM(responses=[])
        node = CompetitorFinderNode(search=FailingSearch(), llm=llm)

        result = await node({"company_context": make_context(), "context_extraction_failed": False})

        assert result["competitors"] == []
        assert result["competitor_finding_failed"] is True

    async def test_llm_returns_wrong_type_sets_finding_failed(self) -> None:
        search = FakeSearch()
        llm = FakeLLM(responses=["not a competitor list"])
        node = CompetitorFinderNode(search=search, llm=llm)

        result = await node({"company_context": make_context(), "context_extraction_failed": False})

        assert result["competitors"] == []
        assert result["competitor_finding_failed"] is True
