package com.diancan.agent.model;

import com.diancan.agent.domain.ExecutionStatus;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

public class ExecutionCaseResult {
    private String caseRunId;
    private String taskId;
    private String caseId;
    private String caseName;
    private String module;
    private String priority;
    private ExecutionStatus status;
    private long durationMs;
    private List<StepExecutionResult> steps = new ArrayList<>();
    private List<AssertionResult> assertions = new ArrayList<>();
    private List<String> evidenceUrls = new ArrayList<>();
    private String failureReason;
    private OffsetDateTime startedAt;
    private OffsetDateTime finishedAt;

    public String getCaseRunId() {
        return caseRunId;
    }

    public void setCaseRunId(String caseRunId) {
        this.caseRunId = caseRunId;
    }

    public String getTaskId() {
        return taskId;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

    public String getCaseId() {
        return caseId;
    }

    public void setCaseId(String caseId) {
        this.caseId = caseId;
    }

    public String getCaseName() {
        return caseName;
    }

    public void setCaseName(String caseName) {
        this.caseName = caseName;
    }

    public String getModule() {
        return module;
    }

    public void setModule(String module) {
        this.module = module;
    }

    public String getPriority() {
        return priority;
    }

    public void setPriority(String priority) {
        this.priority = priority;
    }

    public ExecutionStatus getStatus() {
        return status;
    }

    public void setStatus(ExecutionStatus status) {
        this.status = status;
    }

    public long getDurationMs() {
        return durationMs;
    }

    public void setDurationMs(long durationMs) {
        this.durationMs = durationMs;
    }

    public List<StepExecutionResult> getSteps() {
        return steps;
    }

    public void setSteps(List<StepExecutionResult> steps) {
        this.steps = steps == null ? new ArrayList<>() : steps;
    }

    public List<AssertionResult> getAssertions() {
        return assertions;
    }

    public void setAssertions(List<AssertionResult> assertions) {
        this.assertions = assertions == null ? new ArrayList<>() : assertions;
    }

    public List<String> getEvidenceUrls() {
        return evidenceUrls;
    }

    public void setEvidenceUrls(List<String> evidenceUrls) {
        this.evidenceUrls = evidenceUrls == null ? new ArrayList<>() : evidenceUrls;
    }

    public String getFailureReason() {
        return failureReason;
    }

    public void setFailureReason(String failureReason) {
        this.failureReason = failureReason;
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
}
