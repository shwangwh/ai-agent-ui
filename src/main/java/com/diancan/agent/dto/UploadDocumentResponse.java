package com.diancan.agent.dto;

import java.time.OffsetDateTime;

public record UploadDocumentResponse(
        String documentId,
        String fileName,
        long fileSize,
        OffsetDateTime createdAt,
        String message
) {
}
