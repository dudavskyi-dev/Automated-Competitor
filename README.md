# Competitive Intelligence Pipeline

Given a company website URL, the system extracts business context, finds relevant
competitors, and on request assembles a monitoring brief (news about the company,
its competitors, and the industry). Runs are user-triggered (polling job).

Full specification and phased development plan: [spec_and_plan.md](spec_and_plan.md).

## Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph |
| Website scraping | crawl4ai |
| Web search | duckduckgo-search (`ddgs`), behind an interface swappable for SearXNG |
| LLM | OpenRouter (OpenAI-compatible API) |
| Backend | FastAPI (async) |
| Job storage | in-memory dict behind a `JobStore` interface |
| Tests | pytest + pytest-asyncio + respx/responses |

Every external service (scraper, search, LLM) is hidden behind its own Python
interface (`Protocol`), so the graph and API can be tested without real network calls.

## Repository layout

```
app/
├── domain/    # Pydantic data models
├── ports/     # Protocol interfaces for external services
├── adapters/  # port implementations (crawl4ai, duckduckgo, openrouter)
├── graph/     # LangGraph nodes and graph assembly
├── jobs/      # job storage
└── api/       # FastAPI routes
tests/
├── unit/          # nodes and adapters with mocks/fakes
├── integration/   # full graph, API endpoints
└── contract/      # Pydantic model validation
scripts/           # manual smoke tests (not run in CI)
```

## Development

Dependency manager: [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-groups   # install dependencies
uv run pytest          # run tests
uv run ruff check .    # lint
uv run mypy app        # type check
```

CI (`.github/workflows/ci.yml`) runs lint + mypy + pytest on every push and pull request.
