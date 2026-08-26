from app.domain.models import CompanyContext, Competitor, MonitoringBrief
from app.graph.build_graph import build_graph
from app.graph.nodes.competitor_finder import _CompetitorListResponse
from app.ports.scraper import ScrapedPage
from app.ports.search import SearchResult
from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_scraper import FakeScraper
from tests.fakes.fake_search import FakeSearch

SOURCE_URL = "https://acme.example.com"


class TestGraphEndToEnd:
    async def test_full_pipeline_produces_monitoring_brief(self) -> None:
        page = ScrapedPage(
            url=SOURCE_URL,
            markdown="# Acme\nWe help small dev teams plan sprints faster.",
            title="Acme",
            status_code=200,
        )
        scraper = FakeScraper(pages={SOURCE_URL: page})

        context = CompanyContext(
            source_url=SOURCE_URL,
            domain="B2B SaaS for project management",
            target_audience="small dev teams",
            value_proposition="faster sprint planning",
            keywords=["project management", "saas"],
        )
        competitor = Competitor(
            name="Rival Inc", url="https://rival.example.com", reason="similar audience"
        )

        search = FakeSearch(
            results={
                "project management saas competitors": [
                    SearchResult(
                        title="Rival Inc", url="https://rival.example.com", snippet="a rival"
                    )
                ],
                "project management saas news": [
                    SearchResult(
                        title="Acme raises Series B",
                        url="https://news.example.com/acme",
                        snippet="Acme announced a $20M Series B round.",
                    )
                ],
                "Rival Inc news": [
                    SearchResult(
                        title="Rival Inc expands",
                        url="https://news.example.com/rival",
                        snippet="Rival Inc opened a new office.",
                    )
                ],
                "B2B SaaS for project management industry news": [
                    SearchResult(
                        title="Project management tools trend up",
                        url="https://news.example.com/industry",
                        snippet="The project management software market is growing.",
                    )
                ],
            }
        )

        llm = FakeLLM(
            responses=[
                context,
                _CompetitorListResponse(competitors=[competitor]),
                "Acme raised a $20M Series B round.",
                "Rival Inc opened a new office.",
                "The project management software market is growing.",
                "# Weekly Brief\n\nAcme, Rival Inc, and the industry all had news this week.",
            ]
        )

        graph = build_graph(scraper=scraper, search=search, llm=llm)

        result = await graph.ainvoke({"source_url": SOURCE_URL})

        assert result["scrape_failed"] is False
        assert result["context_extraction_failed"] is False
        assert result["competitor_finding_failed"] is False
        assert result["news_fetching_failed"] is False
        assert result["briefing_failed"] is False
        assert result["editor_failed"] is False

        brief = result["brief"]
        assert isinstance(brief, MonitoringBrief)
        assert brief.company == context
        assert brief.competitors == [competitor]
        assert {item.related_entity for item in brief.items} == {
            "company",
            "Rival Inc",
            "industry",
        }
        assert brief.summary_markdown.startswith("# Weekly Brief")
