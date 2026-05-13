from __future__ import annotations

from app.llm_agent import LLMAgentProtocol, OpenAICompatibleLLMAgent
from app.models import ParsedTestCase


class MarkdownCaseParser:
    def __init__(self, agent: LLMAgentProtocol | None = None) -> None:
        self.agent = agent or OpenAICompatibleLLMAgent()

    def parse(self, document_id: str, parse_task_id: str, markdown: str) -> list[ParsedTestCase]:
        return self.agent.parse_cases(document_id, parse_task_id, markdown)
