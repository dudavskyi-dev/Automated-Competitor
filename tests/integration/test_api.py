import asyncio
import time

from fastapi.testclient import TestClient

from app.api.main import app, get_graph, get_job_store
from app.domain.models import CompanyContext
from app.graph.build_graph import build_graph
from app.graph.nodes.competitor_finder import _CompetitorListResponse
from app.jobs.job_store import InMemoryJobStore
from app.ports.scraper import ScrapedPage
from tests.fakes.fake_llm import FakeLLM
from tests.fakes.fake_scraper import FakeScraper
from tests.fakes.fake_search import FakeSearch

# Pydantic's HttpUrl normalizes bare-domain URLs by appending a trailing slash,
# so this must match what str(HttpUrl("https://acme.example.com")) produces —
# that's what the API actually passes to the graph.
SOURCE_URL = "https://acme.example.com/"


def make_fake_graph() -> object:
    page = ScrapedPage(
        url=SOURCE_URL,
        markdown="# Acme\nWe help teams plan sprints.",
        title="Acme",
        status_code=200,
    )
    scraper = FakeScraper(pages={SOURCE_URL: page})
    context = CompanyContext(
        source_url=SOURCE_URL,
        domain="B2B SaaS for project management",
        target_audience="small dev teams",
        value_proposition="faster sprint planning",
        keywords=["project management"],
    )
    search = FakeSearch()
    llm = FakeLLM(
        responses=[
            context,
            _CompetitorListResponse(competitors=[]),
            "# Weekly Brief\n\nNothing new.",
        ]
    )
    return build_graph(scraper=scraper, search=search, llm=llm)


def make_fake_graph_context_extraction_fails() -> object:
    page = ScrapedPage(
        url=SOURCE_URL,
        markdown="# Acme\nWe help teams plan sprints.",
        title="Acme",
        status_code=200,
    )
    scraper = FakeScraper(pages={SOURCE_URL: page})
    search = FakeSearch()
    # Not a CompanyContext instance -> context_extractor's isinstance check fails,
    # mirroring the real "LLM echoed the schema instead of filling it in" failure.
    llm = FakeLLM(responses=["not valid company-context json"])
    return build_graph(scraper=scraper, search=search, llm=llm)


def poll_until_done(client: TestClient, job_id: str, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/research/{job_id}/status")
        body = response.json()
        if body["status"] in ("done", "error"):
            return body
        time.sleep(0.02)
    raise TimeoutError("job did not finish in time")


class TestResearchApi:
    def test_full_happy_path(self) -> None:
        store = InMemoryJobStore()
        app.dependency_overrides[get_graph] = make_fake_graph
        app.dependency_overrides[get_job_store] = lambda: store
        try:
            with TestClient(app) as client:
                create_response = client.post("/research", json={"url": SOURCE_URL})
                assert create_response.status_code == 200
                job_id = create_response.json()["job_id"]

                status_body = poll_until_done(client, job_id)
                assert status_body["status"] == "done"

                report_response = client.get(f"/research/{job_id}/report")
                assert report_response.status_code == 200
                brief = report_response.json()
                assert brief["summary_markdown"] == "# Weekly Brief\n\nNothing new."
        finally:
            app.dependency_overrides.clear()

    def test_job_with_no_brief_becomes_error(self) -> None:
        store = InMemoryJobStore()
        app.dependency_overrides[get_graph] = make_fake_graph_context_extraction_fails
        app.dependency_overrides[get_job_store] = lambda: store
        try:
            with TestClient(app) as client:
                create_response = client.post("/research", json={"url": SOURCE_URL})
                assert create_response.status_code == 200
                job_id = create_response.json()["job_id"]

                status_body = poll_until_done(client, job_id)
                assert status_body["status"] == "error"

                report_response = client.get(f"/research/{job_id}/report")
                assert report_response.status_code == 500
                assert "monitoring brief" in report_response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_status_for_unknown_job_returns_404(self) -> None:
        app.dependency_overrides[get_job_store] = lambda: InMemoryJobStore()
        try:
            with TestClient(app) as client:
                response = client.get("/research/unknown-id/status")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_report_for_unknown_job_returns_404(self) -> None:
        app.dependency_overrides[get_job_store] = lambda: InMemoryJobStore()
        try:
            with TestClient(app) as client:
                response = client.get("/research/unknown-id/report")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_report_before_done_returns_409(self) -> None:
        # Seed a pending job directly instead of racing the background task —
        # timing-based "check immediately after POST" is inherently flaky.
        store = InMemoryJobStore()
        job = asyncio.run(store.create())
        app.dependency_overrides[get_job_store] = lambda: store
        try:
            with TestClient(app) as client:
                report_response = client.get(f"/research/{job.id}/report")

            assert report_response.status_code == 409
        finally:
            app.dependency_overrides.clear()
