import asyncio
import time

from ddgs import DDGS

from app.adapters.resilience import call_with_retry
from app.ports.search import SearchResult


class DuckDuckGoSearch:
    def __init__(self, min_interval_seconds: float = 1.0) -> None:
        self._min_interval_seconds = min_interval_seconds
        self._rate_limit_lock = asyncio.Lock()
        self._last_call_at: float | None = None

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        async def _do() -> list[SearchResult]:
            async with self._rate_limit_lock:
                await self._wait_for_rate_limit()
                raw_results = await asyncio.to_thread(DDGS().text, query, max_results=max_results)
                self._last_call_at = time.monotonic()

            return [
                SearchResult(title=r["title"], url=r["href"], snippet=r["body"])
                for r in raw_results
            ]

        return await call_with_retry(_do)

    async def _wait_for_rate_limit(self) -> None:
        if self._last_call_at is None:
            return
        elapsed = time.monotonic() - self._last_call_at
        remaining = self._min_interval_seconds - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)
