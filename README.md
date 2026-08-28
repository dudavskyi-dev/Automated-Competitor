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
| LLM | Ollama (local, `qwen2.5:3b` by default) |
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
├── adapters/  # port implementations (crawl4ai, duckduckgo, ollama)
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

### Local LLM setup

The pipeline's LLM calls run against a local [Ollama](https://ollama.com) server — no API key
required. One-time setup:

```bash
winget install --id Ollama.Ollama -e
ollama pull qwen2.5:3b
```

`OLLAMA_MODEL` and `OLLAMA_HOST` in `.env` are optional overrides; the adapter's own defaults
already match the command above.

## Frontend (dev)

A React + Vite + TypeScript UI lives in `frontend/`. Run backend and frontend as two
local processes:

```bash
# terminal 1 — backend
uv run uvicorn app.api.main:app --reload

# terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Vite's dev server proxies `/research*` requests to `http://localhost:8000`, so the
frontend can call relative API paths with no CORS configuration needed on the
backend. This is a local dev-only setup — there's no production bundling/serving
story yet.
