import pytest

from app.domain.state_machine import InvalidTaskTransitionError, transition_task
from app.models import ExecutionTask, TaskStatus, now


def build_task(status: TaskStatus = TaskStatus.created) -> ExecutionTask:
    return ExecutionTask(
        taskId="exec_1",
        documentId="doc_1",
        parseTaskId="parse_1",
        environmentCode="test",
        runMode="strict",
        browser="chromium",
        headless=True,
        status=status,
        createdAt=now(),
    )


def test_task_state_machine_allows_running_to_finished():
    task = build_task(TaskStatus.running)

    transition_task(task, TaskStatus.finished, timestamp=now(), message="done")

    assert task.status == TaskStatus.finished
    assert task.finishedAt is not None
    assert task.message == "done"


def test_task_state_machine_rejects_finished_to_running():
    task = build_task(TaskStatus.finished)

    with pytest.raises(InvalidTaskTransitionError):
        transition_task(task, TaskStatus.running, timestamp=now())
