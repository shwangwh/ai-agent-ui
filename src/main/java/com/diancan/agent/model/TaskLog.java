package com.diancan.agent.model;

import com.diancan.agent.domain.LogLevel;

import java.time.OffsetDateTime;
import java.util.Map;

public record TaskLog(
        String logId,
        LogLevel level,
        String traceId,
        String taskId,
        String caseRunId,
        String stepRunId,
        String event,
        String message,
        Map<String, Object> attributes,
        OffsetDateTime timestamp
) {
}
