# Coding Standards Config

> 项目参数（路径锚点、缓存 TTL、白名单正则、降级策略）。所有参数在此管理，规则文件仅描述模式。

## 路径锚点

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `project_root` | `karpathy-wiki` | 项目根目录相对路径 |
| `backend_dir` | `services/api` | 后端目录 |
| `frontend_dir` | `packages/web` | 前端目录 |
| `config_dir` | `config` | 配置目录 |
| `docs_base_dir` | `docs` | 文档目录 |
| `skills_dir` | `.trae/skills` | 技能目录 |
| `runtime_data_dir` | `data/vault` | 运行时数据目录 |
| `build_output_dirs` | `dist`, `gen` | 构建输出目录 |
| `external_toolchain_dirs` | `w64devkit` | 外部工具链目录 |
| `scripts_dir` | `scripts` | 脚本目录 |

## 缓存 TTL

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_cache_ttl_ms` | `30000` | 配置缓存 TTL（30 秒） |
| `check_update.cache_ttl_ms` | `300000` | 检查更新缓存 TTL（5 分钟） |
| `poll_interval_ms` | `300000` | 轮询间隔（≥ cache_ttl_ms） |
| `offline_mode` | `true` | 离线模式固定返回 has_update: false |

## 白名单正则

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `filename_whitelist` | `[a-zA-Z0-9_\-\.]+$` | 文件名白名单 |
| `path_whitelist` | `^[a-zA-Z0-9_\-/\.]+$` | 路径白名单 |
| `conversation_id_pattern` | `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` | UUID 验证正则 |
| `sensitive_field_patterns` | `["apiKey", "password", "token", "secret", "auth"]` | 敏感字段名 |
| `encoding_scan_pattern` | `["*.ts", "*.vue", "*.json", "*.md", ".gitignore", ".editorconfig"]` | 编码扫描文件扩展名 |
| `encoding_scan_command` | `node scripts/check-encoding.js` | 编码扫描命令 |

## 降级策略

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `fallback.log_to_stdout_only` | `true` | 文件流失败时降级到 stdout |
| `fallback.api_key_ref` | `process.env.LLM_API_KEY` | API Key 环境变量引用 |
| `fallback.base_url` | `http://localhost:3000` | 默认 API 基地址 |
| `fallback.frontend_url` | `http://localhost:5173` | 默认前端地址 |
| `fallback.model` | `doubao` | 默认模型 |
| `fallback.tts.provider` | `browser` | 默认 TTS 提供商 |
| `fallback.sidebar_state` | `expanded` | 默认侧栏状态 |
| `fallback.nav_theme` | `light` | 默认导航栏主题 |

## 编码守卫

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `encoding_guard.write_with_utf8` | `true` | Write 含中文文件时是否强制 UTF-8 |
| `encoding_guard.encoding_fallback` | `encoding_fallback` | 非 UTF-8 文件读写模式 |
| `encoding_guard.verify_after_write` | `true` | 写文件后是否验证编码 |
| `encoding_guard.replacement_char_threshold` | `0` | U+FFFD 替换字符容忍阈值 |

## PowerShell 约束

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `powershell.blocked_commands` | `["&&", "cmd /c", "cd", "$pid"]` | 禁止的命令/语法 |
| `powershell.command_separator` | `;` | 命令分隔符（替代 &&） |
| `powershell.redirect_output_to_file` | `> file.txt 2>&1` | 长时进程输出重定向模板 |
| `powershell.bypass_bat_pause` | `true` | bat 脚本是否自动绕过 pause |
| `powershell.residual_match_pattern` | `pnpm run dev` | 残留进程命令行匹配模式 |
| `powershell.stop_old_process` | `true` | 启动服务前是否停止旧进程 |

## Vue 类型检查

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `vue_tsc_cache_dirs` | `["node_modules/.tmp", "tsconfig.tsbuildinfo", "node_modules/.vite"]` | vue-tsc 增量缓存目录 |
| `vue_tsc_stale_artifact_patterns` | `["src/**/*.js"]` | 需清理的陈旧 .js 产物 |
| `vue_tsc_force_cache_clear` | `true` | 幽灵错误时是否强制清除缓存 |

## Git/编码守卫

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `git.verify_command` | `git check-ignore -v` | 验证 .gitignore 规则 |
| `git.untrack_command` | `git rm --cached` | 从索引移除已跟踪文件 |
| `git.ls_files_command` | `git ls-files` | 检查跟踪状态 |

## 滚动容器

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `scroll_container.max_overflow_layers` | `1` | 溢出层数上限 |
| `scroll_container.flex_shrink_guard` | `true` | flex 自然高度子项是否加 flex-shrink: 0 |

## SPA 导航

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `spa_navigation.event_name_pattern` | `{project}:navigate` | CustomEvent 派发命名模式 |
| `spa_navigation.project_name` | `karpathy` | 项目名（ karpathy:navigate） |
| `spa_navigation.allowed_views` | `["dashboard", "ingest", "progress", "browse", "query", "graph", "health", "config", "tunnel", "cleanup", "users", "skill", "dataclean", "help", "about"]` | 允许的视图白名单 |
| `spa_navigation.require_lifecycle_pair` | `true` | 是否要求 onMounted/onBeforeUnmount 配对 |

## DOM 变更兼容

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dom_compat_class.enabled` | `true` | 启用守卫 |
| `dom_compat_class.severity` | `error` | 严重级别 |
| `dom_compat_class.verify_methods` | `["grep", "glob"]` | class 引用交叉验证方法 |
| `dom_compat_class.test_file_patterns` | `["**/test_*.py", "**/*.spec.ts", "**/*.test.ts"]` | 测试文件 glob |
| `dom_compat_class.stale_class_threshold` | `0` | 失效 class 引用容忍阈值 |
| `dom_compat_class.require_same_commit` | `true` | class 重命名与测试更新是否要求同 commit |
| `dom_compat_class.preserve_original_class_first` | `true` | DOM 变更时是否优先保留原 class 名 |

## Flex 容器高度自适应

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `flex_viewport_adapt.enabled` | `true` | 启用守卫 |
| `flex_viewport_adapt.severity` | `error` | 严重级别 |
| `flex_viewport_adapt.forbidden_height_pattern` | `calc\(100vh` | 禁止的高度计算正则模式 |
| `flex_viewport_adapt.required_parent_props` | `["display: flex", "height: 100%"]` | 父容器必须建立的 CSS 属性 |
| `flex_viewport_adapt.required_child_props` | `["flex: 1", "min-height: 0"]` | 子项必须的 CSS 属性 |
| `flex_viewport_adapt.audit_on_layout_change` | `true` | 布局变更时是否自动审计 calc 引用 |
| `flex_viewport_adapt.view_file_patterns` | `["**/views/*.vue"]` | 需审计的视图文件 glob |

## 状态机简化

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `state_machine_simplify.enabled` | `true` | 启用守卫 |
| `state_machine_simplify.severity` | `suggestion` | 严重级别 |
| `state_machine_simplify.max_state_count` | `2` | 简化后的最大状态数 |
| `state_machine_simplify.forbidden_switch_syntax` | `nested-ternary` | 禁止的状态切换语法 |
| `state_machine_simplify.require_cleanup` | `true` | 简化后是否必须删除废弃状态引用 |
| `state_machine_simplify.require_comment_update` | `true` | 简化后是否必须更新注释 |
| `state_machine_simplify.stale_state_threshold` | `0` | 废弃状态引用容忍阈值 |

## PowerShell 长时进程

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `powershell_long_process.enabled` | `true` | 启用守卫 |
| `powershell_long_process.severity` | `warning` | 严重级别 |
| `powershell_long_process.long_process_threshold_ms` | `30000` | 长时进程阈值（超过则禁管道） |
| `powershell_long_process.vue_tsc_timeout_ms` | `120000` | vue-tsc 超时阈值（超过则清缓存） |
| `powershell_long_process.forbidden_pipe_commands` | `["Select-String", "Out-String", "Where-Object"]` | 禁止对长时进程使用的管道命令 |
| `powershell_long_process.redirect_method` | `> file 2>&1` | 推荐的输出捕获方式 |
| `powershell_long_process.epipe_exit_code` | `-1` | EPIPE 管道断裂退出码 |
| `powershell_long_process.cache_cleanup_targets` | `["node_modules/.tmp", "tsconfig.tsbuildinfo", "node_modules/.vite", "src/**/*.js"]` | 增量缓存清理目标 |

## 回滚最小化

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `rollback_minimal.enabled` | `true` | 启用守卫 |
| `rollback_minimal.severity` | `error` | 严重级别 |
| `rollback_minimal.recovery_order` | `["import", "emit", "template", "style", "parent-binding"]` | 恢复顺序 |
| `rollback_minimal.required_tool` | `Edit` | 必须使用的编辑工具（禁止 Write 重写整个文件） |
| `rollback_minimal.require_typecheck` | `true` | 回滚后是否必须类型检查 |
| `rollback_minimal.require_e2e_test` | `true` | 回滚后是否必须 E2E 测试 |
| `rollback_minimal.require_partial_annotation` | `true` | 部分回滚时是否必须注释标注 |