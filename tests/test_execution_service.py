import logging
from typing import Any

from app.evidence import EvidenceCollector
from app.llm_agent import AssertionPlan, StepPlan
from app.models import (
    ExecutionCaseResult,
    ExecutionStatus,
    ExecutionTask,
    ParseStatus,
    ParseTask,
    ParsedTestCase,
    TaskStatus,
    TestDocument as AgentTestDocument,
    now,
)
from app.reporting import ReportGenerator
from app.runner import ExecutionContext
from app.services import DocumentService, ExecutionTaskService, ParseTaskService, TaskLogService
from app.parser import MarkdownCaseParser
from app.store import InMemoryAgentStore
from app.models import CreateExecutionTaskRequest


class FakeLLMAgent:
    def parse_cases(self, document_id: str, parse_task_id: str, markdown: str) -> list[ParsedTestCase]:
        return []

    def plan_step(
        self,
        task_id: str,
        case_run_id: str,
        step_run_id: str,
        step: str,
        case: ParsedTestCase,
        page_state: dict[str, Any],
    ) -> StepPlan:
        return StepPlan(action="blocked", rationale="not used")

    def plan_assertion(
        self,
        task_id: str,
        case_run_id: str,
        expected: str,
        case: ParsedTestCase,
        page_state: dict[str, Any],
    ) -> AssertionPlan:
        return AssertionPlan(assertionType="text_visible", expected=expected)


class FakeRunner:
    def __init__(self, evidence: EvidenceCollector) -> None:
        self.evidence = evidence
        self.contexts: list[ExecutionContext] = []

    def run_case(self, task: ExecutionTask, test_case: ParsedTestCase, context: ExecutionContext) -> ExecutionCaseResult:
        self.contexts.append(context)
        result = ExecutionCaseResult(
            caseRunId="case_run_fake",
            taskId=task.taskId,
            caseId=test_case.caseId,
            caseName=test_case.caseName,
            module=test_case.module,
            priority=test_case.priority,
            status=ExecutionStatus.passed,
            startedAt=now(),
            finishedAt=now(),
        )
        result.evidenceUrls.append(
            self.evidence.write_json(task.taskId, result.caseRunId, "summary.json", {"status": "passed"})
        )
        return result


class CrashingRunner:
    def run_case(self, task: ExecutionTask, test_case: ParsedTestCase, context: ExecutionContext) -> ExecutionCaseResult:
        raise RuntimeError("browser crashed")


def build_service(tmp_path):
    store = InMemoryAgentStore()
    logs = TaskLogService(store)
    documents = DocumentService(store, logs, storage_root=str(tmp_path))
    parse_tasks = ParseTaskService(store, documents, MarkdownCaseParser(FakeLLMAgent()), logs)
    evidence = EvidenceCollector(storage_root=str(tmp_path))
    reports = ReportGenerator(storage_root=str(tmp_path))
    fake_runner = FakeRunner(evidence)
    service = ExecutionTaskService(
        store,
        parse_tasks,
        logs,
        evidence=evidence,
        reports=reports,
        environment_resolver=lambda code: {"environmentCode": code, "baseUrl": "http://localhost:3000"},
        runner=fake_runner,  # type: ignore[arg-type]
    )
    store.save_document(
        AgentTestDocument(
            documentId="doc_1",
            fileName="cases.md",
            fileSize=10,
            storagePath=str(tmp_path / "cases.md"),
            content="case",
            createdAt=now(),
        )
    )
    store.save_parse_task(
        ParseTask(
            parseTaskId="parse_1",
            documentId="doc_1",
            status=TaskStatus.finished,
            totalCases=1,
            executableCases=1,
            createdAt=now(),
            finishedAt=now(),
        )
    )
    store.save_parsed_cases(
        "parse_1",
        [
            ParsedTestCase(
                caseId="CASE_001",
                documentId="doc_1",
                parseTaskId="parse_1",
                caseName="首页可打开",
                rawMarkdown="case",
                steps=["打开 /"],
                expectedResults=["显示 首页"],
                parseConfidence=0.9,
                status=ParseStatus.executable,
                updatedAt=now(),
            )
        ],
    )
    return service, fake_runner


def build_service_with_runner(tmp_path, runner):
    service, _ = build_service(tmp_path)
    service.runner = runner
    return service


def test_execution_generates_evidence_and_report(tmp_path):
    service, fake_runner = build_service(tmp_path)

    task = service.create(CreateExecutionTaskRequest(documentId="doc_1", parseTaskId="parse_1"))

    assert task.status == TaskStatus.finished
    assert task.passed == 1
    assert task.failed == 0
    assert task.allureReportUrl == f"/reports/allure/{task.taskId}/index.html"
    assert fake_runner.contexts[0].base_url == "http://localhost:3000"
    assert (tmp_path / "artifacts" / task.taskId / "case_run_fake" / "summary.json").exists()
    assert (tmp_path / "allure-report" / task.taskId / "index.html").exists()
    assert list((tmp_path / "allure-results" / task.taskId).glob("*-result.json"))


def test_execution_task_is_marked_failed_when_runner_crashes(tmp_path):
    service = build_service_with_runner(tmp_path, CrashingRunner())

    task = service.create(CreateExecutionTaskRequest(documentId="doc_1", parseTaskId="parse_1"))

    assert task.status == TaskStatus.failed
    assert "browser crashed" in (task.message or "")
    logs = service.logs.find_logs(task.taskId)
    assert any(log.event == "EXECUTION_TASK_FAILED" and log.level == "ERROR" for log in logs)


def test_task_logs_are_forwarded_to_python_logging(tmp_path, caplog):
    service, _ = build_service(tmp_path)

    with caplog.at_level(logging.INFO, logger="app.task"):
        service.logs.log(
            level="INFO",
            trace_id="trace_1",
            task_id="task_1",
            case_run_id="case_1",
            step_run_id="step_1",
            event="STEP_EXECUTION_FINISHED",
            message="step done",
            attributes={"status": "passed"},
        )

    assert any(record.message == "step done" for record in caplog.records)
    log_record = next(record for record in caplog.records if record.message == "step done")
    assert log_record.taskId == "task_1"
    assert log_record.caseRunId == "case_1"
    assert log_record.stepRunId == "step_1"
    assert log_record.event == "STEP_EXECUTION_FINISHED"


def test_execution_rejects_failed_parse_task(tmp_path):
    service, _ = build_service(tmp_path)
    store = service.store
    store.save_parse_task(
        ParseTask(
            parseTaskId="parse_failed",
            documentId="doc_1",
            status=TaskStatus.failed,
            createdAt=now(),
            finishedAt=now(),
            message="解析失败: schema mismatch",
        )
    )

    try:
        service.create(CreateExecutionTaskRequest(documentId="doc_1", parseTaskId="parse_failed"))
    except Exception as exc:
        assert "解析失败" in str(exc)
    else:
        raise AssertionError("expected create() to reject failed parse task")
