from app.domain.models import NewsItem
from app.graph.state import GraphState
from app.ports.llm import LLMClient

SYSTEM_PROMPT = (
    "You are a market analyst. Summarize the following news items into a short, "
    "factual paragraph."
)


def _group_by_entity(items: list[NewsItem]) -> dict[str, list[NewsItem]]:
    grouped: dict[str, list[NewsItem]] = {}
    for item in items:
        grouped.setdefault(item.related_entity, []).append(item)
    return grouped


class BriefingNode:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def __call__(self, state: GraphState) -> GraphState:
        grouped = _group_by_entity(state.get("curated_items", []))

        summaries: dict[str, str] = {}
        for entity, entity_items in grouped.items():
            items_text = "\n".join(f"- {i.title}: {i.snippet}" for i in entity_items)
            try:
                summary = await self._llm.complete(system=SYSTEM_PROMPT, user=items_text)
            except Exception:
                continue
            if not isinstance(summary, str):
                continue
            summaries[entity] = summary

        briefing_failed = bool(grouped) and not summaries
        return {"category_summaries": summaries, "briefing_failed": briefing_failed}
