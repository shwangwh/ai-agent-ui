from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.exception_handlers import register_exception_handlers
from app.api.routers import config, documents, execution_tasks, health, parse_tasks
from app.core.container import AppContainer, build_container
from app.core.logging import configure_logging, install_request_logging
from app.core.settings import Settings, load_settings


def create_app(settings: Settings | None = None, container: AppContainer | None = None) -> FastAPI:
    configure_logging()
    settings = settings or load_settings()
    container = container or build_container(settings)

    app = FastAPI(title=settings.app_title, version=settings.app_version)
    app.state.container = container

    register_exception_handlers(app)
    install_request_logging(app)
    _mount_static(app, settings)
    _include_routers(app)
    return app


def _include_routers(app: FastAPI) -> None:
    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(parse_tasks.router)
    app.include_router(execution_tasks.router)
    app.include_router(config.router)


def _mount_static(app: FastAPI, settings: Settings) -> None:
    artifacts_dir = settings.data_dir / "artifacts"
    reports_dir = settings.data_dir / "allure-report"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/artifacts", StaticFiles(directory=str(artifacts_dir)), name="artifacts")
    app.mount("/reports/allure", StaticFiles(directory=str(reports_dir)), name="allure-reports")
