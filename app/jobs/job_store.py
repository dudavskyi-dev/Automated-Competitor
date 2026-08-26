import asyncio
from enum import StrEnum
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel

from app.domain.models import MonitoringBrief


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class Job(BaseModel):
    id: str
    status: JobStatus = JobStatus.PENDING
    current_step: str | None = None
    brief: MonitoringBrief | None = None
    error: str | None = None


class JobStore(Protocol):
    async def create(self) -> Job: ...
    async def get(self, job_id: str) -> Job | None: ...
    async def save(self, job: Job) -> None: ...


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def create(self) -> Job:
        job = Job(id=str(uuid4()))
        async with self._lock:
            self._jobs[job.id] = job
        return job

    async def get(self, job_id: str) -> Job | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def save(self, job: Job) -> None:
        async with self._lock:
            self._jobs[job.id] = job
