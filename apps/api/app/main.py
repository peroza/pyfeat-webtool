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
