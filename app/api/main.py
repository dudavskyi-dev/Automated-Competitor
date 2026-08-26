import asyncio
import os
from typing import Any

import structlog
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from app.adapters.crawl4ai_scraper import Crawl4AIScraper
from app.adapters.duckduckgo_search import DuckDuckGoSearch
from app.adapters.openrouter_llm import OpenRouterClient
from app.domain.models import MonitoringBrief
from app.graph.build_graph import build_graph
from app.jobs.job_store import InMemoryJobStore, Job, JobStatus, JobStore

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

app = FastAPI(title="Competitive Intelligence Pipeline")

_background_tasks: set[Any] = set()
_job_store: JobStore | None = None
_graph: Any = None


def get_job_store() -> JobStore:
    global _job_store
    if _job_store is None:
        _job_store = InMemoryJobStore()
    return _job_store


def get_graph() -> Any:
    global _graph
    if _graph is None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        _graph = build_graph(
            scraper=Crawl4AIScraper(),
            search=DuckDuckGoSearch(),
            llm=OpenRouterClient(api_key=api_key),
        )
    return _graph


class ResearchRequest(BaseModel):
    url: HttpUrl


class ResearchResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    status: JobStatus
    current_step: str | None


async def _run_job(job_id: str, url: str, store: JobStore, graph: Any) -> None:
    job = await store.get(job_id)
    if job is None:
        return

    job.status = JobStatus.RUNNING
    await store.save(job)

    state: dict[str, Any] = {"source_url": url}
    try:
        async for step in graph.astream(state):
            node_name, update = next(iter(step.items()))
            state.update(update)
            job.current_step = node_name
            await store.save(job)
    except Exception as exc:
        job.status = JobStatus.ERROR
        job.error = str(exc)
        await store.save(job)
        return

    job.status = JobStatus.DONE
    job.brief = state.get("brief")
    await store.save(job)


@app.post("/research")
async def start_research(
    request: ResearchRequest,
    store: JobStore = Depends(get_job_store),
    graph: Any = Depends(get_graph),
) -> ResearchResponse:
    job = await store.create()
    task = asyncio.create_task(_run_job(job.id, str(request.url), store, graph))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return ResearchResponse(job_id=job.id)


@app.get("/research/{job_id}/status")
async def get_status(
    job_id: str, store: JobStore = Depends(get_job_store)
) -> StatusResponse:
    job = await _get_job_or_404(job_id, store)
    return StatusResponse(status=job.status, current_step=job.current_step)


@app.get("/research/{job_id}/report")
async def get_report(
    job_id: str, store: JobStore = Depends(get_job_store)
) -> MonitoringBrief:
    job = await _get_job_or_404(job_id, store)

    if job.status == JobStatus.ERROR:
        raise HTTPException(status_code=500, detail=job.error or "Job failed")
    if job.status != JobStatus.DONE or job.brief is None:
        raise HTTPException(status_code=409, detail="Job is not finished yet")
    return job.brief


async def _get_job_or_404(job_id: str, store: JobStore) -> Job:
    job = await store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
