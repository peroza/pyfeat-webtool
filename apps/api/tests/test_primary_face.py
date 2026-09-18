from app.analysis.primary import select_primary_face
from app.analysis.types import FaceDetection


def test_selects_largest_bbox():
    faces = [
        FaceDetection(bbox=(0, 0, 10, 10), emotions={}, action_units={}, landmarks=[]),
        FaceDetection(
            bbox=(0, 0, 50, 50),
            emotions={"happiness": 0.9},
            action_units={},
            landmarks=[(1.0, 2.0)],
        ),
    ]
    primary = select_primary_face(faces)
    assert primary is not None
    assert primary.bbox == (0, 0, 50, 50)


def test_empty_returns_none():
    assert select_primary_face([]) is None
