"""Manual, real-network smoke test for the full pipeline. Not run in CI.

Usage:
    winget install --id Ollama.Ollama -e   # one-time, installs the local Ollama server
    ollama pull qwen2.5:3b                 # one-time, pulls the default local model
    uv run crawl4ai-setup                  # one-time, installs browser deps for crawl4ai
    uv run python scripts/smoke_test.py [URL]

Set OPENAI_API_KEY in .env instead to use OpenAI rather than the local Ollama setup.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

from app.adapters.crawl4ai_scraper import Crawl4AIScraper
from app.adapters.duckduckgo_search import DuckDuckGoSearch
from app.adapters.llm_factory import build_llm_client
from app.graph.build_graph import build_graph

FAILURE_FLAGS = (
    "scrape_failed",
    "context_extraction_failed",
    "competitor_finding_failed",
    "news_fetching_failed",
    "briefing_failed",
    "editor_failed",
)


async def main() -> None:
    load_dotenv()

    url = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SMOKE_TEST_URL")
    if not url:
        print("No URL given: pass one as an argument or set SMOKE_TEST_URL.", file=sys.stderr)
        raise SystemExit(1)

    graph = build_graph(
        scraper=Crawl4AIScraper(),
        search=DuckDuckGoSearch(),
        llm=build_llm_client(),
    )

    print(f"Running pipeline for {url} ...\n")
    result = await graph.ainvoke({"source_url": url})

    for flag in FAILURE_FLAGS:
        print(f"{flag}: {result.get(flag)}")

    brief = result.get("brief")
    if brief is None:
        print("\nNo brief was produced.", file=sys.stderr)
        raise SystemExit(1)

    print(f"\nFound {len(brief.competitors)} competitors, {len(brief.items)} news items.")
    print("\n--- summary_markdown ---\n")
    print(brief.summary_markdown)


if __name__ == "__main__":
    asyncio.run(main())
