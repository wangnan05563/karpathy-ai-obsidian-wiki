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

## 适用 / 不适用场景

### 适用

- 评审 `services/api/` 下的 Fastify 路由、workflow、engine adapter、vault 操作、state store。
- 评审 SSE 流式输出、文件系统并发追加、引擎预算控制等后端逻辑。
- 评审 TypeScript 后端代码的安全、错误处理、可维护性。
- 评审配置持久化、缓存刷新、跨 origin 存储边界、UUID 防路径穿越等持久化层逻辑。

### 不适用

- 前端代码（`.tsx` / `.jsx` / 浏览器侧 `.ts`）。
- 纯 prompt 文本（`prompts/` 下的 `.md` 内容质量评审，属另一技能职责）。
- Obsidian Vault 内容本身的语义正确性（本技能只评审"对 Vault 的操作是否安全"，不评审内容）。
- 构建配置、CI 脚本等非业务后端代码（除非涉及安全或路径校验）。
