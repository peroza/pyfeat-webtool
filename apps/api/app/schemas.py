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
