from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PYFEAT_")

    max_upload_bytes: int = 10 * 1024 * 1024
    # Longest image edge before analysis. Full-res phone photos fragment faces.
    analysis_max_side: int = 1280
    job_ttl_seconds: int = 20 * 60
    worker_pool_size: int = 1
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    use_stub_analyzer: bool = False  # True in unit tests via fixture

@lru_cache
def get_settings() -> Settings:
    return Settings()
