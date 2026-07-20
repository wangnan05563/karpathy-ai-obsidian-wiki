# 编码规范配置参数

所有规则文件通过引用本文件获取具体参数，禁止在规则文件中硬编码值。

## 路径锚点

| 参数 | 值 | 说明 |
|------|-----|------|
| `path_anchor` | `import.meta.url` | ESM 项目路径解析首选锚点 |
| `path_anchor_cjs` | `__dirname` | CJS 项目路径解析锚点 |
| `packaged_marker` | `process.pkg` | 打包模式检测标识 |
| `config_filename` | `config.json` | 配置文件名 |

## 缓存参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `cache_ttl_ms` | `30000` | 内存缓存默认 TTL（30 秒） |
| `cache_refresh_required` | `true` | 写盘后必须刷新缓存 |

## 白名单正则

| 参数 | 值 | 用途 |
|------|-----|-----|
| `uuid_regex` | `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` | UUID 文件名校验 |
| `safe_filename_regex` | `^[a-zA-Z0-9_-]+$` | 通用安全文件名 |
| `safe_path_regex` | `^[a-zA-Z0-9_/-]+$` | 通用安全相对路径 |

## 存储边界

| 参数 | 值 | 说明 |
|------|-----|-----|
| `browser_storage_lifetime` | `per-origin` | localStorage/IndexedDB 按 origin 隔离 |
| `cross_origin_strategy` | `backend-persistence` | 跨 origin 数据用后端持久化 |
| `cache_fallback_enabled` | `true` | 浏览器存储作为后端降级缓存 |

## 降级策略

| 参数 | 值 | 说明 |
|------|-----|-----|
| `backend_unavailable_action` | `fallback-to-cache` | 后端不可用时降级到本地缓存 |
| `cache_unavailable_action` | `non-blocking` | 缓存不可用不阻断主流程 |
| `silent_failure_layers` | `cache-write,indexdb-write` | 静默失败的层（不抛错） |

## 单一权威源

| 参数 | 值 | 说明 |
|------|-----|-----|
| `authoritative_source_config` | `backend config.json` | 配置类数据权威源 |
| `authoritative_source_session` | `backend data/` | 会话类数据权威源 |
| `allowed_cache_layers` | `localStorage,IndexedDB,memory` | 允许的缓存层 |

## 编码

| 参数 | 值 | 说明 |
|------|-----|-----|
| `source_encoding` | `utf-8-no-bom` | 源文件编码 |
| `meta_encoding` | `utf-8-no-bom` | meta 文件编码 |
| `bat_encoding` | `ascii-no-bom` | .bat 文件编码（cmd.exe 兼容） |

## 编码守卫参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `encoding_detection_method` | `utf8-strict-decode` | 严格 UTF-8 解码检测（UTF8Encoding(false, true)） |
| `encoding_fallback` | `gb2312` | 非 UTF-8 文件的回退编码（Windows 中文环境） |
| `encoding_scan_command` | `node scripts/check-encoding.js` | 编码扫描命令 |
| `encoding_fix_command` | `node scripts/check-encoding.js --fix` | 编码修复命令 |
| `encoding_scan_scope` | `source + meta-config` | 扫描范围（源码 + 元配置文件） |

## PowerShell 环境约束

| 参数 | 值 | 说明 |
|------|-----|------|
| `command_separator` | `;` | 命令分隔符（不支持 &&） |
| `readonly_vars` | `$pid,$PWD,$HOME` | 只读变量列表（禁止赋值） |
| `cwd_param` | `cwd` | RunCommand 工作目录参数名 |
| `blocked_commands` | `cmd /c` | 被安全策略阻止的命令 |

## 服务端口参数

> 服务生命周期管理模板（见 `powershell-constraints-rule.md`）所依赖的端口参数集中在本节。
> 规则文件不硬编码端口号，所有端口从本节读取，便于适配不同项目。

| 参数 | 值 | 说明 |
|------|-----|------|
| `required_ports` | `3000,5173` | 项目所需监听的端口列表（后端 API + 前端 Vite） |
| `port_check_state` | `Listen` | 端口就绪状态判定（Get-NetTCPConnection 的 State 字段） |
| `port_check_method` | `Get-NetTCPConnection` | 端口检测方法（PowerShell 原生 cmdlet） |
| `startup_timeout_ms` | `30000` | 服务启动超时（毫秒），超时判定启动失败 |
| `port_poll_interval_ms` | `1000` | 端口轮询间隔（毫秒） |

- 适配新项目时，仅需修改 `required_ports` 列表即可，规则文件中的服务生命周期模板会自动引用。
- 多端口场景：`required_ports` 以逗号分隔，模板用 `foreach` 遍历。

## bat 脚本约束

| 参数 | 值 | 说明 |
|------|-----|------|
| `bat_encoding` | `ascii-no-bom` | .bat 文件编码（cmd.exe 兼容） |
| `bat_pause_issue` | `true` | bat 脚本末尾 pause 会卡住自动化 |
| `bat_alternative` | `npm run` | 直接用 npm 命令替代 bat 脚本 |

## 路由注册守卫参数

> 路由注册守卫规则（见 `route-registration-rule.md`）所依赖的参数集中在本节。
> 规则文件不硬编码路径与模式，所有参数从本节读取，便于适配不同框架。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `route_registration.enabled` | `true` | 是否启用路由注册守卫 |
| `route_registration.severity` | `error` | 违规严重级别（error / warning） |
| `route_registration.route_directory` | `routes/` | 路由文件所在目录（相对项目根） |
| `route_registration.entry_file` | `index.ts` | 路由注册入口文件路径 |
| `route_registration.register_function_pattern` | `register` | 入口文件中识别注册调用的关键字（如 `register` / `use`） |
| `route_registration.probe_enabled` | `false` | 是否在 CI 中对代表性路径发起真实请求验证 |

- 适配 Fastify：`register_function_pattern` 用 `register`。
- 适配 Express：`register_function_pattern` 改为 `use`。
- 适配 NestJS 等自动发现框架：将 `enabled` 设为 `false`。

## 空值守卫参数

> 空值守卫规则（见 `null-guard-rule.md`）所依赖的参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `null_guard.enabled` | `true` | 是否启用空值守卫 |
| `null_guard.severity` | `error` | 违规严重级别 |
| `null_guard.nullable_field_patterns` | `this.provider, this.child, this.connection` | 可空字段名模式（逗号分隔，支持正则） |
| `null_guard.async_assignment_keywords` | `spawn, exec, fork, connect, createClient, init` | 触发"可空字段"标记的异步赋值关键字 |
| `null_guard.guard_required_severity` | `error` | 缺失守卫的严重级别 |
| `null_guard.rebuild_required` | `true` | 守卫分支是否必须包含重建逻辑（true 时也允许抛错降级） |

- 适配新模块：若引入新的可空外部资源（如 `this.pool`、`this.socket`），追加到 `nullable_field_patterns`。

## 优雅停止参数

> 优雅停止规则（见 `graceful-shutdown-rule.md`）所依赖的参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `graceful_shutdown.enabled` | `true` | 是否启用优雅停止检查 |
| `graceful_shutdown.severity` | `error` | 违规严重级别 |
| `graceful_shutdown.resource_keywords` | `spawn, setInterval, connect, createClient` | 触发"需要清理钩子"检查的资源创建关键字 |
| `graceful_shutdown.shutdown_signals` | `SIGINT, SIGTERM` | 必须注册的信号列表 |
| `graceful_shutdown.child_terminate_signal` | `SIGTERM` | 通知子进程停止的信号 |
| `graceful_shutdown.child_force_kill_timeout_ms` | `5000` | SIGTERM 后等待子进程退出的超时，超时改用 SIGKILL |
| `graceful_shutdown.exit_code_on_clean` | `0` | 清理完成后的退出码 |
| `graceful_shutdown.aggregate_in_entry` | `true` | 是否在入口文件聚合所有清理函数 |

- Serverless / FaaS 环境：将 `enabled` 设为 `false`（平台管理生命周期）。
- Windows 开发环境：`shutdown_signals` 保持 `SIGINT, SIGTERM`，PowerShell 与 cmd 均能正确传递。

## 敏感字段脱敏参数

> 敏感字段脱敏规则（见 `sensitive-field-masking-rule.md`）所依赖的参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `sensitive_field_masking.enabled` | `true` | 是否启用敏感字段脱敏 |
| `sensitive_field_masking.severity` | `error` | 违规严重级别 |
| `sensitive_field_masking.sensitive_field_patterns` | `key\|token\|secret\|password\|authtoken` | 敏感字段名匹配模式（正则，大小写不敏感） |
| `sensitive_field_masking.mask_strategy` | `last4-padstart` | 脱敏策略：保留末 4 位 + 前置 `*` padStart 到原长 |
| `sensitive_field_masking.mask_char` | `*` | 脱敏占位字符 |
| `sensitive_field_masking.mask_visible_suffix` | `4` | 末尾保留可见字符数 |
| `sensitive_field_masking.min_mask_length` | `4` | 原值长度 ≤ 此值时全部脱敏（不保留末尾） |
| `sensitive_field_masking.empty_value_semantics` | `no-change` | POST 空串语义：`no-change`（不修改）/ `clear`（清空） |

- 引入新敏感字段（如 `apiKey`、`refreshToken`）：若命名匹配 `sensitive_field_patterns` 自动覆盖；否则追加模式。
- 调试场景需要明文返回：临时将 `enabled` 设为 `false`，但禁止提交到主分支。

## 类型同步守卫参数

> 类型同步守卫规则（见 `type-sync-rule.md`）所依赖的参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `type_sync.enabled` | `true` | 是否启用类型同步检查 |
| `type_sync.severity` | `error` | 违规严重级别 |
| `type_sync.backend_types_path` | `services/api/src/types.ts` | 后端类型文件相对路径 |
| `type_sync.frontend_types_path` | `packages/web/src/types.ts` | 前端类型文件相对路径 |
| `type_sync.backend_typecheck_command` | `npx tsc --noEmit` | 后端类型检查命令 |
| `type_sync.frontend_typecheck_command` | `npx vue-tsc --noEmit` | 前端类型检查命令（Vue 项目用 vue-tsc） |
| `type_sync.allow_frontend_extra_fields` | `false` | 是否允许前端类型包含后端没有的字段 |
| `type_sync.allow_optional_mismatch` | `false` | 是否允许后端必填 / 前端可选的差异 |

- 适配纯 React 项目：`frontend_typecheck_command` 改为 `npx tsc --noEmit`。
- 适配 OpenAPI 自动生成：将 `enabled` 设为 `false`，由代码生成保证契约。
- 适配 monorepo 共享 types 包：将 `enabled` 设为 `false`，前端直接 import 共享包。

## 滚动容器守卫参数

> 滚动容器单一职责规则（见 [references/scroll-container-rule.md](../references/scroll-container-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件只描述通用模式，不硬编码具体 CSS 属性或选择器。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `scroll_container.enabled` | `true` | 是否启用滚动容器守卫 |
| `scroll_container.severity` | `error` | 违规严重级别 |
| `scroll_container.max_overflow_layers` | `1` | 容器链路上允许的 `overflow-y: auto` 最大层数 |
| `scroll_container.scroll_keywords` | `overflow-y: auto, overflow: auto, overflow-y: scroll` | 触发滚动容器检查的 CSS 关键字（逗号分隔） |
| `scroll_container.flex_shrink_required_in_flex_column` | `true` | flex-direction: column 容器内的自然高度子项是否必须 flex-shrink: 0 |
| `scroll_container.glass_card_overflow_warning` | `true` | 使用 overflow: hidden 的卡片类包裹长内容时是否告警 |

- 适配 CSS Grid 布局项目：将 `flex_shrink_required_in_flex_column` 设为 `false`（grid 子项默认不收缩）。
- 适配必须双重滚动的场景（如表格内嵌独立滚动）：将 `max_overflow_layers` 调整为 `2` 并在代码注释中说明双重滚动必要性。

## SPA 内部跳转参数

> SPA 内部跳转规则（见 [references/spa-navigation-rule.md](../references/spa-navigation-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件不硬编码事件名或视图名，所有约定从本节读取。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `spa_navigation.enabled` | `true` | 是否启用 SPA 跳转守卫 |
| `spa_navigation.severity` | `error` | 违规严重级别 |
| `spa_navigation.event_name_pattern` | `{project}:navigate` | 自定义事件命名模板（`{project}` 占位符运行时替换） |
| `spa_navigation.project_name` | `karpathy` | 项目名（用于事件名替换） |
| `spa_navigation.allowed_view_source` | `config` | 允许的视图名列表来源（`config` / `route-definition`） |
| `spa_navigation.lifecycle_hook_required` | `true` | 监听器是否必须在 onMounted/onBeforeUnmount 配对管理 |

- 适配 vue-router / react-router 项目：将 `enabled` 设为 `false`，由路由库管理跳转。
- 适配多项目共用组件库：`project_name` 改为各项目独立配置，避免事件名冲突。

## 更新检查参数

> 更新检查缓存规则（见 [references/update-check-rule.md](../references/update-check-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件不硬编码 TTL 或外部 API URL，所有数值从本节读取。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `check_update.enabled` | `true` | 是否启用更新检查规则 |
| `check_update.severity` | `error` | 违规严重级别 |
| `check_update.cache_ttl_ms` | `300000` | 后端缓存 TTL（毫秒，默认 5 分钟） |
| `check_update.first_check_delay_ms` | `5000` | 前端首次检查延迟（毫秒，默认 5 秒） |
| `check_update.poll_interval_ms` | `300000` | 前端轮询间隔（毫秒，默认 5 分钟，必须 ≥ cache_ttl_ms） |
| `check_update.latest_state_revert_ms` | `3000` | "已是最新"状态自动回 idle 的延迟（毫秒） |
| `check_update.release_feed_url` | `""` | 外部发布通道 URL（空字符串表示无外网通道） |
| `check_update.offline_mode` | `true` | 离线模式：true 时固定返回 has_update=false，不发起外部请求 |
| `check_update.required_states` | `idle,loading,latest,newer,error` | 状态机必须覆盖的状态列表（逗号分隔） |

- 适配公网开源项目：将 `offline_mode` 设为 `false`，`release_feed_url` 填实际 GitHub Releases API URL。
- 适配内网部署：保持 `offline_mode: true`，避免发起注定失败的外部请求。
- 适配频繁发布项目：将 `cache_ttl_ms` 降至 `60000`（1 分钟），`poll_interval_ms` 同步降低。

## 适配新项目

修改本文件中的参数值即可适配不同项目：
- 路径锚点：根据模块系统选择 `import.meta.url` 或 `__dirname`
- 缓存 TTL：根据业务实时性要求调整
- 白名单正则：根据 ID 生成策略选择 UUID/ULID/Snowflake
- 权威源：根据架构选择 `backend`/`file`/`database`
- 编码回退：根据系统区域选择 `gb2312`/`gbk`/`shift-jis` 等
- 命令分隔符：PowerShell 用 `;`，bash 用 `&&`
- 路由注册：根据框架选择 `register` / `use`，自动发现框架可禁用
- 可空字段：新增外部资源类型时追加到 `nullable_field_patterns`
- 优雅停止：Serverless / FaaS 环境可禁用
- 敏感字段：新字段命名若不匹配模式需追加正则
- 类型同步：OpenAPI / 共享 types 包项目可禁用
- 滚动容器：CSS Grid 项目可关闭 flex-shrink 守卫
- SPA 跳转：vue-router / react-router 项目可关闭事件派发守卫
- 更新检查：公网项目填 release_feed_url，内网项目保持 offline_mode