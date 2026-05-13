import io
import json
import urllib.error

from app.llm_agent import OpenAICompatibleLLMAgent
from app.models import ParseStatus


class StubLLMRecorder:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def log(self, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(kwargs)


def test_llm_agent_normalizes_chat_completions_base_url():
    agent = OpenAICompatibleLLMAgent(
        api_key="test-key",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        model="qwen3.5-plus",
    )

    assert agent.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"


def test_llm_agent_normalizes_common_case_parse_shapes():
    agent = OpenAICompatibleLLMAgent(api_key="test-key")

    payload = {
        "cases": [
            {
                "caseId": "TALENT_001",
                "caseName": "新增候选人成功",
                "steps": ["打开系统", 123456],
                "testData": [{"key": "姓名", "value": "张三"}],
                "expectedResults": ["新增成功"],
                "status": "executable",
                "uncertainItems": None,
            }
        ]
    }

    normalized = agent._normalize_case_parse_payload(payload)

    assert normalized["cases"][0]["steps"] == ["打开系统", "123456"]
    assert normalized["cases"][0]["testData"] == ["姓名: 张三"]
    assert normalized["cases"][0]["uncertainItems"] == []


def test_llm_agent_records_successful_parse_call(monkeypatch):
    recorder = StubLLMRecorder()
    agent = OpenAICompatibleLLMAgent(api_key="test-key", log_recorder=recorder)

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            payload = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "cases": [
                                        {
                                            "caseId": "CASE_001",
                                            "caseName": "submit order",
                                            "steps": ["open /"],
                                            "expectedResults": ["success"],
                                            "status": ParseStatus.executable,
                                        }
                                    ]
                                },
                                ensure_ascii=False,
                            )
                        }
                    }
                ]
            }
            return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout=60: FakeResponse())

    cases = agent.parse_cases("doc_1", "parse_1", "markdown")

    assert len(cases) == 1
    assert recorder.calls[0]["success"] is True
    assert recorder.calls[0]["operation"] == "parse_cases"
    assert recorder.calls[0]["task_id"] == "parse_1"
    assert recorder.calls[0]["response_payload"]["cases"][0]["caseId"] == "CASE_001"


def test_llm_agent_records_failed_http_call(monkeypatch):
    recorder = StubLLMRecorder()
    agent = OpenAICompatibleLLMAgent(api_key="test-key", log_recorder=recorder)

    def raise_http_error(request, timeout=60):  # type: ignore[no-untyped-def]
        raise urllib.error.HTTPError(
            url="https://api.openai.com/v1/chat/completions",
            code=500,
            msg="server error",
            hdrs=None,
            fp=io.BytesIO(b'{"error":"boom"}'),
        )

    monkeypatch.setattr("urllib.request.urlopen", raise_http_error)

    try:
        agent.parse_cases("doc_1", "parse_1", "markdown")
    except Exception as exc:
        assert "HTTP 500" in str(exc)
    else:
        raise AssertionError("expected parse_cases() to fail")

    assert recorder.calls[0]["success"] is False
    assert recorder.calls[0]["error_type"] == "LLMResponseError"
    assert "HTTP 500" in (recorder.calls[0]["error_message"] or "")
