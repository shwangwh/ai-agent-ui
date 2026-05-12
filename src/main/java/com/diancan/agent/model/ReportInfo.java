package com.diancan.agent.model;

public record ReportInfo(
        String taskId,
        String type,
        String status,
        String allureReportUrl,
        String jsonResultUrl,
        String resultsDir,
        String reportDir
) {
}
