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
| 默认值 | defaults.yaml | 技能通用参数：超时、浏览器选项、终端策略、前端验证（类型检查 / 构建，命令与产物目录参数化） |
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
| scope | 测试范围聚焦（只测改动内容：从 changed_paths 推导改动路由/端点） |
| test_coverage | 端点覆盖率检查（校验入口文件注册的每个路由都有测试，防新端点裸奔上线） |
| endpoint_autodiscovery | 端点自动发现（从路由定义推导 api_tests.endpoints，免去手工维护端点清单） |
| idb_reactive_clone_check | IndexedDB 写入前剥离 Vue/Pinia 响应式代理静态守卫（扫描 IDB 写入点 / 校验深拷贝 / 禁伪剥离 toRaw·structuredClone） |
| smoke_strategy | 冒烟验证策略（沙箱受限环境泛化）：进程内冒烟（process_internal_inject，默认，import buildApp() → app.ready() + 最小 SPA-static app inject）与跨进程 TCP 冒烟（tcp_opt_in，真实构建机启用、沙箱禁用）双层；契约级断言（缺密钥 400 / SSE 200 / TTS 200）沙箱无法验证须真实机构建机重跑 |

## 通用性与配置驱动

本技能**完全配置驱动、零硬编码业务参数**，因此可适配任意遵循相同测试约定的项目（不仅限 Karpathy-Wiki），只需修改 `config.yaml` + `defaults.yaml` 即可，无需改动代码。

- **地址 / 端口**：`service.frontend_url` / `service.api_url` / `service.required_ports` 全部参数化；`port_conflict_resolution` 支持端口被占用时自动迁移。
- **API 端点清单**：`api_tests.endpoints` 列表化维护；新增 `endpoint_autodiscovery` 后可由路由定义自动推导，无需手工列举。
- **鉴权**：`auth.login_endpoint` / `auth.token_storage_key` / `auth.token_field` / `auth.credentials` 全部参数化（见 `_shared.authenticate()`，从 `cfg["auth"]` 读取，不硬编码 URL 或 token 键）。
- **路由注册 / 类型对齐**：`route_registration_check` / `type_sync_check` 的路径、入口文件、接口名均配置驱动。
- **测试范围聚焦**：`scope.modified_content`（enabled + `changed_paths`）让技能只测改动内容而非全应用，适配 CI 增量测试与"改动无 UI 界面时浏览器 E2E 低信号"的场景。
- **端点覆盖保障**：`test_coverage.endpoint_coverage_check`（默认 `fail_if_untested: false` 非阻断）标记未测端点，防止新端点裸奔上线。
- 所有 URL / 端口 / 端点 / 选择器 / 攻击向量 / payload 模板均集中在 YAML；模板与 `_shared.py` 仅读取 `cfg`，不内联业务值。
- **前端规范静态守卫泛化**：`frontend_review_static_check` 在后端守卫基础上新增 `required_patterns` 存在性维度（保护性代码被删即告警），`groups` 全配置化——新增任意前端编码规范（如编辑重发 / autoscroll / 按钮样式 / 编辑框宽度）只需在 YAML 加一组 `name/forbidden_patterns/required_patterns/severity/rule_ref`，无需改 `_step_engine.py`，实现"规范即配置"的泛化覆盖。

> 测试策略与流程复盘见 [references/testing-process-review.md](references/testing-process-review.md)（基于"上下文记忆治理"后端模块测试经验提炼的 4 维度参考）。

**沙箱受限环境验证泛化（`smoke_strategy`）**：验证策略按环境可达性分层，全部参数化在 `config.yaml` 的 `smoke_strategy` 段（零硬编码）：
- **进程内冒烟（默认）**：沙箱跨进程 localhost TCP 被拦截、`app.inject` 全量 app 会挂起 → 验证优先落在同一进程（`import buildApp()` → `app.ready()` 验证启动/注册无回归 + 最小 SPA-static app inject 验证静态伺服）。后端入口须导出 `buildApp()` 且以 `WIKI_SMOKE` 守卫 `listen`。
- **跨进程 TCP 冒烟（opt-in）**：仅在「可达 localhost 的真实构建机」启用（`tcp_opt_in.enabled: true`）；沙箱默认关闭，避免跨进程 `connect` 超时假阴性。
- **契约级断言外置**：缺密钥 400 / SSE 200 / TTS 200 等契约依赖真实机可达性，须在真实构建机重跑（`contract_assertions_on_real_host: true`），沙箱不强行验证。
- 该分层使同一套测试引擎可泛化到任意「沙箱受限 / 真实机构建机」组合，无需改代码（见 testing-process-review.md 第十七轮）。

## 测试复盘工作流（Sequential Thinking）

端到端验证（typecheck → unit → build → deploy → 杀孤儿 → 重启 → 冒烟）每经历一次事故或返工，须用 **Sequential Thinking** 做四维度复盘，并把结论沉淀为 `references/testing-process-review.md` 的新一轮（与 wiki-code-dev「规范提炼方法论」同源）：

| 维度 | 复盘问题 | 产出 |
|------|---------|------|
| ① 成功步骤 | 这次端到端验证是怎么跑通的？哪几步被证明有效（如进程内 inject 5/5、跨进程 dangerouslyDisableSandbox 冒烟）？ | 可复用的验证流水线骨架 |
| ② 不确定性与失败点 | 哪里踩坑（沙箱全量写回滚→build 须 dangerouslyDisableSandbox；跨进程 localhost 被拦；helmet 使 app.inject 挂起；.js 遮蔽 .ts；覆盖危机）？环境约束是什么？ | 防御性检查点 / 降级路径 |
| ③ 可抽象流程与判断 | 哪些步骤可参数化、可泛化到同类项目（构建命令/部署脚本/孤儿端口/冒烟端点/特征串全部配置化）？ | 规则 + 对应 `config.yaml` / `defaults.yaml` 参数 |
| ④ 适用与不适用 | 该流水线在哪些项目成立（后端静态伺服 SPA + IndexedDB local-first + FS 持久化）？哪些是噪声（纯后端 API / 无部署的库）？ | 适用边界（写进测试技能与 testing-process-review.md） |

**操作约定**：合成新一轮测试复盘时，先调用 `mcp__Sequential Thinking__sequentialthinking` 按上表四维度逐步推导（thoughtNumber 自增、可在末步 `isRevision` 修正），把最终结论（成功步骤 / 失败点清单 / 抽象流程 / 适用边界）落到 `references/testing-process-review.md` 对应轮次，并同步更新 `config.yaml` / `defaults.yaml` 的参数块与 SKILL.md「测试流程」阶段说明。所有阈值 / 路径 / 端口 / 特征串一律配置化，**零硬编码**。

**部署阶段参数化**：真实部署流（构建 → 写全新时间戳目录 → 杀孤儿旧进程 → 重启后端 → 冒烟）不写死在脚本逻辑里，全部来自 `config.yaml` / `defaults.yaml` 的 `deploy` 段（与上文「端到端编排」四维复盘一致，见 `references/testing-process-review.md` 第十轮 / 第二十一轮）。沙箱环境须 `dangerouslyDisableSandbox`（Bash 全量写回滚会丢弃构建产物），真实构建机可关。

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
| packaging_config_overwrite_test | installer_script, program_files_flags, exclude_user_data, user_data_patterns | 安装器防覆盖验证：解析安装器脚本（*.iss / *.ps1），确认 `[Files]` 仅含程序文件且用 ignoreversion，用户数据（config.json/.env/vault/data）未打包到 {app} |
| data_dir_derivation_test | data_dir_funcs, expected_anchor, fallback_anchors, expected_pattern, verify_filesystem_write | 数据目录解析落点验证：断言 getUserDataDir()/getDataDir() 返回值符合预期锚点（LOCALAPPDATA 回退 APPDATA→HOME），且文件系统实际写入位置与解析一致 |
| user_data_isolation_test | isolation_resources, malicious_ids, expect_status | 用户数据隔离验证：不同线程/会话数据目录互相隔离；非法 ID 用 UUID 正则校验，越权访问必须返回 4xx |
| backend_logic_unit_test | runner_path, test_file, cwd, fail_patterns, pass_patterns, timeout_ms | 后端逻辑单元验证：直接运行实例化 service 的单元测试文件，验证落盘前纯逻辑（文件名清洗 / 内部前缀剥离 / 路径穿越二次校验）无需浏览器或服务 |
| migration_script_e2e | script_path, runtime, target_arg, apply_flag, temp_vault_dir, setup_command, verify_command, cleanup_temp | 迁移 / 修复脚本端到端：对临时 vault 真实调用脚本（默认 dry-run，显式 --apply 才写盘），验证既不改坏原数据又能正确改写 |
| spa_live_deploy_check | live_base_dir, live_dir_pattern, legacy_dir, complete_marker, asset_prefix, malicious_paths, restart_required, verify_via_disk, required_ports | SPA 实时部署验证：读磁盘枚举 live_base_dir 下匹配 live_dir_pattern 的目录、按 mtime 取最新（等价于 ls -dt | head -1）并校验其含 complete_marker 与 assets/index-*.js；verify_via_disk: true 取代旧版两次 HTTP 比对（spaRoot 启动只解析一次，目录高频轮转下两次 HTTP 会读到不同根而误判）；restart_required 时校验 required_ports 监听（部署后须重启后端）；malicious_paths 样本仅作配置保留，真正 within-root 防穿越由 path_traversal_test 覆盖。v2.6.0 仅写入配置块，v2.17.0 注册并实现 handler（registry 模式，step 可覆盖参数） |
| cross_account_session_check | conversation_store_path, owner_field, session_state_refs, auth_watch_signal, persist_reuse_owner_check, malicious_owner_ids, require_reset_on_auth | 多账户会话隔离验证：断言账户切换/登出触发 resetSession（currentConversationId+scopedOwnerId 作废、列表清空）；persistConversation 复用 id 前以 IndexedDB 实际记录校验归属，他人记录绝不覆盖（冲突改用全新 uuid）；filterByOwner 严格按 ownerId 隔离；跨账户须用真实登出/切换 E2E（非 store 直接 setUser）验证无泄漏 |
| byok_per_user_override_check | user_config_service, user_config_namespaces, override_fields, secret_fields, require_key_fields, override_func, empty_override_falls_back | BYOK 多用户密钥代理验证：断言每用户配置按 userId 命名空间隔离（不跨用户共享）；密钥仅经请求体下发、后端不落盘/不回显 GET/不记日志；缺必需密钥（apiKey/provider/baseUrl/model）请求返回 400 不回落服务端共享；覆盖为纯函数 applyPerRequestOverride、空/默认工具配置回退服务端共享不清空；前端仅当配置存在才下发对应块（避免空 toolsConfig 清空服务端能力） |
| streaming_resume_check | streaming_store_path, persist_debounce_ms, last_active_key, streaming_status, no_abort_on_unmount, skip_when_loading | 流式回答增量持久化与续答验证：断言流式分片增量（防抖）落盘中间态而非仅完成时；页面卸载/切页不 abort 在途流（仅卸监听、后台继续生成）；重载恢复仅对 status='streaming' 末条续答、interrupted/error 不自动续；SPA 重挂载且后台流活跃(isLoading)时跳过续答 |
| indexeddb_test_isolation_check | namespace_prefixes, forbidden_patterns, flush_rounds | 前端隔离测试纪律验证：断言隔离测试用唯一 userId 命名空间（而非 beforeEach indexedDB.deleteDatabase，会导致 onblocked/超时/跨用例泄漏）；fake-indexeddb 异步落盘断言须多轮 setTimeout(0) flush |
| backend_review_static_check | scan_dirs, file_glob, groups[name,patterns,message,rule_ref,severity,regex], force | 后端行为级缺陷静态守卫：配置化 grep 后端源码 forbid 模式组（as any 类型绕过 / ffprobe 冗余探测 / 落盘函数吞错信号 / 硬编码 30000 / execFile 未 await / 路由 return 完整性 / 响应钩子安全 / 压缩默认关闭 / 用户库初始化完整性 / PowerShell 端口清理安全），error 级命中即阻断、warn 级仅标记，全部模式来自配置零硬编码 |
| route_response_branch_coverage | routes[{route_name, method, token_env?, branch_cases[name,params,expected_status,required_fields,required_headers,description]}], route_name, method, branch_cases, timeout_ms, force | 路由响应分支覆盖：配置化逐分支断言被测路由（支持多路由 `routes` 列表，向后兼容单路由 `route_name`/`method`/`branch_cases`）在各请求参数组合下的返回状态码，并校验 200 响应含必需字段（`required_fields`）与必需响应头（`required_headers`，如 `Content-Disposition` 验证 BR-098/BR-100）；需登录分支经 `token_env` 环境变量注入 Bearer Token，匿名分支不注入以断言 fail-closed 401（验证 BR-097 鉴权门）；把"归档路由响应分支覆盖 + 静默缺陷回归"与"下载读端点鉴权门 / 错误码透传 / 头时序"判断逻辑落地，全部用例来自配置零硬编码 |
| frontend_review_static_check | scan_dirs, file_glob, groups[name, forbidden_patterns, required_patterns, message, rule_ref, severity, regex], force | 前端行为级缺陷静态守卫：配置化扫描前端源码 forbidden_patterns（命中即违规）+ required_patterns（整个扫描集完全缺失即违规，守护保护性代码被重构误删），error 级阻断 / warn 级标记；比 backend_review_static_check 更泛化（存在性 + 禁止性双模式）。内置 FR-077~FR-080 四组（编辑重发配对 / autoscroll 双 rAF / 成对按钮样式 / 编辑框撑满）+ FR-084 auth_fetch_wrapped（受保护端点禁裸 fetch）+ FR-086~FR-088 三组派生（persistent_component_visible_watch 守护 watch(visible) 不被误删 / object_url_revoked 守护 revokeObjectURL 不被误删 / audio_autoplay_distinguished 守护「语音合成失败」与「播放被浏览器拦截」两类文案分离），新增前端规范只需加一组，全部零硬编码 |
| idb_reactive_clone_check | scan_dirs, file_glob, scan_patterns, reactive_indicators, reactive_arg_regex, safe_clone_indicators, forbidden_unsafe_patterns, scan_window_lines, severity_missing_clone, severity_unsafe, rule_ref, force | IndexedDB 写入前剥离 Vue/Pinia 响应式代理静态守卫：配置化扫描前端源码 IDB 写入点（dbPut / saveUserConfig / idbPut / store.put / transactions.add），核对写入值若源自 store state ref / reactive() 是否在写入前整树深拷贝（JSON.parse(JSON.stringify(x)) / clone(x)）；对"伪剥离"写法 toRaw(（仅剥顶层）判违规（R-2），structuredClone(reactiveObj) 无法克隆代理由 R-1 分支覆盖；直传 reactive 代理导致 `[object Array] could not be cloned` 静默丢配置（R-1）。error 级阻断 / warn 级标记，全部模式来自配置零硬编码；与 FR-081 / CODING-IDB-REACTIVE-CLONE 对齐 |
| dependency_store_hygiene_check | enabled, store_dir_key, canonical_store_dir, forbidden_store_dirs, scan_root, assert_npmrc_store_dir, severity, rule_ref, force | 依赖 store 卫生静态守卫：断言全局 ~/.npmrc 显式声明收敛键（store-dir）避免 pnpm 主目录探测被沙箱钩子打断后退化为盘根散落 .pnpm-store；扫描 scan_root 检测与 canonical_store_dir 不一致的孤儿 .pnpm-store（剪枝 node_modules/.git/dist/build/public 等重目录避免深遍历），warn 级标记、error 级可升；全部路径/键名/目录名来自配置零硬编码；与 FR-085 / BR-095 / CODING-PNPM-STORE-HYGIENE 对齐 |

## 测试模式与协议（按需加载）

以下详情按需加载，避免入口文件 token 浪费：

| 文档 | 内容摘要 |
|------|----------|
| [测试协议（Protocols）](references/protocols.md) | 前置检查 / 测试用例同步 / 失败分类 / 服务管理 / 搜索结果交叉验证 5 个协议 + Flake 隔离协议 |
| [测试流程复盘（Process Review）](references/testing-process-review.md) | 测试 4 维度参考（共十八轮）：后端变更 / 数据迁移·安装器·打包·沙箱回退 / 用户上传文件名·迁移脚本 / SPA 实时部署 / 多账户会话隔离 / BYOK 多用户密钥代理 / 流式续答 / fake-indexeddb 隔离测试 / 端到端测试·部署·冒烟编排 / 后端行为级缺陷专项测试（七类潜伏缺陷）/ 归档路由响应分支覆盖 + 静默缺陷回归 / 规范→测试派生链（前端静态守卫泛化）/ IDB 响应式代理剥离 / 后端静态守卫扩展（BR-089~092）/ process_cleanup_safe（BR-093）/ 沙箱跨进程 localhost 拦截与进程内冒烟 / 受保护接口鉴权封装 + 依赖 store 卫生（各轮均含：成功步骤 / 不确定性失败点 / 可抽象流程与判断 / 适用与不适用） |
| [测试模式（复盘提炼）](references/testing-patterns.md) | 持久化层 / 系统清理 / Async 可靠性 / 配置一致性 / 热更新 / 降级 / 目录结构 / v3 媒体生成 / v2 导航栏 / 端到端测试·部署·冒烟编排 / 归档路由响应分支覆盖（配置驱动，零硬编码）共 11 个模式 |
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
| [references/protocols.md](references/protocols.md) | 前置检查 / 测试用例同步 / 失败分类 / 服务管理 / 搜索交叉验证 共 5 个协议 + Flake 隔离协议 + 导航栏改造复盘 + 批量编译复盘 |
| [references/testing-process-review.md](references/testing-process-review.md) | 测试 4 维度参考（共十八轮）：后端变更 / 数据迁移·安装器·打包·沙箱回退 / 用户上传文件名·迁移脚本 / SPA 实时部署 / 多账户会话隔离 / BYOK 多用户密钥代理 / 流式续答 / fake-indexeddb 隔离测试 / 端到端测试·部署·冒烟编排 / 后端行为级缺陷专项测试 / 归档路由响应分支覆盖 / 规范→测试派生链 / IDB 响应式代理剥离 / 后端静态守卫扩展 / process_cleanup_safe / 沙箱跨进程 localhost 拦截与进程内冒烟 / 受保护接口鉴权封装 + 依赖 store 卫生 |
| [references/tauri-desktop-testing.md](references/tauri-desktop-testing.md) | Tauri 2.x 桌面应用测试（复盘提炼） |
| [references/changelog.md](references/changelog.md) | 版本历史（完整记录） |

## 适配新项目

仅需修改 config.yaml，按需启用配置项（详细参数见对应 references 文档）：

**基础配置**：service.frontend_url / service.api_url / navigation.tab_selector / navigation.pages / button_discovery.button_selectors / api_tests.endpoints / build.script_path / startup.script_path / button_discovery.destructive_button_texts

**增量测试与覆盖配置**（详见 [references/testing-process-review.md](references/testing-process-review.md)，基于"上下文记忆治理"后端模块复盘）：scope.modified_content.enabled / scope.modified_content.changed_paths / test_coverage.endpoint_coverage_check.enabled / endpoint_autodiscovery.enabled / endpoint_autodiscovery.routes_dir / endpoint_autodiscovery.method_match

**复盘提炼配置**（详见 [references/testing-patterns.md](references/testing-patterns.md)）：persistence_tests.endpoints / encoding_tests.check_pages / dangerous_action_tests.test_pages / service_lifecycle.start_backend / cleanup.temp_files_pattern / powershell_constraints.blocked_commands / route_registration_check.backend_route_directory / type_sync_check.backend_types_path / cors_bypass.strategy / headless_crash_guard.required_launch_args / powershell_compatibility.forbidden_syntaxes / encoding_safety_enhanced.check_extensions / scroll_container_tests.test_pages / spa_navigation_tests.test_routes / update_check_tests.test_pages / build_artifact_verification.serving_endpoint_template / browser_automation_fallback.chain / nav_dual_mode_tests.toggle_selector / icon_theme_tests.icon_selectors / powershell_string_verification.forbidden_patterns / async_reliability_tests.timeout_protection / verification.config_consistency_check / verification.hot_update_verification / verification.degradation_verification / destructive_buttons

**Tauri 桌面应用配置**（详见 [references/tauri-desktop-testing.md](references/tauri-desktop-testing.md)）：tauri.enabled / tauri.exe_name / tauri.src_tauri_dir / tauri.build_script_path / spa.source_dirs / spa.output_dir / health_check.endpoint / invoke.commands / invoke.permissions / invoke.url_patterns / disk_space.debug_min_gb / console_log.prefixes

**编码规范测试配置**（详见 [references/testing-patterns.md](references/testing-patterns.md)）：control_layering_tests.toggle_selector / third_party_error_guard_tests.test_libraries / parallel_loading_tests.resource_patterns / timeout_chain_tests.layer_order / folding_panel_event_tests.panel_selector / media_generation_tests.external_api_contract.test_endpoints / media_generation_tests.timeout_tier_verification.expected_tiers / media_generation_tests.archive_frontmatter_check.archive_dir / media_generation_tests.long_task_state_machine.test_views / media_generation_tests.external_api_unavailable.intercepted_endpoints / powershell_long_process.long_running_commands（与 CODING-056/057/059/060/061/063/064/065 编码规范对齐）

**打包与用户数据测试配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第二轮复盘，对应 CODING-PACKAGING-USERDATA / BR-068）：packaging_tests.installer_script / packaging_tests.program_files_flags / packaging_tests.exclude_user_data / packaging_tests.user_data_patterns / data_dir_tests.data_dir_funcs / data_dir_tests.expected_anchor / data_dir_tests.fallback_anchors / data_dir_tests.expected_pattern / data_dir_tests.verify_filesystem_write / user_data_isolation_tests.isolation_resources / user_data_isolation_tests.malicious_ids / user_data_isolation_tests.expect_status

**后端逻辑单元与迁移脚本测试配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第四轮复盘，对应 CODING-USER-UPLOAD-FILENAME / CODING-MIGRATION-SAFETY / BR-069 / BR-070）：backend_logic_unit_test.enabled / backend_logic_unit_test.runner_path / backend_logic_unit_test.test_file / backend_logic_unit_test.cwd / backend_logic_unit_test.fail_patterns / backend_logic_unit_test.pass_patterns / migration_script_e2e.enabled / migration_script_e2e.script_path / migration_script_e2e.runtime / migration_script_e2e.target_arg / migration_script_e2e.apply_flag / migration_script_e2e.temp_vault_dir / migration_script_e2e.setup_command / migration_script_e2e.verify_command / migration_script_e2e.cleanup_temp

**SPA 实时部署验证配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第五轮复盘 / 第十九轮 handler 补齐，对应 CODING-SPA-LIVE-DEPLOY / CODING-DEPLOY-VERIFY-DISK / BR-071 / BR-096 / 前端 FR-068）：spa_live_deploy_check.enabled / spa_live_deploy_check.live_base_dir / spa_live_deploy_check.live_dir_pattern / spa_live_deploy_check.legacy_dir / spa_live_deploy_check.complete_marker / spa_live_deploy_check.asset_prefix / spa_live_deploy_check.malicious_paths / spa_live_deploy_check.restart_required / spa_live_deploy_check.verify_via_disk / spa_live_deploy_check.required_ports

**多账户会话隔离验证配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第六轮复盘，对应 CODING-SESSION-ISOLATION / 前端 FR-069）：cross_account_session_check.enabled / cross_account_session_check.conversation_store_path / cross_account_session_check.owner_field / cross_account_session_check.session_state_refs / cross_account_session_check.auth_watch_signal / cross_account_session_check.persist_reuse_owner_check / cross_account_session_check.malicious_owner_ids / cross_account_session_check.require_reset_on_auth

**BYOK 多用户密钥代理验证配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第七轮复盘，对应 CODING-BYOK / 前端 FR-070 / 后端 BR-072）：byok_per_user_override.enabled / byok_per_user_override.user_config_service / byok_per_user_override.user_config_namespaces / byok_per_user_override.override_fields / byok_per_user_override.secret_fields / byok_per_user_override.require_key_fields / byok_per_user_override.override_func / byok_per_user_override.empty_override_falls_back

**流式回答增量持久化与续答验证配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第八轮复盘，对应 CODING-STREAMING-RESUME / 前端 FR-071）：streaming_resume_check.enabled / streaming_resume_check.streaming_store_path / streaming_resume_check.persist_debounce_ms / streaming_resume_check.last_active_key / streaming_resume_check.streaming_status / streaming_resume_check.no_abort_on_unmount / streaming_resume_check.skip_when_loading

**前端隔离测试纪律配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第九轮复盘，对应 chatDb + fake-indexeddb）：indexeddb_test_isolation.enabled / indexeddb_test_isolation.namespace_prefixes / indexeddb_test_isolation.forbidden_patterns / indexeddb_test_isolation.flush_rounds

**IndexedDB 写入前剥离响应式代理静态守卫配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第十四轮复盘，对应 FR-081 / CODING-IDB-REACTIVE-CLONE）：idb_reactive_clone_check.enabled / idb_reactive_clone_check.scan_dirs / idb_reactive_clone_check.file_glob / idb_reactive_clone_check.scan_patterns / idb_reactive_clone_check.reactive_indicators / idb_reactive_clone_check.reactive_arg_regex / idb_reactive_clone_check.safe_clone_indicators / idb_reactive_clone_check.forbidden_unsafe_patterns / idb_reactive_clone_check.scan_window_lines / idb_reactive_clone_check.severity_missing_clone / idb_reactive_clone_check.severity_unsafe / idb_reactive_clone_check.rule_ref

**前端编码标准静态守卫配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第十三轮复盘 / 第十九轮派生，对应 FR-077~FR-080 / FR-084 / FR-086~FR-088 / CODING-EDIT-RESEND / CODING-STREAMING-AUTOSCROLL / CODING-BUTTON-STYLE-CONSISTENCY / CODING-EDITBOX-WIDTH / CODING-AUTH-REQUEST-FETCH / CODING-PERSISTENT-COMPONENT / CODING-MEDIA-OBJECT-URL / CODING-AUDIO-PLAYBACK-RELIABILITY）：frontend_review_static_check.enabled / frontend_review_static_check.scan_dirs / frontend_review_static_check.file_glob / frontend_review_static_check.groups[name, forbidden_patterns, required_patterns, message, rule_ref, severity, regex]（内置 edit_resend_pair / autoscroll_double_rAF / button_style_pair / editbox_width_fill 四组，覆盖编辑重发配对 / autoscroll 双 rAF / 成对按钮样式 / 编辑框撑满；FR-084 auth_fetch_wrapped 守受保护端点禁裸 fetch；第十九轮新增 FR-086~FR-088 三组派生 persistent_component_visible_watch / object_url_revoked / audio_autoplay_distinguished，覆盖常驻组件生命周期隔离 / ObjectURL 生命周期 / 音频播放可靠性；新增前端规范只需加一组，零硬编码）

**前端编码标准静态守卫新增 auth_fetch_wrapped 组**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第十八轮复盘，对应 FR-084 / BR-094 / CODING-AUTH-REQUEST-FETCH）：`frontend_review_static_check.groups` 新增 `auth_fetch_wrapped` 组（forbidden_patterns 命中裸 `fetch('/api/config')` / `fetch('/api/ai/config')` 即违规——受保护端点须统一经带鉴权封装 apiFetch 调用，裸 fetch 缺 Authorization 头命中即 401 静默失效；required_patterns 守护 apiFetch 鉴权封装不被重构误删；severity:error 级阻断），无需改动引擎，纯配置即可生效

**依赖 store 卫生静态守卫配置**（详见 [references/testing-process-review.md](references/testing-process-review.md) 第十八轮复盘，对应 FR-085 / BR-095 / CODING-PNPM-STORE-HYGIENE）：dependency_store_hygiene_check.enabled / dependency_store_hygiene_check.store_dir_key / dependency_store_hygiene_check.canonical_store_dir / dependency_store_hygiene_check.forbidden_store_dirs / dependency_store_hygiene_check.scan_root / dependency_store_hygiene_check.assert_npmrc_store_dir / dependency_store_hygiene_check.severity / dependency_store_hygiene_check.rule_ref（断言全局 ~/.npmrc 显式声明收敛键 store-dir，避免 pnpm 主目录探测被 safe-delete 沙箱钩子打断退化为盘根散落 .pnpm-store 污染工作区；扫描 scan_root 检测与 canonical_store_dir 不一致的孤儿 .pnpm-store；默认 enabled:false，CI 前置可升 error 级，全部路径/键名/目录名来自配置零硬编码）

**一键启用模板**：针对本仓库（karpathy-wiki）真实路径与字段的 *已启用* 示例见 [examples/config.enabled.example.yaml](examples/config.enabled.example.yaml)（涵盖上述步骤类型：cross_account_session_check / byok_per_user_override / streaming_resume_check / indexeddb_test_isolation / idb_reactive_clone_check，全部 `enabled: true`，字段名取自实际源码）。复制其中对应块到 config.yaml 即可直接使用，无需再逐项推断路径。

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
- **打包（SEA/Electron/Tauri）/ 安装器 / 用户数据目录解析改动**（验证安装器防覆盖 + 数据目录落点 + 用户数据隔离，对应 CODING-PACKAGING-USERDATA / BR-068）
- **后端落盘前纯逻辑验证（无浏览器）**：用 `backend_logic_unit_test` 直接实例化 service 做文件名清洗 / 内部前缀剥离 / 路径穿越二次校验等单元断言，无需启动服务或浏览器，对应 CODING-USER-UPLOAD-FILENAME / BR-069
- **数据迁移 / 修复脚本验证**：用 `migration_script_e2e` 对临时 vault 真实 `--apply`，验证既不破坏原数据又能正确改写；脚本默认 dry-run 安全，对应 CODING-MIGRATION-SAFETY / BR-070
- **沙箱无浏览器 / 无 PyYAML 环境的测试回退**（回退 vitest 单元 + Fastify app.inject + 真实 API HTTP 集成，浏览器 E2E 降级）
- **SPA 实时部署解析改动（后端 resolveSpaRoot / resolveSpaAsset + 部署脚本 _deploy_live.mjs）**：用 `spa_live_deploy_check`（`verify_via_disk: true`）读磁盘枚举 public_live_* 取 mtime 最新 + 校验 .deploy-complete 与 assets/index-*.js，取代两次 HTTP 比对（目录高频轮转下会误判）；restart_required 时校验后端端口监听（部署后须重启后端使 spaRoot 重新解析）；对应 CODING-SPA-LIVE-DEPLOY / CODING-DEPLOY-VERIFY-DISK / BR-071 / BR-096 / 前端 FR-068
- **safe-delete 沙箱钩子约束下的清理 / 部署**：钩子 fail-closed（拦截 overwrite/rename-overwrite/unlink 已存在文件、rm 完全被拦），唯一放行的是新建目录整目录写入与移动到【全新(不存在)路径】；统一走「写新目录 → 移动/重建」而非原地 rm/覆盖，对应第五轮复盘
- **多账户会话隔离改动（Pinia 会话 store + 问答页 auth watch + 持久化层）**：用 `cross_account_session_check` 断言账户切换/登出触发 resetSession（currentConversationId+scopedOwnerId 作废、列表清空）、persistConversation 复用 id 前以 IndexedDB 实际记录校验归属（他人记录绝不覆盖、冲突改用全新 uuid）、filterByOwner 严格按 ownerId 隔离；跨账户须用真实登出/切换 E2E 而非 store 直接 setUser；对应 CODING-SESSION-ISOLATION / 前端 FR-069
- **BYOK 多用户密钥代理改动（前端 userConfig.ts + Config.vue + Query.vue + 后端 applyPerRequestOverride / routes/query.ts）**：用 `byok_per_user_override_check` 断言每用户配置按 userId 命名空间隔离、密钥仅经请求体下发（后端不落盘/不回显/不记日志）、缺必需密钥返回 400 不回落服务端共享、覆盖为纯函数且空工具配置回退服务端共享；对应 CODING-BYOK / 前端 FR-070 / 后端 BR-072
- **流式回答增量持久化与续答改动（stores/query.ts streamingAnswer + Query.vue onBeforeUnmount/maybeResumeOnLoad + types.ts status）**：用 `streaming_resume_check` 断言流式分片增量防抖落盘、卸载不 abort 在途流、重载仅对 streaming 末条续答（interrupted/error 不续）；对应 CODING-STREAMING-RESUME / 前端 FR-071
- **前端隔离测试编写（chatDb + fake-indexeddb）**：用 `indexeddb_test_isolation_check` 断言隔离测试用唯一 userId 命名空间、禁用 beforeEach deleteDatabase（避免 onblocked/超时/跨用例泄漏）、fake-indexeddb 异步落盘断言多轮 flush；对应第九轮复盘
- **前端编码标准静态守卫改动（编辑重发 / 流式自动滚动 / 成对按钮样式 / 编辑框撑满等 UI 规范）**：用 `frontend_review_static_check` 配置化扫描前端源码 forbidden_patterns（命中即违规）+ required_patterns（保护性代码被删即违规），把 FR-077~FR-080 的"静态守卫"判断逻辑落地；新增前端规范只需加一组配置，零硬编码，对应第十三轮复盘 / CODING-EDIT-RESEND / CODING-STREAMING-AUTOSCROLL / CODING-BUTTON-STYLE-CONSISTENCY / CODING-EDITBOX-WIDTH
- **IndexedDB 写入前剥离 Vue/Pinia 响应式代理改动（`services/*UserConfig*.ts` / `*store*.ts` 经 `dbPut`/`saveUserConfig`/`idbPut`/`store.put` 写入 IndexedDB）**：用 `idb_reactive_clone_check` 静态扫描写入点，核对写入值若源自 store state ref / `reactive()` 是否在写入前整树深拷贝（`clone(x)` / `JSON.parse(JSON.stringify(x))`），并判 `toRaw(` 伪剥离（仅剥顶层）违规；直传 reactive 代理会导致 `[object Array] could not be cloned` 静默丢配置；对应第十四轮复盘 / FR-081 / CODING-IDB-REACTIVE-CLONE
- **归档路由（按 threadId + messageIndex + ts 派生存储键）响应分支覆盖改动**：用 `route_response_branch_coverage` 逐分支断言主路径 200 / 回退 404 / 非法 threadId 400 / 非整数 messageIndex 400 / 缺失 messageIndex 400 / 非法 ts 200 / 空内容 400，并校验 200 响应含必需字段（content/refs 等）；把"静默缺陷回归"判断逻辑落地，对应第十二轮复盘 / 前端 FR-076 能力门控同步
- **受保护接口统一经鉴权封装调用改动（前端 utils/apiBase.ts apiFetch + 后端 routes/*.ts requireAuth 守卫）**：用 `frontend_review_static_check` 的 `auth_fetch_wrapped` 组断言后端 requireAuth 受保护端点（/api/config、/api/ai/config）无裸 fetch 不带 Authorization 头（命中即 401 静默失效）、且 apiFetch 鉴权封装存在未被误删；对应第十八轮复盘 / FR-084 / BR-094 / CODING-AUTH-REQUEST-FETCH
- **pnpm store 卫生 / 依赖安装环境收敛改动（CI 前置 / 构建脚本 / 全局 ~/.npmrc / 仓库或盘根）**：用 `dependency_store_hygiene_check` 断言全局 ~/.npmrc 显式声明 store-dir 收敛键、scan_root 下无与统一 store 不一致的孤儿 .pnpm-store；避免 safe-delete 沙箱钩子打断 pnpm 主目录探测后退化为盘根散落污染工作区；对应第十八轮复盘 / FR-085 / BR-095 / CODING-PNPM-STORE-HYGIENE
- **常驻组件生命周期隔离改动（v-show 后台播放 / 账户态切换）**：用 `frontend_review_static_check` 的 `persistent_component_visible_watch` 组守护 `watch(visible)` 不被误删（FR-086）；对应第十九轮复盘 / CODING-PERSISTENT-COMPONENT
- **TTS / 媒体 ObjectURL 使用改动**：用 `frontend_review_static_check` 的 `object_url_revoked` 组守护 `revokeObjectURL` 不被误删（FR-087）；对应第十九轮复盘 / CODING-MEDIA-OBJECT-URL
- **音频播放可靠性改动**：用 `frontend_review_static_check` 的 `audio_autoplay_distinguished` 组守护「语音合成失败」与「播放被浏览器拦截」两类文案分离不被合并（FR-088）；对应第十九轮复盘 / CODING-AUDIO-PLAYBACK-RELIABILITY
- **毛玻璃 backdrop-filter 包含块陷阱改动（多主题 SPA 滚动容器内嵌 position:fixed 悬浮元素）**：用 `frontend_review_static_check` 的 `backdrop_filter_fixed_ancestor` 组守护 `Teleport` 逃逸写法不被误删（FR-089）；对应第二十轮复盘 / CODING-BACKDROP-FILTER-CB
- **双主题 --m-* 变量架构改动**：用 `config_driven_frontend` 透镜扫描主题相关字面量与 `theme ===` 组件分支（FR-090，与 FR-035 协同），不另起静态组；对应第二十轮复盘 / CODING-DUAL-THEME-VAR

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
- **纯前端 UI 动画/交互变更**（落点/安装器验证不适用，应走既有 Playwright 浏览器测试）
- **服务端容器部署（volume 挂载）**（用户数据目录锚点非 LOCALAPPDATA，T2/T5 判定需按部署模型调整）
- **无后端 service / 无迁移脚本的纯前端或纯文档改动**：`backend_logic_unit_test` / `migration_script_e2e` 无对应测试目标，应沿用前几轮流程或既有浏览器测试阶段
- **无可静态识别"保护性代码"的前端规范（纯运行时行为、无特征字符串）**：`frontend_review_static_check` 的 required_patterns 无法可靠匹配，应改用浏览器 E2E（如 button_discovery / theme_switch）或运行时断言验证，而非静态守卫
- **单分支无歧义路由（所有非法输入已被框架/中间件统一拦截为 4xx 且无需逐分支断言返回语义）**：`route_response_branch_coverage` 的分支矩阵价值有限，沿用 `api_check` / `path_traversal_test` 即可；仅当路由内部对"合法请求的不同业务结果"（主路径 vs 回退 vs 空内容）有差异化状态码语义时才有必要

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
- **沙箱无浏览器/无 PyYAML 导致 E2E 与部分脚本无法运行**：第 40 条，回退 vitest 单元 + Fastify app.inject + 真实 API HTTP 集成，浏览器 E2E 降级

## Version History

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v2.17.0 | 2026-08-11 | **前端三项编码规范静态守卫派生 + 部署产物磁盘验证 handler 补齐 + 测试流程第十九轮复盘补充**：基于「聆听页 v-show 常驻后台播放（FR-086 常驻组件生命周期隔离）/ TTS ObjectURL 常驻泄漏（FR-087）/ 两类音频播放失败混报（FR-088）/ 部署目录高频轮转下两次 HTTP 校验误判（BR-096）」四类问题复盘，落地：(1) `frontend_review_static_check` 纯配置新增三组 derived 守卫——`persistent_component_visible_watch`（required_patterns 守护 watch(visible) 不被误删，FR-086）、`object_url_revoked`（守护 revokeObjectURL 不被误删，FR-087）、`audio_autoplay_distinguished`（守护「语音合成失败」与「播放被浏览器拦截」两类文案分离不被合并，FR-088），severity error/warn 可配、无需改引擎；(2) `spa_live_deploy_check` 此前在 v2.6.0 仅写入配置块但 `_step_engine.py` 未注册 handler（死配置），本轮注册并实现 `_handle_spa_live_deploy_check`，新增 `verify_via_disk: true` 取代旧版两次 HTTP 比对（spaRoot 启动只解析一次，目录高频轮转下两次 HTTP 会读到不同根而误判），改为读磁盘枚举 public_live_* 取 mtime 最新 + 校验 .deploy-complete 与 assets/index-*.js + 重启后端口监听校验。_step_engine.py 编译校验通过。testing-process-review.md 追加第十九轮 4 维度复盘（with Sequential Thinking：成功步骤 / 不确定性与失败点 / 可抽象固定流程与判断 / 适用与不适用）。defaults.yaml / config.yaml / examples/config.enabled.example.yaml 同步（3 个前端组 + spa_live_deploy_check.verify_via_disk: true；examples 新增启用态 spa_live_deploy_check 段）。对应 CODING-PERSISTENT-COMPONENT / CODING-MEDIA-OBJECT-URL / CODING-AUDIO-PLAYBACK-RELIABILITY / CODING-DEPLOY-VERIFY-DISK / CODING-SPA-LIVE-DEPLOY / FR-086~FR-088 / BR-096 / BR-071 / FR-068。 |
| v2.18.0 | 2026-08-12 | **毛玻璃 backdrop-filter 包含块陷阱派生守卫 + 双主题变量架构复用 config-driven 透镜 + 测试流程第二十轮复盘补充**：基于「移动端双主题切换（浅白风/毛玻璃）+ 滚动回顶 FAB 主题间行为不一致 / 双主题 --m-* 变量架构」两类问题复盘，落地：(1) `frontend_review_static_check` 纯配置新增一组 derived 守卫 `backdrop_filter_fixed_ancestor`（required_patterns 守护 `Teleport` 逃逸写法不被重构误删，FR-089 / CODING-BACKDROP-FILTER-CB；severity error 可配、零引擎改动）；(2) 双主题变量架构（FR-090 / CODING-DUAL-THEME-VAR）属"主题字面量 / theme 分支"模式，复用既有 `config_driven_frontend` 透镜（CODING-CONFIG-DRIVEN）覆盖，不另起静态组（避免与 FR-035 主题色变量映射重复）；运行时主题状态单例性由浏览器 E2E（theme_switch）验证。testing-process-review.md 追加第二十轮 4 维度复盘（with Sequential Thinking：成功步骤 / 不确定性与失败点 / 可抽象固定流程与判断 / 适用与不适用）。defaults.yaml / config.yaml / examples/config.enabled.example.yaml 同步新增 `backdrop_filter_fixed_ancestor` 组。四技能闭环同步：wiki-code-dev（CODING-BACKDROP-FILTER-CB / CODING-DUAL-THEME-VAR + 路由表 + 参数段）、wiki-frontend-code-review（FR-089/FR-090 + 参数段 + 规则文件 + skill-loader 三表）、wiki-backend-code-review（BR-088-4 跨技能路由）、wiki-auto-testing（本组）。对应 CODING-BACKDROP-FILTER-CB / CODING-DUAL-THEME-VAR / FR-089 / FR-090 / BR-088-4。 |
| v2.16.0 | 2026-08-11 | **受保护接口鉴权封装守卫 + 依赖 store 卫生守卫 + 测试流程第十八轮复盘补充**：基于「401 事故（config.auth.enabled 收紧 requireAuth 后 18 处裸 fetch 缺 token → 受保护端点静默 401 失效、AI 伙伴选项消失、前端报"加载配置失败：HTTP 401"）」与「pnpm store 散落（safe-delete 沙箱钩子打断 pnpm 主目录探测 → 退化为盘根 .pnpm-store 污染工作区且 node_modules 解析不到统一 store）」两类事故复盘，落地两项新静态守卫：(1) `frontend_review_static_check` 纯配置新增 `auth_fetch_wrapped` 组（forbidden_patterns 命中裸 `fetch('/api/config')`/`fetch('/api/ai/config')` 即违规——受保护端点须统一经带鉴权封装 apiFetch、裸 fetch 缺 Authorization 头命中即 401 静默失效；required_patterns 守护 apiFetch 封装不被重构误删；severity:error 级阻断，无需改引擎）；(2) 新增动态引擎步骤类型 `dependency_store_hygiene_check`（断言全局 ~/.npmrc 显式声明 store-dir 收敛键 + 扫描 scan_root 检测与 canonical_store_dir 不一致的孤儿 .pnpm-store，剪枝 node_modules/.git/dist/build/public 等重目录避免深遍历；默认 warn、CI 前置可升 error）。_step_engine.py 注册并实现该 handler（registry 模式，step 可覆盖参数）。testing-process-review.md 追加第十八轮 4 维度复盘（with Sequential Thinking：成功步骤 / 不确定性与失败点 / 可抽象固定流程与判断 / 适用与不适用）。defaults.yaml / config.yaml / examples/config.enabled.example.yaml 同步新增（auth_fetch_wrapped 组 + dependency_store_hygiene_check 零硬编码配置块）。对应 CODING-AUTH-REQUEST-FETCH / FR-084 / BR-094 / CODING-PNPM-STORE-HYGIENE / FR-085 / BR-095。 |
| v2.15.0 | 2026-08-11 | **冒烟验证策略配置化（smoke_strategy）+ 测试流程第十七轮复盘补充**：基于「沙箱跨进程 localhost TCP 被拦截 + app.inject 全量 app 响应挂起」经验，新增 `smoke_strategy` 配置块（process_internal_inject 默认：import buildApp() → app.ready() + 最小 SPA-static app inject 200；tcp_opt_in 真实构建机启用、沙箱默认关闭；contract_assertions_on_real_host 标注契约级断言须在真实机构建机重跑）；testing-process-review.md 追加第十七轮 4 维度复盘（沙箱网络不可信 / inject 挂起≠路由缺陷 / 进程内冒烟优先 / 契约断言位置外置）。对应第十轮端到端编排 / 第十五轮 CODING-RESPONSE-HOOK-SAFE。 |
| v2.13.0 | 2026-08-10 | **后端编码标准静态守卫扩展（BR-089~092）+ 测试流程第十五轮复盘补充**：基于「从历史已解决问题系统性提炼编码规范并同步到测试」经验，在已有 `backend_review_static_check` 步骤类型（registry 模式，零硬编码）的 groups[] 中**新增 4 组**配置驱动的静态守卫——`route_return_completeness`（reply.code(/reply.status( 须逐分支显式 return/throw，漏 return 致 Fastify 双发响应）、`response_hook_safe`（全局 onSend/onResponse/setSerializer/contentTypeParser 须 try/catch fail-open 且无 await 重计算）、`compression_default_off`（压缩中间件须默认关闭且条件注册、阈值来自配置）、`user_store_init`（loadUsers/loadConfig/JSON.parse 须区分 not-found 与 corrupt 并兜底回退默认 + 备份 + log.warn）；全部模式来自配置、error/warn 可配、新增后端规范只需在 config 加一组，零硬编码业务值。testing-process-review.md 追加第十五轮 4 维度复盘（with Sequential Thinking 标注：成功步骤 / 不确定性与失败点 / 可抽象固定流程与判断逻辑 / 适用与不适用场景，含"从编码规范派生静态守卫""配置化步骤类型泛化""safe-delete 沙箱对静态守卫的影响"三小节）。defaults.yaml / config.yaml / examples/config.enabled.example.yaml 同步新增 4 组零硬编码 groups。对应 CODING-ROUTE-RETURN-COMPLETENESS / CODING-RESPONSE-HOOK-SAFE / CODING-COMPRESSION-DEFAULT-OFF / CODING-USER-STORE-INIT / 后端 BR-089~092。 |
| v2.14.0 | 2026-08-11 | **后端编码标准静态守卫扩展（BR-093 process_cleanup_safe）+ 测试流程第十六轮复盘补充**：基于「启动脚本清理旧进程 taskkill stderr 触发 NativeCommandError 中止脚本」复盘，在 `backend_review_static_check` 步骤类型 groups[] 中**新增 1 组**配置驱动的静态守卫——`process_cleanup_safe`（forbidden 模式 `taskkill` 命中即提示复核：端口清理主键须改 Stop-Process -Force + try/catch 非致命、残留兜底须 2>&1|Out-Null + try/catch 吞 stderr；与 BR-093 / CODING-PS-PROCESS-CLEANUP 对齐）。全部模式来自配置、error/warn 可配、新增后端规范只需在 config 加一组，零硬编码业务值。defaults.yaml / config.yaml / examples/config.enabled.example.yaml 同步新增该组（并在启用说明中标注须将 scan_dirs 包含脚本目录、file_glob 放宽到 *.ps1）。对应 wiki-code-dev PS-6.1 / CODING-PS-PROCESS-CLEANUP / 后端 BR-093。 |
| v2.10.0 | 2026-08-08 | **归档路由响应分支覆盖测试复盘补充**：基于「归档路由重构（7 条规范：文件名碰撞 / 非法 ts→RangeError / 非整数 messageIndex→undefined 访问 / refs 换行破坏 wikilink / 空内容 no-op 落盘 / 依赖服务端会话 100% 误报过期 / 前端门控漂移）」经验，新增 1 个动态引擎步骤类型（`route_response_branch_coverage`：配置化逐分支断言被测路由在各请求参数组合下的返回状态码——主路径 200 / 回退 404 / 非法 threadId 400 / 非整数 messageIndex 400 / 缺失 messageIndex 400 / 非法 ts 200 / 空内容 400——并校验 200 响应含必需字段，把"响应分支覆盖 + 静默缺陷回归"判断逻辑落地）；testing-process-review.md 追加第十二轮 4 维度复盘（成功步骤 / 不确定性失败点 / 可抽象流程与判断 / 适用与不适用）；testing-patterns.md 追加「归档路由响应分支覆盖」通用模式；defaults.yaml / config.yaml / examples/config.enabled.example.yaml 新增 `route_response_branch_coverage` 零硬编码配置块（route_name / method / branch_cases[name,params,expected_status,required_fields,description]）。对应 CODING-GENERATED-FILENAME-UNIQUENESS / CODING-WIKILINK-SANITIZATION / CODING-EMPTY-CONTENT-REJECTION / CODING-INTEGER-INDEX-VALIDATION / CODING-SAFE-CLIENT-DATE-PARSE / CODING-PERSISTENCE-CLIENT-CONTENT-DECOUPLING / 前端 FR-076 能力门控同步。 |
| v2.11.0 | 2026-08-08 | **前端编码标准静态守卫 + 测试流程四维度复盘补充**：基于本对话「从历史已解决问题系统性提炼编码规范并同步到测试」经验，新增 1 个**更泛化**的动态引擎步骤类型 `frontend_review_static_check`（在 backend_review_static_check 的 forbidden_patterns 基础上新增 required_patterns「存在性」维度——整个扫描集完全缺失即违规，守护保护性代码被重构误删）；内置 FR-077~FR-080 四组（编辑重发配对 removeMessagesFrom+submitQuestion / autoscroll 双 rAF+stickToBottom / 成对按钮 .edit-btn.confirm+.cancel / 编辑框撑满 .msg-content-wrapper+.msg-edit），新增前端规范只需在 config 加一组、零硬编码；_step_engine.py 注册并实现该 handler（registry 模式，step 可覆盖参数）。testing-process-review.md 追加第十三轮 4 维度复盘（测试流程：成功步骤 / 不确定性与失败点 / 可抽象流程与判断 / 适用与不适用，含"从编码规范派生测试""flake 型 typecheck 诊断""配置化步骤类型泛化"三小节）。defaults.yaml / config.yaml 新增 `frontend_review_static_check` 零硬编码配置块（scan_dirs / file_glob / groups[name,forbidden_patterns,required_patterns,message,rule_ref,severity,regex]）。对应 CODING-EDIT-RESEND / CODING-STREAMING-AUTOSCROLL / CODING-BUTTON-STYLE-CONSISTENCY / CODING-EDITBOX-WIDTH / 前端 FR-077~FR-080 / 后端 BR-087。 |
| v2.12.0 | 2026-08-08 | **IndexedDB 写入前剥离响应式代理静态守卫 + 测试流程第十四轮复盘补充**：基于「userConfig.ts 的 saveUserConfig 直传 Vue/Pinia reactive 代理 → IndexedDB `structuredClone` 抛 `[object Array] could not be cloned`、写失败被 try/catch 仅 warn 掩盖 → 四类本地配置（AI/搜索/工具/输入框）静默丢失」经验，新增 1 个动态引擎步骤类型 `idb_reactive_clone_check`（配置化扫描前端源码 IDB 写入点 dbPut/saveUserConfig/idbPut/store.put/transactions.add，核对写入值若源自 store state ref / reactive() 是否在写入前整树深拷贝 JSON.parse(JSON.stringify(x))/clone(x)；判 toRaw( 伪剥离违规（R-2）、structuredClone(reactiveObj) 由 R-1 分支覆盖；直传 reactive 代理静默丢配置（R-1），error 级阻断）；_step_engine.py 注册并实现该 handler（registry 模式，step 可覆盖参数）。testing-process-review.md 追加第十四轮 4 维度复盘（测试流程：成功步骤 / 不确定性与失败点 / 可抽象流程与判断 / 适用与不适用，含"从编码规范派生静态守卫""窗口上下文启发式""配置化步骤类型泛化"三小节）。defaults.yaml / config.yaml / examples 新增 `idb_reactive_clone_check` 零硬编码配置块（scan_dirs / file_glob / scan_patterns / reactive_indicators / reactive_arg_regex / safe_clone_indicators / forbidden_unsafe_patterns / scan_window_lines / severity_missing_clone / severity_unsafe / rule_ref）。对应 CODING-IDB-REACTIVE-CLONE / 前端 FR-081 / 后端 BR-088（review-scope）。 |
| v2.9.0 | 2026-08-07 | **后端行为级缺陷专项测试复盘补充**：基于「SSML prosody 注入防护 / 子进程异步当同步 / 关键写静默吞错 / 数据文件损坏未区分 / request.method 类型绕过 / 硬编码超时 / 冗余探测」七类后端潜伏缺陷的测试经验，新增 1 个动态引擎步骤类型（`backend_review_static_check`：配置化 grep 后端源码 forbid 模式组，error 级阻断 / warn 级标记，把"静态守卫"判断逻辑落地）；testing-process-review.md 追加第十一轮 4 维度复盘（成功步骤 / 不确定性失败点 / 可抽象流程与判断 / 适用与不适用）；defaults.yaml / config.yaml 新增 `backend_review_static_check` 零硬编码配置块（scan_dirs / file_glob / groups[name,patterns,message,rule_ref,severity,regex]）；步骤类型表追加 1 行。对应 BR-074~080 / CODING-SSML-INJECTION / CODING-CHILD-PROCESS-SYNC / CODING-CRITICAL-WRITE-NO-SWALLOW / CODING-FILE-CORRUPTION-GUARD / CODING-TYPE-SAFE-NO-ANY / CODING-CONFIG-TIMEOUT / CODING-NO-REDUNDANT-PROBE。 |
| v2.6.0 | 2026-08-06 | **SPA 实时部署解析测试复盘补充**：基于「/wiki/* 路径穿越加固 + 实时部署解析（resolveSpaRoot 选最新时间戳目录 + isDeployComplete 完整性门禁；resolveSpaAsset normalize + within-root 防穿越）+ 部署脚本 _deploy_live.mjs 写全新 public_live_<ts> 目录」与沙箱 safe-delete 钩子 fail-closed 经验，新增 1 个动态引擎步骤类型（`spa_live_deploy_check`：断言后端选最新时间戳目录 + 完整性门禁、/wiki/* within-root 防穿越、部署写全新目录不覆盖、重启后端生效）；testing-process-review.md 追加第五轮 4 维度复盘（含 safe-delete 钩子 fail-closed 工作模式：唯一放行新建目录整目录写入与移动到全新路径，清理/部署统一走「写新目录→移动/重建」）；defaults.yaml / config.yaml 新增 `spa_live_deploy_check` 零硬编码配置块；适配新项目章节追加 SPA 实时部署验证配置；适用场景追加 2 项；步骤类型表追加 1 行。对应 CODING-SPA-LIVE-DEPLOY / BR-071 / 前端 FR-068。 |
| v2.8.0 | 2026-08-07 | **端到端测试/部署/冒烟编排复盘补充**：基于「类型门禁→单测→全量→构建(全新目录)→部署(全新目录)→干净重启(杀孤儿 :3000)→冒烟(400 缺密钥不回落/200 SSE/SPA 伺服最新目录)」经验，testing-process-review.md 追加第十轮 4 维度复盘；修复版本表遗漏（补 v2.7.1/2.7.2/2.7.3 对应 BYOK/流式续答/隔离测试三轮）；衔接 CODING-TEST-ISOLATION 与 retrospective-synthesis.md。对应 spa_live_deploy_check / indexeddb_test_isolation_check / service_manage / byok_per_user_override_check。 |
| v2.7.3 | 2026-08-07 | **前端隔离测试纪律复盘补充**：新增动态引擎步骤类型 `indexeddb_test_isolation_check`（断言隔离测试用唯一 userId 命名空间、禁用 beforeEach deleteDatabase、fake-indexeddb 异步落盘断言须多轮 setTimeout(0) flush）；testing-process-review.md 追加第九轮 4 维度复盘；defaults.yaml / config.yaml 新增零硬编码配置块。对应 CODING-TEST-ISOLATION。 |
| v2.7.2 | 2026-08-07 | **流式回答增量持久化与续答复盘补充**：新增动态引擎步骤类型 `streaming_resume_check`（断言流式分片增量防抖落盘、卸载不 abort 在途流、仅 streaming 末条续答、后台流活跃时跳过）；testing-process-review.md 追加第八轮 4 维度复盘；defaults.yaml / config.yaml 新增零硬编码配置块。对应 CODING-STREAMING-RESUME / 前端 FR-071。 |
| v2.7.1 | 2026-08-07 | **BYOK 多用户密钥代理复盘补充**：新增动态引擎步骤类型 `byok_per_user_override_check`（断言每用户命名空间隔离、密钥仅请求体不落盘、缺必需密钥 400 不回落、覆盖纯函数空覆盖回退、前端仅当配置存在才下发）；testing-process-review.md 追加第七轮 4 维度复盘；defaults.yaml / config.yaml 新增零硬编码配置块。对应 CODING-BYOK / 前端 FR-070 / 后端 BR-072。 |
| v2.7.0 | 2026-08-07 | **多账户会话隔离测试复盘补充**：基于「多账户会话隔离泄漏（currentConversationId 模块级共享 ref 跨账户未 reset + scopedOwnerId 漏加 store return 死状态 + persistConversation 复用 id 未校验归属）」经验，新增 1 个动态引擎步骤类型（`cross_account_session_check`：断言账户切换/登出触发 resetSession、persistConversation 复用 id 前以 IndexedDB 实际记录校验归属、filterByOwner 严格隔离、跨账户真实登出/切换 E2E 无泄漏）；testing-process-review.md 追加第六轮 4 维度复盘；defaults.yaml / config.yaml 新增 `cross_account_session_check` 零硬编码配置块；适配新项目章节追加多账户会话隔离验证配置；适用场景追加 1 项；步骤类型表追加 1 行。对应 CODING-SESSION-ISOLATION / 前端 FR-069。 |
| v2.5.0 | 2026-08-05 | **后端逻辑单元与迁移脚本测试复盘补充**：基于「raw 文件名修复 + 走查建议优化」与沙箱 Windows 路径（Git-Bash `/c/Users` vs Windows 原生 `C:\Users` 导致 ENOENT、safe-delete 钩子拦截 `rm`）经验，新增 2 个动态引擎步骤类型（`backend_logic_unit_test` 直接实例化 service 做落盘前纯逻辑单元断言；`migration_script_e2e` 对临时 vault 真实 `--apply` 验证迁移/修复脚本）；testing-process-review.md 追加第四轮 4 维度复盘；defaults.yaml / config.yaml 新增 `backend_logic_unit_test` / `migration_script_e2e` 两个零硬编码配置块；适配新项目章节追加后端逻辑单元与迁移脚本测试配置；适用/不适用场景各追加 2 项；步骤类型表追加 2 行。对应 CODING-USER-UPLOAD-FILENAME / CODING-MIGRATION-SAFETY / BR-069 / BR-070。 |
| v2.3.0 | 2026-07-31 | **PowerShell 长时进程管道陷阱测试补充**：新增 powershell_long_process 核心配置块；新增 EPIPE 故障分类类型（epipe_error）；新增 TROUBLESHOOTING 第 39 条；配置适配章节追加 1 项配置说明。对应 CODING-059 编码规范。 |
| v2.4.0 | 2026-08-05 | **打包与用户数据测试复盘补充**：基于「安装器覆盖配置 / AppData 数据迁移 / SEA 路径解析 / clean-defaults」与沙箱无浏览器回退经验，新增 3 个动态引擎步骤类型（packaging_config_overwrite_test / data_dir_derivation_test / user_data_isolation_test）；testing-process-review.md 追加第二轮 4 维度复盘；适配新项目章节追加打包与用户数据测试配置；适用/不适用场景各追加 2-3 项；故障排查追加第 40 条（沙箱无浏览器/PyYAML 回退）。对应 CODING-PACKAGING-USERDATA / BR-068。 |
| v2.2.0 | 2026-07-31 | **v3 媒体生成工具复盘测试补充**：新增 media_generation_tests 核心配置块（5 个子段）；新增"v3 媒体生成工具测试（复盘提炼）"章节（5 个子阶段 5.15-5.19）；新增 5 个动态引擎步骤类型；适配新项目章节追加 1 项配置说明（第 43 项）；适用场景追加 5 项；不适用场景追加 3 项；故障排查追加 4 条（TROUBLESHOOTING 第 35-38 条）。对应 CODING-056/057/059/060/061/063/064/065 编码规范。 |
| v2.1.0 | 2026-07-31 | **编码规范测试流程补充**：基于控件分层、第三方库错误防护、多资源并行加载、超时阈值链式匹配、折叠面板事件冲突五项编码规范，新增 5 个核心配置块；新增 5 个测试子阶段（5.10-5.14）；新增 5 个动态引擎步骤类型；适配新项目章节追加 5 项配置说明；适用场景追加 5 项；不适用场景追加 5 项；故障排查追加 5 条（TROUBLESHOOTING 第 30-34 条）。 |
| v2.0.0 | 2026-07-22 | **Tauri 2.x 桌面应用测试复盘**：新增"Tauri 2.x 桌面应用测试（复盘提炼）"章节（含 6 阶段测试流程、invoke 权限三层验证、SPA 产物验证、阶段间 DAG 依赖关系、故障排查速查表）；新增 3 个参考文档（tauri-desktop-testing.md / spa-artifact-verification.md / invoke-permission-verification.md）；新增 templates/phase_tauri_desktop.py 测试阶段模板；config.yaml 与 defaults.yaml 新增 tauri / spa / health_check / invoke / disk_space / console_log 6 个配置块。 |

> 完整版本历史见 [references/changelog.md](references/changelog.md)
