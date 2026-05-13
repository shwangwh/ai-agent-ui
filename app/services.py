from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from app.evidence import EvidenceCollector
from app.exceptions import BadRequestError, ResourceNotFoundError
from app.domain.events import LogEvent
from app.domain.repositories import AgentStore
from app.domain.state_machine import transition_task
from app.id_generator import next_id
from app.models import (
    BrowserType,
    CaseFilter,
    ConfirmParseTaskRequest,
    CreateExecutionTaskRequest,
    ExecutionCaseResult,
    ExecutionStatus,
    ExecutionTask,
    LogLevel,
    ParseStatus,
    ParseTask,
    ParsedTestCase,
    ReportInfo,
    ReviewAction,
    RunMode,
    TaskLog,
    TaskStatus,
    TestDocument,
    now,
)
from app.parser import MarkdownCaseParser
from app.reporting import ReportGenerator
from app.runner import ExecutionContext, PlaywrightExecutionRunner


class TaskLogService:
    def __init__(self, store: AgentStore) -> None:
        self.store = store

    def log(
        self,
        level: LogLevel,
        trace_id: str,
        task_id: str,
        case_run_id: str | None,
        step_run_id: str | None,
        event: str,
        message: str,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self.store.add_log(
            TaskLog(
                logId=next_id("log"),
                level=level,
                traceId=trace_id,
                taskId=task_id,
                caseRunId=case_run_id,
                stepRunId=step_run_id,
                event=event,
                message=message,
                attributes=attributes or {},
                timestamp=now(),
            )
        )

    def find_logs(
        self,
        task_id: str,
        case_run_id: str | None = None,
        step_run_id: str | None = None,
        level: LogLevel | None = None,
        event: str | None = None,
    ) -> list[TaskLog]:
        logs = self.store.find_logs(task_id)
        return [
            log
            for log in logs
            if (case_run_id is None or log.caseRunId == case_run_id)
            and (step_run_id is None or log.stepRunId == step_run_id)
            and (level is None or log.level == level)
            and (event is None or log.event.lower() == event.lower())
        ]


class DocumentService:
    def __init__(self, store: AgentStore, logs: TaskLogService, storage_root: str = "data") -> None:
        self.store = store
        self.logs = logs
        self.storage_root = Path(storage_root).absolute()

    def upload(self, file_name: str, content_type: str | None, data: bytes) -> TestDocument:
        if not data:
            raise BadRequestError("Markdown 用例文档不能为空")
        original_name = file_name or "cases.md"
        if not original_name.lower().endswith(".md"):
            raise BadRequestError("仅支持上传 .md Markdown 文件")

        document_id = next_id("doc")
        document_dir = self.storage_root / "documents"
        document_dir.mkdir(parents=True, exist_ok=True)
        path = document_dir / f"{document_id}.md"
        path.write_bytes(data)

        document = TestDocument(
            documentId=document_id,
            fileName=original_name,
            fileSize=len(data),
            contentType=content_type,
            storagePath=str(path),
            content=data.decode("utf-8"),
            createdAt=now(),
        )
        self.store.save_document(document)
        self.logs.log(
            LogLevel.INFO,
            document_id,
            document_id,
            None,
            None,
            LogEvent.DOCUMENT_UPLOADED,
            "Markdown 文档上传成功",
            {"fileName": original_name, "fileSize": len(data)},
        )
        return document

    def get(self, document_id: str) -> TestDocument:
        document = self.store.find_document(document_id)
        if document is None:
            raise ResourceNotFoundError(f"文档不存在: {document_id}")
        return document


class ParseTaskService:
    def __init__(
        self,
        store: AgentStore,
        documents: DocumentService,
        parser: MarkdownCaseParser,
        logs: TaskLogService,
    ) -> None:
        self.store = store
        self.documents = documents
        self.parser = parser
        self.logs = logs

    def create_parse_task(self, document_id: str, parse_mode: str = "smart") -> ParseTask:
        document = self.documents.get(document_id)
        parse_task_id = next_id("parse")
        task = ParseTask(
            parseTaskId=parse_task_id,
            documentId=document_id,
            status=TaskStatus.created,
            createdAt=now(),
            message="解析任务已创建",
        )
        transition_task(task, TaskStatus.parsing, timestamp=now(), message="解析中")
        self.store.save_parse_task(task)
        self.logs.log(
            LogLevel.INFO,
            parse_task_id,
            parse_task_id,
            None,
            None,
            LogEvent.PARSE_TASK_CREATED,
            "创建解析任务",
            {"documentId": document_id, "parseMode": parse_mode or "smart"},
        )

        try:
            cases = self.parser.parse(document_id, parse_task_id, document.content)
            self.store.save_parsed_cases(parse_task_id, cases)
            self._summarize(task, cases)
            transition_task(task, TaskStatus.finished, timestamp=now(), message="解析完成")
            self.store.save_parse_task(task)
            self.logs.log(
                LogLevel.INFO,
                parse_task_id,
                parse_task_id,
                None,
                None,
                LogEvent.PARSE_TASK_FINISHED,
                "解析任务完成",
                {
                    "totalCases": task.totalCases,
                    "executableCases": task.executableCases,
                    "reviewCases": task.reviewCases,
                    "invalidCases": task.invalidCases,
                },
            )
        except Exception as exc:
            transition_task(task, TaskStatus.failed, timestamp=now(), message=f"解析失败: {exc}")
            self.store.save_parse_task(task)
            self.logs.log(
                LogLevel.ERROR,
                parse_task_id,
                parse_task_id,
                None,
                None,
                LogEvent.PARSE_TASK_FAILED,
                "解析任务失败",
                {"errorType": type(exc).__name__, "error": str(exc)},
            )
        return task

    def get_parse_task(self, parse_task_id: str) -> ParseTask:
        task = self.store.find_parse_task(parse_task_id)
        if task is None:
            raise ResourceNotFoundError(f"解析任务不存在: {parse_task_id}")
        return task

    def get_cases(self, parse_task_id: str) -> list[ParsedTestCase]:
        self.get_parse_task(parse_task_id)
        return self.store.find_parsed_cases(parse_task_id)

    def confirm(self, parse_task_id: str, request: ConfirmParseTaskRequest) -> list[ParsedTestCase]:
        task = self.get_parse_task(parse_task_id)
        if not request.cases:
            raise BadRequestError("确认列表不能为空")
        cases = {case.caseId: case for case in self.store.find_parsed_cases(parse_task_id)}

        for item in request.cases:
            test_case = cases.get(item.caseId)
            if test_case is None:
                raise ResourceNotFoundError(f"用例不存在: {item.caseId}")
            if item.action == ReviewAction.confirm:
                test_case.status = ParseStatus.executable
            elif item.action in (ReviewAction.revise, ReviewAction.save):
                self._apply_revision(test_case, item.model_dump())
                test_case.status = ParseStatus.executable
                test_case.parseConfidence = max(test_case.parseConfidence, 0.90)
            elif item.action == ReviewAction.skip:
                test_case.status = ParseStatus.skipped
            elif item.action == ReviewAction.mark_invalid:
                test_case.status = ParseStatus.invalid
            test_case.updatedAt = now()
            self.logs.log(
                LogLevel.INFO,
                parse_task_id,
                parse_task_id,
                None,
                None,
                LogEvent.CASE_REVIEWED,
                "用例解析结果已确认",
                {"caseId": test_case.caseId, "action": item.action, "status": test_case.status},
            )

        updated = list(cases.values())
        self.store.save_parsed_cases(parse_task_id, updated)
        self._summarize(task, updated)
        self.store.save_parse_task(task)
        return updated

    def _apply_revision(self, test_case: ParsedTestCase, data: dict[str, Any]) -> None:
        for field in ("caseName", "module", "priority", "preconditions", "steps", "expectedResults", "testData", "tags", "remarks"):
            if data.get(field) is not None:
                setattr(test_case, field, data[field])
        test_case.uncertainItems = []

    def _summarize(self, task: ParseTask, cases: list[ParsedTestCase]) -> None:
        task.totalCases = len(cases)
        task.executableCases = sum(1 for case in cases if case.status == ParseStatus.executable)
        task.reviewCases = sum(1 for case in cases if case.status == ParseStatus.need_review)
        task.invalidCases = sum(1 for case in cases if case.status == ParseStatus.invalid)


class ExecutionTaskService:
    def __init__(
        self,
        store: AgentStore,
        parse_tasks: ParseTaskService,
        logs: TaskLogService,
        evidence: EvidenceCollector | None = None,
        reports: ReportGenerator | None = None,
        environment_resolver: Callable[[str], dict[str, Any] | None] | None = None,
        runner: PlaywrightExecutionRunner | None = None,
    ) -> None:
        self.store = store
        self.parse_tasks = parse_tasks
        self.logs = logs
        self.evidence = evidence or EvidenceCollector()
        self.reports = reports or ReportGenerator()
        self.environment_resolver = environment_resolver or (lambda code: None)
        self.runner = runner or PlaywrightExecutionRunner(logs, self.evidence)

    def create(self, request: CreateExecutionTaskRequest) -> ExecutionTask:
        parse_task = self.parse_tasks.get_parse_task(request.parseTaskId)
        if parse_task.documentId != request.documentId:
            raise BadRequestError("documentId 与 parseTaskId 不匹配")
        environment_code = request.environmentCode or "test"
        environment = self.environment_resolver(environment_code)
        if environment is None:
            raise BadRequestError(f"执行环境不存在: {environment_code}")

        cases = self._filter_cases(self.parse_tasks.get_cases(request.parseTaskId), request.caseFilter)
        if not cases:
            raise BadRequestError("没有符合条件的可执行用例")

        task_id = next_id("exec")
        task = ExecutionTask(
            taskId=task_id,
            documentId=request.documentId,
            parseTaskId=request.parseTaskId,
            environmentCode=environment_code,
            runMode=request.runMode or RunMode.strict,
            browser=request.browser or BrowserType.chromium,
            headless=request.headless,
            status=TaskStatus.created,
            createdAt=now(),
            message="执行任务已创建",
        )
        transition_task(task, TaskStatus.running, timestamp=now(), message="执行中")
        self.store.save_execution_task(task)
        self.logs.log(
            LogLevel.INFO,
            task_id,
            task_id,
            None,
            None,
            LogEvent.EXECUTION_TASK_CREATED,
            "自动化执行任务已创建",
            {"environmentCode": task.environmentCode, "browser": task.browser, "runMode": task.runMode},
        )

        context = ExecutionContext(
            base_url=str(environment.get("baseUrl") or ""),
            domain_whitelist=list(environment.get("domainWhitelist") or []),
        )
        try:
            results = [self._run_case(task, test_case, context) for test_case in cases]
            self.store.save_execution_cases(task_id, results)
            self._summarize(task, results)
            task.allureReportUrl, _, _ = self.reports.generate(task, results)
            task.jsonResultUrl = f"/api/v1/execution-tasks/{task_id}/cases"
            transition_task(task, TaskStatus.finished, timestamp=now(), message="执行完成，报告和证据已生成")
            self.store.save_execution_task(task)
            self.logs.log(
                LogLevel.INFO,
                task_id,
                task_id,
                None,
                None,
                LogEvent.EXECUTION_TASK_FINISHED,
                "文档执行完成",
                {
                    "totalCases": task.totalCases,
                    "passed": task.passed,
                    "failed": task.failed,
                    "blocked": task.blocked,
                    "locatorUnresolved": task.locatorUnresolved,
                },
            )
        except Exception as exc:
            transition_task(task, TaskStatus.failed, timestamp=now(), message=f"执行失败: {exc}")
            self.store.save_execution_task(task)
            self.logs.log(
                LogLevel.ERROR,
                task_id,
                task_id,
                None,
                None,
                LogEvent.EXECUTION_TASK_FAILED,
                "自动化执行任务失败",
                {"errorType": type(exc).__name__, "error": str(exc)},
            )
        return task

    def get(self, task_id: str) -> ExecutionTask:
        task = self.store.find_execution_task(task_id)
        if task is None:
            raise ResourceNotFoundError(f"执行任务不存在: {task_id}")
        return task

    def get_cases(self, task_id: str) -> list[ExecutionCaseResult]:
        self.get(task_id)
        return self.store.find_execution_cases(task_id)

    def get_report(self, task_id: str) -> ReportInfo:
        task = self.get(task_id)
        return ReportInfo(
            taskId=task_id,
            type="allure",
            status=task.status,
            allureReportUrl=task.allureReportUrl,
            jsonResultUrl=task.jsonResultUrl,
            resultsDir=f"data/allure-results/{task_id}",
            reportDir=f"data/allure-report/{task_id}",
        )

    def _run_case(self, task: ExecutionTask, test_case: ParsedTestCase, context: ExecutionContext) -> ExecutionCaseResult:
        if test_case.status == ParseStatus.skipped:
            return self._blocked_case(task, test_case, ExecutionStatus.skipped, "Case was skipped by the LLM parse plan")
        if test_case.status != ParseStatus.executable:
            return self._blocked_case(task, test_case, ExecutionStatus.blocked, f"Case is not executable: {test_case.status}")
        return self.runner.run_case(task, test_case, context)

    def _blocked_case(
        self,
        task: ExecutionTask,
        test_case: ParsedTestCase,
        status: ExecutionStatus,
        reason: str,
    ) -> ExecutionCaseResult:
        started_at = now()
        case_run_id = next_id("case_run")
        result = ExecutionCaseResult(
            caseRunId=case_run_id,
            taskId=task.taskId,
            caseId=test_case.caseId,
            caseName=test_case.caseName,
            module=test_case.module,
            priority=test_case.priority,
            status=status,
            failureReason=reason,
            startedAt=started_at,
            finishedAt=now(),
        )
        result.evidenceUrls.append(
            self.evidence.write_json(task.taskId, case_run_id, "summary.json", result.model_dump())
        )
        self.logs.log(
            LogLevel.WARN,
            task.taskId,
            task.taskId,
            case_run_id,
            None,
            LogEvent.CASE_EXECUTION_FINISHED,
            "用例未执行",
            {"status": status, "reason": reason},
        )
        return result

    def _filter_cases(self, cases: list[ParsedTestCase], case_filter: CaseFilter | None) -> list[ParsedTestCase]:
        if case_filter is None:
            return cases
        filtered = cases
        if case_filter.priorities:
            filtered = [case for case in filtered if case.priority in case_filter.priorities]
        if case_filter.tags:
            filtered = [case for case in filtered if any(tag in case_filter.tags for tag in case.tags)]
        return filtered

    def _summarize(self, task: ExecutionTask, results: list[ExecutionCaseResult]) -> None:
        task.totalCases = len(results)
        task.passed = sum(1 for item in results if item.status in (ExecutionStatus.passed, ExecutionStatus.locator_healed))
        task.failed = sum(
            1
            for item in results
            if item.status
            in (
                ExecutionStatus.failed,
                ExecutionStatus.assertion_failed,
                ExecutionStatus.execution_error,
                ExecutionStatus.environment_error,
                ExecutionStatus.locator_unresolved,
            )
        )
        task.blocked = sum(1 for item in results if item.status == ExecutionStatus.blocked)
        task.locatorHealed = sum(1 for item in results if item.status == ExecutionStatus.locator_healed)
        task.locatorUnresolved = sum(1 for item in results if item.status == ExecutionStatus.locator_unresolved)
        task.skipped = sum(1 for item in results if item.status == ExecutionStatus.skipped)
