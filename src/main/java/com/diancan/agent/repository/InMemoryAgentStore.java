package com.diancan.agent.repository;

import com.diancan.agent.model.ExecutionCaseResult;
import com.diancan.agent.model.ExecutionTask;
import com.diancan.agent.model.ParseTask;
import com.diancan.agent.model.ParsedTestCase;
import com.diancan.agent.model.TaskLog;
import com.diancan.agent.model.TestDocument;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

@Repository
public class InMemoryAgentStore {
    private final ConcurrentMap<String, TestDocument> documents = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, ParseTask> parseTasks = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, List<ParsedTestCase>> parsedCasesByTask = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, ExecutionTask> executionTasks = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, List<ExecutionCaseResult>> executionCasesByTask = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, List<TaskLog>> logsByTask = new ConcurrentHashMap<>();

    public TestDocument saveDocument(TestDocument document) {
        documents.put(document.getDocumentId(), document);
        return document;
    }

    public Optional<TestDocument> findDocument(String documentId) {
        return Optional.ofNullable(documents.get(documentId));
    }

    public ParseTask saveParseTask(ParseTask parseTask) {
        parseTasks.put(parseTask.getParseTaskId(), parseTask);
        return parseTask;
    }

    public Optional<ParseTask> findParseTask(String parseTaskId) {
        return Optional.ofNullable(parseTasks.get(parseTaskId));
    }

    public void saveParsedCases(String parseTaskId, List<ParsedTestCase> cases) {
        parsedCasesByTask.put(parseTaskId, new ArrayList<>(cases));
    }

    public List<ParsedTestCase> findParsedCases(String parseTaskId) {
        return parsedCasesByTask.getOrDefault(parseTaskId, List.of());
    }

    public ExecutionTask saveExecutionTask(ExecutionTask task) {
        executionTasks.put(task.getTaskId(), task);
        return task;
    }

    public Optional<ExecutionTask> findExecutionTask(String taskId) {
        return Optional.ofNullable(executionTasks.get(taskId));
    }

    public void saveExecutionCases(String taskId, List<ExecutionCaseResult> cases) {
        executionCasesByTask.put(taskId, new ArrayList<>(cases));
    }

    public List<ExecutionCaseResult> findExecutionCases(String taskId) {
        return executionCasesByTask.getOrDefault(taskId, List.of());
    }

    public void addLog(TaskLog log) {
        logsByTask.computeIfAbsent(log.taskId(), ignored -> new ArrayList<>()).add(log);
    }

    public List<TaskLog> findLogs(String taskId) {
        return logsByTask.getOrDefault(taskId, List.of()).stream()
                .sorted(Comparator.comparing(TaskLog::timestamp))
                .toList();
    }
}
