package com.diancan.agent.model;

import com.diancan.agent.domain.ParseStatus;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;

public class ParsedTestCase {
    private String caseId;
    private String documentId;
    private String parseTaskId;
    private String caseName;
    private String module;
    private String priority;
    private String rawMarkdown;
    private List<String> preconditions = new ArrayList<>();
    private List<String> steps = new ArrayList<>();
    private List<String> expectedResults = new ArrayList<>();
    private List<String> testData = new ArrayList<>();
    private List<String> tags = new ArrayList<>();
    private String remarks;
    private double parseConfidence;
    private ParseStatus status;
    private List<String> uncertainItems = new ArrayList<>();
    private OffsetDateTime updatedAt;

    public String getCaseId() {
        return caseId;
    }

    public void setCaseId(String caseId) {
        this.caseId = caseId;
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

    public String getRawMarkdown() {
        return rawMarkdown;
    }

    public void setRawMarkdown(String rawMarkdown) {
        this.rawMarkdown = rawMarkdown;
    }

    public List<String> getPreconditions() {
        return preconditions;
    }

    public void setPreconditions(List<String> preconditions) {
        this.preconditions = preconditions == null ? new ArrayList<>() : preconditions;
    }

    public List<String> getSteps() {
        return steps;
    }

    public void setSteps(List<String> steps) {
        this.steps = steps == null ? new ArrayList<>() : steps;
    }

    public List<String> getExpectedResults() {
        return expectedResults;
    }

    public void setExpectedResults(List<String> expectedResults) {
        this.expectedResults = expectedResults == null ? new ArrayList<>() : expectedResults;
    }

    public List<String> getTestData() {
        return testData;
    }

    public void setTestData(List<String> testData) {
        this.testData = testData == null ? new ArrayList<>() : testData;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(List<String> tags) {
        this.tags = tags == null ? new ArrayList<>() : tags;
    }

    public String getRemarks() {
        return remarks;
    }

    public void setRemarks(String remarks) {
        this.remarks = remarks;
    }

    public double getParseConfidence() {
        return parseConfidence;
    }

    public void setParseConfidence(double parseConfidence) {
        this.parseConfidence = parseConfidence;
    }

    public ParseStatus getStatus() {
        return status;
    }

    public void setStatus(ParseStatus status) {
        this.status = status;
    }

    public List<String> getUncertainItems() {
        return uncertainItems;
    }

    public void setUncertainItems(List<String> uncertainItems) {
        this.uncertainItems = uncertainItems == null ? new ArrayList<>() : uncertainItems;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(OffsetDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
