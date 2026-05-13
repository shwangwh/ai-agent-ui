from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


class BrowserType(StrEnum):
    chromium = "chromium"
    firefox = "firefox"
    webkit = "webkit"


class ExecutionStatus(StrEnum):
    passed = "passed"
    failed = "failed"
    blocked = "blocked"
    locator_healed = "locator_healed"
    locator_unresolved = "locator_unresolved"
    assertion_failed = "assertion_failed"
    execution_error = "execution_error"
    environment_error = "environment_error"
    test_data_error = "test_data_error"
    skipped = "skipped"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class ParseStatus(StrEnum):
    executable = "executable"
    need_review = "need_review"
    invalid = "invalid"
    skipped = "skipped"


class ReviewAction(StrEnum):
    confirm = "confirm"
    revise = "revise"
    skip = "skip"
    mark_invalid = "mark_invalid"
    save = "save"


class RunMode(StrEnum):
    smart = "smart"
    strict = "strict"


class TaskStatus(StrEnum):
    created = "created"
    parsing = "parsing"
    running = "running"
    finished = "finished"
    failed = "failed"


class AgentModel(BaseModel):
    model_config = ConfigDict(use_enum_values=True)


class ApiError(AgentModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class UploadDocumentResponse(AgentModel):
    documentId: str
    fileName: str
    fileSize: int
    createdAt: datetime
    message: str


class CreateTaskResponse(AgentModel):
    taskId: str
    status: str
    message: str | None = None


class TestDocument(AgentModel):
    documentId: str
    fileName: str
    fileSize: int
    contentType: str | None = None
    storagePath: str
    content: str
    createdAt: datetime


class ParseTask(AgentModel):
    parseTaskId: str
    documentId: str
    status: TaskStatus
    totalCases: int = 0
    executableCases: int = 0
    reviewCases: int = 0
    invalidCases: int = 0
    createdAt: datetime
    finishedAt: datetime | None = None
    message: str | None = None


class ParsedTestCase(AgentModel):
    caseId: str
    documentId: str
    parseTaskId: str
    caseName: str | None = None
    module: str | None = None
    priority: str | None = None
    rawMarkdown: str
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    expectedResults: list[str] = Field(default_factory=list)
    testData: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    remarks: str | None = None
    parseConfidence: float = 0.0
    status: ParseStatus | None = None
    uncertainItems: list[str] = Field(default_factory=list)
    updatedAt: datetime


class CaseReviewItem(AgentModel):
    caseId: str
    action: ReviewAction
    caseName: str | None = None
    module: str | None = None
    priority: str | None = None
    preconditions: list[str] | None = None
    steps: list[str] | None = None
    expectedResults: list[str] | None = None
    testData: list[str] | None = None
    tags: list[str] | None = None
    remarks: str | None = None


class ConfirmParseTaskRequest(AgentModel):
    cases: list[CaseReviewItem]


class CreateParseTaskRequest(AgentModel):
    parseMode: str = "smart"


class CaseFilter(AgentModel):
    priorities: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ReportOptions(AgentModel):
    type: str = "allure"
    generateAfterDocumentFinished: bool = True


class CreateExecutionTaskRequest(AgentModel):
    documentId: str
    parseTaskId: str
    environmentCode: str | None = "test"
    runMode: RunMode | None = RunMode.strict
    browser: BrowserType | None = BrowserType.chromium
    headless: bool = True
    caseFilter: CaseFilter | None = None
    report: ReportOptions | None = None


class StepExecutionResult(AgentModel):
    stepRunId: str
    index: int
    action: str
    target: str | None = None
    value: str | None = None
    status: ExecutionStatus
    durationMs: int
    message: str


class AssertionResult(AgentModel):
    assertionType: str
    expected: str
    actual: str
    status: ExecutionStatus


class ExecutionCaseResult(AgentModel):
    caseRunId: str
    taskId: str
    caseId: str
    caseName: str | None = None
    module: str | None = None
    priority: str | None = None
    status: ExecutionStatus | None = None
    durationMs: int = 0
    steps: list[StepExecutionResult] = Field(default_factory=list)
    assertions: list[AssertionResult] = Field(default_factory=list)
    evidenceUrls: list[str] = Field(default_factory=list)
    failureReason: str | None = None
    startedAt: datetime
    finishedAt: datetime | None = None


class ExecutionTask(AgentModel):
    taskId: str
    documentId: str
    parseTaskId: str
    environmentCode: str
    runMode: RunMode
    browser: BrowserType
    headless: bool
    status: TaskStatus
    totalCases: int = 0
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    locatorHealed: int = 0
    locatorUnresolved: int = 0
    skipped: int = 0
    createdAt: datetime
    startedAt: datetime | None = None
    finishedAt: datetime | None = None
    allureReportUrl: str | None = None
    jsonResultUrl: str | None = None
    message: str | None = None


class ReportInfo(AgentModel):
    taskId: str
    type: str
    status: str
    allureReportUrl: str | None = None
    jsonResultUrl: str | None = None
    resultsDir: str
    reportDir: str


class TaskLog(AgentModel):
    logId: str
    level: LogLevel
    traceId: str
    taskId: str
    caseRunId: str | None = None
    stepRunId: str | None = None
    event: str
    message: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class LLMCallLog(AgentModel):
    logId: str
    traceId: str
    taskId: str
    operation: str
    model: str
    endpoint: str
    success: bool
    durationMs: int
    documentId: str | None = None
    parseTaskId: str | None = None
    caseId: str | None = None
    caseRunId: str | None = None
    stepRunId: str | None = None
    requestPayload: dict[str, Any] = Field(default_factory=dict)
    responsePayload: dict[str, Any] | None = None
    rawResponse: str | None = None
    errorType: str | None = None
    errorMessage: str | None = None
    timestamp: datetime
