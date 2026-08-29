from app.domain.models import CompanyContext
from app.graph.nodes.competitor_finder import CompetitorFinderNode, _CompetitorNameListResponse
from app.ports.scraper import ScrapedPage
from app.ports.search import SearchResult
from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_scraper import FakeScraper
from tests.fakes.fake_search import FakeSearch


class FailingSearch:
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raise ConnectionError("search backend unreachable")


class IdentifyOnlySearch:
    """Succeeds for the identify-stage query, fails for any per-competitor site lookup."""

    def __init__(self, identify_results: list[SearchResult]) -> None:
        self._identify_results = identify_results

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if query == '"Acme" competitors':
            return self._identify_results
        raise ConnectionError("search backend unreachable")


def make_context() -> CompanyContext:
    return CompanyContext(
        source_url="https://acme.example.com",
        company_name="Acme",
        domain="B2B SaaS for project management",
        target_audience="small dev teams",
        value_proposition="faster sprint planning",
        keywords=["project management", "saas"],
    )


class TestCompetitorFinderNode:
    async def test_happy_path_scrapes_and_describes_each_competitor(self) -> None:
        context = make_context()
        identify_results = [
            SearchResult(
                title="Top alternatives", url="https://blog.example.com/x", snippet="a list"
            )
        ]
        search = FakeSearch(
            results={
                '"Acme" competitors': identify_results,
                "Rival Inc official website": [
                    SearchResult(
                        title="Rival Inc",
                        url="https://rival.example.com",
                        snippet="a rival snippet",
                    )
                ],
                "Other Co official website": [
                    SearchResult(
                        title="Other Co", url="https://other.example.com", snippet="another snippet"
                    )
                ],
            }
        )
        scraper = FakeScraper(
            pages={
                "https://rival.example.com/": ScrapedPage(
                    url="https://rival.example.com",
                    markdown="Rival Inc builds project management tools.",
                    title="Rival Inc",
                    status_code=200,
                ),
                "https://other.example.com/": ScrapedPage(
                    url="https://other.example.com",
                    markdown="Other Co builds sprint planning software.",
                    title="Other Co",
                    status_code=200,
                ),
            }
        )
        llm = FakeLLM(
            responses=[
                _CompetitorNameListResponse(names=["Rival Inc", "Other Co"]),
                "Rival Inc builds project management software for dev teams.",
                "Other Co builds sprint planning software.",
            ]
        )
        node = CompetitorFinderNode(search=search, scraper=scraper, llm=llm)

        result = await node({"company_context": context, "context_extraction_failed": False})

        assert result["competitor_finding_failed"] is False
        competitors = result["competitors"]
        assert [c.name for c in competitors] == ["Rival Inc", "Other Co"]
        assert str(competitors[0].url) == "https://rival.example.com/"
        assert (
            competitors[0].reason
            == "Rival Inc builds project management software for dev teams."
        )
        assert str(competitors[1].url) == "https://other.example.com/"
        assert competitors[1].reason == "Other Co builds sprint planning software."
        assert search.calls[0] == '"Acme" competitors'
        assert search.max_results_calls[0] == 2

    async def test_competitor_scrape_failure_falls_back_to_search_snippet(self) -> None:
        context = make_context()
        search = FakeSearch(
            results={
                '"Acme" competitors': [],
                "Rival Inc official website": [
                    SearchResult(
                        title="Rival Inc",
                        url="https://rival.example.com",
                        snippet="a rival snippet",
                    )
                ],
            }
        )
        scraper = FakeScraper(pages={})  # no page registered -> fetch_markdown raises KeyError
        llm = FakeLLM(responses=[_CompetitorNameListResponse(names=["Rival Inc"])])
        node = CompetitorFinderNode(search=search, scraper=scraper, llm=llm)

        result = await node({"company_context": context, "context_extraction_failed": False})

        competitors = result["competitors"]
        assert len(competitors) == 1
        assert competitors[0].name == "Rival Inc"
        assert competitors[0].reason == "a rival snippet"

    async def test_competitor_site_search_failure_falls_back_to_generic_reason(self) -> None:
        context = make_context()
        llm = FakeLLM(responses=[_CompetitorNameListResponse(names=["Rival Inc"])])
        search = IdentifyOnlySearch(identify_results=[])
        node = CompetitorFinderNode(search=search, scraper=FakeScraper(), llm=llm)

        result = await node({"company_context": context, "context_extraction_failed": False})

        competitors = result["competitors"]
        assert len(competitors) == 1
        assert competitors[0].reason == "Identified as a competitor of Acme."
        assert competitors[0].url is None

    async def test_skips_self_and_duplicate_names(self) -> None:
        context = make_context()
        search = FakeSearch(
            results={
                '"Acme" competitors': [],
                "Rival Inc official website": [
                    SearchResult(
                        title="Rival Inc",
                        url="https://rival.example.com",
                        snippet="a rival snippet",
                    )
                ],
            }
        )
        scraper = FakeScraper(
            pages={
                "https://rival.example.com/": ScrapedPage(
                    url="https://rival.example.com",
                    markdown="Rival Inc builds tools.",
                    title="Rival Inc",
                    status_code=200,
                ),
            }
        )
        llm = FakeLLM(
            responses=[
                _CompetitorNameListResponse(names=["acme", "Rival Inc", "rival inc", ""]),
                "Rival Inc builds project management tools.",
            ]
        )
        node = CompetitorFinderNode(search=search, scraper=scraper, llm=llm)

        result = await node({"company_context": context, "context_extraction_failed": False})

        assert [c.name for c in result["competitors"]] == ["Rival Inc"]

    async def test_skips_when_context_extraction_failed(self) -> None:
        node = CompetitorFinderNode(
            search=FakeSearch(), scraper=FakeScraper(), llm=FakeLLM(responses=[])
        )

        result = await node({"company_context": None, "context_extraction_failed": True})

        assert result["competitors"] == []
        assert result["competitor_finding_failed"] is True

    async def test_identify_search_exception_sets_finding_failed(self) -> None:
        llm = FakeLLM(responses=[])
        node = CompetitorFinderNode(search=FailingSearch(), scraper=FakeScraper(), llm=llm)

        result = await node({"company_context": make_context(), "context_extraction_failed": False})

        assert result["competitors"] == []
        assert result["competitor_finding_failed"] is True

    async def test_identify_llm_returns_wrong_type_sets_finding_failed(self) -> None:
        search = FakeSearch()
        llm = FakeLLM(responses=["not a name list"])
        node = CompetitorFinderNode(search=search, scraper=FakeScraper(), llm=llm)

        result = await node({"company_context": make_context(), "context_extraction_failed": False})

        assert result["competitors"] == []
        assert result["competitor_finding_failed"] is True
