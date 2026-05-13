from __future__ import annotations

from collections import defaultdict

from app.models import ExecutionCaseResult, ExecutionTask, ParseTask, ParsedTestCase, TaskLog, TestDocument


class InMemoryAgentStore:
    def __init__(self) -> None:
        self.documents: dict[str, TestDocument] = {}
        self.parse_tasks: dict[str, ParseTask] = {}
        self.parsed_cases_by_task: dict[str, list[ParsedTestCase]] = {}
        self.execution_tasks: dict[str, ExecutionTask] = {}
        self.execution_cases_by_task: dict[str, list[ExecutionCaseResult]] = {}
        self.logs_by_task: dict[str, list[TaskLog]] = defaultdict(list)

    def save_document(self, document: TestDocument) -> TestDocument:
        self.documents[document.documentId] = document
        return document

    def find_document(self, document_id: str) -> TestDocument | None:
        return self.documents.get(document_id)

    def save_parse_task(self, parse_task: ParseTask) -> ParseTask:
        self.parse_tasks[parse_task.parseTaskId] = parse_task
        return parse_task

    def find_parse_task(self, parse_task_id: str) -> ParseTask | None:
        return self.parse_tasks.get(parse_task_id)

    def save_parsed_cases(self, parse_task_id: str, cases: list[ParsedTestCase]) -> None:
        self.parsed_cases_by_task[parse_task_id] = list(cases)

    def find_parsed_cases(self, parse_task_id: str) -> list[ParsedTestCase]:
        return list(self.parsed_cases_by_task.get(parse_task_id, []))

    def save_execution_task(self, task: ExecutionTask) -> ExecutionTask:
        self.execution_tasks[task.taskId] = task
        return task

    def find_execution_task(self, task_id: str) -> ExecutionTask | None:
        return self.execution_tasks.get(task_id)

    def save_execution_cases(self, task_id: str, cases: list[ExecutionCaseResult]) -> None:
        self.execution_cases_by_task[task_id] = list(cases)

    def find_execution_cases(self, task_id: str) -> list[ExecutionCaseResult]:
        return list(self.execution_cases_by_task.get(task_id, []))

    def add_log(self, log: TaskLog) -> None:
        self.logs_by_task[log.taskId].append(log)

    def find_logs(self, task_id: str) -> list[TaskLog]:
        return sorted(self.logs_by_task.get(task_id, []), key=lambda log: log.timestamp)
