---
name: wiki-backend-code-review
description: "Review Fastify + TypeScript backend code. Covers SSE streaming, filesystem safety, route design, harness integration, security, error handling, config management, data consistency, session state, route registration guards, null safety, graceful shutdown, sensitive field masking, type sync, config merge preservation, Tauri 2.x build script / capability config / PowerShell stderr handling, multi-resource parallel loading (Promise.allSettled), timeout chain matching (layered timeout coverage), external API contract (fetchWithDiagnostics error code mapping + field fallback + type conversion), timeout tier strategy (task creation / polling / image / video / llm small-large tiers), API key multi-source resolution (dedicated → shared → env fallback chain), long/short task architecture separation (SSE threshold + rate limit + error code classification + dual logging), media archive frontmatter standardization (type/output_mode/generated_at + filename pattern), session store double-layer eviction (TTL + LRU) and tamper-proofing (reference mode), SSE event object mapping dispatch (Record<string, Handler> + outputMode union literal), installer/user-data protection (installer.iss ignoreversion + user data never shipped to {app}, IS_SEA user-data-dir resolution separating resource paths from user-data paths, first-persist clean defaults). All configurable parameters are loaded from config/review-config.md -- no hardcoding in rule files."
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
| Installer & User Data | installer.iss, ignoreversion, {app}, Program Files, IS_SEA, getUserDataDir, getDataDir, LOCALAPPDATA, APPDATA, os.homedir, rebase, clean defaults, machine-absolute, user data dir, getApiDir |
| User Upload Filename | archiveRaw, sanitize, basename, 中文, CJK, 汉字, 全角, 文件名, 上传, wiki-batch, wiki-compile, stripInternalPrefix, internal prefix, originalName |
| Migration / Repair Script | migrate, migration, 迁移, 重写, recover, source:, replace, 批量重命名, recover-title, dry-run, --apply, 脏数据, pageCache |
| SPA Live Deploy | public_live_, resolveSpaRoot, spaRoot, isDeployComplete, .deploy-complete, /wiki/, within-root, path.relative, 时间戳目录, 重启后端 |
| BYOK Per-User Override | llmConfig, searchConfig, toolsConfig, apiKey, applyPerRequestOverride, usercfg::, 400, 缺 apiKey, 覆盖, 服务端共享, 不落盘, 不回显, 纯函数 |
| Test Isolation | indexedDB, localStorage, deleteDatabase, setTimeout(0), vi.clearAllMocks, vi.resetModules, 命名空间, 唯一 userId, fake-indexeddb, onblocked, 异步落盘 |
| SSML / TTS Prosody 注入防护 | prosody, rate, volume, pitch, SSML, express-as, escapeXml, /api/tts/synthesize, 1007, mstts, 注入 |
| 子进程同步边界 | execFile, execFileSync, spawn, child_process, ffmpeg, ffprobe, await, Promise, timeout, 异步当同步 |
| 关键写不吞错 | saveUsers, saveConfig, persistConversation, writeFile, try/catch, ok: true, 落盘, 静默吞错 |
| 文件损坏防护 | loadUsers, readFile, JSON.parse, ENOENT, corrupted, backup, 损坏, .bak, 默认初始化 |
| 类型安全禁用 as any | as any, as unknown as, !., 非空断言, InjectOptions, HTTPMethods, request.method, 类型绕过, @migration |
| 超时可配置化 | setTimeout, AbortSignal.timeout, 30000, 30_000, timeout, fetch, 硬编码, config, edgeTtsTimeoutMs |
| 去除冗余探测 | isFfmpegAvailable, ffprobe, ffmpeg -version, execFileSync, capability, 可用性检测, 探测, probe |
| 归档落盘文件名唯一性 | archive, generateFilename, writeFile, date+shortId, collision, 随机后缀, 覆盖, 静默丢数据, 同日同线程, 派生键 |
| 客户端日期串安全解析 | new Date, toISOString, ts, RangeError, 日期解析, 非法日期, 回退默认, 服务端解析 |
| 整数序号校验 | messageIndex, Number.isInteger, 数组访问, 下标, 非整数, 400, 客户端传索引 |
| Wikilink 注入清洗 | wikilink, [[, refs, replace, trim, 换行, 脏链接, filter(Boolean), 跨行断裂 |
| 创建型写入空内容拒绝 | question, answer, empty, 空串, 创建型写入, 必填字段, 400, no-op, 落盘污染 |
| 归档内容取源解耦 | getSession, threadsPersist, 请求体, 内容解耦, 误报过期, 服务端会话, trust_client_content |
| 编辑重发后端契约 | PUT /api/conversations/:id, body.messages, upsert, merge, append, 全量替换, 幂等, existing.messages, 编辑重发, 悬空答案, removeMessagesFrom |
| 审查范围判定 | frontend/, .vue, frontend/src/stores, Pinia, reactive, IndexedDB 客户端写入, 范围不匹配, 跨技能路由, wiki-frontend-code-review, BR-088 |

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
| 安装器与用户数据 | 安装器 {app} 含用户数据, 程序文件未 ignoreversion, 用户数据路径来自 vaultPath/execPath, 首次落盘固化机器绝对路径 |
| 用户上传文件名 | ASCII 导向清洗把中文变下划线, 内部前缀泄漏到展示名, basename 后缺 `..` 二次校验, 清洗正则硬编码非 config, originalName 缺 `??` 兜底 |
| 迁移/修复脚本 | 默认非 dry-run, 迁移覆盖原文件/无备份, `$1` 字符串拼接污染引用, 边读边写, 同文件重复读取无缓存, 冲突名覆盖 |

## Condensed Output Format

When findings exist, use **Template A (Condensed)**. When no issues, use **Template B**.

### Template A (Condensed)

> **Severity & Scope Legend（与四维度复盘对齐）**
> - **Critical / Suggestion / Nit** 分别对应"阻断合并 / 建议改进 / 吹毛求疵"三级严重度。
> - **Scope（适用边界）**：每条 finding 须标注**适用场景**与**不适用场景**（对应 wiki-code-dev 复盘维度④），避免把噪声当缺陷；跨项目复用规则时须注明本项目适用边界。
> - **Rule link**：标注命中的 BR- 编号与对应 `*-rule.md`，便于回溯"事故 → 规则"来由（见 wiki-code-dev references/retrospective-synthesis.md）。

```
# Code Review Summary

## Critical (<X> issues)

### 1. <brief title>

**File:** <path>:<line>
```
<relevant code, max 3 lines>
```

**Issue:** <one-sentence explanation with rule reference>
**Scope:** 适用：<场景>；不适用：<场景>
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

### 安装器与用户数据（BR-068）

| 规则 | 说明 |
|------|------|
| BR-068-1 | 安装器 `[Files]` 仅含程序文件（exe/public/prompts/node_modules/llm-presets.json/.env.example/图标）且用 `Flags: ignoreversion`；用户数据（config.json/.env/vault/data）绝不出现在 `[Files]` 段、绝不安装到 `{app}`（Program Files） |
| BR-068-2 | 资源路径（getApiDir/getResourcePath/getPromptsDir，随版本更新随 exe 走）与用户数据路径（getUserDataDir/getDataDir/getUserDataPath，跨版本持久随用户走）经不同函数派生；`IS_SEA` 标志统一驱动路径分支 |
| BR-068-3 | 首次落盘 config.json 须回退被 SEA rebase 成机器绝对路径的字段（vaultPath/auth.*/urlCrawl.*/logging.*）为相对/重派生默认值；仅对相对路径字段归一化，尊重用户显式绝对路径 |
| BR-068-4 | 用户数据目录（%LOCALAPPDATA%\KarpathyWiki，回退 APPDATA→HOME）首次运行 `mkdirSync(recursive)` 自建，普通用户可写、不受卸载影响 |

对应编码规范：CODING-PACKAGING-USERDATA，参见 wiki-code-dev references/packaging-userdata-rule.md。

### 用户上传文件名管线（BR-069）

| 规则 | 说明 |
|------|------|
| BR-069-1 | 用户输入作文件名须 Unicode 感知清洗（`/[^\p{L}\p{N}._-]/gu`），禁止 ASCII 导向正则（`/[^\w.-]/`）把中文变下划线 |
| BR-069-2 | 系统内部前缀（`wiki-batch-<ts>-<i>-` / `wiki-compile-<ts>-` / `input-`）须在落盘/展示前剥离（stripInternalPrefix），禁止泄漏到用户可见文件名 |
| BR-069-3 | 清洗后须二次拦截 `..` 路径穿越片段（`/(^\|\/)\.\.(\/\|$)/`）+ `isAbsolute` 检查；仅 `basename` 不足以防御文件名恰为 `..`（与 BR-067 一致） |
| BR-069-4 | 原始文件名经 `CompileInput.originalName?` 透传，后端用 `?? basename` 兜底；前端不消费该内部字段时不得破坏契约（见 FR-066 / BR-026） |

对应编码规范：CODING-USER-UPLOAD-FILENAME，参见 wiki-code-dev references/user-upload-filename-rule.md。

### 数据迁移 / 修复脚本安全（BR-070）

| 规则 | 说明 |
|------|------|
| BR-070-1 | 迁移/修复脚本默认 dry-run，显式 `--apply` 才写盘；先预览后执行 |
| BR-070-2 | 迁移须幂等 + 可恢复：不删原文件（或先备份）、冲突名用 `-2/-3` 后缀而非覆盖 |
| BR-070-3 | 引用改写须函数式替换 `(_, g1) => g1 + newName`，禁止 `"$1" + newName` 字符串拼接（newName 含 `$` 时 `$1` 被当捕获组污染） |
| BR-070-4 | 同一引用页重复读取须用 pageCache / 预读 Map；先全量扫描再批量改写，禁止边读边写 |

对应编码规范：CODING-MIGRATION-SAFETY，参见 wiki-code-dev references/data-repair-script-safety-rule.md。

### SPA 实时部署解析（BR-071）

| 规则 | 说明 |
|------|------|
| BR-071-1 | SPA 托管根目录须从候选（含 `public_live_<ts>` 时间戳目录）中选**数值时间戳最大且通过完整性门禁**的目录，禁止"取第一个存在 index.html 的候选"（扩展 SH-1） |
| BR-071-2 | 选定部署目录前须做完整性门禁（index.html 存在 + 部署完成标记 `.deploy-complete`），禁止选到半写入目录（构建先写 index 再写 hash bundle） |
| BR-071-3 | `/wiki/*` 等静态资源解析须 `path.normalize` + `path.relative(spaRoot, abs)` 做 within-root 校验（逃逸 `..` 即拒绝），与 BR-067 路径穿越防护同一防御纵深 |
| BR-071-4 | 部署须写入**全新时间戳目录**（不覆盖已存在目录，规避 safe-delete 钩子 overwrite 拦截 + 避免清空在服目录）；spaRoot 启动时算一次，写完必须重启后端才生效 |

对应编码规范：CODING-SPA-LIVE-DEPLOY，参见 wiki-code-dev references/spa-live-deploy-rule.md。

### BYOK 多用户配置代理（BR-072）

| 规则 | 说明 |
|------|------|
| BR-072-1 | 每用户配置（provider/baseUrl/apiKey/model）须由前端随请求体带入，后端**不落盘、不回显 GET、不记日志**；服务端不保留用户默认（强制每用户各自配置） |
| BR-072-2 | 缺必需密钥（apiKey 及 provider/baseUrl/model 任一为空）的请求必须返回 **400**，禁止回落到服务端共享密钥（杜绝全员共用额度/互现限流） |
| BR-072-3 | 覆盖逻辑须为**纯函数**（`applyPerRequestOverride`），整体替换须谨慎——空/默认工具配置视为「未提供覆盖」须**回退服务端共享配置**，绝不能把服务端共享 MCP/CLI 清空 |

对应编码规范：CODING-BYOK，参见 wiki-code-dev references/byok-per-user-override-rule.md。

### 隔离测试纪律（BR-073）

| 规则 | 说明 |
|------|------|
| BR-073-1 | 含持久化 / 全局状态的测试用唯一命名空间（userId / 线程 id）隔离，禁止 `beforeEach` 调 `indexedDB.deleteDatabase`（fake-indexeddb + 已开连接会 onblocked / 泄漏） |
| BR-073-2 | 异步落盘断言须多轮 `setTimeout(0)` flush（轮数从 config 读取），避免读到未落盘旧值 |
| BR-073-3 | 后端用例须重置模块态 / mock（`vi.clearAllMocks` / `vi.resetModules`），禁止跨用例共享可变单例 / 模块级缓存 |

对应编码规范：CODING-TEST-ISOLATION，参见 wiki-code-dev references/indexeddb-test-isolation-rule.md。

### SSML / TTS Prosody 注入防护（BR-074）

| 规则 | 说明 |
|------|------|
| BR-074-1 | 来自用户/前端下发的 `rate/volume/pitch` 必须匹配白名单正则（绝对百分比 / 相对倍数 / default）并范围约束，超范围或格式不符须 clamp 到默认或拒绝，禁止原样拼进 `<prosody ...>`（免费端点 `SSML is invalid` / 1007） |
| BR-074-2 | 用户朗读文本在拼入 SSML 前必须转义 `<>&`，禁止破坏 SSML 结构 |
| BR-074-3 | `<mstts:express-as>` 在免费端点不被支持（WebSocket 1007），须剥离或走已配置付费端点；命中 `ssml_injection.forbidden_tags_regex` 即拒绝/剥离 |

对应编码规范：CODING-SSML-INJECTION，参见 wiki-code-dev references/ssml-injection-rule.md（前端 FR-073 为防御纵深）。

### 子进程异步/同步正确性（BR-075）

| 规则 | 说明 |
|------|------|
| BR-075-1 | 在 `async` 函数内若后续逻辑依赖子进程结果（退出码 / stdout / 文件产物），须 `await` 回调/Promise 包装或改用 `execFileSync`（带超时），禁止"调用异步 `execFile` 后不等待就使用结果" |
| BR-075-2 | `execFileSync` 必须设置 `timeout`（从配置读取，禁硬编码字面量），超时须抛错并被上层捕获，禁止 `try/catch` 静默吞掉子进程失败导致下游用残缺产物 |

对应编码规范：CODING-CHILD-PROCESS-SYNC，参见 wiki-code-dev references/child-process-sync-rule.md。

### 关键写不得静默吞错（BR-076）

| 规则 | 说明 |
|------|------|
| BR-076-1 | 关键写（用户 / 配置 / 会话）的 `try/catch` 必须 `throw` 或 `log.error` + `throw`，禁止空 catch 或仅 console 不抛出，调用方借此决定 UI 提示 / 重试 / 降级 |
| BR-076-2 | 若写函数返回 `{ ok: boolean }`，`ok` 必须反映真实写结果——成功才 `true`，任何异常路径不得 `return { ok: true }`，优先直接 `throw` |

对应编码规范：CODING-CRITICAL-WRITE-NO-SWALLOW，参见 wiki-code-dev references/critical-write-no-swallow-rule.md。

### 关键数据文件损坏防护（BR-077）

| 规则 | 说明 |
|------|------|
| BR-077-1 | 读取关键文件须区分"不存在（`ENOENT`）→ 默认初始化"与"内容损坏（`JSON.parse` 抛错）→ `log.error` 告警 + 备份为 `.corrupt-<ts>.bak` + 回退默认"，二者都不得让异常冒泡或静默清零 |
| BR-077-2 | 损坏文件在下次写之前必须重命名备份（`.corrupt-<ts>.bak`），不得原地删除（丢失取证）或放任被写覆盖（原始数据不可恢复） |

对应编码规范：CODING-FILE-CORRUPTION-GUARD，参见 wiki-code-dev references/file-corruption-guard-rule.md。

### 类型安全禁止 `as any` 绕过（BR-078）

| 规则 | 说明 |
|------|------|
| BR-078-1 | 类型来源不明时须从被消费方类型推断（`type Method = InjectOptions['method']`、`import type { HTTPMethods }`）或写类型守卫收窄，禁止 `as any` 把值变成无类型黑洞 |
| BR-078-2 | 确有第三方无类型边界时用 `unknown` 接收 + 局部断言；历史迁移代码若必须 `as any` 须加 `// @migration` 注释并限定作用域，禁止在常驻业务路径长期使用 |

对应编码规范：CODING-TYPE-SAFE-NO-ANY，参见 wiki-code-dev references/type-safe-no-any-rule.md（前端 FR-026 / type-safety-rule 的泛化上位规范）。

### 超时/阈值可配置化（禁止硬编码）（BR-079）

| 规则 | 说明 |
|------|------|
| BR-079-1 | 所有超时 / 阈值须引用配置键（如 `config.edgeTtsTimeoutMs`），禁止在调用处写死 `30000` / `30_000` / `setTimeout(fn, 30000)`，配置键默认值与注释须说明单位与场景 |
| BR-079-2 | 多层调用（前端 → 后端 → 外部 API）各层超时从同一份配置读取且上层 ≥ 下层 × `config_timeout.margin_multiplier`（1.5），禁止各层独立硬编码导致上层先断 |

对应编码规范：CODING-CONFIG-TIMEOUT，参见 wiki-code-dev references/config-timeout-rule.md（扩展 BR-034 配置化边界，与 BR-053/BR-055 协同）。

### 去除冗余探测/探针（BR-080）

| 规则 | 说明 |
|------|------|
| BR-080-1 | 判断工具可用性时调用该工具自身的最小能力检查（如 `ffmpeg -version`），禁止为判断 A 工具而调用 B 工具探测（冗余探针在 B 缺失环境误报 A 不可用且徒增开销） |
| BR-080-2 | 能力检测失败（工具不存在）须返回 `false` 并由调用方降级（跳过后处理 / 提示用户），禁止让探测异常冒泡中断主流程 |

对应编码规范：CODING-NO-REDUNDANT-PROBE，参见 wiki-code-dev references/no-redundant-probe-rule.md。

### 归档落盘文件名唯一性（BR-081）

| 规则 | 说明 |
|------|------|
| BR-081-1 | 落盘文件名若由分组键（日期+shortId 等）派生，**非全局唯一**，须追加随机后缀后再落盘（`generated_filename.collision_suffix_len` 配置长度），禁止直接以派生键命名（同日同线程多条归档互相覆盖静默丢数据） |
| BR-081-2 | 即便追加后缀，仍须做存在性/哈希碰撞校验，冲突即重生成或拒绝，禁止覆盖已存在文件（与 BR-067/BR-071-4 同一防御纵深） |

对应编码规范：CODING-GENERATED-FILENAME-UNIQUENESS，参见 wiki-code-dev references/generated-filename-uniqueness-rule.md。

### 服务端解析客户端日期串安全（BR-082）

| 规则 | 说明 |
|------|------|
| BR-082-1 | 服务端解析客户端传入日期串**禁止** `new Date(str).toISOString()`（非法串抛 RangeError 致全链路 500），须用安全解析覆盖 null/未定义/非字符串/无效日期 |
| BR-082-2 | 解析失败统一回退 `safe_date_parse.default_value`（默认 null），不得让异常冒泡，缺失字段亦不得抛错 |

对应编码规范：CODING-SAFE-CLIENT-DATE-PARSE，参见 wiki-code-dev references/safe-client-date-parse-rule.md。

### 客户端整数序号校验（BR-083）

| 规则 | 说明 |
|------|------|
| BR-083-1 | 客户端传下标（`messageIndex` 等）访问数组前，须 `Number.isInteger` 校验，非法/缺失即返回 `integer_index.reject_status`（400），校验须在数组访问前短路 |
| BR-083-2 | 禁止把非整数当下标导致 `arr[undefined]` 访问 → 下游 undefined 解构/属性读取 500 |

对应编码规范：CODING-INTEGER-INDEX-VALIDATION，参见 wiki-code-dev references/integer-index-validation-rule.md。

### Wikilink 注入清洗（BR-084）

| 规则 | 说明 |
|------|------|
| BR-084-1 | 注入 `[[wikilink]]` / Markdown 链接前须规范化：去换行（`replace(/[\r\n]/g,' ')`）、`trim()`、`filter(Boolean)` 去空串，禁止换行跨行断裂与 `[[ ]]` 脏链接 |
| BR-084-2 | 依 `wikilink.extra_clean_regex` 额外清洗破坏字符（`]`/`\|` 等），字符集从 config 读取，规则文件零硬编码 |

对应编码规范：CODING-WIKILINK-SANITIZATION，参见 wiki-code-dev references/wikilink-sanitization-rule.md（建议级）。

### 创建型写入空内容拒绝（BR-085）

| 规则 | 说明 |
|------|------|
| BR-085-1 | 创建型写入端点（归档/落盘）须在写入前校验必填字段（`empty_content.required_fields`，如 question/answer）：同时缺失或空串即返回 `empty_content.reject_status`（400） |
| BR-085-2 | 纯空白视为空串（`empty_content.treat_whitespace_as_empty`），禁止空内容 no-op 落盘污染知识库 |

对应编码规范：CODING-EMPTY-CONTENT-REJECTION，参见 wiki-code-dev references/empty-content-rejection-rule.md。

### 归档内容取源解耦（BR-086）

| 规则 | 说明 |
|------|------|
| BR-086-1 | 归档内容**优先从请求体取**，仅请求体缺失时回退 `getSession`；在 `threadsPersist=false`（默认）部署下，依赖服务端会话恒为空 → 100% "已过期"误报，须解耦 |
| BR-086-2 | 不得擅自开启 `persist`（threadsPersist=true）以绕过解耦；取源解耦后前端能力门控须随后端契约同步放宽（与 FR-076 同一变更闭环，防两端漂移） |

对应编码规范：CODING-PERSISTENCE-CLIENT-CONTENT-DECOUPLING / CODING-CAPABILITY-GATING-SYNC，参见 wiki-code-dev references/persistence-client-content-decoupling-rule.md · references/capability-gating-sync-rule.md。

### 编辑重发后端会话落盘契约（BR-087）

| 规则 | 说明 |
|------|------|
| BR-087-1 | 会话 upsert 端点（PUT /api/conversations/:id）须将 `body.messages` 视为**权威全量替换（幂等）**，禁止与服务端既有 `messages` 做 merge / append；前端「编辑重发」是 trim 尾随 AI 答案 + 重新插入用户消息后整体重发，服务端若 merge/append 会让被裁掉的悬空答案复活（对应前端 FR-077 / CODING-EDIT-RESEND 后端侧） |
| BR-087-2 | upsert 仅保留服务端特有元数据（createdAt / threadId 透传等），消息体以请求体为唯一来源；`body.messages` 缺失时回退空数组 `[]` 而非 `existing.messages`，避免脏数据/被裁答案复活 |
| BR-087-3 | 并发 / 重试场景须以请求体 messages 为最终态（最后一次写覆盖），不得因服务端缓存的中间态产生消息重复或错位 |

对应编码规范：CODING-EDIT-RESEND，参见 wiki-code-dev references/edit-resend-rule.md；前端侧规则 FR-077（wiki-frontend-code-review）。

### 审查范围判定（BR-088）

> 后端审查技能的适用范围是 Fastify/TS 后端（routes / services / 引擎 / 配置 / 文件系统 / SSE）。跨端规则（BYOK、会话隔离、流式续答、隔离测试、编辑重发、IndexedDB 响应式代理剥离）前后端各有对应 BR-/FR- 编号，须按文件位置选对应技能核，避免范围误配与双重复核。

| 规则 | 说明 |
|------|------|
| BR-088-1 | 待审变更**完全是前端**（`.vue` / `frontend/src/stores/*.ts` / 客户端 IndexedDB 写入 / Pinia reactive 代理剥离）时，须声明范围不匹配并建议切换到 wiki-frontend-code-review，禁止硬套后端规则（如把前端 reactive-proxy-in-IDB 静默丢配置当作后端关键写问题套用 BR-076）——该坑的归属规则是前端 FR-081 / wiki-code-dev CODING-IDB-REACTIVE-CLONE |
| BR-088-2 | 跨端规则（BYOK / 会话隔离 / 流式续答 / 隔离测试 / 编辑重发 / IDB reactive-clone）须以"该规则归属的技能"为准：后端侧规则在后端代码上核、前端侧规则在前端代码上核；同一规则前后端都有对应编号时按文件位置选其一，不双重复核 |
| BR-088-3 | pending-change 模式先按 `git diff --name-only` 的文件位置判定主技能（`frontend/` 下 → 前端；`services/api/` 下 → 后端）；混合变更两端技能各审各的，输出分别标注 |

对应 wiki-code-dev 复盘维度④（适用 / 不适用边界）：每条规则都有适用场景与不适用场景，跨技能复用规则时须注明本项目/本端适用边界。

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
| v2.1.0 | 2026-08-05 | 新增 BR-068 规则（安装器与用户数据保护）：安装器 ignoreversion + 用户数据绝不打包到 {app}；IS_SEA 用户数据目录解析（资源路径 vs 用户数据路径分离）；首次落盘干净默认。校正 review-config.md 中 `config_portable_defaults.user_data_dir_anchor` 为真实实现 `%LOCALAPPDATA%\KarpathyWiki`。对应 wiki-code-dev CODING-PACKAGING-USERDATA。 |
| v2.2.0 | 2026-08-05 | 新增 BR-069（用户上传文件名管线）：Unicode 感知清洗（中文不被变下划线）+ 内部前缀剥离（wiki-batch-/wiki-compile-/input-）+ 清洗后 `..`/`isAbsolute` 二次校验（与 BR-067 一致）+ originalName? 透传 `??` 兜底；新增 BR-070（数据迁移/修复脚本安全）：dry-run 默认、幂等可恢复、冲突后缀、函数式 `$` 替换、pageCache 两阶段。基于「raw 文件名修复 + 走查建议优化」四维度复盘，对应 wiki-code-dev CODING-USER-UPLOAD-FILENAME / CODING-MIGRATION-SAFETY。 |
| v2.3.0 | 2026-08-06 | 新增 BR-071（SPA 实时部署解析）：托管根目录须从候选（含 `public_live_<ts>` 时间戳目录）中选数值时间戳最大且通过完整性门禁的目录（扩展 SH-1）；完整性门禁为 index.html + `.deploy-complete` 标记（禁选半写入目录）；`/wiki/*` 静态资源须 normalize + within-root 校验（与 BR-067 同一防御纵深）；部署须写全新时间戳目录不覆盖已存在目录（规避 safe-delete 钩子）、写完须重启后端。基于「/wiki/* 路径穿越加固 + 实时部署解析」复盘，对应 wiki-code-dev CODING-SPA-LIVE-DEPLOY。 |
| v2.4.0 | 2026-08-07 | 新增 BR-072（BYOK 多用户配置代理）：每用户配置（provider/baseUrl/apiKey/model）须由前端随请求体带入，后端不落盘/不回显 GET/不记日志、且不保留用户默认（BR-072-1）；缺必需密钥的请求必须 400、禁止回落服务端共享密钥（BR-072-2）；覆盖须为纯函数 `applyPerRequestOverride`，空/默认工具配置须回退服务端共享配置、不得清空（BR-072-3）。基于「BYOK 多用户密钥代理」复盘，对应 wiki-code-dev CODING-BYOK。 |
| v2.5.0 | 2026-08-08 | 新增 BR-073（隔离测试纪律）：含状态测试用唯一命名空间隔离、禁止 `beforeEach(indexedDB.deleteDatabase)`（fake-indexeddb + 已开连接会 onblocked/泄漏，BR-073-1）；异步落盘断言须多轮 `setTimeout(0)` flush（BR-073-2）；后端用例须重置模块态/mock 禁止跨用例共享可变单例（BR-073-3）。Feature Scan 表新增 Test Isolation 触发词，Quick-Check Rules 新增 BR-073 段，config/review-config.md 追加 test_isolation_backend 参数段。对应 wiki-code-dev CODING-TEST-ISOLATION，基于「隔离测试 flaky（fake-indexeddb 删库陷阱）」复盘，与 wiki-auto-testing `indexeddb_test_isolation_check` 参数对齐。 |
| v2.6.0 | 2026-08-07 | 新增 BR-074~080 规则（SSML/TTS Prosody 注入防护 / 子进程异步同步正确性 / 关键写不静默吞错 / 关键数据文件损坏防护 / 类型安全禁用 as any / 超时阈值可配置化 / 去除冗余探测）。Feature Scan 表新增 7 类触发词，Quick-Check Rules 追加 BR-074~080 段，config/review-config.md 追加 7 组参数段（ssml_injection / child_process_sync / critical_write_no_swallow / file_corruption_guard / type_safe_no_any / config_timeout / no_redundant_probe）。基于「TTS 端点 + 音频后处理 + 用户存储 + 类型/buffer/探测」系统性复盘，对应 wiki-code-dev CODING-SSML-INJECTION / CODING-CHILD-PROCESS-SYNC / CODING-CRITICAL-WRITE-NO-SWALLOW / CODING-FILE-CORRUPTION-GUARD / CODING-TYPE-SAFE-NO-ANY / CODING-CONFIG-TIMEOUT / CODING-NO-REDUNDANT-PROBE。 |
| v2.7.0 | 2026-08-08 | 新增 BR-081~086 规则（归档落盘文件名唯一性 / 客户端日期串安全解析 / 整数序号校验 / Wikilink 注入清洗 / 创建型写入空内容拒绝 / 归档内容取源解耦）。Feature Scan 表新增 6 类触发词，Quick-Check Rules 追加 BR-081~086 段，config/review-config.md 追加 6 组参数段（generated_filename / safe_date_parse / integer_index / wikilink / empty_content / persistence_client_content）。基于「归档路由重构」四维度复盘（文件名碰撞静默丢数据 / 非法 ts → RangeError 500 / 非整数 messageIndex → undefined 访问 500 / refs 换行破坏 wikilink / 空内容 no-op 落盘 / 依赖服务端会话 100% 误报过期），对应 wiki-code-dev CODING-GENERATED-FILENAME-UNIQUENESS / CODING-SAFE-CLIENT-DATE-PARSE / CODING-INTEGER-INDEX-VALIDATION / CODING-WIKILINK-SANITIZATION / CODING-EMPTY-CONTENT-REJECTION / CODING-PERSISTENCE-CLIENT-CONTENT-DECOUPLING（前端门控同步见 FR-076）。 |
| v2.8.0 | 2026-08-08 | 新增 BR-087（编辑重发后端会话落盘契约）：会话 upsert 端点（PUT /api/conversations/:id）须将 `body.messages` 视为权威全量替换（幂等），禁止与服务端既有 messages 做 merge/append（BR-087-1）；upsert 仅保留服务端特有元数据、消息体以请求体为唯一来源、缺失回退 `[]` 而非 `existing.messages`（BR-087-2）；并发/重试以请求体 messages 为最终态（BR-087-3）。基于「编辑后重新发送」复盘——前端 trim 尾随 AI 答案 + 重新插入用户消息整体重发（FR-077 / CODING-EDIT-RESEND），服务端若 append 会让被裁悬空答案复活。Feature Scan 表新增 Edit-Resend 触发词，Quick-Check Rules 追加 BR-087 段，config/review-config.md 追加 conversation_upsert_contract 参数段。对应 wiki-code-dev CODING-EDIT-RESEND 后端侧。 |
| v2.9.0 | 2026-08-08 | 新增 BR-088（审查范围判定）：待审变更完全是前端（`.vue` / `frontend/src/stores/*.ts` / 客户端 IndexedDB 写入 / Pinia reactive 代理剥离）时须声明范围不匹配并建议切到 wiki-frontend-code-review，禁止硬套后端规则（如把前端 reactive-proxy-in-IDB 静默丢配置误当后端关键写问题，归属应为前端 FR-081 / CODING-IDB-REACTIVE-CLONE）（BR-088-1）；跨端规则按文件位置选对应技能核、不双重复核（BR-088-2）；pending-change 先按 `git diff --name-only` 文件位置判定主技能（BR-088-3）。Feature Scan 表新增「审查范围判定」触发词，Quick-Check Rules 追加 BR-088 段。对齐 wiki-code-dev 复盘维度④（适用 / 不适用边界），并明确本次「输入框隔离设置」改动属纯前端、应由前端技能评审。 |

> 完整版本历史见 [references/changelog.md](references/changelog.md)

## 参考文档

| 文件 | 内容 |
|------|------|
| [references/historical-incidents.md](references/historical-incidents.md) | 历史事故覆盖（完整记录） |
| [references/changelog.md](references/changelog.md) | 版本历史（完整记录） |
