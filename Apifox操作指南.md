# Apifox 操作指南

本文档说明如何通过 Apifox 调用 UI 自动化测试 Agent 后端。

当前服务地址：

```text
http://localhost:8080
```

如果服务没有启动，先在项目目录运行：

```bash
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

首次执行真实浏览器用例前，需要安装 Playwright 浏览器驱动：

```bash
.venv\Scripts\python -m playwright install chromium
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

## 2. 配置被测环境

默认已内置 `test` 环境：

```json
{
  "environmentCode": "test",
  "baseUrl": "http://localhost:3000",
  "domainWhitelist": ["localhost"]
}
```

如果需要修改：

```http
POST {{baseUrl}}/api/v1/config/environments
Content-Type: application/json
```

```json
{
  "environmentCode": "test",
  "baseUrl": "http://localhost:3000",
  "domainWhitelist": ["localhost"]
}
```

## 3. 上传 Markdown 用例

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
  "fileName": "cases.md",
  "fileSize": 1024,
  "createdAt": "2026-05-13T10:00:00+08:00",
  "message": "文档上传成功"
}
```

将返回的 `documentId` 保存为 Apifox 环境变量。

## 4. 创建解析任务

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

## 5. 查询解析结果

接口：

```http
GET {{baseUrl}}/api/v1/parse-tasks/{{parseTaskId}}/cases
```

重点查看：

```text
caseId
caseName
steps
expectedResults
parseConfidence
status
uncertainItems
```

只有 `status=executable` 的用例会进入真实执行。

## 6. 确认或修正用例

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
      "steps": ["打开 /", "点击“宫保鸡丁”", "点击“提交订单”"],
      "expectedResults": ["显示“订单提交成功”", "无报错"]
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

## 7. 创建执行任务

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
  "message": "执行完成，报告和证据已生成"
}
```

将返回的 `taskId` 保存为 `executionTaskId`。

## 8. 查询执行任务

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}
```

重点查看：

```text
totalCases
passed
failed
blocked
locatorUnresolved
allureReportUrl
jsonResultUrl
```

## 9. 查询用例执行明细

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/cases
```

每条用例会返回：

```text
steps
assertions
evidenceUrls
failureReason
durationMs
```

## 10. 查询日志

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/logs
```

常用过滤：

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/logs?level=INFO
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/logs?event=STEP_EXECUTION_FINISHED
```

## 11. 查询报告信息

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/report
```

响应中的 `allureReportUrl` 可以直接在浏览器访问，例如：

```text
http://localhost:8080/reports/allure/{{executionTaskId}}/index.html
```

## 12. 查询附件

```http
GET {{baseUrl}}/api/v1/execution-tasks/{{executionTaskId}}/artifacts
```

常见附件：

```text
screenshots/final.png
trace.zip
console.json
network.json
summary.json
```
