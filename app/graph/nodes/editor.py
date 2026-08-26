from collections.abc import Callable
from datetime import UTC, datetime

from app.domain.models import MonitoringBrief
from app.graph.logging_utils import log_node
from app.graph.state import GraphState
from app.ports.llm import LLMClient

SYSTEM_PROMPT = (
    "You are an editor. Combine the following category summaries into one "
    "well-formatted markdown monitoring brief."
)


def _fallback_markdown(summaries: dict[str, str]) -> str:
    if not summaries:
        return "# Monitoring Brief\n\nNo summaries available."
    sections = [f"## {entity}\n\n{summary}" for entity, summary in summaries.items()]
    return "# Monitoring Brief\n\n" + "\n\n".join(sections)


class EditorNode:
    def __init__(
        self, llm: LLMClient, clock: Callable[[], datetime] = lambda: datetime.now(UTC)
    ) -> None:
        self._llm = llm
        self._clock = clock

    @log_node("editor")
    async def __call__(self, state: GraphState) -> GraphState:
        context = state.get("company_context")
        if state.get("context_extraction_failed") or context is None:
            return {"brief": None, "editor_failed": True}

        summaries = state.get("category_summaries", {})
        summaries_text = "\n".join(f"{entity}: {summary}" for entity, summary in summaries.items())

        try:
            markdown = await self._llm.complete(system=SYSTEM_PROMPT, user=summaries_text)
        except Exception:
            markdown = _fallback_markdown(summaries)

        if not isinstance(markdown, str):
            markdown = _fallback_markdown(summaries)

        brief = MonitoringBrief(
            company=context,
            competitors=state.get("competitors", []),
            items=state.get("curated_items", []),
            generated_at=self._clock(),
            summary_markdown=markdown,
        )
        return {"brief": brief, "editor_failed": False}
