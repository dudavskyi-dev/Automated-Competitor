from crawl4ai import AsyncWebCrawler
from pydantic import HttpUrl

from app.ports.scraper import ScrapedPage


class Crawl4AIScraper:
    async def fetch_markdown(self, url: str) -> ScrapedPage:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)

        markdown = str(result.markdown) if result.markdown is not None else ""
        title = (result.metadata or {}).get("title")

        return ScrapedPage(
            url=HttpUrl(url),
            markdown=markdown,
            title=title,
            status_code=result.status_code or 0,
        )
