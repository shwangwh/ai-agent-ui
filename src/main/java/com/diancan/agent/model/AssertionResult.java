package com.diancan.agent.model;

import com.diancan.agent.domain.ExecutionStatus;

public record AssertionResult(
        String assertionType,
        String expected,
        String actual,
        ExecutionStatus status
) {
}
