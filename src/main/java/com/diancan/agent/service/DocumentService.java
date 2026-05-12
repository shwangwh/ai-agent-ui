package com.diancan.agent.service;

import com.diancan.agent.domain.LogLevel;
import com.diancan.agent.model.TestDocument;
import com.diancan.agent.repository.InMemoryAgentStore;
import com.diancan.agent.support.BadRequestException;
import com.diancan.agent.support.IdGenerator;
import com.diancan.agent.support.ResourceNotFoundException;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.OffsetDateTime;
import java.util.Map;

@Service
public class DocumentService {
    private final InMemoryAgentStore store;
    private final TaskLogService logs;
    private final Path storageRoot;

    public DocumentService(InMemoryAgentStore store, TaskLogService logs,
                           @Value("${agent.storage-root:data}") String storageRoot) {
        this.store = store;
        this.logs = logs;
        this.storageRoot = Path.of(storageRoot).toAbsolutePath().normalize();
    }

    public TestDocument upload(MultipartFile file) {
        if (file == null || file.isEmpty()) {
            throw new BadRequestException("Markdown 用例文档不能为空");
        }
        String originalName = file.getOriginalFilename() == null ? "cases.md" : file.getOriginalFilename();
        if (!originalName.toLowerCase().endsWith(".md")) {
            throw new BadRequestException("仅支持上传 .md Markdown 文件");
        }
        try {
            String documentId = IdGenerator.next("doc");
            Path documentDir = storageRoot.resolve("documents");
            Files.createDirectories(documentDir);
            Path path = documentDir.resolve(documentId + ".md").normalize();
            byte[] bytes = file.getBytes();
            Files.write(path, bytes);

            TestDocument document = new TestDocument();
            document.setDocumentId(documentId);
            document.setFileName(originalName);
            document.setFileSize(bytes.length);
            document.setContentType(file.getContentType());
            document.setStoragePath(path.toString());
            document.setContent(new String(bytes, StandardCharsets.UTF_8));
            document.setCreatedAt(OffsetDateTime.now());
            store.saveDocument(document);

            logs.log(LogLevel.INFO, documentId, documentId, null, null,
                    "DOCUMENT_UPLOADED", "Markdown 文档上传成功",
                    Map.of("fileName", originalName, "fileSize", bytes.length));
            return document;
        } catch (IOException ex) {
            throw new BadRequestException("Markdown 文档保存失败: " + ex.getMessage());
        }
    }

    public TestDocument get(String documentId) {
        return store.findDocument(documentId)
                .orElseThrow(() -> new ResourceNotFoundException("文档不存在: " + documentId));
    }
}
