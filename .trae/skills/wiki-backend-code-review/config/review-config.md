# Review Configuration — wiki-backend-code-review

> 评审参数集中管理。规则文件本身不硬编码任何具体目录名、阈值或事件名，
> 一切可配置项都从本文件读取，便于项目演进时单点维护。

## 技术栈

- Runtime: Node.js (LTS)
- Framework: Fastify 4.x
- Language: TypeScript (target ES2022, module ESNext / ESM)
- 模块系统: ESM（`"type": "module"`，import/export，禁止 require）
- 异步模型: async/await + Node Streams + AsyncIterable

## 项目目录映射

| 逻辑角色 | 目录约定（相对项目根） | 说明 |
|---------|----------------------|------|
| HTTP 路由层 | `api/src/routes/` | Fastify 路由注册，参数解析 + 响应格式化 |
| 工作流编排 | `api/src/workflows/` | 调用 engine adapter，串接 hook 与预算控制 |
| 引擎适配器 | `api/src/engine/` | `EngineAdapter` 接口实现，封装外部引擎调用 |
| Vault 文件系统 | `api/src/vault/` | 对 Obsidian Vault 的读写、追加、状态持久化 |
| Prompt 存储 | `prompts/` | prompt 模板单点存放，禁止内联到 .ts 代码 |
| 状态持久化 | `api/src/state/` | `FileStateStore` 实现，runId 唯一索引 |
| 共享工具 | `api/src/utils/` | 通用 helper（路径校验、临时文件等） |

> 评审时若发现实际路径与上述映射不符，以实际路径为准并在报告中标注差异，
> 不要因路径偏差而跳过规则匹配。

## SSE 事件格式约定

- 事件分隔符：`\n\n`（两个换行）
- 单事件行格式：
  ```
  event: <type>\n
  data: <json-string>\n
  \n
  ```
- 必备事件类型（可扩展，但以下为契约下限）：
  - `progress`：进度/心跳事件
  - `result`：单条结果产出
  - `error`：错误推送（不通过抛异常断连）
  - `done`：正常结束事件
- JSON payload 必须是单行序列化结果（`JSON.stringify`，禁止多行美化后写入）。

## 并发控制阈值

| 场景 | 阈值/策略 | 说明 |
|------|----------|------|
| index.md / log.md 追加 | 串行化（`withCompileLock`） | 防止并发追加交错导致索引损坏 |
| 单进程内 SSE 连接 | 不限硬上限，但须 finally 收尾 | 避免连接泄漏 |
| 引擎调用预算 | 由 `EngineAdapter` 配置项注入 | 耗尽时返回 `budget_exceeded`，不抛异常 |
| 文件锁等待超时 | 由 `FileStateStore` 配置项注入 | 超时后降级，不阻塞事件循环 |

> 具体数值由项目运行时配置注入，评审规则只校验"是否使用对应机制"，
> 不校验具体阈值大小。

## 路径遍历防护规则

- 用户可控输入（如 `runId`、文件名、路径段）必须正则白名单校验后才能拼接到文件系统路径。
- 推荐白名单正则（UUID 形式）：`/^[a-fA-F0-9-]{36}$/`
- 文件名白名单（仅允许字母/数字/下划线/短横线/点）：`/^[A-Za-z0-9._-]+$/`
- 禁止模式：
  - 含 `..` 的相对路径
  - 绝对路径（`/` 或盘符 `C:` 开头）
  - 含 null byte 或换行符的输入
- 拼接后的最终路径必须用 `path.resolve` 解析后，校验仍落在允许的根目录内（`startsWith` 检查）。

## Vault 写入白名单

- AI 工具仅可写入：指定工作目录、`index.md`、`log.md`、`drafts/`、`attachments/`。
- 禁止修改：`SCHEMA.md`（结构契约文件，只能由人工维护）。
- 禁止删除：已归档的内容目录（防止 AI 误删历史）。
- 部分失败策略：不回滚已写入内容，标记 `draft` 状态保留半成品，由人工或后续流程收尾。

## 临时文件策略

- 临时文件必须使用 `os.tmpdir()` 作为根目录。
- 文件名必须带唯一前缀（如 `runId + '-' + Date.now()`），避免并发冲突。
- 临时文件使用完毕后必须 `fs.promises.unlink` 清理（在 finally 中）。

## 配置项管理规范

### 原则：所有可配置参数必须通过 config 注入，禁止硬编码

与前端"所有颜色必须用 CSS 变量"同理，后端的所有可配置参数必须通过配置注入，禁止在代码中硬编码。

### 必须配置化的参数清单

| 参数类别 | 示例 | 注入方式 |
|----------|------|----------|
| API Key / 密钥 | `OPENAI_API_KEY` | 环境变量，config 存变量名（`apiKeyRef`） |
| 端口 / 监听地址 | `port: 3000`, `host: '127.0.0.1'` | config 文件注入 |
| 超时 / 预算阈值 | token 预算、文件锁超时 | config 文件注入 |
| 文件路径 | vaultRoot、stateDir、promptsDir | config 文件注入 |
| 并发控制 | `withCompileLock` 锁 Map | 运行时注入，不硬编码锁 key |
| SSE 事件类型 | `progress` / `result` / `error` / `done` | 本文件"SSE 事件格式约定"定义 |
| 白名单 | 允许的命令、可写目录 | config 文件注入 |

### 检测方式

在代码中搜索以下模式，确认是否通过 config 引用而非直接硬编码：
- `process.env.` — 确认密钥从环境变量读取，而非字面量
- `app.listen(` — 确认 port/host 从 config 读取
- `path.join(` — 确认路径从 config 读取，而非硬编码字符串
- `new Set([` — 确认白名单从 config 读取，而非内联数组

### 与前端主题色规范的对应关系

| 前端 | 后端 |
|------|------|
| 硬编码 `rgba(R,G,B,A)` 禁止 | 硬编码 API Key / port / path 禁止 |
| 用 `var(--css-variable)` 引用 | 用 `config.xxx` / `process.env[config.xxxRef]` 引用 |
| CSS 变量分层（L1/L2/L3） | 配置分层（env → config → runtime） |
| 主题文件覆盖全部变量 | 环境配置覆盖全部参数 |

## 配置管理审查参数

> 配置类路由（reset/restore/保存/测试连接）的审查参数集中在本节。
> 规则文件 [references/config-management-rule.md](../references/config-management-rule.md) 不硬编码具体路径或实例名，
> 一切约定从本节读取，便于项目演进时单点维护。

### 配置恢复接口路径模板

| 模块 | 恢复接口路径 | 说明 |
|------|------------|------|
| LLM / AI | `POST /api/ai/reset-config` | 重置 LLM provider/baseUrl/model/apiKey 到默认值 |
| 通用模板 | `POST /api/{module}/reset-config` | 新增可编辑配置模块时按此模板命名 |

- 恢复接口须与该模块的 `GET /api/{module}/config`、`PUT /api/{module}/config` 同处一个路由文件注册。
- 路径中 `{module}` 为配置模块标识（如 `ai`、`engine`、`vault`），与配置文件中的顶层字段一一对应。

### 配置恢复须同步的运行时实例列表

| 模块 | 须同步的运行时实例 | 同步方法 | 同步字段 |
|------|------------------|----------|----------|
| LLM / AI | `adapter`（EngineAdapter 实例） | `adapter.updateConfig()` | `provider` / `baseUrl` / `model` / `apiKey` |

- 评审时确认：reset 接口写完配置文件后，必须调用上表对应的同步方法，否则视为不通过。
- 新增可编辑配置模块时，若引入新的运行时实例，必须在本表登记其同步方法与字段。

### 配置接口完整生命周期清单

| 动作 | 方法 + 路径模板 | 说明 |
|------|----------------|------|
| 读取 | `GET /api/{module}/config` | 返回当前配置 |
| 保存 | `PUT /api/{module}/config` | 持久化新配置并同步运行时 |
| 恢复 | `POST /api/{module}/reset-config` | 重置目标模块字段到默认值并同步运行时 |
| 测试 | `POST /api/{module}/test-connection` | 用当前配置发起一次连通性测试 |

- 评审时确认：可编辑配置模块的路由文件须同时注册以上四类接口，缺失任一即视为生命周期不完整（suggestion 级）。
- "测试连接"接口允许按模块语义调整（如非网络型模块可改为"校验配置"），但必须有等价的验证动作。

### 预设集中管理位置约定

| 预设类别 | 集中定义位置 | 导出常量名 | 说明 |
|----------|------------|-----------|------|
| LLM 预设 | `api/src/routes/ai.ts` | `LLM_PRESETS` | provider/model 预设列表，供路由与前端共享 |

- 评审时确认：预设列表必须从单一常量导出，禁止在多个路由文件内联重复定义。
- 新增预设类别时，必须在本表登记其集中定义位置与常量名，保持单点维护。

### 预设 ID 列表

预设 ID 必须与后端 `AI_PRESET_BASE_URLS` 字典的键名保持一致。新增预设时，此处必须同步更新。

- openai
- deepseek
- zhipu
- moonshot
- qwen
- ernie
- doubao
- agnes
- ollama

### 密钥存储命名规范

- 全局密钥: `openai_api_key` (LLM), `embedding_api_key` (Embedding)
- 预设独立密钥: `openai_api_key_preset_{preset_id}`
- 脱敏值前缀: `****`（4 个星号）

### 热更新安全要求

- 配置更新必须原子化：先读旧值，再写新值，失败时回滚。
- 更新后必须验证新配置可加载（不崩溃、不报错）。
- 更新日志必须记录 before/after 快照。

## Session State & Cache Management

### 跨进程状态传播

- 子进程写入共享文件后，父进程必须调用 `invalidate_cache()` 再读取。
- 子进程写入后必须通知父进程更新运行中的服务状态。

### 缓存失效策略

- JSON 文件读取前必须调用 `invalidate_cache()`。
- 健康检查端点（`/health`、`/cookies/layers`、`/me`）必须清缓存。
- 缓存 TTL 由配置项管理，默认 30 秒。

### Cookie 层状态同步

- `export_cookies()` 成功后必须调用 `sync_cookie_layers_from_json()`。
- 运行时 Cookie 变更必须推送到 worker 浏览器上下文。
- 身份 Cookie 变更时必须强制刷新 token。

### 会话状态检查三要素

- 缺失检查：必需 Cookie 名称是否存在。
- 过期检查：Cookie expires 是否已过期。
- 陈旧检查：Cookie 值是否与持久化存储中的最新值一致。

## 持久化与缓存刷新审查参数

> 持久化与缓存刷新规则（见 [references/persistence-cache-rule.md](../references/persistence-cache-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体路径、变量名或正则。

### 配置文件路径解析锚点

| 场景 | 解析方式 | 说明 |
|------|---------|------|
| 开发模式（ESM 源码运行） | `path.dirname(fileURLToPath(import.meta.url))` | 与当前源文件位置绑定，不受 CWD 影响 |
| 打包模式（如 pkg） | `path.resolve(process.cwd(), CONFIG_FILENAME)` | 打包后无源文件路径，退回 CWD |
| 通用兜底 | 候选路径数组 + `fsSync.accessSync` 探测 | 按优先级返回首个存在路径，全部缺失时返回开发模式锚点 |

- 禁止模式：使用 `process.cwd()` 作为唯一路径锚点（CWD 受启动方式影响，开发/打包/工具链切换会漂移）。
- 评审时确认：`getConfigPath()` / `getStateDir()` 等路径解析函数必须实现"优先 `import.meta.url` + 打包兜底 + CWD 探测"三级策略。

### 缓存刷新要求

| 写盘函数 | 必须调用的刷新方法 | 刷新内容 |
|---------|------------------|---------|
| `saveAiConfig()` | `refreshConfigCache(data)` | 同步更新 `configCache.data` / `.path` / `.loadedAt` |
| `resetAiConfig()` | `refreshConfigCache(data)` | 同上 |
| `saveWebSearchConfig()` | `refreshConfigCache(data)` | 同上 |
| 通用模板（新增可编辑模块） | `refresh<Module>Cache(data)` | 写盘后立即同步内存缓存 |

- 评审时确认：所有写盘函数必须在 `await fs.writeFile(...)` 成功后、`return reply` 之前调用对应的缓存刷新方法。
- 缓存 TTL 不替代显式刷新：即使 TTL 很短（如 30s），写盘后仍必须立即刷新，避免窗口期内 GET 返回旧值。
- 失败处理：`fs.writeFile` 抛错时不得刷新缓存（保持旧值供降级读取），并须向客户端返回 5xx。

### UUID 白名单正则

| 用途 | 正则 | 说明 |
|------|------|------|
| 资源 ID 参数校验（会话/任务/runId） | `/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i` | 标准 UUID v4 格式，大小写不敏感 |
| 文件名段校验 | `/^[A-Za-z0-9._-]+$/` | 仅字母/数字/下划线/短横线/点 |
| 通用路径段校验 | `/^[A-Za-z0-9_][A-Za-z0-9._-]*$/` | 禁止以 `.` 开头，防 `.`/`..` 穿越 |

- 评审时确认：所有来自 HTTP 请求参数（`request.params.id`、`request.body.filename` 等）用作文件名/路径段时，必须先用上表正则校验。
- 正则本身视为配置项：项目可扩展上表，但禁止在代码内联硬编码正则字面量。

### 落盘目录约定

| 数据类型 | 落盘目录（相对项目根） | 文件命名 | 格式 |
|---------|--------------------|---------|------|
| AI 配置 | `api/config.json` | 固定文件名 | JSON |
| 历史会话 | `data/conversations/` | `{uuid}.json` | JSON（单文件单会话） |
| 运行状态 | `api/src/state/` | `runId` 索引 | 由 `FileStateStore` 定义 |
| 临时文件 | `os.tmpdir()` | `{runId}-{timestamp}` | 任意 |

- 落盘目录必须通过配置项或 `import.meta.url` 解析，禁止硬编码绝对路径。
- `.gitignore` 必须排除运行期写入目录（`data/conversations/`、`test_screenshots/` 等），防止敏感数据误提交。
- 评审时确认：新建落盘目录时，须同步在 `.gitignore` 登记排除规则，并在本表登记目录约定。

### 跨 origin 持久化边界

| 数据类型 | 浏览器存储（缓存层） | 后端权威源 | 跨 origin 共享 |
|---------|---------------------|-----------|---------------|
| AI 配置（apiKey） | localStorage（仅脱敏值） | `/api/ai/config` + `api/config.json` | 是 |
| 历史会话 | IndexedDB（降级缓存） | `/api/conversations/:id` + `data/conversations/` | 是 |
| LLM 预设 UI 状态 | localStorage（baseUrl/model） | 无（前端独立） | 否 |
| 主题偏好 | localStorage | 无（前端独立） | 否 |

- 评审时确认：跨 origin 列为"是"的数据，后端必须提供 CRUD 路由，前端以后端为权威源、浏览器存储仅作降级缓存。
- 降级策略：后端不可用时前端降级到本地缓存，但须 `console.warn` 记录降级事件，不得静默失败。

## 编码安全审查参数

> 编码安全规则（见 [references/encoding-safety-rule.md](../references/encoding-safety-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体编码值、检测方法或扫描范围。

| 参数 | 值 | 说明 |
|------|-----|------|
| `source_encoding_required` | `utf-8-no-bom` | 源文件要求编码 |
| `config_encoding_required` | `utf-8-no-bom` | 配置文件要求编码 |
| `encoding_detection` | `utf8-strict-decode` | 检测方法 |
| `encoding_scan_scope` | `.ts,.json,.md` | 扫描文件扩展名 |
| `fffd_indicator` | `U+FFFD` | 乱码指示字符 |
| `ascii_whitelist` | `true` | 纯 ASCII 文件免检 |

- 评审时确认：被改动文件（`.ts` / `.json` / `.md`）须符合 `source_encoding_required` / `config_encoding_required`，BOM 或非 UTF-8 字节会触发 `tsc` 编译失败或运行时乱码。
- 检测时机：Edit 后、`tsc` 编译前。PowerShell 编辑含中文注释的文件时必须保持原编码，禁止以默认编码回写。

## 清理操作审计参数

> 清理操作审计规则（见 [references/cleanup-audit-rule.md](../references/cleanup-audit-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体审计路径、下限值或默认值。

| 参数 | 值 | 说明 |
|------|-----|------|
| `audit_log_format` | `jsonl` | 审计日志格式 |
| `audit_log_path` | `.harness/cleanup-audit.log` | 审计日志路径（相对项目根） |
| `audit_failure_action` | `non-blocking` | 审计失败不阻塞主流程 |
| `days_min_value` | `1` | days 参数下限 |
| `days_protection` | `Math.max(min, input)` | days 下限保护公式 |
| `dry_run_default` | `true` | dry_run 默认值 |
| `single_item_error_collection` | `errors[]` | 单子项错误收集到数组 |
| `refresh_after_execute` | `true` | 实际执行后刷新状态 |

- 评审时确认：清理类路由（删除、归档、回收）必须按本表配置实现审计日志、days 下限保护、`dry_run` 默认值与执行后状态刷新。
- 审计日志写入失败必须按 `audit_failure_action` 降级，不得阻塞主清理流程。

## 批量操作错误处理参数

> 批量操作错误处理规则（见 [references/error-handling-rule.md](../references/error-handling-rule.md) 的"批量操作单子项错误处理"节）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体字段名或捕获策略。

| 参数 | 值 | 说明 |
|------|-----|------|
| `single_item_try_catch` | `true` | 单子项独立 try-catch |
| `error_collection_field` | `errors` | 错误收集字段名 |
| `main_flow_catch` | `fatal-only` | 主流程只捕获致命错误 |
| `audit_write_catch` | `independent` | 审计写入独立 try-catch |

- 评审时确认：批量操作（清理、迁移、批处理）中单子项失败不中断整体流程，错误信息收集到 `error_collection_field` 数组返回给客户端。
- 主流程 try-catch 只捕获致命错误（如配置缺失、权限拒绝），单子项错误用独立 try-catch 包裹。

## 后端路由注册守卫参数

> 后端路由注册守卫规则（见 [references/route-registration-backend-rule.md](../references/route-registration-backend-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体路径、入口文件名或注册函数名。

| 参数 | 值 | 说明 |
|------|-----|------|
| `route_directory` | `api/src/routes/` | 路由文件目录（相对项目根） |
| `entry_file` | `api/src/index.ts` | 入口文件路径（相对项目根），路由须在此导入与注册 |
| `register_function_pattern` | `register` | 注册函数名匹配模式（正则字面量），用于在入口文件中检索已注册路由 |
| `exempt_files` | `["_types.ts", "_shared.ts", "index.ts"]` | 豁免文件列表（不需注册的辅助文件，如类型定义、共享工具） |

- 评审时确认：`route_directory` 下所有非豁免路由文件均须在 `entry_file` 中被 `import` 并调用注册函数（匹配 `register_function_pattern`）。
- 新增路由文件时，须同步在 `entry_file` 添加导入与注册调用，否则视为不通过。
- 豁免文件须以 `_` 开头或显式登记在 `exempt_files` 中，便于评审时识别"辅助文件 vs 遗漏注册"。

## 空值守卫参数

> 空值守卫规则（见 [references/null-guard-rule.md](../references/null-guard-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体字段名或异步赋值关键词。

| 参数 | 值 | 说明 |
|------|-----|------|
| `nullable_field_patterns` | `this\.provider\|this\.child\|this\.connection\|this\.client\|this\.handle` | 可空字段名匹配模式（正则），匹配的字段须在使用前空值守卫 |
| `async_assignment_keywords` | `spawn\|exec\|connect\|listen\|createClient\|open` | 异步赋值关键词（正则），同文件出现时认定字段为"外部异步赋值" |

- 评审时确认：匹配 `nullable_field_patterns` 的字段若同文件内出现 `async_assignment_keywords` 的赋值语句，使用前必须有 `if (!x)` 守卫。
- 守卫分支必须包含可观察的恢复动作（重建资源 / 抛友好错误 / 日志降级），不能仅 `return` 静默吞错。
- 字段类型必须显式标注为 `T | null`，让 TS 编译器协助检查（TS2531 / TS18047）。

## 优雅停止参数

> 优雅停止规则（见 [references/graceful-shutdown-rule.md](../references/graceful-shutdown-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体资源类型、信号名或清理顺序。

| 参数 | 值 | 说明 |
|------|-----|------|
| `resource_keywords` | `spawn\|setInterval\|connect\|listen\|createClient\|open` | 资源创建关键词（正则），文件内出现时认定需注册清理钩子 |
| `shutdown_signals` | `["SIGINT", "SIGTERM"]` | 触发清理的信号列表，进程收到这些信号时按 `cleanup_order` 释放资源 |
| `cleanup_order` | `["child_process", "timer", "connection"]` | 清理顺序：子进程优先（避免孤儿），再清定时器（避免退出前触发），最后关连接 |

- 评审时确认：创建子进程 / 定时器 / 长连接的模块均须在 `shutdown_signals` 上注册清理钩子。
- 清理函数须按 `cleanup_order` 顺序释放资源，单个资源清理失败不阻塞其他资源释放。
- 清理函数末尾须调用 `process.exit(0)`，避免进程因未关闭句柄挂起。

## 敏感字段脱敏参数

> 敏感字段脱敏规则（见 [references/sensitive-field-masking-rule.md](../references/sensitive-field-masking-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体字段名、脱敏算法或空串语义。

| 参数 | 值 | 说明 |
|------|-----|------|
| `sensitive_field_patterns` | `key\|token\|secret\|password\|authtoken\|apiKey\|apiSecret` | 敏感字段名匹配模式（正则），命中的字段在 GET 返回时必须脱敏 |
| `mask_strategy` | `last4_padstart` | 脱敏策略：保留末 4 位，前缀用 `****` 填充 |
| `empty_string_semantics` | `no_change` | POST/PUT 接收空串的语义：不修改原值（避免覆盖原密钥） |

- 评审时确认：GET handler 返回对象中匹配 `sensitive_field_patterns` 的字段必须经过 `mask()` 处理，并附带 `<field>_configured: boolean` 标志。
- POST/PUT handler 中敏感字段为空串时按 `empty_string_semantics` 跳过更新，不覆盖原值。
- 即使 `configured: false`，GET 返回也不应暴露原始值，统一返回空串或 `null` + 标志。

## 类型同步守卫参数

> 类型同步守卫规则（见 [references/type-sync-backend-rule.md](../references/type-sync-backend-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体文件路径或需同步的接口名列表。

| 参数 | 值 | 说明 |
|------|-----|------|
| `backend_types_path` | `api/src/types.ts` | 后端 types 文件路径（相对项目根） |
| `frontend_types_path` | `frontend/src/types.ts` | 前端 types 文件路径（相对项目根） |
| `sync_interfaces` | `[]` | 需同步的接口名列表（留空则校验全部 `export interface`） |

- 评审时确认：`backend_types_path` 的 `export interface`（或 `sync_interfaces` 列表中的接口）须在 `frontend_types_path` 中存在，且字段名、类型签名、可选性一致。
- 若 monorepo 前端直接 `import type` 引用后端类型（单源定义），可豁免本规则——评审时确认引用路径正确。
- 后端新增字段时，前端在 PR 中同步修改，无遗漏。

## 配置合并保留参数

> 配置合并保留规则（见 [references/config-merge-preservation-rule.md](../references/config-merge-preservation-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体配置文件路径、合并策略或保留段名列表。

| 参数 | 值 | 说明 |
|------|-----|------|
| `config_file_path` | `api/config.json` | 分段配置文件路径（相对项目根） |
| `merge_strategy` | `shallow` | 合并策略：`shallow` 用对象展开覆盖目标段，`deep` 用递归合并 |
| `preserve_sections` | `[]` | 须保留的段名列表（留空则全部保留，仅目标段被覆盖） |
| `exempt_paths` | `["*.tmp.json", "*.cache.json"]` | 豁免文件路径模式（临时/缓存文件不校验合并保留） |

- 评审时确认：写盘函数（`fs.writeFile` / `fs.promises.writeFile`）针对 `config_file_path` 时，必须先读原文件再按 `merge_strategy` 合并，仅覆盖目标段。
- `preserve_sections` 列表中的段在写入对象中必须存在且值与原文件一致。
- 多模块共享同一配置文件时，统一调用 `mergeConfigSection(target, section)` 工具，避免各模块各自实现合并逻辑。

## 检查更新后端审查参数

> 检查更新后端规则（见 [references/update-check-backend-rule.md](../references/update-check-backend-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体缓存 TTL、超时值或 GitHub API URL。

| 参数 | 值 | 说明 |
|------|-----|------|
| `check_update.cache_ttl_ms` | `300000` | 后端内存缓存 TTL（毫秒），默认 5 分钟；TTL 内的请求直接返回缓存值，不发起外部 API 调用 |
| `check_update.offline_mode` | `true` | 离线模式开关；`true` 时固定返回 `has_update: false, source: 'local'`，禁止发起外部 API 调用 |
| `check_update.update_endpoint` | `/api/about/check-update` | 后端检查更新接口路径 |
| `check_update.external_api_timeout_ms` | `10000` | 外部 GitHub API 调用超时（毫秒），默认 10 秒；超时后降级返回 `source: 'local'` |
| `check_update.github_api_url_template` | `https://api.github.com/repos/{owner}/{repo}/releases/latest` | GitHub Releases API URL 模板，`{owner}` / `{repo}` 占位符运行时替换 |
| `check_update.required_response_fields` | `has_update, current_version, latest_version, release_url, source, checked_at` | 必需响应字段列表（逗号分隔）；任一缺失会导致前端状态机无法正确切换 |
| `check_update.fallback_source` | `local` | 降级时 `source` 字段值（区分真实检查 vs 降级结果） |
| `check_update.cache_invalidation_on_error` | `false` | 外部 API 失败时是否刷新缓存；`false` 保持旧值供下次降级读取 |

- 评审时确认：`/api/about/check-update` 接口实现模块级内存缓存，TTL 命中时直接返回缓存值，不发起外部请求。
- 离线模式 `offline_mode: true` 时接口固定返回 `{ has_update: false, source: 'local' }`，禁止任何 `fetch` / `axios` 调用。
- 外部 API 调用必须用 `AbortController` 实现超时控制，超时或失败时降级返回 `source: 'local'`，不抛 5xx。
- `current_version` 必须从 `package.json` 的 `version` 字段读取，禁止硬编码版本号字面量。

## SPA 静态资源托管审查参数

> SPA 静态资源托管规则（见 [references/spa-static-hosting-rule.md](../references/spa-static-hosting-rule.md)）所依赖的可配置参数集中在本节管理，规则文件只描述通用模式。

| 参数 | 值 | 说明 |
|------|-----|------|
| `spa_static_hosting.enabled` | `true` | 是否启用 SPA 静态资源托管审查 |
| `spa_static_hosting.severity` | `error` | 违规严重级别 |
| `spa_static_hosting.required_candidate_paths` | `2` | 多候选路径探测的最少路径数量 |
| `spa_static_hosting.candidate_path_templates` | `cwd/public, dirname/../public, dirname/../static/spa` | 候选路径模板（逗号分隔） |
| `spa_static_hosting.build_output_dir` | `api/public` | 构建产物输出目录（相对项目根） |
| `spa_static_hosting.empty_out_dir_required` | `true` | 是否必须配置 emptyOutDir |
| `spa_static_hosting.spa_fallback_required` | `true` | 是否必须实现 SPA fallback |
| `spa_static_hosting.fallback_file` | `index.html` | SPA fallback 返回的文件名 |
| `spa_static_hosting.api_path_exclusion` | `/api/, /assets/` | 不触发 SPA fallback 的路径前缀（逗号分隔） |
| `spa_static_hosting.watch_reload_required` | `true` | watch 模式重新构建后是否必须重启后端 |
| `spa_static_hosting.health_check_endpoint` | `/api/ai/config` | 重启后验证的健康检查端点 |

> 适用场景：单端口部署（前端构建产物输出到后端 public 目录）+ Vite/webpack 构建 + Fastify/Express 后端的 SPA 项目。多端口部署、SSR 应用、Next.js/Nuxt.js 框架项目不适用。

## 严重级别定义

| 参数 | 值 | 说明 |
|------|-----|------|
| `severity_critical` | `🔴 严重` | 必须修复，阻止合并 |
| `severity_warning` | `🟡 警告` | 建议修复，不阻止合并 |
| `severity_suggestion` | `🟢 建议` | 可选优化 |
| `severity_positive` | `✅ 优点` | 正面反馈 |

## 配置一致性审查参数

> 供 config-consistency-rule.md 引用，禁止在规则文件中硬编码。

| 参数 | 值 | 说明 |
|------|-----|------|
| `config_read_entries` | `startup,hot_reload,api_get,api_test` | 配置读取入口清单 |
| `required_unified_functions` | `getEffectiveApiKey,loadConfig` | 必须统一调用的函数 |
| `forbidden_direct_read` | `process.env[config.llm` | 禁止直接读取（应用统一函数） |

## 热更新闭环审查参数

> 供 hot-update-rule.md 引用，禁止在规则文件中硬编码。

| 参数 | 值 | 说明 |
|------|-----|------|
| `hot_update_required` | `true` | 可热更新字段必须实现 updateConfig |
| `hot_update_chain` | `save→persist→updateConfig→response` | 热更新闭环流程 |
| `hot_update_methods` | `updateConfig` | 热更新方法名 |
| `hot_update_call_required` | `true` | 路由层必须调用 updateConfig |

## 架构审查参数

> 供 architecture-rule.md 引用，禁止在规则文件中硬编码。

| 参数 | 值 | 说明 |
|------|-----|------|
| `layer_order` | `routes→workflows→engine→vault` | 分层顺序 |
| `cross_layer_call_forbidden` | `routes→vault` | 禁止跨层调用 |
| `dependency_direction` | `outer→inner` | 依赖方向 |

## 输出格式参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `max_issues_per_section` | `10` | 每个级别最多输出条数 |
| `include_code_snippet` | `true` | 是否包含代码片段 |
| `include_rule_reference` | `true` | 是否引用规范依据 |
| `suggest_fix_code` | `true` | 是否提供修复代码示例 |

## ESM 与模块接线审查参数

> 供 esm-and-wiring-rule.md 引用，禁止在规则文件中硬编码。

| 参数 | 值 | 说明 |
|------|-----|------|
| `esm_forbidden_globals` | `__dirname,__filename` | ESM 模式下禁用的全局变量 |
| `esm_dirname_derive_pattern` | `path.dirname(fileURLToPath(import.meta.url))` | dirname 派生正确模式 |
| `esm_required_imports` | `path,fileURLToPath` | ESM 派生路径必需的 import |
| `wiring_required_steps` | `import,instantiate,registerRoute` | 模块接线必需的三步骤 |
| `wiring_entry_file` | `api/src/index.ts` | 模块接线的入口文件 |
| `route_register_pattern` | `registerXxxRoute(app, ...)` | 路由注册函数命名模式 |
| `static_analysis_tools` | `SonarQube,ESLint` | 需人工验证的静态分析工具 |
| `static_analysis_verify_checklist` | `operand_throws_on_reference,type_guard_bypassed,side_effect_changed` | 静态分析建议验证清单 |
| `endpoint_reachability_check` | `curl /api/<module>/<action>` | 端点可达性验证命令 |

## Async 可靠性审查参数

> 供 async-reliability-rule.md 引用，禁止在规则文件硬编码。

| 参数 | 值 | 说明 |
|------|-----|------|
| `async_default_call_timeout_sec` | `5.0` | 单次 async 调用默认超时（秒） |
| `async_stage_hard_timeout_sec` | `30.0` | 阶段硬超时（秒） |
| `async_task_total_timeout_sec` | `180.0` | 任务整体超时（秒） |
| `async_heartbeat_interval_sec` | `3.0` | 心跳线程更新间隔 |
| `async_heartbeat_max_interval_sec` | `10.0` | 业务循环内心跳最大间隔 |
| `async_thread_join_timeout_sec` | `5.0` | 线程 join 超时 |
| `async_status_file_update_strategy` | `thread` | 状态文件更新策略 |
| `async_fallback_data_pattern` | `best_holder` | 兜底数据传递模式 |
| `async_timeout_whitelist` | `asyncio.sleep,Promise.resolve` | 无需超时保护的调用白名单 |
| `async_blocking_risk_apis` | `playwright.context.cookies,playwright.context.storage_state,playwright.context.unroute,playwright.page.goto,playwright.page.wait_for_load_state,node_fetch,fs.promises.readFile,child_process.exec` | 可能阻塞事件循环的 API |
| `async_heartbeat_impl_required` | `threading.Thread` | 心跳必须使用的实现方式 |
| `async_heartbeat_forbidden_impl` | `asyncio.Task,Promise.then` | 心跳禁止使用的实现方式 |

## 适用 / 不适用场景

### 适用

- 评审 `api/` 下的 Fastify 路由、workflow、engine adapter、vault 操作、state store。
- 评审 SSE 流式输出、文件系统并发追加、引擎预算控制等后端逻辑。
- 评审 TypeScript 后端代码的安全、错误处理、可维护性。
- 评审配置持久化、缓存刷新、跨 origin 存储边界、UUID 防路径穿越等持久化层逻辑。
- 评审"检查更新"接口的缓存、离线模式、外部 API 超时与降级。

### 不适用

- 前端代码（`.tsx` / `.jsx` / 浏览器侧 `.ts`）。
- 纯 prompt 文本（`prompts/` 下的 `.md` 内容质量评审，属另一技能职责）。
- Obsidian Vault 内容本身的语义正确性（本技能只评审"对 Vault 的操作是否安全"，不评审内容）。
- 构建配置、CI 脚本等非业务后端代码（除非涉及安全或路径校验）。

## API 响应类型同步审查参数（api_response_type_sync）

> 供 api-response-type-sync-rule.md（BR-026）引用，禁止在规则文件中硬编码。
> 适用场景：新增/修改 API 端点时校验后端响应形状与前端 types.ts 中 interface 同步。

| 参数 | 值 | 说明 |
|------|-----|------|
| `api_response_type_sync.enabled` | `true` | 是否启用本规则 |
| `api_response_type_sync.severity` | `critical` | 违规严重级别 |
| `api_response_type_sync.backend_routes_directory` | `api/src/routes/` | 后端路由文件目录（相对项目根） |
| `api_response_type_sync.frontend_types_path` | `frontend/src/types.ts` | 前端 types 文件路径（相对项目根） |
| `api_response_type_sync.backend_types_path` | `api/src/types.ts` | 后端 types 文件路径，用于提取共享 interface |
| `api_response_type_sync.reply_send_pattern` | `reply\.send\|return reply\.` | reply.send 调用匹配模式（正则字面量） |
| `api_response_type_sync.monorepo_import_type_exempt` | `true` | monorepo 前端直接 `import type` 引用后端类型时豁免本规则 |

- 评审时确认：`backend_routes_directory` 下所有 `reply.send(...)` 调用的对象形状须与 `frontend_types_path` 中对应 interface 字段名、类型签名、可选性一致。
- 后端新增响应字段时，前端 interface 必须在同一 PR 中同步新增。
- 若 monorepo 前端通过 `import type` 直接引用后端 types.ts，可将 `monorepo_import_type_exempt` 设为 `true` 豁免。
- 适配 Express：`reply_send_pattern` 改为 `res\.json\(|return res\.`；NestJS：改为 `return\s+\{` 或检查 DTO 与 `@ApiResponse` 装饰器；Koa：改为 `ctx\.body\s*=`。

## SSE 事件类型扩展路由审查参数（sse_event_type_route）

> 供 sse-event-type-route-rule.md（BR-027）引用，禁止在规则文件中硬编码。
> 适用场景：新增 SSE 事件类型时校验 config 列表同步与前端 handler 同步。

| 参数 | 值 | 说明 |
|------|-----|------|
| `sse_event_type_route.enabled` | `true` | 是否启用本规则 |
| `sse_event_type_route.severity` | `critical` | 违规严重级别 |
| `sse_event_type_route.sse_event_types_config_field` | `sse.event_types` | config 中事件类型列表的字段名 |
| `sse_event_type_route.required_event_types` | `progress,result,error,done` | 必备事件类型（契约下限，逗号分隔） |
| `sse_event_type_route.backend_sse_routes_directory` | `api/src/routes/` | 后端 SSE 路由所在目录 |
| `sse_event_type_route.event_pattern` | `event:\s*\w+` | SSE 事件类型字面量匹配模式（正则） |
| `sse_event_type_route.frontend_sse_consumer_path` | `frontend/src/lib/sse.ts` | 前端 SSE 消费函数文件路径 |
| `sse_event_type_route.unknown_event_strategy` | `warn` | 未知事件类型的默认处理策略（`warn` / `error` / `ignore`） |

- 评审时确认：后端 SSE 路由中所有 `event: <type>` 字面量须登记在 `sse_event_types_config_field` 字段对应列表中。
- 后端新增事件类型时，前端 `frontend_sse_consumer_path` 中必须同步新增对应 handler 分支。
- 未知事件类型的默认 handler 行为须符合 `unknown_event_strategy`（如 `warn` 时必须 `console.warn`，禁止静默 return）。
- 适配 Express：`event_pattern` 不变，helper 改为 `res.write`；NestJS：`event_pattern` 改为 `type:\s*['"]\w+['"]`；Koa：改为 `ctx.res.write`。

## 配置字段 optional 合并审查参数（optional_merge）

> 供 optional-merge-rule.md（BR-028）引用，禁止在规则文件中硬编码。
> 适用场景：配置合并函数中访问可选字段时禁止用 `!` 断言或 `as` 强转绕过类型检查。

| 参数 | 值 | 说明 |
|------|-----|------|
| `optional_merge.enabled` | `true` | 是否启用本规则 |
| `optional_merge.severity` | `suggestion` | 违规严重级别 |
| `optional_merge.config_merge_function_patterns` | `updateConfig,mergeConfig,mergeConfigSection,saveAiConfig,saveConfig` | 配置合并函数名匹配模式（逗号分隔，正则字面量） |
| `optional_merge.forbidden_assertion_operators` | `!,as` | 禁用的断言操作符（逗号分隔） |
| `optional_merge.recommended_operators` | `??,if guard,typeof guard` | 推荐的替代写法 |
| `optional_merge.scan_scope_glob` | `api/src/**/*.ts` | 扫描范围（glob 模式） |
| `optional_merge.allow_as_in_migration` | `false` | 迁移期代码是否允许 `as` 强转（临时豁免） |

- 评审时确认：`config_merge_function_patterns` 匹配的函数体内，访问可选字段（`T | undefined`）禁止用 `!` 后缀断言或 `as T` 强转。
- 必须用 `??` 默认值或 `if` 守卫显式处理 `undefined` 分支，避免 `undefined` 被序列化写入配置文件。
- 若使用 zod / joi schema 校验，校验后类型已收敛为必填，可在 `allow_as_in_migration` 设为 `true` 豁免校验后代码。
- 适配 Express / Koa：函数名匹配模式按项目实际调整；NestJS：改为 `src/config/**/*.ts`，匹配 `set,databaseOptions,mergeConfig`。

## EngineAdapter 接口变更实现同步审查参数（engine_adapter_sync）

> 供 engine-adapter-sync-rule.md（BR-029）引用，禁止在规则文件中硬编码。
> 适用场景：EngineAdapter 接口新增/修改方法时校验所有实现类同步更新。

| 参数 | 值 | 说明 |
|------|-----|------|
| `engine_adapter_sync.enabled` | `true` | 是否启用本规则 |
| `engine_adapter_sync.severity` | `critical` | 违规严重级别 |
| `engine_adapter_sync.engine_adapter_interface_path` | `api/src/engine/adapter.ts` | EngineAdapter 接口定义文件路径（相对项目根） |
| `engine_adapter_sync.adapter_implementations_directory` | `api/src/engine/` | 适配器实现类所在目录（相对项目根） |
| `engine_adapter_sync.forbidden_assertion_patterns` | `as unknown as,@ts-ignore,@ts-expect-error` | 禁用的绕过检查模式（逗号分隔） |
| `engine_adapter_sync.required_methods` | `` | 必备方法名列表（留空则校验接口声明的全部方法） |
| `engine_adapter_sync.optional_methods` | `beforeLoop,afterLoop` | 可选方法名列表（接口中声明为可选，调用方做存在性检查） |
| `engine_adapter_sync.allow_not_implemented_placeholder` | `false` | 是否允许 `throw new Error('not implemented')` 占位实现 |

- 评审时确认：`engine_adapter_interface_path` 中 `interface EngineAdapter` 声明的方法须在所有 `implements EngineAdapter` 的实现类中存在且签名一致。
- 禁止用 `as unknown as EngineAdapter` 断言、`@ts-ignore`、`@ts-expect-error` 绕过 implements 检查。
- 若方法对某些实现无意义，应在接口中声明为可选（`method?(...)`），由调用方做存在性检查，而非强制实现类提供空实现或 throw 占位。
- 适配 Express：路径按项目实际调整；NestJS：`adapter_implementations_directory` 改为 `src/engine/adapters/`，仍以 `implements` 子句为准；Strategy/Plugin 模式：`engine_adapter_interface_path` 指向实际接口文件，Grep 模式调整为 `implements <StrategyName>`。

## 项目目录结构审查参数（project_structure_review）

> BR-030~033 项目目录结构与文件组织审查的参数。所有参数可适配不同项目。
> 规则文件 [references/project-structure-review-rule.md](../references/project-structure-review-rule.md) 不硬编码具体目录名、命令或正则，一切约定从本节读取，便于项目演进时单点维护。

### 总开关

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `project_structure_review.enabled` | `true` | 是否启用本组规则（BR-030~033） |
| `project_structure_review.severity_br030` | `critical` | BR-030 目录结构分离违规严重级别 |
| `project_structure_review.severity_br031` | `critical` | BR-031 .gitignore 完整性违规严重级别 |
| `project_structure_review.severity_br032` | `suggestion` | BR-032 运行时数据外迁违规严重级别 |
| `project_structure_review.severity_br033` | `suggestion` | BR-033 file: 协议路径验证违规严重级别 |

### 目录结构分离审查参数（BR-030）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `project_structure_review.source_dirs` | `api/src/,frontend/src/,scripts/` | 源码目录列表（逗号分隔，相对项目根）；BR-030 检查这些目录下是否混放运行时数据 / 构建产物 / 外部工具链 |
| `project_structure_review.runtime_data_dir` | `data/` | 运行时数据统一存放目录（相对项目根）；源码目录内不得出现此目录 |
| `project_structure_review.build_output_dirs` | `dist/,build/` | 构建产物目录列表（逗号分隔）；源码目录内不得出现这些目录 |
| `project_structure_review.external_toolchain_dirs` | `w64devkit/` | 外部工具链目录列表（逗号分隔）；源码目录内不得出现这些目录，且应在 .gitignore 排除 |

- 评审时确认：`source_dirs` 中每个目录下不得存在匹配 `runtime_data_dir` / `build_output_dirs` / `external_toolchain_dirs` 的子目录或文件。
- 适配 Monorepo：`source_dirs` 调整为 `packages/*/src/,apps/*/src/`，`runtime_data_dir` 调整为 `packages/*/data/` 或统一 `data/`。
- 适配 Express / NestJS：`source_dirs` 改为 `src/`，其余参数按项目实际调整。

### .gitignore 完整性审查参数（BR-031）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `project_structure_review.runtime_data_ignore` | `data/,*.log` | 须在 .gitignore 登记的运行时数据规则（逗号分隔） |
| `project_structure_review.build_output_ignore` | `dist/,build/` | 须在 .gitignore 登记的构建产物规则（逗号分隔） |
| `project_structure_review.verification_command` | `git check-ignore -v <path>` | 验证 .gitignore 规则是否生效的命令；`<path>` 占位符运行时替换为目标路径 |
| `project_structure_review.tracked_check_command` | `git ls-files <path>` | 检查文件是否被 git 跟踪的命令；`<path>` 占位符运行时替换；返回非空表示需 `git rm --cached` |
| `project_structure_review.gitignore_file_path` | `.gitignore` | .gitignore 文件路径（相对项目根） |

- 评审时确认：`runtime_data_ignore` 与 `build_output_ignore` 中的规则须在 `gitignore_file_path` 中登记。
- 已跟踪文件须先执行 `git rm --cached <path>` 移除索引，仅添加 .gitignore 对已跟踪文件无效。
- 适配 Git LFS / 子模块：`tracked_check_command` 按项目实际调整；CI 环境可集成 pre-commit hook 自动校验。

### 运行时数据外迁审查参数（BR-032）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `project_structure_review.vaultpath_config_field` | `vaultPath` | 配置文件中 vaultPath 字段名；该字段值不得指向 `source_dirs` 任一目录 |
| `project_structure_review.config_files_to_check` | `api/config.json,config/default.json` | 须检查 vaultPath 的配置文件列表（逗号分隔，相对项目根） |
| `project_structure_review.runtime_data_patterns` | `data/` | 运行时数据应外迁到的目录模式（逗号分隔）；vaultPath 默认值须落在这些目录下 |

- 评审时确认：`config_files_to_check` 中每个配置文件的 `vaultpath_config_field` 字段值须落在 `runtime_data_patterns` 约定的目录下，不得落在 `source_dirs` 任一目录内。
- 路径解析须用 `path.resolve` 解析后 `startsWith` 检查，避免相对路径绕过。
- 适配 Express：`config_files_to_check` 改为 `config/default.json,.env`，`vaultpath_config_field` 按项目实际字段名调整（如 `dataDir`、`storagePath`）。
- 适配 NestJS：`config_files_to_check` 按项目配置文件实际路径调整（如 `src/config/` 下的配置类）。

### file: 协议路径验证审查参数（BR-033）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `project_structure_review.file_protocol_pattern` | `file:` | package.json 中本地路径引用的协议前缀；匹配此模式的依赖项须验证路径存在 |
| `project_structure_review.verify_command` | `npm ls <pkg>` | 验证 file: 引用路径有效性的命令；`<pkg>` 占位符运行时替换为依赖名 |
| `project_structure_review.package_json_files` | `package.json,api/package.json,frontend/package.json` | 须检查 file: 引用的 package.json 文件列表（逗号分隔，相对项目根） |

- 评审时确认：`package_json_files` 中每个 `package.json` 的 `dependencies` / `devDependencies` 中匹配 `file_protocol_pattern` 的引用须经过路径存在性验证。
- 验证方式：用 `verify_command` 或 `fs.existsSync(path.resolve(ref.slice(file_protocol_pattern.length)))` 检查路径是否存在。
- 适配 pnpm / yarn：`file_protocol_pattern` 改为 `link:` / `workspace:`（pnpm）或 `portal:`（yarn），`verify_command` 改为 `pnpm ls <pkg>` / `yarn why <pkg>`。
- 适配 Monorepo：`package_json_files` 调整为 `package.json,packages/*/package.json,apps/*/package.json`。
- 适配非 Node.js 项目：`file_protocol_pattern` 改为对应包管理器的本地路径引用格式（如 Python 的 `-e ./local-pkg`），`verify_command` 改为 `pip show <pkg>`。

## 配置化与持久化边界审查参数（config_persistence_boundary）

> BR-034~037 配置化参数与持久化边界审查的参数。所有参数可适配不同项目。
> 规则文件 [references/config-persistence-boundary-rule.md](../references/config-persistence-boundary-rule.md) 不硬编码具体参数名、路径或函数名，一切约定从本节读取。
> 复盘来源：前端硬编码 rgba() 颜色在浅色主题下辨识度低（CODING-041~046），后端同理存在硬编码 API Key/port/path/timeout 问题。

### 总开关

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_persistence_boundary.enabled` | `true` | 是否启用本组规则（BR-034~037） |
| `config_persistence_boundary.severity_br034` | `critical` | BR-034 配置化参数检测违规严重级别 |
| `config_persistence_boundary.severity_br035` | `critical` | BR-035 路径解析锚点合规性违规严重级别 |
| `config_persistence_boundary.severity_br036` | `critical` | BR-036 缓存刷新机制违规严重级别 |
| `config_persistence_boundary.severity_br037` | `suggestion` | BR-037 跨 origin 持久化边界违规严重级别 |

### 配置化参数检测审查参数（BR-034）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_persistence_boundary.configurable_param_patterns` | `apiKey, port, host, path, timeout, secret, token, password` | 必须配置化的参数名模式（逗号分隔，大小写不敏感） |
| `config_persistence_boundary.detection_patterns` | `process.env., app.listen(, path.join(, new Set([` | 硬编码检测模式（逗号分隔，用于 Grep 匹配） |
| `config_persistence_boundary.config_file_path` | `api/config.json` | 配置文件路径（相对项目根） |
| `config_persistence_boundary.env_var_ref_field` | `apiKeyRef` | config.json 中环境变量引用字段名（存储环境变量名而非值） |

- 评审时确认：`detection_patterns` 中每个模式命中的代码行，须检查参数是否从 `config_file_path` 或 `process.env[config[env_var_ref_field]]` 读取，而非字面量。
- 适配 Express：`app.listen(` 改为 `server.listen(`。
- 适配 NestJS：`app.listen(` 改为 `await app.listen(`。
- 适配 Python FastAPI：`detection_patterns` 改为 `os.environ., os.getenv(, Path(`。

### 路径解析锚点审查参数（BR-035）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_persistence_boundary.path_resolution_strategy` | `import.meta.url + process.cwd() fallback + CWD probe` | 路径解析三级策略描述 |
| `config_persistence_boundary.primary_anchor` | `import.meta.url` | ESM 项目路径解析首选锚点 |
| `config_persistence_boundary.packaged_fallback` | `process.cwd()` | 打包模式兜底锚点 |
| `config_persistence_boundary.forbidden_sole_anchor` | `process.cwd()` | 禁止作为唯一路径锚点的方法 |
| `config_persistence_boundary.path_resolution_functions` | `getConfigPath, getStateDir, getPromptsDir, getVaultRoot` | 须实现三级策略的路径解析函数名列表（逗号分隔） |

- 评审时确认：`path_resolution_functions` 中每个函数须实现"优先 `import.meta.url` + 打包兜底 + CWD 探测"三级策略，禁止 `forbidden_sole_anchor` 作为唯一锚点。
- 适配 CJS 项目：`primary_anchor` 改为 `__dirname`。
- 适配 Deno 项目：`primary_anchor` 改为 `import.meta.url`（Deno 原生支持）。

### 缓存刷新机制审查参数（BR-036）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_persistence_boundary.write_persistence_functions` | `saveAiConfig, resetAiConfig, saveWebSearchConfig, saveCleanupConfig` | 须调用缓存刷新的写盘函数名列表（逗号分隔） |
| `config_persistence_boundary.cache_refresh_method` | `refreshConfigCache(data)` | 缓存刷新方法名 |
| `config_persistence_boundary.cache_ttl_ms` | `30000` | 内存缓存默认 TTL（毫秒，30 秒） |
| `config_persistence_boundary.refresh_required_after_write` | `true` | 写盘后是否必须立即刷新缓存 |
| `config_persistence_boundary.refresh_failure_behavior` | `keep_old_value` | 写盘失败时的缓存行为（keep_old_value=保持旧值供降级读取） |

- 评审时确认：`write_persistence_functions` 中每个函数在 `await fs.writeFile(...)` 成功后、`return reply` 之前必须调用 `cache_refresh_method`。
- 缓存 TTL 不替代显式刷新：即使 TTL 很短（如 30s），写盘后仍必须立即刷新。
- 适配 Redis 缓存：`cache_refresh_method` 改为 `redisClient.del(key)` 或 `redisClient.set(key, value)`。
- 适配内存缓存：`cache_refresh_method` 改为 `cache.invalidate(key)` 或 `cache.set(key, value)`。

### 跨 origin 持久化边界审查参数（BR-037）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_persistence_boundary.cross_origin_data_types` | `ai_config, conversations` | 跨 origin 共享的数据类型列表（逗号分隔） |
| `config_persistence_boundary.backend_authoritative_source` | `config.json + data/conversations/` | 后端权威源路径 |
| `config_persistence_boundary.frontend_cache_layers` | `localStorage, IndexedDB` | 前端缓存层列表 |
| `config_persistence_boundary.localstorage_allowed_fields` | `baseUrl, model, theme, navCollapsed` | localStorage 允许存储的非敏感字段列表（逗号分隔） |
| `config_persistence_boundary.localstorage_forbidden_fields` | `apiKey, authtoken, password, secret` | localStorage 禁止存储的敏感字段列表（逗号分隔） |
| `config_persistence_boundary.degradation_log_required` | `true` | 降级时是否必须 console.warn 记录 |
| `config_persistence_boundary.crud_route_required` | `true` | 跨 origin 数据是否必须后端提供 CRUD 路由 |

- 评审时确认：`cross_origin_data_types` 中每种数据类型后端必须提供 CRUD 路由，前端以后端为权威源。
- `localstorage_forbidden_fields` 中的字段必须存储在 `backend_authoritative_source`，禁止存入 `frontend_cache_layers`。
- 适配 SSR 项目（Next.js SSR）：`cross_origin_data_types` 可设为空（SSR 服务端渲染无跨 origin 问题）。
- 适配纯前端项目（无后端）：`crud_route_required` 设为 `false`，但敏感字段仍须加密存储或改用后端方案。

## Tauri 构建脚本审查参数（tauri_build_script）

> BR-038~040 Tauri 构建脚本审查的参数。所有参数可适配不同 Tauri 项目。
> 规则文件 [references/tauri-build-script-rule.md](../references/tauri-build-script-rule.md) 不硬编码具体包名、路径或阈值，一切约定从本节读取。
> 复盘来源：Tauri 2.x 桌面应用集成中构建脚本漏写 SPA 构建步骤、用错 pnpm 子包命令、未清理旧产物、未做磁盘空间预检查导致构建失败。

### 总开关

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_build_script.enabled` | `true` | 是否启用本组规则（BR-038~040） |
| `tauri_build_script.severity_br038` | `critical` | BR-038 SPA 构建步骤缺失违规严重级别 |
| `tauri_build_script.severity_br039` | `critical` | BR-039 旧产物清理 + SPA 产物验证缺失违规严重级别 |
| `tauri_build_script.severity_br040` | `suggestion` | BR-040 磁盘空间预检查缺失违规严重级别 |

### 构建脚本与 SPA 子包配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_build_script.build_scripts` | `tauri-build-debug.ps1,tauri-build-release.ps1` | Tauri 构建脚本文件名列表（逗号分隔，相对项目根） |
| `tauri_build_script.spa_package_name` | `@karpathy-wiki/web` | SPA 子包名（`pnpm --filter` 参数） |
| `tauri_build_script.spa_artifact_path` | `services/api/public/` | SPA 构建产物输出目录（相对项目根），构建后此目录须含 `spa_entry_file` |
| `tauri_build_script.spa_entry_file` | `index.html` | SPA 入口文件名（用于 BR-039 存在性验证） |
| `tauri_build_script.forbidden_build_command` | `pnpm run build` | 禁用的根目录构建命令（在 monorepo 根目录会递归触发 tauri 构建） |
| `tauri_build_script.required_build_command_pattern` | `pnpm --filter <pkg> build` | 必需的 SPA 构建命令模式（`<pkg>` 占位符运行时替换为 `spa_package_name`） |
| `tauri_build_script.tauri_build_commands` | `cargo tauri build --debug,cargo tauri build --release` | Tauri 打包命令列表（逗号分隔，用于识别 tauri 构建步骤） |

### 磁盘空间预检查参数（BR-040）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_build_script.debug_min_gb` | `3` | debug 模式磁盘空间下限（GB） |
| `tauri_build_script.release_min_gb` | `5` | release 模式磁盘空间下限（GB） |
| `tauri_build_script.disk_space_cleanup_hint` | `cargo cache -a; 清理 target/ 目录` | 空间不足时的清理建议命令（分号分隔多条） |

- 评审时确认：`build_scripts` 中每个脚本须包含 SPA 构建步骤，且命令形式匹配 `required_build_command_pattern`。
- SPA 构建前须清理 `spa_artifact_path` 下旧产物；构建后须用 `Test-Path` 验证 `spa_entry_file` 存在性。
- debug / release 构建前须做磁盘空间预检查，阈值分别从 `debug_min_gb` / `release_min_gb` 读取，禁止硬编码字面量。
- 适配 npm / yarn：`required_build_command_pattern` 改为 `npm run build --workspace <pkg>` / `yarn workspace <pkg> build`，`forbidden_build_command` 改为 `npm run build` / `yarn build`。
- 适配 Tauri 1.x：`tauri_build_commands` 改为 `tauri build --debug,tauri build --release`（无 `cargo` 前缀）。
- 适配多 SPA 子包：`spa_package_name` 用逗号分隔多个包名，每个包名都须用 `--filter` 单独构建并验证产物。

## Tauri Capability 配置审查参数（tauri_capability_config）

> BR-041~044 Tauri Capability 配置审查的参数。所有参数可适配不同 Tauri 项目。
> 规则文件 [references/tauri-capability-config-rule.md](../references/tauri-capability-config-rule.md) 不硬编码具体命令名、权限名或 URL 模式，一切约定从本节读取。
> 复盘来源：Tauri 2.x 桌面应用集成中 `build.rs` 未注册自定义命令、`capabilities/default.json` 缺权限、`remote.urls` 顶层格式错误、`tauri.conf.json` 未引用 default capability 导致运行时 ACL 拒绝。

### 总开关

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_capability_config.enabled` | `true` | 是否启用本组规则（BR-041~044） |
| `tauri_capability_config.severity_br041` | `critical` | BR-041 build.rs AppManifest::commands 注册缺失违规严重级别 |
| `tauri_capability_config.severity_br042` | `critical` | BR-042 capabilities/default.json permissions 缺失违规严重级别 |
| `tauri_capability_config.severity_br043` | `critical` | BR-043 remote.urls 格式错误违规严重级别 |
| `tauri_capability_config.severity_br044` | `critical` | BR-044 tauri.conf.json capabilities 引用缺失违规严重级别 |

### build.rs 与命令注册参数（BR-041）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_capability_config.build_rs_path` | `src-tauri/build.rs` | build.rs 文件路径（相对项目根） |
| `tauri_capability_config.command_source_directory` | `src-tauri/src/` | 自定义命令源码目录（用于检索 `#[tauri::command]` 标注的函数） |
| `tauri_capability_config.command_decorator_pattern` | `#\[tauri::command\]` | 自定义命令装饰器匹配模式（正则） |
| `tauri_capability_config.app_manifest_method_pattern` | `AppManifest::commands\|\.commands\(` | AppManifest::commands 调用匹配模式（正则） |

### capabilities/default.json 权限参数（BR-042）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_capability_config.capabilities_directory` | `src-tauri/capabilities/` | capability 文件目录（相对项目根） |
| `tauri_capability_config.default_capability_file` | `default.json` | 默认 capability 文件名（在 `capabilities_directory` 下） |
| `tauri_capability_config.default_capability_identifier` | `default` | 默认 capability 的 identifier 值（须被 tauri.conf.json 引用） |
| `tauri_capability_config.permissions_array_field` | `permissions` | capability JSON 中权限数组字段名 |
| `tauri_capability_config.allow_prefix` | `allow-` | 自定义命令权限前缀（如 `allow-load-vault-content`） |
| `tauri_capability_config.required_core_permissions` | `core:default` | 必备的核心插件权限（逗号分隔） |

### remote.urls 配置参数（BR-043）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_capability_config.external_url_permission` | `core:webview:allow-external-urls` | 加载外部 URL 所需权限名 |
| `tauri_capability_config.remote_field_name` | `remote` | 外部 URL 配置的嵌套字段名（非顶层 `urls`） |
| `tauri_capability_config.url_patterns_field` | `urls` | `remote` 对象下 URL 列表字段名 |

### tauri.conf.json 引用参数（BR-044）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_capability_config.tauri_conf_path` | `src-tauri/tauri.conf.json` | tauri.conf.json 文件路径（相对项目根） |
| `tauri_capability_config.capabilities_reference_path` | `app.security.capabilities` | tauri.conf.json 中 capability 引用的 JSON 路径 |

- 评审时确认：`command_source_directory` 下所有 `#[tauri::command]` 标注的函数名须在 `build_rs_path` 的 `AppManifest::commands` 中显式注册。
- `capabilities_directory` / `default_capability_file` 的 `permissions` 数组须包含所有 `allow-<command>` 权限（命令名与 build.rs 注册的命令对应）。
- 外部 URL 加载场景须配置 `remote.urls`（嵌套结构，非顶层 `urls`），并声明 `external_url_permission`。
- `tauri_conf_path` 的 `capabilities_reference_path` 字段须包含 `default_capability_identifier`，且引用的 capability 文件实际存在。
- 适配 Tauri 1.x：本组规则不适用（1.x 用 `allowlist` 而非 capability-based ACL），将 `enabled` 设为 `false`。
- 适配多 capability 项目：`tauri.conf.json` 的 `capabilities` 数组须包含所有 identifier，BR-042 检查须对每个 capability 文件分别校验。
- 适配不同 src-tauri 目录：`build_rs_path` / `capabilities_directory` / `tauri_conf_path` 按项目实际路径调整。

## PowerShell stderr 处理审查参数（powershell_stderr）

> BR-045~047 PowerShell stderr 处理审查的参数。所有参数可适配不同 PowerShell 脚本项目。
> 规则文件 [references/powershell-stderr-rule.md](../references/powershell-stderr-rule.md) 不硬编码具体工具名或正则，一切约定从本节读取。
> 复盘来源：Tauri 2.x 桌面应用集成中 PowerShell 构建脚本在 `$ErrorActionPreference = 'Stop'` 模式下直接调用 cargo，stderr 触发脚本终止；用 `2>&1 | Out-Host` 合并流后 stderr 错误语义丢失。

### 总开关

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `powershell_stderr.enabled` | `true` | 是否启用本组规则（BR-045~047） |
| `powershell_stderr.severity_br045` | `critical` | BR-045 直接 `&` 调用违规严重级别 |
| `powershell_stderr.severity_br046` | `critical` | BR-046 `2>&1` 合并流违规严重级别 |
| `powershell_stderr.severity_br047` | `suggestion` | BR-047 Stop 模式下未用 Start-Process 违规严重级别 |

### 扫描范围与工具列表参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `powershell_stderr.script_glob_pattern` | `**/*.ps1` | 扫描的 PowerShell 脚本文件 glob 模式 |
| `powershell_stderr.start_process_required_commands` | `cargo,rustc,pnpm,npm,node,tsc,tsx,git,go,python,py,java,dotnet` | 必须用 Start-Process 包装的外部工具列表（逗号分隔） |
| `powershell_stderr.forbidden_invoke_pattern` | `&\s*\b(cargo\|rustc\|pnpm\|npm\|node\|tsc\|tsx\|git\|go\|python\|py\|java\|dotnet)\b` | 禁用的 `& <tool>` 直接调用匹配模式（正则字面量） |
| `powershell_stderr.forbidden_redirect_pattern` | `2>&1.*\|\s*Out-Host` | 禁用的 stderr 合并模式（正则，匹配 `2>&1 \| Out-Host`） |
| `powershell_stderr.error_action_preference_pattern` | `\$ErrorActionPreference\s*=\s*['"]Stop['"]` | `$ErrorActionPreference = 'Stop'` 声明匹配模式（正则） |

### Start-Process 调用参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `powershell_stderr.required_start_process_params` | `-NoNewWindow,-Wait,-PassThru` | `Start-Process` 必备参数列表（逗号分隔，缺失任一即视为不通过） |
| `powershell_stderr.recommended_redirect_params` | `-RedirectStandardOutput,-RedirectStandardError` | 推荐的 stderr/stdout 重定向参数（逗号分隔，用于错误定位） |
| `powershell_stderr.exit_code_check_pattern` | `ExitCode\|LASTEXITCODE` | 退出码检查字段匹配模式（正则，调用外部工具后须检查退出码） |

- 评审时确认：`script_glob_pattern` 下所有 `.ps1` 脚本中，调用 `start_process_required_commands` 列表中的工具时必须用 `Start-Process` 包装，且包含 `required_start_process_params` 中的所有必备参数。
- 禁止用 `forbidden_redirect_pattern` 中的合并流模式（如 `2>&1 | Out-Host`），stderr 须用 `recommended_redirect_params` 单独重定向到文件。
- 声明 `error_action_preference_pattern`（Stop 模式）的脚本中，所有外部工具调用必须用 Start-Process，违规严重级别从 critical 提升至 critical（已是最高，但额外标注"Stop 模式下违规更严重"）。
- 适配不同工具链：`start_process_required_commands` 按项目实际使用的外部工具扩展（如 Go 项目追加 `golangci-lint`；Python 项目追加 `pip` / `poetry`；Java 项目追加 `mvn` / `gradle`）。
- 适配 Bash / Zsh 脚本：本规则仅适用于 PowerShell（`.ps1`），Bash 中 `2>&1` 是合法用法（语义不同），无需检查；将 `script_glob_pattern` 设为 `**/*.ps1` 即可仅扫描 PowerShell 脚本。
- 适配 PowerShell Core 7+：默认仍按 5.1 行为；建议统一用 `Start-Process` 模式以兼容 5.1 与 7+。
