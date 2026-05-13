from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_container
from app.api.schemas import CreateExecutionTaskRequest, CreateTaskResponse
from app.core.container import AppContainer
from app.domain.models import LogLevel


router = APIRouter(prefix="/api/v1/execution-tasks", tags=["execution-tasks"])


@router.post("", response_model=CreateTaskResponse)
def create_execution_task(
    request: CreateExecutionTaskRequest,
    container: AppContainer = Depends(get_container),
) -> CreateTaskResponse:
    if not request.documentId or not request.parseTaskId:
        raise HTTPException(status_code=422, detail="documentId 和 parseTaskId 不能为空")
    task = container.execution_tasks.create(request)
    return CreateTaskResponse(taskId=task.taskId, status=task.status, message=task.message)


@router.get("/{task_id}")
def get_execution_task(task_id: str, container: AppContainer = Depends(get_container)):
    return container.execution_tasks.get(task_id)


@router.get("/{task_id}/cases")
def get_execution_cases(task_id: str, container: AppContainer = Depends(get_container)):
    return container.execution_tasks.get_cases(task_id)


@router.get("/{task_id}/logs")
def get_execution_logs(
    task_id: str,
    caseRunId: str | None = None,
    stepRunId: str | None = None,
    level: LogLevel | None = None,
    event: str | None = None,
    container: AppContainer = Depends(get_container),
):
    container.execution_tasks.get(task_id)
    return container.logs.find_logs(task_id, caseRunId, stepRunId, level, event)


@router.get("/{task_id}/report")
def get_execution_report(task_id: str, container: AppContainer = Depends(get_container)):
    return container.execution_tasks.get_report(task_id)


@router.get("/{task_id}/artifacts")
def get_execution_artifacts(task_id: str, container: AppContainer = Depends(get_container)) -> dict[str, Any]:
    container.execution_tasks.get(task_id)
    return {
        "taskId": task_id,
        "artifacts": container.evidence.list_task_artifacts(task_id),
    }
