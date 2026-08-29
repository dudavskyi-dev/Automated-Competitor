from app.domain.models import CompanyContext
from app.graph.logging_utils import log_node
from app.graph.state import GraphState
from app.ports.llm import LLMClient

SYSTEM_PROMPT = (
    "You are a business analyst. Given a company website's markdown content, "
    "extract its company name, domain, target audience, value proposition, and "
    "keywords describing main fields of the company."
)


class ContextExtractorNode:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    @log_node("context_extractor")
    async def __call__(self, state: GraphState) -> GraphState:
        page = state.get("scraped_page")
        if state.get("scrape_failed") or page is None:
            return {"company_context": None, "context_extraction_failed": True}

        try:
            context = await self._llm.complete(
                system=SYSTEM_PROMPT,
                user=page.markdown,
                response_model=CompanyContext,
            )
        except Exception:
            return {"company_context": None, "context_extraction_failed": True}

        if not isinstance(context, CompanyContext):
            return {"company_context": None, "context_extraction_failed": True}

        return {"company_context": context, "context_extraction_failed": False}
