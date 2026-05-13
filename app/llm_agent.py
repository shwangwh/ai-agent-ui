from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Protocol

from pydantic import BaseModel, Field, ValidationError

from app.models import ParseStatus, ParsedTestCase, now


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


class LLMAgentProtocol(Protocol):
    def parse_cases(self, document_id: str, parse_task_id: str, markdown: str) -> list[ParsedTestCase]:
        ...

    def plan_step(self, step: str, case: ParsedTestCase, page_state: dict[str, Any]) -> StepPlan:
        ...

    def plan_assertion(self, expected: str, case: ParsedTestCase, page_state: dict[str, Any]) -> AssertionPlan:
        ...


class OpenAICompatibleLLMAgent:
    """LLM agent backed by an OpenAI-compatible chat completions endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        self.timeout_seconds = timeout_seconds

    def parse_cases(self, document_id: str, parse_task_id: str, markdown: str) -> list[ParsedTestCase]:
        payload = self._complete_json(
            system=(
                "You are a UI test case parsing agent. Convert markdown test documents "
                "into strict JSON. Do not invent runnable details that are absent. Mark "
                "cases executable only when steps and expected results are clear."
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
        try:
            plan = CaseParsePlan.model_validate(payload)
        except ValidationError as exc:
            raise LLMResponseError(f"LLM parse response schema mismatch: {exc}") from exc

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
        return cases

    def plan_step(self, step: str, case: ParsedTestCase, page_state: dict[str, Any]) -> StepPlan:
        payload = self._complete_json(
            system=(
                "You are a browser automation planning agent. Convert one natural language "
                "test step into a single executable action. Allowed actions are: goto, "
                "click, fill, select, wait, scroll, press, blocked."
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
        try:
            return StepPlan.model_validate(payload)
        except ValidationError as exc:
            raise LLMResponseError(f"LLM step response schema mismatch: {exc}") from exc

    def plan_assertion(self, expected: str, case: ParsedTestCase, page_state: dict[str, Any]) -> AssertionPlan:
        payload = self._complete_json(
            system=(
                "You are a UI assertion planning agent. Convert one expected result into "
                "a single executable browser assertion. Allowed assertionType values are: "
                "text_visible, url_contains, no_console_error, element_enabled, element_disabled."
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
        try:
            return AssertionPlan.model_validate(payload)
        except ValidationError as exc:
            raise LLMResponseError(f"LLM assertion response schema mismatch: {exc}") from exc

    def _complete_json(self, system: str, user: str) -> dict[str, Any]:
        if not self.api_key:
            raise LLMConfigurationError("LLM_API_KEY is required to run the LLM agent")

        body = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
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
        return parsed
