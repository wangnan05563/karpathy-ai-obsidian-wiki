---
name: wiki-backend-code-review
description: "Review Fastify + TypeScript backend code. Covers SSE streaming, filesystem safety, route design, harness integration, security, error handling, config management, data consistency, session state, route registration guards, null safety, graceful shutdown, sensitive field masking, type sync, config merge preservation, Tauri 2.x build script / capability config / PowerShell stderr handling. All configurable parameters are loaded from config/review-config.md -- no hardcoding in rule files."
---

# Wiki Backend Code Review

## Review Modes

Choose the mode from the user's request:

- **Pending-change**: review staged/working-tree files slated for commit
- **Snippet**: review pasted code excerpts (function/class/module)
- **File-focused**: review specific files or directories the user points to

Scope tightly: review only what the user provided or explicitly referenced.

## Step-by-Step Workflow

1. **Detect review mode** from user input (pending-change / snippet / file-focused).
2. **Load config**: read [config/review-config.md](config/review-config.md) for directory mappings, SSE conventions, concurrency thresholds, path traversal rules, Tauri build script / capability config / PowerShell stderr parameters, and other parameters. Rule files never hardcode values -- all config comes from this file.
3. **Load rules index**: read [references/.rules-index.md](references/.rules-index.md) for the compact summary of all rule files with trigger keywords and core checks.
4. **Feature-scan the code**: scan review scope for trigger keywords from the index. Match patterns to rule files. For Tauri-related files (e.g., `tauri-build-*.ps1`, `src-tauri/build.rs`, `src-tauri/capabilities/*.json`, `src-tauri/tauri.conf.json`), match Tauri rule categories (BR-038~047). For auth middleware files (e.g., `middleware/auth.ts`, `routes/auth.ts`), match auth endpoint classification rules (BR-048~049). For file deletion operations (e.g., `fs.rm`, `rmSync`, `execSync` with `rd`), match Windows file operation rules (BR-050~051).
5. **Load only matched rule files** from [references/](references/) -- skip categories not triggered.
6. **Apply all matched rules** to the review scope. Each rule file defines rules with severity (critical/suggestion/best-practice), description, and suggested fix with TypeScript / Rust / PowerShell examples.
7. **If no rule matches**, fall back to the Generic Safety Net (below) for a best-effort review.
8. **Compose output** following the Condensed Output Format (below).

## Feature Scan

See [references/.rules-index.md](references/.rules-index.md) for the complete list of trigger keywords per rule file. Quick reference:

| Category | Key Triggers |
|----------|-------------|
| SSE streaming | 	ext/event-stream, 
eply.raw.write/writeHead |
| Filesystem / Vault | s/promises, index.md/log.md, FileStateStore, ault/ |
| Route design | 
equest.body/query/params, Content-Type, Fastify routes |
| Harness integration | EngineAdapter, AsyncIterable, yield, eforeLoop/fterLoop |
| Security | API key refs, path.join from user input, execFile/spawn, pp.listen |
| Error handling | 	ry/catch, instanceof Error, error events, state file corruption |
| Config management | 
eset-config, 
estore, updateConfig(), preset lists |
| Data consistency | display, rand, 
ormalize, 	ask_links |
| Session state | invalidate_cache, cookie, session, health check endpoints |
| Persistence & cache | import.meta.url, process.cwd(), refreshConfigCache, request.params.id, path.join, localStorage, IndexedDB, data/conversations, .gitignore |
| Encoding safety | UTF-8, BOM, GB2312, tsc encoding error, Set-Content/Out-File without -Encoding, WriteAllText, 中文注释乱码, Invalid character |
| Cleanup audit | cleanup, archive, deleteOne, dry_run, days parameter, JSONL audit log, loadStatus, batch delete, errors[] collection |
| Route registration | routes/*.ts, index.ts, register(), app.post/app.get, Fastify route, 404 |
| Null guard | this.provider, this.child, this.connection, spawn/exec/connect/listen, TS2531, possibly null |
| Graceful shutdown | spawn, setInterval, connect, listen, SIGINT, SIGTERM, process.on, process.exit, child.kill, clearInterval |
| Sensitive field masking | apiKey, authtoken, password, secret, token, GET /config, mask, configured flag, empty string |
| Type sync | types.ts, export interface, frontend, backend, sync, monorepo, import type |
| Config merge preservation | config.json, writeFile, readFile, merge, shallow, preserve_sections, tunnel/llm/server section |
| Update check backend | check-update, has_update, offline_mode, cache_ttl, GitHub API, releases/latest, AbortController, current_version |
| Architecture | routes, workflows, engine, vault, 分层, 依赖注入, 跨层调用 |
| Config consistency | getEffectiveApiKey, loadConfig, process.env, 配置读取, 统一函数 |
| Hot update | updateConfig, saveAiConfig, 热更新, 热重载, 闭环 |
| ESM & wiring | __dirname, __filename, import.meta.url, ESM, 接线, registerRoute, SonarQube, S6606, 404, ReferenceError |
| Async reliability | asyncio.wait_for, Promise.race, 超时, 心跳, threading.Thread, worker_threads, best_holder, 兜底 |
| API response type sync | reply.send, reply.raw.write, return result, response shape, API contract, types.ts, export interface |
| SSE event type route | text/event-stream, reply.raw.write, event: xxx, SSE event types, consumeSSEStream, sse_event_types |
| Optional merge | updateConfig, merge, optional, ??, !, non-null assertion, as, mergeConfigSection, Partial<T> |
| Engine adapter sync | EngineAdapter, interface, implements, beforeLoop, afterLoop, yield, compile, query, as unknown as |
| 项目目录结构 | vaultPath, data/vault/, services/api/vault/, .gitignore, git rm --cached, file:../, w64devkit/ |
| 配置化与持久化边界 | process.env., app.listen(, path.join(, new Set([, import.meta.url, process.cwd(), refreshConfigCache, saveAiConfig, localStorage, IndexedDB, data/conversations, apiKey, config.json |
| Tauri 构建脚本 | tauri-build-debug.ps1, tauri-build-release.ps1, pnpm --filter, pnpm run build, services/api/public/, index.html, PSDrive, 磁盘空间, cargo tauri |
| Tauri capability 配置 | build.rs, AppManifest::commands, #[tauri::command], capabilities/default.json, permissions, allow-, remote, urls, tauri.conf.json, app.security.capabilities |
| PowerShell stderr 处理 | $ErrorActionPreference, Start-Process, -NoNewWindow, -Wait, -PassThru, 2>&1, Out-Host, & cargo, & pnpm, RedirectStandardError |
| 认证端点分类 | publicPaths, preHandler, authGuard, /api/auth/me, currentUser, 401, setupAuthMiddleware, isPublicPath |
| Windows 文件操作 | fs.rm, rmSync, rd /s /q, execSync, existsSync, Windows, 文件句柄, 静默失败, SKILL_ID_PATTERN |

## Generic Safety Net

If no rule matches, perform best-effort review on: **Security** (hardcoded keys, path traversal, command injection, improper binding, error info leakage), **Performance** (sync FS APIs, missing locks, unclosed SSE connections, missing budget checks), **Code Quality** (SRP violations, inconsistent signatures, inline prompts, magic strings), **Testing** (missing coverage, implementation-detail tests, flaky patterns, missing edge cases), **Encoding** (non-UTF-8 source files, BOM in .ts/.json, PowerShell default-encoding writes on Chinese-commented files), **Cleanup safety** (batch delete without audit log, missing days lower-bound, dry_run default false, missing per-item try-catch, missing state refresh after delete), **Route registration** (new routes/*.ts not imported or register() not called in entry file), **Null safety** (external-async-assigned fields used without `if (!x)` guard, TS2531), **Graceful shutdown** (spawn/setInterval/connect without SIGINT/SIGTERM cleanup hooks), **Type sync** (backend types.ts new interface missing in frontend types.ts), **Config merge** (writeFile on multi-section config without reading original first, preserve_sections lost), **Update check** (check-update route without module-level cache, offline_mode true but still calling GitHub API, missing AbortController timeout, hardcoded current_version instead of reading package.json), **Architecture** (routes→vault cross-layer calls, missing dependency injection), **Config consistency** (direct process.env reads instead of unified functions), **Hot update** (saveAiConfig without updateConfig call), **ESM & wiring** (__dirname/__filename in ESM, new routes not wired in entry, blind static-analysis suggestion adoption), **Async reliability** (await without timeout, asyncio.Task heartbeat instead of threading.Thread, status file ts dependent on blocked event loop, timeout without fallback data), **API response type sync** (reply.send object shape diverges from frontend types.ts interface, new response field not synced in same PR, optionality mismatch), **SSE event type route** (new SSE event type not registered in config list, frontend consumeSSEStream missing handler branch, unknown event silently swallowed), **Optional merge** (config merge function uses `!` non-null assertion or `as` cast on optional fields, undefined serialized to config file), **Engine adapter sync** (EngineAdapter interface method not implemented in all `implements` classes, `as unknown as` bypassing implements check, `@ts-ignore` suppressing missing method error), **项目目录结构** (源码目录混放运行时数据、.gitignore 缺失运行时产物规则、已跟踪文件未 git rm --cached、file: 协议路径未验证), **配置化与持久化边界** (硬编码 API Key/port/path/timeout、process.cwd() 作为唯一路径锚点、写盘函数未调用 refreshConfigCache、跨 origin 数据后端未提供 CRUD 路由、localStorage 存储 API key), **Tauri 构建脚本** (tauri-build-*.ps1 缺失 SPA 构建步骤、用 `pnpm run build` 递归触发 tauri 构建、未清理 services/api/public/ 旧产物、未验证 index.html 存在性、未做磁盘空间预检查), **Tauri capability 配置** (build.rs 未在 AppManifest::commands 注册自定义命令、capabilities/default.json permissions 缺 allow-<command>、remote.urls 顶层格式错误非嵌套、tauri.conf.json app.security.capabilities 未引用 default), **PowerShell stderr 处理** (Stop 模式下直接 `& cargo` 调用导致 stderr 触发终止、用 `2>&1 | Out-Host` 合并流丢失错误语义、Start-Process 缺 -NoNewWindow/-Wait/-PassThru 必备参数、未检查 ExitCode), **认证端点分类** (需鉴权端点误放入 publicPaths 白名单导致 preHandler 跳过 token 解析，currentUser 永远 null，authGuard 返回 401), **Windows 文件操作** (win32 平台服务进程用 fs.rm 删除目录静默失败不抛异常，删除后未 existsSync 验证结果，路径穿越防护缺失导致用户输入拼接到删除命令).

## Condensed Output Format

When findings exist, use **Template A (Condensed)**. When no issues, use **Template B**.

### Template A (Condensed)

`
# Code Review Summary

## Critical (<X> issues)

### 1. <brief title>

**File:** <path>:<line>
`	s
<relevant code, max 3 lines>
`

**Issue:** <one-sentence explanation with rule reference>
**Fix:** <one-line suggestion>. [Code example only if non-trivial]

---
[repeat for each issue]

## Suggestions (<Y>)
[same condensed format]

## Nits (<Z>)
[same condensed format]

## What's Good
- <positive feedback, max 3 points>
`

Rules:
- Omit any section with zero items.
- If any category has 10+ items, summarize as "10+" and show the first 10.
- Keep blank lines between sections for readability.
- If issues require code changes, append: "Would you like me to apply the suggested fix(es)?"

### Template B (No Issues)

`
## Code Review Summary
No issues found.
`

## Usage Notes

- Always include actionable fixes with code snippets when applicable. Rule file examples are in TypeScript / Rust / PowerShell (depending on the rule category).
- Rule Description fields are in Chinese to align with codebase conventions -- keep review explanations consistent.
- Use best-effort File:Line references; fall back to the most specific identifier available.
- When actual file paths differ from config directory mappings, review anyway and note the discrepancy.
- The rules index ([references/.rules-index.md](references/.rules-index.md)) provides trigger keywords and core checks for all rule files. Load full rule files only for matched categories.

## Quick-Check Rules (通用审查规则)

> 以下规则作为快速检查清单，与 references/ 下的详细规则文件互补。
> 命名约定：BR- 前缀表示 Backend Review 规则编号。

### 类型安全
- 禁止 `any` 类型（除迁移期代码）
- 异步函数返回值必须显式标注 `Promise<T>`
- catch 块必须用 `err instanceof Error` 守卫
- 可选字段必须显式标注 `?` 或 `undefined`

### 异步与并发
- SSE 路由必须用 `reply.raw.write()` 而非 `return reply.send()`
- 长时间操作必须设置超时
- 文件 I/O 必须用 `fs/promises` 异步版本

### 错误处理
- 错误消息不能暴露内部实现细节
- 必须区分用户错误（4xx）和服务器错误（5xx）
- 外部 API 调用失败必须有降级逻辑

### 安全
- API Key 不硬编码
- 用户输入必须校验
- 文件路径必须防穿越
- `localOnly` 默认 `true`

### Async 可靠性（BR-ASYNC-01~04）

> 详细规则见 [references/async-reliability-rule.md](references/async-reliability-rule.md)，参数见 `config/review-config.md` 的"Async 可靠性审查参数"章节。

- **BR-ASYNC-01**：async 调用必须设置超时（`Promise.race` / `asyncio.wait_for` 包裹，超时值从配置读取）
- **BR-ASYNC-02**：事件循环阻塞场景必须使用线程级心跳（`worker_threads` / `threading.Thread`，禁止 `Promise.then` / `asyncio.Task`）
- **BR-ASYNC-03**：状态文件 `ts` 字段更新必须独立于业务事件循环（独立线程写入或循环间隔 ≤ `heartbeat_max_interval_sec`）
- **BR-ASYNC-04**：async 调用超时必须提供兜底数据（`best_holder` 模式，禁止直接 raise 终止流程）

### ESM 与模块接线（BR-ESM-01~04）

> 详细规则见 [references/esm-and-wiring-rule.md](references/esm-and-wiring-rule.md)，参数见 `config/review-config.md` 的"ESM 与模块接线审查参数"章节。

- **BR-ESM-01**：ESM 模式下禁用 `__dirname` / `__filename`，必须用 `import.meta.url` 派生
- **BR-ESM-02**：新增 `routes/*.ts` 或 `workflows/*.ts` 模块必须在入口文件完成接线三步骤（import → instantiate → registerRoute）
- **BR-ESM-03**：静态分析工具（SonarQube / ESLint）的修复建议必须人工验证运行时语义
- **BR-ESM-04**：所有 `routes/*.ts` 中暴露的端点必须在入口文件可达（注册函数被调用）

### API 响应类型同步检查（BR-026）

> 详细规则见 [references/api-response-type-sync-rule.md](references/api-response-type-sync-rule.md)，参数见 `config/review-config.md` 的"API 响应类型同步审查参数（api_response_type_sync）"章节。

- **BR-026-1**：API 端点 `reply.send(...)` 返回的对象形状必须与前端 `frontend_types_path` 中对应 interface 字段名、类型签名、可选性一致
- **BR-026-2**：后端在响应对象中新增字段时，前端 interface 必须在同一 PR 中同步新增；可选字段必须用 `field?: T` 标注，禁止用 `field: T` 强制非空
- 例外：monorepo 前端通过 `import type` 直接引用后端 types.ts 时豁免（单源定义即保证一致）

### SSE 事件类型扩展路由同步（BR-027）

> 详细规则见 [references/sse-event-type-route-rule.md](references/sse-event-type-route-rule.md)，参数见 `config/review-config.md` 的"SSE 事件类型扩展路由审查参数（sse_event_type_route）"章节。

- **BR-027-1**：后端 SSE 路由中 `event: <type>` 字面量必须登记在 config 的 `sse_event_types_config_field` 字段对应列表中；事件类型从 config 读取，禁止字面量硬编码
- **BR-027-2**：后端新增 SSE 事件类型时，前端 `consumeSSEStream` 必须同步新增 handler 分支；未知事件类型的默认 handler 行为必须明确（如 `console.warn`），禁止静默吞掉

### 配置字段 optional 合并非空断言（BR-028）

> 详细规则见 [references/optional-merge-rule.md](references/optional-merge-rule.md)，参数见 `config/review-config.md` 的"配置字段 optional 合并审查参数（optional_merge）"章节。

- **BR-028-1**：配置合并函数（`updateConfig` / `mergeConfigSection` 等）中访问可选字段（`T | undefined`）禁止用 `field!` 后缀断言，必须用 `??` 默认值或 `if` 守卫显式处理 `undefined` 分支
- **BR-028-2**：配置合并函数中禁止用 `as T` 强转将 `T | undefined` 断言为 `T`，必须用类型守卫（`typeof x === 'string'`）、`??` 默认值或显式 `if (x === undefined)` 分支处理

### EngineAdapter 接口变更实现同步（BR-029）

> 详细规则见 [references/engine-adapter-sync-rule.md](references/engine-adapter-sync-rule.md)，参数见 `config/review-config.md` 的"EngineAdapter 接口变更实现同步审查参数（engine_adapter_sync）"章节。

- **BR-029-1**：`EngineAdapter` 接口新增/修改方法签名时，所有 `implements EngineAdapter` 的实现类必须同步新增/修改对应方法，签名（参数名、参数类型、返回类型）与接口完全一致
- **BR-029-2**：禁止用 `as unknown as EngineAdapter` 断言、`@ts-ignore`、`@ts-expect-error` 绕过 implements 检查；禁止用 `throw new Error('not implemented')` 占位——若方法对当前实现无意义，应在接口中声明为可选方法（`method?(...)`），由调用方做存在性检查

### 项目目录结构与文件组织（BR-030~033）

> 详细规则见 [references/project-structure-review-rule.md](references/project-structure-review-rule.md)，参数见 `config/review-config.md` 的"项目目录结构审查参数（project_structure_review）"章节。

- **BR-030**：源码目录（`source_dirs`）中不得混放运行时数据（`runtime_data_dir`，如 `data/vault/`）、构建产物（`build_output_dirs`，如 `dist/`、`build/`）以及外部工具链（`external_toolchain_dirs`，如 `w64devkit/`）。混放会导致运行时写入污染源码、构建产物误提交、仓库膨胀且不可跨平台复用
- **BR-031**：运行时产物（`runtime_data_ignore`）和构建产物（`build_output_ignore`）必须在 `.gitignore` 中登记排除规则；已跟踪文件须先 `git rm --cached` 移除索引，仅添加 `.gitignore` 对已跟踪文件无效。用 `verification_command`（`git check-ignore -v`）验证规则生效，用 `tracked_check_command`（`git ls-files`）检查残留跟踪文件
- **BR-032**：配置文件（`config_files_to_check`）中 `vaultpath_config_field`（如 `vaultPath`）字段默认值不得指向 `source_dirs` 任一源码目录，运行时数据须统一外迁到 `runtime_data_patterns`（如 `data/`）约定的目录下
- **BR-033**：`package.json`（`package_json_files`）中 `file_protocol_pattern`（如 `file:../`）协议引用必须经过路径存在性验证——被引用路径必须实际存在且可解析，用 `verify_command`（如 `npm ls <pkg>`）验证，未验证的 `file:` 引用会导致 CI / 新克隆环境下 `npm install` 失败

### 配置化参数与持久化边界（BR-034~037）

> 详细规则见 [references/config-persistence-boundary-rule.md](references/config-persistence-boundary-rule.md)，参数见 `config/review-config.md` 的"配置化与持久化边界审查参数（config_persistence_boundary）"章节。
> 复盘来源：前端硬编码 rgba() 颜色在浅色主题下辨识度低（CODING-041~046），后端同理存在硬编码 API Key/port/path/timeout 问题。

- **BR-034**：后端代码中禁止硬编码可配置参数（`configurable_param_patterns`：API Key/port/path/timeout/secret），必须通过 `config.json` 或环境变量注入；检测模式：`process.env.` 读取须确认密钥从环境变量读取而非字面量，`app.listen(` 须确认 port/host 从 config 读取，`path.join(` 须确认路径从 config 读取而非硬编码字符串，`new Set([` 须确认白名单从 config 读取而非内联数组
- **BR-035**：路径解析必须采用三级策略（`path_resolution_strategy`：优先 `import.meta.url` + 打包兜底 `process.cwd()` + CWD 探测），禁止 `process.cwd()` 作为唯一路径锚点（CWD 受启动方式影响，开发/打包/工具链切换会漂移）；`getConfigPath()` / `getStateDir()` 等路径解析函数必须实现三级策略
- **BR-036**：写盘函数（`write_persistence_functions`：saveAiConfig/resetAiConfig/saveWebSearchConfig 等）必须在 `await fs.writeFile(...)` 成功后、`return reply` 之前调用对应的缓存刷新方法（`refreshConfigCache(data)`）；缓存 TTL（默认 30s）不替代显式刷新——即使 TTL 很短，写盘后仍必须立即刷新，避免窗口期内 GET 返回旧值；`fs.writeFile` 抛错时不得刷新缓存（保持旧值供降级读取），并须向客户端返回 5xx
- **BR-037**：跨 origin 持久化数据（`cross_origin_data_types`：AI 配置 apiKey / 历史会话）必须后端为权威源，前端浏览器存储（localStorage/IndexedDB）仅作降级缓存；后端必须提供 CRUD 路由（`/api/conversations/:id` 等）；后端不可用时前端降级到本地缓存，但须 `console.warn` 记录降级事件，不得静默失败；localStorage 仅存储非敏感 UI 状态（baseUrl/model），API key 必须存储在 backend config.json

### Tauri 2.x 桌面应用集成审查（BR-038~047）

> 基于 Tauri 2.x 桌面应用集成历史问题复盘提炼，覆盖构建脚本、capability 配置、PowerShell stderr 处理三个维度。
> 详细规则见对应 references 文件，参数见 `config/review-config.md` 的对应章节。

#### Tauri 构建脚本审查（BR-038~040）

> 详细规则见 [references/tauri-build-script-rule.md](references/tauri-build-script-rule.md)，参数见 `config/review-config.md` 的"Tauri 构建脚本审查参数（tauri_build_script）"章节。

- **BR-038**：Tauri 构建脚本（`tauri-build-debug.ps1` / `tauri-build-release.ps1`）必须包含 SPA 构建步骤，且用 `pnpm --filter <spa_package_name> build`（禁止 `pnpm run build` 在根目录递归触发 tauri 构建）；缺失 SPA 构建步骤 → 审查失败（critical）
- **BR-039**：构建前必须清理 `spa_artifact_path`（如 `services/api/public/`）下旧产物（避免旧 hash 文件残留）；构建后必须用 `Test-Path` 验证 `spa_entry_file`（如 `index.html`）存在性，缺失则中断构建（critical）
- **BR-040**：debug / release 构建前必须做磁盘空间预检查（debug >= `debug_min_gb` GB，release >= `release_min_gb` GB，阈值从 config 读取）；空间不足时中断并给出清理建议（suggestion）

#### Tauri Capability 配置审查（BR-041~044）

> 详细规则见 [references/tauri-capability-config-rule.md](references/tauri-capability-config-rule.md)，参数见 `config/review-config.md` 的"Tauri Capability 配置审查参数（tauri_capability_config）"章节。
> 仅适用于 Tauri 2.x（capability-based ACL 系统），Tauri 1.x 用 allowlist 模式不适用本组规则。

- **BR-041**：`build.rs` 必须显式声明 `AppManifest::commands(...)` 注册所有自定义命令（与 `src-tauri/src/` 下所有 `#[tauri::command]` 标注的函数列表对比，差异即违规）（critical）
- **BR-042**：`capabilities/default.json` 的 `permissions` 数组必须包含所有 `allow-<command>` 权限（命令名与 build.rs 注册的命令对应）+ 必备核心权限（`core:default`）（critical）
- **BR-043**：外部 URL 加载场景必须配置 `remote.urls` 嵌套结构（**非**顶层 `urls`，正确格式为 `{ "remote": { "urls": [...] } }`）+ 声明 `core:webview:allow-external-urls` 权限；顶层 `urls` 会被 Tauri 静默忽略导致 WebView 加载失败（critical）
- **BR-044**：`tauri.conf.json` 的 `app.security.capabilities` 数组必须引用 `default`（即 capability 文件的 identifier），且引用的 capability 文件实际存在；未引用 → 所有 invoke 调用被 ACL 拒绝（critical）

#### PowerShell stderr 处理审查（BR-045~047）

> 详细规则见 [references/powershell-stderr-rule.md](references/powershell-stderr-rule.md)，参数见 `config/review-config.md` 的"PowerShell stderr 处理审查参数（powershell_stderr）"章节。
> 仅适用于 PowerShell（.ps1）脚本，Bash/Zsh 中 `2>&1` 是合法用法（语义不同）无需检查。

- **BR-045**：PowerShell 脚本中调用 `cargo` / `rustc` / `pnpm` / `node` 等外部工具必须用 `Start-Process -NoNewWindow -Wait -PassThru` 包装，禁止直接 `& cargo ...` 或 `cargo ...`（直接调用时 stderr 会触发 `$ErrorActionPreference = 'Stop'` 终止脚本，或污染 `$Error` 集合）（critical）
- **BR-046**：禁止用 `2>&1 | Out-Host` / `2>&1 | Out-File` 合并 stderr 与 stdout（stderr 错误语义丢失，无法区分 cargo 警告 vs 致命错误）；必须用 `Start-Process -RedirectStandardError <file>` 将 stderr 单独重定向到文件便于错误定位（critical）
- **BR-047**：声明 `$ErrorActionPreference = 'Stop'` 的脚本中，所有外部工具调用必须用 `Start-Process` 避免 stderr 误报；建议统一用 Stop + Start-Process 模式（suggestion）

### 认证端点分类审查（BR-048~049）

> 详细规则见 [references/auth-endpoint-classification-rule.md](references/auth-endpoint-classification-rule.md)，参数见 `config/review-config.md` 的"认证端点分类审查参数（auth_endpoint_classification）"章节。
> 复盘来源：Skill 导入模块开发中 `/api/auth/me` 误放入 publicPaths 导致 RBAC 401（CODING-054）。

- **BR-048-1**：`publicPaths` 白名单只能包含完全公开端点（`auth_endpoint_classification.public_paths_whitelist`，默认 `/api/auth/login,/health`），需鉴权端点（如 `/api/auth/me`）禁止放入——publicPaths 中的路径会让全局 preHandler 跳过 token 解析（critical）
- **BR-048-2**：`publicPaths` 陷阱是反直觉的：看似"公开"端点放入白名单，实际导致认证中间件跳过解析，`currentUser` 永远为 null，authGuard 必然返回 401（critical）
- **BR-049-1**：`/api/auth/me` 等"获取当前用户信息"端点必须走正常 token 解析流程，未登录时由 authGuard 返回 401（critical）
- **BR-049-2**：`publicPaths` 配置位置必须在认证中间件初始化处集中管理，禁止散落在多处（suggestion）

### Windows 文件操作审查（BR-050~051）

> 详细规则见 [references/windows-file-operation-rule.md](references/windows-file-operation-rule.md)，参数见 `config/review-config.md` 的"Windows 文件操作审查参数（windows_file_operation）"章节。
> 复盘来源：Skill 导入模块开发中 deleteSkill 用 fs.rm 静默失败导致目录残留（CODING-055）。
> 仅适用于 Windows（`windows_file_operation.platform` = `win32`）环境，Linux/macOS 用 `rm -rf` 或 fs.rm 通常可靠。

- **BR-050-1**：`win32` 平台服务进程中的目录删除必须用 `rd /s /q` + `existsSync` 验证，`fs.rm`/`rmSync` 作为 fallback（critical）
- **BR-050-2**：fallback 仍失败必须抛错，禁止静默返回成功（`{ ok: true }` 但目录仍存在）（critical）
- **BR-051-1**：删除后必须用 `existsSync` 验证目录已不存在，返回值反映真实删除结果（critical）
- **BR-051-2**：路径穿越防护（如白名单正则校验）必须在删除前执行，禁止直接拼接用户输入到 `execSync` 命令中（critical）

## Related Skills

| Skill | 协作场景 |
|---|---|
| wiki-code-dev | 审查后发现的问题由 wiki-code-dev 修复 |
| wiki-frontend-code-review | 前端代码审查 |
| obsidian-auto-testing | 审查后验证修复效果 |

## Version History

| 版本 | 日期 | 变更说明 |
|---|---|---|
| v1.0.0 | 2026-07-10 | 初始版本，含配置一致性和热更新闭环规则 |
| v1.1.0 | 2026-07-18 | 新增 BR-ESM-01~04 规则；新增 references/esm-and-wiring-rule.md；更新 review-config.md 追加 ESM 与模块接线审查参数章节 |
| v1.2.0 | 2026-07-21 | 新增 BR-ASYNC-01~04 规则；新增 references/async-reliability-rule.md；更新 review-config.md 追加 Async 可靠性审查参数章节 |
| v1.3.0 | 2026-07-22 | 新增 BR-026~029 规则；新增 4 个规则文件（api-response-type-sync-rule.md / sse-event-type-route-rule.md / optional-merge-rule.md / engine-adapter-sync-rule.md）；更新 review-config.md 追加 4 个参数章节（api_response_type_sync / sse_event_type_route / optional_merge / engine_adapter_sync）；更新 .rules-index.md 追加 4 条索引；更新 Feature Scan 表格、Generic Safety Net、Quick-Check Rules |
| v1.4.0 | 2026-07-22 | 新增 BR-030~033 规则；新增 references/project-structure-review-rule.md（目录结构分离 / .gitignore 完整性 / 运行时数据外迁 / file: 协议路径验证）；更新 review-config.md 追加项目目录结构审查参数（project_structure_review）章节；更新 Feature Scan 表格、Generic Safety Net、Quick-Check Rules |
| v1.5.0 | 2026-07-22 | 新增 BR-034~037 规则（配置化参数与持久化边界）：配置化参数检测（硬编码 API Key/port/path/timeout 禁止）、路径解析锚点合规性（import.meta.url 三级策略）、缓存刷新机制（写盘后 refreshConfigCache）、跨 origin 持久化边界（后端权威源+localStorage 降级缓存）。更新 Feature Scan 表格追加"配置化与持久化边界"类别，Generic Safety Net 追加对应条目，Quick-Check Rules 追加 BR-034~037 章节。基于「主题色变量映射」复盘对应的后端配置化原则。 |
| v1.6.0 | 2026-07-22 | 新增 BR-038~047 规则（Tauri 2.x 桌面应用集成审查）：BR-038~040 Tauri 构建脚本审查（SPA 构建步骤 + pnpm --filter + 旧产物清理 + index.html 验证 + 磁盘空间预检查）；BR-041~044 Tauri capability 配置审查（build.rs AppManifest::commands 注册 + capabilities/default.json allow- 权限 + remote.urls 嵌套格式 + tauri.conf.json capabilities 引用 default）；BR-045~047 PowerShell stderr 处理审查（Start-Process 包装外部工具 + 禁止 2>&1 合并流 + Stop 模式下避免 stderr 误报）。新增 3 个规则文件（tauri-build-script-rule.md / tauri-capability-config-rule.md / powershell-stderr-rule.md）；更新 review-config.md 追加 3 个参数章节（tauri_build_script / tauri_capability_config / powershell_stderr）；更新 .rules-index.md 追加 10 条索引；更新 Feature Scan 表格、Generic Safety Net、Quick-Check Rules。基于 Tauri 2.x 桌面应用集成历史问题复盘提炼。 |
| v1.7.0 | 2026-07-23 | 新增 BR-048~051 规则（认证端点分类 + Windows 文件操作）：BR-048~049 认证端点分类审查（publicPaths 白名单只能含完全公开端点，需鉴权端点禁止放入，避免 preHandler 跳过 token 解析导致 currentUser 永远 null）；BR-050~051 Windows 文件操作审查（win32 平台目录删除用 rd /s /q + existsSync 验证，fs.rm 作为 fallback，路径穿越防护在删除前执行）。新增 2 个规则文件（auth-endpoint-classification-rule.md / windows-file-operation-rule.md）；更新 review-config.md 追加 2 个参数章节（auth_endpoint_classification / windows_file_operation）；更新 .rules-index.md 追加 2 条索引；更新 Feature Scan 表格、Generic Safety Net、Quick-Check Rules。基于「Skill 导入模块开发」任务四维度复盘（成功步骤/不确定性/可抽象流程/适用场景）。 |
