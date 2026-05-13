from fastapi.testclient import TestClient

from app.app_factory import create_app
from app.core.settings import Settings


def test_create_app_wires_health_and_default_config(tmp_path):
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)

    health = client.get("/health")
    environments = client.get("/api/v1/config/environments")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert environments.status_code == 200
    assert environments.json()[0]["environmentCode"] == "test"
