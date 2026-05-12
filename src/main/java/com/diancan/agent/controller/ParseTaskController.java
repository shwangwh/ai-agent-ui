package com.diancan.agent.controller;

import com.diancan.agent.dto.ConfirmParseTaskRequest;
import com.diancan.agent.model.ParseTask;
import com.diancan.agent.model.ParsedTestCase;
import com.diancan.agent.service.ParseTaskService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/parse-tasks")
public class ParseTaskController {
    private final ParseTaskService parseTasks;

    public ParseTaskController(ParseTaskService parseTasks) {
        this.parseTasks = parseTasks;
    }

    @GetMapping("/{parseTaskId}")
    public ParseTask get(@PathVariable String parseTaskId) {
        return parseTasks.getParseTask(parseTaskId);
    }

    @GetMapping("/{parseTaskId}/cases")
    public List<ParsedTestCase> cases(@PathVariable String parseTaskId) {
        return parseTasks.getCases(parseTaskId);
    }

    @PostMapping("/{parseTaskId}/confirm")
    public List<ParsedTestCase> confirm(@PathVariable String parseTaskId, @RequestBody ConfirmParseTaskRequest request) {
        return parseTasks.confirm(parseTaskId, request);
    }
}
