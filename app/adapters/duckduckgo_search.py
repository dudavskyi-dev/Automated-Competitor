import asyncio

from ddgs import DDGS

from app.ports.search import SearchResult


class DuckDuckGoSearch:
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raw_results = await asyncio.to_thread(DDGS().text, query, max_results=max_results)
        return [
            SearchResult(title=r["title"], url=r["href"], snippet=r["body"]) for r in raw_results
        ]
