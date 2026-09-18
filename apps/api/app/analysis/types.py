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
