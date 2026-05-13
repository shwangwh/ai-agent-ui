from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any

from fastapi import FastAPI, Request


request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    _reserved_keys = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = request_id_var.get()
        if request_id:
            payload["requestId"] = request_id
        payload.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in self._reserved_keys and not key.startswith("_")
            }
        )
        if record.exc_info:
            payload["excInfo"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


def install_request_logging(app: FastAPI) -> None:
    logger = logging.getLogger("app.http")

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("x-request-id") or f"req_{uuid.uuid4().hex}"
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - started) * 1000)
            logger.exception(
                "HTTP request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "durationMs": duration_ms,
                },
            )
            request_id_var.reset(token)
            raise
        duration_ms = int((time.perf_counter() - started) * 1000)
        response.headers["x-request-id"] = request_id
        logger.info(
            "HTTP request finished",
            extra={
                "method": request.method,
                "path": request.url.path,
                "statusCode": response.status_code,
                "durationMs": duration_ms,
            },
        )
        request_id_var.reset(token)
        return response
