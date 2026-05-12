package com.diancan.agent.service;

import com.diancan.agent.domain.LogLevel;
import com.diancan.agent.model.TaskLog;
import com.diancan.agent.repository.InMemoryAgentStore;
import com.diancan.agent.support.IdGenerator;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

@Service
public class TaskLogService {
    private final InMemoryAgentStore store;

    public TaskLogService(InMemoryAgentStore store) {
        this.store = store;
    }

    public void log(LogLevel level, String traceId, String taskId, String caseRunId, String stepRunId,
                    String event, String message, Map<String, Object> attributes) {
        store.addLog(new TaskLog(
                IdGenerator.next("log"),
                level,
                traceId,
                taskId,
                caseRunId,
                stepRunId,
                event,
                message,
                attributes == null ? Map.of() : attributes,
                OffsetDateTime.now()
        ));
    }

    public List<TaskLog> findLogs(String taskId, String caseRunId, String stepRunId, LogLevel level, String event) {
        return store.findLogs(taskId).stream()
                .filter(log -> caseRunId == null || caseRunId.equals(log.caseRunId()))
                .filter(log -> stepRunId == null || stepRunId.equals(log.stepRunId()))
                .filter(log -> level == null || level == log.level())
                .filter(log -> event == null || event.equalsIgnoreCase(log.event()))
                .toList();
    }
}
