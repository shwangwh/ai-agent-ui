from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EvidenceCollector:
    def __init__(self, storage_root: str = "data") -> None:
        self.storage_root = Path(storage_root).absolute()

    def task_dir(self, task_id: str) -> Path:
        path = self.storage_root / "artifacts" / task_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def case_dir(self, task_id: str, case_run_id: str) -> Path:
        path = self.task_dir(task_id) / case_run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_json(self, task_id: str, case_run_id: str, name: str, data: dict[str, Any]) -> str:
        path = self.case_dir(task_id, case_run_id) / name
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return self._artifact_url(task_id, case_run_id, name)

    def write_text(self, task_id: str, case_run_id: str, name: str, content: str) -> str:
        path = self.case_dir(task_id, case_run_id) / name
        path.write_text(content, encoding="utf-8")
        return self._artifact_url(task_id, case_run_id, name)

    def screenshot_path(self, task_id: str, case_run_id: str, name: str = "final.png") -> Path:
        path = self.case_dir(task_id, case_run_id) / "screenshots" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def trace_path(self, task_id: str, case_run_id: str) -> Path:
        path = self.case_dir(task_id, case_run_id) / "trace.zip"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def artifact_url(self, task_id: str, case_run_id: str, relative_path: str) -> str:
        return self._artifact_url(task_id, case_run_id, relative_path)

    def list_task_artifacts(self, task_id: str) -> list[dict[str, Any]]:
        root = self.task_dir(task_id)
        artifacts: list[dict[str, Any]] = []
        for path in sorted(root.rglob("*")):
            if path.is_file():
                relative = path.relative_to(root).as_posix()
                artifacts.append(
                    {
                        "name": path.name,
                        "path": str(path),
                        "url": f"/artifacts/{task_id}/{relative}",
                        "size": path.stat().st_size,
                    }
                )
        return artifacts

    def _artifact_url(self, task_id: str, case_run_id: str, name: str) -> str:
        return f"/artifacts/{task_id}/{case_run_id}/{name}"
