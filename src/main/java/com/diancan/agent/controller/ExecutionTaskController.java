package com.diancan.agent.controller;

import com.diancan.agent.domain.LogLevel;
import com.diancan.agent.dto.CreateExecutionTaskRequest;
import com.diancan.agent.dto.CreateTaskResponse;
import com.diancan.agent.model.ExecutionCaseResult;
import com.diancan.agent.model.ExecutionTask;
import com.diancan.agent.model.ReportInfo;
import com.diancan.agent.model.TaskLog;
import com.diancan.agent.service.ExecutionTaskService;
import com.diancan.agent.service.TaskLogService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/execution-tasks")
public class ExecutionTaskController {
    private final ExecutionTaskService executionTasks;
    private final TaskLogService logs;

    public ExecutionTaskController(ExecutionTaskService executionTasks, TaskLogService logs) {
        this.executionTasks = executionTasks;
        this.logs = logs;
    }

    @PostMapping
    public CreateTaskResponse create(@Valid @RequestBody CreateExecutionTaskRequest request) {
        ExecutionTask task = executionTasks.create(request);
        return new CreateTaskResponse(task.getTaskId(), task.getStatus().name(), task.getMessage());
    }

    @GetMapping("/{taskId}")
    public ExecutionTask get(@PathVariable String taskId) {
        return executionTasks.get(taskId);
    }

    @GetMapping("/{taskId}/cases")
    public List<ExecutionCaseResult> cases(@PathVariable String taskId) {
        return executionTasks.getCases(taskId);
    }

    @GetMapping("/{taskId}/logs")
    public List<TaskLog> logs(@PathVariable String taskId,
                              @RequestParam(required = false) String caseRunId,
                              @RequestParam(required = false) String stepRunId,
                              @RequestParam(required = false) LogLevel level,
                              @RequestParam(required = false) String event) {
        executionTasks.get(taskId);
        return logs.findLogs(taskId, caseRunId, stepRunId, level, event);
    }

    @GetMapping("/{taskId}/report")
    public ReportInfo report(@PathVariable String taskId) {
        return executionTasks.getReport(taskId);
    }

    @GetMapping("/{taskId}/artifacts")
    public Map<String, Object> artifacts(@PathVariable String taskId) {
        executionTasks.get(taskId);
        return Map.of(
                "taskId", taskId,
                "artifacts", List.of(
                        "screenshots 占位目录: data/artifacts/" + taskId + "/screenshots",
                        "trace 占位目录: data/artifacts/" + taskId + "/trace",
                        "network 占位目录: data/artifacts/" + taskId + "/network"
                )
        );
    }
}
