package com.diancan.agent.controller;

import com.diancan.agent.dto.CreateParseTaskRequest;
import com.diancan.agent.dto.CreateTaskResponse;
import com.diancan.agent.dto.UploadDocumentResponse;
import com.diancan.agent.model.ParseTask;
import com.diancan.agent.model.TestDocument;
import com.diancan.agent.service.DocumentService;
import com.diancan.agent.service.ParseTaskService;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/v1/test-documents")
public class TestDocumentController {
    private final DocumentService documents;
    private final ParseTaskService parseTasks;

    public TestDocumentController(DocumentService documents, ParseTaskService parseTasks) {
        this.documents = documents;
        this.parseTasks = parseTasks;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public UploadDocumentResponse upload(@RequestPart("file") MultipartFile file) {
        TestDocument document = documents.upload(file);
        return new UploadDocumentResponse(
                document.getDocumentId(),
                document.getFileName(),
                document.getFileSize(),
                document.getCreatedAt(),
                "文档上传成功"
        );
    }

    @GetMapping("/{documentId}")
    public TestDocument get(@PathVariable String documentId) {
        return documents.get(documentId);
    }

    @PostMapping("/{documentId}/parse")
    public CreateTaskResponse parse(@PathVariable String documentId, @RequestBody(required = false) CreateParseTaskRequest request) {
        ParseTask task = parseTasks.createParseTask(documentId, request == null ? "smart" : request.parseMode());
        return new CreateTaskResponse(task.getParseTaskId(), task.getStatus().name(), task.getMessage());
    }
}
