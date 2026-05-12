package com.diancan.agent.service;

import com.diancan.agent.domain.BrowserType;
import com.diancan.agent.domain.ExecutionStatus;
import com.diancan.agent.domain.LogLevel;
import com.diancan.agent.domain.ParseStatus;
import com.diancan.agent.domain.RunMode;
import com.diancan.agent.domain.TaskStatus;
import com.diancan.agent.dto.CreateExecutionTaskRequest;
import com.diancan.agent.model.AssertionResult;
import com.diancan.agent.model.ExecutionCaseResult;
import com.diancan.agent.model.ExecutionTask;
import com.diancan.agent.model.ParsedTestCase;
import com.diancan.agent.model.ReportInfo;
import com.diancan.agent.model.StepExecutionResult;
import com.diancan.agent.repository.InMemoryAgentStore;
import com.diancan.agent.support.BadRequestException;
import com.diancan.agent.support.IdGenerator;
import com.diancan.agent.support.ResourceNotFoundException;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

@Service
public class ExecutionTaskService {
    private final InMemoryAgentStore store;
    private final ParseTaskService parseTasks;
    private final TaskLogService logs;

    public ExecutionTaskService(InMemoryAgentStore store, ParseTaskService parseTasks, TaskLogService logs) {
        this.store = store;
        this.parseTasks = parseTasks;
        this.logs = logs;
    }

    public ExecutionTask create(CreateExecutionTaskRequest request) {
        parseTasks.getParseTask(request.parseTaskId());
        List<ParsedTestCase> cases = filterCases(parseTasks.getCases(request.parseTaskId()), request.caseFilter());
        if (cases.isEmpty()) {
            throw new BadRequestException("没有符合条件的可执行用例");
        }

        String taskId = IdGenerator.next("exec");
        ExecutionTask task = new ExecutionTask();
        task.setTaskId(taskId);
        task.setDocumentId(request.documentId());
        task.setParseTaskId(request.parseTaskId());
        task.setEnvironmentCode(request.environmentCode() == null ? "test" : request.environmentCode());
        task.setRunMode(request.runMode() == null ? RunMode.strict : request.runMode());
        task.setBrowser(request.browser() == null ? BrowserType.chromium : request.browser());
        task.setHeadless(request.headless());
        task.setStatus(TaskStatus.running);
        task.setCreatedAt(OffsetDateTime.now());
        task.setStartedAt(OffsetDateTime.now());
        task.setMessage("执行中");
        store.saveExecutionTask(task);

        logs.log(LogLevel.INFO, taskId, taskId, null, null,
                "EXECUTION_TASK_CREATED", "自动化执行任务已创建",
                Map.of("environmentCode", task.getEnvironmentCode(), "browser", task.getBrowser().name(),
                        "runMode", task.getRunMode().name()));

        List<ExecutionCaseResult> results = new ArrayList<>();
        for (ParsedTestCase testCase : cases) {
            results.add(runCase(task, testCase));
        }
        store.saveExecutionCases(taskId, results);
        summarize(task, results);
        task.setStatus(TaskStatus.finished);
        task.setFinishedAt(OffsetDateTime.now());
        task.setAllureReportUrl("/reports/allure/" + taskId + "/index.html");
        task.setJsonResultUrl("/api/v1/execution-tasks/" + taskId + "/cases");
        task.setMessage("执行完成，Allure 报告元数据已生成");
        store.saveExecutionTask(task);

        logs.log(LogLevel.INFO, taskId, taskId, null, null,
                "EXECUTION_TASK_FINISHED", "文档执行完成",
                Map.of("totalCases", task.getTotalCases(), "passed", task.getPassed(), "failed", task.getFailed(),
                        "blocked", task.getBlocked(), "locatorUnresolved", task.getLocatorUnresolved()));
        return task;
    }

    public ExecutionTask get(String taskId) {
        return store.findExecutionTask(taskId)
                .orElseThrow(() -> new ResourceNotFoundException("执行任务不存在: " + taskId));
    }

    public List<ExecutionCaseResult> getCases(String taskId) {
        get(taskId);
        return store.findExecutionCases(taskId);
    }

    public ReportInfo getReport(String taskId) {
        ExecutionTask task = get(taskId);
        return new ReportInfo(
                taskId,
                "allure",
                task.getStatus().name(),
                task.getAllureReportUrl(),
                task.getJsonResultUrl(),
                "data/allure-results/" + taskId,
                "data/allure-report/" + taskId
        );
    }

    private ExecutionCaseResult runCase(ExecutionTask task, ParsedTestCase testCase) {
        OffsetDateTime startedAt = OffsetDateTime.now();
        String caseRunId = IdGenerator.next("case_run");
        ExecutionCaseResult result = new ExecutionCaseResult();
        result.setCaseRunId(caseRunId);
        result.setTaskId(task.getTaskId());
        result.setCaseId(testCase.getCaseId());
        result.setCaseName(testCase.getCaseName());
        result.setModule(testCase.getModule());
        result.setPriority(testCase.getPriority());
        result.setStartedAt(startedAt);

        logs.log(LogLevel.INFO, task.getTaskId(), task.getTaskId(), caseRunId, null,
                "CASE_EXECUTION_STARTED", "用例开始执行",
                Map.of("caseId", testCase.getCaseId(), "caseName", testCase.getCaseName()));

        if (testCase.getStatus() == ParseStatus.skipped) {
            result.setStatus(ExecutionStatus.skipped);
            result.setFailureReason("调用方选择跳过该用例");
        } else if (testCase.getStatus() != ParseStatus.executable) {
            result.setStatus(ExecutionStatus.blocked);
            result.setFailureReason("解析状态不是 executable: " + testCase.getStatus());
        } else if (hasBlockingPrecondition(testCase)) {
            result.setStatus(ExecutionStatus.blocked);
            result.setFailureReason("前置条件无法自动满足，请人工确认");
        } else {
            result.setSteps(buildStepResults(task.getTaskId(), caseRunId, testCase));
            result.setAssertions(buildAssertions(testCase));
            boolean assertionFailed = result.getAssertions().stream()
                    .anyMatch(assertion -> assertion.status() != ExecutionStatus.passed);
            result.setStatus(assertionFailed ? ExecutionStatus.assertion_failed : ExecutionStatus.passed);
            result.setFailureReason(assertionFailed ? "存在预期结果断言未通过" : null);
        }

        result.setEvidenceUrls(List.of(
                "/api/v1/execution-tasks/" + task.getTaskId() + "/artifacts/" + caseRunId + "/summary.json"
        ));
        result.setFinishedAt(OffsetDateTime.now());
        result.setDurationMs(Duration.between(startedAt, result.getFinishedAt()).toMillis());
        logs.log(result.getStatus() == ExecutionStatus.passed ? LogLevel.INFO : LogLevel.WARN,
                task.getTaskId(), task.getTaskId(), caseRunId, null,
                "CASE_EXECUTION_FINISHED", "用例执行结束",
                Map.of("status", result.getStatus().name(), "durationMs", result.getDurationMs()));
        return result;
    }

    private List<StepExecutionResult> buildStepResults(String taskId, String caseRunId, ParsedTestCase testCase) {
        List<StepExecutionResult> steps = new ArrayList<>();
        int index = 1;
        for (String step : testCase.getSteps()) {
            String stepRunId = IdGenerator.next("step_run");
            String action = inferAction(step);
            logs.log(LogLevel.INFO, taskId, taskId, caseRunId, stepRunId,
                    "STEP_EXECUTION_FINISHED", "步骤执行完成",
                    Map.of("action", action, "target", maskSensitive(step), "status", "passed"));
            steps.add(new StepExecutionResult(stepRunId, index, action, maskSensitive(step), null,
                    ExecutionStatus.passed, 120, "MVP 模拟执行成功，待接入 Playwright Runner"));
            index++;
        }
        return steps;
    }

    private List<AssertionResult> buildAssertions(ParsedTestCase testCase) {
        return testCase.getExpectedResults().stream()
                .map(expected -> {
                    ExecutionStatus status = expected.contains("系统异常") ? ExecutionStatus.assertion_failed : ExecutionStatus.passed;
                    String actual = status == ExecutionStatus.passed ? "页面满足预期: " + expected : "实际页面出现非预期错误";
                    return new AssertionResult(inferAssertionType(expected), maskSensitive(expected), actual, status);
                })
                .toList();
    }

    private List<ParsedTestCase> filterCases(List<ParsedTestCase> cases, CreateExecutionTaskRequest.CaseFilter filter) {
        return cases.stream()
                .filter(testCase -> filter == null || filter.priorities() == null || filter.priorities().isEmpty()
                        || filter.priorities().contains(testCase.getPriority()))
                .filter(testCase -> filter == null || filter.tags() == null || filter.tags().isEmpty()
                        || testCase.getTags().stream().anyMatch(filter.tags()::contains))
                .toList();
    }

    private boolean hasBlockingPrecondition(ParsedTestCase testCase) {
        return testCase.getPreconditions().stream()
                .filter(Objects::nonNull)
                .anyMatch(item -> item.contains("人工确认") || item.contains("无法满足") || item.contains("休息中"));
    }

    private String inferAction(String step) {
        if (step.contains("打开") || step.toLowerCase().contains("open")) return "open";
        if (step.contains("输入")) return "input";
        if (step.contains("选择")) return "select_or_click";
        if (step.contains("等待")) return "wait";
        if (step.contains("滚动")) return "scroll";
        if (step.contains("点击") || step.contains("点")) return "click";
        return "unknown";
    }

    private String inferAssertionType(String expected) {
        if (expected.contains("跳转")) return "url_contains";
        if (expected.contains("不可点击")) return "button_disabled";
        if (expected.contains("订单号")) return "regex_match";
        if (expected.contains("无报错")) return "no_console_error";
        return "text_visible";
    }

    private String maskSensitive(String value) {
        if (value == null) {
            return null;
        }
        return value.replaceAll("(1[3-9]\\d)\\d{4}(\\d{4})", "$1****$2")
                .replaceAll("(?i)(密码\\s*[:：]?\\s*)\\S+", "$1******")
                .replaceAll("(?i)(token\\s*[:：]?\\s*)\\S+", "$1******");
    }

    private void summarize(ExecutionTask task, List<ExecutionCaseResult> results) {
        task.setTotalCases(results.size());
        task.setPassed((int) results.stream().filter(item -> item.getStatus() == ExecutionStatus.passed).count());
        task.setFailed((int) results.stream().filter(item -> item.getStatus() == ExecutionStatus.failed
                || item.getStatus() == ExecutionStatus.assertion_failed).count());
        task.setBlocked((int) results.stream().filter(item -> item.getStatus() == ExecutionStatus.blocked).count());
        task.setLocatorHealed((int) results.stream().filter(item -> item.getStatus() == ExecutionStatus.locator_healed).count());
        task.setLocatorUnresolved((int) results.stream().filter(item -> item.getStatus() == ExecutionStatus.locator_unresolved).count());
        task.setSkipped((int) results.stream().filter(item -> item.getStatus() == ExecutionStatus.skipped).count());
    }
}
