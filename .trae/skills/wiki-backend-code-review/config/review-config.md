# Review Configuration — wiki-backend-code-review

评审参数集中管理。规则文件不硬编码目录名、阈值或事件名，一切可配置项从本文件读取。

## 技术栈

- Runtime: Node.js (LTS) · Framework: Fastify 4.x · Language: TypeScript (ES2022, ESM) · 模块: ESM（禁止 require） · 异步: async/await + Streams

## 项目目录映射

| 逻辑角色 | 目录约定 | 说明 |
|---------|---------|------|
| HTTP 路由层 | `api/src/routes/` | Fastify 路由注册 |
| 工作流编排 | `api/src/workflows/` | engine adapter + hook + 预算控制 |
| 引擎适配器 | `api/src/engine/` | `EngineAdapter` 接口实现 |
| Vault 文件系统 | `api/src/vault/` | Vault 读写、追加、状态持久化 |
| Prompt 存储 | `prompts/` | 模板单点存放，禁止内联到 .ts |
| 状态持久化 | `api/src/state/` | `FileStateStore`，runId 索引 |
| 共享工具 | `api/src/utils/` | 通用 helper |

> 实际路径与映射不符时以实际路径为准并在报告中标注差异。

## SSE 事件格式约定

- 分隔符 `\n\n`，格式 `event: <type>\ndata: <json-string>\n\n`
- 必备事件：`progress`、`result`、`error`、`done`
- JSON payload 须单行 `JSON.stringify`，禁止多行美化

## 并发控制阈值

| 场景 | 阈值/策略 | 说明 |
|------|----------|------|
| index.md / log.md 追加 | 串行化（`withCompileLock`） | 防并发交错 |
| 单进程内 SSE 连接 | 不限硬上限，须 finally 收尾 | 避免连接泄漏 |
| 引擎调用预算 | `EngineAdapter` 配置注入 | 耗尽返回 `budget_exceeded` |
| 文件锁等待超时 | `FileStateStore` 配置注入 | 超时降级 |

> 具体数值由运行时配置注入，评审只校验"是否使用对应机制"。

## 路径遍历防护

用户可控输入须正则白名单校验后拼接路径。UUID: `/^[a-fA-F0-9-]{36}$/`；文件名: `/^[A-Za-z0-9._-]+$/`。禁止 `..` 相对路径、绝对路径、null byte/换行符。拼接后须 `path.resolve` + `startsWith` 检查。

## Vault 写入白名单 / 临时文件

- 可写：指定工作目录、`index.md`、`log.md`、`drafts/`、`attachments/`
- 禁止修改 `SCHEMA.md`，禁止删除已归档目录
- 部分失败不回滚，标记 `draft` 保留半成品
- 临时文件根 `os.tmpdir()`，命名 `{runId}-{Date.now()}`，finally 中 `fs.promises.unlink`

## 配置项管理规范

所有可配置参数必须通过 config 注入，禁止硬编码。

| 参数类别 | 示例 | 注入方式 |
|----------|------|----------|
| API Key | `OPENAI_API_KEY` | 环境变量，config 存 `apiKeyRef` |
| 端口/地址 | `port: 3000`, `host: '127.0.0.1'` | config 文件 |
| 超时/预算 | token 预算、锁超时 | config 文件 |
| 文件路径 | vaultRoot、stateDir、promptsDir | config 文件 |
| 并发控制 | `withCompileLock` 锁 Map | 运行时注入 |
| SSE 事件类型 | `progress`/`result`/`error`/`done` | 本文件约定 |
| 白名单 | 命令、可写目录 | config 文件 |

检测：搜索 `process.env.`、`app.listen(`、`path.join(`、`new Set([` 确认通过 config 引用。

## 配置管理审查参数

| 动作 | 方法 + 路径 | 说明 |
|------|------------|------|
| 读取 | `GET /api/{module}/config` | 返回当前配置 |
| 保存 | `PUT /api/{module}/config` | 持久化并同步运行时 |
| 恢复 | `POST /api/{module}/reset-config` | 重置到默认值并同步 |
| 测试 | `POST /api/{module}/test-connection` | 连通性测试 |

四类接口须同时注册，缺失视为生命周期不完整。恢复须调用 `adapter.updateConfig()` 同步 `provider`/`baseUrl`/`model`/`apiKey`。

| 预设类别 | 集中位置 | 导出常量 |
|----------|---------|---------|
| LLM 预设 | `api/src/routes/ai.ts` | `LLM_PRESETS` |

预设 ID：openai / deepseek / zhipu / moonshot / qwen / ernie / doubao / agnes / ollama

密钥：全局 `openai_api_key` / `embedding_api_key`；预设独立 `openai_api_key_preset_{preset_id}`；脱敏前缀 `****`。热更新须原子化（先读后写，失败回滚），更新后验证可加载，记录 before/after 快照。

## Session State & Cache Management

子进程写入后父进程须 `invalidate_cache()` 再读取；JSON 读取前须 `invalidate_cache()`。缓存 TTL 默认 30s。`export_cookies()` 后须 `sync_cookie_layers_from_json()`。Cookie 变更推送 worker，身份变更强制刷新 token。会话检查：缺失、过期、陈旧。

## 持久化与缓存刷新审查参数

| 场景 | 解析方式 | 说明 |
|------|---------|------|
| 开发模式 | `path.dirname(fileURLToPath(import.meta.url))` | 不受 CWD 影响 |
| 打包模式 | `path.resolve(process.cwd(), CONFIG_FILENAME)` | CWD 兜底 |
| 通用兜底 | 候选路径 + `fsSync.accessSync` 探测 | 按优先级 |

禁止 `process.cwd()` 作为唯一锚点，须"import.meta.url + 打包兜底 + CWD 探测"三级策略。

| 写盘函数 | 刷新方法 | 刷新内容 |
|---------|---------|---------|
| `saveAiConfig()` | `refreshConfigCache(data)` | `configCache.data`/`.path`/`.loadedAt` |
| `resetAiConfig()` | `refreshConfigCache(data)` | 同上 |
| `saveWebSearchConfig()` | `refreshConfigCache(data)` | 同上 |
| 通用模板 | `refresh<Module>Cache(data)` | 写盘后立即同步 |

`fs.writeFile` 成功后、`return reply` 前须调用刷新。TTL 不替代显式刷新。`fs.writeFile` 失败时不刷新（保持旧值），返回 5xx。

| 用途 | 正则 | 说明 |
|------|------|------|
| 资源 ID | `/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i` | UUID v4 |
| 文件名段 | `/^[A-Za-z0-9._-]+$/` | 字母/数字/下划线/短横线/点 |
| 路径段 | `/^[A-Za-z0-9_][A-Za-z0-9._-]*$/` | 禁止 `.` 开头 |

HTTP 请求参数用作路径时须用上表校验。正则视为配置项，禁止内联硬编码。

| 数据类型 | 落盘目录 | 文件命名 | 格式 |
|---------|---------|---------|------|
| AI 配置 | `api/config.json` | 固定 | JSON |
| 历史会话 | `data/conversations/` | `{uuid}.json` | JSON |
| 运行状态 | `api/src/state/` | runId 索引 | `FileStateStore` |
| 临时文件 | `os.tmpdir()` | `{runId}-{timestamp}` | 任意 |

落盘目录须通过配置项或 `import.meta.url` 解析，禁止硬编码绝对路径。`.gitignore` 须排除运行期写入目录。

| 数据类型 | 浏览器存储 | 后端权威源 | 跨 origin |
|---------|-----------|-----------|----------|
| AI 配置（apiKey） | localStorage（脱敏） | `/api/ai/config` + `api/config.json` | 是 |
| 历史会话 | IndexedDB（降级） | `/api/conversations/:id` + `data/conversations/` | 是 |
| LLM 预设 UI | localStorage | 无 | 否 |
| 主题偏好 | localStorage | 无 | 否 |

跨 origin 列为"是"的数据后端须 CRUD 路由，降级时须 `console.warn`。

## 编码安全 / 清理审计 / 批量错误 / 路由注册 审查参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `source_encoding_required` | `utf-8-no-bom` | 源文件编码 |
| `config_encoding_required` | `utf-8-no-bom` | 配置文件编码 |
| `encoding_detection` | `utf8-strict-decode` | 检测方法 |
| `encoding_scan_scope` | `.ts,.json,.md` | 扫描范围 |
| `fffd_indicator` | `U+FFFD` | 乱码指示 |
| `ascii_whitelist` | `true` | ASCII 免检 |
| `audit_log_format` | `jsonl` | 审计日志格式 |
| `audit_log_path` | `.harness/cleanup-audit.log` | 日志路径 |
| `audit_failure_action` | `non-blocking` | 审计失败不阻塞 |
| `days_min_value` | `1` | days 下限 |
| `days_protection` | `Math.max(min, input)` | 下限保护 |
| `dry_run_default` | `true` | dry_run 默认 |
| `single_item_error_collection` | `errors[]` | 单子项错误收集 |
| `refresh_after_execute` | `true` | 执行后刷新 |
| `single_item_try_catch` | `true` | 单子项独立 try-catch |
| `error_collection_field` | `errors` | 错误收集字段 |
| `main_flow_catch` | `fatal-only` | 主流程仅致命错误 |
| `audit_write_catch` | `independent` | 审计写入独立 try |
| `route_directory` | `api/src/routes/` | 路由目录 |
| `entry_file` | `api/src/index.ts` | 入口文件 |
| `register_function_pattern` | `register` | 注册函数模式 |
| `exempt_files` | `["_types.ts", "_shared.ts", "index.ts"]` | 豁免文件 |

## 空值守卫 / 优雅停止 / 敏感脱敏 / 类型同步 / 配置合并 审查参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `nullable_field_patterns` | `this\.provider\|this\.child\|this\.connection\|this\.client\|this\.handle` | 可空字段模式 |
| `async_assignment_keywords` | `spawn\|exec\|connect\|listen\|createClient\|open` | 异步赋值关键词 |
| `resource_keywords` | `spawn\|setInterval\|connect\|listen\|createClient\|open` | 资源创建关键词 |
| `shutdown_signals` | `["SIGINT", "SIGTERM"]` | 清理信号 |
| `cleanup_order` | `["child_process", "timer", "connection"]` | 清理顺序 |
| `sensitive_field_patterns` | `key\|token\|secret\|password\|authtoken\|apiKey\|apiSecret` | 敏感字段模式 |
| `mask_strategy` | `last4_padstart` | 脱敏策略 |
| `empty_string_semantics` | `no_change` | 空串不修改原值 |
| `backend_types_path` | `api/src/types.ts` | 后端 types 路径 |
| `frontend_types_path` | `frontend/src/types.ts` | 前端 types 路径 |
| `sync_interfaces` | `[]` | 需同步接口（留空=全部） |
| `config_file_path` | `api/config.json` | 配置文件路径 |
| `merge_strategy` | `shallow` | 合并策略 |
| `preserve_sections` | `[]` | 保留段名 |
| `exempt_paths` | `["*.tmp.json", "*.cache.json"]` | 豁免文件 |

## 检查更新 / SPA 托管 / 综合审查 参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `check_update.cache_ttl_ms` | `300000` | 缓存 TTL（5 分钟） |
| `check_update.offline_mode` | `true` | 离线模式 |
| `check_update.update_endpoint` | `/api/about/check-update` | 更新接口 |
| `check_update.external_api_timeout_ms` | `10000` | 外部 API 超时 |
| `check_update.github_api_url_template` | `https://api.github.com/repos/{owner}/{repo}/releases/latest` | API URL 模板 |
| `check_update.required_response_fields` | `has_update, current_version, latest_version, release_url, source, checked_at` | 必需响应字段 |
| `check_update.fallback_source` | `local` | 降级 source |
| `check_update.cache_invalidation_on_error` | `false` | 失败是否刷新缓存 |
| `spa_static_hosting.enabled` | `true` | 是否启用 |
| `spa_static_hosting.severity` | `error` | 违规级别 |
| `spa_static_hosting.required_candidate_paths` | `2` | 候选路径最少数量 |
| `spa_static_hosting.candidate_path_templates` | `cwd/public, dirname/../public, dirname/../static/spa` | 候选路径 |
| `spa_static_hosting.build_output_dir` | `api/public` | 构建输出目录 |
| `spa_static_hosting.empty_out_dir_required` | `true` | 须 emptyOutDir |
| `spa_static_hosting.spa_fallback_required` | `true` | 须 SPA fallback |
| `spa_static_hosting.fallback_file` | `index.html` | fallback 文件 |
| `spa_static_hosting.api_path_exclusion` | `/api/, /assets/` | 不触发 fallback 前缀 |
| `spa_static_hosting.watch_reload_required` | `true` | watch 后须重启 |
| `spa_static_hosting.health_check_endpoint` | `/api/ai/config` | 健康检查端点 |
| `spa_live_deploy.enabled` | `true` | 启用实时部署解析审查（BR-071） |
| `spa_live_deploy.public_base_dir` | `api` | 部署目录基准父目录（相对 cwd） |
| `spa_live_deploy.live_dir_pattern` | `public_live_` | 时间戳部署目录前缀（后接数值时间戳） |
| `spa_live_deploy.legacy_dir` | `public` | 兜底固定目录（新目录完整性失败时回退） |
| `spa_live_deploy.quarantine_keyword` | `quarantine` | 排除关键字（隔离目录不参与候选） |
| `spa_live_deploy.complete_marker` | `.deploy-complete` | 完整性门禁标记文件名（最后写） |
| `spa_live_deploy.sort_order` | `desc` | 候选按数值时间戳降序（最新在前） |
| `spa_live_deploy.asset_prefix` | `/wiki/` | 需 within-root 防穿越的静态资源前缀 |
| `spa_live_deploy.require_within_root` | `true` | 资源解析须 normalize + path.relative 逃逸拦截 |
| `spa_live_deploy.require_restart` | `true` | 部署新目录后必须重启后端才生效 |
| `severity_critical` | `🔴 严重` | 必须修复，阻止合并 |
| `severity_warning` | `🟡 警告` | 建议修复 |
| `severity_suggestion` | `🟢 建议` | 可选优化 |
| `severity_positive` | `✅ 优点` | 正面反馈 |
| `config_read_entries` | `startup,hot_reload,api_get,api_test` | 配置读取入口 |
| `required_unified_functions` | `getEffectiveApiKey,loadConfig` | 统一调用函数 |
| `forbidden_direct_read` | `process.env[config.llm` | 禁止直接读取 |
| `hot_update_required` | `true` | 须实现 updateConfig |
| `hot_update_chain` | `save→persist→updateConfig→response` | 闭环流程 |
| `hot_update_methods` | `updateConfig` | 热更新方法 |
| `hot_update_call_required` | `true` | 路由层须调用 |
| `layer_order` | `routes→workflows→engine→vault` | 分层顺序 |
| `cross_layer_call_forbidden` | `routes→vault` | 禁止跨层 |
| `dependency_direction` | `outer→inner` | 依赖方向 |
| `max_issues_per_section` | `10` | 每节最多输出 |
| `include_code_snippet` | `true` | 含代码片段 |
| `include_rule_reference` | `true` | 含规则引用 |
| `suggest_fix_code` | `true` | 修复代码示例 |

> SPA 托管适用：单端口 + Vite/webpack + Fastify/Express。多端口、SSR、Next.js/Nuxt.js 不适用。

## ESM / Async / 适用场景 审查参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `esm_forbidden_globals` | `__dirname,__filename` | ESM 禁用全局变量 |
| `esm_dirname_derive_pattern` | `path.dirname(fileURLToPath(import.meta.url))` | dirname 派生 |
| `esm_required_imports` | `path,fileURLToPath` | 必需 import |
| `wiring_required_steps` | `import,instantiate,registerRoute` | 接线三步骤 |
| `wiring_entry_file` | `api/src/index.ts` | 接线入口 |
| `route_register_pattern` | `registerXxxRoute(app, ...)` | 注册命名 |
| `static_analysis_tools` | `SonarQube,ESLint` | 分析工具 |
| `static_analysis_verify_checklist` | `operand_throws_on_reference,type_guard_bypassed,side_effect_changed` | 验证清单 |
| `endpoint_reachability_check` | `curl /api/<module>/<action>` | 端点验证 |
| `async_default_call_timeout_sec` | `5.0` | 单次超时（秒） |
| `async_stage_hard_timeout_sec` | `30.0` | 阶段超时 |
| `async_task_total_timeout_sec` | `180.0` | 任务超时 |
| `async_heartbeat_interval_sec` | `3.0` | 心跳间隔 |
| `async_heartbeat_max_interval_sec` | `10.0` | 心跳最大间隔 |
| `async_thread_join_timeout_sec` | `5.0` | 线程 join 超时 |
| `async_status_file_update_strategy` | `thread` | 状态更新策略 |
| `async_fallback_data_pattern` | `best_holder` | 兜底模式 |
| `async_timeout_whitelist` | `asyncio.sleep,Promise.resolve` | 超时豁免 |
| `async_blocking_risk_apis` | `playwright.context.cookies,playwright.context.storage_state,playwright.context.unroute,playwright.page.goto,playwright.page.wait_for_load_state,node_fetch,fs.promises.readFile,child_process.exec` | 阻塞风险 API |
| `async_heartbeat_impl_required` | `threading.Thread` | 心跳方式 |
| `async_heartbeat_forbidden_impl` | `asyncio.Task,Promise.then` | 心跳禁止方式 |

适用：`api/` 下 Fastify 路由、workflow、engine adapter、vault、state store；SSE；配置持久化、缓存刷新。不适用：前端代码、纯 prompt、Vault 内容语义、构建/CI 脚本（安全相关除外）。

## API 响应类型 / SSE 事件 / Optional 合并 / EngineAdapter 审查参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `api_response_type_sync.enabled` | `true` | 启用 |
| `api_response_type_sync.severity` | `critical` | 严重级别 |
| `api_response_type_sync.backend_routes_directory` | `api/src/routes/` | 路由目录 |
| `api_response_type_sync.frontend_types_path` | `frontend/src/types.ts` | 前端 types |
| `api_response_type_sync.backend_types_path` | `api/src/types.ts` | 后端 types |
| `api_response_type_sync.reply_send_pattern` | `reply\.send\|return reply\.` | reply.send 模式 |
| `api_response_type_sync.monorepo_import_type_exempt` | `true` | monorepo 豁免 |
| `sse_event_type_route.enabled` | `true` | 启用 |
| `sse_event_type_route.severity` | `critical` | 严重级别 |
| `sse_event_type_route.sse_event_types_config_field` | `sse.event_types` | 事件类型字段 |
| `sse_event_type_route.required_event_types` | `progress,result,error,done` | 必备事件 |
| `sse_event_type_route.backend_sse_routes_directory` | `api/src/routes/` | SSE 路由目录 |
| `sse_event_type_route.event_pattern` | `event:\s*\w+` | 事件匹配 |
| `sse_event_type_route.frontend_sse_consumer_path` | `frontend/src/lib/sse.ts` | 前端消费路径 |
| `sse_event_type_route.unknown_event_strategy` | `warn` | 未知事件策略 |
| `optional_merge.enabled` | `true` | 启用 |
| `optional_merge.severity` | `suggestion` | 严重级别 |
| `optional_merge.config_merge_function_patterns` | `updateConfig,mergeConfig,mergeConfigSection,saveAiConfig,saveConfig` | 合并函数模式 |
| `optional_merge.forbidden_assertion_operators` | `!,as` | 禁止操作符 |
| `optional_merge.recommended_operators` | `??,if guard,typeof guard` | 推荐替代 |
| `optional_merge.scan_scope_glob` | `api/src/**/*.ts` | 扫描范围 |
| `optional_merge.allow_as_in_migration` | `false` | 迁移期豁免 |
| `engine_adapter_sync.enabled` | `true` | 启用 |
| `engine_adapter_sync.severity` | `critical` | 严重级别 |
| `engine_adapter_sync.engine_adapter_interface_path` | `api/src/engine/adapter.ts` | 接口路径 |
| `engine_adapter_sync.adapter_implementations_directory` | `api/src/engine/` | 实现目录 |
| `engine_adapter_sync.forbidden_assertion_patterns` | `as unknown as,@ts-ignore,@ts-expect-error` | 禁止绕过 |
| `engine_adapter_sync.required_methods` | `` | 必备方法（留空=全部） |
| `engine_adapter_sync.optional_methods` | `beforeLoop,afterLoop` | 可选方法 |
| `engine_adapter_sync.allow_not_implemented_placeholder` | `false` | 允许 throw 占位 |

## 项目目录结构审查参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `project_structure_review.enabled` | `true` | 启用（BR-030~033） |
| `project_structure_review.severity_br030` | `critical` | 目录分离 |
| `project_structure_review.severity_br031` | `critical` | .gitignore |
| `project_structure_review.severity_br032` | `suggestion` | 数据外迁 |
| `project_structure_review.severity_br033` | `suggestion` | file: 协议 |
| `project_structure_review.source_dirs` | `api/src/,frontend/src/,scripts/` | 源码目录 |
| `project_structure_review.runtime_data_dir` | `data/` | 禁止在源码目录 |
| `project_structure_review.build_output_dirs` | `dist/,build/` | 禁止在源码目录 |
| `project_structure_review.external_toolchain_dirs` | `w64devkit/` | 禁止在源码目录 |
| `project_structure_review.runtime_data_ignore` | `data/,*.log` | .gitignore 规则 |
| `project_structure_review.build_output_ignore` | `dist/,build/` | .gitignore 规则 |
| `project_structure_review.verification_command` | `git check-ignore -v <path>` | 验证命令 |
| `project_structure_review.tracked_check_command` | `git ls-files <path>` | 跟踪检查 |
| `project_structure_review.gitignore_file_path` | `.gitignore` | gitignore 路径 |
| `project_structure_review.vaultpath_config_field` | `vaultPath` | 配置字段 |
| `project_structure_review.config_files_to_check` | `api/config.json,config/default.json` | 检查文件 |
| `project_structure_review.runtime_data_patterns` | `data/` | 外迁目录 |
| `project_structure_review.file_protocol_pattern` | `file:` | 协议前缀 |
| `project_structure_review.verify_command` | `npm ls <pkg>` | 验证命令 |
| `project_structure_review.package_json_files` | `package.json,api/package.json,frontend/package.json` | 检查文件 |

## 配置化与持久化边界审查参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_persistence_boundary.enabled` | `true` | 启用（BR-034~037） |
| `config_persistence_boundary.severity_br034` | `critical` | 配置化检测 |
| `config_persistence_boundary.severity_br035` | `critical` | 路径锚点 |
| `config_persistence_boundary.severity_br036` | `critical` | 缓存刷新 |
| `config_persistence_boundary.severity_br037` | `suggestion` | 跨 origin |
| `config_persistence_boundary.configurable_param_patterns` | `apiKey, port, host, path, timeout, secret, token, password` | 须配置化参数 |
| `config_persistence_boundary.detection_patterns` | `process.env., app.listen(, path.join(, new Set([` | 硬编码检测 |
| `config_persistence_boundary.config_file_path` | `api/config.json` | 配置文件 |
| `config_persistence_boundary.env_var_ref_field` | `apiKeyRef` | 环境变量引用字段 |
| `config_persistence_boundary.path_resolution_strategy` | `import.meta.url + process.cwd() fallback + CWD probe` | 三级策略 |
| `config_persistence_boundary.primary_anchor` | `import.meta.url` | ESM 首选锚点 |
| `config_persistence_boundary.packaged_fallback` | `process.cwd()` | 打包兜底 |
| `config_persistence_boundary.forbidden_sole_anchor` | `process.cwd()` | 禁止唯一锚点 |
| `config_persistence_boundary.path_resolution_functions` | `getConfigPath, getStateDir, getPromptsDir, getVaultRoot` | 须三级策略 |
| `config_persistence_boundary.write_persistence_functions` | `saveAiConfig, resetAiConfig, saveWebSearchConfig, saveCleanupConfig` | 须刷新函数 |
| `config_persistence_boundary.cache_refresh_method` | `refreshConfigCache(data)` | 刷新方法 |
| `config_persistence_boundary.cache_ttl_ms` | `30000` | 缓存 TTL |
| `config_persistence_boundary.refresh_required_after_write` | `true` | 写后须刷新 |
| `config_persistence_boundary.refresh_failure_behavior` | `keep_old_value` | 失败保持旧值 |
| `config_persistence_boundary.cross_origin_data_types` | `ai_config, conversations` | 跨 origin 类型 |
| `config_persistence_boundary.backend_authoritative_source` | `config.json + data/conversations/` | 后端权威源 |
| `config_persistence_boundary.frontend_cache_layers` | `localStorage, IndexedDB` | 前端缓存层 |
| `config_persistence_boundary.localstorage_allowed_fields` | `baseUrl, model, theme, navCollapsed` | 允许字段 |
| `config_persistence_boundary.localstorage_forbidden_fields` | `apiKey, authtoken, password, secret` | 禁止字段 |
| `config_persistence_boundary.degradation_log_required` | `true` | 降级须 log |
| `config_persistence_boundary.crud_route_required` | `true` | 须 CRUD 路由 |

## Tauri 构建脚本审查参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_build_script.enabled` | `true` | 启用（BR-038~040） |
| `tauri_build_script.severity_br038` | `critical` | SPA 构建缺失 |
| `tauri_build_script.severity_br039` | `critical` | 产物清理+验证 |
| `tauri_build_script.severity_br040` | `suggestion` | 磁盘检查 |
| `tauri_build_script.build_scripts` | `tauri-build-debug.ps1,tauri-build-release.ps1` | 构建脚本 |
| `tauri_build_script.spa_package_name` | `@karpathy-wiki/web` | SPA 子包名 |
| `tauri_build_script.spa_artifact_path` | `services/api/public/` | SPA 产物目录 |
| `tauri_build_script.spa_entry_file` | `index.html` | SPA 入口 |
| `tauri_build_script.forbidden_build_command` | `pnpm run build` | 禁用命令 |
| `tauri_build_script.required_build_command_pattern` | `pnpm --filter <pkg> build` | 必需命令 |
| `tauri_build_script.tauri_build_commands` | `cargo tauri build --debug,cargo tauri build --release` | Tauri 命令 |
| `tauri_build_script.debug_min_gb` | `3` | debug 磁盘下限 |
| `tauri_build_script.release_min_gb` | `5` | release 磁盘下限 |
| `tauri_build_script.disk_space_cleanup_hint` | `cargo cache -a; 清理 target/ 目录` | 清理建议 |

## Tauri Capability 配置审查参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_capability_config.enabled` | `true` | 启用（BR-041~044） |
| `tauri_capability_config.severity_br041` | `critical` | build.rs 命令注册 |
| `tauri_capability_config.severity_br042` | `critical` | capabilities 权限 |
| `tauri_capability_config.severity_br043` | `critical` | remote.urls 格式 |
| `tauri_capability_config.severity_br044` | `critical` | tauri.conf.json 引用 |
| `tauri_capability_config.build_rs_path` | `src-tauri/build.rs` | build.rs 路径 |
| `tauri_capability_config.command_source_directory` | `src-tauri/src/` | 命令源码目录 |
| `tauri_capability_config.command_decorator_pattern` | `#\[tauri::command\]` | 命令装饰器 |
| `tauri_capability_config.app_manifest_method_pattern` | `AppManifest::commands\|\.commands\(` | manifest 调用 |
| `tauri_capability_config.capabilities_directory` | `src-tauri/capabilities/` | capability 目录 |
| `tauri_capability_config.default_capability_file` | `default.json` | 默认文件名 |
| `tauri_capability_config.default_capability_identifier` | `default` | 默认 identifier |
| `tauri_capability_config.permissions_array_field` | `permissions` | 权限字段 |
| `tauri_capability_config.allow_prefix` | `allow-` | 权限前缀 |
| `tauri_capability_config.required_core_permissions` | `core:default` | 核心权限 |
| `tauri_capability_config.external_url_permission` | `core:webview:allow-external-urls` | 外部 URL 权限 |
| `tauri_capability_config.remote_field_name` | `remote` | 嵌套字段（非顶层） |
| `tauri_capability_config.url_patterns_field` | `urls` | URL 列表字段 |
| `tauri_capability_config.tauri_conf_path` | `src-tauri/tauri.conf.json` | tauri.conf.json 路径 |
| `tauri_capability_config.capabilities_reference_path` | `app.security.capabilities` | 引用路径 |

Tauri 1.x 不适用，设 `enabled` 为 `false`。

## PowerShell stderr 处理审查参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `powershell_stderr.enabled` | `true` | 启用（BR-045~047） |
| `powershell_stderr.severity_br045` | `critical` | 直接 `&` 调用 |
| `powershell_stderr.severity_br046` | `critical` | `2>&1` 合并流 |
| `powershell_stderr.severity_br047` | `suggestion` | Stop 模式 |
| `powershell_stderr.script_glob_pattern` | `**/*.ps1` | 脚本扫描 |
| `powershell_stderr.start_process_required_commands` | `cargo,rustc,pnpm,npm,node,tsc,tsx,git,go,python,py,java,dotnet` | 须 Start-Process |
| `powershell_stderr.forbidden_invoke_pattern` | `&\s*\b(cargo\|rustc\|pnpm\|npm\|node\|tsc\|tsx\|git\|go\|python\|py\|java\|dotnet)\b` | 禁止直接调用 |
| `powershell_stderr.forbidden_redirect_pattern` | `2>&1.*\|\s*Out-Host` | 禁止合并流 |
| `powershell_stderr.error_action_preference_pattern` | `\$ErrorActionPreference\s*=\s*['"]Stop['"]` | Stop 声明 |
| `powershell_stderr.required_start_process_params` | `-NoNewWindow,-Wait,-PassThru` | 必备参数 |
| `powershell_stderr.recommended_redirect_params` | `-RedirectStandardOutput,-RedirectStandardError` | 推荐重定向 |
| `powershell_stderr.exit_code_check_pattern` | `ExitCode\|LASTEXITCODE` | 退出码检查 |

仅适用于 PowerShell（`.ps1`）。

## 认证端点 / Windows 文件操作 审查参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `auth_endpoint_classification.enabled` | `true` | 启用 |
| `auth_endpoint_classification.severity` | `critical` | 严重级别 |
| `auth_endpoint_classification.public_paths_whitelist` | `/api/auth/login,/health` | 公开端点 |
| `auth_endpoint_classification.auth_required_endpoints` | `/api/auth/me,/api/auth/logout` | 须鉴权端点 |
| `auth_endpoint_classification.middleware_hook` | `preHandler` | 中间件 hook |
| `auth_endpoint_classification.skip_mechanism` | `isPublicPath` | 跳过机制 |
| `windows_file_operation.enabled` | `true` | 启用 |
| `windows_file_operation.severity` | `critical` | 严重级别 |
| `windows_file_operation.platform` | `win32` | 触发平台 |
| `windows_file_operation.delete_command` | `rd /s /q` | 原生删除 |
| `windows_file_operation.fallback_method` | `fs.rmSync` | 回退方法 |
| `windows_file_operation.verify_after_delete` | `true` | 删除后验证 |
| `windows_file_operation.retry_count` | `1` | 重试次数 |
| `windows_file_operation.retry_delay_ms` | `100` | 重试间隔 |

## 多资源并行加载 / 超时链 / 外部 API / 超时分级 审查参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `parallel_loading_backend.enabled` | `true` | 启用（BR-052） |
| `parallel_loading_backend.severity_br052_1` | `critical` | 串行加载 |
| `parallel_loading_backend.severity_br052_2` | `critical` | Promise.all |
| `parallel_loading_backend.severity_br052_3` | `critical` | 错误收集 |
| `parallel_loading_backend.severity_br052_4` | `best-practice` | 过度并行 |
| `parallel_loading_backend.severity_br052_5` | `suggestion` | 总超时兜底 |
| `parallel_loading_backend.independent_resource_patterns` | `MCP,API,file` | 资源类型 |
| `parallel_loading_backend.required_wrapper` | `Promise.allSettled` | 并行包装器 |
| `parallel_loading_backend.forbidden_patterns` | `for await,for...of,serial` | 禁止串行 |
| `parallel_loading_backend.error_collection_required` | `true` | 须收集错误 |
| `parallel_loading_backend.error_collection_field` | `errors` | 错误字段 |
| `parallel_loading_backend.error_source_field` | `source` | 来源字段 |
| `parallel_loading_backend.total_timeout_required` | `true` | 总超时兜底 |
| `timeout_chain_backend.enabled` | `true` | 启用（BR-053） |
| `timeout_chain_backend.severity_br053_1` | `critical` | 链式覆盖 |
| `timeout_chain_backend.severity_br053_2` | `critical` | 硬编码超时 |
| `timeout_chain_backend.severity_br053_3` | `critical` | 清空结果 |
| `timeout_chain_backend.severity_br053_4` | `critical` | 无降级 |
| `timeout_chain_backend.severity_br053_5` | `suggestion` | 阈值变更 |
| `timeout_chain_backend.layer_order` | `frontend>backend>mcp>llm` | 链顺序 |
| `timeout_chain_backend.margin_multiplier` | `1.5` | 余量倍数 |
| `timeout_chain_backend.config_field_pattern` | `timeout_chain_backend.layer_timeouts` | config 字段 |
| `timeout_chain_backend.partial_result_preservation_required` | `true` | 保留部分结果 |
| `timeout_chain_backend.degradation_path_required` | `true` | 须降级路径 |
| `timeout_chain_backend.layer_timeouts.llmTimeoutMs` | `30000` | LLM 层超时 |
| `timeout_chain_backend.layer_timeouts.mcpTimeoutMs` | `30000` | MCP 层超时 |
| `timeout_chain_backend.layer_timeouts.backendTimeoutMs` | `90000` | 后端层超时 |
| `timeout_chain_backend.layer_timeouts.questionTimeoutMs` | `120000` | 前端层超时 |
| `external_api_contract.enabled` | `true` | 启用（BR-054） |
| `external_api_contract.severity_br054_1` | `critical` | 原生 fetch |
| `external_api_contract.severity_br054_2` | `critical` | 单路径访问 |
| `external_api_contract.severity_br054_3` | `critical` | 类型未转换 |
| `external_api_contract.severity_br054_4` | `suggestion` | 未 export |
| `external_api_contract.diagnostic_error_codes` | 见下 | undici 错误码映射 |
| `external_api_contract.unknown_error_hint` | `cause?.message \|\| err.message` | 兜底提示 |
| `external_api_contract.export_for_testing` | `true` | 须 export |
| `external_api_contract.field_fallback_separator` | `\|\|` | 双重兼容 |
| `external_api_contract.type_conversion_required` | `true` | 类型转换 |
| `external_api_contract.fetch_whitelist` | `fetchWithDiagnostics internal,test mock` | fetch 白名单 |

| 错误码 | 提示文案 |
|--------|---------|
| `UND_ERR_CONNECT_TIMEOUT` / `ETIMEDOUT` | 网络连接超时（{url} 不可达），请检查网络或代理设置 |
| `ENOTFOUND` | 域名解析失败（{hostname}），请检查 DNS 或网络连接 |
| `ECONNREFUSED` | 连接被拒绝（{host}），目标服务未启动或端口被防火墙拦截 |
| `CERT_HAS_EXPIRED` / `UNABLE_TO_VERIFY_LEAF_SIGNATURE` | TLS 证书校验失败（{code}），请检查系统时间或证书链 |
| `UND_ERR_ABORTED` | 请求超时或被中止，请确认目标服务响应是否过慢 |

## 超时分级 / 密钥解析 / 长任务 / 媒体归档 / 会话存储 / SSE 分发 审查参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `timeout_tier.enabled` | `true` | 启用（BR-055） |
| `timeout_tier.severity_br055_1` | `critical` | 统一超时 |
| `timeout_tier.severity_br055_2` | `critical` | 硬编码超时 |
| `timeout_tier.severity_br055_3` | `critical` | 分级混用 |
| `timeout_tier.severity_br055_4` | `suggestion` | LLM 未分级 |
| `timeout_tier.severity_br055_5` | `suggestion` | 代理未加宽 |
| `timeout_tier.timeout_tiers.task_creation` | `30000` | 任务创建 |
| `timeout_tier.timeout_tiers.task_polling` | `30000` | 任务轮询 |
| `timeout_tier.timeout_tiers.image_generation` | `60000` | 图像生成 |
| `timeout_tier.timeout_tiers.video_download` | `120000` | 视频下载 |
| `timeout_tier.timeout_tiers.llm_small` | `60000` | LLM 小 token |
| `timeout_tier.timeout_tiers.llm_large` | `180000` | LLM 大 token |
| `timeout_tier.proxy_overhead_ms` | `20000` | 代理开销 |
| `timeout_tier.llm_small_token_threshold` | `4000` | small token 上限 |
| `timeout_tier.llm_large_token_threshold` | `16000` | large token 上限 |
| `api_key_resolution.enabled` | `true` | 启用（BR-056） |
| `api_key_resolution.severity_br056_1` | `critical` | 未三级回退 |
| `api_key_resolution.severity_br056_2` | `critical` | 回退顺序错误 |
| `api_key_resolution.severity_br056_3` | `critical` | 错误消息不全 |
| `api_key_resolution.severity_br056_4` | `suggestion` | 返回值非 null |
| `api_key_resolution.fallback_chain` | `dedicated,shared,env` | 回退链路 |
| `api_key_resolution.dedicated_field_pattern` | `config.{service}.apiKey` | 专用段模板 |
| `api_key_resolution.shared_field_pattern` | `config.llm.apiKeys.{provider}` | 共享段模板 |
| `api_key_resolution.env_ref_field_pattern` | `config.{service}.apiKeyRef` | 环境变量模板 |
| `api_key_resolution.error_message_template` | `{service} API key not configured (set {dedicated_field} or {shared_field} or env {env_ref_field})` | 错误消息 |
| `api_key_resolution.null_return_required` | `true` | 强制返回 null |
| `long_task_architecture.enabled` | `true` | 启用（BR-057） |
| `long_task_architecture.severity_br057_1` | `critical` | 长任务 SSE |
| `long_task_architecture.severity_br057_2` | `critical` | 无限流 |
| `long_task_architecture.severity_br057_3` | `critical` | 错误码未区分 |
| `long_task_architecture.severity_br057_4` | `critical` | 单日志通道 |
| `long_task_architecture.severity_br057_5` | `suggestion` | 缺少注释 |
| `long_task_architecture.severity_br057_6` | `suggestion` | 限流不匹配 |
| `long_task_architecture.sse_threshold_ms` | `30000` | SSE 阈值 |
| `long_task_architecture.destructive_rate_limit` | `5` | 破坏性限流 |
| `long_task_architecture.destructive_rate_window` | `1 minute` | 限流窗口 |
| `long_task_architecture.poll_rate_limit` | `60` | 轮询限流 |
| `long_task_architecture.poll_rate_window` | `1 minute` | 轮询窗口 |
| `long_task_architecture.poll_interval_ms` | `5000` | 轮询间隔 |
| `long_task_architecture.config_error_keyword` | `not configured` | 错误关键词 |
| `long_task_architecture.config_error_status` | `400` | 配置错误码 |
| `long_task_architecture.api_error_status` | `500` | API 错误码 |
| `media_archive_frontmatter.enabled` | `true` | 启用（BR-058） |
| `media_archive_frontmatter.severity_br058_1` | `critical` | 目录未在白名单 |
| `media_archive_frontmatter.severity_br058_2` | `critical` | 缺少字段 |
| `media_archive_frontmatter.severity_br058_3` | `critical` | 文件名不匹配 |
| `media_archive_frontmatter.severity_br058_4` | `suggestion` | 字段散落 |
| `media_archive_frontmatter.severity_br058_5` | `suggestion` | 双重 frontmatter |
| `media_archive_frontmatter.archive_dir` | `vault/queries/` | 归档目录 |
| `media_archive_frontmatter.frontmatter_required_fields` | `type,output_mode,generated_at` | 必备字段 |
| `media_archive_frontmatter.allowed_output_modes` | `image,ppt,video,podcast` | 允许模式 |
| `media_archive_frontmatter.filename_pattern` | `^(image\|ppt\|video)-\d{8}-\d{6}\.(md\|png\|mp4)$` | 文件名正则 |
| `media_archive_frontmatter.timestamp_format` | `YYYYMMDD-HHmmss` | 时间戳格式 |
| `media_archive_frontmatter.generated_at_format` | `ISO8601` | generated_at 格式 |
| `media_archive_frontmatter.allow_marp_merge` | `true` | marp 合并 |
| `session_store_review.enabled` | `true` | 启用（BR-059） |
| `session_store_review.severity_br059_1` | `critical` | 无淘汰策略 |
| `session_store_review.severity_br059_2` | `critical` | 未检查 TTL |
| `session_store_review.severity_br059_3` | `critical` | 接收客户端内容 |
| `session_store_review.severity_br059_4` | `critical` | 未忽略客户端内容 |
| `session_store_review.severity_br059_5` | `suggestion` | 无 TTL 写入 |
| `session_store_review.max_sessions` | `100` | 会话上限 |
| `session_store_review.ttl_ms` | `3600000` | 会话 TTL |
| `session_store_review.trust_client_content` | `false` | 信任客户端 |
| `session_store_review.evict_strategy` | `ttl-then-lru` | 淘汰策略 |
| `session_store_review.reference_fields` | `sessionId,messageIndex` | 引用字段 |
| `sse_event_dispatch.enabled` | `true` | 启用（BR-060） |
| `sse_event_dispatch.severity_br060_1` | `critical` | if/else 链 |
| `sse_event_dispatch.severity_br060_2` | `critical` | 未用映射表 |
| `sse_event_dispatch.severity_br060_3` | `critical` | outputMode string |
| `sse_event_dispatch.severity_br060_4` | `suggestion` | outputMode 混用 |
| `sse_event_dispatch.severity_br060_5` | `critical` | 未知事件静默 |
| `sse_event_dispatch.object_dispatch_threshold` | `3` | 映射表阈值 |
| `sse_event_dispatch.cognitive_complexity_limit` | `15` | 认知复杂度 |
| `sse_event_dispatch.unknown_event_strategy` | `warn` | 未知事件策略 |
| `sse_event_dispatch.allowed_output_modes` | `normal,mindmap,image,ppt,video` | 允许的模式 |

## 限流韧性审查参数（BR-063）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `rate_limit_resilience.enabled` | `true` | 启用（BR-063） |
| `rate_limit_resilience.severity_br063_1` | `critical` | 限流键错误违规级别 |
| `rate_limit_resilience.severity_br063_2` | `critical` | 无界 Map 违规级别 |
| `rate_limit_resilience.severity_br063_3` | `critical` | 可变时间比较违规级别 |
| `rate_limit_resilience.severity_br063_4` | `suggestion` | 时钟无关测试违规级别 |
| `rate_limit_resilience.trusted_proxy_hop` | `1` | 可信代理跳数（从右剔除） |
| `rate_limit_resilience.window_ms` | `60000` | 滑动窗口长度 |
| `rate_limit_resilience.max_per_window` | `60` | 每窗口最大命中数 |
| `rate_limit_resilience.max_buckets` | `10000` | 桶数上限（LRU 兜底） |
| `rate_limit_resilience.timing_safe_equal_required` | `true` | 令牌比较须常量时间 |

## 确定性文本处理审查参数（BR-064）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `deterministic_text_processing.enabled` | `true` | 启用（BR-064） |
| `deterministic_text_processing.severity_br064_1` | `critical` | 宽泛 Unicode 区间违规级别 |
| `deterministic_text_processing.severity_br064_2` | `critical` | 非实体感知去重违规级别 |
| `deterministic_text_processing.severity_br064_3` | `critical` | 仅按短删违规级别 |
| `deterministic_text_processing.severity_br064_4` | `critical` | 预算不保证净下降违规级别 |
| `deterministic_text_processing.severity_br064_5` | `critical` | 跌破连贯性地板违规级别 |
| `deterministic_text_processing.ideograph_regex` | `[㐀-鿿㐀-䶿]` | 仅表意文字区间（不含标点） |
| `deterministic_text_processing.jaccard_threshold` | `0.9` | 去重 Jaccard 阈值 |
| `deterministic_text_processing.greeting_blacklist` | `你好,谢谢,hi,hello` | 问候黑名单 |
| `deterministic_text_processing.compression_ratio` | `0.3` | 压缩比例 |
| `deterministic_text_processing.min_floor` | `200` | 压缩最小地板（token） |
| `deterministic_text_processing.cjk_token_ratio` | `1` | CJK token 估算（1/字） |
| `deterministic_text_processing.latin_token_ratio` | `4` | Latin token 估算（4/词） |
| `deterministic_text_processing.recency_window` | `8` | 连贯性最近窗口 |
| `deterministic_text_processing.coherence_k` | `12` | 连贯性地板 K |

## 运行时数据隐私审查参数（BR-065）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `runtime_data_privacy.enabled` | `true` | 启用（BR-065） |
| `runtime_data_privacy.severity_br065_1` | `critical` | 新目录未 gitignore 违规级别 |
| `runtime_data_privacy.severity_br065_2` | `critical` | 默认服务端存会话违规级别 |
| `runtime_data_privacy.runtime_data_dirs` | `data/,cache/,index/,userData/` | 运行期数据目录清单（须被 gitignore） |
| `runtime_data_privacy.gitignore_file_path` | `.gitignore` | gitignore 路径 |
| `runtime_data_privacy.verification_command` | `git check-ignore -v <path>` | 验证命令 |
| `runtime_data_privacy.server_side_sessions` | `false` | 服务端存会话默认开关 |
| `runtime_data_privacy.server_side_sessions_config_field` | `persistSessions` | 显式开关字段名 |

## 配置可移植默认审查参数（BR-066）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_portable_defaults.enabled` | `true` | 启用（BR-066） |
| `config_portable_defaults.severity_br066_1` | `critical` | 依赖 vaultPath 推导违规级别 |
| `config_portable_defaults.severity_br066_2` | `critical` | 写机器绝对路径违规级别 |
| `config_portable_defaults.user_data_dir_anchor` | `%LOCALAPPDATA%\KarpathyWiki` | 用户数据目录锚点（SEA 模式真实实现；回退 APPDATA → HOME，应用名目录） |
| `config_portable_defaults.forbidden_absolute_prefixes` | `C:\Users\,/home/,/Users/,/root/` | 禁止写入的绝对路径前缀 |
| `config_portable_defaults.portable_token` | `${userDataDir}` | 可重派生锚点占位符 |

> 注意：`user_data_dir_anchor` 须与 `runtime.ts` 真实实现保持一致——SEA 模式解析为 `%LOCALAPPDATA%\KarpathyWiki`（回退 `APPDATA` → `os.homedir()`），开发模式沿用 `api/` 目录。旧值 `os.homedir()/.karpathy-wiki` 与实现不符，已校正。

## 安装器与用户数据审查参数（BR-068）

> 对应后端打包 / 安装器 / 用户数据目录解析与防覆盖规则（CODING-PACKAGING-USERDATA，wiki-code-dev references/packaging-userdata-rule.md）。
> 聚焦三类事故：安装器覆盖用户配置 / 路径解析错基准（SEA import.meta.url 失效）/ 机器绝对路径固化进配置。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `packaging_user_data.enabled` | `true` | 启用（BR-068） |
| `packaging_user_data.severity_br068_1` | `critical` | 安装器覆盖用户数据违规级别 |
| `packaging_user_data.severity_br068_2` | `critical` | 资源路径/用户数据路径混用违规级别 |
| `packaging_user_data.severity_br068_3` | `critical` | 固化机器绝对路径违规级别 |
| `packaging_user_data.severity_br068_4` | `suggestion` | 用户数据目录未首次自建违规级别 |
| `packaging_user_data.app_name` | `KarpathyWiki` | 用户数据目录名（贴 LOCALAPPDATA 之下） |
| `packaging_user_data.user_data_dir_anchor` | `LOCALAPPDATA` | 用户数据根首选锚点 |
| `packaging_user_data.user_data_dir_fallback` | `APPDATA, HOME` | 回退锚点顺序 |
| `packaging_user_data.user_data_dir_pattern` | `{anchor}/{app_name}` | 用户数据目录解析模板 |
| `packaging_user_data.installer_program_files_flags` | `ignoreversion` | 程序文件安装 Flags（升级即覆盖） |
| `packaging_user_data.installer_exclude_user_data` | `true` | 用户数据（config.json/.env/vault/data）禁止打包到 {app} |
| `packaging_user_data.sea_detection_symbol` | `IS_SEA` | 打包模式检测标志 |
| `packaging_user_data.resource_path_funcs` | `getApiDir, getResourcePath, getPromptsDir` | 资源路径派生函数（随版本更新，随 exe 走） |
| `packaging_user_data.user_data_path_funcs` | `getUserDataDir, getDataDir, getUserDataPath` | 用户数据路径派生函数（跨版本持久，随用户走） |
| `packaging_user_data.forbidden_data_dir_sources` | `vaultPath, process.execPath, {app}` | 禁止作为用户数据目录来源的基准 |
| `packaging_user_data.rebase_relative_only` | `true` | 仅相对路径字段被归一化到用户数据目录，尊重用户显式绝对路径 |
| `packaging_user_data.clean_default_fields` | `vaultPath, auth.usersFilePath, auth.auditLogPath, urlCrawl.*, logging.logFilePath` | 首次落盘须回退为相对默认值的字段清单 |
| `packaging_user_data.script_glob_pattern` | `**/*.ps1, **/*.iss` | 安装器/构建脚本扫描范围 |

## 严格路径穿越审查参数（BR-067）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `path_traversal_strict.enabled` | `true` | 启用（BR-067，扩展 security-rule） |
| `path_traversal_strict.severity_br067_1` | `critical` | 缺 `..` 段二次校验违规级别 |
| `path_traversal_strict.severity_br067_2` | `critical` | 缺 `isAbsolute` 检查违规级别 |
| `path_traversal_strict.name_whitelist_regex` | `^[A-Za-z0-9_][A-Za-z0-9._-]*$` | 文件名白名单（与 security-rule 一致） |
| `path_traversal_strict.traversal_regex` | `(^\|\/)\.\.(\/\|$)` | `..` 段负向匹配 |
| `path_traversal_strict.require_isabsolute_check` | `true` | 拼接前须 isAbsolute 检查 |

## 用户上传文件名管线审查参数（BR-069）

> 对应"用户输入作文件名"的 Unicode 感知清洗 + 内部前缀剥离 + `..`/`isAbsolute` 二次校验（CODING-USER-UPLOAD-FILENAME，wiki-code-dev references/user-upload-filename-rule.md）。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `user_upload_filename.enabled` | `true` | 启用（BR-069） |
| `user_upload_filename.severity_br069_1` | `critical` | ASCII 导向清洗把中文变下划线违规级别 |
| `user_upload_filename.severity_br069_2` | `critical` | 内部前缀泄漏到展示名违规级别 |
| `user_upload_filename.severity_br069_3` | `critical` | 缺 `..`/`isAbsolute` 二次校验违规级别 |
| `user_upload_filename.severity_br069_4` | `suggestion` | originalName 缺 `??` 兜底违规级别 |
| `user_upload_filename.sanitize_regex` | `/[^\p{L}\p{N}._-]/gu` | Unicode 感知清洗正则（保留 CJK/字母/数字/点/下划线/短横线） |
| `user_upload_filename.internal_prefix_patterns` | `wiki-batch-\d+-\d+-, wiki-compile-\d+-` | 须剥离的系统内部前缀（落盘/展示前） |
| `user_upload_filename.traversal_regex` | `(^\|\/)\.\.(\/\|$)` | `..` 段负向匹配（复用 BR-067） |
| `user_upload_filename.require_isabsolute_check` | `true` | 拼接前须 isAbsolute 检查（复用 BR-067） |
| `user_upload_filename.original_name_field` | `originalName` | 透传原始文件名的契约字段（optional + `??` 兜底） |

## 数据迁移 / 修复脚本安全审查参数（BR-070）

> 对应数据迁移/修复脚本的安全范式（CODING-MIGRATION-SAFETY，wiki-code-dev references/data-repair-script-safety-rule.md）。聚焦三类事故：迁移覆盖原文件无备份 / `$1` 字符串拼接污染引用 / 边读边写导致重复处理。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `migration_script_safety.enabled` | `true` | 启用（BR-070） |
| `migration_script_safety.severity_br070_1` | `critical` | 默认非 dry-run 违规级别 |
| `migration_script_safety.severity_br070_2` | `critical` | 无备份/覆盖原文件违规级别 |
| `migration_script_safety.severity_br070_3` | `critical` | `$1` 字符串拼接污染违规级别 |
| `migration_script_safety.severity_br070_4` | `best-practice` | 边读边写 / 无缓存违规级别 |
| `migration_script_safety.dry_run_default` | `true` | 默认 dry-run，显式 `--apply` 才写盘 |
| `migration_script_safety.apply_flag` | `--apply` | 显式执行写盘的标志 |
| `migration_script_safety.conflict_suffix_pattern` | `-{n}` | 冲突文件名递增后缀（禁止覆盖） |
| `migration_script_safety.reference_replace_style` | `function` | 引用改写须函数式替换（非 `"$1" + x`） |
| `migration_script_safety.require_two_phase` | `true` | 先全量扫描再批量改写 |
| `migration_script_safety.pagecache_required` | `true` | 同文件重复读取须缓存 |

## BYOK 多用户配置代理审查参数（BR-072）

> 对应 BYOK 多用户密钥代理（前端本地命名空间 + 密钥仅经请求体下发 + 覆盖纯函数 + 缺密钥不回落服务端共享）。CODING-BYOK（wiki-code-dev references/byok-per-user-override-rule.md）。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `byok_per_user_override.enabled` | `true` | 启用（BR-072） |
| `byok_per_user_override.severity_no_persist` | `critical` | 密钥落盘 / 回显 GET / 记日志违规级别 |
| `byok_per_user_override.severity_require_key` | `critical` | 缺必需密钥回落服务端共享违规级别 |
| `byok_per_user_override.severity_pure_override` | `critical` | 覆盖非纯函数 / 空覆盖清空服务端共享违规级别 |
| `byok_per_user_override.require_key_fields` | `apiKey,provider,baseUrl,model` | 缺任一即 400 的必需字段 |
| `byok_per_user_override.override_func` | `applyPerRequestOverride` | 覆盖纯函数名（运行时零依赖） |
| `byok_per_user_override.empty_override_falls_back` | `true` | 空 / 默认工具配置须回退服务端共享配置 |

## 审查流程优化（Review Process Optimization）

> 以下判定步骤适用于每次评审，旨在降低误报与漏报。规则文件与脚本不硬编码阈值，所有参数从本文件读取。

### 1. Flake 隔离（Flake Isolation）

当某条测试在完整测试套件中失败，但在单独运行时通过，先**单独运行该测试文件**再决定是否归咎于本次变更。预存在的时序 / 状态 flake 很常见（例如固定窗口限流跨过 60s 边界偶发触发 429，见 BR-063-4）。流程：

1. 复现：单独运行失败测试文件（如 `vitest run rate-limit.test.ts` / `pytest tests/test_x.py::test_y`）。
2. 若单独通过 → 判定为 flake，不计入本次变更问题；记录为预存在 issue。
3. 若单独也失败 → 才进入变更内容排查。

### 2. 变更内容范围（Modified-content Scope）

评审时聚焦**实际变更的文件**，不扩大扫描面：

- 优先用 `git diff` / `git diff --cached` 取得变更文件清单与行号。
- 对新增 / 修改的**路由**（routes/*.ts），必须运行 `route_registration_check`（确认注册）+ `type_sync_check`（确认前后端 types.ts 同步，见 BR-026 / type-sync 规则）。
- 仅对变更行及其直接上下文应用规则；未变更代码标记为"已验证，跳过"。

### 3. 配置驱动（Config-driven）

所有阈值 / 参数 / 严重级别均从本文件读取，**禁止在审查逻辑（规则文件、脚本、prompt）中硬编码**。新增规则须同步在对应"审查参数"段落追加参数表，并默认从 config 引用。若某判定需要新阈值，先加到本文件再在规则中引用。

## 隔离测试纪律（Test Isolation — BR-073）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `test_isolation_backend.namespaces_prefixes` | `usercfg::`,`tts-config::` | 隔离测试须唯一化的命名空间前缀（每用例用唯一 userId / 线程 id 拼接） |
| `test_isolation_backend.forbidden_patterns` | `indexedDB.deleteDatabase`,`deleteDatabase` | `beforeEach` 中禁止的删库模式（fake-indexeddb + 已开连接会 onblocked / 泄漏） |
| `test_isolation_backend.flush_rounds` | `3` | 异步落盘断言前 `await new Promise(r => setTimeout(r, 0))` 的轮数 |
| `test_isolation_backend.severity_namespace` | `critical` | BR-073-1 未用唯一命名空间 / 用 beforeEach 删库的违规级别 |
| `test_isolation_backend.severity_flush` | `suggestion` | BR-073-2 异步断言未多轮 flush 的违规级别 |
| `test_isolation_backend.severity_module_state` | `suggestion` | BR-073-3 后端用例未重置模块态 / mock 的违规级别 |

> 参数与 wiki-auto-testing `indexeddb_test_isolation_check`（`namespace_prefixes` / `forbidden_patterns` / `flush_rounds`）对齐；规则正文见 wiki-code-dev references/indexeddb-test-isolation-rule.md。

## SSML / TTS Prosody 注入防护审查参数（BR-074）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `ssml_injection.enabled` | `true` | 是否启用本规则 |
| `ssml_injection.rate_regex` | `^(default\|\d{1,3}%\...)$` | 语速白名单正则（绝对百分比 / 相对倍数 / default） |
| `ssml_injection.volume_regex` | `^(default\|\d{1,3}%\...)$` | 音量白名单正则 |
| `ssml_injection.pitch_regex` | `^(default\|\d{1,3}Hz\...)$` | 语调白名单正则 |
| `ssml_injection.default_value` | `default` | 校验失败回退值 |
| `ssml_injection.escape_chars` | `<>&` | 用户文本拼入 SSML 前须转义的字符 |
| `ssml_injection.forbidden_tags_regex` | `<mstts:express-as` | 免费端点不支持标签（命中即剥离/拒绝） |
| `ssml_injection.unsupported_endpoint_code` | `1007` | 免费端点拒绝 SSML 的 WebSocket 关闭码 |

## 子进程异步/同步正确性审查参数（BR-075）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `child_process_sync.enabled` | `true` | 是否启用本规则 |
| `child_process_sync.sync_calls` | `ffmpeg` | 须同步拿结果的子进程命令清单 |
| `child_process_sync.timeout_ms` | `30000` | 子进程同步调用超时（毫秒，从配置读取） |
| `child_process_sync.require_await_pattern` | `await \| execFileSync` | 结果被使用前的必要同步标志 |
| `child_process_sync.severity_fake_sync` | `critical` | 异步 API 当同步用违规级别 |

## 关键写不静默吞错审查参数（BR-076）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `critical_write_no_swallow.enabled` | `true` | 是否启用本规则 |
| `critical_write_no_swallow.critical_functions` | `saveUsers,saveConfig,persistConversation` | 关键写函数清单（命中即须错误传播） |
| `critical_write_no_swallow.severity` | `critical` | 关键写静默吞错违规级别 |
| `critical_write_no_swallow.silent_catch_pattern` | `catch\s*\([^)]*\)\s*\{\s*\}` | 空 catch（无 throw/log）匹配模式 |

## 关键数据文件损坏防护审查参数（BR-077）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `file_corruption_guard.enabled` | `true` | 是否启用本规则 |
| `file_corruption_guard.critical_files` | `users.json,config.json` | 关键 JSON 文件清单 |
| `file_corruption_guard.backup_on_corruption` | `true` | 损坏时备份为 `.corrupt-<ts>.bak` |
| `file_corruption_guard.backup_suffix` | `.corrupt` | 坏文件备份名标记 |
| `file_corruption_guard.severity` | `critical` | 损坏当 not-found 静默清零违规级别 |

## 类型安全禁用 as any 审查参数（BR-078）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `type_safe_no_any.enabled` | `true` | 是否启用本规则 |
| `type_safe_no_any.forbidden_patterns` | `as any, as unknown as, as any as` | 禁止的绕过写法 |
| `type_safe_no_any.allowed_in` | `@migration` | 允许放行的标注 |
| `type_safe_no_any.proper_type_ref` | `InjectOptions['method']` | 推荐的类型提取示例 |
| `type_safe_no_any.severity` | `critical` | 常驻业务路径 `as any` 绕过违规级别 |

## 超时/阈值可配置化审查参数（BR-079）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `config_timeout.enabled` | `true` | 是否启用本规则 |
| `config_timeout.timeout_keys` | `edgeTtsTimeoutMs` | 须配置化的超时键清单 |
| `config_timeout.default_ms` | `30000` | 超时默认毫秒 |
| `config_timeout.forbidden_literal_ms` | `30000,30_000,60000` | 禁止直接在代码出现硬编码毫秒字面量 |
| `config_timeout.margin_multiplier` | `1.5` | 多层超时递增倍数（与 BR-053 对齐） |

## 去除冗余探测/探针审查参数（BR-080）

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `no_redundant_probe.enabled` | `true` | 是否启用本规则 |
| `no_redundant_probe.capability_check` | `ffmpeg -version` | 工具可用性能力检测命令 |
| `no_redundant_probe.redundant_probe_regex` | `ffprobe` | 冗余探针命令（命中即告警） |
| `no_redundant_probe.forbidden_commands` | `ffprobe` | 禁止用于可用性探测的命令清单 |
| `no_redundant_probe.severity` | `suggestion` | 冗余探测违规级别 |

## 归档落盘文件名唯一性审查参数（BR-081）

> 对应"归档落盘文件名碰撞 → 静默丢数据"复盘（CODING-GENERATED-FILENAME-UNIQUENESS，wiki-code-dev references/generated-filename-uniqueness-rule.md）。落盘文件名由派生分组键（日期+shortId）构成时非全局唯一，须追加随机后缀。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `generated_filename.enabled` | `true` | 是否启用本规则 |
| `generated_filename.derived_group_key` | `date+shortId` | 派生分组键组成（非全局唯一，仅分组） |
| `generated_filename.collision_suffix_len` | `4` | 追加随机后缀长度（hex 字符数） |
| `generated_filename.collision_suffix_charset` | `hex` | 随机后缀字符集（hex/base36/uuid） |
| `generated_filename.reject_on_collision` | `true` | 仍哈希碰撞即拒绝/重生成，禁止覆盖已存在文件 |
| `generated_filename.severity` | `critical` | 派生键直接落盘覆盖他人数据违规级别 |

## 服务端解析客户端日期串安全审查参数（BR-082）

> 对应"非法 ts → RangeError → 500"复盘（CODING-SAFE-CLIENT-DATE-PARSE，wiki-code-dev references/safe-client-date-parse-rule.md）。禁止 `new Date(str).toISOString()` 对非法串抛错。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `safe_date_parse.enabled` | `true` | 是否启用本规则 |
| `safe_date_parse.forbidden_pattern` | `new Date(str).toISOString()` | 命中即告警的非法写法 |
| `safe_date_parse.default_value` | `null` | 解析失败回退值（或 ISO 当前时间，按业务定） |
| `safe_date_parse.accept_undefined` | `true` | 未定义字段允许回退默认而非抛错 |
| `safe_date_parse.coerce_nonstring` | `true` | 非字符串先规范化再校验，不直接 toISOString |
| `safe_date_parse.severity` | `critical` | 非法日期串导致 500 的违规级别 |

## 客户端整数序号校验审查参数（BR-083）

> 对应"非整数 messageIndex → undefined 访问 → 500"复盘（CODING-INTEGER-INDEX-VALIDATION，wiki-code-dev references/integer-index-validation-rule.md）。客户端传下标访问数组前须 `Number.isInteger` 校验。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `integer_index.enabled` | `true` | 是否启用本规则 |
| `integer_index.reject_status` | `400` | 非法/非整数的拒绝状态码 |
| `integer_index.validate_before_access` | `true` | 校验须在数组访问前短路 |
| `integer_index.severity` | `critical` | 非整数当下标导致 undefined 访问 500 的违规级别 |

## Wikilink 注入清洗审查参数（BR-084）

> 对应"refs 含换行破坏 wikilink / 空串脏链接"复盘（CODING-WIKILINK-SANITIZATION，wiki-code-dev references/wikilink-sanitization-rule.md）。注入 `[[wikilink]]` 前去换行+trim+去空。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `wikilink.enabled` | `true` | 是否启用本规则 |
| `wikilink.sanitize_regex` | `[\r\n]` | 须清除的换行字符集 |
| `wikilink.replace_with` | ` ` | 换行替换字符（空格） |
| `wikilink.trim` | `true` | 注入前 trim |
| `wikilink.filter_empty` | `true` | 去空串（`filter(Boolean)`） |
| `wikilink.extra_clean_regex` | `[\]\|]` | 额外清洗的破坏性字符（`]`/`\|`） |
| `wikilink.severity` | `suggestion` | 脏链接/跨行断裂违规级别 |

## 创建型写入空内容拒绝审查参数（BR-085）

> 对应"空内容仍创建空节点"复盘（CODING-EMPTY-CONTENT-REJECTION，wiki-code-dev references/empty-content-rejection-rule.md）。必填字段缺失或空串即拒绝。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `empty_content.enabled` | `true` | 是否启用本规则 |
| `empty_content.reject_status` | `400` | 空内容拒绝状态码 |
| `empty_content.required_fields` | `question,answer` | 必填字段清单（从配置读取，缺失即拒） |
| `empty_content.treat_whitespace_as_empty` | `true` | 纯空白视为空串 |
| `empty_content.severity` | `critical` | 空内容落盘污染知识的违规级别 |

## 归档内容取源解耦审查参数（BR-086）

> 对应"依赖服务端会话 → 默认部署 100% 误报过期"复盘（CODING-PERSISTENCE-CLIENT-CONTENT-DECOUPLING / CODING-CAPABILITY-GATING-SYNC，wiki-code-dev references/persistence-client-content-decoupling-rule.md · references/capability-gating-sync-rule.md）。内容优先请求体取，仅缺失回退会话。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `persistence_client_content.enabled` | `true` | 是否启用本规则 |
| `persistence_client_content.prefer_request_body` | `true` | 内容优先从请求体取 |
| `persistence_client_content.fallback_to_session` | `false` | 仅请求体缺失才回退会话（默认关） |
| `persistence_client_content.default_threads_persist` | `false` | 默认会话持久化开关 |
| `persistence_client_content.forbid_auto_persist` | `true` | 不得擅自开启 persist 以绕过解耦 |
| `persistence_client_content.severity` | `critical` | 依赖服务端会话导致误报过期的违规级别 |

## 编辑重发后端会话落盘契约审查参数（BR-087）

> 对应"编辑后重新发送"复盘（CODING-EDIT-RESEND，wiki-code-dev references/edit-resend-rule.md）。前端 trim 尾随 AI 答案 + 重新插入用户消息后整体重发（FR-077），后端会话 upsert（PUT /api/conversations/:id）须将 `body.messages` 视为权威全量替换（幂等），禁止与服务端既有 messages 做 merge/append，否则被裁悬空答案复活。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `conversation_upsert_contract.enabled` | `true` | 是否启用本规则 |
| `conversation_upsert_contract.messages_authoritative_replace` | `true` | `body.messages` 须为权威全量替换（幂等），禁止服务端 `existing.messages` merge/append |
| `conversation_upsert_contract.missing_messages_fallback` | `[]` | `body.messages` 缺失时回退空数组而非 `existing.messages`（防脏数据/被裁答案复活） |
| `conversation_upsert_contract.preserve_server_metadata` | `createdAt,threadId` | upsert 仅保留的服务端特有元数据键（消息体以请求体为唯一来源） |
| `conversation_upsert_contract.last_write_wins` | `true` | 并发/重试以请求体 messages 为最终态（最后写覆盖），禁止中间态产生重复 |
| `conversation_upsert_contract.severity` | `critical` | 服务端 append/merge 导致悬空答案复活的违规级别 |

## 审查范围判定审查参数（BR-088）

> 后端审查技能的适用范围是 Fastify/TS 后端（routes / services / 引擎 / 配置 / 文件系统 / SSE）。跨端规则前后端各有对应 BR-/FR- 编号，须按文件位置选对应技能核，避免范围误配与双重复核。对齐 wiki-code-dev 复盘维度④（适用 / 不适用边界）。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `review_scope.enabled` | `true` | 是否启用范围判定（待审变更完全前端时声明不匹配并建议切前端技能） |
| `review_scope.frontend_dir_glob` | `frontend/` | 命中即判为前端主导的目录 glob |
| `review_scope.frontend_file_patterns` | `*.vue,frontend/src/stores/*.ts,frontend/src/services/*UserConfig*.ts` | 纯前端文件特征（客户端 IndexedDB 写入 / Pinia reactive 代理剥离属此） |
| `review_scope.route_to_frontend_skill` | `wiki-frontend-code-review` | 范围不匹配时建议切换的前端评审技能名 |
| `review_scope.cross_edge_rules` | `BYOK,SESSION-ISOLATION,STREAMING-RESUME,TEST-ISOLATION,EDIT-RESEND,IDB-REACTIVE-CLONE` | 前后端各有对应编号的跨端规则；按文件位置选其一核，不双重复核 |
| `review_scope.severity_misroute` | `suggestion` | 纯前端改动硬套后端规则的违规级别（如把前端 reactive-proxy-in-IDB 误当后端关键写问题，归属应为前端 FR-081 / CODING-IDB-REACTIVE-CLONE） |

## 服务端权限隔离审查参数（BR-ISOLATION）

> 对应"权限隔离审查"复盘（CODING-ISOLATION，wiki-code-dev references/isolation-guard-rule.md）。全局 `preHandler` 只注入 `currentUser` 不拒绝未认证请求，导致写接口零守卫（游客越权写 / 篡改共享密钥）；限流 / 审计 IP 若只用 `request.ip`（代理下为代理 IP）或只用 `X-Forwarded-For`（可伪造）会误判或被绕过。整改引入 auth 感知守卫工厂 + 服务端 ownerId 盖章 + 限流复合键。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `server_side_isolation.enabled` | `true` | 是否启用服务端权限隔离审查（auth 感知守卫 + ownerId 盖章 + 限流复合键） |
| `server_side_isolation.admin_permission` | `users` | `requireAdmin` 校验的权限键（管理员角色），`requirePermission(permission, ttl)` 入参 |
| `server_side_isolation.pass_through_when_auth_disabled` | `true` | `auth.enabled=false`（单租户）时守卫一律放行，保持"关认证=全管理员"部署形态，禁止对单租户引入 401 |
| `server_side_isolation.guard_factory` | `createIsolationGuards` | 守卫工厂函数名（auth 感知：enabled=false 直通） |
| `server_side_isolation.required_on_write_endpoints` | `requireAdmin` | 写端点默认注入的守卫（共享配置 / 清理 / 归档 / 隧道 / vault / schema / 工具配置 / ingest 配置等） |
| `server_side_isolation.owner_id_source` | `request.currentUser.userId` | 服务端 ownerId 盖章的受信来源（禁止客户端 `body.ownerId` 直接落盘） |
| `server_side_isolation.owner_mismatch_status` | `404` | 归属不匹配时返回状态码（禁 200 携他人数据 / 禁 403 暴露存在性） |
| `server_side_isolation.client_ip_composite_key` | `request.ip\|xffFirst` | 限流 / 审计 IP 复合键模板（socket 对端 IP 不可伪造 + XFF 首段） |

## 路由 return 完整性审查参数（BR-089）

> 对应"登录路由漏 return 双发响应"复盘（CODING-ROUTE-RETURN-COMPLETENESS，wiki-code-dev references/route-return-completeness-rule.md）。Fastify 路由 handler 任一分支漏 return 会隐式触发 `reply.send()`，与已有响应冲突导致 `ERR_STREAM_WRITE_AFTER_END` 双发响应或前端收到空响应/超时。每个 `if/else` 分支与提前退出点都必须显式 `return`/`throw`。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `route_return_completeness.enabled` | `true` | 是否启用路由 return 完整性审查 |
| `route_return_completeness.reply_api` | `reply.send,reply.code,reply.status` | 视为已响应的 reply 调用集合 |
| `route_return_completeness.severity` | `critical` | 漏 return 导致双发响应 / 前端超时的违规级别 |

## 响应钩子安全审查参数（BR-090）

> 对应"compression onSend 钩子挂死"复盘（CODING-RESPONSE-HOOK-SAFE，wiki-code-dev references/response-hook-safe-rule.md）。全局 `onSend`/`onResponse`/`setSerializer`/`contentTypeParser` 在每条响应路径执行，一旦阻塞或抛错会使所有 API 挂起或 500；须全程 `try/catch` fail-open（异常原样放行），禁 `await` 重计算。与 BR-091 互补。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `response_hook_safe.enabled` | `true` | 是否启用响应钩子安全审查 |
| `response_hook_safe.hook_names` | `onSend,onResponse,setSerializer,contentTypeParser` | 视为全局响应钩子的注册点 |
| `response_hook_safe.require_fail_open` | `true` | 钩子主体须被 try/catch 包裹且异常放行 |
| `response_hook_safe.severity` | `critical` | 钩子挂死全量 API 的违规级别 |

## 压缩默认关闭审查参数（BR-091）

> 对应"压缩默认注册致钩子挂死"复盘（CODING-COMPRESSION-DEFAULT-OFF，wiki-code-dev references/compression-default-off-rule.md）。响应压缩中间件必须默认关闭、仅 `config.compress.enable===true` 时条件注册（`if` 包裹），阈值/级别/白名单全来自配置，禁硬编码。压测验证关闭须发 ≥100 紧请求确认无拦截生效。与 BR-090 互补。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `compression.enabled` | `false` | 压缩默认关闭（显式开启才注册） |
| `compression.threshold_bytes` | `1024` | 小于此字节数的响应不压缩（配置化） |
| `compression.level` | `6` | zlib 压缩级别（配置化） |
| `compression.disable_env` | `WIKI_DISABLE_COMPRESS` | 全局硬关闭开关环境变量名 |
| `compression.severity` | `major` | 压缩无条件注册 / 硬编码阈值的违规级别 |

## 用户库初始化完整性审查参数（BR-092）

> 对应"users.json 空壳致登录失败"复盘（CODING-USER-STORE-INIT，wiki-code-dev references/user-store-init-rule.md）。`loadUsers`/`loadConfig` 须区分 not-found（→默认）与 corrupt/空壳（→备份+回退默认+`log.warn`），禁静默清零；初始化写盘须合法非空 JSON。与 BR-076/BR-077 互补。

| 参数键 | 默认值 | 说明 |
|--------|--------|------|
| `user_store_init.enabled` | `true` | 是否启用用户库初始化完整性审查 |
| `user_store_init.critical_files` | `users.json,config.json` | 须保证非空默认的关键数据文件 |
| `user_store_init.backup_on_corrupt` | `true` | 损坏/空壳文件须先备份再回退 |
| `user_store_init.severity` | `critical` | 空壳/损坏未兜底导致登录失败的违规级别 |
| `server_side_isolation.trust_proxy` | `false` | 是否信任代理（保持 false 防 XFF 伪造绕过限流）；与 `rate_limit.trust_proxy` 同源 |