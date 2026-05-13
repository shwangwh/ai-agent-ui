from __future__ import annotations

from typing import Any

from app.core.settings import EnvironmentSettings
from app.exceptions import BadRequestError


class RuntimeConfigService:
    def __init__(self, default_environment: EnvironmentSettings) -> None:
        self._environments: list[dict[str, Any]] = [default_environment.model_dump()]
        self._accounts: list[dict[str, Any]] = []

    def list_environments(self) -> list[dict[str, Any]]:
        return self._environments

    def find_environment(self, environment_code: str) -> dict[str, Any] | None:
        return next(
            (item for item in self._environments if item.get("environmentCode") == environment_code),
            None,
        )

    def upsert_environment(self, environment: dict[str, Any]) -> dict[str, Any]:
        if not environment.get("environmentCode"):
            raise BadRequestError("environmentCode 不能为空")
        if not environment.get("baseUrl"):
            raise BadRequestError("baseUrl 不能为空")

        existing = self.find_environment(environment["environmentCode"])
        if existing:
            existing.update(environment)
            return existing

        self._environments.append(environment)
        return environment

    def list_accounts(self) -> list[dict[str, Any]]:
        return self._accounts

    def add_account(self, account: dict[str, Any]) -> dict[str, Any]:
        masked = dict(account)
        if "password" in masked:
            masked["password"] = "******"
        self._accounts.append(masked)
        return masked
