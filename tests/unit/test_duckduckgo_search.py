import time
from unittest.mock import patch

from app.adapters.duckduckgo_search import DuckDuckGoSearch


class TestDuckDuckGoSearch:
    async def test_maps_ddgs_results_to_search_results(self) -> None:
        raw_results = [
            {"title": "Acme", "href": "https://acme.example.com", "body": "Acme snippet"},
            {"title": "Rival", "href": "https://rival.example.com", "body": "Rival snippet"},
        ]

        with patch("app.adapters.duckduckgo_search.DDGS") as mock_ddgs_class:
            mock_ddgs_class.return_value.text.return_value = raw_results
            search = DuckDuckGoSearch()

            results = await search.search("acme", max_results=2)

        assert [r.title for r in results] == ["Acme", "Rival"]
        assert str(results[0].url) == "https://acme.example.com/"
        assert results[0].snippet == "Acme snippet"
        mock_ddgs_class.return_value.text.assert_called_once_with("acme", max_results=2)

    async def test_empty_results_returns_empty_list(self) -> None:
        with patch("app.adapters.duckduckgo_search.DDGS") as mock_ddgs_class:
            mock_ddgs_class.return_value.text.return_value = []
            search = DuckDuckGoSearch()

            results = await search.search("no such query")

        assert results == []

    async def test_retries_after_transient_failure(self) -> None:
        raw_results = [
            {"title": "Acme", "href": "https://acme.example.com", "body": "Acme snippet"},
        ]

        with patch("app.adapters.duckduckgo_search.DDGS") as mock_ddgs_class:
            mock_ddgs_class.return_value.text.side_effect = [
                ConnectionError("transient failure"),
                raw_results,
            ]
            search = DuckDuckGoSearch()

            results = await search.search("acme")

        assert [r.title for r in results] == ["Acme"]
        assert mock_ddgs_class.return_value.text.call_count == 2

    async def test_respects_minimum_interval_between_calls(self) -> None:
        with patch("app.adapters.duckduckgo_search.DDGS") as mock_ddgs_class:
            mock_ddgs_class.return_value.text.return_value = []
            search = DuckDuckGoSearch(min_interval_seconds=0.1)

            start = time.monotonic()
            await search.search("first query")
            await search.search("second query")
            elapsed = time.monotonic() - start

        # Small tolerance: asyncio.sleep can wake marginally early depending on
        # OS timer granularity.
        assert elapsed >= 0.1 * 0.9
