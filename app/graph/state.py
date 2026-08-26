from typing import TypedDict

from app.domain.models import CompanyContext, Competitor, MonitoringBrief, NewsItem
from app.ports.scraper import ScrapedPage


class GraphState(TypedDict, total=False):
    source_url: str
    scraped_page: ScrapedPage | None
    scrape_failed: bool
    company_context: CompanyContext | None
    context_extraction_failed: bool
    competitors: list[Competitor]
    competitor_finding_failed: bool
    news_items: list[NewsItem]
    news_fetching_failed: bool
    curated_items: list[NewsItem]
    category_summaries: dict[str, str]
    briefing_failed: bool
    brief: MonitoringBrief | None
    editor_failed: bool
