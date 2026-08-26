from urllib.parse import urlparse

from app.domain.models import NewsItem
from app.graph.state import GraphState
from app.ports.search import SearchResult, WebSearch


def _to_news_item(result: SearchResult, related_entity: str) -> NewsItem:
    return NewsItem(
        title=result.title,
        url=result.url,
        source=urlparse(str(result.url)).netloc,
        published_at=None,
        snippet=result.snippet,
        related_entity=related_entity,
    )


class NewsFetcherNode:
    def __init__(self, search: WebSearch) -> None:
        self._search = search

    async def __call__(self, state: GraphState) -> GraphState:
        context = state.get("company_context")
        if state.get("context_extraction_failed") or context is None:
            return {"news_items": [], "news_fetching_failed": True}

        competitors = state.get("competitors", [])
        queries = [(f"{' '.join(context.keywords)} news", "company")]
        queries += [(f"{c.name} news", c.name) for c in competitors]
        queries.append((f"{context.domain} industry news", "industry"))

        items: list[NewsItem] = []
        any_success = False
        for query, related_entity in queries:
            try:
                results = await self._search.search(query)
            except Exception:
                continue
            any_success = True
            items.extend(_to_news_item(r, related_entity) for r in results)

        return {"news_items": items, "news_fetching_failed": not any_success}
