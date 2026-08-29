from pydantic import BaseModel

from app.domain.models import Competitor
from app.graph.logging_utils import log_node
from app.graph.state import GraphState
from app.ports.llm import LLMClient
from app.ports.scraper import WebScraper
from app.ports.search import WebSearch

IDENTIFY_SYSTEM_PROMPT = (
    "You are a market research analyst. Given a company's profile and a list of "
    "web search results, identify the names of 5-7 real top competitors."
)

DESCRIBE_SYSTEM_PROMPT = (
    "You are a market research analyst. Given a competitor company's official website "
    "content, write one short, factual sentence describing what they do."
)

# Local LLM inference slows down a lot with long inputs - a competitor's homepage
# markdown can be huge, and we only need enough of it to write one sentence.
MAX_DESCRIBE_MARKDOWN_CHARS = 4000


class _CompetitorNameListResponse(BaseModel):
    names: list[str]


class CompetitorFinderNode:
    def __init__(self, search: WebSearch, scraper: WebScraper, llm: LLMClient) -> None:
        self._search = search
        self._scraper = scraper
        self._llm = llm

    @log_node("competitor_finder")
    async def __call__(self, state: GraphState) -> GraphState:
        context = state.get("company_context")
        if state.get("context_extraction_failed") or context is None:
            return {"competitors": [], "competitor_finding_failed": True}

        identify_query = f'"{context.company_name}" competitors'

        try:
            search_results = await self._search.search(identify_query, max_results=2)
        except Exception:
            return {"competitors": [], "competitor_finding_failed": True}

        results_text = "\n".join(f"- {r.title} ({r.url}): {r.snippet}" for r in search_results)
        identify_prompt = (
            f"Company name: {context.company_name}\n"
            f"Company domain: {context.domain}\n"
            f"Value proposition: {context.value_proposition}\n"
            f"Search results:\n{results_text}"
        )

        try:
            response = await self._llm.complete(
                system=IDENTIFY_SYSTEM_PROMPT,
                user=identify_prompt,
                response_model=_CompetitorNameListResponse,
            )
        except Exception:
            return {"competitors": [], "competitor_finding_failed": True}

        if not isinstance(response, _CompetitorNameListResponse):
            return {"competitors": [], "competitor_finding_failed": True}

        competitors: list[Competitor] = []
        seen_names: set[str] = {context.company_name.strip().lower()}
        for raw_name in response.names:
            name = raw_name.strip()
            if not name or name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            competitors.append(await self._describe_competitor(name, context.company_name))

        return {"competitors": competitors, "competitor_finding_failed": False}

    async def _describe_competitor(self, name: str, company_name: str) -> Competitor:
        fallback_reason = f"Identified as a competitor of {company_name}."
        try:
            site_results = await self._search.search(f"{name} official website", max_results=1)
        except Exception:
            return Competitor(name=name, url=None, reason=fallback_reason)

        if not site_results:
            return Competitor(name=name, url=None, reason=fallback_reason)

        site = site_results[0]
        fallback_reason = site.snippet or fallback_reason

        try:
            page = await self._scraper.fetch_markdown(str(site.url))
        except Exception:
            return Competitor(name=name, url=site.url, reason=fallback_reason)

        try:
            description = await self._llm.complete(
                system=DESCRIBE_SYSTEM_PROMPT,
                user=page.markdown[:MAX_DESCRIBE_MARKDOWN_CHARS],
            )
        except Exception:
            return Competitor(name=name, url=site.url, reason=fallback_reason)

        if not isinstance(description, str) or not description.strip():
            return Competitor(name=name, url=site.url, reason=fallback_reason)

        return Competitor(name=name, url=site.url, reason=description.strip())
