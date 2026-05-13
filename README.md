# UI 自动化测试 Agent

这是一个 Python/FastAPI 版本的 Markdown 驱动 UI 自动化测试 Agent 后端。当前版本已经从“模拟执行 MVP”升级为可落地的后端执行闭环：上传 Markdown 用例、解析并确认用例、调度 Playwright 执行真实浏览器操作、采集截图/Trace/Console/Network 证据、生成结构化结果和 HTML 报告。

## 技术栈

- Python 3.12
- FastAPI / Uvicorn
- Pydantic v2
- Playwright
- 本地文件存储：`data/`

## 本地启动

安装依赖：

```bash
.venv\Scripts\pip install -r requirements-dev.txt
```

首次使用真实浏览器执行前，需要安装 Playwright 浏览器驱动：

```bash
.venv\Scripts\python -m playwright install chromium
```

启动服务：

```bash
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

健康检查：

```http
GET http://localhost:8080/health
```

## 核心能力

- Markdown 用例上传、解析、置信度评估和人工确认/修正。
- 执行环境配置，支持 `baseUrl` 和 `domainWhitelist`。
- Playwright 真实浏览器执行，支持 `chromium`、`firefox`、`webkit`。
- 基础自然语言步骤映射：打开、点击、选择、输入、等待、滚动。
- 基础断言映射：文本可见、URL 包含、Console 无报错。
- 执行证据采集：最终截图、Playwright Trace、Console、Network、执行摘要。
- 报告输出：Allure 风格 JSON 结果文件和可直接访问的 HTML 报告页。
- 结构化日志查询，支持按用例、步骤、级别和事件过滤。

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

配置执行环境：

```http
POST /api/v1/config/environments
Content-Type: application/json

{
  "environmentCode": "test",
  "baseUrl": "http://localhost:3000",
  "domainWhitelist": ["localhost"]
}
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

查询任务、日志、用例明细、报告和附件：

```http
GET /api/v1/execution-tasks/{taskId}
GET /api/v1/execution-tasks/{taskId}/logs
GET /api/v1/execution-tasks/{taskId}/cases
GET /api/v1/execution-tasks/{taskId}/report
GET /api/v1/execution-tasks/{taskId}/artifacts
```

报告和附件也会通过静态路径暴露：

```http
GET /reports/allure/{taskId}/index.html
GET /artifacts/{taskId}/{caseRunId}/screenshots/final.png
GET /artifacts/{taskId}/{caseRunId}/trace.zip
```

## Markdown 用例建议格式

```markdown
## 用例：用户成功提交订单
用例编号：ORDER_001
优先级：P0
模块：点餐下单

### 前置条件
- 用户已登录

### 测试步骤
1. 打开 /
2. 点击“宫保鸡丁”
3. 点击“提交订单”

### 预期结果
- 显示“订单提交成功”
- 无报错
```

## 当前边界

当前版本已经执行真实浏览器操作，但自然语言步骤到页面操作的映射仍是规则驱动，适合规范化 Markdown 用例。复杂控件、动态定位、自愈策略和更丰富的业务断言可以继续在 `PlaywrightExecutionRunner` 中扩展。报告生成采用本地 HTML 报告和 Allure 风格结果文件；如果团队已有 Allure CLI，可基于 `data/allure-results/{taskId}` 做进一步集成。

## 测试

```bash
.venv\Scripts\python -m pytest -q
```
