from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.nodes.briefing import BriefingNode
from app.graph.nodes.competitor_finder import CompetitorFinderNode
from app.graph.nodes.context_extractor import ContextExtractorNode
from app.graph.nodes.curator import CuratorNode
from app.graph.nodes.editor import EditorNode
from app.graph.nodes.news_fetcher import NewsFetcherNode
from app.graph.nodes.website_scraper import WebsiteScraperNode
from app.graph.state import GraphState
from app.ports.llm import LLMClient
from app.ports.scraper import WebScraper
from app.ports.search import WebSearch


def build_graph(
    scraper: WebScraper, search: WebSearch, llm: LLMClient
) -> CompiledStateGraph[GraphState, None, GraphState, GraphState]:
    graph: StateGraph[GraphState] = StateGraph(GraphState)

    graph.add_node("website_scraper", WebsiteScraperNode(scraper))
    graph.add_node("context_extractor", ContextExtractorNode(llm))
    graph.add_node("competitor_finder", CompetitorFinderNode(search, scraper, llm))
    graph.add_node("news_fetcher", NewsFetcherNode(search))
    graph.add_node("curator", CuratorNode())
    graph.add_node("briefing", BriefingNode(llm))
    graph.add_node("editor", EditorNode(llm))

    graph.add_edge(START, "website_scraper")
    graph.add_edge("website_scraper", "context_extractor")
    graph.add_edge("context_extractor", "competitor_finder")
    graph.add_edge("competitor_finder", "news_fetcher")
    graph.add_edge("news_fetcher", "curator")
    graph.add_edge("curator", "briefing")
    graph.add_edge("briefing", "editor")
    graph.add_edge("editor", END)

    return graph.compile()
