from crawl4ai import AsyncWebCrawler
from pydantic import HttpUrl

from app.adapters.resilience import call_with_retry
from app.ports.scraper import ScrapedPage


class Crawl4AIScraper:
    async def fetch_markdown(self, url: str) -> ScrapedPage:
        async def _do() -> ScrapedPage:
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

        return await call_with_retry(_do)
