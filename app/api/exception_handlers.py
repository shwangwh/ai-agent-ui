from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.schemas import ApiError
from app.exceptions import BadRequestError, ResourceNotFoundError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BadRequestError)
    async def bad_request_handler(_: Request, exc: BadRequestError) -> JSONResponse:
        return JSONResponse(status_code=400, content=ApiError(code="BAD_REQUEST", message=str(exc)).model_dump())

    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(_: Request, exc: ResourceNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content=ApiError(code="NOT_FOUND", message=str(exc)).model_dump())
