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
| HTTP 路由层 | `services/api/src/routes/` | Fastify 路由注册，参数解析 + 响应格式化 |
| 工作流编排 | `services/api/src/workflows/` | 调用 engine adapter，串接 hook 与预算控制 |
| 引擎适配器 | `services/api/src/engine/` | `EngineAdapter` 接口实现，封装外部引擎调用 |
| Vault 文件系统 | `services/api/src/vault/` | 对 Obsidian Vault 的读写、追加、状态持久化 |
| Prompt 存储 | `prompts/` | prompt 模板单点存放，禁止内联到 .ts 代码 |
| 状态持久化 | `services/api/src/state/` | `FileStateStore` 实现，runId 唯一索引 |
| 共享工具 | `services/api/src/utils/` | 通用 helper（路径校验、临时文件等） |

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
| LLM 预设 | `services/api/src/routes/ai.ts` | `LLM_PRESETS` | provider/model 预设列表，供路由与前端共享 |

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
| 运行状态 | `services/api/src/state/` | `runId` 索引 | 由 `FileStateStore` 定义 |
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
| `route_directory` | `services/api/src/routes/` | 路由文件目录（相对项目根） |
| `entry_file` | `services/api/src/index.ts` | 入口文件路径（相对项目根），路由须在此导入与注册 |
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
| `backend_types_path` | `services/api/src/types.ts` | 后端 types 文件路径（相对项目根） |
| `frontend_types_path` | `packages/web/src/types.ts` | 前端 types 文件路径（相对项目根） |
| `sync_interfaces` | `[]` | 需同步的接口名列表（留空则校验全部 `export interface`） |

- 评审时确认：`backend_types_path` 的 `export interface`（或 `sync_interfaces` 列表中的接口）须在 `frontend_types_path` 中存在，且字段名、类型签名、可选性一致。
- 若 monorepo 前端直接 `import type` 引用后端类型（单源定义），可豁免本规则——评审时确认引用路径正确。
- 后端新增字段时，前端在 PR 中同步修改，无遗漏。

## 配置合并保留参数

> 配置合并保留规则（见 [references/config-merge-preservation-rule.md](../references/config-merge-preservation-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体配置文件路径、合并策略或保留段名列表。

| 参数 | 值 | 说明 |
|------|-----|------|
| `config_file_path` | `services/api/config.json` | 分段配置文件路径（相对项目根） |
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

## 适用 / 不适用场景

### 适用

- 评审 `services/api/` 下的 Fastify 路由、workflow、engine adapter、vault 操作、state store。
- 评审 SSE 流式输出、文件系统并发追加、引擎预算控制等后端逻辑。
- 评审 TypeScript 后端代码的安全、错误处理、可维护性。
- 评审配置持久化、缓存刷新、跨 origin 存储边界、UUID 防路径穿越等持久化层逻辑。
- 评审"检查更新"接口的缓存、离线模式、外部 API 超时与降级。

### 不适用

- 前端代码（`.tsx` / `.jsx` / 浏览器侧 `.ts`）。
- 纯 prompt 文本（`prompts/` 下的 `.md` 内容质量评审，属另一技能职责）。
- Obsidian Vault 内容本身的语义正确性（本技能只评审"对 Vault 的操作是否安全"，不评审内容）。
- 构建配置、CI 脚本等非业务后端代码（除非涉及安全或路径校验）。
