---
name: "wiki-auto-testing"
description: "Automates end-to-end frontend testing with Playwright: build, start services, run page/interaction/API/responsive tests, button auto-discovery, fix issues. Invoke when user asks to test frontend, run e2e tests, or verify system after changes."
---

# Wiki Auto Testing

基于 Playwright 的前端自动化测试技能。覆盖构建、启动、页面导航、交互功能、API 端点、响应式布局、控制台错误检查的全流程测试。

## 触发条件

- "测试前端" / "全面测试" / "e2e 测试"
- "构建后测试" / "启动后测试"
- "验证系统是否正常"
- "Playwright 测试" / "浏览器测试"

## 前置条件

1. **Playwright 已安装**：python -c "from playwright.sync_api import sync_playwright" 可执行
2. **PyYAML 已安装**：python -c "import yaml" 可执行
3. **配置文件存在**：config.yaml + defaults.yaml 已配置
4. **项目根标记存在**：项目根目录有 .git 或 package.json

## 配置文件

所有参数通过 YAML 统一管理。修改配置文件即可适配不同项目。

### 配置分层

| 层级 | 文件 | 内容 |
|------|------|------|
| 默认值 | defaults.yaml | 技能通用参数：超时、浏览器选项、终端策略 |
| 项目配置 | config.yaml | 项目特定参数：URL、端口、选择器、页面列表、API 端点 |

### 执行模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 传统模式 | 按阶段脚本执行 | 默认，稳定可靠 |
| 动态引擎 | 读取 test_plan.phases 中的步骤定义 | 灵活定制，无需改代码 |

### 核心配置块

| 配置块 | 用途 |
|--------|------|
| working_directory | 项目根目录自动定位 |
| build / startup | 构建/启动脚本（可设 enabled: false 跳过） |
| service | 前后端地址、端口、健康检查 |
| browser | headless、启动参数、多视口 |
| navigation | 导航选择器、页面列表及期望元素 |
| button_discovery | 按钮自动发现、排除规则、破坏性保护 |
| interactions | 主题切换、表单、标签页交互 |
| api_tests | API 端点列表 |
| console_error_filter | 控制台错误过滤关键词 |
| test_plan | 测试阶段编排（可选子集或自定义步骤） |
| route_registration_check | 路由注册验证（后端 routes/*.ts 是否在入口文件注册） |
| type_sync_check | 类型同步验证（前后端 types.ts 接口字段对齐） |
| cors_bypass | CORS 绕过策略（context_request / backend_proxy / disabled） |
| headless_crash_guard | Headless 崩溃防护（必须的 Chromium 启动参数） |
| powershell_compatibility | PowerShell 兼容性（禁止 && / || 语法、长命令拆分） |
| encoding_safety_enhanced | 编码安全增强（写入后验证、U+FFFD 检测） |
| scroll_container_tests | 滚动容器测试（双重滚动裁切、flex 子项压缩检测） |
| spa_navigation_tests | SPA 内部跳转测试（CustomEvent 派发、监听器清理） |
| update_check_tests | 检查更新状态机测试（5 态覆盖、定时器清理、轮询节奏） |
| build_artifact_verification | 构建产物三要素验证（HTTP 状态码 + Content-Length + 关键字符串） |
| browser_automation_fallback | 浏览器自动化降级链（MCP→subagent→curl，每级降级记录原因） |
| nav_dual_mode_tests | 导航栏折叠/展开测试（切换、tooltip、12 图标导航、状态持久化） |
| icon_theme_tests | 图标主题跟随测试（currentColor + 6 主题切换验证） |
| powershell_string_verification | PowerShell 字符串验证模式（禁用 curl.exe 管道赋值，改用 Invoke-WebRequest） |
| async_reliability_tests | Async 可靠性测试（超时防护/心跳线程/兜底数据/运行时验证） |
| verification | 配置一致性/热更新闭环/降级机制验证 |
| destructive_buttons | 破坏性按钮白名单（测试流程安全保护） |
| tauri | Tauri 2.x 桌面应用测试（构建/启动/窗口/invoke 权限/错误诊断） |
| spa | SPA 产物验证（时间戳对比 + JS chunk 特征验证） |
| health_check | Tauri 后端健康检查（端点/重试次数/超时） |
| invoke | Tauri invoke 权限三层验证（插件依赖/权限声明/URL 白名单） |
| disk_space | 磁盘空间检查（debug/release 最小空间阈值） |
| console_log | Tauri 日志采集（前缀过滤/错误关键词分类） |
| playwright_wait_strategy | Playwright 等待策略（禁用 networkidle + domcontentloaded + 显式等待） |
| test_selector_priority | 测试选择器优先级（ID > data-testid > aria-label > class > placeholder） |
| vite_cache_cleanup | Vite 缓存清理（测试前清理缓存或硬刷新） |
| control_layering_tests | 控件分层测试（折叠面板展开/收起、动画、视觉反馈） |
| third_party_error_guard_tests | 第三方库错误防护测试（三层防护验证、LLM 内容预校验） |
| parallel_loading_tests | 多资源并行加载测试（allSettled 验证、错误收集、降级） |
| timeout_chain_tests | 超时阈值链式匹配测试（递增覆盖、部分结果保留、降级路径） |
| folding_panel_event_tests | 折叠面板事件冲突测试（click outside 排除、teleport 组件、@mousedown.stop） |
| media_generation_tests | v3 媒体生成工具测试（外部 API 契约/超时分级/归档 frontmatter/长任务状态机/外部 API 不可达降级） |

## 测试流程（6 阶段）

### 阶段 1：构建
读取 build.script_path → 执行构建 → 验证产物 index.html 存在。
- 子阶段 1.1 构建前检查（可选）：编码安全增强检查、PowerShell 兼容性检查

### 阶段 2：启动服务
读取 startup.script_path → 执行启动 → 轮询端口 → 验证 /health 返回 200。

### 阶段 3：基础功能
首页加载 → 验证 title → 遍历导航 tabs → 验证各页面元素 → 截图 → 收集控制台错误。
- 子阶段 3.1 编码检测 / 3.2 路由注册验证 / 3.3 类型同步验证 / 3.4 Headless 崩溃防护 / 3.5 Playwright 等待策略验证 / 3.6 测试选择器优先级验证 / 3.7 Vite 缓存清理验证（均可选）

### 阶段 4：交互功能
主题切换 → 表单输入 → 标签页切换 → **按钮自动发现**。
- 子阶段 4.1 危险操作测试（可选）：dry_run 默认开启 / danger 样式 / 二次确认 / 取消不发请求

### 阶段 5：补充测试
响应式布局 → API 端点 → 控制台错误校验 → **临时文件清理**（`cleanup.cleanup_on_success: true` 时）。
- 子阶段 5.1 CORS 绕过 / 5.2 滚动容器裁切 / 5.3 SPA 内部跳转 / 5.4 检查更新状态机 / 5.10 控件分层 / 5.11 第三方库错误防护 / 5.12 并行加载 / 5.13 超时阈值链式 / 5.14 折叠面板事件冲突 / 5.15-5.19 v3 媒体生成工具测试（均可选）

### 阶段 6：结果汇总
输出摘要 → 保存 JSON 结果 → 如有失败项，自动修复后回归。

> 子阶段详细验证逻辑、参数表与配置示例见 [references/testing-patterns.md](references/testing-patterns.md) 各模式说明。

## 使用方式

1. 确保 config.yaml 已按项目配置
2. 服务已运行时，设 build.enabled: false 和 startup.enabled: false
3. 调用本技能
4. 结果保存在 output.result_file 和 output.screenshot_dir
5. 失败项自动修复并回归

## 运行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| --config PATH | 指定配置文件路径 | --config /path/to/config.yaml |
| --quiet | 抑制逐条测试日志 | --quiet |
| --phase PHASES... | 只运行指定阶段 | --phase basic |
| --engine | 使用动态引擎模式 | --engine |

## 动态引擎步骤类型

| 步骤类型 | 参数 | 说明 |
|----------|------|------|
| navigate | url, wait, timeout | 导航到页面 |
| navigate_tab | selector, label, wait_ms | 点击导航 tab |
| assert_visible | selector, name | 断言元素可见 |
| assert_title | contains | 断言页面标题 |
| click | selector, force | 点击元素 |
| fill | selector, text | 填写输入框 |
| fill_and_submit | selector, text, submit, submit_method | 填写并提交表单 |
| press_key | key | 按下键盘按键 |
| api_check | path, expected_status | API 端点检查 |
| screenshot | path | 保存截图 |
| wait | ms | 等待指定毫秒 |
| theme_switch | - | 主题切换测试 |
| button_discovery | - | 按钮自动发现 |
| responsive_check | - | 响应式布局检查 |
| console_check | - | 控制台错误检查 |
| persistence_crud_test | resource, test_id, payload | 持久化层 CRUD 全生命周期 + PUT 后立即 GET 对比（验证缓存刷新） |
| path_traversal_test | resource, malicious_ids | 路径穿越防护测试（非法 ID 必须返回 4xx） |
| fallback_degradation_test | api_patterns, expected_behavior, wait_ms | 降级测试（拦截 API 返回 503，验证前端不崩溃） |
| encoding_check | check_pages, scan_selectors, fffd_codepoint | 编码检测：dump DOM 文本码点，检查是否含 U+FFFD 替换字符 |
| dangerous_action_test | test_pages, forms, confirm_component | 危险操作完整测试：dry_run 默认值 → danger 样式 → 二次确认 → 取消 → 执行 |
| multi_form_test | test_pages, form_container_selector, loading_selector, result_selector | 多表单独立状态测试：验证每表单独立 loading/result，互不干扰 |
| service_lifecycle | stop_old_process, start_backend, start_frontend, required_ports | 服务生命周期：停止旧进程 → 启动新服务 → 验证端口监听 |
| temp_cleanup | temp_files_pattern, temp_screenshots_pattern, cleanup_dirs | 临时文件清理：按 pattern 删除测试产生的临时脚本和截图 |
| scroll_container_check | test_pages, outer_scroll_selectors, inner_overflow_selectors, card_selectors, min_card_height_px | 滚动容器裁切检测：验证容器链路上 overflow-y: auto 嵌套层数 ≤ 1，卡片高度 ≥ min_card_height_px |
| spa_navigation_check | test_routes, event_name_pattern, project_name, app_entry, allowed_views | SPA 内部跳转验证：触发跳转 → 验证视图切换 → 检查 CustomEvent 派发与监听器生命周期配对 |
| update_check_state_machine | test_pages, update_endpoint, required_states, offline_mode, cache_ttl_ms, poll_interval_ms | 检查更新状态机验证：5 态覆盖 + 离线模式固定返回 + 轮询间隔 ≥ 缓存 TTL + 定时器清理 |
| build_artifact_check | bundle_directory, key_strings, required_http_status | 构建产物验证：扫描产物目录，验证 HTTP 200 + Content-Length + 关键字符串包含 |
| browser_fallback_check | chain, core_verifications, unsupported_verifications | 浏览器自动化降级：按链路降级 MCP→subagent→curl，记录降级原因 |
| nav_dual_mode_check | toggle_selector, menu_items, tooltip_selector | 导航栏双模式测试：折叠/展开切换 + tooltip 显示 + 12 图标点击导航 + localStorage 持久化 |
| icon_theme_check | icon_selectors, test_themes, theme_switcher_selector | 图标主题跟随测试：6 主题切换验证图标颜色变化（currentColor 生效） |
| powershell_string_check | forbidden_patterns, recommended_pattern | PowerShell 字符串验证：扫描测试脚本中 curl.exe 管道赋值模式，提示改用 Invoke-WebRequest |
| async_reliability_static_check | check_sections (timeout_protection, heartbeat_reliability, fallback_data) | Async 可靠性静态检查：grep 扫描未包裹超时的 await、心跳使用 asyncio.Task 违规、超时后无兜底数据 |
| async_reliability_runtime_check | monitor_duration_sec, max_gap_sec, status_file_pattern | Async 可靠性运行时验证：监控状态文件 ts 字段更新间隔，模拟阻塞验证心跳线程独立性 |
| config_consistency_check | check_entries, verify_method | 配置一致性验证：修改配置 → 重启 → 验证所有入口返回一致值 |
| hot_update_check | verify_api | 热更新闭环验证：保存配置 → 不重启 → 验证立即生效 |
| degradation_check | test_cases | 降级机制验证：正常路径 + 降级路径 + 兜底路径 |
| precheck | required_ports, health_check_endpoint | 前置检查步骤：端口监听 + 健康检查 + 浏览器可启动性验证，失败时按配置自动启动服务 |
| test_sync_check | test_file_patterns, selector_patterns | 测试用例同步检查：扫描 git diff 选择器变更，Grep 测试文件引用，检测静默吞错与同 commit 提交 |
| failure_classify | failure_rules, suggestions | 失败分类：按 rules 模式匹配错误消息，输出对应 suggestions 修复建议，auto_fix 时触发测试同步检查 |
| service_manage | action (stop/start/status), required_ports | 服务管理：按 action 执行停止/启动/状态查询，处理端口冲突与日志重定向残留进程清理 |
| playwright_wait_strategy_check | check_pages, forbidden_wait_strategy, recommended_wait_strategy, persistent_resource_patterns | Playwright 等待策略验证：检查测试代码是否使用禁用的等待策略，有持续加载资源时禁用 networkidle |
| test_selector_priority_check | test_file_patterns, selector_priority_order, discouraged_selectors, required_stable_attributes | 测试选择器优先级验证：扫描测试文件选择器，优先使用 ID/data-testid，禁用 placeholder/text 匹配 |
| vite_cache_cleanup_check | vite_cache_dirs, auto_cleanup_before_test, cleanup_command, stale_version_signals | Vite 缓存清理验证：检查缓存目录，可选自动清理，监控旧版本加载信号 |
| control_layering_check | toggle_selector, panel_selector, animation_duration_ms, trigger_active_class | 控件分层验证：折叠面板展开/收起 + Transition 动画 + 触发按钮激活状态 |
| third_party_error_guard_check | test_libraries, invalid_inputs, suppress_config_keys, parse_method_names, error_css_classes | 第三方库错误防护验证：注入错误语法 + 验证三层防护 + CSS 兜底 |
| parallel_loading_check | resource_patterns, required_wrapper, error_collection_required, degradation_path_required, total_timeout_ms | 并行加载验证：多资源并行加载 + 单失败降级 + 错误收集验证 |
| timeout_chain_check | layer_order, margin_multiplier, partial_result_required, degradation_path_required, simulate_timeout_ms | 超时阈值链式验证：模拟下层超时 + 验证上层不中断 + 部分结果保留 |
| folding_panel_event_check | panel_selector, click_outside_exclude_selectors, teleport_selectors, required_dropdown_props, required_event_modifiers | 折叠面板事件冲突验证：click outside + el-dropdown 交互 + teleport 排除 |
| external_api_contract_check | test_endpoints, test_payloads, require_fetch_wrapper, diagnostic_error_codes | 外部 API 集成契约验证：fetchWithDiagnostics 包装 + 字段双重路径兼容 + 类型显式转换 + 错误码翻译 |
| timeout_tier_check | expected_tiers, verify_method, scan_directories, forbidden_uniform_timeout | 超时分级验证：grep AbortSignal.timeout 调用，比对超时值与任务类型，禁止所有调用用同一超时 |
| archive_frontmatter_check | archive_dir, required_fields, expected_output_modes, filename_pattern, business_fields_by_mode | 归档 frontmatter 验证：扫描归档目录，验证 type/output_mode/generated_at 字段完整 + 文件名模式匹配 |
| long_task_state_machine_check | required_states, test_views, video_dialog_selector, state_ui_selectors, required_abort_reasons | 长任务状态机验证：5 态覆盖 + abortReason 三态 + 定时器清理 + 关闭/重置拆分 + setTimeout 超时 |
| external_api_unavailable_test | intercepted_endpoints, response_status, expected_behavior, forbidden_error_messages, require_abort_error_swallow | 外部 API 不可达降级验证：拦截端点返回 503 + 验证前端不崩溃 + 错误消息分类 + AbortError 吞掉 |

## 测试模式与协议（按需加载）

以下详情按需加载，避免入口文件 token 浪费：

| 文档 | 内容摘要 |
|------|----------|
| [测试协议（Protocols）](references/protocols.md) | 前置检查 / 测试用例同步 / 失败分类 / 服务管理 / 搜索结果交叉验证 5 个协议 |
| [测试模式（复盘提炼）](references/testing-patterns.md) | 持久化层 / 系统清理 / Async 可靠性 / 配置一致性 / 热更新 / 降级 / 目录结构 / v3 媒体生成 / v2 导航栏 9 个模式 |
| [批量编译测试复盘](references/batch-compile-testing.md) | 文件夹上传批量编译六阶段测试流程、4 个新增配置块、DAG 依赖关系 |
| [Tauri 桌面应用测试](references/tauri-desktop-testing.md) | Tauri 2.x 桌面应用 6 阶段测试流程、invoke 权限三层验证、SPA 产物验证 |
| [Async 可靠性测试详情](references/async-reliability-testing.md) | Async 可靠性测试方法、模拟阻塞模板、覆盖矩阵 |
| [SPA 产物验证](references/spa-artifact-verification.md) | 时间戳对比法 + JS chunk 特征验证法 |
| [invoke 权限验证](references/invoke-permission-verification.md) | Tauri 2.x capabilities.json 三层权限验证 |
| [版本历史（完整）](references/changelog.md) | 完整版本历史（v1.1.0 - v2.2.0），本文件仅保留最近 3 版 |

## 破坏性按钮保护机制

测试中遇到破坏性按钮时，必须先备份配置，测试后恢复。破坏性按钮白名单在 `destructive_buttons` 配置中定义。

| 按钮文本 | 风险 | 处理策略 |
|---|---|---|
| 恢复初始配置 | 覆盖用户自定义配置 | 测试前备份 config.json，测试后恢复 |
| 删除 | 删除数据 | 测试前备份相关数据，测试后恢复 |
| 清除 | 清空配置 | 测试前备份，测试后恢复 |
| 重置 | 恢复默认值 | 测试前备份，测试后恢复 |

**强制流程**：测试前备份 → 执行破坏性操作 → 验证效果 → 测试后从备份恢复

> 与 `dangerous_action_tests` 的关系：`dangerous_action_tests` 验证 UI 交互行为（dry_run/二次确认/danger 样式），本节确保测试流程自身不会因点击破坏性按钮而破坏测试环境。两者互补，前者测功能正确性，后者测测试流程安全性。

## 参考文档导航

以下内容已拆分到 references/ 目录（渐进式披露，一层引用深度）：

| 文件 | 内容 |
|------|------|
| [references/testing-patterns.md](references/testing-patterns.md) | 持久化层 / 系统清理 / Async可靠性 / 配置一致性 / 热更新 / 降级机制 / 目录结构 / v3媒体生成 共 9 个测试复盘章节 |
| [references/protocols.md](references/protocols.md) | 前置检查 / 测试用例同步 / 失败分类 / 服务管理 / 搜索交叉验证 共 5 个协议 + 导航栏改造复盘 + 批量编译复盘 |
| [references/tauri-desktop-testing.md](references/tauri-desktop-testing.md) | Tauri 2.x 桌面应用测试（复盘提炼） |
| [references/changelog.md](references/changelog.md) | 版本历史（完整记录） |

## 适配新项目

仅需修改 config.yaml，按需启用配置项（详细参数见对应 references 文档）：

**基础配置**：service.frontend_url / service.api_url / navigation.tab_selector / navigation.pages / button_discovery.button_selectors / api_tests.endpoints / build.script_path / startup.script_path / button_discovery.destructive_button_texts

**复盘提炼配置**（详见 [references/testing-patterns.md](references/testing-patterns.md)）：persistence_tests.endpoints / encoding_tests.check_pages / dangerous_action_tests.test_pages / service_lifecycle.start_backend / cleanup.temp_files_pattern / powershell_constraints.blocked_commands / route_registration_check.backend_route_directory / type_sync_check.backend_types_path / cors_bypass.strategy / headless_crash_guard.required_launch_args / powershell_compatibility.forbidden_syntaxes / encoding_safety_enhanced.check_extensions / scroll_container_tests.test_pages / spa_navigation_tests.test_routes / update_check_tests.test_pages / build_artifact_verification.serving_endpoint_template / browser_automation_fallback.chain / nav_dual_mode_tests.toggle_selector / icon_theme_tests.icon_selectors / powershell_string_verification.forbidden_patterns / async_reliability_tests.timeout_protection / verification.config_consistency_check / verification.hot_update_verification / verification.degradation_verification / destructive_buttons

**Tauri 桌面应用配置**（详见 [references/tauri-desktop-testing.md](references/tauri-desktop-testing.md)）：tauri.enabled / tauri.exe_name / tauri.src_tauri_dir / tauri.build_script_path / spa.source_dirs / spa.output_dir / health_check.endpoint / invoke.commands / invoke.permissions / invoke.url_patterns / disk_space.debug_min_gb / console_log.prefixes

**编码规范测试配置**（详见 [references/testing-patterns.md](references/testing-patterns.md)）：control_layering_tests.toggle_selector / third_party_error_guard_tests.test_libraries / parallel_loading_tests.resource_patterns / timeout_chain_tests.layer_order / folding_panel_event_tests.panel_selector / media_generation_tests.external_api_contract.test_endpoints / media_generation_tests.timeout_tier_verification.expected_tiers / media_generation_tests.archive_frontmatter_check.archive_dir / media_generation_tests.long_task_state_machine.test_views / media_generation_tests.external_api_unavailable.intercepted_endpoints / powershell_long_process.long_running_commands（与 CODING-056/057/059/060/061/063/064/065 编码规范对齐）

## 适用场景

- Vue 3 / React / Angular 等 SPA 应用
- Vite / Webpack 构建的前端项目
- 有独立后端 API 的全栈项目
- Element Plus / Ant Design 等组件库项目
- Windows 环境下的 Playwright 测试
- **有编码风险的 Windows 中文环境**（页面 tab/标签可能乱码，需用 Unicode 码点验证）
- **有危险操作（dry_run/二次确认/danger 样式）的清理类模块**
- **多表单独立状态管理（每表单独立 loading/result）的模块**
- **flex 布局的多卡片长内容页面**（帮助文档、设置面板，需检测双重滚动裁切）
- **SPA 手动路由项目的跨组件跳转**（无 vue-router，需验证 CustomEvent 派发）
- **内网部署项目的检查更新功能**（无 GitHub Release 通道，需验证离线模式降级）
- **菜单项 >7 的导航栏需折叠/展开双模式**（验证切换、tooltip、12 图标导航、localStorage 持久化）
- **多主题项目的矢量图标**（验证 currentColor 在 6 主题下自动跟随变色）
- **vite build 后构建产物可访问性验证**（HTTP 200 + Content-Length + 关键字符串）
- **Playwright MCP 不可用时的浏览器自动化降级**（MCP→subagent→curl 三级降级）
- **PowerShell 测试脚本的字符串验证模式**（避免 curl.exe 管道赋值陷阱）
- **asyncio + Playwright 的项目**（需验证心跳可靠性、超时防护、兜底数据）
- **子进程通过状态文件通信的架构**（需验证 ts 字段持续更新）
- **有配置热更新需求的项目**（需验证保存后立即生效）
- **有降级机制的项目**（需验证降级路径正常工作）
- **Tauri 2.x 桌面应用**（需验证构建/启动/窗口创建/invoke 权限/错误诊断全流程）
- **Tauri 项目的 SPA 产物与源码同步验证**（时间戳对比 + JS chunk 特征验证）
- **Tauri 项目的 invoke 权限完整性验证**（capabilities.json 三层权限检查）
- **工具栏控件 > 5 的折叠面板分层**（验证展开/收起、Transition 动画、触发按钮激活状态）
- **mermaid/katex 等第三方库的错误防护**（验证三层防护：库级配置 + LLM 内容预校验 + CSS 兜底）
- **MCP 工具多资源并行加载**（验证 Promise.allSettled 并行加载、单失败降级、错误收集）
- **前后端超时阈值链式匹配**（验证前端 120s > 后端 MCP 30s 递增覆盖、部分结果保留、降级路径）
- **折叠面板内 el-dropdown 事件冲突**（验证 click outside 排除、teleport 组件处理、@mousedown.stop 修饰符）
- **调用外部 API 的媒体生成功能**（验证 fetchWithDiagnostics 包装 + 字段双重路径兼容 + 错误码翻译，对应 CODING-056）
- **多任务类型的不同超时阈值验证**（验证 task_creation/polling/image/video/llm 分级超时，禁止统一超时，对应 CODING-057）
- **LLM 生成产物归档到 vault**（验证 frontmatter 字段 type/output_mode/generated_at 完整 + 文件名模式匹配，对应 CODING-060）
- **长任务前端轮询 + 状态机 UI**（验证 5 态覆盖 + abortReason 三态 + 定时器清理 + setTimeout 超时，对应 CODING-065）
- **外部 API 不可达时的降级策略**（验证拦截 503 不崩溃 + 错误消息分类 + AbortError 吞掉 + reader.cancel 兜底，对应 CODING-056/064）

## 不适用场景

- 纯静态 HTML 页面
- 移动端 App 测试
- 需要 OAuth/SSO 认证的页面
- SSR 应用（渲染时机不同）
- WebSocket 密集的应用
- **无前端界面的纯 API 测试**（用 `persistence_crud_test` / `path_traversal_test` 替代）
- **CSS Grid 布局**（grid 子项默认不收缩，无需 flex-shrink 守卫）
- **vue-router / react-router 项目**（直接用 router.push，无需验证 CustomEvent）
- **公网开源项目的检查更新**（需真实 GitHub API 调用，离线模式不适用）
- **多端口部署项目**（前端由 nginx/CDN 托管，无需构建产物验证）
- **Font Awesome 等字体图标项目**（图标主题跟随测试不适用）
- **Linux/Mac bash 环境**（PowerShell 字符串验证不适用，bash 的 curl 输出天然是字符串）
- **纯同步代码项目**（Async 可靠性测试不适用）
- **无 IPC 调用的简单 Web 项目**（心跳线程/状态文件验证不适用）
- **Tauri 1.x 项目**（权限模型与 2.x 不同，invoke 权限验证不适用）
- **无 invoke 调用的简单 Tauri 项目**（invoke 权限三层验证不适用）
- **纯后端 API 项目**（无 SPA 前端，Tauri 测试全流程不适用）
- **控件数量 ≤ 5 的简单工具栏**（无需分层，控件可直接平铺）
- **无第三方库依赖的纯文本渲染**（无需错误防护，CSS 兜底不适用）
- **串行加载的单资源项目**（无需 Promise.allSettled，allSettled 验证不适用）
- **单层超时的简单项目**（无前后端链式关系，链式匹配验证不适用）
- **无 teleport 组件的纯本地 dropdown**（无事件冲突，click outside 排除验证不适用）
- **纯本地 LLM 调用**（无外部 API 集成，fetchWithDiagnostics 包装与错误码翻译验证不适用）
- **秒级同步任务**（无长任务轮询，5 状态机与 abortReason 三态验证不适用）
- **无归档需求的临时查询**（LLM 产物不落盘 vault，frontmatter 标准化验证不适用）

## 故障排查

常见问题及解决方案见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。重点关注：

- **编码乱码（U+FFFD）**：第 11 条，用 Unicode 码点匹配替代终端字符串匹配
- **Playwright 中文匹配失败**：第 12 条，避免 `has_text` 中文，改用 `get_dom_text_codepoints` 比对码点
- **端口占用**：第 13 条，用 `service_lifecycle.stop_old_process: true` 启动前清理
- **bat 脚本 pause 卡住**：第 14 条，配置 `powershell_constraints.bypass_bat_pause: true`
- **GPU 崩溃**：第 15 条，`browser.launch_args` 必须含 `--disable-gpu`
- **Python 文件编码声明缺失**：第 16 条，所有 .py 文件首行加 `# -*- coding: utf-8 -*-`
- **API 测试返回 404（路由未注册）**：第 17 条，启用 `route_registration_check.enabled: true`
- **前后端类型不匹配**：第 18 条，启用 `type_sync_check.enabled: true`
- **Chromium headless 模式崩溃**：第 19 条，启用 `headless_crash_guard.enabled: true`
- **Python 测试脚本编码错误**：第 20 条，启用 `encoding_safety_enhanced.verify_after_write: true`
- **PowerShell 命令拼接失败**：第 21 条，启用 `powershell_compatibility.enabled: true`
- **章节卡片仅显示标题（双重滚动裁切）**：第 22 条，启用 `scroll_container_tests.enabled: true`
- **跨组件跳转失效（About → Help 无响应）**：第 23 条，启用 `spa_navigation_tests.enabled: true`
- **检查更新卡在 loading 不恢复**：第 24 条，启用 `update_check_tests.enabled: true`
- **构建产物 HTTP 404 或内容截断**：第 25 条，启用 `build_artifact_verification.enabled: true`
- **Playwright MCP 报 "MCP server is not found"**：第 26 条，启用 `browser_automation_fallback.enabled: true`
- **导航栏折叠/展开切换失效**：第 27 条，启用 `nav_dual_mode_tests.enabled: true`
- **图标不跟随主题变色**：第 28 条，启用 `icon_theme_tests.enabled: true`
- **PowerShell 字符串验证输出混乱**：第 29 条，启用 `powershell_string_verification.enabled: true`
- **Tauri 启动后立即退出或白屏**：第 30 条，启用 `tauri.enabled: true`
- **Tauri invoke 调用报 `Plugin not found` / `not allowed` / `URL: local`**：第 31 条，启用 `invoke` 配置块
- **Tauri 编译报 `linker 'lld-link' not found`**：第 32 条，启用 `tauri.enabled: true` 自动预检
- **折叠面板展开后立即收起**：第 30 条，启用 `control_layering_tests.enabled: true`
- **第三方库渲染显示 Syntax error in text**：第 31 条，启用 `third_party_error_guard_tests.enabled: true`
- **MCP 工具加载导致 AI 未回复**：第 32 条，启用 `parallel_loading_tests.enabled: true`
- **超时阈值不匹配导致 AI 回复被丢弃**：第 33 条，启用 `timeout_chain_tests.enabled: true`
- **折叠面板内下拉菜单点击后关闭**：第 34 条，启用 `folding_panel_event_tests.enabled: true`
- **视频生成卡在 processing 不返回**：第 35 条，启用 `media_generation_tests.long_task_state_machine.enabled: true`
- **归档 Markdown frontmatter 字段缺失**：第 36 条，启用 `media_generation_tests.archive_frontmatter_check.enabled: true`
- **外部 API 类型契约不匹配（seconds 字段）**：第 37 条，启用 `media_generation_tests.external_api_contract.enabled: true`
- **长任务轮询定时器未清理**：第 38 条，启用 `media_generation_tests.long_task_state_machine.require_timer_cleanup: true`
- **PowerShell 管道导致 EPIPE 断裂（退出码 -1）**：第 39 条，启用 `powershell_long_process.enabled: true`

## Version History

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v2.3.0 | 2026-07-31 | **PowerShell 长时进程管道陷阱测试补充**：新增 powershell_long_process 核心配置块；新增 EPIPE 故障分类类型（epipe_error）；新增 TROUBLESHOOTING 第 39 条；配置适配章节追加 1 项配置说明。对应 CODING-059 编码规范。 |
| v2.2.0 | 2026-07-31 | **v3 媒体生成工具复盘测试补充**：新增 media_generation_tests 核心配置块（5 个子段）；新增"v3 媒体生成工具测试（复盘提炼）"章节（5 个子阶段 5.15-5.19）；新增 5 个动态引擎步骤类型；适配新项目章节追加 1 项配置说明（第 43 项）；适用场景追加 5 项；不适用场景追加 3 项；故障排查追加 4 条（TROUBLESHOOTING 第 35-38 条）。对应 CODING-056/057/059/060/061/063/064/065 编码规范。 |
| v2.1.0 | 2026-07-31 | **编码规范测试流程补充**：基于控件分层、第三方库错误防护、多资源并行加载、超时阈值链式匹配、折叠面板事件冲突五项编码规范，新增 5 个核心配置块；新增 5 个测试子阶段（5.10-5.14）；新增 5 个动态引擎步骤类型；适配新项目章节追加 5 项配置说明；适用场景追加 5 项；不适用场景追加 5 项；故障排查追加 5 条（TROUBLESHOOTING 第 30-34 条）。 |
| v2.0.0 | 2026-07-22 | **Tauri 2.x 桌面应用测试复盘**：新增"Tauri 2.x 桌面应用测试（复盘提炼）"章节（含 6 阶段测试流程、invoke 权限三层验证、SPA 产物验证、阶段间 DAG 依赖关系、故障排查速查表）；新增 3 个参考文档（tauri-desktop-testing.md / spa-artifact-verification.md / invoke-permission-verification.md）；新增 templates/phase_tauri_desktop.py 测试阶段模板；config.yaml 与 defaults.yaml 新增 tauri / spa / health_check / invoke / disk_space / console_log 6 个配置块。 |

> 完整版本历史见 [references/changelog.md](references/changelog.md)
