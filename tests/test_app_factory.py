from fastapi.testclient import TestClient

from app.app_factory import create_app
from app.core.settings import Settings
from app.models import ParseTask, TaskStatus, now


def test_create_app_wires_health_and_default_config(tmp_path):
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)

    health = client.get("/health")
    environments = client.get("/api/v1/config/environments")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert environments.status_code == 200
    assert environments.json()[0]["environmentCode"] == "test"


def test_create_app_serves_frontend_assets(tmp_path):
    app = create_app(Settings(data_dir=tmp_path))
    client = TestClient(app)

    index = client.get("/")
    script = client.get("/ui/app.js")

    assert index.status_code == 200
    assert "UI" in index.text
    assert script.status_code == 200
    assert "runWorkflow" in script.text


def test_create_app_writes_log_file_to_data_dir(tmp_path):
    app = create_app(Settings(data_dir=tmp_path))

    assert app is not None
    assert (tmp_path / "logs" / "app.log").exists()


def test_create_app_exposes_parse_task_llm_logs(tmp_path):
    app = create_app(Settings(data_dir=tmp_path))
    container = app.state.container
    container.store.save_parse_task(
        ParseTask(
            parseTaskId="parse_1",
            documentId="doc_1",
            status=TaskStatus.finished,
            createdAt=now(),
            finishedAt=now(),
        )
    )
    container.llm_logs.log(
        trace_id="parse_1",
        task_id="parse_1",
        operation="parse_cases",
        model="gpt-4o-mini",
        endpoint="https://api.openai.com/v1/chat/completions",
        success=False,
        duration_ms=123,
        request_payload={"messages": []},
        response_payload=None,
        raw_response=None,
        error_type="LLMResponseError",
        error_message="schema mismatch",
        document_id="doc_1",
        parse_task_id="parse_1",
    )

    client = TestClient(app)
    response = client.get("/api/v1/parse-tasks/parse_1/llm-logs")

    assert response.status_code == 200
    assert response.json()[0]["operation"] == "parse_cases"
    assert response.json()[0]["success"] is False
    assert (tmp_path / "llm-logs" / "llm-calls.jsonl").exists()
