package com.diancan.agent.dto;

import java.time.OffsetDateTime;

public record ApiError(String code, String message, OffsetDateTime timestamp) {
}
