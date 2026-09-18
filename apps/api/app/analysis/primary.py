from app.analysis.types import FaceDetection


def select_primary_face(faces: list[FaceDetection]) -> FaceDetection | None:
    if not faces:
        return None
    return max(faces, key=lambda f: f.bbox[2] * f.bbox[3])
