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
| `type_sync.backend_types_path` | `api/src/types.ts` | 后端类型文件相对路径 |
| `type_sync.frontend_types_path` | `frontend/src/types.ts` | 前端类型文件相对路径 |
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

## SVG 资源创建参数

> SVG/资源文件创建规则（见硬约束 #19）所依赖的可配置参数集中在本节。
> 规则文件不硬编码具体编码值或工具名，所有参数从本节读取。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `svg_resource.enabled` | `true` | 是否启用 SVG 资源创建守卫 |
| `svg_resource.severity` | `error` | 违规严重级别 |
| `svg_resource.encoding` | `utf-8-no-bom` | SVG 文件编码（含中文时必须） |
| `svg_resource.ascii_preferred` | `true` | 优先使用纯 ASCII（避免 Write 工具编码陷阱） |
| `svg_resource.fallback_write_method` | `powershell-utf8noBom` | Write 工具不可靠时的回退写入方法 |
| `svg_resource.cache_bust_param` | `?v={version}` | HTML 引用 SVG 时的破缓存版本参数模板 |
| `svg_resource.version_increment_on_change` | `true` | SVG 内容变更时 HTML 引用必须递增版本号 |

- 适配无中文项目：`ascii_preferred` 保持 `true` 即可。
- 适配含中文 SVG 项目：必须确保文件以 `utf-8-no-bom` 保存，必要时用 PowerShell 回退方法。

## 构建产物验证参数

> 构建产物验证规则（见硬约束 #20）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `build_verification.enabled` | `true` | 是否启用构建产物验证 |
| `build_verification.severity` | `error` | 违规严重级别 |
| `build_verification.required_http_status` | `200` | 构建产物 HTTP 访问必需的状态码 |
| `build_verification.content_length_match` | `true` | Content-Length 必须与磁盘文件大小一致 |
| `build_verification.key_strings_check` | `true` | 必须验证 bundle 中包含新增的关键字符串 |
| `build_verification.serving_endpoint` | `http://localhost:{api_port}/assets/{bundle_filename}` | 构建产物访问端点模板 |
| `build_verification.bundle_directory` | `api/public/assets/` | 构建产物输出目录（相对项目根） |

- 适配 CDN 部署：`serving_endpoint` 改为 CDN URL 模板。
- 适配多入口项目：`bundle_directory` 改为实际输出目录。

## PowerShell 字符串验证参数

> PowerShell 字符串验证模式规则（见硬约束 #21）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `powershell_string_verification.enabled` | `true` | 是否启用 PowerShell 字符串验证模式守卫 |
| `powershell_string_verification.severity` | `error` | 违规严重级别 |
| `powershell_string_verification.forbidden_patterns` | `curl.exe -s \|管道赋值 + .Contains()` | 禁止的字符串验证模式 |
| `powershell_string_verification.recommended_pattern` | `Invoke-WebRequest + .Content.Contains()` | 推荐的字符串验证模式 |
| `powershell_string_verification.content_property` | `Content` | Invoke-WebRequest 返回对象的字符串内容属性名 |

- 适配 Linux/Mac：`recommended_pattern` 改为 `curl + bash 字符串包含`。
- 适配 Python 脚本：本节不适用，由 Python 字符串方法替代。

## 浏览器自动化降级参数

> 浏览器自动化降级链规则（见硬约束 #22）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `browser_automation_fallback.enabled` | `true` | 是否启用浏览器自动化降级链 |
| `browser_automation_fallback.severity` | `warning` | 违规严重级别（降级为警告，不阻断） |
| `browser_automation_fallback.chain` | `playwright-mcp,browser-use-subagent,powershell-curl` | 降级链路顺序（逗号分隔） |
| `browser_automation_fallback.log_degradation_reason` | `true` | 每级降级必须记录降级原因 |
| `browser_automation_fallback.max_retry_per_level` | `1` | 每级降级的最大重试次数 |
| `browser_automation_fallback.timeout_ms` | `30000` | 每级降级的超时时间（毫秒） |

- 适配无 MCP 环境：`chain` 移除 `playwright-mcp`，从 `browser-use-subagent` 开始。
- 适配纯命令行环境：`chain` 仅保留 `powershell-curl`。

## 主题感知图标设计参数

> 主题感知图标设计规则（见硬约束 #23）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `theme_aware_icon.enabled` | `true` | 是否启用主题感知图标设计守卫 |
| `theme_aware_icon.severity` | `error` | 违规严重级别 |
| `theme_aware_icon.color_attribute` | `currentColor` | SVG 必须使用的颜色属性值 |
| `theme_aware_icon.stroke_style` | `line` | 图标风格（line=线条风，fill=填充风） |
| `theme_aware_icon.glow_filter` | `drop-shadow(0 0 {radius}px currentColor)` | 主题色光晕滤镜模板 |
| `theme_aware_icon.glow_radius_default` | `4` | 光晕默认半径（px） |
| `theme_aware_icon.glow_radius_hover` | `8` | hover 时光晕半径（px） |
| `theme_aware_icon.viewbox_standard` | `0 0 24 24` | SVG viewBox 标准（24x24 网格） |
| `theme_aware_icon.stroke_width_default` | `1.8` | stroke 默认宽度 |
| `theme_aware_icon.forbidden_color_values` | `#hex, rgb(), rgba(), hsl()` | 禁止硬编码的颜色值格式 |

- 适配 Material Design 图标：`stroke_style` 改为 `fill`，`stroke_width_default` 不适用。
- 适配无主题项目：`color_attribute` 改为具体色值，`glow_filter` 设为空字符串。

## 导航栏双模式参数

> 导航栏双模式设计规则（见硬约束 #24）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `nav_dual_mode.enabled` | `true` | 是否启用导航栏双模式守卫 |
| `nav_dual_mode.severity` | `error` | 违规严重级别 |
| `nav_dual_mode.nav_threshold` | `7` | 菜单项数量阈值，超过此值必须实现双模式 |
| `nav_dual_mode.tooltip_implementation` | `pure-css-hover` | tooltip 实现方式（pure-css-hover=纯 CSS hover，js-tooltip=JS 库） |
| `nav_dual_mode.transition_mode` | `out-in` | Vue Transition 切换模式 |
| `nav_dual_mode.state_persistence_key` | `navCollapsed` | localStorage 持久化 key 名 |
| `nav_dual_mode.state_persistence_type` | `boolean` | 持久化值类型（boolean/string） |
| `nav_dual_mode.expanded_icon_size` | `16` | 展开模式图标尺寸（px） |
| `nav_dual_mode.collapsed_icon_size` | `22` | 折叠模式图标尺寸（px，通常略大于展开模式） |
| `nav_dual_mode.tooltip_position` | `bottom` | tooltip 出现位置（bottom/top/right/left） |
| `nav_dual_mode.tooltip_delay_ms` | `200` | tooltip 显示延迟（毫秒） |

- 适配移动端优先项目：`nav_threshold` 改为 `5`，`tooltip_implementation` 改为 `js-tooltip`（移动端无 hover）。
- 适配 vue-router 项目：`enabled` 设为 `false`，由路由库管理导航。
- 适配菜单项固定较少（≤7）的项目：`enabled` 设为 `false`，无需双模式。

## 配置读取一致性参数

> 同一配置项存在多个读取入口时，必须统一使用单一读取函数。
> 复盘来源：AI 服务模块开发中，新增 `getEffectiveApiKey()` 但启动入口 `index.ts` 仍用 `process.env`，导致 config.json 中的 apiKey 被忽略，LLM 401 错误。

| 参数 | 值 | 说明 |
|------|-----|------|
| `config_read_single_source` | `true` | 同一配置项的所有读取入口必须使用统一函数 |
| `config_read_entries` | `startup,hot_reload,api_get,api_test` | 配置读取入口清单（需全部一致） |
| `config_check_command` | `grep -rn "process.env\[" services/api/src` | 检查是否有绕过统一函数的直接环境变量读取 |

## 热更新闭环参数

> 保存配置后必须验证运行实例是否同步更新。
> 复盘来源：保存 AI 配置后 adapter 实例仍持有旧 apiKey，需重启才生效。

| 参数 | 值 | 说明 |
|------|-----|------|
| `hot_update_required` | `true` | 可热更新字段必须实现 updateConfig 并在路由层调用 |
| `hot_update_chain` | `save→persist→updateConfig→response` | 热更新闭环流程 |
| `hot_update_verifiable` | `true` | 热更新后必须可通过 API 验证生效 |
| `hot_update_fields` | `model,provider,baseUrl,apiKey,maxSteps,tokenBudget,staleDays` | 可热更新字段清单 |

## 脱敏值回传参数

> 敏感字段（API Key）的脱敏值回传处理规则。
> 复盘来源：前端保存配置时回传脱敏值，后端需正确识别为"未修改"。

| 参数 | 值 | 说明 |
|------|-----|------|
| `mask_prefix` | `****` | 脱敏值前缀标识 |
| `mask_suffix_length` | `4` | 保留末尾字符数 |
| `mask_treatment_unmodified` | `skip` | 脱敏值回传视为未修改，跳过更新 |
| `mask_treatment_empty` | `clear` | 空字符串视为清除 |
| `mask_treatment_new` | `update` | 其他值视为新值，写入存储 |

## 预设配置外置参数

> 预设列表必须集中定义在后端常量，前端通过 API 获取。
> 复盘来源：新增 Agnes AI 预设时，前后端各存一份导致不一致。

| 参数 | 值 | 说明 |
|------|-----|------|
| `preset_source` | `backend_constant` | 预设定义集中位置 |
| `preset_frontend_access` | `api_only` | 前端仅通过 API 获取预设 |
| `preset_duplication` | `forbidden` | 禁止前后端各存一份预设 |

## 类型收窄参数（Vue 3 + TypeScript）

> ref<T|null> 在 await 后不能直接访问，需用计算属性或局部变量。
> 复盘来源：vue-tsc 报错"Object is possibly null"。

| 参数 | 值 | 说明 |
|------|-----|------|
| `ref_nullable_pattern` | `computed_or_local_var` | 可空 ref 的访问模式 |
| `ref_await_rule` | `use_local_var` | await 后访问 ref 必须先赋值给局部变量 |
| `ref_template_rule` | `use_computed` | 模板中访问可空 ref 必须用计算属性 |

## Async 可靠性参数

> async/await + IPC/Playwright 场景的可靠性参数。
> 复盘来源：浏览器登录 91s 超时，Playwright context.cookies() 永久挂起阻塞事件循环，asyncio.Task 心跳失效。

| 参数 | 值 | 说明 |
|------|-----|------|
| `default_call_timeout_sec` | `5.0` | 单次 async 调用默认超时（秒） |
| `stage_hard_timeout_sec` | `30.0` | 阶段硬超时（秒），整体卡住时强制结束 |
| `task_total_timeout_sec` | `180.0` | 任务整体超时（秒），由主进程 kill 子进程 |
| `heartbeat_interval_sec` | `3.0` | 心跳线程更新 status file 的间隔 |
| `heartbeat_max_interval_sec` | `10.0` | 业务循环内心跳更新的最大间隔（超过此值需独立线程） |
| `thread_join_timeout_sec` | `5.0` | 线程 join 超时（秒） |
| `status_file_update_strategy` | `thread` | 状态文件更新策略（thread=独立线程，async_loop=事件循环内） |
| `fallback_data_pattern` | `best_holder` | 兜底数据传递模式（可变容器） |
| `timeout_whitelist` | `asyncio.sleep,Promise.resolve` | 无需超时保护的 async 调用白名单 |
| `blocking_risk_apis` | `playwright.*,node_fetch,fs.promises.readFile,child_process.exec` | 可能阻塞事件循环的 API 列表 |

### 多层超时参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `multi_layer_timeout.level_1_call` | `default_call_timeout_sec` | 第 1 层：单次调用超时 |
| `multi_layer_timeout.level_2_stage` | `stage_hard_timeout_sec` | 第 2 层：阶段硬超时 |
| `multi_layer_timeout.level_3_task` | `task_total_timeout_sec` | 第 3 层：任务整体超时 |

### 适配新项目（Async 可靠性）

修改 `config/tech-stack.json` 的 `async_reliability` 字段即可适配不同项目：
- 超时阈值：根据 IPC 响应速度调整（Playwright 通常 5s，数据库 3s，文件 I/O 10s）
- 心跳间隔：根据主进程的存活检测窗口调整（通常为主进程超时的 1/3）
- 阻塞风险 API：根据项目使用的 IPC 库补充（如 puppeteer、selenium、requests-futures）
- 白名单：根据项目约定的安全 async 调用补充

## 类型检查缓存清理参数

> 类型检查缓存清理规则（见 [references/typecheck-cache-rule.md](../references/typecheck-cache-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件不硬编码缓存文件名或路径，所有参数从本节读取，便于适配不同构建工具。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `typecheck_cache.enabled` | `true` | 是否启用缓存清理守卫 |
| `typecheck_cache.severity` | `error` | 违规严重级别 |
| `typecheck_cache.incremental_cache_files` | `tsconfig.tsbuildinfo,tsconfig.app.tsbuildinfo,tsconfig.node.tsbuildinfo` | TypeScript 增量缓存文件名（逗号分隔） |
| `typecheck_cache.vite_cache_dirs` | `.vite,node_modules/.vite` | Vite 缓存目录（逗号分隔） |
| `typecheck_cache.stale_artifact_patterns` | `src/**/*.js` | 旧版 TypeScript 增量编译产物 glob（污染源码目录） |
| `typecheck_cache.typecheck_command` | `npx vue-tsc --noEmit` | 类型检查命令 |
| `typecheck_cache.prevent_bypass_assertions` | `as any, as unknown, ! postfix, // @ts-ignore, // @ts-expect-error` | 禁止用于绕过幽灵错误的断言模式（逗号分隔） |

- 适配纯 React 项目：`typecheck_command` 改为 `npx tsc --noEmit`，`stale_artifact_patterns` 改为 `dist/**/*.js`。
- 适配 Webpack 项目：`vite_cache_dirs` 改为 `node_modules/.cache`。
- 适配 monorepo：`incremental_cache_files` 列出各子项目的 tsbuildinfo 路径。
- 适配 CI 环境：将 `enabled` 设为 `false`（CI 每次 fresh checkout 无缓存问题）。

## Composable API 先读后用参数

> Composable API 先读后用规则（见 [references/composable-api-rule.md](../references/composable-api-rule.md)）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `composable_api.enabled` | `true` | 是否启用 Composable 先读后用守卫 |
| `composable_api.severity` | `error` | 违规严重级别 |
| `composable_api.pattern_prefixes` | `use, store, composable` | 触发"先读后用"检查的命名前缀（逗号分隔） |
| `composable_api.excluded_patterns` | `useRouter, useRoute, useStore, useState` | 豁免列表（标准库 composable，逗号分隔） |
| `composable_api.required_confirmation` | `export_shape,method_signature,setup_order` | 必须确认的 API 形状要素（逗号分隔） |
| `composable_api.diagnostic_code_must_not_rebuild` | `true` | 诊断代码禁止调用 `$dispose` / `_s.delete` 重建 store |

- 适配 React 项目：`pattern_prefixes` 改为 `use, hook`。
- 适配 Angular 项目：`pattern_prefixes` 改为 `service, inject`。
- 适配无 store 项目：将 `enabled` 设为 `false`。

## 混合类型运行时分流参数

> 混合类型运行时分流规则（见 [references/mixed-type-dispatch-rule.md](../references/mixed-type-dispatch-rule.md)）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `mixed_type_dispatch.enabled` | `true` | 是否启用混合类型分流守卫 |
| `mixed_type_dispatch.severity` | `error` | 违规严重级别 |
| `mixed_type_dispatch.forbidden_assertions` | `as any, as unknown as, as T` | 禁止的强制类型断言模式（逗号分隔） |
| `mixed_type_dispatch.required_type_guards` | `typeof, in, instanceof` | 必须使用的运行时分流运算符（任一即可，逗号分隔） |
| `mixed_type_dispatch.helper_function_required` | `true` | 是否必须封装为独立 helper 函数（而非内联 typeof） |
| `mixed_type_dispatch.helper_naming_pattern` | `is<TypeName>` | helper 函数命名约定 |

- 适配 JavaScript 项目（无类型）：仍需用 `typeof` / `in` 运行时分流，但无需 type guard。
- 适配严格类型项目：可将 `helper_function_required` 降级为 `suggestion`。
- 适配无类型升级场景：将 `enabled` 设为 `false`。

## Vue SFC 单 script 块参数

> Vue SFC 单 script 块规则（见 [references/sfc-single-script-rule.md](../references/sfc-single-script-rule.md)）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `sfc_script_block.enabled` | `true` | 是否启用 SFC 单 script 块守卫 |
| `sfc_script_block.severity` | `error` | 违规严重级别 |
| `sfc_script_block.allowed_blocks` | `script setup lang="ts"` | 允许的 script 块类型（唯一） |
| `sfc_script_block.exception_allowed` | `true` | 是否允许例外情况（双 script 块） |
| `sfc_script_block.exception_conditions` | `name export,inheritAttrs:false,custom_options,third_party_lib` | 例外条件（逗号分隔） |
| `sfc_script_block.exception_comment_required` | `true` | 例外必须显式注释说明用途 |
| `sfc_script_block.exception_comment_pattern` | `// 例外：` | 例外注释前缀模式 |

- 适配 Vue 2 项目：将 `enabled` 设为 `false`（无 setup 语法）。
- 适配 React 项目：本节不适用。
- 适配全 Options API Vue 3 项目：将 `allowed_blocks` 改为 `script`，`exception_allowed` 改为 `false`。

## E2E 测试前置服务检查参数

> E2E 测试前置服务检查规则（见 [references/e2e-precheck-rule.md](../references/e2e-precheck-rule.md)）所依赖的可配置参数集中在本节。
> 规则文件不硬编码端口号或健康检查路径，所有参数从本节读取，便于适配不同项目。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `e2e_precheck.enabled` | `true` | 是否启用前置服务检查 |
| `e2e_precheck.severity` | `error` | 违规严重级别（error = 测试中止） |
| `e2e_precheck.required_ports` | `3000,5173` | 必须监听的端口列表（逗号分隔） |
| `e2e_precheck.port_check_state` | `Listen` | 端口就绪状态判定 |
| `e2e_precheck.port_check_method` | `Get-NetTCPConnection` | 端口检测方法 |
| `e2e_precheck.health_check_endpoint` | `/health` | 健康检查路径 |
| `e2e_precheck.health_check_expected_status` | `200` | 健康检查期望状态码 |
| `e2e_precheck.startup_timeout_ms` | `30000` | 服务启动超时（毫秒） |
| `e2e_precheck.port_poll_interval_ms` | `1000` | 端口轮询间隔（毫秒） |
| `e2e_precheck.browser_launch_check` | `true` | 是否检查浏览器可启动 |
| `e2e_precheck.service_start_script` | `automation.ps1 -Action start` | 服务启动脚本 |
| `e2e_precheck.auto_start_on_failure` | `true` | 检查失败时是否自动启动服务 |

- 适配纯前端项目（无后端）：`required_ports` 改为仅前端端口（如 `5173`），`health_check_endpoint` 设为空字符串跳过。
- 适配 Docker 部署：`service_start_script` 改为 `docker-compose up -d`。
- 适配 CI 环境：`auto_start_on_failure` 设为 `false`（CI 通常已独立启动服务）。
- 适配云环境：`port_check_method` 改为 `Test-NetConnection`（跨网络）。

## 测试用例与代码结构同步参数

> 测试用例与代码结构同步规则（见 [references/test-case-sync-rule.md](../references/test-case-sync-rule.md)）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `test_case_sync.enabled` | `true` | 是否启用测试同步守卫 |
| `test_case_sync.severity` | `error` | 违规严重级别 |
| `test_case_sync.test_file_patterns` | `**/test_*.py,**/test_*.ts,**/*.spec.ts,**/*.test.ts` | 测试文件 glob 模式（逗号分隔） |
| `test_case_sync.selector_patterns` | `\.[-\w]+, #[-\w]+, \[class="[^"]+"\], data-testid="[^"]+"` | 选择器匹配模式（CSS class / id / attribute，逗号分隔） |
| `test_case_sync.require_same_commit` | `true` | 代码与测试用例是否必须在同一 commit |
| `test_case_sync.silent_failure_forbidden` | `true` | 禁止 try/except 静默吞掉选择器失效错误 |
| `test_case_sync.stale_selector_threshold` | `0` | 允许的失效选择器数量（默认 0） |
| `test_case_sync.auto_update_on_refactor` | `true` | 重构时是否自动建议更新测试用例 |

- 适配 Cypress 项目：`test_file_patterns` 改为 `**/cypress/integration/*.spec.js`。
- 适配 Jest 项目：`test_file_patterns` 改为 `**/__tests__/*.test.ts`。
- 适配无自动化测试项目：将 `enabled` 设为 `false`，但建议补充测试。

## 阅读视野优化参数

> 阅读视野优化与输入区固定规则（见 [references/reading-viewport-rule.md](../references/reading-viewport-rule.md)）所依赖的可配置参数集中在本节。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `reading_viewport.enabled` | `true` | 是否启用阅读视野守卫 |
| `reading_viewport.severity` | `error` | 违规严重级别 |
| `reading_viewport.applicable_views` | `Query, Reader, Document, Chat, Browse` | 适用视图列表（逗号分隔） |
| `reading_viewport.max_header_ratio` | `0.15` | 标题头区域最大占比（15%） |
| `reading_viewport.min_content_ratio` | `0.75` | 内容区最小占比（75%） |
| `reading_viewport.input_bar_position` | `sticky bottom` | 输入区定位策略 |
| `reading_viewport.input_bar_z_index` | `2` | 输入区 z-index（高于内容区） |
| `reading_viewport.input_bar_background` | `rgba(var(--bg-scene-rgb), 0.85)` | 毛玻璃背景（CSS 变量形式，跟随主题） |
| `reading_viewport.input_bar_backdrop_filter` | `blur(12px)` | 毛玻璃模糊滤镜 |
| `reading_viewport.input_bar_padding` | `12px 4px 4px` | 输入区内边距 |
| `reading_viewport.calc_template` | `calc(100vh - {nav_height}px - {other_fixed}px)` | 内容区高度计算模板 |

- 适配移动端项目：`input_bar_position` 改为 `fixed bottom`（移动端 sticky 兼容性问题），`max_header_ratio` 改为 `0.1`。
- 适配桌面端固定窗口：`min_content_ratio` 改为 `0.8`（窗口已固定大小，可利用空间更多）。
- 适配无输入区视图：从 `applicable_views` 中移除该视图名。
- 适配多输入区视图（如评论 + 主输入）：`input_bar_position` 保持 `sticky bottom`，主输入区在最底部。

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
- 类型检查缓存：CI 环境可禁用（fresh checkout 无缓存），Webpack 项目改用 `node_modules/.cache`
- Composable API：无 store 项目可禁用；React 项目改 `pattern_prefixes` 为 `use, hook`
- 混合类型分流：无类型升级场景可禁用；JavaScript 项目仍需 typeof 分流但无需 type guard
- SFC 单 script 块：Vue 2 项目禁用；React 项目不适用
- E2E 前置检查：纯前端项目仅检查前端端口；CI 环境关闭 `auto_start_on_failure`
- 测试用例同步：无自动化测试项目可禁用，但建议补充测试
- 阅读视野：移动端改 `input_bar_position` 为 `fixed bottom`；无输入区视图从 `applicable_views` 移除
- Tauri ACL：Tauri 1.x 项目禁用（无 ACL 模型）；多窗口项目按窗口分 capability 文件
- Tauri 外部 URL：纯离线 Tauri 应用禁用；远程 SPA 部署改 `allowed_url_patterns` 为生产域名
- Tauri webview 隔离：单窗口项目禁用；不同源多窗口天然隔离无需此规则
- Tauri 透明窗口：不透明窗口项目禁用；React 项目改 `app_container_id` 为 `root`
- Tauri 构建脚本：无前端 Tauri 项目禁用；npm/yarn 项目改 `spa_build_command` 为对应 workspace 命令
- Tauri drag-click 冲突：用原生窗口装饰（`decorations: true`）的项目禁用；触屏设备阈值放大到 10px
- PowerShell stderr：Bash 项目不适用；需要捕获输出的场景用 `Start-Process -RedirectStandardOutput`

## 项目目录结构参数（project_structure）

> CODING-033~037 目录结构分离、脚本命名统一、gitignore 完整性、文档归并、运行时数据外迁的参数。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| source_dirs | `["packages/", "services/"]` | 源码目录列表 |
| runtime_data_dir | `data/vault/` | 运行时数据目录 |
| build_output_dirs | `["dist/", "build/"]` | 构建产物目录 |
| external_toolchain_dirs | `["w64devkit/"]` | 外部工具链目录（不入库） |
| docs_base_dir | `docs/` | 文档根目录 |
| docs_subdirs | `["requirements/", "design/", "plan/", "dev-guides/"]` | 文档子目录 |
| scripts_dir | `scripts/` | 脚本目录 |
| ide_skills_dir | `.trae/skills/` | IDE 技能目录 |
| seed_data_patterns | `["concepts/", "comparisons/", "SCHEMA.md"]` | 种子数据（入库） |
| runtime_data_patterns | `["raw/", "entities/", "queries/", "log.md", "index.md", ".harness/"]` | 运行时数据（gitignore） |
| config_files_to_update | `["config.json", "src/config.ts", "install.ps1", "setup-env.ps1"]` | 数据外迁时需同步更新的配置文件 |

## 脚本命名参数（script_naming）

> CODING-034 脚本命名统一原则的参数。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| naming_style | `kebab-case` | 脚本文件命名风格 |
| naming_language | `en` | 命名语言 |
| bat_role | `thin-wrapper` | bat 文件角色 |
| bat_max_lines | `5` | bat 文件最大行数（不含注释），超过判定为承载过多逻辑 |
| bat_content_template | `@call powershell -File "%~dp0{script}.ps1" %*` | bat 标准内容模板 |
| forbidden_patterns | `["启动服务", "停止服务", "环境配置", "前端构建", "构建打包"]` | 禁止的中文文件名 |

## gitignore 规则参数（gitignore_rules）

> CODING-035 .gitignore 完整性原则的参数。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| runtime_data_ignore | `["data/vault/raw/", "data/vault/log.md", "data/vault/index.md"]` | 运行时数据忽略规则 |
| build_output_ignore | `["dist/", "build/", "*.exe"]` | 构建产物忽略规则 |
| toolchain_ignore | `["w64devkit/"]` | 外部工具链忽略规则 |
| binary_wrapper_ignore | `["scripts/windres.exe"]` | 二进制 wrapper 忽略规则 |
| test_artifacts_ignore | `["test_screenshots/", "test_*.json"]` | 测试产物忽略规则 |
| verification_command | `git check-ignore -v` | 规则验证命令 |
| tracked_check_command | `git ls-files --error-unmatch` | 已跟踪检查命令 |
| untrack_command | `git rm --cached` | 移除索引命令（非破坏性） |

## 文档结构参数（docs_structure）

> CODING-036 文档归并原则的参数。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| requirements_dir | `docs/requirements/` | 需求文档目录 |
| design_dir | `docs/design/` | 设计文档目录 |
| plan_dir | `docs/plan/` | 计划文档目录 |
| dev_guides_dir | `docs/dev-guides/` | 开发规范目录 |
| forbidden_doc_locations | `["project_root", "services/*/src/"]` | 禁止存放文档的位置 |
| skill_source_dir | `.trae/skills/` | 技能源目录 |
| skill_doc_redirect | `docs/dev-guides/` | 技能文档迁移目标 |

## 路径验证参数（path_verification）

> CODING-038 file: 协议路径验证原则的参数。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| verify_command | `Resolve-Path` | PowerShell 路径解析命令 |
| file_protocol_pattern | `^file:` | file: 协议匹配正则 |
| manual_calculation_forbidden | `true` | 禁止手动计算 ../../../ 层级 |
| package_json_files | `["package.json", "services/api/package.json"]` | 需检查的 package.json 文件列表 |

## 搜索验证参数（search_verification）

> CODING-039 搜索结果交叉验证原则的参数。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| primary_search_tools | `["Glob", "Grep", "LS"]` | 主要搜索工具 |
| fallback_search_tools | `["PowerShell Test-Path", "PowerShell Resolve-Path"]` | 兜底搜索工具 |
| ls_truncate_threshold | `40000` | LS 输出截断阈值（字符数） |
| cross_verify_required | `true` | 阴性结果是否必须交叉验证 |
| glob_escape_chars | `["+", "(", ")", "[", "]"]` | Glob 需转义的特殊字符 |
| grep_content_patterns | `["export class {name}", "export.*{name}"]` | Grep 内容搜索模式 |

## 构建产物源码化参数（build_artifact_source）

> CODING-040 构建产物源码化原则的参数。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| source_extensions | `[".c", ".rs", ".go"]` | 源码文件扩展名 |
| binary_extensions | `[".exe", ".dll", ".so", ".dylib"]` | 二进制文件扩展名 |
| compile_command_template | `{compiler} -o {output} {source}` | 编译命令模板 |
| setup_script_files | `["tauri-setup-env.ps1"]` | 需包含编译步骤的 setup 脚本 |

## 主题色变量映射参数（theme_color_mapping）

> CODING-041~046 主题色变量映射规则的参数集中在本节。
> 规则文件 [references/theme-color-mapping-rule.md](../references/theme-color-mapping-rule.md) 不硬编码任何具体颜色值、变量名或 alpha 列表。
> 复盘来源：仪表盘 .recent-log 与 FloatingChat 在浅色主题下辨识度低，11 处硬编码 rgba() 颜色替换为 CSS 变量。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `theme_color_mapping.enabled` | `true` | 是否启用主题色变量映射守卫 |
| `theme_color_mapping.severity` | `error` | 违规严重级别 |
| `theme_color_mapping.variable_definition_files` | `["packages/web/src/styles/themes.css", "packages/web/src/styles/variables.css"]` | CSS 变量定义文件列表（Grep 查找可用变量名） |
| `theme_color_mapping.whitelist_patterns` | `rgba(255, 255, 255, *), transparent, inherit, currentColor` | 允许硬编码的颜色值模式（逗号分隔，支持通配符） |
| `theme_color_mapping.forbidden_color_formats` | `rgba(), rgb(), #hex, hsl(), hsla()` | 禁止硬编码的颜色值格式（逗号分隔） |
| `theme_color_mapping.allowed_alpha_values` | `03, 05, 06, 08, 10, 12, 15, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70` | 允许的 alpha 百分比列表（两位数字，逗号分隔） |
| `theme_color_mapping.alpha_variable_pattern` | `--accent-{color}-a{NN}` | alpha 变体变量名命名模板 |
| `theme_color_mapping.color_identifiers` | `cyan, purple, pink, magenta` | 支持的颜色标识列表（替换 {color} 占位符） |
| `theme_color_mapping.semantic_priority` | `scene_bg, card_bg, text, border, shadow, scrollbar` | 语义变量优先级（从高到低，逗号分隔） |
| `theme_color_mapping.semantic_variable_map` | `scene_bg=--bg-scene, card_bg=--bg-card-solid, text=--text-base|--text-muted, border=--accent-{color}-a15, shadow=--glow-{color}, scrollbar=--accent-{color}-a20\|--accent-{color}-a40` | 语义场景到变量名的映射表（\| 分隔多个可选变量） |
| `theme_color_mapping.edit_tool_preferred` | `true` | 是否优先使用 Edit 精准替换（禁止 Write 重写整个文件） |
| `theme_color_mapping.edit_threshold_ratio` | `0.5` | 修改范围占文件总行数的阈值，低于此值用单次 Edit，高于此值分多次 Edit |
| `theme_color_mapping.backend_typecheck_command` | `npx tsc --noEmit` | 后端类型检查命令 |
| `theme_color_mapping.frontend_typecheck_command` | `npx vue-tsc --noEmit` | 前端类型检查命令（Vue 项目用 vue-tsc） |
| `theme_color_mapping.require_both_pass` | `true` | 是否要求前后端类型检查均通过才允许提交 |

### 适配新项目（主题色变量映射）

- **单主题项目**：将 `enabled` 设为 `false`，所有硬编码颜色均可保留
- **React 项目**：`frontend_typecheck_command` 改为 `npx tsc --noEmit`
- **CSS-in-JS 项目**（styled-components/emotion）：白名单模式不变，但变量引用方式改为 `theme.xxx`
- **不同的 alpha 步进**（如 5% 步进）：修改 `allowed_alpha_values` 列表
- **Material Design 项目**：`semantic_priority` 改为 `surface, background, on_surface, outline, shadow`
- **无光晕效果项目**：从 `semantic_priority` 中移除 `shadow` 项
- **纯 ASCII 项目**：`edit_tool_preferred` 可设为 `false`，允许使用 Write 重写

## Tauri ACL 三层声明参数（tauri_acl）

> CODING-047 Tauri 2.x 自定义命令 ACL 三层声明规则的参数集中在本节。
> 规则文件 [references/tauri-acl-rule.md](../references/tauri-acl-rule.md) 不硬编码任何命令名或文件路径。
> 复盘来源：Tauri 2.x 桌面集成中新增 `invoke` 命令后，运行时报 `Plugin not found` / `not allowed`，根因是 ACL 三层声明缺失。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_acl.enabled` | `true` | 是否启用 ACL 三层守卫 |
| `tauri_acl.severity` | `error` | 违规严重级别 |
| `tauri_acl.build_manifest_file` | `build.rs` | 第 1 层：构建清单文件（AppManifest::commands 声明位置） |
| `tauri_acl.capabilities_file` | `capabilities/default.json` | 第 2 层：权限清单文件（permissions 数组） |
| `tauri_acl.handler_registration_file` | `src/lib.rs` | 第 3 层：处理器注册文件（generate_handler! 宏） |
| `tauri_acl.permission_prefix` | `allow-` | 权限名前缀（与命令名拼接为 allow-cmd-name） |
| `tauri_acl.command_name_case` | `kebab-case` | 命令名命名风格（拼接 permission 时使用） |
| `tauri_acl.diagnostic_map.plugin_not_found_layer` | `1` | 'Plugin not found' 对应缺失层级 |
| `tauri_acl.diagnostic_map.not_allowed_layer` | `2` | 'not allowed' / 'permission denied' 对应缺失层级 |
| `tauri_acl.diagnostic_map.command_not_found_layer` | `3` | 'command X not found' 对应缺失层级 |

- 适配多窗口项目：为每个窗口创建独立 capability 文件，命令权限按窗口分配
- 适配插件化项目：插件权限名前缀为 `plugin:<plugin-name>:`
- 适配 Tauri 1.x 升级：为所有存量 invoke_handler 命令补齐第 1 层与第 2 层声明
- 适配 Tauri Mobile：capabilities 区分 android / iOS 目标

## Tauri 外部 URL 配置参数（tauri_external_url）

> CODING-048 Tauri 2.x 外部 URL 加载 capability 配置规则的参数集中在本节。
> 规则文件 [references/tauri-external-url-rule.md](../references/tauri-external-url-rule.md) 不硬编码端口号或 URL 模式。
> 复盘来源：Tauri 2.x 加载 `http://localhost:3000` 报 `URL: local only`，根因是外部 URL 放在顶层 `urls` 而非 `remote.urls`。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_external_url.enabled` | `true` | 是否启用外部 URL 配置守卫 |
| `tauri_external_url.severity` | `error` | 违规严重级别 |
| `tauri_external_url.capabilities_file` | `capabilities/default.json` | capability 配置文件路径 |
| `tauri_external_url.required_field` | `remote.urls` | 外部 URL 必须放置的字段（点分隔路径） |
| `tauri_external_url.forbidden_field` | `urls` | 禁止放置外部 URL 的字段（顶层 urls） |
| `tauri_external_url.allowed_url_patterns` | `http://localhost:3000/*, http://127.0.0.1:3000/*` | 允许的外部 URL 模式（逗号分隔，支持通配符） |
| `tauri_external_url.dev_port` | `3000` | 开发环境 SPA 服务端口 |
| `tauri_external_url.prod_url` | `tauri://localhost` | 生产环境内置资源 URL |
| `tauri_external_url.url_pattern_glob` | `true` | URL 模式是否支持 glob 通配符 |
| `tauri_external_url.diagnostic_map.url_local_only` | `remote.urls 未配置或格式错误` | 'URL: local only' 错误诊断说明 |

- 适配纯离线 Tauri 应用：`enabled` 设为 `false`，无需配置 `remote.urls`
- 适配远程 SPA 部署：`allowed_url_patterns` 改为 `https://your-app.example.com/*`
- 适配多端口项目：`allowed_url_patterns` 列出所有端口模式
- 适配动态端口：dev 用 `http://localhost:*/*` 通配，prod 固定端口
- 适配 OAuth 集成：`remote.urls` 追加 OAuth 回调 URL 模式

## Tauri 多 Webview 状态隔离参数（tauri_webview_isolation）

> CODING-049 Tauri 多 webview 状态隔离规则的参数集中在本节。
> 规则文件 [references/tauri-webview-isolation-rule.md](../references/tauri-webview-isolation-rule.md) 不硬编码属性名或前缀。
> 复盘来源：主窗口与悬浮窗口同源，`initialization_script` 写 `localStorage` 导致模式标记互相污染。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_webview_isolation.enabled` | `true` | 是否启用 webview 隔离守卫 |
| `tauri_webview_isolation.severity` | `error` | 违规严重级别 |
| `tauri_webview_isolation.forbidden_isolation_methods` | `initialization_script+localStorage, external_url_hash` | 禁止的状态隔离方法（逗号分隔） |
| `tauri_webview_isolation.recommended_isolation_method` | `webview.eval + window property` | 推荐的状态隔离方法 |
| `tauri_webview_isolation.window_property_prefix` | `__TAURI_` | window 属性命名前缀（避免与业务变量冲突） |
| `tauri_webview_isolation.cross_webview_sync_method` | `tauri_event_system` | 跨 webview 状态同步方法（emit/listen） |
| `tauri_webview_isolation.shared_storage_forbidden` | `localStorage, sessionStorage` | 同源 webview 共享的存储（禁止用作隔离） |
| `tauri_webview_isolation.eval_timing` | `on_webview_created` | eval() 注入时机（webview 创建后立即执行） |

- 适配单窗口项目：`enabled` 设为 `false`，无隔离需求
- 适配不同源多窗口：天然 localStorage 隔离，跨源通信用 Tauri 事件系统
- 适配 Electron 项目：规则不适用（BrowserWindow 独立 session）
- 适配多窗口共享大量状态：Rust 后端作权威源，各 webview 通过 invoke 读取

## Tauri 透明窗口 CSS 参数（tauri_transparent_window）

> CODING-050 Tauri 透明窗口 CSS 全覆盖规则的参数集中在本节。
> 规则文件 [references/tauri-transparent-window-rule.md](../references/tauri-transparent-window-rule.md) 不硬编码 CSS 选择器或 class 名。
> 复盘来源：`transparent: true` 启用后仅设置 `body` 透明，`html` 与 `#app` 默认白色背景透出，毛玻璃失效。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_transparent_window.enabled` | `true` | 是否启用透明窗口 CSS 守卫 |
| `tauri_transparent_window.severity` | `error` | 违规严重级别 |
| `tauri_transparent_window.transparent_class` | `floating-active` | 透明模式激活时 html 元素的 class 名 |
| `tauri_transparent_window.required_selectors` | `html, body, #app, *` | 必须覆盖 background 的选择器列表（逗号分隔） |
| `tauri_transparent_window.required_property` | `background-color` | 必须设置的 CSS 属性 |
| `tauri_transparent_window.required_value` | `transparent` | 必须设置的 CSS 值 |
| `tauri_transparent_window.important_required` | `true` | 是否必须用 `!important` 强制覆盖 |
| `tauri_transparent_window.app_container_id` | `app` | SPA 挂载容器 id（Vue/React 的 #app） |
| `tauri_transparent_window.toggle_method` | `eval+classList.toggle` | 切换透明模式的 JS 方法 |
| `tauri_transparent_window.global_selector_prefix` | `:global()` | Svelte/Vue scoped CSS 的全局选择器前缀 |

- 适配不透明窗口项目：`enabled` 设为 `false`，无需透明覆盖
- 适配 React 项目：`app_container_id` 改为 `root`
- 适配 Svelte 项目：`global_selector_prefix` 保持 `:global()`
- 适配原生 CSS 项目：`global_selector_prefix` 设为空字符串
- 适配多透明模式：`transparent_class` 列表扩展（floating-active / acrylic-active / mica-active）
- 适配 Electron 项目：规则不适用，用 vibrancy + backgroundColor

## Tauri 构建脚本参数（tauri_build_script）

> CODING-051 Tauri 构建脚本 SPA 构建步骤规则的参数集中在本节。
> 规则文件 [references/tauri-build-script-rule.md](../references/tauri-build-script-rule.md) 不硬编码脚本名或路径。
> 复盘来源：构建脚本直接 `cargo build` 未构建 SPA，Tauri 加载旧产物；用 `pnpm run build` 触发递归构建死循环。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_build_script.enabled` | `true` | 是否启用构建脚本守卫 |
| `tauri_build_script.severity` | `error` | 违规严重级别 |
| `tauri_build_script.required_scripts` | `tauri-build-debug.ps1, tauri-build-release.ps1` | 必须包含 SPA 构建步骤的脚本列表（逗号分隔） |
| `tauri_build_script.spa_build_command` | `pnpm --filter @karpathy-wiki/web build` | SPA 构建命令（用 --filter 精确构建） |
| `tauri_build_script.forbidden_build_command` | `pnpm run build` | 禁止的构建命令（递归构建风险） |
| `tauri_build_script.spa_output_dir` | `services/api/public/` | SPA 产物输出目录 |
| `tauri_build_script.spa_source_dir` | `packages/web/src/` | SPA 源码目录（用于 mtime 对比） |
| `tauri_build_script.cargo_build_command_debug` | `cargo build` | debug 构建 cargo 命令 |
| `tauri_build_script.cargo_build_command_release` | `cargo build --release` | release 构建 cargo 命令 |
| `tauri_build_script.cleanup_patterns` | `*.html, assets/*.js, assets/*.css` | 旧产物清理 glob（逗号分隔） |
| `tauri_build_script.key_strings_check` | `true` | 是否验证 JS chunk 含关键字符串 |
| `tauri_build_script.key_string_examples` | `FloatingChat, RecentLog, TauriMode` | 关键字符串示例（实际由任务动态确定） |
| `tauri_build_script.mtime_check_enabled` | `true` | 是否启用源码 mtime vs 产物 mtime 对比 |
| `tauri_build_script.expected_binary_path` | `target/debug/karpathy-wiki.exe` | Tauri 构建产物二进制路径 |

- 适配单包 Tauri 项目（前端在根目录）：`spa_build_command` 改为 `pnpm run build:web`（独立脚本）
- 适配 npm 项目：`spa_build_command` 改为 `npm run build --workspace <pkg>`
- 适配 yarn workspace 项目：`spa_build_command` 改为 `yarn workspace <pkg> build`
- 适配 webpack 项目：`spa_output_dir` 改为 webpack output.path
- 适配无前端 Tauri 项目：`enabled` 设为 `false`

## Tauri drag-click 冲突参数（tauri_drag_click_conflict）

> CODING-052 Tauri drag-region 与 click 冲突处理规则的参数集中在本节。
> 规则文件 [references/tauri-drag-click-conflict-rule.md](../references/tauri-drag-click-conflict-rule.md) 不硬编码阈值或选择器。
> 复盘来源：标题栏 `data-tauri-drag-region` 吞掉 click，关闭按钮无响应。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `tauri_drag_click_conflict.enabled` | `true` | 是否启用 drag-click 冲突守卫 |
| `tauri_drag_click_conflict.severity` | `error` | 违规严重级别 |
| `tauri_drag_click_conflict.drag_attribute` | `data-tauri-drag-region` | Tauri 拖动属性名 |
| `tauri_drag_click_conflict.drag_threshold_px` | `5` | 拖动判定位移阈值（像素，系统默认值） |
| `tauri_drag_click_conflict.drag_threshold_ms` | `300` | 拖动判定时间阈值（毫秒） |
| `tauri_drag_click_conflict.rust_command_name` | `start_dragging` | Rust 端拖动命令名（需 ACL 三层声明） |
| `tauri_drag_click_conflict.mouse_down_record_fields` | `clientX, clientY, timestamp` | mousedown 记录的字段（逗号分隔） |
| `tauri_drag_click_conflict.drag_state_var` | `isDragging` | 拖动状态标志变量名 |
| `tauri_drag_click_conflict.required_lifecycle_hooks` | `onMounted, onBeforeUnmount` | 必须配对管理事件监听器的生命周期钩子 |

- 适配 React 项目：`required_lifecycle_hooks` 改为 `useEffect mount, useEffect cleanup`
- 适配 Svelte 项目：用 `onMount` / `onDestroy` 替代 Vue 钩子
- 适配原生 JS 项目：DOM Ready 时 addEventListener，unload 时 remove
- 适配触屏设备：追加 touchstart/touchmove/touchend，阈值放大到 10px
- 适配不同阈值偏好：精确操作场景用 3px，粗放场景用 8px
- 适配 Electron 项目：规则不适用，用 `-webkit-app-region: drag/no-drag`

## PowerShell stderr 处理参数（powershell_stderr）

> CODING-053 PowerShell 调用 cargo 的 stderr 处理规则的参数集中在本节。
> 规则文件 [references/powershell-stderr-rule.md](../references/powershell-stderr-rule.md) 不硬编码工具名或参数。
> 复盘来源：`$ErrorActionPreference=Stop` 把 cargo 编译进度 stderr 误判为错误，脚本中断。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `powershell_stderr.enabled` | `true` | 是否启用 stderr 处理守卫 |
| `powershell_stderr.severity` | `error` | 违规严重级别 |
| `powershell_stderr.recommended_invocation` | `Start-Process -NoNewWindow -Wait -PassThru` | 推荐的工具调用方式 |
| `powershell_stderr.forbidden_invocation` | `直接调用 + $ErrorActionPreference=Stop` | 禁止的工具调用方式 |
| `powershell_stderr.success_exit_code` | `0` | 成功退出码 |
| `powershell_stderr.stderr_progress_tools` | `cargo, rustc, go, gcc, cl` | 输出 stderr 进度的工具列表（逗号分隔） |
| `powershell_stderr.error_action_preference_for_tools` | `Continue` | 调用工具时 $ErrorActionPreference 的推荐值 |
| `powershell_stderr.exit_code_var` | `ExitCode` | 进程退出码属性名 |
| `powershell_stderr.require_explicit_exit_check` | `true` | 是否必须显式检查退出码 |

- 适配 Bash 项目：规则不适用，Bash 默认不把 stderr 当错误
- 适配 Python 脚本：用 `subprocess.run(capture_output=True)` + `returncode` 判断
- 适配 Node.js 脚本：用 `child_process.spawn` + `exit` 事件判断
- 适配不同工具链：`stderr_progress_tools` 追加新工具（如 cmake / make / ninja）
- 适配需要捕获输出的场景：`Start-Process -RedirectStandardOutput` + `-RedirectStandardError` 分别重定向
- 适配 CI 环境：显式设置 $ErrorActionPreference，避免依赖环境默认值

## 认证端点分类守卫参数（auth_endpoint_classification）

> 认证端点分类规则（见 [references/auth-endpoint-classification-rule.md](../references/auth-endpoint-classification-rule.md)）所依赖的参数集中在本节。
> 规则文件不硬编码端点路径或中间件名称，所有参数从本节读取，便于适配不同框架。
> 复盘来源：携带有效 token 调用 `/api/auth/me` 返回 401，根因是 `/api/auth/me` 误入 publicPaths 白名单导致全局 preHandler 跳过 token 解析。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `auth_endpoint_classification.enabled` | `true` | 是否启用认证端点分类守卫 |
| `auth_endpoint_classification.severity` | `error` | 违规严重级别（error = 必须修复） |
| `auth_endpoint_classification.public_paths_whitelist` | `/api/auth/login,/health` | 完全公开端点列表（逗号分隔，仅放无需鉴权的端点） |
| `auth_endpoint_classification.auth_required_pattern` | `/api/auth/me,/api/auth/logout` | 需鉴权端点示例列表（用于识别"看似公开实则需鉴权"的端点） |
| `auth_endpoint_classification.middleware_hook` | `preHandler` | 认证中间件 hook 名称（Fastify 用 preHandler，Express 用 use） |
| `auth_endpoint_classification.skip_mechanism` | `isPublicPath` | 跳过 token 解析的机制名称（白名单匹配函数名） |

- 适配 Express：`middleware_hook` 改为 `use`，`skip_mechanism` 改为 `path match`。
- 适配无认证应用：`enabled` 设为 `false`。

## Windows 文件操作守卫参数（windows_file_operation）

> Windows 文件操作规则（见 [references/windows-file-operation-rule.md](../references/windows-file-operation-rule.md)）所依赖的参数集中在本节。
> 规则文件不硬编码命令或平台，所有参数从本节读取，便于跨平台适配。
> 复盘来源：API 服务进程调用 `fs.rm` 删除目录，调用完成不抛异常但目录仍存在，根因是 Windows 文件句柄占用导致 fs.rm 静默失败。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `windows_file_operation.enabled` | `true` | 是否启用 Windows 文件操作守卫 |
| `windows_file_operation.severity` | `error` | 违规严重级别 |
| `windows_file_operation.platform` | `win32` | 触发原生命令的平台（process.platform 值） |
| `windows_file_operation.delete_command` | `rd /s /q` | Windows 原生删除命令 |
| `windows_file_operation.delete_command_flags` | `/s /q` | 递归 + 静默标志（/s 递归，/q 静默不确认） |
| `windows_file_operation.fallback_method` | `fs.rmSync` | 原生命令失败时的回退方法 |
| `windows_file_operation.verify_after_delete` | `true` | 删除后必须 existsSync 验证 |
| `windows_file_operation.retry_count` | `1` | fallback 重试次数 |
| `windows_file_operation.retry_delay_ms` | `100` | 重试间隔（毫秒） |

- 适配 Linux/macOS：`platform` 改为 `linux`/`darwin`，`delete_command` 改为 `rm -rf`。
- 适配容器环境：`enabled` 设为 `false`（容器内 fs.rm 通常可靠）。
