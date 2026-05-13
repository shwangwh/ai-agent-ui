from __future__ import annotations

from dataclasses import dataclass

from app.core.config_service import RuntimeConfigService
from app.core.settings import Settings
from app.evidence import EvidenceCollector
from app.parser import MarkdownCaseParser
from app.reporting import ReportGenerator
from app.services import DocumentService, ExecutionTaskService, ParseTaskService, TaskLogService
from app.store import InMemoryAgentStore


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    store: InMemoryAgentStore
    logs: TaskLogService
    documents: DocumentService
    parse_tasks: ParseTaskService
    execution_tasks: ExecutionTaskService
    evidence: EvidenceCollector
    reports: ReportGenerator
    runtime_config: RuntimeConfigService


def build_container(settings: Settings) -> AppContainer:
    store = InMemoryAgentStore()
    logs = TaskLogService(store)
    documents = DocumentService(store, logs, storage_root=str(settings.data_dir))
    parser = MarkdownCaseParser()
    parse_tasks = ParseTaskService(store, documents, parser, logs)
    evidence = EvidenceCollector(storage_root=str(settings.data_dir))
    reports = ReportGenerator(storage_root=str(settings.data_dir))
    runtime_config = RuntimeConfigService(settings.default_environment)
    execution_tasks = ExecutionTaskService(
        store,
        parse_tasks,
        logs,
        evidence=evidence,
        reports=reports,
        environment_resolver=runtime_config.find_environment,
    )
    return AppContainer(
        settings=settings,
        store=store,
        logs=logs,
        documents=documents,
        parse_tasks=parse_tasks,
        execution_tasks=execution_tasks,
        evidence=evidence,
        reports=reports,
        runtime_config=runtime_config,
    )
