package com.diancan.agent.model;

import com.diancan.agent.domain.ExecutionStatus;

public record StepExecutionResult(
        String stepRunId,
        int index,
        String action,
        String target,
        String value,
        ExecutionStatus status,
        long durationMs,
        String message
) {
}
