package com.diancan.agent.service;

import com.diancan.agent.domain.ParseStatus;
import com.diancan.agent.model.ParsedTestCase;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class MarkdownCaseParser {
    private static final Pattern CASE_HEADING = Pattern.compile("(?m)^#{1,2}\\s*(?:用例[:：]?|case[:：]?|场景[:：]?|测试点[:：]?)?\\s*(.+)$", Pattern.CASE_INSENSITIVE);
    private static final Pattern BRACKET_FIELD = Pattern.compile("【([^】]+)】([^【]+)");
    private static final Pattern INLINE_FIELD = Pattern.compile("^(用例编号|编号|case_id|优先级|priority|模块|module|标签|tags|备注|remarks)\\s*[:：]\\s*(.+)$", Pattern.CASE_INSENSITIVE);

    private final double executableThreshold;
    private final double reviewThreshold;

    public MarkdownCaseParser(
            @Value("${agent.parser.executable-threshold:0.85}") double executableThreshold,
            @Value("${agent.parser.review-threshold:0.60}") double reviewThreshold) {
        this.executableThreshold = executableThreshold;
        this.reviewThreshold = reviewThreshold;
    }

    public List<ParsedTestCase> parse(String documentId, String parseTaskId, String markdown) {
        List<String> blocks = splitCaseBlocks(markdown);
        List<ParsedTestCase> cases = new ArrayList<>();
        int index = 1;
        for (String block : blocks) {
            ParsedTestCase testCase = parseBlock(documentId, parseTaskId, block, index);
            cases.add(testCase);
            index++;
        }
        return cases;
    }

    private ParsedTestCase parseBlock(String documentId, String parseTaskId, String block, int index) {
        ParsedTestCase testCase = new ParsedTestCase();
        testCase.setDocumentId(documentId);
        testCase.setParseTaskId(parseTaskId);
        testCase.setRawMarkdown(block.trim());
        testCase.setCaseId("CASE_" + String.format(Locale.ROOT, "%03d", index));
        testCase.setUpdatedAt(OffsetDateTime.now());

        if (block.contains("【")) {
            parseBracketFields(block, testCase);
        }
        parseLineFieldsAndSections(block, testCase);
        if (isBlank(testCase.getCaseName())) {
            testCase.setCaseName(extractCaseName(block, index));
        }
        if (isBlank(testCase.getCaseId()) || testCase.getCaseId().startsWith("CASE_")) {
            testCase.setCaseId(extractInlineValue(block, "用例编号", "编号", "case_id").orElse(testCase.getCaseId()));
        }

        clean(testCase.getPreconditions());
        clean(testCase.getSteps());
        clean(testCase.getExpectedResults());
        score(testCase);
        return testCase;
    }

    private List<String> splitCaseBlocks(String markdown) {
        String normalized = markdown == null ? "" : markdown.replace("\r\n", "\n");
        if (normalized.isBlank()) {
            return List.of();
        }

        List<String> blocks = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        boolean foundCaseHeading = false;
        for (String line : normalized.split("\n", -1)) {
            String trimmed = line.trim();
            boolean caseHeadingLine = trimmed.startsWith("## ")
                    || trimmed.matches("^#\\s*(用例|case|场景|测试点)[:：].*");
            String heading = caseHeadingLine ? trimmed.replaceFirst("^#{1,2}\\s*", "").trim() : "";
            if (caseHeadingLine && looksLikeCaseHeading(heading)) {
                foundCaseHeading = true;
                if (!current.isEmpty()) {
                    blocks.add(current.toString());
                    current.setLength(0);
                }
            }
            current.append(line).append('\n');
        }
        if (!current.isEmpty()) {
            blocks.add(current.toString());
        }
        if (!foundCaseHeading) {
            return List.of(normalized);
        }
        return blocks.stream().filter(block -> !block.isBlank()).toList();
    }

    private boolean looksLikeCaseHeading(String heading) {
        String lower = heading.toLowerCase(Locale.ROOT);
        return lower.contains("用例")
                || lower.contains("case")
                || lower.contains("登录")
                || lower.contains("订单")
                || lower.contains("提交")
                || lower.contains("失败")
                || lower.contains("成功")
                || lower.length() <= 40;
    }

    private void parseBracketFields(String block, ParsedTestCase testCase) {
        Matcher matcher = BRACKET_FIELD.matcher(block.replace("\n", " "));
        while (matcher.find()) {
            String key = matcher.group(1).trim().toLowerCase(Locale.ROOT);
            String value = matcher.group(2).trim();
            if (matches(key, "用例名称", "用例", "case", "标题")) {
                testCase.setCaseName(value);
            } else if (matches(key, "前置", "前提", "given")) {
                testCase.setPreconditions(splitItems(value));
            } else if (matches(key, "操作", "步骤", "when")) {
                testCase.setSteps(splitItems(value));
            } else if (matches(key, "预期", "期望", "then", "结果")) {
                testCase.setExpectedResults(splitItems(value));
            }
        }
    }

    private void parseLineFieldsAndSections(String block, ParsedTestCase testCase) {
        Map<String, List<String>> sections = new LinkedHashMap<>();
        String current = "";
        for (String rawLine : block.replace("\r\n", "\n").split("\n")) {
            String line = rawLine.trim();
            if (line.isBlank() || line.matches("^[-]{3,}$")) {
                continue;
            }
            Matcher inline = INLINE_FIELD.matcher(stripMarkdownMarker(line));
            if (inline.find()) {
                applyMetadata(inline.group(1), inline.group(2), testCase);
                continue;
            }
            FieldHeader header = parseHeader(line);
            if (header != null) {
                if ("case".equals(header.field())) {
                    testCase.setCaseName(header.inlineValue());
                    current = "";
                    continue;
                }
                current = header.field();
                if (!header.inlineValue().isBlank()) {
                    sections.computeIfAbsent(current, ignored -> new ArrayList<>()).addAll(splitItems(header.inlineValue()));
                }
                continue;
            }
            if (!current.isBlank()) {
                sections.computeIfAbsent(current, ignored -> new ArrayList<>()).addAll(splitItems(line));
            }
        }
        mergeIfPresent(testCase.getPreconditions(), sections.get("preconditions"));
        mergeIfPresent(testCase.getSteps(), sections.get("steps"));
        mergeIfPresent(testCase.getExpectedResults(), sections.get("expected"));
    }

    private FieldHeader parseHeader(String line) {
        String stripped = stripMarkdownMarker(line);
        String lower = stripped.toLowerCase(Locale.ROOT);
        String[] parts = stripped.split("[:：]", 2);
        String key = parts[0].replace("#", "").trim().toLowerCase(Locale.ROOT);
        String value = parts.length > 1 ? parts[1].trim() : "";

        if (matches(key, "前置条件", "前置", "前提", "given", "准备条件", "初始化条件")) {
            return new FieldHeader("preconditions", value);
        }
        if (matches(key, "测试步骤", "步骤", "操作", "when", "操作步骤", "测试过程")) {
            return new FieldHeader("steps", value);
        }
        if (matches(key, "预期结果", "预期", "期望", "then", "校验点", "断言", "结果")) {
            return new FieldHeader("expected", value);
        }
        if (lower.startsWith("case:") || lower.startsWith("case：")) {
            return new FieldHeader("case", value);
        }
        return null;
    }

    private void applyMetadata(String key, String value, ParsedTestCase testCase) {
        String normalized = key.toLowerCase(Locale.ROOT);
        if (matches(normalized, "用例编号", "编号", "case_id")) {
            testCase.setCaseId(value.trim());
        } else if (matches(normalized, "优先级", "priority")) {
            testCase.setPriority(value.trim());
        } else if (matches(normalized, "模块", "module")) {
            testCase.setModule(value.trim());
        } else if (matches(normalized, "标签", "tags")) {
            testCase.setTags(splitItems(value));
        } else if (matches(normalized, "备注", "remarks")) {
            testCase.setRemarks(value.trim());
        }
    }

    private java.util.Optional<String> extractInlineValue(String block, String... keys) {
        for (String line : block.split("\\R")) {
            String stripped = stripMarkdownMarker(line.trim());
            for (String key : keys) {
                if (stripped.toLowerCase(Locale.ROOT).startsWith(key.toLowerCase(Locale.ROOT))) {
                    String[] parts = stripped.split("[:：]", 2);
                    if (parts.length == 2 && !parts[1].isBlank()) {
                        return java.util.Optional.of(parts[1].trim());
                    }
                }
            }
        }
        return java.util.Optional.empty();
    }

    private String extractCaseName(String block, int index) {
        Matcher matcher = CASE_HEADING.matcher(block);
        if (matcher.find()) {
            String name = matcher.group(1).replaceFirst("^用例[:：]?", "").trim();
            if (!name.isBlank()) {
                return name;
            }
        }
        return "未命名用例 " + index;
    }

    private void score(ParsedTestCase testCase) {
        double score = 0.20;
        if (!isBlank(testCase.getCaseName()) && !testCase.getCaseName().startsWith("未命名")) {
            score += 0.25;
        } else {
            testCase.getUncertainItems().add("缺少清晰的用例名称");
        }
        if (!testCase.getSteps().isEmpty()) {
            score += Math.min(0.30, 0.10 + testCase.getSteps().size() * 0.05);
        } else {
            testCase.getUncertainItems().add("缺少测试步骤");
        }
        if (!testCase.getExpectedResults().isEmpty()) {
            score += Math.min(0.25, 0.10 + testCase.getExpectedResults().size() * 0.05);
        } else {
            testCase.getUncertainItems().add("缺少预期结果");
        }
        if (!testCase.getPreconditions().isEmpty()) {
            score += 0.05;
        }
        double confidence = Math.min(0.99, Math.round(score * 100.0) / 100.0);
        testCase.setParseConfidence(confidence);
        if (testCase.getSteps().isEmpty() || testCase.getExpectedResults().isEmpty() || confidence < reviewThreshold) {
            testCase.setStatus(ParseStatus.invalid);
        } else if (confidence >= executableThreshold) {
            testCase.setStatus(ParseStatus.executable);
        } else {
            testCase.setStatus(ParseStatus.need_review);
        }
    }

    private List<String> splitItems(String value) {
        if (value == null || value.isBlank()) {
            return new ArrayList<>();
        }
        String normalized = value.replace("->", "\n")
                .replace("；", "\n")
                .replace(";", "\n")
                .replace("，", "\n");
        List<String> items = new ArrayList<>();
        for (String line : normalized.split("\\R")) {
            String cleaned = stripMarkdownMarker(line.trim());
            if (!cleaned.isBlank() && !cleaned.endsWith(":") && !cleaned.endsWith("：")) {
                items.add(cleaned);
            }
        }
        return items;
    }

    private String stripMarkdownMarker(String line) {
        return line.replaceFirst("^#{1,6}\\s*", "")
                .replaceFirst("^[-*+]\\s+", "")
                .replaceFirst("^\\d+[.、)]\\s*", "")
                .trim();
    }

    private void clean(List<String> items) {
        items.replaceAll(item -> item.replaceAll("\\s+", " ").trim());
        items.removeIf(String::isBlank);
    }

    private void mergeIfPresent(List<String> target, List<String> source) {
        if (source != null) {
            target.addAll(source);
        }
    }

    private boolean matches(String value, String... candidates) {
        for (String candidate : candidates) {
            if (value.equalsIgnoreCase(candidate) || value.contains(candidate.toLowerCase(Locale.ROOT))) {
                return true;
            }
        }
        return false;
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    private record FieldHeader(String field, String inlineValue) {
    }
}
