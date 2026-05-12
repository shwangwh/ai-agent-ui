package com.diancan.agent.dto;

import com.diancan.agent.domain.BrowserType;
import com.diancan.agent.domain.RunMode;
import jakarta.validation.constraints.NotBlank;

import java.util.List;

public record CreateExecutionTaskRequest(
        @NotBlank String documentId,
        @NotBlank String parseTaskId,
        String environmentCode,
        RunMode runMode,
        BrowserType browser,
        boolean headless,
        CaseFilter caseFilter,
        ReportOptions report
) {
    public record CaseFilter(List<String> priorities, List<String> tags) {
    }

    public record ReportOptions(String type, boolean generateAfterDocumentFinished) {
    }
}
