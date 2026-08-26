from app.graph.logging_utils import log_node
from app.graph.state import GraphState


class CuratorNode:
    @log_node("curator")
    async def __call__(self, state: GraphState) -> GraphState:
        seen_urls: set[str] = set()
        curated = []
        for item in state.get("news_items", []):
            if not item.title.strip() or not item.snippet.strip():
                continue
            url = str(item.url)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            curated.append(item)

        return {"curated_items": curated}
