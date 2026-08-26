from typing import Protocol, runtime_checkable

from pydantic import BaseModel, HttpUrl


class SearchResult(BaseModel):
    title: str
    url: HttpUrl
    snippet: str


@runtime_checkable
class WebSearch(Protocol):
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]: ...
