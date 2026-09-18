from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.imaging.upload import read_bounded_upload
from app.imaging.validate import ImageValidationError
from app.settings import get_settings
from app.schemas import (
    AnalysisResultSchema,
    AnalyzeAccepted,
    JobErrorSchema,
    JobResponse,
)

router = APIRouter(prefix="/v1")


@router.post("/analyze", response_model=AnalyzeAccepted, status_code=202)
async def analyze(request: Request, image: UploadFile = File(...)) -> AnalyzeAccepted:
    settings = get_settings()
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            if int(content_length) > settings.max_upload_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="Upload exceeds maximum size.",
                )
        except ValueError:
            pass

    data = await read_bounded_upload(image, settings.max_upload_bytes)
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
