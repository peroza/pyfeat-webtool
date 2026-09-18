from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from app.analysis.primary import select_primary_face
from app.analysis.protocol import FaceAnalyzer
from app.imaging.overlay import render_landmark_overlay
from app.imaging.validate import decode_image, downsample_for_analysis
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
        analysis_max_side: int = 1280,
    ) -> None:
        self._store = store
        self._analyzer = analyzer
        self._max_upload_bytes = max_upload_bytes
        self._analysis_max_side = analysis_max_side
        self._executor = ThreadPoolExecutor(max_workers=pool_size)

    def submit(self, image_bytes: bytes) -> str:
        image = decode_image(image_bytes, self._max_upload_bytes)
        image = downsample_for_analysis(image, self._analysis_max_side)
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
            overlay = render_landmark_overlay(
                image,
                primary.landmarks,
                face_bbox=primary.bbox,
            )
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
