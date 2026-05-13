from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies import get_container
from app.api.schemas import CreateParseTaskRequest, CreateTaskResponse, UploadDocumentResponse
from app.core.container import AppContainer


router = APIRouter(prefix="/api/v1/test-documents", tags=["test-documents"])


@router.post("", response_model=UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    container: AppContainer = Depends(get_container),
) -> UploadDocumentResponse:
    document = container.documents.upload(file.filename or "cases.md", file.content_type, await file.read())
    return UploadDocumentResponse(
        documentId=document.documentId,
        fileName=document.fileName,
        fileSize=document.fileSize,
        createdAt=document.createdAt,
        message="文档上传成功",
    )


@router.get("/{document_id}")
def get_document(document_id: str, container: AppContainer = Depends(get_container)):
    return container.documents.get(document_id)


@router.post("/{document_id}/parse", response_model=CreateTaskResponse)
def create_parse_task(
    document_id: str,
    request: CreateParseTaskRequest | None = None,
    container: AppContainer = Depends(get_container),
) -> CreateTaskResponse:
    task = container.parse_tasks.create_parse_task(document_id, request.parseMode if request else "smart")
    return CreateTaskResponse(taskId=task.parseTaskId, status=task.status, message=task.message)
