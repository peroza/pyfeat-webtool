from datetime import datetime, timedelta, timezone

from app.jobs.models import JobStatus
from app.jobs.store import InMemoryJobStore


def test_create_and_get_job():
    store = InMemoryJobStore(ttl_seconds=60)
    job = store.create()
    assert job.status == JobStatus.queued
    assert store.get(job.id) is job


def test_update_status():
    store = InMemoryJobStore(ttl_seconds=60)
    job = store.create()
    store.update(job.id, status=JobStatus.running)
    assert store.get(job.id).status == JobStatus.running


def test_unknown_job_returns_none():
    store = InMemoryJobStore(ttl_seconds=60)
    assert store.get("missing") is None


def test_purge_expired_removes_old_jobs():
    store = InMemoryJobStore(ttl_seconds=10)
    job = store.create()
    job.created_at = datetime.now(timezone.utc) - timedelta(seconds=30)
    store.purge_expired(datetime.now(timezone.utc))
    assert store.get(job.id) is None
