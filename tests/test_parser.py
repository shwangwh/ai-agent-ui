from typing import Any

from app.llm_agent import AssertionPlan, StepPlan
from app.models import ParseStatus, ParsedTestCase, now
from app.parser import MarkdownCaseParser


class FakeLLMAgent:
    def parse_cases(self, document_id: str, parse_task_id: str, markdown: str) -> list[ParsedTestCase]:
        return [
            ParsedTestCase(
                caseId="ORDER_001",
                documentId=document_id,
                parseTaskId=parse_task_id,
                caseName="submit order",
                module="ordering",
                priority="P0",
                rawMarkdown=markdown,
                steps=["open /", "click submit"],
                expectedResults=["success visible"],
                parseConfidence=0.96,
                status=ParseStatus.executable,
                updatedAt=now(),
            )
        ]

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


def test_parser_delegates_markdown_understanding_to_llm_agent():
    parser = MarkdownCaseParser(FakeLLMAgent())

    cases = parser.parse("doc_1", "parse_1", "free-form markdown")

    assert len(cases) == 1
    assert cases[0].caseId == "ORDER_001"
    assert cases[0].status == ParseStatus.executable
    assert cases[0].steps == ["open /", "click submit"]
