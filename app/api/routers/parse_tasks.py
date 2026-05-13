from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.api.schemas import ConfirmParseTaskRequest
from app.core.container import AppContainer


router = APIRouter(prefix="/api/v1/parse-tasks", tags=["parse-tasks"])


@router.get("/{parse_task_id}")
def get_parse_task(parse_task_id: str, container: AppContainer = Depends(get_container)):
    return container.parse_tasks.get_parse_task(parse_task_id)


@router.get("/{parse_task_id}/cases")
def get_parse_cases(parse_task_id: str, container: AppContainer = Depends(get_container)):
    return container.parse_tasks.get_cases(parse_task_id)


@router.get("/{parse_task_id}/llm-logs")
def get_parse_llm_logs(
    parse_task_id: str,
    success: bool | None = None,
    operation: str | None = None,
    container: AppContainer = Depends(get_container),
):
    container.parse_tasks.get_parse_task(parse_task_id)
    return container.llm_logs.find_logs(parse_task_id, success=success, operation=operation)


@router.post("/{parse_task_id}/confirm")
def confirm_parse_cases(
    parse_task_id: str,
    request: ConfirmParseTaskRequest,
    container: AppContainer = Depends(get_container),
):
    return container.parse_tasks.confirm(parse_task_id, request)
