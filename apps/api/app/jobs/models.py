from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


@dataclass
class JobError:
    code: str
    message: str


@dataclass
class Job:
    id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.queued
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: JobError | None = None
    result: dict[str, Any] | None = None
