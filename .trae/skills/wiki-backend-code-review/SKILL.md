---
name: wiki-backend-code-review
description: "Review Fastify + TypeScript backend code. Covers SSE streaming, filesystem safety, route design, harness integration, security, error handling, config management, data consistency, session state, route registration guards, null safety, graceful shutdown, sensitive field masking, type sync, config merge preservation, Tauri 2.x build script / capability config / PowerShell stderr handling, multi-resource parallel loading (Promise.allSettled), timeout chain matching (layered timeout coverage), external API contract (fetchWithDiagnostics error code mapping + field fallback + type conversion), timeout tier strategy (task creation / polling / image / video / llm small-large tiers), API key multi-source resolution (dedicated → shared → env fallback chain), long/short task architecture separation (SSE threshold + rate limit + error code classification + dual logging), media archive frontmatter standardization (type/output_mode/generated_at + filename pattern), session store double-layer eviction (TTL + LRU) and tamper-proofing (reference mode), SSE event object mapping dispatch (Record<string, Handler> + outputMode union literal). All configurable parameters are loaded from config/review-config.md -- no hardcoding in rule files."
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
4. **Feature-scan the code**: scan review scope for trigger keywords from the index. Match detected patterns to corresponding rule files per the Feature Scan table below (BR-038~047 for Tauri, BR-048~049 for auth, BR-050~051 for file ops, BR-052~060 for media generation, etc.).
5. **Load only matched rule files** from [references/](references/) -- skip categories not triggered.
6. **Apply all matched rules** to the review scope. Each rule file defines rules with severity (critical/suggestion/best-practice), description, and suggested fix with TypeScript / Rust / PowerShell examples.
7. **If no rule matches**, fall back to the Generic Safety Net (below) for a best-effort review.
8. **Compose output** following the Condensed Output Format (below).

## Feature Scan

See [references/.rules-index.md](references/.rules-index.md) for the complete list of trigger keywords per rule file. Quick reference:

| Category | Key Triggers |
|----------|-------------|
| SSE streaming | text/event-stream, reply.raw.write/writeHead |
| Filesystem / Vault | fs/promises, index.md/log.md, FileStateStore, vault/ |
| Route design | request.body/query/params, Content-Type, Fastify routes |
| Harness integration | EngineAdapter, AsyncIterable, yield, beforeLoop/afterLoop |
| Security | API key refs, path.join from user input, execFile/spawn, app.listen |
| Error handling | try/catch, instanceof Error, error events, state file corruption |
| Config management | reset-config, restore, updateConfig(), preset lists |
| Data consistency | display, brand, normalize, task_links |
| Session state | invalidate_cache, cookie, session, health check endpoints |
| Persistence & cache | import.meta.url, process.cwd(), refreshConfigCache, path.join, localStorage, IndexedDB, data/conversations, .gitignore |
| Encoding safety | UTF-8, BOM, GB2312, tsc encoding error, Set-Content/Out-File without -Encoding, 中文注释乱码 |
| Cleanup audit | cleanup, archive, deleteOne, dry_run, days parameter, JSONL audit log, loadStatus, batch delete, errors[] |
| Route registration | routes/*.ts, index.ts, register(), app.post/app.get, Fastify route, 404 |
| Null guard | this.provider, this.child, this.connection, spawn/exec/connect/listen, TS2531 |
| Graceful shutdown | spawn, setInterval, connect, listen, SIGINT, SIGTERM, process.on, process.exit |
| Sensitive field masking | apiKey, authtoken, password, secret, token, GET /config, mask |
| Type sync | types.ts, export interface, frontend, backend, sync, monorepo, import type |
| Config merge preservation | config.json, writeFile, readFile, merge, shallow, preserve_sections |
| Update check backend | check-update, has_update, offline_mode, cache_ttl, GitHub API, releases/latest, AbortController |
| Architecture | routes, workflows, engine, vault, 分层, 依赖注入, 跨层调用 |
| Config consistency | getEffectiveApiKey, loadConfig, process.env, 配置读取, 统一函数 |
| Hot update | updateConfig, saveAiConfig, 热更新, 热重载, 闭环 |
| ESM & wiring | __dirname, __filename, import.meta.url, ESM, 接线, registerRoute, SonarQube, S6606, 404 |
| Async reliability | asyncio.wait_for, Promise.race, 超时, 心跳, threading.Thread, worker_threads, best_holder |
| API response type sync | reply.send, reply.raw.write, return result, response shape, API contract, types.ts |
| SSE event type route | text/event-stream, reply.raw.write, event: xxx, SSE event types, consumeSSEStream, sse_event_types |
| Optional merge | updateConfig, merge, optional, ??, !, non-null assertion, as, mergeConfigSection, Partial<T> |
| Engine adapter sync | EngineAdapter, interface, implements, beforeLoop, afterLoop, yield, compile, query, as unknown as |
| 项目目录结构 | vaultPath, data/vault/, services/api/vault/, .gitignore, git rm --cached, file:../ |
| 配置化与持久化边界 | process.env., app.listen(, path.join(, new Set([, import.meta.url, process.cwd(), refreshConfigCache, saveAiConfig, apiKey |
| Tauri 构建脚本 | tauri-build-debug.ps1, tauri-build-release.ps1, pnpm --filter, services/api/public/, index.html, PSDrive, cargo tauri |
| Tauri capability 配置 | build.rs, AppManifest::commands, #[tauri::command], capabilities/default.json, permissions, allow-, remote, urls, tauri.conf.json |
| PowerShell stderr 处理 | $ErrorActionPreference, Start-Process, -NoNewWindow, -Wait, -PassThru, 2>&1, Out-Host, & cargo, RedirectStandardError |
| 认证端点分类 | publicPaths, preHandler, authGuard, /api/auth/me, currentUser, 401, setupAuthMiddleware, isPublicPath |
| Windows 文件操作 | fs.rm, rmSync, rd /s /q, execSync, existsSync, Windows, 文件句柄, 静默失败, SKILL_ID_PATTERN |
| Parallel Loading | Promise.allSettled, Promise.all, for await, for...of, 串行加载, MCP, loadMcpTools, loadResources, errors[], source, 降级 |
| Timeout Chain | setTimeout, AbortController, AbortSignal.timeout, 超时, mcpTimeoutMs, questionTimeoutMs, 链式超时, margin |
| External API Contract | fetch(, fetchWithDiagnostics, err.cause.code, UND_ERR_CONNECT_TIMEOUT, ENOTFOUND, data.url, data.metadata.url, String(value), Go 后端, type conversion |
| Timeout Tier | AbortSignal.timeout, task_creation, task_polling, image_generation, video_download, llm_small, llm_large, proxy_overhead_ms, tokenBudget |
| API Key Resolution | apiKey, apiKeyRef, apiKeys, dedicated, shared, env, fallback_chain, resolveApiKey, getEffectiveApiKey, process.env[ |
| Long Task Architecture | SSE, text/event-stream, rateLimit, timeWindow, destructive, poll, setInterval, request.log.error, not configured, 设计要点 |
| Media Archive Frontmatter | frontmatter, type: query, output_mode, generated_at, image_file, video_file, task_id, source_url, vault/queries/, archive, marp: true |
| Session Store | new Map(, Map.set, Map.delete, Map.keys().next(), sessions, max_sessions, ttl_ms, expiresAt, sessionId, messageIndex, trust_client_content, 防篡改 |
| SSE Event Dispatch | text/event-stream, reply.raw.write, event:, chunk.text, chunk.image, chunk.ppt, chunk.video, if/else if, Record<string, Handler>, outputMode, outputModes, S3776 |
| PowerShell Long Process | EPIPE, broken pipe, exit code -1, vue-tsc, orchestrator.py, powershell pipe, long-running process, Select-String, Out-String, Where-Object |
| Rollback Safety | rollback, restore, revert, partial rollback, recovery order, Edit tool, Write forbidden, deleted code, functional recovery |

## Generic Safety Net

If no rule matches, perform best-effort review on these categories (see Quick-Check Rules for details):

| Category | Key Checks |
|----------|-----------|
| Security | hardcoded keys, path traversal, command injection, improper binding, error info leakage |
| Performance | sync FS APIs, missing locks, unclosed SSE, missing budget checks |
| Code Quality | SRP violations, inconsistent signatures, inline prompts, magic strings |
| Testing | missing coverage, implementation-detail tests, flaky patterns |
| Encoding | non-UTF-8 sources, BOM in .ts/.json, PowerShell default-encoding writes |
| Cleanup safety | batch delete without audit log, missing days lower-bound, missing per-item try-catch |
| Route registration | new routes/*.ts not imported or register() not called |
| Null safety | external-async-assigned fields used without guard, TS2531 |
| Graceful shutdown | spawn/setInterval/connect without SIGINT/SIGTERM cleanup |
| Type sync | backend types.ts new interface missing in frontend |
| Config merge | writeFile on multi-section config without reading original first |
| Update check | missing module-level cache, offline_mode=true still calling API, missing timeout |
| Architecture | cross-layer calls, missing dependency injection |
| Config consistency | direct process.env reads instead of unified functions |
| Hot update | saveAiConfig without updateConfig call |
| ESM & wiring | __dirname in ESM, new routes not wired, blind static-analysis fixes |
| Async reliability | await without timeout, status file ts dependent on blocked event loop |
| API response type sync | reply.send shape diverges from frontend interface |
| SSE event type route | new event type not in config, consumeSSEStream missing handler |
| Optional merge | ! non-null assertion or as cast on optional fields in merge functions |
| Engine adapter sync | implements class missing method, as unknown as bypass |
| 项目目录结构 | 源码混放运行时数据, .gitignore 缺失, file: 协议未验证 |
| 配置化与持久化边界 | 硬编码 key/port/path, process.cwd() 唯一锚点, 未 refreshConfigCache |
| Tauri 构建 | 缺 SPA 构建步骤, pnpm run build 递归, 未清理旧产物, 未验证 index.html |
| Tauri capability | 缺 AppManifest::commands, 缺 allow- 权限, remote.urls 格式错误 |
| PowerShell stderr | 直接 & cargo 触发 Stop, 2>&1 合并流, 缺 Start-Process 参数 |
| 认证端点 | publicPaths 白名单误放需鉴权端点 |
| Windows 文件操作 | fs.rm 静默失败, 缺 existsSync 验证, 缺路径穿越防护 |
| 多资源并行加载 | for await 串行, Promise.all 单失败全丢, rejected 静默丢弃 |
| 超时链式匹配 | 上层 < 下层×倍数, 硬编码超时, 超时清空已收结果, 无降级路径 |
| 外部 API 契约 | 原生 fetch 无诊断, err.cause.code 未翻译, 单路径访问无 fallback |
| 超时分级 | 统一超时值, 字面量硬编码, 分级语义不匹配, 代理未加宽 |
| 多源密钥 | 只查一个位置, 回退顺序错误, 错误消息不列位置, null 语义不统一 |
| 长任务架构 | 长任务走 SSE, 破坏性端点无限流, 错误码统一 500, 无后端日志 |
| 媒体归档 | 目录不在白名单, 缺必备 frontmatter, UUID 文件名, 业务字段散落正文 |
| 会话存储 | 无淘汰策略, 只 TTL 无 LRU, 返回过期会话, 客户端传内容篡改 |
| SSE 事件分发 | if/else 链, 认知复杂度 > 15, string 泛型, 未知事件静默吞掉 |
| PowerShell 长进程 | pipe 管道连接长时进程, EPIPE 退出码 -1, vue-tsc/orchestrator 管道 |
| 回滚安全 | Write 重写文件恢复代码, 未按删除反向顺序, 缺少类型检查+E2E 验证 |

## Condensed Output Format

When findings exist, use **Template A (Condensed)**. When no issues, use **Template B**.

### Template A (Condensed)

```
# Code Review Summary

## Critical (<X> issues)

### 1. <brief title>

**File:** <path>:<line>
```
<relevant code, max 3 lines>
```

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
```

Rules:
- Omit any section with zero items.
- If any category has 10+ items, summarize as "10+" and show the first 10.
- Keep blank lines between sections for readability.
- If issues require code changes, append: "Would you like me to apply the suggested fix(es)?"

### Template B (No Issues)

```
## Code Review Summary
No issues found.
```

## Usage Notes

- Always include actionable fixes with code snippets when applicable. Rule file examples are in TypeScript / Rust / PowerShell (depending on the rule category).
- Rule Description fields are in Chinese to align with codebase conventions -- keep review explanations consistent.
- Use best-effort File:Line references; fall back to the most specific identifier available.
- When actual file paths differ from config directory mappings, review anyway and note the discrepancy.
- The rules index ([references/.rules-index.md](references/.rules-index.md)) provides trigger keywords and core checks for all rule files. Load full rule files only for matched categories.

## Quick-Check Rules（通用审查规则）

> 命名约定：BR- 前缀表示 Backend Review 规则编号。详细规则见 references/ 下对应文件，参数见 config/review-config.md。
> 历史事故覆盖完整记录见 [references/historical-incidents.md](references/historical-incidents.md)

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

| 规则 | 说明 |
|------|------|
| BR-ASYNC-01 | async 调用必须设置超时，值从配置读取 |
| BR-ASYNC-02 | 事件循环阻塞场景必须用线程级心跳（worker_threads/threading.Thread） |
| BR-ASYNC-03 | 状态文件 ts 字段必须独立于业务事件循环更新 |
| BR-ASYNC-04 | async 调用超时必须提供兜底数据（best_holder 模式） |

### ESM 与模块接线（BR-ESM-01~04）

| 规则 | 说明 |
|------|------|
| BR-ESM-01 | ESM 模式下禁用 __dirname / __filename，必须用 import.meta.url 派生 |
| BR-ESM-02 | 新增 routes/*.ts 必须在入口文件完成 import → instantiate → registerRoute 接线 |
| BR-ESM-03 | 静态分析工具修复建议必须人工验证运行时语义 |
| BR-ESM-04 | 所有 routes/*.ts 暴露的端点必须在入口文件可达 |

### API 响应类型同步（BR-026）

| 规则 | 说明 |
|------|------|
| BR-026-1 | reply.send 返回形状与前端 types.ts interface 字段/类型/可选性一致 |
| BR-026-2 | 后端新增字段前端同步新增，可选字段用 field?: T |

### SSE 事件类型扩展路由同步（BR-027）

| 规则 | 说明 |
|------|------|
| BR-027-1 | SSE 路由 event: <type> 登记在 config 列表，事件类型从 config 读取 |
| BR-027-2 | 新增 SSE 事件类型前端 consumeSSEStream 同步新增 handler，未知事件 console.warn |

### 配置字段 optional 合并非空断言（BR-028）

| 规则 | 说明 |
|------|------|
| BR-028-1 | 配置合并函数访问可选字段禁 field! 断言，用 ?? 或 if 守卫 |
| BR-028-2 | 禁 as T 强转 T \| undefined 为 T，用类型守卫/??/if 处理 |

### EngineAdapter 接口变更实现同步（BR-029）

| 规则 | 说明 |
|------|------|
| BR-029-1 | EngineAdapter 接口变更时所有 implements 类同步实现 |
| BR-029-2 | 禁止 as unknown as / @ts-ignore 绕过 implements 检查 |

### 项目目录结构与文件组织（BR-030~033）

| 规则 | 说明 |
|------|------|
| BR-030 | 源码目录不得混放运行时数据、构建产物及外部工具链 |
| BR-031 | 运行时/构建产物必须在 .gitignore 登记，已跟踪文件 git rm --cached |
| BR-032 | vaultPath 默认值不得指向源码目录，运行时数据外迁到 data/ |
| BR-033 | package.json file: 协议引用验证路径存在性 |

### 配置化参数与持久化边界（BR-034~037）

| 规则 | 说明 |
|------|------|
| BR-034 | 禁止硬编码 API Key/port/path/timeout，从 config 或环境变量注入 |
| BR-035 | 路径解析用三级策略（import.meta.url → process.cwd() → CWD） |
| BR-036 | 写盘后调用 refreshConfigCache(data)，抛错不刷新 |
| BR-037 | 跨 origin 数据后端为权威源，localStorage 仅降级；API key 禁存 localStorage |

### Tauri 构建脚本（BR-038~040）

| 规则 | 说明 |
|------|------|
| BR-038 | 构建脚本含 SPA 构建步骤，用 pnpm --filter <spa> build |
| BR-039 | 构建前清理 services/api/public/ 旧产物，构建后验证 index.html |
| BR-040 | 构建前磁盘空间预检查，不足则中断 |

### Tauri Capability 配置（BR-041~044）

| 规则 | 说明 |
|------|------|
| BR-041 | build.rs 显式声明 AppManifest::commands(...) 注册所有 #[tauri::command] |
| BR-042 | capabilities/default.json permissions 含所有 allow-<command> + core:default |
| BR-043 | 外部 URL 配置 remote.urls 嵌套结构 + core:webview:allow-external-urls |
| BR-044 | tauri.conf.json app.security.capabilities 引用 default |

### PowerShell stderr 处理（BR-045~047）

| 规则 | 说明 |
|------|------|
| BR-045 | 外部工具用 Start-Process -NoNewWindow -Wait -PassThru 包装，禁止直接 & |
| BR-046 | 禁止 2>&1 \| Out-Host 合并流，用 -RedirectStandardError 单独重定向 |
| BR-047 | Stop 模式下外部工具用 Start-Process 避免 stderr 误报 |

### 认证端点分类（BR-048~049）

| 规则 | 说明 |
|------|------|
| BR-048-1 | publicPaths 白名单只能含完全公开端点，需鉴权端点禁止放入 |
| BR-048-2 | 放入白名单导致 preHandler 跳过 token 解析，currentUser 永远 null |
| BR-049-1 | /api/auth/me 必须走正常 token 解析，未登录由 authGuard 返 401 |
| BR-049-2 | publicPaths 配置在认证中间件初始化处集中管理 |

### Windows 文件操作（BR-050~051）

| 规则 | 说明 |
|------|------|
| BR-050-1 | win32 目录删除用 rd /s /q + existsSync 验证，fs.rm/rmSync 作为 fallback |
| BR-050-2 | fallback 仍失败必须抛错，禁止静默返回 ok: true |
| BR-051-1 | 删除后必须 existsSync 验证目录已不存在 |
| BR-051-2 | 路径穿越防护在删除前执行，禁止拼接用户输入到 execSync |

### 多资源并行加载（BR-052）

| 规则 | 说明 |
|------|------|
| BR-052-1 | N 个独立资源 Promise.allSettled 并行，禁止 for await 串行 |
| BR-052-2 | 必须 allSettled 非 all，单失败不阻断 |
| BR-052-3 | rejected 收集到 errors[] 含 source，禁止静默丢弃 |
| BR-052-4 | 资源内子任务可串行，并行聚焦粒度 |
| BR-052-5 | 总超时兜底（Promise.race）防永久挂起 |

### 超时阈值链式匹配（BR-053）

| 规则 | 说明 |
|------|------|
| BR-053-1 | 多层超时自下而上递增，每层 ≥ 下层 × 1.5 |
| BR-053-2 | 超时阈值从 config 读取，禁硬编码 |
| BR-053-3 | 超时保留已收结果（如 SSE 部分答案），禁清空 |
| BR-053-4 | 超时后需降级路径，禁无限等待或 throw |
| BR-053-5 | 阈值变更检查链上所有层，config 标注依赖 |

### 外部 API 集成契约（BR-054）

| 规则 | 说明 |
|------|------|
| BR-054-1 | 外部 API 调用用 fetchWithDiagnostics 包装，翻译 err.cause.code |
| BR-054-2 | 响应字段双重路径兼容（data.url \|\| data.metadata?.url），禁单路径 |
| BR-054-3 | 调用 Go/Rust 后端时 number/boolean 显式 String()/Number()/Boolean() 转换 |
| BR-054-4 | fetchWithDiagnostics export 供单元测试验证 |

### 超时分级策略（BR-055）

| 规则 | 说明 |
|------|------|
| BR-055-1 | 外部 API 按耗时分级设置超时（6 级：task_creation/task_polling/image/video/llm_small/llm_large） |
| BR-055-2 | 超时阈值从 config 读取，禁字面量硬编码 |
| BR-055-3 | 调用类型与超时分级语义匹配，禁混用 |
| BR-055-4 | LLM 调用必须按 tokenBudget 选择 llm_small（4k）或 llm_large（16k） |
| BR-055-5 | HTTPS_PROXY 场景超时考虑 proxy_overhead_ms（20s）加宽 |

### 多源密钥解析（BR-056）

| 规则 | 说明 |
|------|------|
| BR-056-1 | 密钥解析按 dedicated → shared → env 三级回退 |
| BR-056-2 | 回退顺序专用→共享→环境变量，禁调整 |
| BR-056-3 | 回退全缺时错误消息列三个配置位置 |
| BR-056-4 | 每级 null 进入下一级，禁 undefined 或空串 |

### 长/短任务架构分离（BR-057）

| 规则 | 说明 |
|------|------|
| BR-057-1 | 任务耗时 > 30s 走 JSON 端点 + 轮询，禁 SSE 流 |
| BR-057-2 | 破坏性端点配置 rateLimit，≤ 5/min |
| BR-057-3 | 错误码用 message.includes('not configured') 区分 400/500 |
| BR-057-4 | 错误双日志：JSON 响应 + request.log.error(...) |
| BR-057-5 | 路由顶部"设计要点"注释列关键决策 |
| BR-057-6 | 轮询限流匹配 poll_interval_ms（5s），≥ 60/min |

### 媒体归档 frontmatter（BR-058）

| 规则 | 说明 |
|------|------|
| BR-058-1 | 归档目录必须为 vault/queries/，且在 WRITE_ALLOWED_DIRS 白名单 |
| BR-058-2 | 归档 .md 含 type,output_mode,generated_at 三必备字段 |
| BR-058-3 | 文件名匹配 image-YYYYMMDD-HHMMSS.md 格式，禁 UUID |
| BR-058-4 | 业务字段（image_file 等）放 frontmatter |
| BR-058-5 | Marp 归档合并 frontmatter，禁双重 |

### 会话存储双层淘汰（BR-059）

| 规则 | 说明 |
|------|------|
| BR-059-1 | 内存 Map 双层淘汰：先 TTL，超上限按插入顺序淘汰最早 |
| BR-059-2 | 读取时检查 expiresAt，过期删除返回 null |
| BR-059-3 | 归档接口只接受 sessionId/messageIndex，禁接收内容字段 |
| BR-059-4 | trust_client_content=false 时客户端内容忽略，从服务端取 |
| BR-059-5 | 会话写入记录 expiresAt = Date.now() + ttl_ms |

### SSE 事件对象映射分发（BR-060）

| 规则 | 说明 |
|------|------|
| BR-060-1 | 后端 SSE 按 chunk 独立 if 分发，禁 if/else 链 |
| BR-060-2 | 前端事件 ≥ 3 用 Record<string, Handler> 映射表，复杂度 < 15 |
| BR-060-3 | outputMode 用联合字面量类型，禁 string 泛型 |
| BR-060-4 | outputMode 与 outputModes 正交分离 |
| BR-060-5 | 映射表含 default handler，按 warn 处理未知事件 |

### PowerShell 长时进程管道（BR-061）

| 规则 | 说明 |
|------|------|
| BR-061-1 | 长时进程（≥30s）禁止通过 PowerShell 管道（\| Select-String / \| Out-String）运行，EPIPE 风险 |
| BR-061-2 | 需过滤输出时重定向到文件后用 Grep 工具读取 |
| BR-061-3 | 退出码 -1 视为管道断裂而非真实失败，重新直接运行验证 |
| BR-061-4 | vue-tsc 耗时过长（>2min）先清理增量缓存（node_modules/.tmp / tsconfig.tsbuildinfo / node_modules/.vite / src/**/*.js） |

对应编码规范：CODING-059，参见 wiki-code-dev references/powershell-long-process-rule.md。

### 功能回滚最小化（BR-062）

| 规则 | 说明 |
|------|------|
| BR-062-1 | 恢复已删除代码必须按删除反向顺序（import→emit→template→style→parent-binding） |
| BR-062-2 | 回滚必须用 Edit 精准替换，禁止 Write 重写整个文件（编码破坏风险） |
| BR-062-3 | 回滚后必须执行 vue-tsc/tsc 类型检查 + E2E 测试双重验证 |
| BR-062-4 | 部分回滚时用注释明确标注哪些已恢复、哪些保持删除 |

对应编码规范：CODING-060，参见 wiki-code-dev references/rollback-minimal-rule.md。

## Related Skills

| Skill | 协作场景 |
|---|---|
| wiki-code-dev | 审查后发现的问题由 wiki-code-dev 修复 |
| wiki-frontend-code-review | 前端代码审查 |
| obsidian-auto-testing | 审查后验证修复效果 |

## Version History

| 版本 | 日期 | 变更说明 |
|---|---|---|
| v1.7.0 | 2026-07-23 | 新增 BR-048~051 规则（认证端点分类 + Windows 文件操作）。基于「Skill 导入模块开发」任务四维度复盘 |
| v1.8.0 | 2026-07-31 | 新增 BR-052~053 规则（多资源并行加载 + 超时阈值链式匹配）。基于「MCP 并行加载和超时阈值问题」复盘提炼（PL-1~5 / TC-1~5） |
| v1.9.0 | 2026-07-31 | 新增 BR-054~060 规则（外部 API 集成契约 / 超时分级策略 / 多源密钥解析 / 长任务架构分离 / 媒体归档 frontmatter / 会话存储双层淘汰 / SSE 事件对象映射分发）。基于「v3 媒体生成工具开发」四维度复盘，对应 CODING-056~063 |
| v1.10.0 | 2026-07-31 | 新增 BR-061~062 规则（PowerShell 长时进程管道 / 功能回滚最小化）。基于「顶部导航栏→左侧侧栏 + 编码规范提炼」五维度复盘，对应 CODING-059~060 |

> 完整版本历史见 [references/changelog.md](references/changelog.md)

## 参考文档

| 文件 | 内容 |
|------|------|
| [references/historical-incidents.md](references/historical-incidents.md) | 历史事故覆盖（完整记录） |
| [references/changelog.md](references/changelog.md) | 版本历史（完整记录） |
