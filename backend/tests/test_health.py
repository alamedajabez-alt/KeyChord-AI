from fastapi.testclient import TestClient

from app.main import app


def test_liveness():
    r = TestClient(app).get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
