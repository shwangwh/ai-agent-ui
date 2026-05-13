from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from app.evidence import EvidenceCollector
from app.domain.events import LogEvent
from app.id_generator import next_id
from app.llm_agent import LLMAgentProtocol, OpenAICompatibleLLMAgent
from app.models import (
    AssertionResult,
    ExecutionCaseResult,
    ExecutionStatus,
    ExecutionTask,
    LogLevel,
    ParsedTestCase,
    StepExecutionResult,
    now,
)


@dataclass
class ExecutionContext:
    base_url: str
    domain_whitelist: list[str]


class SensitiveDataMasker:
    def mask(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = re.sub(r"(1[3-9]\d)\d{4}(\d{4})", r"\1****\2", value)
        value = re.sub(r"(?i)(password\s*[:=]\s*)\S+", r"\1******", value)
        value = re.sub(r"(?i)(token\s*[:=]\s*)\S+", r"\1******", value)
        return value


class LocatorResolver:
    def resolve(self, page: Any, target: str | None) -> Any:
        if not target:
            raise ValueError("LLM action target is required")
        if target.startswith(("css=", "xpath=", "text=", "role=", "label=", "placeholder=", "testid=")):
            prefix, value = target.split("=", 1)
            if prefix == "css":
                return page.locator(value)
            if prefix == "xpath":
                return page.locator(f"xpath={value}")
            if prefix == "text":
                return page.get_by_text(value, exact=False)
            if prefix == "label":
                return page.get_by_label(value)
            if prefix == "placeholder":
                return page.get_by_placeholder(value)
            if prefix == "testid":
                return page.get_by_test_id(value)
            if prefix == "role":
                role, _, name = value.partition(":")
                return page.get_by_role(role, name=name or None)
        return page.locator(target)


class EvidenceRecorder:
    def __init__(self, evidence: EvidenceCollector, logs: Any) -> None:
        self.evidence = evidence
        self.logs = logs

    def capture_screenshot(self, page: Any, task_id: str, case_run_id: str) -> str | None:
        screenshot_path = self.evidence.screenshot_path(task_id, case_run_id)
        try:
            page.screenshot(path=str(screenshot_path), full_page=True)
            url = self.evidence.artifact_url(task_id, case_run_id, "screenshots/final.png")
            self._log_success(task_id, case_run_id, "screenshot", url)
            return url
        except Exception as exc:
            self._log_failure(task_id, case_run_id, "screenshot", exc)
            return None

    def capture_trace(self, browser_context: Any, task_id: str, case_run_id: str) -> str | None:
        trace_path = self.evidence.trace_path(task_id, case_run_id)
        try:
            browser_context.tracing.stop(path=str(trace_path))
            url = self.evidence.artifact_url(task_id, case_run_id, "trace.zip")
            self._log_success(task_id, case_run_id, "trace", url)
            return url
        except Exception as exc:
            self._log_failure(task_id, case_run_id, "trace", exc)
            return None

    def _log_success(self, task_id: str, case_run_id: str, artifact_type: str, url: str) -> None:
        self.logs.log(
            LogLevel.INFO,
            task_id,
            task_id,
            case_run_id,
            None,
            LogEvent.EVIDENCE_CAPTURED,
            "Evidence captured",
            {"artifactType": artifact_type, "url": url},
        )

    def _log_failure(self, task_id: str, case_run_id: str, artifact_type: str, exc: Exception) -> None:
        self.logs.log(
            LogLevel.WARN,
            task_id,
            task_id,
            case_run_id,
            None,
            LogEvent.EVIDENCE_CAPTURE_FAILED,
            "Evidence capture failed",
            {"artifactType": artifact_type, "errorType": type(exc).__name__, "error": str(exc)},
        )


class PlaywrightExecutionRunner:
    def __init__(self, logs: Any, evidence: EvidenceCollector, agent: LLMAgentProtocol | None = None) -> None:
        self.logs = logs
        self.evidence = evidence
        self.agent = agent or OpenAICompatibleLLMAgent()
        self.locators = LocatorResolver()
        self.masker = SensitiveDataMasker()
        self.recorder = EvidenceRecorder(evidence, logs)

    def run_case(self, task: ExecutionTask, test_case: ParsedTestCase, context: ExecutionContext) -> ExecutionCaseResult:
        started_at = now()
        case_run_id = next_id("case_run")
        result = ExecutionCaseResult(
            caseRunId=case_run_id,
            taskId=task.taskId,
            caseId=test_case.caseId,
            caseName=test_case.caseName,
            module=test_case.module,
            priority=test_case.priority,
            startedAt=started_at,
        )
        console_messages: list[dict[str, str]] = []
        network_events: list[dict[str, Any]] = []

        self.logs.log(
            LogLevel.INFO,
            task.taskId,
            task.taskId,
            case_run_id,
            None,
            LogEvent.CASE_EXECUTION_STARTED,
            "Case execution started",
            {"caseId": test_case.caseId, "caseName": test_case.caseName},
        )

        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError:
            result.status = ExecutionStatus.environment_error
            result.failureReason = "playwright is not installed or browser drivers are missing"
            self._finalize(task, result, started_at, console_messages, network_events)
            return result

        try:
            with sync_playwright() as playwright:
                browser_type = getattr(playwright, task.browser)
                browser = browser_type.launch(headless=task.headless)
                browser_context = browser.new_context(base_url=context.base_url or None)
                browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)
                page = browser_context.new_page()
                page.on("console", lambda msg: console_messages.append({"type": msg.type, "text": msg.text}))
                page.on(
                    "response",
                    lambda response: network_events.append(
                        {"url": response.url, "status": response.status, "method": response.request.method}
                    ),
                )

                try:
                    for index, step in enumerate(test_case.steps, start=1):
                        step_result = self._execute_step(
                            page,
                            task.taskId,
                            case_run_id,
                            index,
                            step,
                            test_case,
                            context,
                        )
                        result.steps.append(step_result)
                        if step_result.status != ExecutionStatus.passed:
                            result.status = step_result.status
                            result.failureReason = step_result.message
                            break

                    if result.status is None:
                        result.assertions = self._execute_assertions(page, test_case, console_messages)
                        failed = next((item for item in result.assertions if item.status != ExecutionStatus.passed), None)
                        if failed:
                            result.status = failed.status
                            result.failureReason = failed.actual
                        else:
                            result.status = ExecutionStatus.passed
                finally:
                    screenshot_url = self.recorder.capture_screenshot(page, task.taskId, case_run_id)
                    if screenshot_url:
                        result.evidenceUrls.append(screenshot_url)
                    trace_url = self.recorder.capture_trace(browser_context, task.taskId, case_run_id)
                    if trace_url:
                        result.evidenceUrls.append(trace_url)
                    browser.close()
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            result.status = ExecutionStatus.execution_error
            result.failureReason = str(exc)
        except Exception as exc:
            result.status = ExecutionStatus.execution_error
            result.failureReason = str(exc)

        self._finalize(task, result, started_at, console_messages, network_events)
        return result

    def _execute_step(
        self,
        page: Any,
        task_id: str,
        case_run_id: str,
        index: int,
        step: str,
        test_case: ParsedTestCase,
        context: ExecutionContext,
    ) -> StepExecutionResult:
        started_at = now()
        step_run_id = next_id("step_run")
        page_state = self._page_state(page)
        plan = self.agent.plan_step(step, test_case, page_state)
        action = plan.action
        target = plan.target or plan.url
        status = ExecutionStatus.passed
        message = plan.rationale or "LLM plan executed"

        try:
            if action == "goto":
                page.goto(self._resolve_url(plan.url or plan.target, context), wait_until="domcontentloaded")
            elif action == "click":
                self.locators.resolve(page, plan.target).first.click(timeout=plan.timeoutMs)
            elif action == "fill":
                self.locators.resolve(page, plan.target).first.fill(plan.value or "", timeout=plan.timeoutMs)
            elif action == "select":
                self.locators.resolve(page, plan.target).first.select_option(plan.value or "", timeout=plan.timeoutMs)
            elif action == "wait":
                page.wait_for_timeout(plan.timeoutMs)
            elif action == "scroll":
                page.mouse.wheel(0, int(plan.value or 800))
            elif action == "press":
                page.keyboard.press(plan.value or plan.target or "Enter")
            elif action == "blocked":
                status = ExecutionStatus.blocked
                message = plan.rationale or "LLM agent marked this step as blocked"
            else:
                status = ExecutionStatus.blocked
                message = f"Unsupported LLM action: {action}"
        except Exception as exc:
            status = ExecutionStatus.locator_unresolved if action in ("click", "fill", "select") else ExecutionStatus.execution_error
            message = str(exc)

        duration = self._duration_ms(started_at, now())
        self.logs.log(
            LogLevel.INFO if status == ExecutionStatus.passed else LogLevel.WARN,
            task_id,
            task_id,
            case_run_id,
            step_run_id,
            LogEvent.STEP_EXECUTION_FINISHED,
            "Step execution finished",
            {"action": action, "target": self.masker.mask(target), "status": status, "durationMs": duration},
        )
        return StepExecutionResult(
            stepRunId=step_run_id,
            index=index,
            action=action,
            target=self.masker.mask(target),
            value=self.masker.mask(plan.value),
            status=status,
            durationMs=duration,
            message=message,
        )

    def _execute_assertions(
        self,
        page: Any,
        test_case: ParsedTestCase,
        console_messages: list[dict[str, str]],
    ) -> list[AssertionResult]:
        assertions: list[AssertionResult] = []
        console_errors = [item["text"] for item in console_messages if item["type"] == "error"]
        for expected in test_case.expectedResults:
            plan = self.agent.plan_assertion(expected, test_case, self._page_state(page))
            status = ExecutionStatus.passed
            actual = plan.rationale or "Assertion passed"
            try:
                if plan.assertionType == "url_contains":
                    target = plan.target or plan.expected
                    if target not in page.url:
                        status = ExecutionStatus.assertion_failed
                        actual = f"Current URL: {page.url}"
                elif plan.assertionType == "no_console_error":
                    if console_errors:
                        status = ExecutionStatus.assertion_failed
                        actual = "Console errors: " + "; ".join(console_errors[:3])
                elif plan.assertionType == "element_enabled":
                    if not self.locators.resolve(page, plan.target or plan.expected).first.is_enabled(timeout=3000):
                        status = ExecutionStatus.assertion_failed
                        actual = "Element is not enabled"
                elif plan.assertionType == "element_disabled":
                    if self.locators.resolve(page, plan.target or plan.expected).first.is_enabled(timeout=3000):
                        status = ExecutionStatus.assertion_failed
                        actual = "Element is enabled"
                elif plan.assertionType == "text_visible":
                    if not page.get_by_text(plan.target or plan.expected, exact=False).first.is_visible(timeout=3000):
                        status = ExecutionStatus.assertion_failed
                        actual = f"Visible text not found: {plan.target or plan.expected}"
                else:
                    status = ExecutionStatus.assertion_failed
                    actual = f"Unsupported LLM assertion: {plan.assertionType}"
            except Exception as exc:
                status = ExecutionStatus.assertion_failed
                actual = str(exc)
            assertions.append(
                AssertionResult(
                    assertionType=plan.assertionType,
                    expected=self.masker.mask(plan.expected) or "",
                    actual=actual,
                    status=status,
                )
            )
        return assertions

    def _locator(self, page: Any, target: str | None) -> Any:
        return self.locators.resolve(page, target)

    def _page_state(self, page: Any) -> dict[str, Any]:
        try:
            title = page.title()
        except Exception:
            title = ""
        try:
            url = page.url
        except Exception:
            url = ""
        try:
            snapshot = page.locator("body").inner_text(timeout=1000)[:4000]
        except Exception:
            snapshot = ""
        return {"url": url, "title": title, "bodyText": snapshot}

    def _resolve_url(self, value: str | None, context: ExecutionContext) -> str:
        if not value:
            raise ValueError("LLM goto action requires url or target")
        if value.startswith("/"):
            url = f"{context.base_url.rstrip('/')}{value}"
        elif urlparse(value).scheme:
            url = value
        else:
            url = f"{context.base_url.rstrip('/')}/{value.lstrip('/')}"
        self._validate_url(url, context)
        return url

    def _validate_url(self, url: str, context: ExecutionContext) -> None:
        if not context.domain_whitelist:
            return
        host = urlparse(url).hostname
        if not host:
            return
        if not any(host == domain or host.endswith(f".{domain}") for domain in context.domain_whitelist):
            raise ValueError(f"Target host is outside domain whitelist: {host}")

    def _finalize(
        self,
        task: ExecutionTask,
        result: ExecutionCaseResult,
        started_at: datetime,
        console_messages: list[dict[str, str]],
        network_events: list[dict[str, Any]],
    ) -> None:
        result.finishedAt = now()
        result.durationMs = self._duration_ms(started_at, result.finishedAt)
        result.evidenceUrls.append(
            self.evidence.write_json(task.taskId, result.caseRunId, "console.json", {"messages": console_messages})
        )
        result.evidenceUrls.append(
            self.evidence.write_json(
                task.taskId,
                result.caseRunId,
                "network.json",
                {"responses": network_events[-200:]},
            )
        )
        result.evidenceUrls.append(
            self.evidence.write_json(task.taskId, result.caseRunId, "summary.json", result.model_dump())
        )
        self.logs.log(
            LogLevel.INFO if result.status == ExecutionStatus.passed else LogLevel.WARN,
            task.taskId,
            task.taskId,
            result.caseRunId,
            None,
            LogEvent.CASE_EXECUTION_FINISHED,
            "Case execution finished",
            {"status": result.status, "durationMs": result.durationMs},
        )

    def _mask_sensitive(self, value: str | None) -> str | None:
        return self.masker.mask(value)

    def _duration_ms(self, started_at: datetime, finished_at: datetime | None) -> int:
        if finished_at is None:
            return 0
        return int((finished_at - started_at).total_seconds() * 1000)
