from tests.conftest import api_test_client


def test_unknown_job_404(monkeypatch):
    monkeypatch.setenv("PYFEAT_USE_STUB_ANALYZER", "true")
    from app.settings import get_settings

    get_settings.cache_clear()
    with api_test_client() as client:
        assert client.get("/v1/jobs/does-not-exist").status_code == 404
