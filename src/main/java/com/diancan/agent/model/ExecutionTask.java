package com.diancan.agent.model;

import com.diancan.agent.domain.BrowserType;
import com.diancan.agent.domain.RunMode;
import com.diancan.agent.domain.TaskStatus;

import java.time.OffsetDateTime;

public class ExecutionTask {
    private String taskId;
    private String documentId;
    private String parseTaskId;
    private String environmentCode;
    private RunMode runMode;
    private BrowserType browser;
    private boolean headless;
    private TaskStatus status;
    private int totalCases;
    private int passed;
    private int failed;
    private int blocked;
    private int locatorHealed;
    private int locatorUnresolved;
    private int skipped;
    private OffsetDateTime createdAt;
    private OffsetDateTime startedAt;
    private OffsetDateTime finishedAt;
    private String allureReportUrl;
    private String jsonResultUrl;
    private String message;

    public String getTaskId() {
        return taskId;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public String getDocumentId() {
        return documentId;
    }

    public void setDocumentId(String documentId) {
        this.documentId = documentId;
    }

    public String getParseTaskId() {
        return parseTaskId;
    }

    public void setParseTaskId(String parseTaskId) {
        this.parseTaskId = parseTaskId;
    }

    public String getEnvironmentCode() {
        return environmentCode;
    }

    public void setEnvironmentCode(String environmentCode) {
        this.environmentCode = environmentCode;
    }

    public RunMode getRunMode() {
        return runMode;
    }

    public void setRunMode(RunMode runMode) {
        this.runMode = runMode;
    }

    public BrowserType getBrowser() {
        return browser;
    }

    public void setBrowser(BrowserType browser) {
        this.browser = browser;
    }

    public boolean isHeadless() {
        return headless;
    }

    public void setHeadless(boolean headless) {
        this.headless = headless;
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

    public int getPassed() {
        return passed;
    }

    public void setPassed(int passed) {
        this.passed = passed;
    }

    public int getFailed() {
        return failed;
    }

    public void setFailed(int failed) {
        this.failed = failed;
    }

    public int getBlocked() {
        return blocked;
    }

    public void setBlocked(int blocked) {
        this.blocked = blocked;
    }

    public int getLocatorHealed() {
        return locatorHealed;
    }

    public void setLocatorHealed(int locatorHealed) {
        this.locatorHealed = locatorHealed;
    }

    public int getLocatorUnresolved() {
        return locatorUnresolved;
    }

    public void setLocatorUnresolved(int locatorUnresolved) {
        this.locatorUnresolved = locatorUnresolved;
    }

    public int getSkipped() {
        return skipped;
    }

    public void setSkipped(int skipped) {
        this.skipped = skipped;
    }

    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public OffsetDateTime getStartedAt() {
        return startedAt;
    }

    public void setStartedAt(OffsetDateTime startedAt) {
        this.startedAt = startedAt;
    }

    public OffsetDateTime getFinishedAt() {
        return finishedAt;
    }

    public void setFinishedAt(OffsetDateTime finishedAt) {
        this.finishedAt = finishedAt;
    }

    public String getAllureReportUrl() {
        return allureReportUrl;
    }

    public void setAllureReportUrl(String allureReportUrl) {
        this.allureReportUrl = allureReportUrl;
    }

    public String getJsonResultUrl() {
        return jsonResultUrl;
    }

    public void setJsonResultUrl(String jsonResultUrl) {
        this.jsonResultUrl = jsonResultUrl;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
