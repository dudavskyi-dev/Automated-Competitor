import pytest

from app.ports.llm import LLMClient
from app.ports.scraper import ScrapedPage, WebScraper
from app.ports.search import SearchResult, WebSearch
from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_scraper import FakeScraper
from tests.fakes.fake_search import FakeSearch


class TestFakeScraper:
    def test_isinstance_of_protocol(self) -> None:
        assert isinstance(FakeScraper(), WebScraper)

    async def test_returns_page_for_known_url(self) -> None:
        page = ScrapedPage(
            url="https://example.com", markdown="# Hello", title="Hello", status_code=200
        )
        scraper = FakeScraper(pages={"https://example.com": page})

        result = await scraper.fetch_markdown("https://example.com")

        assert result == page
        assert scraper.calls == ["https://example.com"]

    async def test_falls_back_to_default(self) -> None:
        default = ScrapedPage(
            url="https://fallback.com", markdown="# Fallback", title=None, status_code=200
        )
        scraper = FakeScraper(default=default)

        result = await scraper.fetch_markdown("https://unknown.com")

        assert result == default

    async def test_raises_when_no_match_and_no_default(self) -> None:
        scraper = FakeScraper()

        with pytest.raises(KeyError):
            await scraper.fetch_markdown("https://unknown.com")


class TestFakeSearch:
    def test_isinstance_of_protocol(self) -> None:
        assert isinstance(FakeSearch(), WebSearch)

    async def test_returns_results_for_known_query(self) -> None:
        results = [
            SearchResult(title="A", url="https://a.example.com", snippet="snippet a"),
            SearchResult(title="B", url="https://b.example.com", snippet="snippet b"),
        ]
        search = FakeSearch(results={"acme": results})

        found = await search.search("acme")

        assert found == results
        assert search.calls == ["acme"]

    async def test_truncates_to_max_results(self) -> None:
        results = [
            SearchResult(title=str(i), url=f"https://{i}.example.com", snippet="s")
            for i in range(5)
        ]
        search = FakeSearch(results={"acme": results})

        found = await search.search("acme", max_results=2)

        assert len(found) == 2

    async def test_falls_back_to_default(self) -> None:
        default = [SearchResult(title="D", url="https://d.example.com", snippet="s")]
        search = FakeSearch(default=default)

        found = await search.search("unknown query")

        assert found == default

    async def test_default_is_empty_list_when_unset(self) -> None:
        search = FakeSearch()

        found = await search.search("unknown query")

        assert found == []


class TestFakeLLM:
    def test_isinstance_of_protocol(self) -> None:
        assert isinstance(FakeLLM(responses=[]), LLMClient)

    async def test_returns_responses_in_queue_order(self) -> None:
        llm = FakeLLM(responses=["first", "second"])

        first = await llm.complete(system="sys", user="u1")
        second = await llm.complete(system="sys", user="u2")

        assert first == "first"
        assert second == "second"

    async def test_records_calls(self) -> None:
        llm = FakeLLM(responses=["ok"])

        await llm.complete(system="sys", user="hello", response_model=None)

        assert llm.calls == [("sys", "hello", None)]
