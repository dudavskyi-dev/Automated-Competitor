from app.ports.search import SearchResult


class FakeSearch:
    def __init__(
        self,
        results: dict[str, list[SearchResult]] | None = None,
        default: list[SearchResult] | None = None,
    ) -> None:
        self._results = results or {}
        self._default = default if default is not None else []
        self.calls: list[str] = []
        self.max_results_calls: list[int] = []

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        self.calls.append(query)
        self.max_results_calls.append(max_results)
        return self._results.get(query, self._default)[:max_results]
