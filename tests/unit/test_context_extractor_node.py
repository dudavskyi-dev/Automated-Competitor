from app.domain.models import CompanyContext
from app.graph.nodes.context_extractor import ContextExtractorNode
from app.ports.scraper import ScrapedPage
from tests.fakes.fake_llm import FakeLLM


class FailingLLM:
    async def complete(self, system: str, user: str, response_model: object = None) -> object:
        raise ValueError("invalid JSON from LLM")


def make_page(markdown: str = "# Acme\nWe help teams plan sprints.") -> ScrapedPage:
    return ScrapedPage(
        url="https://acme.example.com", markdown=markdown, title="Acme", status_code=200
    )


def make_context() -> CompanyContext:
    return CompanyContext(
        source_url="https://acme.example.com",
        domain="B2B SaaS for project management",
        target_audience="small dev teams",
        value_proposition="faster sprint planning",
        keywords=["project management", "saas"],
    )


class TestContextExtractorNode:
    async def test_happy_path_sets_company_context(self) -> None:
        context = make_context()
        llm = FakeLLM(responses=[context])
        node = ContextExtractorNode(llm=llm)

        result = await node({"scraped_page": make_page(), "scrape_failed": False})

        assert result["company_context"] == context
        assert result["context_extraction_failed"] is False
        assert llm.calls[0][2] is CompanyContext

    async def test_skips_extraction_when_scrape_failed(self) -> None:
        llm = FakeLLM(responses=[])
        node = ContextExtractorNode(llm=llm)

        result = await node({"scraped_page": None, "scrape_failed": True})

        assert result["company_context"] is None
        assert result["context_extraction_failed"] is True
        assert llm.calls == []

    async def test_llm_exception_sets_extraction_failed(self) -> None:
        node = ContextExtractorNode(llm=FailingLLM())

        result = await node({"scraped_page": make_page(), "scrape_failed": False})

        assert result["company_context"] is None
        assert result["context_extraction_failed"] is True

    async def test_llm_returns_wrong_type_sets_extraction_failed(self) -> None:
        llm = FakeLLM(responses=["not a CompanyContext"])
        node = ContextExtractorNode(llm=llm)

        result = await node({"scraped_page": make_page(), "scrape_failed": False})

        assert result["company_context"] is None
        assert result["context_extraction_failed"] is True
