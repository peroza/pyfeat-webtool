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
                    landmarks=[
                        (w * 0.4, h * 0.4),
                        (w * 0.6, h * 0.4),
                        (w * 0.5, h * 0.6),
                    ],
                )
            ]
        )
