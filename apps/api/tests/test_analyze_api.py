import io
import time

from PIL import Image

from tests.conftest import api_test_client


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (10, 20, 30)).save(buf, format="PNG")
    return buf.getvalue()


def test_analyze_accepts_image_and_completes(monkeypatch):
    monkeypatch.setenv("PYFEAT_USE_STUB_ANALYZER", "true")
    from app.settings import get_settings

    get_settings.cache_clear()
    with api_test_client() as client:
        response = client.post(
            "/v1/analyze",
            files={"image": ("face.png", _png(), "image/png")},
        )
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        result = None
        for _ in range(50):
            poll = client.get(f"/v1/jobs/{job_id}")
            assert poll.status_code == 200
            body = poll.json()
            if body["status"] in ("succeeded", "failed"):
                result = body
                break
            time.sleep(0.05)
        assert result is not None
        assert result["status"] == "succeeded"
        assert result["result"]["face_count"] == 1
        assert "happiness" in result["result"]["emotions"]
        assert result["result"]["overlay_image_base64"]


def test_analyze_rejects_garbage(monkeypatch):
    monkeypatch.setenv("PYFEAT_USE_STUB_ANALYZER", "true")
    from app.settings import get_settings

    get_settings.cache_clear()
    with api_test_client() as client:
        response = client.post(
            "/v1/analyze",
            files={"image": ("bad.png", b"not-an-image", "image/png")},
        )
        assert response.status_code == 400


def test_no_face_fails_job(monkeypatch):
    monkeypatch.setenv("PYFEAT_USE_STUB_ANALYZER", "true")
    from app.settings import get_settings

    get_settings.cache_clear()
    from app.analysis.types import RawAnalysis

    monkeypatch.setattr(
        "app.analysis.stub.StubAnalyzer.analyze",
        lambda self, image: RawAnalysis(faces=[]),
    )
    with api_test_client() as client:
        response = client.post(
            "/v1/analyze",
            files={"image": ("face.png", _png(), "image/png")},
        )
        assert response.status_code == 202
        job_id = response.json()["job_id"]

        result = None
        for _ in range(50):
            poll = client.get(f"/v1/jobs/{job_id}")
            assert poll.status_code == 200
            body = poll.json()
            if body["status"] in ("succeeded", "failed"):
                result = body
                break
            time.sleep(0.05)
        assert result is not None
        assert result["status"] == "failed"
        assert result["error"]["code"] == "no_face"
