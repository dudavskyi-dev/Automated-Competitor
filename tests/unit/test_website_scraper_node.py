from app.graph.nodes.website_scraper import WebsiteScraperNode
from app.ports.scraper import ScrapedPage
from tests.fakes.fake_scraper import FakeScraper


class TestWebsiteScraperNode:
    async def test_happy_path_sets_scraped_page(self) -> None:
        page = ScrapedPage(
            url="https://example.com", markdown="# Hello", title="Hello", status_code=200
        )
        scraper = FakeScraper(pages={"https://example.com": page})
        node = WebsiteScraperNode(scraper=scraper)

        result = await node({"source_url": "https://example.com"})

        assert result["scraped_page"] == page
        assert result["scrape_failed"] is False

    async def test_non_200_status_sets_scrape_failed(self) -> None:
        page = ScrapedPage(
            url="https://example.com", markdown="Forbidden", title=None, status_code=403
        )
        scraper = FakeScraper(pages={"https://example.com": page})
        node = WebsiteScraperNode(scraper=scraper)

        result = await node({"source_url": "https://example.com"})

        assert result["scraped_page"] is None
        assert result["scrape_failed"] is True

    async def test_empty_markdown_sets_scrape_failed(self) -> None:
        page = ScrapedPage(url="https://example.com", markdown="", title=None, status_code=200)
        scraper = FakeScraper(pages={"https://example.com": page})
        node = WebsiteScraperNode(scraper=scraper)

        result = await node({"source_url": "https://example.com"})

        assert result["scraped_page"] is None
        assert result["scrape_failed"] is True

    async def test_scraper_exception_sets_scrape_failed(self) -> None:
        scraper = FakeScraper()  # no pages, no default -> raises KeyError
        node = WebsiteScraperNode(scraper=scraper)

        result = await node({"source_url": "https://unknown.com"})

        assert result["scraped_page"] is None
        assert result["scrape_failed"] is True
