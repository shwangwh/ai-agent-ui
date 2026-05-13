from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from app.models import ExecutionCaseResult, ExecutionStatus, ExecutionTask


class ReportGenerator:
    def __init__(self, storage_root: str = "data") -> None:
        self.storage_root = Path(storage_root).absolute()

    def generate(self, task: ExecutionTask, results: list[ExecutionCaseResult]) -> tuple[str, str, str]:
        results_dir = self.storage_root / "allure-results" / task.taskId
        report_dir = self.storage_root / "allure-report" / task.taskId
        results_dir.mkdir(parents=True, exist_ok=True)
        report_dir.mkdir(parents=True, exist_ok=True)

        for result in results:
            (results_dir / f"{result.caseRunId}-result.json").write_text(
                json.dumps(self._allure_result(result), ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )

        (report_dir / "index.html").write_text(self._html_report(task, results), encoding="utf-8")
        return (
            f"/reports/allure/{task.taskId}/index.html",
            str(results_dir),
            str(report_dir),
        )

    def _allure_result(self, result: ExecutionCaseResult) -> dict[str, Any]:
        status = self._allure_status(result.status)
        return {
            "uuid": result.caseRunId,
            "name": result.caseName or result.caseId,
            "fullName": result.caseId,
            "status": status,
            "statusDetails": {"message": result.failureReason} if result.failureReason else {},
            "labels": [
                {"name": "module", "value": result.module or "未分组"},
                {"name": "priority", "value": result.priority or "P2"},
            ],
            "steps": [
                {
                    "name": f"{step.index}. {step.action}: {step.target or ''}",
                    "status": self._allure_status(step.status),
                    "statusDetails": {"message": step.message},
                }
                for step in result.steps
            ],
            "attachments": [
                {"name": url.rsplit("/", 1)[-1], "source": url, "type": self._attachment_type(url)}
                for url in result.evidenceUrls
            ],
        }

    def _html_report(self, task: ExecutionTask, results: list[ExecutionCaseResult]) -> str:
        rows = "\n".join(
            f"<tr><td>{html.escape(item.caseId)}</td><td>{html.escape(item.caseName or '')}</td>"
            f"<td>{html.escape(item.module or '')}</td><td class='{html.escape(str(item.status))}'>"
            f"{html.escape(str(item.status))}</td><td>{html.escape(item.failureReason or '')}</td></tr>"
            for item in results
        )
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>UI Automation Report - {html.escape(task.taskId)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; }}
    th {{ background: #f3f4f6; }}
    .passed {{ color: #047857; font-weight: 700; }}
    .failed, .assertion_failed, .locator_unresolved, .execution_error, .environment_error {{ color: #b91c1c; font-weight: 700; }}
    .blocked, .skipped {{ color: #92400e; font-weight: 700; }}
  </style>
</head>
<body>
  <h1>UI Automation Report</h1>
  <p>Task: {html.escape(task.taskId)}</p>
  <p>Total: {task.totalCases}, Passed: {task.passed}, Failed: {task.failed}, Blocked: {task.blocked}, Skipped: {task.skipped}</p>
  <table>
    <thead><tr><th>Case ID</th><th>Name</th><th>Module</th><th>Status</th><th>Failure Reason</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""

    def _allure_status(self, status: ExecutionStatus | str | None) -> str:
        if status in (ExecutionStatus.passed, "passed", ExecutionStatus.locator_healed, "locator_healed"):
            return "passed"
        if status in (ExecutionStatus.skipped, "skipped"):
            return "skipped"
        if status in (ExecutionStatus.blocked, "blocked", ExecutionStatus.environment_error, "environment_error"):
            return "broken"
        return "failed"

    def _attachment_type(self, url: str) -> str:
        if url.endswith(".png"):
            return "image/png"
        if url.endswith(".zip"):
            return "application/zip"
        if url.endswith(".txt"):
            return "text/plain"
        return "application/json"
