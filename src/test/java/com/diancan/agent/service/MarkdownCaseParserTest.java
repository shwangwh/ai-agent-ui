package com.diancan.agent.service;

import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class MarkdownCaseParserTest {

    @Test
    void parsesRecommendedMarkdownCase() throws Exception {
        String markdown = """
                ## 用例：用户成功提交订单
                用例编号：ORDER_001
                优先级：P0
                模块：点餐下单

                ### 前置条件
                - 用户已登录
                - 当前门店营业中

                ### 测试步骤
                1. 打开菜单页
                2. 点击菜品“宫保鸡丁”
                3. 点击“提交订单”按钮

                ### 预期结果
                - 订单提交成功
                - 页面展示订单号
                """;

        Object testCase = parseFirst(markdown);

        assertThat(get(testCase, "getCaseId")).isEqualTo("ORDER_001");
        assertThat(get(testCase, "getCaseName")).isEqualTo("用户成功提交订单");
        assertThat(get(testCase, "getPriority")).isEqualTo("P0");
        assertThat(get(testCase, "getModule")).isEqualTo("点餐下单");
        assertThat((List<?>) get(testCase, "getSteps")).hasSize(3);
        assertThat(list(testCase, "getExpectedResults")).contains("订单提交成功", "页面展示订单号");
        assertThat(String.valueOf(get(testCase, "getStatus"))).isEqualTo("executable");
    }

    @Test
    void parsesGivenWhenThenMarkdownCase() throws Exception {
        Object testCase = parseFirst("""
                case: 提交订单
                given:
                用户已经登录
                购物车为空

                when:
                打开菜单页 -> 选择宫保鸡丁 -> 加入购物车 -> 提交订单

                then:
                提示下单成功，生成订单号
                """);

        assertThat(get(testCase, "getCaseName")).isEqualTo("提交订单");
        assertThat(list(testCase, "getPreconditions")).contains("用户已经登录", "购物车为空");
        assertThat(list(testCase, "getSteps")).contains("打开菜单页", "选择宫保鸡丁", "加入购物车", "提交订单");
        assertThat(list(testCase, "getExpectedResults")).contains("提示下单成功", "生成订单号");
    }

    @Test
    void marksMissingExpectedResultInvalid() throws Exception {
        Object testCase = parseFirst("""
                ## 登录成功
                步骤：
                1、进入登录页
                2、点登录
                """);

        assertThat(String.valueOf(get(testCase, "getStatus"))).isEqualTo("invalid");
        assertThat(list(testCase, "getUncertainItems")).contains("缺少预期结果");
    }

    private Object parseFirst(String markdown) throws Exception {
        Class<?> parserType = Class.forName("com.diancan.agent.service.MarkdownCaseParser");
        Object parser = parserType.getConstructor(double.class, double.class).newInstance(0.85, 0.60);
        Method parse = parserType.getMethod("parse", String.class, String.class, String.class);
        List<?> cases = (List<?>) parse.invoke(parser, "doc_1", "parse_1", markdown);
        assertThat(cases).hasSize(1);
        return cases.getFirst();
    }

    private Object get(Object target, String methodName) throws Exception {
        return target.getClass().getMethod(methodName).invoke(target);
    }

    @SuppressWarnings("unchecked")
    private List<Object> list(Object target, String methodName) throws Exception {
        return (List<Object>) get(target, methodName);
    }
}
