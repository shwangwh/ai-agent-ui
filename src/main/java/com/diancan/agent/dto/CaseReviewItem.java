package com.diancan.agent.dto;

import com.diancan.agent.domain.ReviewAction;

import java.util.List;

public record CaseReviewItem(
        String caseId,
        ReviewAction action,
        String caseName,
        String module,
        String priority,
        List<String> preconditions,
        List<String> steps,
        List<String> expectedResults,
        List<String> testData,
        List<String> tags,
        String remarks
) {
}
