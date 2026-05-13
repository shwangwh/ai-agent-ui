from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Protocol

from pydantic import BaseModel, Field, ValidationError

from app.models import ParseStatus, ParsedTestCase, now


AGENT_PERSONA = (
    "You are SeniorUIAutomationTestAgent, a senior QA automation engineer with 10 years "
    "of hands-on experience in web UI automation, test analysis, regression design, "
    "locator strategy, assertion design, and execution risk control. You follow the "
    "uploaded test cases strictly, prefer deterministic actions and assertions, and do "
    "not invent business facts, page elements, test data, or expected results that are "
    "not supported by the uploaded case or the current page state. When information is "
    "ambiguous, incomplete, or not executable, you must be conservative, explain the "
    "uncertainty briefly, and mark the item for review or return a blocked action."
)


class LLMConfigurationError(RuntimeError):
    pass


class LLMResponseError(RuntimeError):
    pass


class PlannedTestCase(BaseModel):
    caseId: str
    caseName: str
    module: str | None = None
    priority: str | None = None
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expectedResults: list[str] = Field(default_factory=list)
    testData: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    remarks: str | None = None
    parseConfidence: float = Field(default=0.9, ge=0.0, le=1.0)
    status: ParseStatus = ParseStatus.need_review
    uncertainItems: list[str] = Field(default_factory=list)


class CaseParsePlan(BaseModel):
    cases: list[PlannedTestCase]


class StepPlan(BaseModel):
    action: str
    target: str | None = None
    value: str | None = None
    url: str | None = None
    timeoutMs: int = Field(default=5000, ge=0, le=60000)
    rationale: str | None = None


class AssertionPlan(BaseModel):
    assertionType: str
    target: str | None = None
    expected: str
    rationale: str | None = None


@dataclass(slots=True)
class LLMCallContext:
    operation: str
    trace_id: str
    task_id: str
    document_id: str | None = None
    parse_task_id: str | None = None
    case_id: str | None = None
    case_run_id: str | None = None
    step_run_id: str | None = None


class LLMLogRecorderProtocol(Protocol):
    def log(
        self,
        *,
        trace_id: str,
        task_id: str,
        operation: str,
        model: str,
        endpoint: str,
        success: bool,
        duration_ms: int,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any] | None = None,
        raw_response: str | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        document_id: str | None = None,
        parse_task_id: str | None = None,
        case_id: str | None = None,
        case_run_id: str | None = None,
        step_run_id: str | None = None,
    ) -> Any:
        ...


class LLMAgentProtocol(Protocol):
    def parse_cases(self, document_id: str, parse_task_id: str, markdown: str) -> list[ParsedTestCase]:
        ...

    def plan_step(
        self,
        task_id: str,
        case_run_id: str,
        step_run_id: str,
        step: str,
        case: ParsedTestCase,
        page_state: dict[str, Any],
    ) -> StepPlan:
        ...

    def plan_assertion(
        self,
        task_id: str,
        case_run_id: str,
        expected: str,
        case: ParsedTestCase,
        page_state: dict[str, Any],
    ) -> AssertionPlan:
        ...


class OpenAICompatibleLLMAgent:
    """LLM agent backed by an OpenAI-compatible chat completions endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 60,
        log_recorder: LLMLogRecorderProtocol | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = self._normalize_base_url(base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1")
        self.model = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        self.timeout_seconds = timeout_seconds
        self.log_recorder = log_recorder

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        normalized = base_url.strip().rstrip("/")
        completions_suffix = "/chat/completions"
        if normalized.endswith(completions_suffix):
            normalized = normalized[: -len(completions_suffix)].rstrip("/")
        return normalized

    def parse_cases(self, document_id: str, parse_task_id: str, markdown: str) -> list[ParsedTestCase]:
        context = LLMCallContext(
            operation="parse_cases",
            trace_id=parse_task_id,
            task_id=parse_task_id,
            document_id=document_id,
            parse_task_id=parse_task_id,
        )
        request_payload = self._build_chat_request(
            system=(
                f"{AGENT_PERSONA} "
                "Your current responsibility is test case parsing. Convert markdown test "
                "documents into strict JSON test cases for downstream automation execution. "
                "Preserve the user's intent faithfully. Extract case id, case name, module, "
                "priority, preconditions, steps, expected results, test data, tags, and "
                "remarks when present. Do not invent runnable details that are absent. Mark "
                "cases executable only when the steps and expected results are clear enough "
                "to execute. Mark need_review when key information is ambiguous or missing. "
                "Mark invalid when the content is not a test case. Mark skipped only when "
                "the uploaded case explicitly says it should be skipped."
            ),
            user=(
                "Return JSON with this shape: "
                '{"cases":[{"caseId":"...","caseName":"...","module":null,'
                '"priority":null,"preconditions":[],"steps":[],"expectedResults":[],'
                '"testData":[],"tags":[],"remarks":null,"parseConfidence":0.0,'
                '"status":"executable|need_review|invalid|skipped","uncertainItems":[]}]}.\n\n'
                f"Markdown:\n{markdown}"
            ),
        )
        raw_response: str | None = None
        payload: dict[str, Any] | None = None
        started = time.perf_counter()
        try:
            raw_response, payload = self._complete_json(request_payload)
            payload = self._normalize_case_parse_payload(payload)
            plan = CaseParsePlan.model_validate(payload)
        except ValidationError as exc:
            self._record_call(context, request_payload, payload, raw_response, exc, started)
            raise LLMResponseError(f"LLM parse response schema mismatch: {exc}") from exc
        except Exception as exc:
            self._record_call(context, request_payload, payload, raw_response, exc, started)
            raise

        cases: list[ParsedTestCase] = []
        for index, item in enumerate(plan.cases, start=1):
            case_id = item.caseId.strip() or f"CASE_{index:03d}"
            cases.append(
                ParsedTestCase(
                    caseId=case_id,
                    documentId=document_id,
                    parseTaskId=parse_task_id,
                    caseName=item.caseName,
                    module=item.module,
                    priority=item.priority,
                    rawMarkdown=markdown,
                    preconditions=item.preconditions,
                    steps=item.steps,
                    expectedResults=item.expectedResults,
                    testData=item.testData,
                    tags=item.tags,
                    remarks=item.remarks,
                    parseConfidence=item.parseConfidence,
                    status=item.status,
                    uncertainItems=item.uncertainItems,
                    updatedAt=now(),
                )
            )
        self._record_call(context, request_payload, payload, raw_response, None, started)
        return cases

    def plan_step(
        self,
        task_id: str,
        case_run_id: str,
        step_run_id: str,
        step: str,
        case: ParsedTestCase,
        page_state: dict[str, Any],
    ) -> StepPlan:
        context = LLMCallContext(
            operation="plan_step",
            trace_id=task_id,
            task_id=task_id,
            document_id=case.documentId,
            parse_task_id=case.parseTaskId,
            case_id=case.caseId,
            case_run_id=case_run_id,
            step_run_id=step_run_id,
        )
        request_payload = self._build_chat_request(
            system=(
                f"{AGENT_PERSONA} "
                "Your current responsibility is browser automation planning. Convert one "
                "natural language test step into exactly one executable browser action for "
                "automation runtime. Allowed actions are: goto, click, fill, select, wait, "
                "scroll, press, blocked. Use the uploaded case as the primary source of "
                "truth and use the current page state only to ground the action target. "
                "Prefer stable selectors and deterministic interactions. If the step cannot "
                "be executed safely from the given case and page state, return blocked "
                "instead of guessing."
            ),
            user=(
                "Return JSON with this shape: "
                '{"action":"goto|click|fill|select|wait|scroll|press|blocked",'
                '"target":null,"value":null,"url":null,"timeoutMs":5000,"rationale":null}.\n\n'
                f"Case: {case.model_dump(mode='json')}\n"
                f"Page state: {json.dumps(page_state, ensure_ascii=False)}\n"
                f"Step: {step}"
            ),
        )
        raw_response: str | None = None
        payload: dict[str, Any] | None = None
        started = time.perf_counter()
        try:
            raw_response, payload = self._complete_json(request_payload)
            plan = StepPlan.model_validate(payload)
            self._record_call(context, request_payload, payload, raw_response, None, started)
            return plan
        except Exception as exc:
            self._record_call(context, request_payload, payload, raw_response, exc, started)
            if isinstance(exc, ValidationError):
                raise LLMResponseError(f"LLM step response schema mismatch: {exc}") from exc
            raise

    def plan_assertion(
        self,
        task_id: str,
        case_run_id: str,
        expected: str,
        case: ParsedTestCase,
        page_state: dict[str, Any],
    ) -> AssertionPlan:
        context = LLMCallContext(
            operation="plan_assertion",
            trace_id=task_id,
            task_id=task_id,
            document_id=case.documentId,
            parse_task_id=case.parseTaskId,
            case_id=case.caseId,
            case_run_id=case_run_id,
        )
        request_payload = self._build_chat_request(
            system=(
                f"{AGENT_PERSONA} "
                "Your current responsibility is assertion planning. Convert one expected "
                "result into exactly one executable browser assertion. Allowed "
                "assertionType values are: text_visible, url_contains, no_console_error, "
                "element_enabled, element_disabled. Prefer the most direct and verifiable "
                "assertion type. Do not rewrite a vague expected result into a stronger "
                "claim than the uploaded case supports. If the expectation is unclear, stay "
                "conservative in rationale and target selection."
            ),
            user=(
                "Return JSON with this shape: "
                '{"assertionType":"text_visible|url_contains|no_console_error|element_enabled|element_disabled",'
                '"target":null,"expected":"...","rationale":null}.\n\n'
                f"Case: {case.model_dump(mode='json')}\n"
                f"Page state: {json.dumps(page_state, ensure_ascii=False)}\n"
                f"Expected result: {expected}"
            ),
        )
        raw_response: str | None = None
        payload: dict[str, Any] | None = None
        started = time.perf_counter()
        try:
            raw_response, payload = self._complete_json(request_payload)
            plan = AssertionPlan.model_validate(payload)
            self._record_call(context, request_payload, payload, raw_response, None, started)
            return plan
        except Exception as exc:
            self._record_call(context, request_payload, payload, raw_response, exc, started)
            if isinstance(exc, ValidationError):
                raise LLMResponseError(f"LLM assertion response schema mismatch: {exc}") from exc
            raise

    def _build_chat_request(self, system: str, user: str) -> dict[str, Any]:
        return {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

    def _complete_json(self, body: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        if not self.api_key:
            raise LLMConfigurationError("LLM_API_KEY is required to run the LLM agent")

        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise LLMResponseError(f"LLM endpoint returned HTTP {exc.code}: {details}") from exc
        except urllib.error.URLError as exc:
            raise LLMResponseError(f"LLM endpoint request failed: {exc}") from exc

        try:
            completion = json.loads(raw)
            content = completion["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise LLMResponseError("LLM endpoint returned a non-JSON chat response") from exc
        if not isinstance(parsed, dict):
            raise LLMResponseError("LLM JSON response must be an object")
        return raw, parsed

    def _record_call(
        self,
        context: LLMCallContext,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any] | None,
        raw_response: str | None,
        exc: Exception | None,
        started: float,
    ) -> None:
        if self.log_recorder is None:
            return
        self.log_recorder.log(
            trace_id=context.trace_id,
            task_id=context.task_id,
            operation=context.operation,
            model=self.model,
            endpoint=f"{self.base_url}/chat/completions",
            success=exc is None,
            duration_ms=int((time.perf_counter() - started) * 1000),
            request_payload=request_payload,
            response_payload=response_payload,
            raw_response=raw_response,
            error_type=type(exc).__name__ if exc else None,
            error_message=str(exc) if exc else None,
            document_id=context.document_id,
            parse_task_id=context.parse_task_id,
            case_id=context.case_id,
            case_run_id=context.case_run_id,
            step_run_id=context.step_run_id,
        )

    def _normalize_case_parse_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        cases = payload.get("cases")
        if not isinstance(cases, list):
            return payload

        normalized_cases: list[dict[str, Any]] = []
        for item in cases:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            for field in ("preconditions", "steps", "expectedResults", "testData", "tags", "uncertainItems"):
                normalized[field] = self._normalize_string_list(item.get(field))
            normalized_cases.append(normalized)
        payload["cases"] = normalized_cases
        return payload

    def _normalize_string_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            normalized: list[str] = []
            for item in value:
                text = self._stringify_value(item)
                if text:
                    normalized.append(text)
            return normalized
        text = self._stringify_value(value)
        return [text] if text else []

    def _stringify_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float, bool)):
            return str(value)
        if isinstance(value, dict):
            key = value.get("key")
            nested = value.get("value")
            if key is not None and nested is not None:
                key_text = self._stringify_value(key)
                value_text = self._stringify_value(nested)
                return f"{key_text}: {value_text}".strip(": ").strip()
            try:
                return json.dumps(value, ensure_ascii=False)
            except TypeError:
                return str(value)
        if isinstance(value, list):
            parts = [self._stringify_value(item) for item in value]
            return ", ".join(part for part in parts if part)
        return str(value)
