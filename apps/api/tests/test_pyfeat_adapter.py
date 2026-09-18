import numpy as np
import pandas as pd

from app.analysis.pyfeat import PyFeatAnalyzer, fex_row_to_face


def test_fex_row_to_face_maps_columns():
    row = pd.Series(
        {
            "FaceRectX": 1.0,
            "FaceRectY": 2.0,
            "FaceRectWidth": 30.0,
            "FaceRectHeight": 40.0,
            "happiness": 0.8,
            "anger": 0.1,
            "AU12": 0.5,
            "x_0": 5.0,
            "y_0": 6.0,
            "x_1": 7.0,
            "y_1": 8.0,
        }
    )
    face = fex_row_to_face(row)
    assert face.bbox == (1.0, 2.0, 30.0, 40.0)
    assert face.emotions["happiness"] == 0.8
    assert face.action_units["AU12"] == 0.5
    assert face.landmarks == [(5.0, 6.0), (7.0, 8.0)]


def test_fex_row_to_face_maps_detector_v2_emotion_names():
    """Detectorv2 emits Title-Case emotion columns (Happy/Sad/…)."""
    row = pd.Series(
        {
            "FaceRectX": 0.0,
            "FaceRectY": 0.0,
            "FaceRectWidth": 10.0,
            "FaceRectHeight": 10.0,
            "Neutral": 0.05,
            "Happy": 0.1,
            "Sad": 0.7,
            "Surprise": 0.05,
            "Fear": 0.02,
            "Disgust": 0.03,
            "Anger": 0.05,
            "AU12": 0.2,
            "x_0": 1.0,
            "y_0": 2.0,
        }
    )
    face = fex_row_to_face(row)
    assert face.emotions["sadness"] == 0.7
    assert face.emotions["happiness"] == 0.1
    assert face.emotions["anger"] == 0.05
    assert "Happy" not in face.emotions


def test_analyzer_calls_detector():
    class FakeDetector:
        def detect_image(self, *args, **kwargs):
            return pd.DataFrame(
                [
                    {
                        "FaceRectX": 0,
                        "FaceRectY": 0,
                        "FaceRectWidth": 10,
                        "FaceRectHeight": 10,
                        "happiness": 1.0,
                        "AU01": 0.2,
                        "x_0": 1.0,
                        "y_0": 2.0,
                    }
                ]
            )

    analyzer = PyFeatAnalyzer(FakeDetector())
    raw = analyzer.analyze(np.zeros((20, 20, 3), dtype=np.uint8))
    assert len(raw.faces) == 1


def test_analyzer_uses_detect_when_no_detect_image():
    class FakeDetector:
        def detect(self, paths, data_type="image", progress_bar=False):
            assert data_type == "image"
            assert progress_bar is False
            assert len(paths) == 1
            assert paths[0].endswith(".png")
            return pd.DataFrame(
                [
                    {
                        "FaceRectX": 0,
                        "FaceRectY": 0,
                        "FaceRectWidth": 10,
                        "FaceRectHeight": 10,
                        "happiness": 1.0,
                        "AU01": 0.2,
                        "x_0": 1.0,
                        "y_0": 2.0,
                    }
                ]
            )

    analyzer = PyFeatAnalyzer(FakeDetector())
    raw = analyzer.analyze(np.zeros((20, 20, 3), dtype=np.uint8))
    assert len(raw.faces) == 1
