from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Lock

from app.jobs.models import Job


def _snapshot_job(job: Job) -> Job:
    return replace(
        job,
        error=replace(job.error) if job.error is not None else None,
        result=deepcopy(job.result) if job.result is not None else None,
    )


class InMemoryJobStore:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()

    def create(self) -> Job:
        job = Job()
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return _snapshot_job(job)

    def update(self, job_id: str, **fields: object) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            for key, value in fields.items():
                setattr(job, key, value)
            return _snapshot_job(job)

    def purge_expired(self, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        with self._lock:
            expired = [
                jid
                for jid, job in self._jobs.items()
                if now - job.created_at > self._ttl
            ]
            for jid in expired:
                del self._jobs[jid]
