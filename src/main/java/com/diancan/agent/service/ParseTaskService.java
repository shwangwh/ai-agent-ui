package com.diancan.agent.service;

import com.diancan.agent.domain.LogLevel;
import com.diancan.agent.domain.ParseStatus;
import com.diancan.agent.domain.TaskStatus;
import com.diancan.agent.dto.CaseReviewItem;
import com.diancan.agent.dto.ConfirmParseTaskRequest;
import com.diancan.agent.model.ParseTask;
import com.diancan.agent.model.ParsedTestCase;
import com.diancan.agent.model.TestDocument;
import com.diancan.agent.repository.InMemoryAgentStore;
import com.diancan.agent.support.BadRequestException;
import com.diancan.agent.support.IdGenerator;
import com.diancan.agent.support.ResourceNotFoundException;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class ParseTaskService {
    private final InMemoryAgentStore store;
    private final DocumentService documents;
    private final MarkdownCaseParser parser;
    private final TaskLogService logs;

    public ParseTaskService(InMemoryAgentStore store, DocumentService documents, MarkdownCaseParser parser, TaskLogService logs) {
        this.store = store;
        this.documents = documents;
        this.parser = parser;
        this.logs = logs;
    }

    public ParseTask createParseTask(String documentId, String parseMode) {
        TestDocument document = documents.get(documentId);
        String parseTaskId = IdGenerator.next("parse");
        ParseTask task = new ParseTask();
        task.setParseTaskId(parseTaskId);
        task.setDocumentId(documentId);
        task.setStatus(TaskStatus.parsing);
        task.setCreatedAt(OffsetDateTime.now());
        task.setMessage("解析中");
        store.saveParseTask(task);

        logs.log(LogLevel.INFO, parseTaskId, parseTaskId, null, null,
                "PARSE_TASK_CREATED", "创建解析任务",
                Map.of("documentId", documentId, "parseMode", parseMode == null ? "smart" : parseMode));

        List<ParsedTestCase> cases = parser.parse(documentId, parseTaskId, document.getContent());
        store.saveParsedCases(parseTaskId, cases);
        summarize(task, cases);
        task.setStatus(TaskStatus.finished);
        task.setFinishedAt(OffsetDateTime.now());
        task.setMessage("解析完成");
        store.saveParseTask(task);

        logs.log(LogLevel.INFO, parseTaskId, parseTaskId, null, null,
                "PARSE_TASK_FINISHED", "解析任务完成",
                Map.of("totalCases", task.getTotalCases(), "executableCases", task.getExecutableCases(),
                        "reviewCases", task.getReviewCases(), "invalidCases", task.getInvalidCases()));
        return task;
    }

    public ParseTask getParseTask(String parseTaskId) {
        return store.findParseTask(parseTaskId)
                .orElseThrow(() -> new ResourceNotFoundException("解析任务不存在: " + parseTaskId));
    }

    public List<ParsedTestCase> getCases(String parseTaskId) {
        getParseTask(parseTaskId);
        return store.findParsedCases(parseTaskId);
    }

    public List<ParsedTestCase> confirm(String parseTaskId, ConfirmParseTaskRequest request) {
        ParseTask task = getParseTask(parseTaskId);
        if (request == null || request.cases() == null || request.cases().isEmpty()) {
            throw new BadRequestException("确认列表不能为空");
        }
        Map<String, ParsedTestCase> cases = new ArrayList<>(store.findParsedCases(parseTaskId)).stream()
                .collect(Collectors.toMap(ParsedTestCase::getCaseId, Function.identity(), (a, b) -> a));

        for (CaseReviewItem item : request.cases()) {
            ParsedTestCase testCase = cases.get(item.caseId());
            if (testCase == null) {
                throw new ResourceNotFoundException("用例不存在: " + item.caseId());
            }
            switch (item.action()) {
                case confirm -> testCase.setStatus(ParseStatus.executable);
                case revise, save -> {
                    applyRevision(testCase, item);
                    testCase.setStatus(ParseStatus.executable);
                    testCase.setParseConfidence(Math.max(testCase.getParseConfidence(), 0.90));
                }
                case skip -> testCase.setStatus(ParseStatus.skipped);
                case mark_invalid -> testCase.setStatus(ParseStatus.invalid);
            }
            testCase.setUpdatedAt(OffsetDateTime.now());
            logs.log(LogLevel.INFO, parseTaskId, parseTaskId, null, null,
                    "CASE_REVIEWED", "用例解析结果已确认",
                    Map.of("caseId", testCase.getCaseId(), "action", item.action().name(), "status", testCase.getStatus().name()));
        }
        List<ParsedTestCase> updated = new ArrayList<>(cases.values());
        store.saveParsedCases(parseTaskId, updated);
        summarize(task, updated);
        store.saveParseTask(task);
        return updated;
    }

    private void applyRevision(ParsedTestCase testCase, CaseReviewItem item) {
        if (item.caseName() != null) testCase.setCaseName(item.caseName());
        if (item.module() != null) testCase.setModule(item.module());
        if (item.priority() != null) testCase.setPriority(item.priority());
        if (item.preconditions() != null) testCase.setPreconditions(item.preconditions());
        if (item.steps() != null) testCase.setSteps(item.steps());
        if (item.expectedResults() != null) testCase.setExpectedResults(item.expectedResults());
        if (item.testData() != null) testCase.setTestData(item.testData());
        if (item.tags() != null) testCase.setTags(item.tags());
        if (item.remarks() != null) testCase.setRemarks(item.remarks());
        testCase.setUncertainItems(List.of());
    }

    private void summarize(ParseTask task, List<ParsedTestCase> cases) {
        task.setTotalCases(cases.size());
        task.setExecutableCases((int) cases.stream().filter(c -> c.getStatus() == ParseStatus.executable).count());
        task.setReviewCases((int) cases.stream().filter(c -> c.getStatus() == ParseStatus.need_review).count());
        task.setInvalidCases((int) cases.stream().filter(c -> c.getStatus() == ParseStatus.invalid).count());
    }
}
