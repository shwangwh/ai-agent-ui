# UI 自动化测试 Agent 需求文档

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 产品名称 | UI 自动化测试 Agent |
| 文档类型 | 产品需求文档 PRD |
| 版本 | V1.0 |
| 编写日期 | 2026-05-12 |
| 目标阶段 | 可落地后端项目 |
| 产品定位 | Markdown 用例驱动的 UI 自动化测试 Agent |

## 2. 产品背景

当前 UI 自动化测试在实际落地中常见以下问题：

1. 测试人员已有大量 Markdown、文档、表格形式的历史用例，但格式不完全统一。
2. 传统自动化脚本需要人工维护选择器，页面结构稍有变化就容易失败。
3. 自动化报告经常只给出失败结果，无法清楚区分是业务失败、环境失败，还是元素定位失败。
4. 执行失败后的证据链不足，测试人员仍然需要手动复现、截图、查看日志。
5. 现有 AI 测试工具较多强调自动生成用例，但本产品场景中，用例主要由用户提供。

因此，本产品的核心价值不是替用户设计测试用例，而是将用户已有的 Markdown 用例转化为可执行、可断言、可追踪、可报告的自动化测试任务。

## 3. 产品定位

本产品是一个基于用户提供用例的 UI 自动化测试 Agent。

用户提交 `.md` 格式测试用例文档，Agent 自动解析其中的用例名称、前置条件、测试步骤、预期结果等信息，并根据解析结果完成浏览器自动化执行、断言校验、失败归因和测试报告生成。

一句话定位：

> 一个 Markdown 用例驱动的 UI 自动化测试 Agent，负责根据用户已有用例自动执行测试、校验预期结果，并输出可信的测试报告。

## 4. 产品目标

### 4.1 业务目标

1. 降低测试人员手工执行回归用例的成本。
2. 提升已有 Markdown 用例的自动化执行率。
3. 减少因元素定位失败造成的误报。
4. 提升测试报告的可读性和可信度。
5. 支持后续接入 CI/CD，形成持续回归能力。

### 4.2 项目目标

项目需要完成以下闭环：

```text
上传 Markdown 用例
  ↓
Agent 解析用例
  ↓
调用方确认或直接执行解析结果
  ↓
Agent 执行 UI 自动化测试
  ↓
Agent 根据预期结果断言
  ↓
生成测试报告
```

项目成功标准：

1. 能解析常见非标准 Markdown 用例。
2. 能执行 Web UI 自动化测试。
3. 能根据预期结果完成基础断言。
4. 能在元素定位失败时尝试自动修复。
5. 能区分业务失败和自动化执行失败。
6. 能输出包含证据链的测试报告。

## 5. 目标用户

| 用户角色 | 诉求 |
| --- | --- |
| QA 测试工程师 | 上传已有用例，自动执行回归测试，减少重复劳动 |
| 自动化测试工程师 | 将自然语言用例转化为可维护的自动化资产 |
| 开发工程师 | 在提测前快速执行冒烟用例 |
| QA Lead | 查看执行结果、失败归因、质量趋势 |
| 研发负责人 | 在发版前获得稳定可信的质量报告 |

## 6. 使用场景

### 6.1 冒烟测试

测试人员上传核心流程 Markdown 用例，Agent 自动执行登录、下单、支付、查询等主路径，快速判断版本是否具备提测或发版条件。

### 6.2 回归测试

发版前执行已有回归用例集，Agent 输出通过率、失败用例、失败原因和证据。

### 6.3 缺陷复测

用户将 Bug 复现步骤整理为 Markdown 用例，Agent 自动执行并判断问题是否修复。

### 6.4 开发自测

开发人员在本地或测试环境上传简单用例，验证核心页面流程是否正常。

### 6.5 CI/CD 集成

后续支持在流水线中执行指定 Markdown 用例集，并在整份用例文档执行完成后统一生成 Allure 测试报告。

## 7. 产品边界

### 7.1 本期建设范围

本期作为可落地后端项目，需要支持：

1. Markdown 用例上传。
2. 非标准 Markdown 用例智能解析。
3. 用例解析结果结构化返回。
4. 调用方通过接口确认、修正、跳过用例。
5. Web UI 自动化执行。
6. 基础前置条件处理。
7. 基础 UI 操作执行。
8. 基础断言生成与执行。
9. 元素定位容错与自愈。
10. 截图、日志、网络请求、Trace 等证据采集。
11. Allure 测试报告，整份用例文档执行完成后统一输出。
12. 执行结果分类，包括通过、业务失败、定位失败、环境阻塞、执行异常等。

### 7.2 本期不建设范围

1. 自动生成完整测试用例。
2. 移动端 App 自动化。
3. 大规模多浏览器并发云测。
4. 深度数据库断言。
5. 自动创建缺陷单。
6. 复杂视觉还原度断言。
7. 跨系统链路质量分析。
8. 前端控制台页面。

## 8. 总体流程

```text
用户上传 .md 用例文档
  ↓
Markdown Parser 解析用例块
  ↓
Agent 标准化用例结构
  ↓
Agent 评估解析置信度
  ↓
调用方通过接口确认、修正或跳过解析结果
  ↓
Execution Planner 生成执行计划
  ↓
UI Executor 调用 Playwright 执行浏览器操作
  ↓
Locator Healing Engine 处理元素定位失败
  ↓
Assertion Engine 根据预期结果执行断言
  ↓
Evidence Collector 采集证据
  ↓
Report Generator 生成测试报告
```

## 9. Markdown 用例输入设计

### 9.1 推荐用例格式

系统推荐用户使用以下格式，但不强制要求完全一致。

```md
# 点餐系统回归测试用例

## 用例：用户成功提交订单

用例编号：ORDER_001
优先级：P0
模块：点餐下单

### 前置条件
- 用户已登录
- 当前门店营业中
- 菜品“宫保鸡丁”库存充足

### 测试步骤
1. 打开菜单页
2. 点击菜品“宫保鸡丁”
3. 点击购物车
4. 点击“提交订单”按钮

### 预期结果
- 菜品成功加入购物车
- 订单提交成功
- 页面展示订单号
- 订单状态为“待支付”
```

### 9.2 非标准格式兼容

用户当前使用的模板可能不标准，因此系统需要支持常见的半结构化写法。

示例一：

```md
## 登录成功
前提：账号已存在
步骤：
1、进入登录页
2、输入手机号 13800000000
3、输入密码 123456
4、点登录

期望：
进入首页，看到用户昵称
```

示例二：

```md
case: 提交订单
given:
用户已经登录
购物车为空

when:
打开菜单页 -> 选择宫保鸡丁 -> 加入购物车 -> 提交订单

then:
提示下单成功，生成订单号
```

示例三：

```md
【用例名称】密码错误登录失败
【前置】账号存在
【操作】打开登录页；输入错误密码；点击登录
【预期】提示账号或密码错误，不进入首页
```

## 10. Markdown 解析能力

### 10.1 字段识别

Agent 需要从 Markdown 中识别以下字段：

| 字段 | 是否必需 | 说明 |
| --- | --- | --- |
| case_name | 是 | 用例名称 |
| case_id | 否 | 用例编号，缺失时由系统生成 |
| module | 否 | 所属模块 |
| priority | 否 | P0 / P1 / P2 |
| preconditions | 否 | 前置条件 |
| steps | 是 | 测试步骤 |
| expected_results | 是 | 预期结果 |
| test_data | 否 | 测试数据 |
| tags | 否 | 标签 |
| remarks | 否 | 备注 |

### 10.2 标题识别

系统需要识别以下标题或同义表达：

| 标准字段 | 可识别表达 |
| --- | --- |
| 用例名称 | 用例、case、场景、测试点、标题 |
| 前置条件 | 前置、前提、given、准备条件、初始化条件 |
| 测试步骤 | 步骤、操作、when、操作步骤、测试过程 |
| 预期结果 | 预期、期望、then、校验点、断言、结果 |

### 10.3 分隔符兼容

系统需要支持以下分隔方式：

1. Markdown 标题。
2. 编号列表。
3. 无序列表。
4. 中文分号。
5. 英文分号。
6. 箭头 `->`。
7. 中文顿号、逗号。
8. 表格。
9. 分割线 `---`。
10. 多用例连续书写。

### 10.4 解析输出结构

解析后的内部结构示例：

```json
{
  "case_id": "LOGIN_001",
  "case_name": "手机号密码登录成功",
  "priority": "P0",
  "module": "登录",
  "preconditions": [
    "用户账号存在",
    "用户密码正确"
  ],
  "steps": [
    "打开登录页",
    "在手机号输入框输入：13800000000",
    "在密码输入框输入：123456",
    "点击登录按钮"
  ],
  "expected_results": [
    "登录成功",
    "页面跳转到首页",
    "首页展示用户昵称"
  ],
  "parse_confidence": 0.92,
  "status": "executable"
}
```

## 11. 用例解析确认

### 11.1 功能说明

由于用户提供的 Markdown 用例可能不标准，Agent 在执行前必须通过后端接口返回结构化解析结果，而不是直接静默执行。

本项目不建设前端页面，解析确认由调用方系统完成。后端需要提供查询、确认、修正、跳过等接口，方便外部系统、脚本或 CI 流程集成。

### 11.2 解析结果内容

每条用例解析结果需要返回：

1. 原始 Markdown 片段。
2. Agent 解析出的用例名称。
3. 前置条件。
4. 测试步骤。
5. 预期结果。
6. 测试数据。
7. 解析置信度。
8. 执行状态。
9. 不确定项说明。

### 11.3 调用方操作

调用方可以通过接口对解析结果执行：

1. 确认执行。
2. 修正字段后执行。
3. 跳过该用例。
4. 标记为不可执行。
5. 保存为标准结构化用例。

### 11.4 解析状态

| 状态 | 说明 |
| --- | --- |
| executable | 字段完整，步骤和预期清晰，可执行 |
| need_review | 大部分内容可解析，但存在不确定项，需要人工确认 |
| invalid | 缺少关键字段，无法执行 |
| skipped | 用户选择跳过 |

### 11.5 置信度规则

| 置信度 | 系统处理 |
| --- | --- |
| 大于等于 85% | 默认可执行，仍通过接口返回结构化结果 |
| 60% 到 85% | 进入人工确认队列 |
| 小于 60% | 标记为不可执行，要求用户补充 |

## 12. 前置条件处理

### 12.1 功能说明

Agent 需要根据用例中的前置条件完成测试准备或校验。前置条件不能只作为说明文字，应尽量被转化为可执行动作或检查项。

### 12.2 前置条件处理策略

| 前置条件示例 | Agent 处理方式 |
| --- | --- |
| 用户已登录 | 复用登录态，或执行登录流程 |
| 用户账号存在 | 检查测试账号配置 |
| 用户密码正确 | 使用配置中的测试密码 |
| 当前门店营业中 | 打开门店页校验营业状态，或调用准备接口 |
| 菜品库存充足 | 检查菜品是否可加购 |
| 购物车为空 | 打开购物车并清空，或调用清理接口 |
| 当前无未支付订单 | 检查订单列表，或调用清理接口 |

### 12.3 前置条件状态

| 状态 | 说明 |
| --- | --- |
| passed | 前置条件已满足 |
| prepared | Agent 已自动准备完成 |
| need_manual_confirm | 需要人工确认 |
| blocked | 前置条件不满足，阻塞执行 |

### 12.4 前置条件阻塞规则

如果关键前置条件无法满足，Agent 不应继续执行后续步骤，应将用例标记为 `blocked`。

示例：

```text
用例：提交订单成功
状态：blocked
原因：前置条件“当前门店营业中”未满足
说明：当前门店状态为“休息中”，无法继续执行下单流程
```

## 13. 测试步骤执行

### 13.1 支持动作

本期需要支持以下 UI 操作：

| 动作 | 说明 |
| --- | --- |
| open | 打开页面 |
| click | 点击元素 |
| input | 输入文本 |
| clear | 清空输入框 |
| select | 下拉选择 |
| check | 勾选 |
| uncheck | 取消勾选 |
| hover | 鼠标悬停 |
| scroll | 页面滚动 |
| wait | 等待页面状态 |
| press | 键盘操作 |
| upload | 上传文件 |
| switch_tab | 切换标签页 |
| close_popup | 关闭弹窗 |
| screenshot | 截图 |

### 13.2 自然语言步骤转换

Agent 需要将自然语言步骤转换为结构化动作。

| Markdown 步骤 | 结构化动作 |
| --- | --- |
| 打开登录页 | `open("/login")` |
| 点击登录按钮 | `click("登录按钮")` |
| 在手机号输入框输入：13800000000 | `input("手机号输入框", "13800000000")` |
| 选择门店“上海人民广场店” | `select_or_click("上海人民广场店")` |
| 点击菜品“宫保鸡丁” | `click("宫保鸡丁")` |
| 等待订单提交完成 | `wait_for("订单提交完成")` |

### 13.3 执行原则

1. Agent 负责理解用例语义和生成执行计划。
2. Playwright 负责真实浏览器操作。
3. 操作执行前需要等待页面稳定。
4. 每一步操作都需要记录执行状态。
5. 操作失败后需要进入定位自愈或失败归因流程。

## 14. 断言设计

### 14.1 功能说明

Agent 根据 Markdown 中的预期结果自动生成断言，并通过浏览器页面状态、DOM、URL、接口响应、文本内容等方式验证结果。

### 14.2 支持断言类型

| 断言类型 | 示例 |
| --- | --- |
| text_visible | 页面出现指定文本 |
| element_visible | 指定元素可见 |
| element_hidden | 指定元素不可见 |
| url_contains | URL 包含指定内容 |
| value_equals | 输入框值等于预期 |
| count_equals | 数量符合预期 |
| toast_visible | 出现提示信息 |
| button_enabled | 按钮可点击 |
| button_disabled | 按钮不可点击 |
| regex_match | 页面出现符合规则的文本，例如订单号 |
| api_success | 关键接口返回成功 |
| no_console_error | 页面无严重 Console 错误 |

### 14.3 预期结果转换规则

| 预期结果 | 断言方式 |
| --- | --- |
| 页面跳转到首页 | URL、页面标题、首页关键元素 |
| 页面提示“账号或密码错误” | 文本可见断言 |
| 展示订单号 | 文本正则匹配 |
| 订单状态为“待支付” | 文本或元素状态断言 |
| 按钮不可点击 | disabled 状态断言 |
| 购物车数量为 1 | 数值断言 |
| 金额为 28 元 | 文本或数值断言 |
| 页面无报错 | Console 和页面错误断言 |

### 14.4 断言优先级

断言应优先采用确定性方式。

```text
结构化断言 > 页面状态断言 > URL 断言 > 接口断言 > 视觉断言 > LLM 辅助判断
```

### 14.5 断言原则

1. 不应只依赖大模型判断测试是否通过。
2. 每个断言必须保留实际结果。
3. 断言失败必须展示预期结果和实际结果。
4. 多个预期结果应拆成多个独立断言。
5. 用例最终结果由步骤执行结果和断言结果共同决定。

## 15. 元素定位容错与自愈

### 15.1 背景

用户明确希望自动化测试执行时，不要因为单一元素定位失败就直接在报告中提示业务失败。元素定位失败常常是自动化执行问题，不一定代表被测系统功能失败。

因此系统必须区分：

```text
元素定位失败 != 业务功能失败
```

### 15.2 定位策略

每个元素目标都需要生成多个候选定位方式。

推荐优先级：

1. `data-testid`
2. role + accessible name
3. label
4. placeholder
5. text
6. CSS selector
7. XPath
8. DOM 语义相似元素
9. 截图视觉识别兜底

### 15.3 自愈流程

```text
执行步骤：点击“提交订单”按钮
  ↓
尝试主定位器
  ↓
定位失败
  ↓
等待页面稳定后重试
  ↓
重新获取 DOM 和可访问性快照
  ↓
生成候选元素
  ↓
根据文本、类型、区域、上下文、属性进行评分
  ↓
高置信度候选自动执行
  ↓
低置信度候选进入人工确认或标记 unresolved
```

### 15.4 候选元素评分维度

| 维度 | 说明 |
| --- | --- |
| 文案相似度 | 登录 vs 立即登录 |
| 元素类型 | button、input、select 等是否一致 |
| 可见性 | 元素是否可见、可点击 |
| 页面区域 | 是否处于相似区域 |
| 上下文 | 是否位于相关表单或模块内 |
| 属性相似度 | id、class、name、aria-label、data-testid |
| 操作语义 | 点击、输入、选择等动作是否匹配 |

### 15.5 自愈阈值

| 评分 | 处理 |
| --- | --- |
| 大于等于 90 | 自动使用候选元素，并记录自愈 |
| 75 到 90 | 智能模式下可提示用户确认，严格模式下不自动执行 |
| 小于 75 | 标记为 locator_unresolved |

### 15.6 报告展示

如果定位自愈成功，报告中应展示：

```text
步骤：点击“提交订单”按钮
原定位：getByRole('button', { name: '提交订单' })
新定位：getByRole('button', { name: '确认下单' })
相似度：91%
处理结果：自愈成功，步骤继续执行
```

如果定位自愈失败，报告中应展示：

```text
用例状态：locator_unresolved
说明：Agent 无法在当前页面找到与“提交订单按钮”匹配的高置信度元素。
结论：该结果不能证明业务功能失败，建议检查页面是否变更、用例是否过期或元素标识是否缺失。
```

## 16. 执行结果分类

测试报告中不应只有 passed / failed，需要更细的结果分类。

| 状态 | 含义 |
| --- | --- |
| passed | 用例通过 |
| failed | 业务断言失败 |
| blocked | 前置条件或环境阻塞 |
| locator_healed | 元素定位失败但已自愈，最终执行通过 |
| locator_unresolved | 元素定位失败且无法自愈 |
| assertion_failed | 页面执行成功，但预期断言失败 |
| execution_error | Agent 或脚本执行异常 |
| environment_error | 测试环境异常 |
| test_data_error | 测试数据异常 |
| skipped | 用例跳过 |

最终报告需要同时展示：

1. 用例最终状态。
2. 是否存在定位自愈。
3. 是否存在前置条件阻塞。
4. 是否存在业务断言失败。
5. 是否存在执行异常。

## 17. 证据采集

### 17.1 采集内容

Agent 在执行过程中需要自动采集：

1. 每一步执行状态。
2. 每一步关键截图。
3. 失败截图。
4. 页面 URL。
5. DOM 快照。
6. Accessibility snapshot。
7. Console 日志。
8. Network 请求和响应摘要。
9. Playwright trace。
10. 执行耗时。
11. 错误堆栈。
12. 定位自愈记录。

### 17.2 失败时必须采集

失败用例至少保留：

1. 失败步骤。
2. 失败截图。
3. 预期结果。
4. 实际结果。
5. Console error。
6. 关键 Network 请求。
7. 当前页面 URL。
8. Trace 链接。
9. 失败归因。

## 18. 测试报告设计

### 18.1 报告格式

本期测试报告统一使用 Allure。

报告生成规则：

1. Agent 执行同一个 Markdown 用例文档时，需要先完成文档内全部可执行用例。
2. 每条用例执行过程中只采集 Allure 所需的结果数据和附件，不在单条用例结束时生成最终报告。
3. 整个用例文档执行完成后，由 Report Generator 统一汇总并生成 Allure Report。
4. Allure 报告中需要保留用例层级、步骤层级、断言结果、失败原因、截图、Trace、Console 日志和 Network 摘要。
5. 对于 `blocked`、`locator_unresolved`、`execution_error` 等非业务失败状态，需要在 Allure 中通过标签、状态说明或附件明确区分，避免被误读为普通业务断言失败。

辅助输出：

1. JSON 结构化结果用于系统存储和接口返回。
2. Markdown 摘要用于页面展示或通知消息。
3. JUnit XML 作为后续 CI/CD 兼容能力，不作为本期主报告。

### 18.2 报告总览

报告总览需要展示：

| 字段 | 说明 |
| --- | --- |
| 测试任务 ID | 本次执行唯一 ID |
| 执行环境 | test / staging / production |
| 浏览器 | Chromium / Firefox / WebKit |
| 开始时间 | 执行开始时间 |
| 结束时间 | 执行结束时间 |
| 总耗时 | 执行耗时 |
| 用例总数 | 总执行用例数 |
| 通过数 | passed |
| 失败数 | failed |
| 阻塞数 | blocked |
| 定位自愈数 | locator_healed |
| 定位失败数 | locator_unresolved |
| 跳过数 | skipped |
| 通过率 | passed / total |

### 18.3 用例详情

每条用例需要展示：

1. 用例编号。
2. 用例名称。
3. 所属模块。
4. 优先级。
5. 执行结果。
6. 执行耗时。
7. 前置条件处理结果。
8. 步骤执行明细。
9. 预期结果断言明细。
10. 失败步骤。
11. 失败原因。
12. 定位自愈记录。
13. 截图。
14. Trace 链接。
15. Console 日志。
16. Network 日志。

### 18.4 失败分析示例

```text
用例编号：LOGIN_002
用例名称：密码错误登录失败
执行结果：failed

失败步骤：
第 4 步：点击登录按钮

失败断言：
预期：页面提示“账号或密码错误”
实际：页面提示“系统异常，请稍后再试”

失败类型：
assertion_failed

可能原因：
登录接口返回 500，非预期业务错误提示

证据：
- 失败截图
- 登录接口响应
- Console 错误
- Trace 文件
```

### 18.5 定位失败示例

```text
用例编号：ORDER_001
用例名称：用户成功提交订单
执行结果：locator_unresolved

失败步骤：
第 4 步：点击“提交订单”按钮

说明：
Agent 无法在当前页面找到与“提交订单按钮”匹配的高置信度元素。

结论：
该结果不能证明业务功能失败。建议检查页面文案是否变更、用例步骤是否过期，或为关键按钮补充 data-testid。
```

## 19. 技术方案建议

### 19.1 总体架构

```text
Markdown 用例
  ↓
Case Parser
  ↓
Case Review
  ↓
Execution Planner
  ↓
Playwright UI Executor
  ↓
Locator Healing Engine
  ↓
Assertion Engine
  ↓
Evidence Collector
  ↓
Report Generator
```

### 19.2 模块职责

| 模块 | 职责 |
| --- | --- |
| Case Parser | 解析 Markdown 用例 |
| Case Review | 返回解析结果，支持调用方确认、修正和跳过 |
| Execution Planner | 生成可执行步骤和等待策略 |
| UI Executor | 调用 Playwright 执行浏览器操作 |
| Locator Healing Engine | 处理元素定位失败和自愈 |
| Assertion Engine | 根据预期结果生成并执行断言 |
| Evidence Collector | 采集截图、日志、Trace、Network |
| Report Generator | 在整份 Markdown 用例文档执行完成后统一生成 Allure 测试报告 |

### 19.3 推荐技术栈

| 模块 | 推荐技术 |
| --- | --- |
| 浏览器自动化 | Playwright |
| Agent 能力 | LLM + 工具调用 |
| Markdown 解析 | Markdown AST parser + LLM 辅助解析 |
| 后端服务 | Spring Boot |
| 任务队列 | Spring Task / Spring Batch / MQ，按项目复杂度选择 |
| 存储 | PostgreSQL |
| 文件存储 | 本地文件 / MinIO / S3 |
| 对外调用 | REST API + 可选 Java SDK |
| 报告 | Allure Report + JSON 结构化结果 |
| CI 集成 | CLI + Allure Report，后续兼容 JUnit XML |

### 19.4 Playwright 分工

建议采用以下职责划分：

```text
Agent 负责理解、规划、归因和报告
Playwright 负责真实浏览器执行、断言和证据采集
```

不建议让大模型直接无约束地操作浏览器。更稳妥的方式是：Agent 将自然语言用例转换为结构化执行计划，由 Playwright 执行确定性操作和断言。

### 19.5 Spring Boot 后端实现约束

本项目代码编写以 Spring Boot 为后端主框架。

Spring Boot 服务需要承担以下职责：

1. 接收 Markdown 用例文档上传。
2. 管理用例解析任务、执行任务和报告生成任务。
3. 存储原始用例、解析结果、执行结果和报告元数据。
4. 调度 Playwright 执行器执行 UI 自动化任务。
5. 汇总每条用例的执行结果、截图、Trace、Console 日志和 Network 摘要。
6. 在整份 Markdown 用例文档执行完成后触发 Allure Report 生成。
7. 提供测试任务查询、执行进度查询、报告查看和报告下载接口。
8. 管理测试环境、测试账号、执行配置和敏感数据脱敏。
9. 为关键处理步骤输出结构化日志，支持问题排查和链路追踪。

推荐后端模块拆分：

| 模块 | 说明 |
| --- | --- |
| case-parser-service | Markdown 用例解析与结构化转换 |
| case-review-service | 解析结果确认、编辑和状态管理 |
| execution-service | 测试任务编排和执行状态管理 |
| playwright-runner-adapter | 调用 Playwright 执行器并接收执行结果 |
| assertion-service | 断言规则生成和断言结果归档 |
| evidence-service | 截图、Trace、日志、Network 附件管理 |
| allure-report-service | Allure 结果聚合和报告生成 |
| config-service | 环境、账号、域名白名单和执行配置管理 |
| api-service | 对外 REST API 和调用示例封装 |
| log-service | 执行日志、步骤日志和链路日志管理 |

## 20. 对外调用设计

本项目不建设前端页面，只提供后端服务能力。外部系统可以通过 REST API 调用 Agent，也可以后续封装 Java SDK 或 CLI。

### 20.1 核心调用流程

```text
上传 Markdown 用例文档
  ↓
创建解析任务
  ↓
查询解析结果
  ↓
确认或修正解析结果
  ↓
创建执行任务
  ↓
查询执行进度
  ↓
等待整份文档执行完成
  ↓
获取 Allure 报告地址和 JSON 结果
```

### 20.2 REST API 清单

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/test-documents` | POST | 上传 Markdown 用例文档 |
| `/api/v1/test-documents/{documentId}` | GET | 查询文档详情 |
| `/api/v1/test-documents/{documentId}/parse` | POST | 创建解析任务 |
| `/api/v1/parse-tasks/{parseTaskId}` | GET | 查询解析任务状态 |
| `/api/v1/parse-tasks/{parseTaskId}/cases` | GET | 查询结构化用例解析结果 |
| `/api/v1/parse-tasks/{parseTaskId}/confirm` | POST | 确认或修正解析结果 |
| `/api/v1/execution-tasks` | POST | 创建自动化执行任务 |
| `/api/v1/execution-tasks/{taskId}` | GET | 查询执行任务状态 |
| `/api/v1/execution-tasks/{taskId}/logs` | GET | 查询任务日志 |
| `/api/v1/execution-tasks/{taskId}/cases` | GET | 查询用例执行明细 |
| `/api/v1/execution-tasks/{taskId}/report` | GET | 查询 Allure 报告信息 |
| `/api/v1/execution-tasks/{taskId}/artifacts` | GET | 查询截图、Trace、日志等附件 |
| `/api/v1/config/environments` | GET/POST | 查询或创建测试环境配置 |
| `/api/v1/config/accounts` | GET/POST | 查询或创建测试账号配置 |

### 20.3 创建执行任务示例

请求：

```http
POST /api/v1/execution-tasks
Content-Type: application/json
```

```json
{
  "documentId": "doc_202605120001",
  "parseTaskId": "parse_202605120001",
  "environmentCode": "test",
  "runMode": "strict",
  "browser": "chromium",
  "headless": true,
  "caseFilter": {
    "priorities": ["P0", "P1"],
    "tags": ["smoke"]
  },
  "report": {
    "type": "allure",
    "generateAfterDocumentFinished": true
  }
}
```

响应：

```json
{
  "taskId": "exec_202605120001",
  "status": "created",
  "message": "执行任务已创建"
}
```

### 20.4 查询执行结果示例

```http
GET /api/v1/execution-tasks/exec_202605120001
```

```json
{
  "taskId": "exec_202605120001",
  "documentId": "doc_202605120001",
  "status": "finished",
  "totalCases": 20,
  "passed": 16,
  "failed": 2,
  "blocked": 1,
  "locatorUnresolved": 1,
  "startedAt": "2026-05-12T16:20:00+08:00",
  "finishedAt": "2026-05-12T16:28:30+08:00",
  "allureReportUrl": "/reports/allure/exec_202605120001/index.html",
  "jsonResultUrl": "/api/v1/execution-tasks/exec_202605120001/cases"
}
```

### 20.5 Java SDK 调用示例

后续可提供轻量 Java SDK，便于其他 Spring Boot 项目集成。

```java
UiTestAgentClient client = new UiTestAgentClient("http://agent-host:8080");

String documentId = client.uploadMarkdown("order-regression.md");
String parseTaskId = client.parseDocument(documentId);

ParsedCases cases = client.waitParseFinished(parseTaskId);
client.confirmCases(parseTaskId, cases);

ExecutionTask task = client.createExecutionTask(ExecutionTaskRequest.builder()
    .documentId(documentId)
    .parseTaskId(parseTaskId)
    .environmentCode("test")
    .browser("chromium")
    .headless(true)
    .runMode("strict")
    .build());

ExecutionResult result = client.waitExecutionFinished(task.getTaskId());
System.out.println(result.getAllureReportUrl());
```

## 21. 日志输出规范

项目主要步骤都需要有日志输出。日志既要方便开发排查，也要能支撑测试任务追踪和报告归因。

### 21.1 日志原则

1. 每个测试任务必须生成唯一 `traceId`。
2. 每个执行任务必须生成唯一 `taskId`。
3. 每条用例必须生成唯一 `caseRunId`。
4. 每个测试步骤必须生成唯一 `stepRunId`。
5. 后端日志、执行日志、Allure 附件日志需要能通过 `taskId` 关联。
6. 日志中不得明文输出密码、Token、Cookie、手机号等敏感信息。
7. 关键状态变更必须打日志，例如 `created`、`parsing`、`running`、`finished`、`failed`。

### 21.2 必须输出日志的步骤

| 阶段 | 必须输出的日志 |
| --- | --- |
| 文档上传 | 文件名、文件大小、documentId、上传结果 |
| 用例解析开始 | parseTaskId、documentId、解析模式 |
| 用例切分 | 识别到的用例数量、无法识别的片段数量 |
| 字段解析 | caseId、caseName、parseConfidence、status |
| 解析确认 | 确认人或调用方、确认时间、修正字段数量 |
| 执行任务创建 | taskId、environmentCode、browser、runMode |
| 前置条件处理 | caseRunId、前置条件、处理状态、失败原因 |
| 步骤执行开始 | stepRunId、action、target、value 是否脱敏 |
| 元素定位 | 主定位器、候选定位器数量、定位结果 |
| 元素自愈 | 原定位器、新定位器、相似度、是否采用 |
| 断言执行 | assertionType、expected、actual、result |
| 证据采集 | screenshot、trace、console、network 附件路径 |
| 用例结束 | caseRunId、status、duration、失败类型 |
| 文档执行结束 | taskId、总数、通过数、失败数、阻塞数、耗时 |
| Allure 生成 | resultsDir、reportDir、生成状态、报告地址 |

### 21.3 日志级别

| 级别 | 使用场景 |
| --- | --- |
| INFO | 任务创建、解析完成、用例开始结束、报告生成等关键流程 |
| WARN | 低置信度解析、定位自愈、前置条件需人工确认、非阻塞异常 |
| ERROR | 用例执行异常、报告生成失败、Playwright 调用失败、系统异常 |
| DEBUG | 候选元素评分、详细 DOM 摘要、调试信息，默认生产环境关闭 |

### 21.4 结构化日志示例

```json
{
  "level": "INFO",
  "traceId": "trace_202605120001",
  "taskId": "exec_202605120001",
  "caseRunId": "case_run_001",
  "stepRunId": "step_run_004",
  "event": "STEP_EXECUTION_FINISHED",
  "action": "click",
  "target": "提交订单按钮",
  "status": "passed",
  "durationMs": 843,
  "timestamp": "2026-05-12T16:24:12+08:00"
}
```

### 21.5 日志查询要求

后端需要提供按任务查询日志的接口：

```http
GET /api/v1/execution-tasks/{taskId}/logs
```

支持查询参数：

| 参数 | 说明 |
| --- | --- |
| `caseRunId` | 按用例过滤 |
| `stepRunId` | 按步骤过滤 |
| `level` | 按日志级别过滤 |
| `event` | 按事件类型过滤 |
| `from` / `to` | 按时间范围过滤 |

## 22. 产品模式

### 22.1 智能模式

适合人工测试辅助场景。

特点：

1. 尽量解析非标准 Markdown。
2. 低置信度时提示用户确认。
3. 允许调用方通过接口修正解析结果。
4. 定位自愈可在高置信度时自动执行。
5. 报告强调解释和证据。

### 22.2 严格模式

适合 CI/CD 自动执行场景。

特点：

1. 只执行结构完整、置信度高的用例。
2. 低置信度用例直接跳过或标记 invalid。
3. 定位候选低于阈值时不自动执行。
4. 报告强调机器可读和稳定性。
5. 支持非交互式运行。

## 23. 非功能需求

### 23.1 稳定性

1. 单条用例失败不能影响整个任务。
2. 支持失败重试。
3. 支持步骤超时控制。
4. 支持测试任务中断。
5. 支持失败证据保留。

### 23.2 安全性

1. 密码、Token、手机号等敏感数据需要脱敏展示。
2. 测试账号和密钥不能明文写入报告。
3. 支持测试环境域名白名单。
4. 禁止 Agent 操作未授权域名。
5. 登录态按任务隔离。

### 23.3 可追溯性

每次执行需要记录：

1. 用例原始文件。
2. 用例解析结果。
3. 用例解析版本。
4. Agent 版本。
5. 执行环境。
6. 浏览器版本。
7. 执行人或触发来源。
8. 执行时间。
9. 报告文件。
10. 证据文件。

### 23.4 性能目标

| 指标 | 项目目标 |
| --- | --- |
| Markdown 文件解析 | 100 条用例小于 30 秒 |
| 单用例启动浏览器 | 小于 10 秒 |
| 单步骤常规操作 | 小于 5 秒，特殊等待除外 |
| 报告生成 | 100 条用例小于 30 秒 |
| 失败证据采集成功率 | 大于等于 95% |

## 24. 落地功能清单

### 24.1 核心功能

1. Markdown 文件上传。
2. 多用例切分。
3. 用例名称、前置条件、测试步骤、预期结果解析。
4. 非标准模板兼容。
5. 解析置信度评分。
6. 解析结果结构化返回。
7. 调用方确认、修正、跳过。
8. Playwright 执行 Web UI 操作。
9. 基础动作支持：open、click、input、select、wait、scroll。
10. 基础断言支持：文本、元素、URL、输入值。
11. 元素多定位策略。
12. 元素定位失败重试。
13. 高置信度定位自愈。
14. 执行结果分类。
15. 截图、Console、Network、Trace 采集。
16. Allure 报告，整份 Markdown 用例文档执行完成后统一生成。

### 24.2 集成功能

1. JUnit XML 报告兼容。
2. 登录态复用。
3. 失败重试配置。
4. 测试数据配置中心。
5. 用例解析结果保存为结构化资产。
6. 命令行执行。
7. Java SDK 调用封装。
8. 任务日志查询接口。

### 24.3 后续增强功能

1. AI 视觉识别兜底。
2. App 自动化。
3. 接口和数据库联合断言。
4. 自动创建缺陷单。
5. 多浏览器并发执行。
6. 用例质量评分。
7. 历史失败趋势分析。
8. 自愈规则沉淀。
9. CI/CD 深度集成。
10. 测试资产管理平台。

## 25. 成功指标

| 指标 | 项目目标 |
| --- | --- |
| Markdown 用例解析成功率 | 大于等于 85% |
| 高置信度用例执行成功率 | 大于等于 90% |
| 失败证据完整率 | 大于等于 95% |
| 元素定位误报降低 | 大于等于 50% |
| 报告生成成功率 | 大于等于 99% |
| 用户人工回归耗时降低 | 大于等于 40% |

## 26. 风险与应对

| 风险 | 说明 | 应对策略 |
| --- | --- | --- |
| Markdown 模板差异过大 | 用户历史用例不统一 | 使用智能解析 + 结构化结果确认 |
| 自然语言步骤不清晰 | 步骤无法转成明确操作 | 标记 need_review，不强制执行 |
| 元素定位不稳定 | 页面改版导致找不到元素 | 多定位策略 + 自愈 + 报告分类 |
| 断言误判 | 预期结果描述模糊 | 使用确定性断言优先，LLM 仅辅助 |
| 环境数据不稳定 | 前置条件无法满足 | 前置条件状态化，阻塞时不判业务失败 |
| 报告不可信 | 只有结论没有证据 | 强制采集截图、日志、Trace |

## 27. 设计原则

1. 用例由用户负责，执行由 Agent 负责。
2. 不强迫用户一开始使用标准模板。
3. Agent 可以智能解析，但必须展示不确定性。
4. 定位失败不能直接等同于业务失败。
5. 断言必须可解释、可追踪、有证据。
6. Playwright 负责确定性执行，Agent 负责理解、规划、自愈和归因。
7. 本期按可落地后端项目建设，先保证接口、执行、日志、报告和证据链完整，再持续增强智能能力。

## 28. 参考产品与技术

以下产品和技术可作为能力设计参考：

1. Playwright：Web 自动化执行、断言、截图、Trace、报告。
2. Playwright MCP：Agent 调用浏览器、观察页面、执行操作的参考方式。
3. mabl：AI 测试自动化、自愈、报告能力参考。
4. Testim：AI 驱动 UI 测试、元素稳定性和报告能力参考。
5. Allure Report：测试报告展示和结果归档参考。

## 29. 总结

本产品应被设计成一个面向已有测试用例的执行型 Agent，而不是用例生成工具。

核心闭环是：

```text
用户提供 Markdown 用例
  ↓
Agent 解析并通过接口返回结构化结果
  ↓
调用方确认或修正
  ↓
Agent 调用 Playwright 执行
  ↓
Agent 根据预期断言
  ↓
Agent 对失败归因
  ↓
整份用例文档执行完成后统一生成 Allure 报告
```

本项目不建设前端页面，重点是交付一个可被外部系统稳定调用的 Spring Boot 后端服务。只要系统能稳定解析 Markdown 用例、可靠执行 UI 操作、完整输出关键日志、正确区分业务失败和自动化执行失败，并在整份文档执行完成后生成证据完整的 Allure 报告，就具备真实落地价值。
