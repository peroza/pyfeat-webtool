from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analysis.stub import StubAnalyzer
from app.api.routes import router
from app.jobs.runner import JobRunner
from app.jobs.store import InMemoryJobStore
from app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = InMemoryJobStore(ttl_seconds=settings.job_ttl_seconds)
    analyzer = StubAnalyzer() if settings.use_stub_analyzer else StubAnalyzer()
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


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Py-FEAT Analysis API",
        version="0.1.0",
        lifespan=lifespan,
    )
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

    app.include_router(router)
    return app
