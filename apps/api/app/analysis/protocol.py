from typing import Protocol

import numpy as np

from app.analysis.types import RawAnalysis


class FaceAnalyzer(Protocol):
    def analyze(self, image_rgb: np.ndarray) -> RawAnalysis: ...
