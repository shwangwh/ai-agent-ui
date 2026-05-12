package com.diancan.agent.model;

import com.diancan.agent.domain.TaskStatus;

import java.time.OffsetDateTime;

public class ParseTask {
    private String parseTaskId;
    private String documentId;
    private TaskStatus status;
    private int totalCases;
    private int executableCases;
    private int reviewCases;
    private int invalidCases;
    private OffsetDateTime createdAt;
    private OffsetDateTime finishedAt;
    private String message;

    public String getParseTaskId() {
        return parseTaskId;
    }

    public void setParseTaskId(String parseTaskId) {
        this.parseTaskId = parseTaskId;
    }

    public String getDocumentId() {
        return documentId;
    }

    public void setDocumentId(String documentId) {
        this.documentId = documentId;
    }

    public TaskStatus getStatus() {
        return status;
    }

    public void setStatus(TaskStatus status) {
        this.status = status;
    }

    public int getTotalCases() {
        return totalCases;
    }

    public void setTotalCases(int totalCases) {
        this.totalCases = totalCases;
    }

    public int getExecutableCases() {
        return executableCases;
    }

    public void setExecutableCases(int executableCases) {
        this.executableCases = executableCases;
    }

    public int getReviewCases() {
        return reviewCases;
    }

    public void setReviewCases(int reviewCases) {
        this.reviewCases = reviewCases;
    }

    public int getInvalidCases() {
        return invalidCases;
    }

    public void setInvalidCases(int invalidCases) {
        this.invalidCases = invalidCases;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public OffsetDateTime getFinishedAt() {
        return finishedAt;
    }

    public void setFinishedAt(OffsetDateTime finishedAt) {
        this.finishedAt = finishedAt;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
