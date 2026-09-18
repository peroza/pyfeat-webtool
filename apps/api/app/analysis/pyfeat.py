from __future__ import annotations

import re
import tempfile
from pathlib import Path
from collections.abc import Callable
from typing import Any, Protocol

import numpy as np
import pandas as pd
from PIL import Image

from app.analysis.types import FaceDetection, RawAnalysis

EMOTION_KEYS = (
    "anger",
    "disgust",
    "fear",
    "happiness",
    "sadness",
    "surprise",
    "neutral",
)

_AU_COLUMN_PATTERN = re.compile(r"^AU\d+")


class _PyFeatDetector(Protocol):
    def detect_image(self, *args: Any, **kwargs: Any) -> pd.DataFrame: ...

    def detect(self, *args: Any, **kwargs: Any) -> pd.DataFrame: ...


def fex_row_to_face(row: pd.Series) -> FaceDetection:
    emotions = {
        key: float(row[key])
        for key in EMOTION_KEYS
        if key in row.index and pd.notna(row[key])
    }
    action_units = {
        str(col): float(row[col])
        for col in row.index
        if _AU_COLUMN_PATTERN.match(str(col)) and pd.notna(row[col])
    }
    landmark_indexes = sorted(
        int(str(col)[2:])
        for col in row.index
        if str(col).startswith("x_") and str(col)[2:].isdigit()
    )
    landmarks: list[tuple[float, float]] = []
    for index in landmark_indexes:
        y_key = f"y_{index}"
        x_key = f"x_{index}"
        if y_key in row.index and pd.notna(row[x_key]) and pd.notna(row[y_key]):
            landmarks.append((float(row[x_key]), float(row[y_key])))
    bbox = (
        float(row.get("FaceRectX", 0) or 0),
        float(row.get("FaceRectY", 0) or 0),
        float(row.get("FaceRectWidth", 0) or 0),
        float(row.get("FaceRectHeight", 0) or 0),
    )
    return FaceDetection(
        bbox=bbox,
        emotions=emotions,
        action_units=action_units,
        landmarks=landmarks,
    )


def _fex_to_dataframe(fex: Any) -> pd.DataFrame:
    if isinstance(fex, pd.DataFrame):
        return fex
    return pd.DataFrame(fex)


def _write_temp_png(image_rgb: np.ndarray) -> Path:
    fd, name = tempfile.mkstemp(suffix=".png")
    path = Path(name)
    try:
        with open(fd, "wb") as handle:
            Image.fromarray(image_rgb).save(handle, format="PNG")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path


class PyFeatAnalyzer:
    """Maps py-feat Fex rows to API face detections."""

    def __init__(self, detector: _PyFeatDetector) -> None:
        self._detector = detector

    def analyze(self, image_rgb: np.ndarray) -> RawAnalysis:
        fex_df = self._run_detector(image_rgb)
        faces = [fex_row_to_face(row) for _, row in fex_df.iterrows()]
        return RawAnalysis(faces=faces)

    def _run_detector(self, image_rgb: np.ndarray) -> pd.DataFrame:
        detect_image = getattr(self._detector, "detect_image", None)
        if callable(detect_image):
            return self._detect_via_temp_file(
                image_rgb,
                lambda path: detect_image(str(path)),
            )

        detect = getattr(self._detector, "detect", None)
        if not callable(detect):
            raise TypeError("Detector must provide detect_image or detect")

        return self._detect_via_temp_file(
            image_rgb,
            lambda path: detect(
                [str(path)],
                data_type="image",
                progress_bar=False,
            ),
        )

    def _detect_via_temp_file(
        self,
        image_rgb: np.ndarray,
        run_detect: Callable[[Path], Any],
    ) -> pd.DataFrame:
        temp_path = _write_temp_png(image_rgb)
        try:
            return _fex_to_dataframe(run_detect(temp_path))
        finally:
            temp_path.unlink(missing_ok=True)
