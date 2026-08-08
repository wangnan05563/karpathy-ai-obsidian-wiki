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

## Vite 解析顺序

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `vite.resolve_extensions` | `[".mjs",".ts",".tsx",".js",".jsx",".vue",".json"]` | 模块解析扩展名顺序，`.ts` 必须排在 `.js` 之前 |

## 文本处理

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `text.cjk_token_ratio` | `1` | 每个 CJK 字符约计 token 数 |
| `text.latin_chars_per_token` | `4` | 每 token 约含 Latin 字符数 |

## 压缩与淘汰

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `compression.ratio` | `0.3` | 压缩后保留长度占原文的最大比例 |
| `compression.min_floor_chars` | `40` | 压缩保留长度的最小地板（保证短内容不被压没） |
| `eviction.coherence_floor_k` | `4` | 淘汰时必须保留的近期消息最小条数 |

## 限流

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `rate_limit.window` | `"sliding"` | 限流窗口类型（滑动/有界 + sweep） |
| `rate_limit.restore_real_ip_header` | `"X-Forwarded-For"` | 还原真实客户端 IP 的请求头 |
| `rate_limit.trust_proxy` | `false` | 是否信任代理（保持 false 防头伪造） |

## 测试

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `testing.flake_isolation` | `"run failing file alone before blaming new code"` | flaky 隔离策略：先单独跑失败文件再归咎新代码 |

## 打包与用户数据（SEA / 安装器）

> 对应 references/packaging-userdata-rule.md（CODING-PACKAGING-USERDATA）。所有参数集中管理，规则文件仅描述模式。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `packaging.app_name` | `KarpathyWiki` | 用户数据目录名（贴在 LOCALAPPDATA 等之下） |
| `packaging.user_data_dir_anchor` | `LOCALAPPDATA` | 用户数据根首选锚点（Windows） |
| `packaging.user_data_dir_fallback` | `APPDATA, HOME` | 回退锚点顺序（非常规环境兼容） |
| `packaging.user_data_dir_pattern` | `{anchor}/{app_name}` | 用户数据目录解析模板 |
| `packaging.installer_program_files_flags` | `ignoreversion` | 程序文件安装 Flags（升级即覆盖） |
| `packaging.installer_exclude_user_data` | `true` | 用户数据（config.json/.env/vault/data）禁止打包到 {app} |
| `packaging.sea_detection` | `IS_SEA` | 打包模式检测标志（基于 __filename + existsSync + process.execPath） |
| `packaging.resource_path_func` | `getApiDir, getResourcePath, getPromptsDir` | 资源路径派生函数（随版本更新，随 exe 走） |
| `packaging.user_data_path_func` | `getUserDataDir, getDataDir, getUserDataPath` | 用户数据路径派生函数（跨版本持久，随用户走） |
| `packaging.rebase_relative_only` | `true` | 仅相对路径字段被归一化到用户数据目录，尊重用户显式绝对路径 |
| `packaging.clean_default_fields` | `vaultPath, auth.usersFilePath, auth.auditLogPath, urlCrawl.*, logging.logFilePath` | 首次落盘须回退为相对默认值的字段清单 |

## 第三方 UI 库 API 时效性

> 对应 references/third-party-ui-api-currency-rule.md（CODING-UI-API-1/2）。组件库已弃用属性须迁移、主版本升级前全量扫描。所有参数集中管理，规则文件仅描述模式。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ui_library_api.scan_components` | `el-radio,el-radio-button,el-radio-group` | 受影响组件（按实际使用的 UI 库调整） |
| `ui_library_api.deprecated_attrs` | `label` | 禁止用作选项值的弃用属性 |
| `ui_library_api.replacement_attrs` | `value` | 替代属性（选项值） |
| `ui_library_api.display_text_strategy` | `slot` | 显示文本改用默认插槽 |
| `ui_library_api.deprecation_since_version` | `2.6.0` | 该用法被标记弃用的库版本 |
| `ui_library_api.removal_version` | `3.0.0` | 该用法被移除的库主版本 |

## SPA 实时部署

> 对应 references/spa-live-deploy-rule.md（CODING-SPA-LIVE-DEPLOY-1~4）。扩展 spa-static-hosting-rule.md（SH-1~SH-5）：当部署采用"每次构建写入全新 `public_live_<ts>` 目录、后端动态选最新"模式时，须按数值时间戳选最新且完整目录、静态资源解析须 within-root 防穿越、部署须写全新目录不覆盖已存在目录。所有参数集中管理，规则文件仅描述模式。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `spa_live_deploy.enabled` | `true` | 是否启用实时部署解析审查（后端按时间戳选最新部署目录的场景） |
| `spa_live_deploy.public_base_dir` | `api` | 部署目录基准父目录（相对 process.cwd()） |
| `spa_live_deploy.live_dir_pattern` | `public_live_` | 时间戳部署目录前缀（后接数值时间戳） |
| `spa_live_deploy.legacy_dir` | `public` | 兜底固定目录（新目录完整性校验失败时回退） |
| `spa_live_deploy.quarantine_keyword` | `quarantine` | 排除关键字（隔离/回收目录不参与候选） |
| `spa_live_deploy.index_file` | `index.html` | 完整性门禁：index 文件名 |
| `spa_live_deploy.complete_marker` | `.deploy-complete` | 完整性门禁：部署完成标记文件名（最后写，保证原子可见） |
| `spa_live_deploy.sort_order` | `desc` | 候选排序方向（数值时间戳降序，最新在前） |
| `spa_live_deploy.asset_prefix` | `/wiki/` | 静态资源前缀（需 within-root 防穿越的请求路径前缀） |
| `spa_live_deploy.require_within_root` | `true` | 资源解析须 normalize + path.relative(root) 逃逸拦截（逃逸即拒绝） |
| `spa_live_deploy.require_restart` | `true` | spaRoot 启动时计算一次，部署新目录后必须重启后端才生效 |

## 会话跨账户隔离

> 对应 references/frontend-session-isolation-rule.md（CODING-SESSION-ISOLATION-1~3）。客户端按用户隔离的会话/草稿/个人配置（IndexedDB 按 ownerId），但 Pinia 模块级共享会话 state ref 在账户切换/登出时若未重置，下一账户复用同一 id 持久化会覆盖并改属他人记录（表现为「历史消失/人人可见」）。规则文件仅描述模式，所有参数集中管理。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `session_isolation.enabled` | `true` | 是否启用会话跨账户隔离审查（前端 Pinia 会话状态 + 客户端按 ownerId 持久化场景） |
| `session_isolation.reset_on_auth_signal` | `user?.id` | auth watch 信号，变化时必须先 resetSession 再 loadConversations |
| `session_isolation.state_refs_must_return` | `currentConversationId,scopedOwnerId` | Pinia setup store 中必须加入 return 对象的会话状态 ref（漏加则赋值不可观测=死状态） |
| `session_isolation.owner_check_source` | `dbGet (IndexedDB actual record)` | 复用 id 前校验归属所依据的实际存储记录 |
| `session_isolation.use_fresh_uuid_when_conflict` | `true` | 已存在且归属他人时改用全新 uuid，绝不覆盖/改属他人记录 |
| `session_isolation.attach_after_flush` | `true` | 归属迁移须「落盘成功后才内存归属」（安全失败不泄漏） |

## BYOK 多用户密钥代理
| `byok_per_user_override.enabled` | `true` | 是否启用 BYOK 多用户密钥代理审查（前端本地命名空间 + 密钥仅经请求体下发 + 覆盖纯函数） |
| `byok_per_user_override.byok_user_config_namespaces` | `usercfg::ai::,usercfg::search::,usercfg::tools::` | 前端按用户命名空间键前缀（键内化 userId，天然隔离） |
| `byok_per_user_override.secret_not_persisted` | `true` | 密钥仅经请求体下发，后端不落盘 / 不回显 GET / 不记日志 |
| `byok_per_user_override.require_key_no_fallback` | `true` | 缺 apiKey（及 provider / baseUrl / model）直接 400，不回落服务端共享 |
| `byok_per_user_override.override_must_be_pure` | `true` | 覆盖逻辑须纯函数（无副作用、不污染服务端共享 config） |
| `byok_per_user_override.empty_override_falls_back` | `true` | 空 / 默认工具配置视为未提供覆盖，回退服务端共享配置（不清空） |

## 流式回答增量持久化与续答
| `streaming_resume.enabled` | `true` | 是否启用流式回答增量持久化与续答审查（前端流式 UI） |
| `streaming_resume.persist_debounce_ms` | `1500` | 流式分片增量落盘防抖毫秒 |
| `streaming_resume.no_abort_on_unmount` | `true` | 页面卸载 / 切页不得 abort 在途流（仅卸监听） |
| `streaming_resume.last_active_key` | `LAST_ACTIVE_CONVERSATION` | 上次活跃会话存储键（重载恢复用） |
| `streaming_resume.resume_only_streaming` | `true` | 仅末条 status='streaming' 续答，interrupted / error 不自动续 |
| `streaming_resume.skip_when_loading` | `true` | SPA 重挂载且后台流活跃(isLoading)时跳过续答 |

## SSML / Prosody 注入防护（CODING-SSML-INJECTION）

> 对应 references/ssml-injection-rule.md。任何外部输入拼进 TTS/SSML 前须校验 prosody 格式 + 转义 + 禁用不支持标签。所有参数集中管理，规则文件仅描述模式。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `ssml_injection.enabled` | `true` | 启用 SSML 注入防护审查 |
| `ssml_injection.rate_regex` | `^(default|\d{1,3}%|x-?\d(\.\d)?|\+\d(\.\d)?|-?\d(\.\d)?)$` | 语速白名单正则 |
| `ssml_injection.volume_regex` | `^(default|\d{1,3}%|x-?\d(\.\d)?|\+\d(\.\d)?|-?\d(\.\d)?)$` | 音量白名单正则 |
| `ssml_injection.pitch_regex` | `^(default|\d{1,3}Hz|x-?\d(\.\d)?|\+\d(\.\d)?|-?\d(\.\d)?)$` | 语调白名单正则 |
| `ssml_injection.default_value` | `default` | 校验失败回退值 |
| `ssml_injection.escape_chars` | `<>&` | 须转义的特殊字符 |
| `ssml_injection.forbidden_tags_regex` | `<mstts:express-as` | 免费端点不支持的标签（命中即拒绝/剥离） |
| `ssml_injection.unsupported_endpoint_code` | `1007` | 免费端点拒绝 SSML 的 WebSocket 关闭码 |

## 子进程异步/同步正确性（CODING-CHILD-PROCESS-SYNC）

> 对应 references/child-process-sync-rule.md。子进程调用须按"同步结果/异步事件"二选一 API，禁止异步当同步。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `child_process_sync.enabled` | `true` | 启用子进程同步正确性审查 |
| `child_process_sync.sync_calls` | `ffmpeg` | 须同步拿结果的子进程命令清单 |
| `child_process_sync.timeout_ms` | `30000` | 子进程同步调用超时（毫秒，从配置读取禁硬编码） |
| `child_process_sync.require_await_pattern` | `await | execFileSync` | 结果被使用前的必要同步标志 |
| `child_process_sync.severity_fake_sync` | `critical` | 异步 API 当同步用违规级别 |

## 关键写不得静默吞错（CODING-CRITICAL-WRITE-NO-SWALLOW）

> 对应 references/critical-write-no-swallow-rule.md。关键写失败必须传播。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `critical_write_no_swallow.enabled` | `true` | 启用关键写错误传播审查 |
| `critical_write_no_swallow.critical_functions` | `saveUsers,saveConfig,persistConversation` | 关键写函数清单 |
| `critical_write_no_swallow.severity` | `critical` | 关键写静默吞错违规级别 |
| `critical_write_no_swallow.silent_catch_pattern` | `catch\s*\([^)]*\)\s*\{\s*\}` | 空 catch（无 throw/log）匹配模式 |

## 关键数据文件损坏防护（CODING-FILE-CORRUPTION-GUARD）

> 对应 references/file-corruption-guard-rule.md。读取关键 JSON 须区分 not-found 与 corrupt。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `file_corruption_guard.enabled` | `true` | 启用文件损坏防护审查 |
| `file_corruption_guard.critical_files` | `users.json,config.json` | 关键 JSON 文件清单 |
| `file_corruption_guard.backup_on_corruption` | `true` | 损坏时备份为 `.corrupt-<ts>.bak` |
| `file_corruption_guard.backup_suffix` | `.corrupt` | 坏文件备份名标记 |
| `file_corruption_guard.severity` | `critical` | 损坏当 not-found 静默清零违规级别 |

## 类型安全禁止 `as any` 绕过（CODING-TYPE-SAFE-NO-ANY）

> 对应 references/type-safe-no-any-rule.md。禁止 `as any` 绕过类型检查。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `type_safe_no_any.enabled` | `true` | 启用类型安全绕过审查 |
| `type_safe_no_any.forbidden_patterns` | `as any, as unknown as, as any as` | 禁止的绕过写法 |
| `type_safe_no_any.allowed_in` | `@migration` | 允许放行的标注 |
| `type_safe_no_any.proper_type_ref` | `InjectOptions['method']` | 推荐的类型提取示例 |
| `type_safe_no_any.severity` | `critical` | 常驻业务路径 `as any` 绕过违规级别 |

## 超时/阈值可配置化（CODING-CONFIG-TIMEOUT）

> 对应 references/config-timeout-rule.md。超时须从配置读取，禁硬编码。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `config_timeout.enabled` | `true` | 启用超时可配置化审查 |
| `config_timeout.timeout_keys` | `edgeTtsTimeoutMs` | 须配置化的超时键清单 |
| `config_timeout.default_ms` | `30000` | 超时默认毫秒 |
| `config_timeout.forbidden_literal_ms` | `30000,30_000,60000` | 禁止直接在代码出现硬编码毫秒字面量 |
| `config_timeout.margin_multiplier` | `1.5` | 多层超时递增倍数（与 BR-053 对齐） |

## 去除冗余探测/探针（CODING-NO-REDUNDANT-PROBE）

> 对应 references/no-redundant-probe-rule.md。用能力检测替代冗余探针。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `no_redundant_probe.enabled` | `true` | 启用冗余探测审查 |
| `no_redundant_probe.capability_check` | `ffmpeg -version` | 工具可用性能力检测命令 |
| `no_redundant_probe.redundant_probe_regex` | `ffprobe` | 冗余探针命令（命中即告警） |
| `no_redundant_probe.forbidden_commands` | `ffprobe` | 禁止用于可用性探测的命令清单 |
| `no_redundant_probe.severity` | `suggestion` | 冗余探测违规级别 |

## 归档落盘文件名唯一性（CODING-GENERATED-FILENAME-UNIQUENESS）

> 对应 references/generated-filename-uniqueness-rule.md（GFU-1~4 → BR-081）。落盘文件名若由分组键（日期+shortId）派生，非全局唯一，须追加随机后缀后再落盘，冲突即拒绝/重生成。所有参数集中管理，规则文件仅描述模式。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `generated_filename.enabled` | `true` | 启用落盘文件名唯一性审查 |
| `generated_filename.derived_group_key` | `date+shortId` | 派生分组键组成（非全局唯一，仅作分组） |
| `generated_filename.collision_suffix_len` | `4` | 追加随机后缀长度（hex 字符数） |
| `generated_filename.collision_suffix_charset` | `hex` | 随机后缀字符集（hex/base36/uuid） |
| `generated_filename.reject_on_collision` | `true` | 仍发生哈希碰撞即拒绝/重生成，禁止覆盖 |
| `generated_filename.severity` | `critical` | 派生键直接落盘覆盖他人数据违规级别 |

## 服务端解析客户端日期串安全（CODING-SAFE-CLIENT-DATE-PARSE）

> 对应 references/safe-client-date-parse-rule.md（SCD-1~4 → BR-082）。禁止 `new Date(str).toISOString()` 对非法串抛 RangeError；统一安全解析覆盖 null/未定义/非字符串/无效日期，回退默认。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `safe_date_parse.enabled` | `true` | 启用客户端日期串安全解析审查 |
| `safe_date_parse.forbidden_pattern` | `new Date(str).toISOString()` | 命中即告警的非法写法 |
| `safe_date_parse.default_value` | `null` | 解析失败回退值（或 ISO 当前时间，按业务定） |
| `safe_date_parse.accept_undefined` | `true` | 未定义字段允许回退默认而非抛错 |
| `safe_date_parse.coerce_nonstring` | `true` | 非字符串先规范化再校验，不直接 toISOString |
| `safe_date_parse.severity` | `critical` | 非法日期串导致 500 的违规级别 |

## 客户端整数序号校验（CODING-INTEGER-INDEX-VALIDATION）

> 对应 references/integer-index-validation-rule.md（IIV-1~4 → BR-083）。客户端传下标访问数组前须 `Number.isInteger` 校验，非法/缺失即拒绝，校验在数组访问前短路。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `integer_index.enabled` | `true` | 启用整数序号校验审查 |
| `integer_index.reject_status` | `400` | 非法/非整数的拒绝状态码 |
| `integer_index.validate_before_access` | `true` | 校验须在数组访问前短路 |
| `integer_index.severity` | `critical` | 非整数当下标导致 undefined 访问 500 的违规级别 |

## Wikilink 注入清洗（CODING-WIKILINK-SANITIZATION）

> 对应 references/wikilink-sanitization-rule.md（WLS-1~4 → BR-084）。注入 `[[wikilink]]` 前须去换行+trim+去空，并按配置正则额外清洗破坏字符。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `wikilink.enabled` | `true` | 启用 wikilink 注入清洗审查 |
| `wikilink.sanitize_regex` | `[\r\n]` | 须清除的换行字符集 |
| `wikilink.replace_with` | ` ` | 换行替换字符（空格） |
| `wikilink.trim` | `true` | 注入前 trim |
| `wikilink.filter_empty` | `true` | 去空串（`filter(Boolean)`） |
| `wikilink.extra_clean_regex` | `[\]\|]` | 额外清洗的破坏性字符（`]`/`\|`） |
| `wikilink.severity` | `suggestion` | 脏链接/跨行断裂违规级别 |

## 创建型写入空内容拒绝（CODING-EMPTY-CONTENT-REJECTION）

> 对应 references/empty-content-rejection-rule.md（ECR-1~4 → BR-085）。必填字段同时缺失或空串即拒绝，写入前短路，禁止空内容 no-op 落盘。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `empty_content.enabled` | `true` | 启用空内容拒绝审查 |
| `empty_content.reject_status` | `400` | 空内容拒绝状态码 |
| `empty_content.required_fields` | `question,answer` | 必填字段清单（从配置读取，缺失即拒） |
| `empty_content.treat_whitespace_as_empty` | `true` | 纯空白视为空串 |
| `empty_content.severity` | `critical` | 空内容落盘污染知识的违规级别 |

## 归档内容取源解耦（CODING-PERSISTENCE-CLIENT-CONTENT-DECOUPLING）

> 对应 references/persistence-client-content-decoupling-rule.md（PCC-1~4 → BR-086 / FR-076）。归档优先请求体取内容，仅缺失回退会话；默认 `threadsPersist=false` 须解耦，不擅自开 persist。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `persistence_client_content.enabled` | `true` | 启用内容取源解耦审查 |
| `persistence_client_content.prefer_request_body` | `true` | 内容优先从请求体取 |
| `persistence_client_content.fallback_to_session` | `false` | 仅请求体缺失才回退会话（默认关） |
| `persistence_client_content.default_threads_persist` | `false` | 默认会话持久化开关 |
| `persistence_client_content.forbid_auto_persist` | `true` | 不得擅自开启 persist 以绕过解耦 |
| `persistence_client_content.severity` | `critical` | 依赖服务端会话导致误报过期的违规级别 |

## 能力门控同步（CODING-CAPABILITY-GATING-SYNC）

> 对应 references/capability-gating-sync-rule.md（CGS-1~4 → FR-076）。前端功能门控（`:can-archive` 等）须随后端契约放宽同步，依据"内容可得性"，同变更完成避免漂移。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `capability_gating_sync.enabled` | `true` | 启用能力门控同步审查 |
| `capability_gating_sync.sync_with_backend_contract` | `true` | 前端门控须与后端契约同步放宽 |
| `capability_gating_sync.relax_signal` | `content availability` | 放宽依据（内容可得性而非 sessionId 存在） |
| `capability_gating_sync.complete_in_same_change` | `true` | 前后端放宽须同一变更完成 |

## 编辑重发重新插入用户消息（CODING-EDIT-RESEND）

> 对应 references/edit-resend-rule.md（R-1~R-3 → FR-077）。编辑已发送消息并重发：`removeMessagesFrom(i)` 丢弃尾部后必须 `submitQuestion` 重新插入 user 消息，否则对话只剩悬空 AI 答案；须先终止在途流式回复；文本未变仅退出编辑态不重发。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `edit_resend.enabled` | `true` | 启用编辑重发审查 |
| `edit_resend.reinsert_required` | `true` | `removeMessagesFrom` 后必须 `submitQuestion` 重新插入 user 消息 |
| `edit_resend.stop_inflight_first` | `true` | 编辑重发前须先终止在途流式回复、释放 loading，再丢弃尾部 |
| `edit_resend.idempotent_noop` | `true` | 编辑后文本未变化仅退出编辑态、不重发 |
| `edit_resend.severity` | `critical` | 丢弃尾部未重插导致悬空答案的违规级别 |

## 流式聊天自动贴底滚动（CODING-STREAMING-AUTOSCROLL）

> 对应 references/streaming-autoscroll-rule.md（R-1~R-5 → FR-078）。流式输出自动贴底：nextTick + 双 rAF 捕获布局变化；用户上滑超阈值暂停贴底；capture 阶段监听 img load 补滚；容器挂载/卸载自动绑定/解绑监听。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `chat_autoscroll.enabled` | `true` | 启用流式自动贴底滚动审查 |
| `chat_autoscroll.double_raf` | `true` | 贴底定位须 nextTick + 双 requestAnimationFrame |
| `chat_autoscroll.near_bottom_px` | `80` | 判定用户是否贴底的阈值（px） |
| `chat_autoscroll.img_load_reflow` | `true` | 须 capture 阶段监听 img load 异步撑高后补滚 |
| `chat_autoscroll.bind_unbind` | `true` | 容器 scroll/load 监听须挂载绑定、卸载解绑 |
| `chat_autoscroll.force_semantics` | `true` | force 仅用于新消息到达，其余仅跟随用户贴底 |
| `chat_autoscroll.severity` | `major` | 自动贴底失效（落后于高度/打断回看）的违规级别 |

## 成对按钮样式一致性（CODING-BUTTON-STYLE-CONSISTENCY）

> 对应 references/button-style-consistency-rule.md（R-1~R-3 → FR-079）。同一操作组确认/取消按钮须共享一致基础样式，差异仅经 hover 强调；配色用主题变量；`type="primary"` 仅留给唯一主操作。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `button_style.enabled` | `true` | 启用成对按钮样式一致性审查 |
| `button_style.shared_base` | `true` | 同组确认/取消按钮共享一致基础样式 |
| `button_style.diff_via_hover` | `true` | 区分仅经 hover/active 强调，非基础配色差异 |
| `button_style.theme_vars` | `true` | 配色须用主题变量、无硬编码色值 |
| `button_style.single_primary` | `true` | 避免确认/取消同时 `type="primary"` |
| `button_style.severity` | `minor` | 成对按钮样式不一致的违规级别 |

## 编辑态撑满问答列宽（CODING-EDITBOX-WIDTH）

> 对应 references/editbox-width-rule.md（R-1~R-3 → FR-080）。消息气泡进入编辑态须撑满问答列宽，以 align-items:stretch / width:100% 覆盖已发送态 flex-end 窄宽；textarea 须 width:100% 且内边距与首问输入框一致。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `editbox_width.enabled` | `true` | 启用编辑态撑满列宽审查 |
| `editbox_width.fill_column` | `true` | 编辑容器须撑满问答列宽而非停留已发送窄宽 |
| `editbox_width.override_alignment` | `true` | 以 align-items:stretch / width:100% 覆盖已发送态 flex-end |
| `editbox_width.control_fullwidth` | `true` | textarea/input 须 width:100% 且内边距与首问输入框一致 |
| `editbox_width.severity` | `minor` | 编辑框停留窄宽、文字频繁换行的违规级别 |
| `capability_gating_sync.severity` | `warning` | 门控漂移导致功能卡死的违规级别 |

## IndexedDB 写入前剥离 Vue/Pinia 响应式代理（CODING-IDB-REACTIVE-CLONE）

> 对应 references/idb-reactive-clone-rule.md。凡将 store state ref / `reactive()` 对象经 `dbPut`/`put`/`add` 写入 IndexedDB 的路径，写入前必须整树深拷贝为 plain object，否则 proxy 无法被 `structuredClone` 克隆 → `DataError: [object Array] could not be cloned` → 静默丢数据。所有参数集中管理，规则文件仅描述模式。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `idb_reactive_clone.enabled` | `true` | 启用响应式代理写入 IndexedDB 审查（Vue 3 + Pinia + IDB 落盘场景） |
| `idb_reactive_clone.scan_patterns` | `dbPut,saveUserConfig,idbPut,store.put,transactions.add` | 命中即须核对入参是否已深拷贝的 IDB 写入点（逗号分隔） |
| `idb_reactive_clone.clone_required_before_put` | `true` | IDB 写入前必须对 reactive 入参整树深拷贝 |
| `idb_reactive_clone.forbidden_unsafe_patterns` | `toRaw(,structuredClone(` | 命中即判违规的"伪剥离"写法（toRaw 只剥顶层 / structuredClone 无法克隆代理） |
| `idb_reactive_clone.recommended_clone` | `JSON.parse(JSON.stringify(x))` | 推荐深拷贝范式（纯数据模型）；含 Date/函数/undefined 改用 toRaw+递归 |
| `idb_reactive_clone.severity` | `critical` | 直传 reactive 代理导致静默丢配置的违规级别 |