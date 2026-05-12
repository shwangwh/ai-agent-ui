# Apifox 操作指南

本文档说明如何通过 Apifox 调用当前 UI 自动化测试 Agent 后端项目。

当前服务地址：

```text
http://localhost:8080
```

如果服务没有启动，先在项目目录运行：

```bash
mvn spring-boot:run
```

## 1. 配置环境变量

在 Apifox 新建环境，例如 `local`：

```text
baseUrl = http://localhost:8080
```

后续接口地址都可以写成：

```text
{{baseUrl}}/api/v1/...
```

## 2. 上传 Markdown 用例

接口：

```http
POST {{baseUrl}}/api/v1/test-documents
```

Body 选择 `form-data`：

```text
key: file
type: File
value: 选择一个 .md 文件
```

响应示例：

```json
{
  "documentId": "doc_xxx",
  "fileName": "xxx.md",
  "message": "文档上传成功"
}
```

将返回的 `documentId` 保存为 Apifox 环境变量。

## 3. 创建解析任务

接口：

```http
POST {{baseUrl}}/api/v1/test-documents/{{documentId}}/parse
Content-Type: application/json
```

Body：

```json
{
  "parseMode": "smart"
}
```

响应示例：

```json
{
  "taskId": "parse_xxx",
  "status": "finished",
  "message": "解析完成"
}
```

这里返回的 `taskId` 就是 `parseTaskId`，将它保存为 Apifox 环境变量。

## 4. 查询解析结果

接口：

```http
GET {{baseUrl}}/api/v1/parse-tasks/{{parseTaskId}}/cases
```

响应示例：

```json
[
  {
    "caseId": "ORDER_001",
    "caseName": "用户成功提交订单",
    "steps": [],
    "expectedResults": [],
    "parseConfidence": 0.9,
    "status": "executable"
  }
]
```

## 5. 确认或修正用例

接口：

```http
POST {{baseUrl}}/api/v1/parse-tasks/{{parseTaskId}}/confirm
Content-Type: application/json
```

确认用例：

```json
{
  "cases": [
    {
      "caseId": "ORDER_001",
      "action": "confirm"
    }
  ]
}
```

修正字段：

```json
{
  "cases": [
    {
      "caseId": "ORDER_001",
      "action": "revise",
      "caseName": "用户成功提交订单",
      "module": "点餐下单",
      "priority": "P0",
      "preconditions": ["用户已登录"],
      "steps": ["打开菜单页", "点击菜品“宫保鸡丁”", "点击提交订单按钮"],
      "expectedResults": ["订单提交成功", "页面展示订单号"]
    }
  ]
}
```

`action` 支持：

```text
confirm
revise
skip
mark_invalid
save
```

## 6. 创建执行任务

接口：

```http
POST {{baseUrl}}/api/v1/execution-tasks
Content-Type: application/json
```

Body：

```json
{
  "documentId": "{{documentId}}",
  "parseTaskId": "{{parseTaskId}}",
  "environmentCode": "test",
  "runMode": "strict",
  "browser": "chromium",
  "headless": true,
  "caseFilter": {
    "priorities": ["P0", "P1"],
    "tags": []
  },
  "report": {
    "type": "allure",
    "generateAfterDocumentFinished": true
  }
}
```

响应示例：

```json
{
  "taskId": "exec_xxx",
  "status": "finished",
  "message": "执行完成，Allure 报告元数据已生成"
}
```

将返回的 `taskId` 保存为 `executionTaskId`。

## 7. 查询执行结果

接口：

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}
```

## 8. 查询用例执行明细

接口：

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/cases
```

## 9. 查询日志

接口：

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/logs
```

按日志级别过滤：

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/logs?level=INFO
```

## 10. 查询报告信息

接口：

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/report
```

当前返回的是 Allure 报告元数据，真实 Allure 页面还没有接入生成。
