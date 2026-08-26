from pydantic import BaseModel

from app.domain.models import Competitor
from app.graph.state import GraphState
from app.ports.llm import LLMClient
from app.ports.search import WebSearch

SYSTEM_PROMPT = (
    "You are a market research analyst. Given a company's profile and a list of "
    "web search results, identify 3-5 real competitors with a short reason each."
)


class _CompetitorListResponse(BaseModel):
    competitors: list[Competitor]


class CompetitorFinderNode:
    def __init__(self, search: WebSearch, llm: LLMClient) -> None:
        self._search = search
        self._llm = llm

    async def __call__(self, state: GraphState) -> GraphState:
        context = state.get("company_context")
        if state.get("context_extraction_failed") or context is None:
            return {"competitors": [], "competitor_finding_failed": True}

        query = f"{' '.join(context.keywords)} competitors"

        try:
            search_results = await self._search.search(query)
        except Exception:
            return {"competitors": [], "competitor_finding_failed": True}

        results_text = "\n".join(f"- {r.title} ({r.url}): {r.snippet}" for r in search_results)
        user_prompt = (
            f"Company domain: {context.domain}\n"
            f"Value proposition: {context.value_proposition}\n"
            f"Search results:\n{results_text}"
        )

        try:
            response = await self._llm.complete(
                system=SYSTEM_PROMPT,
                user=user_prompt,
                response_model=_CompetitorListResponse,
            )
        except Exception:
            return {"competitors": [], "competitor_finding_failed": True}

        if not isinstance(response, _CompetitorListResponse):
            return {"competitors": [], "competitor_finding_failed": True}

        return {"competitors": response.competitors, "competitor_finding_failed": False}
