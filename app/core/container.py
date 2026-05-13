from __future__ import annotations

from dataclasses import dataclass

from app.core.config_service import RuntimeConfigService
from app.core.settings import Settings
from app.evidence import EvidenceCollector
from app.llm_agent import OpenAICompatibleLLMAgent
from app.parser import MarkdownCaseParser
from app.reporting import ReportGenerator
from app.runner import PlaywrightExecutionRunner
from app.services import DocumentService, ExecutionTaskService, LLMLogService, ParseTaskService, TaskLogService
from app.store import InMemoryAgentStore


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    store: InMemoryAgentStore
    logs: TaskLogService
    llm_logs: LLMLogService
    documents: DocumentService
    parse_tasks: ParseTaskService
    execution_tasks: ExecutionTaskService
    evidence: EvidenceCollector
    reports: ReportGenerator
    runtime_config: RuntimeConfigService


def build_container(settings: Settings) -> AppContainer:
    store = InMemoryAgentStore()
    logs = TaskLogService(store)
    llm_logs = LLMLogService(store, storage_root=str(settings.data_dir))
    documents = DocumentService(store, logs, storage_root=str(settings.data_dir))
    llm_agent = OpenAICompatibleLLMAgent(
        api_key=settings.llm.api_key,
        base_url=settings.llm.base_url,
        model=settings.llm.model,
        timeout_seconds=settings.llm.timeout_seconds,
        log_recorder=llm_logs,
    )
    parser = MarkdownCaseParser(llm_agent)
    parse_tasks = ParseTaskService(store, documents, parser, logs)
    evidence = EvidenceCollector(storage_root=str(settings.data_dir))
    reports = ReportGenerator(storage_root=str(settings.data_dir))
    runtime_config = RuntimeConfigService(settings.default_environment)
    runner = PlaywrightExecutionRunner(logs, evidence, agent=llm_agent)
    execution_tasks = ExecutionTaskService(
        store,
        parse_tasks,
        logs,
        evidence=evidence,
        reports=reports,
        environment_resolver=runtime_config.find_environment,
        runner=runner,
    )
    return AppContainer(
        settings=settings,
        store=store,
        logs=logs,
        llm_logs=llm_logs,
        documents=documents,
        parse_tasks=parse_tasks,
        execution_tasks=execution_tasks,
        evidence=evidence,
        reports=reports,
        runtime_config=runtime_config,
    )
