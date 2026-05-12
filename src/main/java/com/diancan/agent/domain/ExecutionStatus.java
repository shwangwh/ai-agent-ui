package com.diancan.agent.domain;

public enum ExecutionStatus {
    passed,
    failed,
    blocked,
    locator_healed,
    locator_unresolved,
    assertion_failed,
    execution_error,
    environment_error,
    test_data_error,
    skipped
}
