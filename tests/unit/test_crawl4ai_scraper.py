from types import SimpleNamespace
from unittest.mock import patch

from app.adapters.crawl4ai_scraper import Crawl4AIScraper


class FakeAsyncWebCrawler:
    def __init__(self, result: SimpleNamespace) -> None:
        self._result = result

    async def __aenter__(self) -> "FakeAsyncWebCrawler":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def arun(self, url: str) -> SimpleNamespace:
        self.called_with_url = url
        return self._result


class TestCrawl4AIScraper:
    async def test_happy_path_maps_result_to_scraped_page(self) -> None:
        result = SimpleNamespace(
            markdown="# Acme\nWe help teams plan sprints.",
            status_code=200,
            metadata={"title": "Acme"},
        )
        fake_crawler = FakeAsyncWebCrawler(result)

        with patch(
            "app.adapters.crawl4ai_scraper.AsyncWebCrawler", return_value=fake_crawler
        ):
            scraper = Crawl4AIScraper()
            page = await scraper.fetch_markdown("https://acme.example.com")

        assert str(page.url) == "https://acme.example.com/"
        assert page.markdown == "# Acme\nWe help teams plan sprints."
        assert page.title == "Acme"
        assert page.status_code == 200
        assert fake_crawler.called_with_url == "https://acme.example.com"

    async def test_non_200_status_is_passed_through_unmodified(self) -> None:
        result = SimpleNamespace(markdown="Forbidden", status_code=403, metadata=None)
        fake_crawler = FakeAsyncWebCrawler(result)

        with patch(
            "app.adapters.crawl4ai_scraper.AsyncWebCrawler", return_value=fake_crawler
        ):
            scraper = Crawl4AIScraper()
            page = await scraper.fetch_markdown("https://acme.example.com")

        assert page.status_code == 403
        assert page.title is None

    async def test_missing_status_code_defaults_to_zero(self) -> None:
        result = SimpleNamespace(markdown=None, status_code=None, metadata=None)
        fake_crawler = FakeAsyncWebCrawler(result)

        with patch(
            "app.adapters.crawl4ai_scraper.AsyncWebCrawler", return_value=fake_crawler
        ):
            scraper = Crawl4AIScraper()
            page = await scraper.fetch_markdown("https://acme.example.com")

        assert page.status_code == 0
        assert page.markdown == ""
