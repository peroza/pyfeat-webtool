# Py-FEAT Web Interface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a monorepo with a Next.js + shadcn upload UI and a FastAPI job API that runs Py-FEAT on face images and returns emotions, AUs, landmarks, and an overlay.

**Architecture:** Browser talks to Next.js; Next.js calls FastAPI over HTTP. FastAPI owns an in-memory job store, runs Py-FEAT in a bounded executor, and returns results via `GET /v1/jobs/{id}`. The UI polls until success/failure. No auth, no persistence beyond a short TTL.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, Pillow, NumPy, py-feat; Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui; Docker Compose; pytest + httpx; Vitest + Testing Library for web.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-18-pyfeat-web-interface-design.md`
- API base path: `/v1`; endpoints `POST /v1/analyze` (202 + `job_id`) and `GET /v1/jobs/{job_id}`
- Image only: JPEG/PNG/WebP, max 10 MB; ephemeral jobs, TTL default 20 minutes
- Primary face = largest bbox; overlay = landmarks required; no auth; no video in v1
- Never import Py-FEAT in the web app; mock Detector in unit tests
- Conventional commits; frequent small commits per task

---

## File Structure

```
apps/api/
  pyproject.toml
  README.md
  Dockerfile
  app/
    __init__.py
    main.py                 # FastAPI app, lifespan, CORS, routers
    settings.py             # env config
    schemas.py              # request/response Pydantic models
    jobs/
      __init__.py
      store.py              # InMemoryJobStore
      models.py             # Job dataclass / status enum
      runner.py             # schedule + execute analysis in executor
    imaging/
      __init__.py
      validate.py           # decode bytes → RGB ndarray
      overlay.py            # draw landmarks → PNG base64
    analysis/
      __init__.py
      types.py              # AnalysisResult dataclass
      protocol.py           # FaceAnalyzer Protocol
      primary.py            # pick largest face
      pyfeat.py             # PyFeatAnalyzer wrapping Detector
      stub.py               # StubAnalyzer for tests / boot without models
  tests/
    conftest.py
    test_job_store.py
    test_validate_image.py
    test_overlay.py
    test_primary_face.py
    test_analyze_api.py
    test_jobs_api.py
    fixtures/
      tiny.png              # generated in test setup if needed

apps/web/
  package.json
  next.config.ts
  tailwind.config.ts
  components.json
  src/
    app/
      layout.tsx
      page.tsx
      globals.css
    components/
      ui/                   # shadcn primitives
      image-upload.tsx
      analysis-progress.tsx
      results-panel.tsx
      emotion-bars.tsx
      action-unit-table.tsx
      overlay-preview.tsx
    lib/
      api.ts                # submitAnalyze, getJob
      types.ts              # JobStatus, AnalysisResult, etc.
      poll-job.ts           # backoff polling helper
      constants.ts          # MAX_BYTES, ACCEPT types
    hooks/
      use-analysis.ts       # idle→ready→submitting→polling→succeeded|failed
  vitest.config.ts
  src/
    lib/
      poll-job.test.ts
      api.test.ts
    hooks/
      use-analysis.test.ts

docker-compose.yml
.gitignore
README.md
```

---

### Task 1: API project scaffold + health endpoint

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/app/__init__.py`
- Create: `apps/api/app/settings.py`
- Create: `apps/api/app/main.py`
- Create: `apps/api/tests/conftest.py`
- Create: `apps/api/tests/test_health.py`
- Create: `.gitignore` (root)

**Interfaces:**
- Consumes: nothing
- Produces: FastAPI app factory `create_app() -> FastAPI`; settings via `get_settings()`; `GET /health` → `{ "status": "ok" }`

- [ ] **Step 1: Write the failing health test**

```python
# apps/api/tests/test_health.py
from fastapi.testclient import TestClient
from app.main import create_app

def test_health_returns_ok():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/api && python -m pytest tests/test_health.py -v`  
Expected: FAIL (module/app not found or import error)

- [ ] **Step 3: Add project files and minimal app**

```toml
# apps/api/pyproject.toml
[project]
name = "pyfeat-api"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.32.0",
  "python-multipart>=0.0.12",
  "pydantic-settings>=2.6.0",
  "pillow>=10.0.0",
  "numpy>=1.26.0",
  "py-feat>=0.6.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "httpx>=0.27.0"]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

```python
# apps/api/app/settings.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PYFEAT_")

    max_upload_bytes: int = 10 * 1024 * 1024
    job_ttl_seconds: int = 20 * 60
    worker_pool_size: int = 1
    cors_origins: str = "http://localhost:3000"
    use_stub_analyzer: bool = False  # True in unit tests via fixture

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

```python
# apps/api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.settings import get_settings

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Py-FEAT Analysis API", version="0.1.0")
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
```

```python
# apps/api/tests/conftest.py
import pytest
from app.settings import get_settings

@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
```

Root `.gitignore` should include at least: `node_modules/`, `.next/`, `__pycache__/`, `.venv/`, `*.pyc`, `.env`, `dist/`, `.DS_Store`.

- [ ] **Step 4: Install deps and run test**

Run:
```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/test_health.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .gitignore apps/api
git commit -m "chore: scaffold FastAPI app with health endpoint"
```

---

### Task 2: Job models and in-memory store

**Files:**
- Create: `apps/api/app/jobs/__init__.py`
- Create: `apps/api/app/jobs/models.py`
- Create: `apps/api/app/jobs/store.py`
- Create: `apps/api/app/schemas.py`
- Create: `apps/api/tests/test_job_store.py`

**Interfaces:**
- Consumes: `Settings.job_ttl_seconds`
- Produces:
  - `JobStatus` enum: `queued | running | succeeded | failed`
  - `JobError(code: str, message: str)`
  - `AnalysisResultData` (Pydantic): `face_count`, `emotions: dict[str, float]`, `action_units: dict[str, float]`, `landmarks: list[list[float]]`, `overlay_image_base64: str`
  - `Job` dataclass with `id`, `status`, `created_at`, `error`, `result`
  - `InMemoryJobStore.create() -> Job`, `get(job_id) -> Job | None`, `update(job_id, **fields)`, `purge_expired(now)`

- [ ] **Step 1: Write failing store tests**

```python
# apps/api/tests/test_job_store.py
from datetime import datetime, timedelta, timezone
from app.jobs.store import InMemoryJobStore
from app.jobs.models import JobStatus

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
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `cd apps/api && pytest tests/test_job_store.py -v`  
Expected: FAIL (imports missing)

- [ ] **Step 3: Implement models, schemas, store**

```python
# apps/api/app/jobs/models.py
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
```

```python
# apps/api/app/schemas.py
from pydantic import BaseModel, Field
from app.jobs.models import JobStatus

class AnalyzeAccepted(BaseModel):
    job_id: str

class JobErrorSchema(BaseModel):
    code: str
    message: str

class AnalysisResultSchema(BaseModel):
    face_count: int
    emotions: dict[str, float]
    action_units: dict[str, float]
    landmarks: list[list[float]]
    overlay_image_base64: str

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    error: JobErrorSchema | None = None
    result: AnalysisResultSchema | None = None
```

```python
# apps/api/app/jobs/store.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from threading import Lock
from app.jobs.models import Job, JobStatus

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
            return self._jobs.get(job_id)

    def update(self, job_id: str, **fields: object) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            for key, value in fields.items():
                setattr(job, key, value)
            return job

    def purge_expired(self, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        with self._lock:
            expired = [
                jid for jid, job in self._jobs.items()
                if now - job.created_at > self._ttl
            ]
            for jid in expired:
                del self._jobs[jid]
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `pytest tests/test_job_store.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/jobs apps/api/app/schemas.py apps/api/tests/test_job_store.py
git commit -m "feat(api): add in-memory job store and schemas"
```

---

### Task 3: Image validation

**Files:**
- Create: `apps/api/app/imaging/__init__.py`
- Create: `apps/api/app/imaging/validate.py`
- Create: `apps/api/tests/test_validate_image.py`

**Interfaces:**
- Consumes: raw `bytes`, `max_bytes: int`
- Produces: `decode_image(data: bytes, max_bytes: int) -> np.ndarray` (H×W×3 RGB uint8); raises `ImageValidationError(code, message)` with codes `invalid_image`

- [ ] **Step 1: Write failing validation tests**

```python
# apps/api/tests/test_validate_image.py
import io
import pytest
from PIL import Image
from app.imaging.validate import decode_image, ImageValidationError

def _png_bytes(size=(32, 32), color=(255, 0, 0)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()

def test_decode_valid_png():
    arr = decode_image(_png_bytes(), max_bytes=10_000_000)
    assert arr.shape == (32, 32, 3)

def test_reject_oversized():
    data = _png_bytes()
    with pytest.raises(ImageValidationError) as exc:
        decode_image(data, max_bytes=10)
    assert exc.value.code == "invalid_image"

def test_reject_garbage():
    with pytest.raises(ImageValidationError) as exc:
        decode_image(b"not-an-image", max_bytes=10_000_000)
    assert exc.value.code == "invalid_image"
```

- [ ] **Step 2: Run — expect FAIL**

Run: `pytest tests/test_validate_image.py -v`

- [ ] **Step 3: Implement validation**

```python
# apps/api/app/imaging/validate.py
from __future__ import annotations
import io
import numpy as np
from PIL import Image

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

class ImageValidationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

def decode_image(data: bytes, max_bytes: int) -> np.ndarray:
    if len(data) == 0 or len(data) > max_bytes:
        raise ImageValidationError(
            "invalid_image",
            "Image is empty or exceeds the maximum allowed size.",
        )
    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.format not in ALLOWED_FORMATS:
                raise ImageValidationError(
                    "invalid_image",
                    "Unsupported image format. Use JPEG, PNG, or WebP.",
                )
            rgb = img.convert("RGB")
            return np.asarray(rgb)
    except ImageValidationError:
        raise
    except Exception as exc:
        raise ImageValidationError(
            "invalid_image",
            "Could not decode image. Use a valid JPEG, PNG, or WebP file.",
        ) from exc
```

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/imaging apps/api/tests/test_validate_image.py
git commit -m "feat(api): validate and decode uploaded images"
```

---

### Task 4: Primary-face selection, overlay, and analysis types

**Files:**
- Create: `apps/api/app/analysis/__init__.py`
- Create: `apps/api/app/analysis/types.py`
- Create: `apps/api/app/analysis/protocol.py`
- Create: `apps/api/app/analysis/primary.py`
- Create: `apps/api/app/analysis/stub.py`
- Create: `apps/api/app/imaging/overlay.py`
- Create: `apps/api/tests/test_primary_face.py`
- Create: `apps/api/tests/test_overlay.py`

**Interfaces:**
- Consumes: face detections with `bbox: tuple[float,float,float,float]` (x, y, w, h)
- Produces:
  - `FaceDetection`, `RawAnalysis` dataclasses
  - `FaceAnalyzer` Protocol: `analyze(image_rgb: np.ndarray) -> RawAnalysis`
  - `select_primary_face(faces: list[FaceDetection]) -> FaceDetection | None`
  - `render_landmark_overlay(image_rgb, landmarks: list[tuple[float,float]]) -> str` (base64 PNG, no data-URL prefix)
  - `StubAnalyzer` for deterministic tests

- [ ] **Step 1: Write failing tests**

```python
# apps/api/tests/test_primary_face.py
from app.analysis.primary import select_primary_face
from app.analysis.types import FaceDetection

def test_selects_largest_bbox():
    faces = [
        FaceDetection(bbox=(0, 0, 10, 10), emotions={}, action_units={}, landmarks=[]),
        FaceDetection(bbox=(0, 0, 50, 50), emotions={"happiness": 0.9}, action_units={}, landmarks=[(1.0, 2.0)]),
    ]
    primary = select_primary_face(faces)
    assert primary is not None
    assert primary.bbox == (0, 0, 50, 50)

def test_empty_returns_none():
    assert select_primary_face([]) is None
```

```python
# apps/api/tests/test_overlay.py
import base64
import io
import numpy as np
from PIL import Image
from app.imaging.overlay import render_landmark_overlay

def test_overlay_returns_png_base64():
    image = np.zeros((40, 40, 3), dtype=np.uint8)
    b64 = render_landmark_overlay(image, [(10.0, 10.0), (20.0, 20.0)])
    raw = base64.b64decode(b64)
    with Image.open(io.BytesIO(raw)) as img:
        assert img.format == "PNG"
        assert img.size == (40, 40)
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement**

```python
# apps/api/app/analysis/types.py
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class FaceDetection:
    bbox: tuple[float, float, float, float]  # x, y, w, h
    emotions: dict[str, float]
    action_units: dict[str, float]
    landmarks: list[tuple[float, float]]

@dataclass
class RawAnalysis:
    faces: list[FaceDetection] = field(default_factory=list)
```

```python
# apps/api/app/analysis/protocol.py
from typing import Protocol
import numpy as np
from app.analysis.types import RawAnalysis

class FaceAnalyzer(Protocol):
    def analyze(self, image_rgb: np.ndarray) -> RawAnalysis:
        ...
```

```python
# apps/api/app/analysis/primary.py
from app.analysis.types import FaceDetection

def select_primary_face(faces: list[FaceDetection]) -> FaceDetection | None:
    if not faces:
        return None
    return max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
```

```python
# apps/api/app/analysis/stub.py
import numpy as np
from app.analysis.types import FaceDetection, RawAnalysis

class StubAnalyzer:
    """Deterministic analyzer for tests and local UI work without models."""

    def analyze(self, image_rgb: np.ndarray) -> RawAnalysis:
        h, w = image_rgb.shape[:2]
        return RawAnalysis(
            faces=[
                FaceDetection(
                    bbox=(w * 0.25, h * 0.25, w * 0.5, h * 0.5),
                    emotions={
                        "anger": 0.01,
                        "disgust": 0.0,
                        "fear": 0.02,
                        "happiness": 0.85,
                        "sadness": 0.03,
                        "surprise": 0.04,
                        "neutral": 0.05,
                    },
                    action_units={"AU12": 0.91, "AU06": 0.4},
                    landmarks=[(w * 0.4, h * 0.4), (w * 0.6, h * 0.4), (w * 0.5, h * 0.6)],
                )
            ]
        )
```

```python
# apps/api/app/imaging/overlay.py
from __future__ import annotations
import base64
import io
import numpy as np
from PIL import Image, ImageDraw

def render_landmark_overlay(
    image_rgb: np.ndarray,
    landmarks: list[tuple[float, float]],
) -> str:
    image = Image.fromarray(image_rgb.copy())
    draw = ImageDraw.Draw(image)
    for x, y in landmarks:
        r = 2
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(0, 255, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
```

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/analysis apps/api/app/imaging/overlay.py apps/api/tests/test_primary_face.py apps/api/tests/test_overlay.py
git commit -m "feat(api): add face selection, overlay, and stub analyzer"
```

---

### Task 5: Job runner + analyze/jobs HTTP endpoints (stub analyzer)

**Files:**
- Create: `apps/api/app/jobs/runner.py`
- Create: `apps/api/app/api/__init__.py`
- Create: `apps/api/app/api/routes.py`
- Modify: `apps/api/app/main.py`
- Modify: `apps/api/tests/conftest.py`
- Create: `apps/api/tests/test_analyze_api.py`
- Create: `apps/api/tests/test_jobs_api.py`

**Interfaces:**
- Consumes: `InMemoryJobStore`, `FaceAnalyzer`, `decode_image`, `select_primary_face`, `render_landmark_overlay`
- Produces:
  - `JobRunner.submit(image_bytes: bytes) -> str` (job_id)
  - `POST /v1/analyze` → 202 `{ "job_id" }`
  - `GET /v1/jobs/{job_id}` → `JobResponse`
  - On no faces: job `failed` with `code=no_face`
  - On bad image at submit: HTTP 400 with safe message (validation before queue)

- [ ] **Step 1: Write failing API tests**

```python
# apps/api/tests/test_analyze_api.py
import io
import time
from PIL import Image
from fastapi.testclient import TestClient
from app.main import create_app

def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (10, 20, 30)).save(buf, format="PNG")
    return buf.getvalue()

def test_analyze_accepts_image_and_completes(monkeypatch):
    monkeypatch.setenv("PYFEAT_USE_STUB_ANALYZER", "true")
    from app.settings import get_settings
    get_settings.cache_clear()
    client = TestClient(create_app())
    response = client.post(
        "/v1/analyze",
        files={"image": ("face.png", _png(), "image/png")},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    result = None
    for _ in range(50):
        poll = client.get(f"/v1/jobs/{job_id}")
        assert poll.status_code == 200
        body = poll.json()
        if body["status"] in ("succeeded", "failed"):
            result = body
            break
        time.sleep(0.05)
    assert result is not None
    assert result["status"] == "succeeded"
    assert result["result"]["face_count"] == 1
    assert "happiness" in result["result"]["emotions"]
    assert result["result"]["overlay_image_base64"]

def test_analyze_rejects_garbage(monkeypatch):
    monkeypatch.setenv("PYFEAT_USE_STUB_ANALYZER", "true")
    from app.settings import get_settings
    get_settings.cache_clear()
    client = TestClient(create_app())
    response = client.post(
        "/v1/analyze",
        files={"image": ("bad.png", b"not-an-image", "image/png")},
    )
    assert response.status_code == 400

def test_unknown_job_404(monkeypatch):
    monkeypatch.setenv("PYFEAT_USE_STUB_ANALYZER", "true")
    from app.settings import get_settings
    get_settings.cache_clear()
    client = TestClient(create_app())
    assert client.get("/v1/jobs/does-not-exist").status_code == 404
```

Also add a no-face failure test (see Step 3 monkeypatch of `StubAnalyzer.analyze`).

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement runner, routes, wire lifespan**

```python
# apps/api/app/jobs/runner.py
from __future__ import annotations
import logging
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from app.analysis.primary import select_primary_face
from app.analysis.protocol import FaceAnalyzer
from app.imaging.overlay import render_landmark_overlay
from app.imaging.validate import ImageValidationError, decode_image
from app.jobs.models import JobError, JobStatus
from app.jobs.store import InMemoryJobStore

logger = logging.getLogger(__name__)

class JobRunner:
    def __init__(
        self,
        store: InMemoryJobStore,
        analyzer: FaceAnalyzer,
        max_upload_bytes: int,
        pool_size: int = 1,
    ) -> None:
        self._store = store
        self._analyzer = analyzer
        self._max_upload_bytes = max_upload_bytes
        self._executor = ThreadPoolExecutor(max_workers=pool_size)

    def submit(self, image_bytes: bytes) -> str:
        # Validate synchronously so bad uploads never become jobs
        image = decode_image(image_bytes, self._max_upload_bytes)
        job = self._store.create()
        self._executor.submit(self._run, job.id, image)
        return job.id

    def _run(self, job_id: str, image: np.ndarray) -> None:
        self._store.update(job_id, status=JobStatus.running)
        try:
            raw = self._analyzer.analyze(image)
            primary = select_primary_face(raw.faces)
            if primary is None:
                self._store.update(
                    job_id,
                    status=JobStatus.failed,
                    error=JobError("no_face", "No face detected in the image."),
                    result=None,
                )
                return
            overlay = render_landmark_overlay(image, primary.landmarks)
            result = {
                "face_count": len(raw.faces),
                "emotions": {k: float(v) for k, v in primary.emotions.items()},
                "action_units": {k: float(v) for k, v in primary.action_units.items()},
                "landmarks": [[float(x), float(y)] for x, y in primary.landmarks],
                "overlay_image_base64": overlay,
            }
            self._store.update(
                job_id,
                status=JobStatus.succeeded,
                error=None,
                result=result,
            )
        except Exception:
            logger.exception("Analysis failed for job %s", job_id)
            self._store.update(
                job_id,
                status=JobStatus.failed,
                error=JobError("internal", "Analysis failed. Please try again."),
                result=None,
            )

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
```

```python
# apps/api/app/api/routes.py
from __future__ import annotations
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from app.imaging.validate import ImageValidationError
from app.jobs.models import JobStatus
from app.schemas import AnalyzeAccepted, JobErrorSchema, JobResponse, AnalysisResultSchema

router = APIRouter(prefix="/v1")

@router.post("/analyze", response_model=AnalyzeAccepted, status_code=202)
async def analyze(request: Request, image: UploadFile = File(...)) -> AnalyzeAccepted:
    data = await image.read()
    runner = request.app.state.runner
    store = request.app.state.store
    store.purge_expired()
    try:
        job_id = runner.submit(data)
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc
    return AnalyzeAccepted(job_id=job_id)

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, request: Request) -> JobResponse:
    store = request.app.state.store
    store.purge_expired()
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    error = (
        JobErrorSchema(code=job.error.code, message=job.error.message)
        if job.error
        else None
    )
    result = AnalysisResultSchema(**job.result) if job.result else None
    return JobResponse(job_id=job.id, status=job.status, error=error, result=result)
```

Update `create_app` to attach store/runner on lifespan and include router. Prefer stub when `settings.use_stub_analyzer` is true; otherwise prepare for Task 6 Py-FEAT wiring (temporarily raise if stub false and pyfeat not ready — Task 6 fixes that).

```python
# lifespan sketch in main.py
from contextlib import asynccontextmanager
from app.jobs.store import InMemoryJobStore
from app.jobs.runner import JobRunner
from app.analysis.stub import StubAnalyzer
from app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = InMemoryJobStore(ttl_seconds=settings.job_ttl_seconds)
    analyzer = StubAnalyzer() if settings.use_stub_analyzer else StubAnalyzer()
    # Task 6 replaces the non-stub branch with PyFeatAnalyzer
    runner = JobRunner(
        store=store,
        analyzer=analyzer,
        max_upload_bytes=settings.max_upload_bytes,
        pool_size=settings.worker_pool_size,
    )
    app.state.store = store
    app.state.runner = runner
    yield
    runner.shutdown()
```

Ensure `TestClient(create_app())` triggers lifespan (Starlette TestClient does by default).

Add test for no-face: set `app.state.runner` analyzer to one returning `RawAnalysis(faces=[])` — easiest via a `EmptyAnalyzer` in the test file and constructing app with dependency override, or monkeypatch `StubAnalyzer.analyze`. Prefer monkeypatch:

```python
def test_no_face_fails_job(monkeypatch):
    monkeypatch.setenv("PYFEAT_USE_STUB_ANALYZER", "true")
    from app.settings import get_settings
    get_settings.cache_clear()
    from app.analysis.types import RawAnalysis
    monkeypatch.setattr(
        "app.analysis.stub.StubAnalyzer.analyze",
        lambda self, image: RawAnalysis(faces=[]),
    )
    client = TestClient(create_app())
    # ... post and poll until failed with code no_face
```

- [ ] **Step 4: Run API tests — expect PASS**

Run: `pytest tests/test_analyze_api.py tests/test_jobs_api.py -v`

- [ ] **Step 5: Commit**

```bash
git add apps/api
git commit -m "feat(api): add analyze and job polling endpoints"
```

---

### Task 6: Py-FEAT analyzer adapter

**Files:**
- Create: `apps/api/app/analysis/pyfeat.py`
- Create: `apps/api/tests/test_pyfeat_adapter.py` (mocked Detector only)
- Modify: `apps/api/app/main.py` (wire real analyzer when stub false)
- Create: `apps/api/README.md`

**Interfaces:**
- Consumes: `feat.Detector` (mocked in tests)
- Produces: `PyFeatAnalyzer(detector)` implementing `FaceAnalyzer`; maps Fex rows → `FaceDetection` (bbox from FaceRect*, emotions from emotion columns, AUs from AU columns, landmarks from `x_*`/`y_*` pairs)

- [ ] **Step 1: Write failing adapter test with fake Fex-like DataFrame**

```python
# apps/api/tests/test_pyfeat_adapter.py
import numpy as np
import pandas as pd
from app.analysis.pyfeat import PyFeatAnalyzer, fex_row_to_face

def test_fex_row_to_face_maps_columns():
    row = pd.Series({
        "FaceRectX": 1.0,
        "FaceRectY": 2.0,
        "FaceRectWidth": 30.0,
        "FaceRectHeight": 40.0,
        "happiness": 0.8,
        "anger": 0.1,
        "AU12": 0.5,
        "x_0": 5.0,
        "y_0": 6.0,
        "x_1": 7.0,
        "y_1": 8.0,
    })
    face = fex_row_to_face(row)
    assert face.bbox == (1.0, 2.0, 30.0, 40.0)
    assert face.emotions["happiness"] == 0.8
    assert face.action_units["AU12"] == 0.5
    assert face.landmarks == [(5.0, 6.0), (7.0, 8.0)]

def test_analyzer_calls_detector(monkeypatch):
    class FakeDetector:
        def detect_image(self, *args, **kwargs):
            return pd.DataFrame([{
                "FaceRectX": 0, "FaceRectY": 0,
                "FaceRectWidth": 10, "FaceRectHeight": 10,
                "happiness": 1.0, "AU01": 0.2,
                "x_0": 1.0, "y_0": 2.0,
            }])

    analyzer = PyFeatAnalyzer(FakeDetector())
    # Implementation may write a temp PNG path for detect_image — assert faces length 1
    raw = analyzer.analyze(np.zeros((20, 20, 3), dtype=np.uint8))
    assert len(raw.faces) == 1
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement adapter**

Use temp file for `detect_image` if the installed py-feat version requires a path; prefer in-memory API if available. Map columns defensively:

- Emotion keys: known set `anger, disgust, fear, happiness, sadness, surprise, neutral` if present
- AU keys: any column matching `^AU\d+`
- Landmarks: paired `x_{i}` / `y_{i}` sorted by i

```python
# apps/api/app/analysis/pyfeat.py (core idea)
EMOTION_KEYS = ("anger", "disgust", "fear", "happiness", "sadness", "surprise", "neutral")

def fex_row_to_face(row: pd.Series) -> FaceDetection:
    emotions = {k: float(row[k]) for k in EMOTION_KEYS if k in row.index and pd.notna(row[k])}
    action_units = {
        str(col): float(row[col])
        for col in row.index
        if str(col).startswith("AU") and pd.notna(row[col])
    }
    landmark_idxs = sorted(
        int(col[2:]) for col in row.index if str(col).startswith("x_") and col[2:].isdigit()
    )
    landmarks = []
    for i in landmark_idxs:
        y_key = f"y_{i}"
        if y_key in row.index:
            landmarks.append((float(row[f"x_{i}"]), float(row[y_key])))
    bbox = (
        float(row.get("FaceRectX", 0) or 0),
        float(row.get("FaceRectY", 0) or 0),
        float(row.get("FaceRectWidth", 0) or 0),
        float(row.get("FaceRectHeight", 0) or 0),
    )
    return FaceDetection(bbox=bbox, emotions=emotions, action_units=action_units, landmarks=landmarks)
```

Wire `main.py` lifespan:

```python
if settings.use_stub_analyzer:
    analyzer = StubAnalyzer()
else:
    from feat import Detector
    from app.analysis.pyfeat import PyFeatAnalyzer
    detector = Detector()  # document defaults in README
    analyzer = PyFeatAnalyzer(detector)
```

`apps/api/README.md` must document: default Detector models, first-run model download, score meanings (library-native), env vars (`PYFEAT_USE_STUB_ANALYZER`, `PYFEAT_MAX_UPLOAD_BYTES`, `PYFEAT_JOB_TTL_SECONDS`, `PYFEAT_WORKER_POOL_SIZE`, `PYFEAT_CORS_ORIGINS`), and video as future `job_type`.

- [ ] **Step 4: Run unit tests (mocked) — expect PASS**

Run: `pytest tests/test_pyfeat_adapter.py tests/test_analyze_api.py -v`

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/analysis/pyfeat.py apps/api/app/main.py apps/api/README.md apps/api/tests/test_pyfeat_adapter.py
git commit -m "feat(api): integrate Py-FEAT detector adapter"
```

---

### Task 7: API Dockerfile

**Files:**
- Create: `apps/api/Dockerfile`
- Create: `apps/api/.dockerignore`

**Interfaces:**
- Produces: image that runs `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000`

- [ ] **Step 1: Add Dockerfile**

```dockerfile
FROM python:3.11-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .
ENV PYFEAT_CORS_ORIGINS=http://localhost:3000
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

`.dockerignore`: `.venv`, `__pycache__`, `tests`, `.pytest_cache`

- [ ] **Step 2: Build image (optional smoke)**

Run: `docker build -t pyfeat-api ./apps/api`  
Expected: success (may take time due to py-feat deps)

- [ ] **Step 3: Commit**

```bash
git add apps/api/Dockerfile apps/api/.dockerignore
git commit -m "chore(api): add Dockerfile for analysis service"
```

---

### Task 8: Next.js + Tailwind + shadcn scaffold

**Files:**
- Create: `apps/web/**` via `create-next-app` and shadcn init
- Modify: root `.gitignore` if needed

**Interfaces:**
- Produces: runnable Next.js app on port 3000 with Tailwind and shadcn `Button`, `Alert`, `Progress`, `Card` available under `src/components/ui/`

- [ ] **Step 1: Scaffold Next.js app**

Run from repo root:
```bash
npx create-next-app@latest apps/web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --turbopack false
```
Accept defaults consistent with App Router + src dir.

- [ ] **Step 2: Init shadcn and add components**

```bash
cd apps/web
npx shadcn@latest init -y
npx shadcn@latest add button alert progress card
```

- [ ] **Step 3: Set env example**

Create `apps/web/.env.local.example`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 4: Verify dev server starts**

Run: `npm run build` in `apps/web`  
Expected: build success

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "chore(web): scaffold Next.js with Tailwind and shadcn"
```

---

### Task 9: Web API client, types, and poll helper

**Files:**
- Create: `apps/web/src/lib/types.ts`
- Create: `apps/web/src/lib/constants.ts`
- Create: `apps/web/src/lib/api.ts`
- Create: `apps/web/src/lib/poll-job.ts`
- Create: `apps/web/vitest.config.ts`
- Create: `apps/web/src/lib/poll-job.test.ts`
- Create: `apps/web/src/lib/api.test.ts`
- Modify: `apps/web/package.json` (add vitest, jsdom, testing-library)

**Interfaces:**
- Consumes: `NEXT_PUBLIC_API_URL`
- Produces:
  - Types mirroring API: `JobStatus`, `JobError`, `AnalysisResult`, `JobResponse`
  - `submitAnalyze(file: File): Promise<string>`
  - `getJob(jobId: string): Promise<JobResponse>`
  - `pollJob(jobId, { timeoutMs, signal }): Promise<JobResponse>` with backoff 500→1000→2000ms

- [ ] **Step 1: Add vitest and write failing poll test**

```typescript
// apps/web/src/lib/poll-job.test.ts
import { describe, it, expect, vi } from "vitest";
import { pollJob } from "./poll-job";
import type { JobResponse } from "./types";

describe("pollJob", () => {
  it("resolves when job succeeds", async () => {
    const getJob = vi
      .fn<(id: string) => Promise<JobResponse>>()
      .mockResolvedValueOnce({
        job_id: "1",
        status: "running",
        error: null,
        result: null,
      })
      .mockResolvedValueOnce({
        job_id: "1",
        status: "succeeded",
        error: null,
        result: {
          face_count: 1,
          emotions: { happiness: 1 },
          action_units: {},
          landmarks: [],
          overlay_image_base64: "abc",
        },
      });

    const result = await pollJob("1", {
      getJob,
      timeoutMs: 5000,
      initialDelayMs: 1,
    });
    expect(result.status).toBe("succeeded");
    expect(getJob).toHaveBeenCalledTimes(2);
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

Run: `cd apps/web && npx vitest run src/lib/poll-job.test.ts`

- [ ] **Step 3: Implement types, api, poll-job**

```typescript
// apps/web/src/lib/types.ts
export type JobStatus = "queued" | "running" | "succeeded" | "failed";

export interface JobError {
  code: string;
  message: string;
}

export interface AnalysisResult {
  face_count: number;
  emotions: Record<string, number>;
  action_units: Record<string, number>;
  landmarks: number[][];
  overlay_image_base64: string;
}

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  error: JobError | null;
  result: AnalysisResult | null;
}
```

```typescript
// apps/web/src/lib/constants.ts
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
export const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;
export const POLL_TIMEOUT_MS = 120_000;
```

```typescript
// apps/web/src/lib/api.ts
import type { JobResponse } from "./types";

function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  return base.replace(/\/$/, "");
}

export async function submitAnalyze(file: File): Promise<string> {
  const body = new FormData();
  body.append("image", file);
  const response = await fetch(`${apiBase()}/v1/analyze`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Upload failed");
  }
  const json = (await response.json()) as { job_id: string };
  return json.job_id;
}

export async function getJob(jobId: string): Promise<JobResponse> {
  const response = await fetch(`${apiBase()}/v1/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch job status");
  }
  return (await response.json()) as JobResponse;
}
```

```typescript
// apps/web/src/lib/poll-job.ts
import type { JobResponse } from "./types";

export interface PollOptions {
  getJob: (jobId: string) => Promise<JobResponse>;
  timeoutMs: number;
  initialDelayMs?: number;
  signal?: AbortSignal;
}

export async function pollJob(
  jobId: string,
  options: PollOptions,
): Promise<JobResponse> {
  const start = Date.now();
  let delay = options.initialDelayMs ?? 500;
  while (Date.now() - start < options.timeoutMs) {
    if (options.signal?.aborted) {
      throw new Error("Polling aborted");
    }
    const job = await options.getJob(jobId);
    if (job.status === "succeeded" || job.status === "failed") {
      return job;
    }
    await new Promise((r) => setTimeout(r, delay));
    delay = Math.min(delay * 2, 2000);
  }
  throw new Error("Analysis timed out. Please try again.");
}
```

- [ ] **Step 4: Run vitest — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "feat(web): add API client and job polling helper"
```

---

### Task 10: Analysis hook + upload UI shell

**Files:**
- Create: `apps/web/src/hooks/use-analysis.ts`
- Create: `apps/web/src/hooks/use-analysis.test.ts`
- Create: `apps/web/src/components/image-upload.tsx`
- Create: `apps/web/src/components/analysis-progress.tsx`
- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/src/app/layout.tsx` / `globals.css` for a simple non-dashboard layout

**Interfaces:**
- Consumes: `submitAnalyze`, `getJob`, `pollJob`, constants
- Produces: `useAnalysis()` with state `idle | ready | submitting | polling | succeeded | failed`, actions `selectFile`, `analyze`, `reset`, and fields `file`, `previewUrl`, `job`, `errorMessage`

- [ ] **Step 1: Write failing hook test**

```typescript
// apps/web/src/hooks/use-analysis.test.ts
import { describe, it, expect, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useAnalysis } from "./use-analysis";

describe("useAnalysis", () => {
  it("moves from ready to succeeded", async () => {
    const file = new File([new Uint8Array([1, 2, 3])], "face.png", {
      type: "image/png",
    });
    const deps = {
      submitAnalyze: vi.fn().mockResolvedValue("job-1"),
      getJob: vi.fn().mockResolvedValue({
        job_id: "job-1",
        status: "succeeded",
        error: null,
        result: {
          face_count: 1,
          emotions: { happiness: 0.9 },
          action_units: { AU12: 0.8 },
          landmarks: [[1, 2]],
          overlay_image_base64: "aaa",
        },
      }),
      validateFile: () => null as string | null,
    };
    const { result } = renderHook(() => useAnalysis(deps));
    act(() => result.current.selectFile(file));
    expect(result.current.status).toBe("ready");
    await act(async () => {
      await result.current.analyze();
    });
    await waitFor(() => expect(result.current.status).toBe("succeeded"));
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement hook + upload components**

`validateFile` rejects non-accepted MIME and size > `MAX_UPLOAD_BYTES` with user-safe messages.

`ImageUpload`: drag/drop + input; shows preview; Analyze button disabled unless `ready`.

`AnalysisProgress`: shows status text for `submitting` / `polling`.

`page.tsx`: compose upload + progress; leave results for Task 11; brand title “Py-FEAT” as hero-level product name; one short supporting sentence; no dashboard chrome.

- [ ] **Step 4: Run hook tests — expect PASS**; `npm run build`

- [ ] **Step 5: Commit**

```bash
git add apps/web
git commit -m "feat(web): add analysis state hook and upload UI"
```

---

### Task 11: Results panel

**Files:**
- Create: `apps/web/src/components/emotion-bars.tsx`
- Create: `apps/web/src/components/action-unit-table.tsx`
- Create: `apps/web/src/components/overlay-preview.tsx`
- Create: `apps/web/src/components/results-panel.tsx`
- Modify: `apps/web/src/app/page.tsx`

**Interfaces:**
- Consumes: `AnalysisResult`
- Produces: results UI with emotions (sorted bars), AUs table, landmarks count (+ optional coordinate list collapsed), overlay via `data:image/png;base64,...`, note when `face_count > 1`, Reset button

- [ ] **Step 1: Implement components (presentational; light tests optional)**

Sort emotions by value descending. Render AU entries sorted by key. Overlay uses next/image only if configured for data URLs; otherwise plain `<img alt="Face landmarks overlay" />`.

- [ ] **Step 2: Wire into page for `succeeded` / `failed` states**

Failed: shadcn `Alert` with `job.error.message` or timeout message; offer Reset.

- [ ] **Step 3: Manual checklist (document in commit body)**

1. Stub API + web: upload PNG → see stub happiness overlay  
2. Bad file → client or API error shown  
3. Reset returns to idle

- [ ] **Step 4: Commit**

```bash
git add apps/web
git commit -m "feat(web): render emotions, AUs, landmarks, and overlay"
```

---

### Task 12: Docker Compose + root README

**Files:**
- Create: `docker-compose.yml`
- Create: `apps/web/Dockerfile`
- Modify: `README.md`
- Create: `apps/web/.dockerignore`

**Interfaces:**
- Produces: `docker compose up --build` serving web `:3000` and api `:8000`

- [ ] **Step 1: Write compose + web Dockerfile**

```yaml
# docker-compose.yml
services:
  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    environment:
      PYFEAT_CORS_ORIGINS: http://localhost:3000
      # PYFEAT_USE_STUB_ANALYZER: "true"  # uncomment for UI-only work
  web:
    build:
      context: ./apps/web
      args:
        NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - api
```

Web Dockerfile: multi-stage Next.js standalone or `next start`; pass `NEXT_PUBLIC_API_URL` at build time.

- [ ] **Step 2: Update root README**

Include: what the app does, architecture diagram (text), how to run with Compose, how to run API stub mode + `npm run dev`, env vars, first-run Py-FEAT model download note, scale-up path (Redis / workers / video extension), link to design spec.

- [ ] **Step 3: Smoke**

Run: `docker compose up --build` (or local stub mode if models too heavy in CI)  
Hit `http://localhost:3000`, upload a face image, confirm results.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml apps/web/Dockerfile apps/web/.dockerignore README.md
git commit -m "docs: add compose setup and project README"
```

---

## Spec coverage checklist (self-review)

| Spec requirement | Task |
|------------------|------|
| Next.js + Tailwind + shadcn UI | 8, 10, 11 |
| FastAPI job API `/v1/analyze` + `/v1/jobs/{id}` | 5 |
| Emotions, AUs, landmarks, overlay | 4, 5, 6, 11 |
| Ephemeral in-memory TTL jobs | 2, 5 |
| Image-only JPEG/PNG/WebP 10MB | 3, 9, 10 |
| Primary face = largest bbox | 4 |
| Stub/mockable Detector for tests | 4, 5, 6 |
| CORS + docker compose | 1, 7, 12 |
| Scale path documented | 6 README, 12 README |
| Video extension documented only | 6, 12 |
| No auth / no history | throughout (YAGNI) |
| Polling backoff + 2 min timeout | 9, 10 |
| Error codes no_face / invalid_image / internal | 3, 5 |

## Placeholder / consistency notes

- Emotion/AU keys: pass-through from Py-FEAT; stub uses fixed keys for UI development.
- `PYFEAT_USE_STUB_ANALYZER` env drives stub vs real Detector; tests set it true.
- Overlay is raw base64 without data-URL prefix in API; web prefixes for `<img>`.
- Job result field names match between `schemas.py` and `types.ts` exactly.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-18-pyfeat-web-interface.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration  
2. **Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints  

Which approach?
