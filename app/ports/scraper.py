from typing import Protocol, runtime_checkable

from pydantic import BaseModel, HttpUrl


class ScrapedPage(BaseModel):
    url: HttpUrl
    markdown: str
    title: str | None
    status_code: int


@runtime_checkable
class WebScraper(Protocol):
    async def fetch_markdown(self, url: str) -> ScrapedPage: ...
