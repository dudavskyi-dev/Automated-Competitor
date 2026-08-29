from datetime import datetime

from pydantic import BaseModel, HttpUrl


class CompanyContext(BaseModel):
    source_url: HttpUrl
    company_name: str
    domain: str
    target_audience: str
    value_proposition: str
    keywords: list[str]


class Competitor(BaseModel):
    name: str
    url: HttpUrl | None
    reason: str


class NewsItem(BaseModel):
    title: str
    url: HttpUrl
    source: str
    published_at: datetime | None
    snippet: str
    related_entity: str


class MonitoringBrief(BaseModel):
    company: CompanyContext
    competitors: list[Competitor]
    items: list[NewsItem]
    generated_at: datetime
    summary_markdown: str
