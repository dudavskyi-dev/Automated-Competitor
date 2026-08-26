from app.graph.state import GraphState
from app.ports.scraper import WebScraper


class WebsiteScraperNode:
    def __init__(self, scraper: WebScraper) -> None:
        self._scraper = scraper

    async def __call__(self, state: GraphState) -> GraphState:
        try:
            page = await self._scraper.fetch_markdown(state["source_url"])
        except Exception:
            return {"scraped_page": None, "scrape_failed": True}

        if page.status_code != 200 or not page.markdown:
            return {"scraped_page": None, "scrape_failed": True}

        return {"scraped_page": page, "scrape_failed": False}
