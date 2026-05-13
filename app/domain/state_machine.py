from __future__ import annotations

from datetime import datetime

from app.models import TaskStatus


class InvalidTaskTransitionError(ValueError):
    pass


_ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.created: {TaskStatus.parsing, TaskStatus.running, TaskStatus.failed},
    TaskStatus.parsing: {TaskStatus.finished, TaskStatus.failed},
    TaskStatus.running: {TaskStatus.finished, TaskStatus.failed},
    TaskStatus.finished: set(),
    TaskStatus.failed: set(),
}


def transition_task(
    task: object,
    target: TaskStatus,
    *,
    timestamp: datetime,
    message: str | None = None,
) -> None:
    current = getattr(task, "status")
    if current == target:
        if message is not None:
            setattr(task, "message", message)
        return
    if target not in _ALLOWED_TRANSITIONS.get(current, set()):
        raise InvalidTaskTransitionError(f"Illegal task status transition: {current} -> {target}")

    setattr(task, "status", target)
    if target in (TaskStatus.parsing, TaskStatus.running) and hasattr(task, "startedAt"):
        setattr(task, "startedAt", timestamp)
    if target in (TaskStatus.finished, TaskStatus.failed) and hasattr(task, "finishedAt"):
        setattr(task, "finishedAt", timestamp)
    if message is not None:
        setattr(task, "message", message)
