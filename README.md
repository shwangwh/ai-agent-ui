# UI 自动化测试 Agent

基于 `UI自动化测试Agent需求文档.md` 落地的 Spring Boot 后端 MVP。当前版本聚焦后端闭环：Markdown 用例上传、解析、确认/修正、执行任务编排、结构化日志、执行结果与 Allure 报告元数据查询。

## 技术栈

- Java 21
- Spring Boot 3.3
- Maven
- 当前存储：内存 + 本地 `data/` 文件目录
- 预留适配：PostgreSQL、Playwright Runner、Allure CLI

## 启动

```bash
mvn spring-boot:run
```

服务默认监听 `http://localhost:8080`。

## 核心接口

上传 Markdown 文档：

```http
POST /api/v1/test-documents
Content-Type: multipart/form-data
file=<cases.md>
```

创建解析任务：

```http
POST /api/v1/test-documents/{documentId}/parse
```

查询解析结果：

```http
GET /api/v1/parse-tasks/{parseTaskId}/cases
```

确认或修正解析结果：

```http
POST /api/v1/parse-tasks/{parseTaskId}/confirm
```

创建执行任务：

```http
POST /api/v1/execution-tasks
Content-Type: application/json

{
  "documentId": "doc_xxx",
  "parseTaskId": "parse_xxx",
  "environmentCode": "test",
  "runMode": "strict",
  "browser": "chromium",
  "headless": true
}
```

查询任务、日志、用例明细和报告：

```http
GET /api/v1/execution-tasks/{taskId}
GET /api/v1/execution-tasks/{taskId}/logs
GET /api/v1/execution-tasks/{taskId}/cases
GET /api/v1/execution-tasks/{taskId}/report
GET /api/v1/execution-tasks/{taskId}/artifacts
```

## 当前实现边界

当前执行器是 MVP 模拟适配层，会根据解析出的步骤和预期结果生成步骤结果、断言结果、日志和报告元数据。真实浏览器自动化执行、自愈定位、截图、Trace、Network 采集应在 `ExecutionTaskService` 后续拆出的 Playwright Runner Adapter 中接入。
