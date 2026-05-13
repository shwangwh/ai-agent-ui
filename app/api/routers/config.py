from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.core.container import AppContainer


router = APIRouter(prefix="/api/v1/config", tags=["config"])


@router.get("/environments")
def get_environments(container: AppContainer = Depends(get_container)):
    return container.runtime_config.list_environments()


@router.post("/environments")
def create_environment(environment: dict[str, Any], container: AppContainer = Depends(get_container)):
    return container.runtime_config.upsert_environment(environment)


@router.get("/accounts")
def get_accounts(container: AppContainer = Depends(get_container)):
    return container.runtime_config.list_accounts()


@router.post("/accounts")
def create_account(account: dict[str, Any], container: AppContainer = Depends(get_container)):
    return container.runtime_config.add_account(account)
