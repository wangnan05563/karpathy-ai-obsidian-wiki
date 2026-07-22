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
| 动态引擎 | 读取 	est_plan.phases 中的步骤定义 | 灵活定制，无需改代码 |

动态引擎模式通过在 config.yaml 中定义步骤列表实现：
`yaml
test_plan:
  phases:
    basic:
      steps:
        - type: navigate
          url: "http://localhost:5173"
        - type: assert_visible
          selector: ".robot-avatar"
          name: "Avatar"
`

### 核心配置块

| 配置块 | 用途 |
|--------|------|
| working_directory | 项目根目录自动定位 |
| uild / startup | 构建/启动脚本（可设 enabled: false 跳过） |
| service | 前后端地址、端口、健康检查 |
| rowser | headless、启动参数、多视口 |
| 
avigation | 导航选择器、页面列表及期望元素 |
| utton_discovery | 按钮自动发现、排除规则、破坏性保护 |
| interactions | 主题切换、表单、标签页交互 |
| pi_tests | API 端点列表 |
| console_error_filter | 控制台错误过滤关键词 |
| 	est_plan | 测试阶段编排（可选子集或自定义步骤） |
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

## 测试流程（6 阶段）

### 阶段 1：构建
读取 uild.script_path → 执行构建 → 验证产物 index.html 存在

#### 子阶段 1.1：构建前检查（可选）
> 基于历史问题复盘提炼，针对 Windows 中文环境与 PowerShell 兼容性的源头预防。

仅在对应配置 `enabled: true` 时执行：

1. **编码安全增强检查**（`encoding_safety_enhanced.enabled: true`）：
   - 遍历 `encoding_safety_enhanced.check_extensions` 中配置的源文件扩展名
   - 对每个文件检测是否含 U+FFFD 替换字符（编码损坏标志）
   - 若 `replacement_char_threshold: 0`，发现任何 U+FFFD 即判定失败
   - 防止源文件被 GBK 写入后污染测试流程

2. **PowerShell 兼容性检查**（`powershell_compatibility.enabled: true`）：
   - 扫描测试脚本与配置文件中是否出现 `powershell_compatibility.forbidden_syntaxes`（默认 `&&` / `||`）
   - 命中禁止语法即判定失败，并提示用 `syntax_replacements` 中的替代语法
   - 防止 PowerShell 5.1 执行命令链时报 "The token '&&' is not a valid statement separator"

### 阶段 2：启动服务
读取 startup.script_path → 执行启动 → 轮询端口 → 验证 /health 返回 200

### 阶段 3：基础功能
首页加载 → 验证 title → 遍历导航 tabs → 验证各页面元素 → 截图 → 收集控制台错误

#### 子阶段 3.1：编码检测（可选）
> 基于系统清理模块前端验证复盘提炼，针对 Windows 中文环境终端编码与 Playwright 中文匹配问题。

仅在 `encoding_tests.enabled: true` 时执行：
1. 遍历 `encoding_tests.check_pages` 中配置的页面
2. 对每个 `scan_selectors` 选择器，dump DOM 文本并提取 Unicode 码点
3. 检查码点中是否含 `encoding_tests.fffd_codepoint`（默认 `0xFFFD`，即替换字符）
4. 若发现 U+FFFD：判定为编码乱码 → `screenshot_on_fail` 时截图取证
5. 通过 Unicode 码点匹配避免终端编码影响（详见 `_shared.get_dom_text_codepoints`）

#### 子阶段 3.2：路由注册验证（可选）
> 基于历史问题复盘提炼，防止新增路由文件未在入口文件注册导致 404。

仅在 `route_registration_check.enabled: true` 时执行：

1. **后端路由检查**：
   - 枚举 `route_registration_check.backend_route_directory` 下所有 `.ts` 文件
   - 排除 `route_registration_check.exempt_files` 中的文件
   - 对每个路由文件名（不含扩展名），在 `backend_entry_file` 中 Grep 匹配导入语句
   - 同时 Grep 匹配 `register_function_pattern`（如 `register`）开头的注册调用
   - 任一缺失即判定失败，并输出未注册的路由文件列表

2. **前端视图检查**（仅当 `frontend_views_directory` 非空时）：
   - 枚举 `frontend_views_directory` 下所有视图文件
   - 在 `frontend_entry_file` 中匹配 `frontend_required_hooks`（如 `import` / `type` / `v-for` / `v-else-if`）
   - 任一缺失即判定失败

#### 子阶段 3.3：类型同步验证（可选）
> 基于历史问题复盘提炼，防止前后端 types.ts 接口字段不一致导致运行时 undefined。

仅在 `type_sync_check.enabled: true` 时执行：

1. 读取 `type_sync_check.backend_types_path` 与 `frontend_types_path`
2. 提取所有 `export interface` 定义（接口名 + 字段列表）
3. 若 `sync_interfaces` 非空，仅校验该列表中的接口；否则校验全部
4. 跳过 `ignore_interfaces` 中的接口（如仅后端使用的内部接口）
5. 对每个需同步接口：比对前后端字段名集合是否一致
6. 任一接口字段不一致即判定失败，输出缺失/多余字段列表

#### 子阶段 3.4：Headless 崩溃防护（可选）
> 基于历史问题复盘提炼，防止 Chromium headless 模式 Canvas/WebGL 崩溃。

仅在 `headless_crash_guard.enabled: true` 时执行：

1. 读取 `browser.launch_args` 配置
2. 验证 `headless_crash_guard.required_launch_args` 中每个参数都被包含（默认 `--disable-gpu` / `--no-sandbox` / `--disable-dev-shm-usage` / `--disable-setuid-sandbox`）
3. 缺失任一参数即判定失败
4. 若浏览器启动崩溃，按 `max_retries` 重试，间隔 `retry_interval_ms`

### 阶段 4：交互功能
主题切换 → 表单输入 → 标签页切换 → **按钮自动发现**

#### 子阶段 4.1：危险操作测试（可选）
> 验证 dry_run 默认开启 / danger 样式 / 二次确认 / 取消不发请求。

仅在 `dangerous_action_tests.enabled: true` 时执行，对每个 `test_pages` 配置的页面：
1. 导航到目标页面
2. 对每个 `forms` 配置的表单：
   - 验证 `dry_run_switch` 默认开启（`default_dry_run: true`）
   - 关闭 dry_run → 验证触发按钮带 `danger_class` 样式
   - 点击触发按钮 → 等待 `confirm_component` 二次确认弹窗
   - 点击 `confirm_cancel_text` 取消 → 验证未发出清理请求
   - 再次点击触发按钮 → 确认弹窗 → 点击 `confirm_ok_text` → 验证执行结果
   - 若 `has_days_input: true`，验证 days 输入框存在
3. 验证多表单独立状态：一个表单的 loading/result 不影响其他表单

### 阶段 5：补充测试
响应式布局 → API 端点 → 控制台错误校验 → **临时文件清理**（`cleanup.cleanup_on_success: true` 时）

#### 子阶段 5.1：CORS 绕过策略验证（可选）
> 基于历史问题复盘提炼，防止浏览器 fetch 调用 API 被跨域拦截。

仅在 `cors_bypass.enabled: true` 时执行：

1. 读取 `cors_bypass.strategy`（默认 `context_request`，可选 `backend_proxy` / `disabled`）
2. 遍历 `cors_bypass.api_path_prefixes`（如 `/api` / `/health`）匹配的端点
3. **`context_request` 策略**：验证 `api_tests` 端点使用 Playwright `context.request.get()` 而非浏览器端 `fetch()`
4. **`backend_proxy` 策略**：验证测试通过后端代理转发，绕过浏览器同源策略
5. **`disabled` 策略**：跳过验证（仅在前后端同源时使用）
6. 命中浏览器端 fetch 调用即判定失败，提示改用 `context.request`

#### 子阶段 5.2：滚动容器裁切检测（可选）
> 基于帮助文档与关于模块测试复盘提炼，防止 flex 布局的双重滚动导致章节卡片仅显示标题。

仅在 `scroll_container_tests.enabled: true` 时执行：

1. 遍历 `scroll_container_tests.test_pages` 中配置的页面（如 `help` / `about`）
2. 对每个 `inner_overflow_selectors` 选择器，检查其 `overflow-y` computed style 是否为 `auto` / `scroll`
3. 同时检查 `outer_scroll_selectors` 选择器的 `overflow-y`，统计容器链路上 `overflow-y: auto` 嵌套层数
4. 嵌套层数 > 1 即判定为双重滚动，告警并输出外层与内层位置
5. 对每个 `card_selectors` 选择器，获取 `boundingRect().height`
6. 卡片高度 < `min_card_height_px`（默认 200px）即判定为被压缩
7. 若 `require_content_visible: true`，验证卡片内除标题外至少有一个内容块可见
8. 失败时若 `screenshot_on_fail: true`，截图取证

#### 子阶段 5.3：SPA 内部跳转验证（可选）
> 基于帮助文档与关于模块测试复盘提炼，防止跨组件视图跳转缺失 CustomEvent 派发。

仅在 `spa_navigation_tests.enabled: true` 时执行：

1. 遍历 `spa_navigation_tests.test_routes` 中配置的跳转链路（如 `about → help`）
2. 导航到 `from` 页面，点击 `trigger_selector` 触发跳转
3. 等待 `switch_wait_ms`（默认 1000ms）后验证 `to` 视图已渲染（通过 `expected_elements` 检查）
4. 读取 `app_entry` 文件，搜索 `addEventListener` 与 `removeEventListener` 调用
5. 验证事件名匹配 `event_name_pattern`（`{project}:navigate` → `karpathy:navigate`）
6. 若 `require_lifecycle_pair: true`，验证 add 在 `onMounted` 中、remove 在 `onBeforeUnmount` 中
7. 若 `validate_detail_whitelist: true`，验证派发的 `detail` 字段在 `allowed_views` 白名单内

#### 子阶段 5.4：检查更新状态机验证（可选）
> 基于帮助文档与关于模块测试复盘提炼，防止检查更新状态机不完整或定时器未清理。

仅在 `update_check_tests.enabled: true` 时执行：

1. 遍历 `update_check_tests.test_pages` 中配置的页面（如 `about`）
2. 验证状态机覆盖 `required_states` 全部状态（默认 5 态：idle/loading/latest/newer/error）
3. 对每个状态，检查 UI 中有对应的 `v-if` / `v-else-if` 分支
4. 调用 `update_endpoint` 接口：
   - 若 `offline_mode: true`，验证响应固定为 `{ has_update: false, source: 'local' }`
   - 若 `validate_no_external_call_in_offline: true`，验证后端未发起外部 GitHub API 调用
5. 若 `validate_poll_ge_ttl: true`，读取前端代码中的 `setInterval` 间隔，验证 ≥ `cache_ttl_ms`
6. 若 `require_timer_cleanup: true`，读取 `app_entry` 文件，验证 `setInterval` 与 `clearInterval` 在 `onMounted` / `onBeforeUnmount` 配对

### 阶段 6：结果汇总
输出摘要 → 保存 JSON 结果 → 如有失败项，自动修复后回归

## 使用方式

1. 确保 config.yaml 已按项目配置
2. 服务已运行时，设 uild.enabled: false 和 startup.enabled: false
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
| 
avigate | url, wait, timeout | 导航到页面 |
| 
avigate_tab | selector, label, wait_ms | 点击导航 tab |
| ssert_visible | selector, name | 断言元素可见 |
| ssert_title | contains | 断言页面标题 |
| click | selector, force | 点击元素 |
| ill | selector, text | 填写输入框 |
| ill_and_submit | selector, text, submit, submit_method | 填写并提交表单 |
| press_key | key | 按下键盘按键 |
| pi_check | path, expected_status | API 端点检查 |
| screenshot | path | 保存截图 |
| wait | ms | 等待指定毫秒 |
| 	heme_switch | - | 主题切换测试 |
| utton_discovery | - | 按钮自动发现 |
| 
esponsive_check | - | 响应式布局检查 |
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

## 持久化层测试（复盘提炼）

> 本节步骤类型基于持久化数据丢失问题的修复验证复盘提炼，所有参数从 `config.persistence_tests` 读取，不在代码中硬编码业务端点或攻击向量。

### 适用场景

- 后端新增持久化资源（配置、会话、文件落盘）后的回归测试
- 涉及缓存机制修改后的缓存刷新验证
- 涉及 HTTP 路由参数到文件系统映射的安全验证
- 涉及前后端数据同步、降级策略的容错验证

### 不适用场景

- 纯 UI 样式修改（用现有 `responsive_check` 即可）
- 纯 prompt 文本修改
- 纯构建配置修改

### 测试编排示例

在 `config.yaml` 的 `test_plan.phases` 中编排持久化测试步骤：

```yaml
test_plan:
  phases:
    persistence:
      steps:
        - type: persistence_crud_test
          resource: "conversations"
        - type: path_traversal_test
          resource: "conversations"
        - type: fallback_degradation_test
          api_patterns:
            - "/api/conversations"
          expected_behavior: "no-crash"
```

### 验证逻辑

| 步骤类型 | 验证点 | 通过条件 |
|---------|--------|---------|
| persistence_crud_test | PUT 创建 → GET 读取 → PUT 更新 → GET 验证更新（缓存刷新）→ DELETE → GET 确认删除 | 6 步全部通过，特别验证 PUT 后立即 GET 返回新值 |
| path_traversal_test | 遍历 `malicious_ids` 逐个请求 | 全部返回 4xx（5xx 或 200 均视为失败） |
| fallback_degradation_test | 拦截 API 返回 503，前端加载页面 | body 仍可见（不崩溃）|

## 系统清理模块测试（复盘提炼）

> 本节步骤类型基于系统清理模块 Playwright 前端验证复盘提炼，所有参数从 `config.encoding_tests`、`config.dangerous_action_tests`、`config.service_lifecycle`、`config.cleanup` 读取，不在代码中硬编码页面、表单、选择器或攻击向量。

### 适用场景

- Windows 中文环境下，页面 tab 标签或表单标签可能编码乱码的回归测试
- 有危险操作（dry_run/二次确认/danger 样式）的清理类模块
- 多表单独立状态管理（每表单独立 loading/result）的模块
- 测试前需停止旧服务、测试后需清理临时脚本的场景

### 不适用场景

- 纯静态 HTML 页面（用 `responsive_check` 即可）
- 移动端 App 测试
- 无前端界面的纯 API 测试

### 测试编排示例

在 `config.yaml` 的 `test_plan.phases` 中编排系统清理模块测试步骤：

```yaml
test_plan:
  phases:
    cleanup_module:
      steps:
        - type: service_lifecycle
          stop_old_process: true
        - type: encoding_check
          check_pages: ["dashboard", "cleanup"]
        - type: dangerous_action_test
          test_pages:
            - key: "cleanup"
              forms:
                - key: "compileCache"
                  has_days_input: false
                  default_dry_run: true
        - type: multi_form_test
          test_pages:
            - key: "cleanup"
        - type: temp_cleanup
          cleanup_dirs: ["."]
```

### 验证逻辑

| 步骤类型 | 验证点 | 通过条件 |
|---------|--------|---------|
| encoding_check | 遍历 `check_pages` 中每个页面的 `scan_selectors`，dump DOM 文本码点 | 不含 `fffd_codepoint`（默认 `0xFFFD`），即无替换字符 |
| dangerous_action_test | dry_run 默认开启 → 关闭 dry_run 出现 danger 样式 → 点击触发二次确认 → 取消不发请求 → 确认执行成功 | 全部断言通过，特别验证"取消"路径不发请求 |
| multi_form_test | 每个 `form_container_selector` 独立显示 loading 和 result | 表单 A 的 loading 不影响表单 B，结果互不污染 |
| service_lifecycle | 停止旧进程 → 启动后端/前端 → 轮询端口 Listen | 所有 `required_ports` 在 `startup_timeout_ms` 内进入 Listen 状态 |
| temp_cleanup | 按 pattern 匹配并删除临时文件 | 删除过程中无异常，残留文件计数为 0 |

## Async 可靠性测试（复盘提炼）

> 本节基于浏览器登录 91s 超时复盘提炼，验证 async/await + IPC 场景的可靠性。所有参数从 `config.async_reliability_tests` 读取，不在代码中硬编码检查模式或阈值。

### 子阶段 3.6：Async 可靠性静态检查（可选）

仅在 `async_reliability_tests.enabled: true` 时执行：

1. **超时防护检查**（`timeout_protection.enabled: true`）：
   - 按配置的 `pattern` 扫描未包裹超时的 await 调用
   - 排除 `whitelist_pattern` 中的白名单调用
   - 验证违规调用是否被 `required_wrapper` 包裹
   - 命中违规 → 标记为 `severity` 级别（critical/warning/suggestion）

2. **心跳线程实现检查**（`heartbeat_reliability.enabled: true`）：
   - 检查心跳是否使用 `forbidden_in_heartbeat` 中禁止的异步实现
   - 验证是否使用 `required_impl`（如 threading.Thread）
   - 验证状态文件 ts 字段更新独立性（是否在 `required_context` 内）

3. **兜底数据检查**（`fallback_data.enabled: true`）：
   - 扫描超时后的异常处理分支
   - 验证是否包含 `forbidden_actions`（如 raise、pass）
   - 验证是否包含 `required_action`（如 fallback_data_assignment）

### 子阶段 5.5：Async 可靠性运行时验证（可选）

仅在 `async_reliability_tests.runtime_verification.enabled: true` 时执行：

1. 启动子进程（如 browser_login.py）
2. 监控状态文件 ts 字段更新间隔
3. 若间隔 > `max_gap_sec`（默认 10s）→ 测试失败
4. 可选：模拟 IPC 阻塞，验证心跳线程仍能更新 ts

### 测试报告格式

Async 可靠性测试结果必须包含以下字段：

```
## Async 可靠性测试报告
- CODING-021 超时保护：✅/❌（N 处违规）
- CODING-022 心跳线程实现：✅/❌（心跳使用 asyncio.Task 违规）
- CODING-023 状态文件更新独立性：✅/❌（ts 更新间隔最大 Xs）
- CODING-024 兜底数据：✅/❌（N 处超时后无兜底）
- CODING-025 多层超时：✅/❌（仅单层超时）
```

详细的测试方法、模拟阻塞模板和覆盖矩阵见 [async-reliability-testing.md](references/async-reliability-testing.md)。

## 配置一致性验证（复盘提炼）

> 基于历史配置读取不一致问题复盘提炼，验证所有入口使用统一的配置读取函数。

仅在 `verification.config_consistency_check.enabled: true` 时执行：

### 验证流程

1. 修改 config.json 中的配置项（如 apiKey）
2. 重启服务
3. 调用 GET /api/ai/config 验证返回值是否反映新配置
4. 调用 POST /api/ai/test-connection 验证是否使用新配置
5. 如果结果不一致，说明存在配置读取不一致问题

### 判断标准

- config.json 中的值 == GET 接口返回的值 == 测试连接使用的值

## 热更新闭环验证（复盘提炼）

> 基于保存配置后运行实例未同步更新问题复盘提炼，验证保存配置后运行实例是否同步更新（无需重启）。

仅在 `verification.hot_update_verification.enabled: true` 时执行：

### 验证流程

1. 记录当前配置状态（GET /api/ai/config）
2. 保存新配置（PUT /api/ai/config）
3. 不重启服务，立即调用 GET /api/ai/config 验证返回值
4. 调用 POST /api/ai/test-connection 验证使用的是新配置
5. 恢复原始配置

### 判断标准

- 保存后 GET 返回新值（无需重启）
- 保存后测试连接使用新值（无需重启）

## 降级机制验证（复盘提炼）

> 基于无效 API Key 场景复盘提炼，覆盖正常路径和降级路径。

仅在 `verification.degradation_verification.enabled: true` 时执行：

### 验证流程

1. 正常路径：配置有效 API Key，验证 LLM 问答正常
2. 降级路径：配置无效 API Key，验证降级为检索模式
3. 兜底路径：服务不可用时，验证兜底提示

### 判断标准

- 正常路径：LLM 问答正常，无降级标记
- 降级路径：显示降级提示信息
- 兜底路径：显示服务不可用提示

测试用例在 `verification.degradation_verification.test_cases` 中配置，每条包含 `name`、`simulate`（模拟方式）和 `expected`（期望行为）。

## 目录结构验证测试（复盘提炼）

> 基于 P0/P1/P2 目录结构优化复盘提炼，覆盖 .gitignore 规则、目录结构完整性、脚本引用完整性、类型检查回归四个子项。所有参数从 `config.structure_verification` 读取，不在代码中硬编码路径、命令或模式。

仅在 `structure_verification.enabled: true` 时执行。**目录结构变更后的强制回归测试**（在阶段 5 补充测试中执行），覆盖 .gitignore 规则匹配、文件迁移后的目录结构、脚本引用无残留旧名、TypeScript 类型检查四个维度。

### 子阶段 5.6：.gitignore 规则验证测试

#### 测试目标
验证更新 .gitignore 后，目标规则正确匹配预期文件，且已跟踪文件已从 git 索引移除（避免 .gitignore 对已跟踪文件不生效的陷阱）。

#### 测试步骤
1. 遍历 `gitignore_target_patterns` 中的每个模式
2. 对每个模式执行 `gitignore_verify_command`（如 `git check-ignore -v`），验证规则匹配
3. 对每个匹配的文件执行 `gitignore_tracked_check`（如 `git ls-files --error-unmatch`），检查是否仍被跟踪
4. 若仍被跟踪，按 `gitignore_untrack_command`（如 `git rm --cached`）移除索引
5. 验证移除后 `gitignore_tracked_check` 返回非零退出码（即已不被跟踪）

#### 预期结果
- 所有 `gitignore_target_patterns` 都被 .gitignore 规则匹配
- 所有匹配的文件都已从 git 索引移除（`git ls-files` 不再列出）
- .gitignore 工作树状态干净（无未提交的索引变更残留）

#### 失败处理
- 规则不匹配：检查 .gitignore 语法（路径分隔符、通配符、前导斜杠语义）
- 已跟踪未移除：执行 `gitignore_untrack_command` 移除索引，验证 .gitignore 对该文件生效
- 移除后仍被跟踪：检查 global .gitignore 或 .git/info/exclude 是否有冲突规则

### 子阶段 5.7：目录结构完整性测试

#### 测试目标
验证文件迁移后目录结构完整，运行时数据与源码分离（避免运行时数据污染源码目录导致 git 仓库膨胀与跨环境不一致）。

#### 测试步骤
1. 验证 `expected_source_dirs` 中每个源码目录存在
2. 验证 `expected_data_dir`、`expected_docs_dir`、`expected_scripts_dir` 存在
3. 遍历 `forbidden_mixing_patterns`，对每个 `pattern` 用 Glob/Grep 检测是否命中
4. 命中即判定为运行时数据与源码混合（违反分离原则）
5. 输出违规路径列表及对应 `reason`

#### 预期结果
- 所有预期目录存在
- 无 `forbidden_mixing_patterns` 命中（运行时数据未混入源码目录）
- 源码目录、运行时数据目录、文档目录、脚本目录各司其职

#### 失败处理
- 预期目录缺失：检查文件迁移是否遗漏，补全目录创建
- 命中禁止混合模式：将运行时数据迁移到 `expected_data_dir`，从源码目录移除
- 重复检查迁移后状态，直到无禁止模式命中

### 子阶段 5.8：脚本引用完整性测试

#### 测试目标
验证文件重命名后无残留旧名引用（避免脚本运行时找不到文件导致 ENOENT）。

#### 测试步骤
1. 对每次文件重命名，将旧文件名作为 `script_rename_grep_pattern`
2. 执行 `script_rename_verify_command`（如 `git grep`）搜索旧名引用
3. 排除 .git 历史与备份文件（仅扫描工作树）
4. 命中即判定为残留引用
5. 输出命中文件列表与行号

#### 预期结果
- 工作树中无任何旧文件名引用
- 所有引用都已更新为新文件名
- `git grep` 退出码为 1（即未找到匹配）

#### 失败处理
- 命中残留引用：逐个更新引用为新文件名
- 排除合法引用（如 CHANGELOG、迁移日志）后再次验证
- 重复检查直到 `git grep` 无匹配

### 子阶段 5.9：类型检查回归测试

#### 测试目标
验证文件迁移/路径变更后 TypeScript 类型检查通过（避免 import 路径断裂导致运行时 undefined）。

#### 测试步骤
1. 遍历 `typecheck_working_dirs` 中每个工作目录（如 `backend` / `frontend`）
2. 在对应工作目录执行 `typecheck_commands` 中的命令（如 `npx tsc --noEmit`）
3. 捕获命令退出码与 stdout/stderr
4. 退出码非零即判定为类型检查失败
5. 解析输出中的错误行号与错误信息

#### 预期结果
- 所有 `typecheck_commands` 退出码为 0
- 无 TS2xxx / TS6xxx 错误（特别是 "Cannot find module" 与 "Cannot find name"）
- 类型检查报告无新增错误（与基线对比）

#### 失败处理
- TS2307 Cannot find module：检查 import 路径是否在迁移后更新，修正相对路径或 alias
- TS2503 Cannot find namespace：检查 types.ts 是否迁移到新位置，更新引用
- 其他类型错误：按错误信息逐个修复，修复后重新运行 `typecheck_commands`

## 破坏性按钮保护机制

测试中遇到破坏性按钮时，必须先备份配置，测试后恢复。破坏性按钮白名单在 `destructive_buttons` 配置中定义。

| 按钮文本 | 风险 | 处理策略 |
|---|---|---|
| 恢复初始配置 | 覆盖用户自定义配置 | 测试前备份 config.json，测试后恢复 |
| 删除 | 删除数据 | 测试前备份相关数据，测试后恢复 |
| 清除 | 清空配置 | 测试前备份，测试后恢复 |
| 重置 | 恢复默认值 | 测试前备份，测试后恢复 |

**强制流程**：
1. 测试前：备份受影响的配置/数据文件
2. 执行破坏性操作
3. 验证操作效果
4. 测试后：从备份恢复

> 与 `dangerous_action_tests` 的关系：`dangerous_action_tests` 验证 UI 交互行为（dry_run/二次确认/danger 样式），本节确保测试流程自身不会因点击破坏性按钮而破坏测试环境。两者互补，前者测功能正确性，后者测测试流程安全性。

## 适配新项目

仅需修改 config.yaml：

1. **服务地址**：service.frontend_url / service.api_url
2. **导航结构**：
avigation.tab_selector / 
avigation.pages
3. **按钮选择器**：utton_discovery.button_selectors
4. **API 端点**：pi_tests.endpoints
5. **构建/启动脚本**：uild.script_path / startup.script_path
6. **破坏性按钮**：utton_discovery.destructive_button_texts
7. **持久化测试资源**：persistence_tests.endpoints / test_payloads（新增持久化资源时追加端点模板与最小 payload）
8. **编码检测**：encoding_tests.check_pages / encoding_tests.scan_selectors（按需启用 `enabled: true`，缩窄选择器范围减少噪音）
9. **危险操作测试**：dangerous_action_tests.test_pages / forms（按实际表单配置 dry_run/确认弹窗/danger 样式选择器）
10. **服务生命周期**：service_lifecycle.start_backend / start_frontend / required_ports（与 service.required_ports 对齐）
11. **临时文件清理**：cleanup.temp_files_pattern / cleanup.cleanup_dirs（按项目约定的临时文件命名约定配置）
12. **PowerShell 约束**：powershell_constraints.blocked_commands / bypass_bat_pause（按项目环境调整）
13. **路由注册验证**：route_registration_check.backend_route_directory / backend_entry_file（按实际后端目录配置，新增路由文件后自动检测是否在入口注册）
14. **类型同步验证**：type_sync_check.backend_types_path / frontend_types_path（按实际 types.ts 路径配置，新增 interface 后自动检测前后端字段对齐）
15. **CORS 绕过策略**：cors_bypass.strategy / api_path_prefixes（默认 context_request，前后端跨域时无需调整；同源时改 disabled）
16. **Headless 崩溃防护**：headless_crash_guard.required_launch_args / max_retries（默认含 --disable-gpu，虚拟机/RDP 环境按需追加 --use-gl=swiftshader）
17. **PowerShell 兼容性**：powershell_compatibility.forbidden_syntaxes / syntax_replacements（默认禁止 && / ||，新增禁止语法时追加）
18. **编码安全增强**：encoding_safety_enhanced.check_extensions / replacement_char_threshold（默认检测 .ts/.vue/.py 等，U+FFFD 阈值 0 即不允许）
19. **滚动容器测试**：scroll_container_tests.test_pages / inner_overflow_selectors / card_selectors / min_card_height_px（按实际页面与卡片选择器配置，卡片高度阈值默认 200px）
20. **SPA 内部跳转测试**：spa_navigation_tests.test_routes / event_name_pattern / project_name / allowed_views（按实际跳转链路与事件名配置，与前端审查的 spa_navigation 段对齐）
21. **检查更新状态机测试**：update_check_tests.test_pages / update_endpoint / required_states / offline_mode（按实际接口与状态机配置，与前端审查的 check_update 段对齐）
22. **构建产物验证**：build_artifact_verification.serving_endpoint_template / bundle_directory / key_strings（按实际构建产物路径与新增 CSS 类配置）
23. **浏览器自动化降级**：browser_automation_fallback.chain / max_retry_per_level / timeout_ms（按可用工具链配置，无 MCP 时移除 playwright-mcp）
24. **导航栏双模式测试**：nav_dual_mode_tests.toggle_selector / menu_items / tooltip_selector（按实际导航栏选择器配置，菜单项变更时同步 menu_items）
25. **图标主题跟随测试**：icon_theme_tests.icon_selectors / test_themes / theme_switcher_selector（按实际图标选择器与主题列表配置）
26. **PowerShell 字符串验证**：powershell_string_verification.forbidden_patterns / recommended_pattern（按实际测试脚本语言配置，bash/Python 环境可禁用）
27. **Async 可靠性测试**：async_reliability_tests.timeout_protection / heartbeat_reliability / fallback_data / runtime_verification（按项目使用的 async 模式配置，纯同步项目可禁用）
28. **配置一致性验证**：verification.config_consistency_check.check_entries / verify_method（按实际配置读取入口配置）
29. **热更新闭环验证**：verification.hot_update_verification.verify_api（按实际热更新接口配置）
30. **降级机制验证**：verification.degradation_verification.test_cases（按实际降级路径配置 simulate 和 expected）
31. **破坏性按钮白名单**：destructive_buttons（按实际按钮文本追加，测试流程遇到白名单按钮自动备份恢复）
32. **Tauri 桌面应用测试**：tauri.enabled / exe_name / src_tauri_dir / build_script_path（仅 Tauri 项目启用，按实际项目结构与构建脚本配置）
33. **SPA 产物验证**：spa.source_dirs / output_dir / key_strings（按实际前端源码目录与产物路径配置，新增功能时追加 key_strings）
34. **后端健康检查**：health_check.endpoint / retry_count / timeout（按 Tauri 后端实际端口与路径配置）
35. **invoke 权限验证**：invoke.commands / permissions / url_patterns（按实际使用的 Tauri 插件与命令配置，新增 invoke 命令时同步追加）
36. **磁盘空间检查**：disk_space.debug_min_gb / release_min_gb（按项目编译产物大小调整阈值）
37. **Console 日志采集**：console_log.prefixes / error_keywords（按 Tauri 应用的日志前缀与错误模式配置，与 failure_classification.rules 对齐）

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

## 故障排查

常见问题及解决方案见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。重点关注：

- **编码乱码（U+FFFD）**：见 TROUBLESHOOTING 第 11 条，用 Unicode 码点匹配替代终端字符串匹配
- **Playwright 中文匹配失败**：见 TROUBLESHOOTING 第 12 条，避免 `has_text` 中文，改用 `get_dom_text_codepoints` 比对码点
- **端口占用**：见 TROUBLESHOOTING 第 13 条，用 `service_lifecycle.stop_old_process: true` 启动前清理
- **bat 脚本 pause 卡住**：见 TROUBLESHOOTING 第 14 条，配置 `powershell_constraints.bypass_bat_pause: true`
- **GPU 崩溃**：见 TROUBLESHOOTING 第 15 条，`browser.launch_args` 必须含 `--disable-gpu`
- **Python 文件编码声明缺失**：见 TROUBLESHOOTING 第 16 条，所有 .py 文件首行加 `# -*- coding: utf-8 -*-`
- **API 测试返回 404（路由未注册）**：见 TROUBLESHOOTING 第 17 条，启用 `route_registration_check.enabled: true` 自动检测
- **前后端类型不匹配**：见 TROUBLESHOOTING 第 18 条，启用 `type_sync_check.enabled: true` 自动检测
- **Chromium headless 模式崩溃**：见 TROUBLESHOOTING 第 19 条，启用 `headless_crash_guard.enabled: true` 自动验证启动参数
- **Python 测试脚本编码错误**：见 TROUBLESHOOTING 第 20 条，启用 `encoding_safety_enhanced.verify_after_write: true` 写入后验证
- **PowerShell 命令拼接失败**：见 TROUBLESHOOTING 第 21 条，启用 `powershell_compatibility.enabled: true` 自动检测禁止语法
- **章节卡片仅显示标题（双重滚动裁切）**：见 TROUBLESHOOTING 第 22 条，启用 `scroll_container_tests.enabled: true` 自动检测容器链路上 `overflow-y: auto` 嵌套层数与卡片实际高度
- **跨组件跳转失效（About → Help 无响应）**：见 TROUBLESHOOTING 第 23 条，启用 `spa_navigation_tests.enabled: true` 自动检测 CustomEvent 派发与监听器生命周期配对
- **检查更新卡在 loading 不恢复**：见 TROUBLESHOOTING 第 24 条，启用 `update_check_tests.enabled: true` 自动检测状态机 5 态覆盖与定时器清理
- **构建产物 HTTP 404 或内容截断**：见 TROUBLESHOOTING 第 25 条，启用 `build_artifact_verification.enabled: true` 自动验证 HTTP 三要素
- **Playwright MCP 报 "MCP server is not found"**：见 TROUBLESHOOTING 第 26 条，启用 `browser_automation_fallback.enabled: true` 自动降级到 browser_use subagent
- **导航栏折叠/展开切换失效**：见 TROUBLESHOOTING 第 27 条，启用 `nav_dual_mode_tests.enabled: true` 自动验证切换、tooltip、12 图标导航
- **图标不跟随主题变色**：见 TROUBLESHOOTING 第 28 条，启用 `icon_theme_tests.enabled: true` 自动验证 currentColor 在 6 主题下的颜色变化
- **PowerShell 字符串验证输出混乱**：见 TROUBLESHOOTING 第 29 条，启用 `powershell_string_verification.enabled: true` 自动检测 curl.exe 管道赋值陷阱
- **Tauri 启动后立即退出或白屏**：见 TROUBLESHOOTING 第 30 条，启用 `tauri.enabled: true` 自动验证 SPA 产物时间戳 + Rust 编译 + Tauri 启动
- **Tauri invoke 调用报 `Plugin not found` / `not allowed` / `URL: local`**：见 TROUBLESHOOTING 第 31 条，启用 `invoke` 配置块自动执行三层权限验证（插件依赖 / 权限声明 / URL 白名单）
- **Tauri 编译报 `linker 'lld-link' not found`**：见 TROUBLESHOOTING 第 32 条，启用 `tauri.enabled: true` 自动预检 cargo / LLD / windres / 磁盘空间

## 前置检查协议（Pre-flight Check Protocol）

> 基于 v2 导航栏改造复盘提炼，防止 E2E 测试在服务未就绪时运行导致全部用例误报失败。

仅在 `precheck.enabled: true` 时执行。**测试入口前置检查**（在阶段 1 构建之前执行），通过端口监听 + 健康检查 + 浏览器可启动性三层验证，确保后续测试在就绪环境上运行。

### 子阶段：测试入口前置检查

1. **端口监听检查**：遍历 `precheck.required_ports`，用 `precheck.port_check_method` 检测每个端口状态是否为 `precheck.port_check_state`
2. **健康检查**：调用 `precheck.health_check_endpoint`，验证 HTTP 响应状态码 == `precheck.health_check_expected_status`
3. **浏览器可启动检查（可选）**：若 `precheck.browser_launch_check: true`，尝试启动浏览器并访问 `about:blank`，验证 Playwright 环境可用
4. **失败处理**：
   - 若 `precheck.auto_start_on_failure: true`：调用 `precheck.service_start_script` 启动服务，按 `precheck.port_poll_interval_ms` 轮询端口，最长等待 `precheck.startup_timeout_ms` 毫秒
   - 否则：中止测试，输出诊断日志
5. **日志输出**：必须输出诊断信息（端口状态、健康检查响应），便于排查环境问题

### 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `precheck.enabled` | `true` | 是否启用前置检查协议 |
| `precheck.required_ports` | `[3000, 5173]` | 必须监听的端口列表 |
| `precheck.port_check_state` | `Listen` | 端口期望状态（Listen / Bound） |
| `precheck.port_check_method` | `Get-NetTCPConnection` | 端口检测方法（PowerShell cmdlet） |
| `precheck.health_check_endpoint` | `/health` | 健康检查端点路径 |
| `precheck.health_check_expected_status` | `200` | 健康检查期望 HTTP 状态码 |
| `precheck.startup_timeout_ms` | `30000` | 启动后最长等待毫秒数 |
| `precheck.port_poll_interval_ms` | `1000` | 端口轮询间隔毫秒数 |
| `precheck.browser_launch_check` | `true` | 是否执行浏览器可启动检查 |
| `precheck.service_start_script` | `automation.ps1 -Action start` | 服务启动脚本 |
| `precheck.auto_start_on_failure` | `true` | 检查失败时是否自动启动服务 |

### 配置示例

```yaml
precheck:
  enabled: true
  required_ports:
    - 3000
    - 5173
  port_check_state: "Listen"
  port_check_method: "Get-NetTCPConnection"
  health_check_endpoint: "/health"
  health_check_expected_status: 200
  startup_timeout_ms: 30000
  port_poll_interval_ms: 1000
  browser_launch_check: true
  service_start_script: "automation.ps1 -Action start"
  auto_start_on_failure: true
```

## 测试用例同步协议（Test Case Sync Protocol）

> 基于 v2 改造复盘提炼，防止代码变更影响 DOM 后测试用例引用已删除的选择器。

仅在 `test_sync.enabled: true` 时执行。**代码变更后测试同步验证**（在阶段 5 补充测试中执行），通过 git diff 扫描选择器变更并交叉检查测试用例引用，避免测试引用失效选择器。

### 子阶段：代码变更后测试同步验证

1. **选择器变更识别**：用 `test_sync.selector_patterns` 中配置的正则模式，扫描 git diff 中 class / id / 层级 / data-testid 的删除或修改
2. **测试用例引用扫描**：按 `test_sync.test_file_patterns` 匹配测试文件，Grep 查找引用了被删除选择器的用例
3. **失败处理**：命中即判定为同步失败，必须更新测试用例（若 `test_sync.stale_selector_threshold: 0`，零容忍）
4. **静默错误检测**：若 `test_sync.silent_failure_forbidden: true`，扫描测试用例的 try/except 块，确认 except 分支未静默吞错（必须 `record(..., False, str(e))`）
5. **同 commit 验证**：若 `test_sync.require_same_commit: true`，检查 commit 中是否同时包含代码与测试用例修改，避免代码先行/测试滞后的不对称提交

### 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `test_sync.enabled` | `true` | 是否启用测试同步协议 |
| `test_sync.test_file_patterns` | `**/test_*.py,**/test_*.ts,**/*.spec.ts,**/*.test.ts` | 测试文件 glob 匹配模式（逗号分隔） |
| `test_sync.selector_patterns` | `\.[-\w]+, #[-\w]+, [class="[^"]+"], data-testid="[^"]+"` | 选择器变更识别正则（逗号分隔） |
| `test_sync.require_same_commit` | `true` | 是否要求代码与测试同 commit 提交 |
| `test_sync.silent_failure_forbidden` | `true` | 是否禁止 except 分支静默吞错 |
| `test_sync.stale_selector_threshold` | `0` | 失效选择器容忍阈值（0 = 零容忍） |

### 配置示例

```yaml
test_sync:
  enabled: true
  test_file_patterns:
    - "**/test_*.py"
    - "**/test_*.ts"
    - "**/*.spec.ts"
    - "**/*.test.ts"
  selector_patterns:
    - '\.[-\w]+'
    - '#[-\w]+'
    - '[class="[^"]+"]'
    - 'data-testid="[^"]+"'
  require_same_commit: true
  silent_failure_forbidden: true
  stale_selector_threshold: 0
```

## 失败分类协议（Failure Classification Protocol）

> 基于 v2 改造复盘提炼，标准化测试失败的分类与处理流程。

仅在 `failure_classification.enabled: true` 时执行。**测试失败后自动分类**（在阶段 6 结果汇总中执行），按错误消息模式匹配失败类型，并输出对应的修复建议。

### 子阶段：测试失败后自动分类

1. **失败类型枚举**：`connection_refused` / `selector_not_found` / `assertion_failed` / `timeout` / `browser_crash` / `encoding_corrupted` / `config_mismatch`
2. **分类规则**：按 `failure_classification.rules` 中的模式匹配错误消息，每条规则包含 `type` / `pattern` / `suggestion` 三元组
3. **处理建议**：每种失败类型对应 `failure_classification.suggestions` 中的修复建议（命令或操作步骤）
4. **自动修复触发**：若 `failure_classification.auto_fix: true`，对 `selector_not_found` 类型自动触发测试用例同步检查（衔接 Test Case Sync Protocol）

### 失败类型 + 模式 + 建议对照表

| 失败类型 | 匹配模式 | 修复建议 |
|----------|----------|----------|
| `connection_refused` | `ERR_CONNECTION_REFUSED`, `ECONNREFUSED` | 运行 `automation.ps1 -Action start` 启动服务 |
| `selector_not_found` | `TimeoutError.*waiting for selector`, `Element not found` | 检查代码是否删除了该选择器，同步更新测试用例 |
| `assertion_failed` | `AssertionError`, `expect(*) to be` | 检查断言预期值是否与实际行为一致 |
| `timeout` | `TimeoutError`, `Exceeded timeout` | 增加超时时间或优化等待策略 |
| `browser_crash` | `Target closed`, `Browser crashed` | 检查 Chromium 启动参数，参考 `headless_crash_guard` |
| `encoding_corrupted` | `U+FFFD`, `锟斤拷`, `乱码` | 运行 `node scripts/check-encoding.js --fix` |
| `config_mismatch` | `config.*not.*found`, `undefined` | 检查 config.yaml 与 defaults.yaml 配置项 |

### 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `failure_classification.enabled` | `true` | 是否启用失败分类协议 |
| `failure_classification.rules` | 见配置示例 | 失败类型匹配规则列表（type + pattern + suggestion） |
| `failure_classification.suggestions` | 见配置示例 | 失败类型对应的修复建议映射 |
| `failure_classification.auto_fix` | `true` | 是否对 selector_not_found 自动触发测试同步检查 |

### 配置示例

```yaml
failure_classification:
  enabled: true
  auto_fix: true
  rules:
    - type: "connection_refused"
      pattern: "ERR_CONNECTION_REFUSED|ECONNREFUSED"
      suggestion: "运行 automation.ps1 -Action start 启动服务"
    - type: "selector_not_found"
      pattern: "TimeoutError.*waiting for selector|Element not found"
      suggestion: "检查代码是否删除了该选择器，同步更新测试用例"
    - type: "assertion_failed"
      pattern: "AssertionError|expect\\(.*\\) to be"
      suggestion: "检查断言预期值是否与实际行为一致"
    - type: "timeout"
      pattern: "TimeoutError|Exceeded timeout"
      suggestion: "增加超时时间或优化等待策略"
    - type: "browser_crash"
      pattern: "Target closed|Browser crashed"
      suggestion: "检查 Chromium 启动参数，参考 headless_crash_guard"
    - type: "encoding_corrupted"
      pattern: "U\\+FFFD|锟斤拷|乱码"
      suggestion: "运行 node scripts/check-encoding.js --fix"
    - type: "config_mismatch"
      pattern: "config.*not.*found|undefined"
      suggestion: "检查 config.yaml 与 defaults.yaml 配置项"
  suggestions:
    connection_refused: "运行 automation.ps1 -Action start 启动服务"
    selector_not_found: "检查代码是否删除了该选择器，同步更新测试用例"
    assertion_failed: "检查断言预期值是否与实际行为一致"
    timeout: "增加超时时间或优化等待策略"
    browser_crash: "检查 Chromium 启动参数，参考 headless_crash_guard"
    encoding_corrupted: "运行 node scripts/check-encoding.js --fix"
    config_mismatch: "检查 config.yaml 与 defaults.yaml 配置项"
```

## 服务管理协议（Service Management Protocol）

> 基于 v2 改造复盘提炼，标准化测试过程中的服务生命周期管理。

仅在 `service_management.enabled: true` 时执行。**测试过程服务管理**（贯穿阶段 1-6），覆盖服务状态检测、端口冲突预防、日志重定向残留清理、测试后清理四个环节。

### 子阶段：测试过程服务管理

1. **服务状态检测**：测试前、测试中、测试后分别检测服务状态（端口监听 + 健康检查）
2. **端口冲突预防**：若 `service_management.stop_old_process: true`，测试启动前先停止占用 `precheck.required_ports` 的旧进程，避免端口冲突导致新服务启动失败
3. **日志重定向清理**：若 `service_management.cleanup_residual: true`，测试后清理因 `pnpm run dev` 等日志重定向产生的 cmd.exe 残留进程（按 `service_management.residual_match_pattern` 匹配命令行）
4. **测试后清理**：若 `service_management.cleanup_after_test: true`，测试完成后调用 `service_management.stop_script` 停止服务（仅当 `service_management.keep_running: false` 时执行）

### 参数表（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `service_management.enabled` | `true` | 是否启用服务管理协议 |
| `service_management.stop_old_process` | `true` | 测试启动前是否停止占用端口的旧进程 |
| `service_management.cleanup_residual` | `true` | 是否清理日志重定向残留进程 |
| `service_management.cleanup_after_test` | `false` | 测试后是否停止服务（受 keep_running 控制） |
| `service_management.keep_running` | `true` | 测试后是否保持服务运行（true 时即使 cleanup_after_test=true 也不停止） |
| `service_management.residual_match_pattern` | `pnpm run dev` | 残留进程命令行匹配模式 |
| `service_management.stop_script` | `automation.ps1 -Action stop` | 服务停止脚本 |

### 配置示例

```yaml
service_management:
  enabled: true
  stop_old_process: true
  cleanup_residual: true
  cleanup_after_test: false
  keep_running: true
  residual_match_pattern: "pnpm run dev"
  stop_script: "automation.ps1 -Action stop"
```

## 搜索结果交叉验证协议（Search Result Cross-Verification Protocol）

> 基于 P0/P1/P2 目录结构优化复盘提炼，防止单一搜索方法因工具限制（路径含特殊字符、输出截断、未入库文件）返回假阴性，导致测试用例误判失败或漏检真实问题。所有参数从 `config.search_cross_verification` 读取，不在代码中硬编码工具名或阈值。

仅在 `search_cross_verification.cross_verify_required: true` 时执行。**搜索结果未找到时的强制交叉验证**（贯穿所有测试阶段），覆盖 Glob / Grep / LS / Test-Path 四种方法的互相验证，确保"未找到"结论经过至少两种方法确认。

### 适用场景

- 测试用例通过 Glob 查找文件未命中，需确认是否因路径含特殊字符（`+` / `(` / `)` / `[` / `]`）导致通配符转义失败
- 测试用例通过 Grep 搜索文件内容未命中，需确认是否因文件未入库或被 .gitignore 排除
- 测试用例通过 LS 列目录未命中目标，需确认是否因输出超长被截断（> `ls_truncate_threshold`）
- 验证文件/目录是否存在时，单一方法返回"不存在"必须用另一种方法复核

### 验证矩阵

| 工具 | 适用场景 | 限制 |
|------|----------|------|
| Glob | 文件名模式匹配（支持 `*` / `?` / `[]`） | 路径含 `glob_escape_chars` 中的特殊字符时可能转义失败 |
| Grep | 文件内容搜索（正则匹配） | 无法搜索未入库的文件（受 .gitignore 与索引影响） |
| LS | 目录列表（递归枚举） | 输出超 `ls_truncate_threshold` 字符时可能截断 |
| Test-Path | 精确路径存在性判断 | 需已知完整路径，不支持通配符 |

### 验证流程

1. **主搜索方法未找到目标**：任一 `primary_tools`（Glob / Grep / LS）返回空结果或退出码 1
2. **触发交叉验证**：从 `fallback_tools`（PowerShell `Test-Path` / `Resolve-Path`）中选择互补方法
3. **互补方法选择规则**：
   - Glob 失败 → 用 `Test-Path` 精确验证（避免通配符转义问题）
   - Grep 失败 → 用 `LS` 或 `Test-Path` 验证文件存在性（排除索引未入库问题）
   - LS 失败 → 用 `Glob` 精确模式验证（避免输出截断）
4. **结果汇总**：
   - 互补方法找到目标 → 主方法为假阴性，记录工具限制原因，测试继续
   - 互补方法也未找到 → 确认为真阴性，按测试用例预期处理
5. **日志输出**：交叉验证必须记录主方法、互补方法、各自结果、最终判定

### 关键原则

- **任一搜索方法未找到目标时，必须用另一种方法交叉验证**，禁止仅凭单一方法返回空即判定目标不存在
- **Glob 模式中的特殊字符**（`+` / `(` / `)` / `[` / `]`）必须按 `glob_escape_chars` 配置转义，否则视为无效搜索
- **LS 输出超 `ls_truncate_threshold`** 时自动降级为 Glob 精确模式，避免截断导致的假阴性
- **Grep 内容搜索**应同时尝试 `grep_content_patterns` 中的多种模式（如 `export class {name}` 与 `export.*{name}`），避免单一模式遗漏

### 失败处理

- **主方法假阴性**：在测试报告中标注工具限制原因，更新 `verification_matrix` 中的 limitation 说明
- **互补方法也失败**：确认为真阴性，按测试用例预期失败处理，输出诊断日志（主方法输出、互补方法输出、尝试的模式列表）
- **Glob 转义失败**：检查路径是否含 `glob_escape_chars`，重新构造转义后的模式重试
- **Grep 未入库**：检查文件是否被 .gitignore 排除或未 git add，必要时用 `Test-Path` 直接验证文件系统存在性

## v2 导航栏改造测试复盘（2026-07-22）

> 本节基于 v2 导航栏改造（折叠/展开双模式 + 12 图标导航）的 E2E 测试执行过程复盘，提炼可复用的固定流程与失败模式。

### 成功执行任务的完整步骤

| 步骤 | 操作 | 验证点 | 对应协议 |
|------|------|--------|----------|
| 1 | 端口监听检查（3000/5173） | 两端口均处于 Listen 状态 | Pre-flight Check |
| 2 | 健康检查（GET /health） | HTTP 200 响应 | Pre-flight Check |
| 3 | 浏览器启动检查（about:blank） | Playwright 环境可用 | Pre-flight Check |
| 4 | 停止占用端口的旧进程 | 无残留 cmd.exe / node.exe 占用端口 | Service Management |
| 5 | 启动后端 + 前端服务 | 端口在 startup_timeout_ms 内就绪 | Service Management |
| 6 | 执行阶段 1-6 测试用例 | 全部断言通过 | 标准流程 |
| 7 | 失败时按错误消息模式分类 | 输出对应修复建议 | Failure Classification |
| 8 | selector_not_found 自动触发同步检查 | 检测 git diff 选择器变更 | Test Case Sync |
| 9 | 测试后清理残留进程 | 无日志重定向 cmd.exe 残留 | Service Management |

### 不确定性与失败点

1. **ERR_CONNECTION_REFUSED**：服务未启动或启动未完成时，所有用例报连接拒绝 → 已由 Pre-flight Check 协议在测试入口拦截
2. **选择器失效**：v2 改造删除/重命名了 `.tab-btn` / `.nav-toggle` 等选择器后，旧测试用例引用失效 → 已由 Test Case Sync 协议在阶段 5 检测
3. **静默吞错**：测试用例 except 分支用 `pass` 吞掉异常，导致用例"假通过" → 已由 Test Case Sync 协议的 silent_failure_forbidden 检测
4. **端口冲突**：旧服务未停止即启动新服务，导致新服务绑定端口失败 → 已由 Service Management 协议的 stop_old_process 预防
5. **日志重定向残留**：`pnpm run dev > log.txt 2>&1` 产生的 cmd.exe 残留进程占用资源 → 已由 Service Management 协议的 cleanup_residual 清理

### 可抽象的固定流程

#### 前置检查流程（Pre-flight Check Flow）

```
端口检查 → 健康检查 → 浏览器检查 → (失败) 自动启动服务 → 轮询端口 → 通过/中止
```

该流程与具体业务无关，可作为所有 E2E 测试的统一入口。

#### 测试同步流程（Test Case Sync Flow）

```
git diff 选择器变更 → Grep 测试文件引用 → 命中失效引用 → 检测静默吞错 → 同 commit 验证 → 失败/通过
```

该流程与具体页面无关，可作为所有代码变更后的测试同步验证。

### 适用场景

- v2 导航栏改造后的回归测试（折叠/展开切换、12 图标导航、tooltip、localStorage 持久化）
- 服务重启或端口变更后的环境就绪验证
- 代码变更涉及 DOM 选择器删除/重命名时的测试同步检查
- 测试失败原因不明确时按错误消息模式自动分类
- 长时间测试流程中的服务生命周期管理

### 不适用场景

- 纯静态 HTML 页面（无服务启动需求，Pre-flight Check 仅需浏览器检查）
- 无 git 仓库的项目（Test Case Sync 的 git diff 扫描不适用）
- 单次性临时测试（Service Management 的残留清理不必要）
- 已知失败原因明确无需分类的场景（Failure Classification 的分类开销不必要）

## Version History

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v2.0.0 | 2026-07-22 | **Tauri 2.x 桌面应用测试复盘**：新增"Tauri 2.x 桌面应用测试（复盘提炼）"章节（含 6 阶段测试流程、invoke 权限三层验证、SPA 产物验证、阶段间 DAG 依赖关系、故障排查速查表）；新增 3 个参考文档（tauri-desktop-testing.md / spa-artifact-verification.md / invoke-permission-verification.md）；新增 templates/phase_tauri_desktop.py 测试阶段模板；config.yaml 与 defaults.yaml 新增 tauri / spa / health_check / invoke / disk_space / console_log 6 个配置块；核心配置块表追加 6 行 Tauri 相关条目。 |
| v1.7.0 | 2026-07-22 | 新增前置检查协议（Pre-flight Check Protocol）、测试用例同步协议（Test Case Sync Protocol）、失败分类协议（Failure Classification Protocol）、服务管理协议（Service Management Protocol）；追加 4 个动态引擎步骤类型（precheck / test_sync_check / failure_classify / service_manage）；追加 v2 导航栏改造测试复盘章节 |
| v1.8.0 | 2026-07-13 | **目录结构验证测试复盘**：新增"目录结构验证测试（复盘提炼）"章节（含 .gitignore 规则验证、目录结构完整性、脚本引用完整性、类型检查回归 4 个子项）；新增"搜索结果交叉验证协议"章节；config.yaml 新增 structure_verification 和 search_cross_verification 配置块 |
| v1.9.0 | 2026-07-22 | **文件夹上传批量编译 E2E 测试复盘**：新增"文件夹上传批量编译测试复盘"章节（含六阶段测试流程、4 个新配置块说明、阶段间 DAG 依赖关系）；defaults.yaml 新增 vite_proxy_check / port_conflict_resolution / compile_artifact_check / process_cleanup 配置块；基于 Vite proxy SSE 中断、端口冲突迁移、编译产物污染、日志重定向残留 4 类失败点的复盘提炼。 |

## 文件夹上传批量编译测试复盘（2026-07-22）

> 本节基于文件夹上传批量编译功能的 E2E 测试执行过程复盘，提炼可复用的六阶段测试流程与失败模式。

### 成功执行任务的完整步骤

| 步骤 | 操作 | 验证点 | 对应阶段 |
|------|------|--------|----------|
| 1 | 预检查（环境/端口/配置/PowerShell） | 所有预检项通过 | 阶段 1：预检查 |
| 2 | 服务启动（非阻塞模式） | 端口在 startup_timeout_ms 内就绪 | 阶段 2：服务启动 |
| 3 | API 端点测试（10 个端点） | 全部返回 200 | 阶段 3：动态验证 |
| 4 | 路由注册验证 + 类型同步验证 | 后端路由全部注册、前后端 types.ts 对齐 | 阶段 3：静态验证（并行） |
| 5 | UI 元素验证（11 个页面） | expected_elements 选择器全部存在 | 阶段 3：动态验证 |
| 6 | SSE 事件流验证 | batch_start→file_start→progress×8→file_done→file_complete→batch_done 完整 | 阶段 3：动态验证 |
| 7 | 编码乱码检测 + 危险操作测试 + 滚动容器测试 + SPA 跳转测试 + 检查更新测试 | 全部通过 | 阶段 4：专项验证 |
| 8 | 测试后清理（停止服务+清理临时文件） | 无残留进程 | 阶段 5：清理 |

### 不确定性与失败点

1. **端口占用冲突**：5173 被其他项目占用，被迫改用 5174，导致 config.yaml 中硬编码的 5173 失效 → 已由 port_conflict_resolution 配置块的自动迁移策略解决
2. **Vite proxy SSE 中断**：简写形式 `'/api': 'http://localhost:3000'` 缺少 changeOrigin/timeout，导致 SSE 长连接被中断，出现 'Failed to fetch' → 已由 vite_proxy_check 配置块检测
3. **PRESETS_PATH 路径解析错误**：api/src/routes/ai.ts:13 少一个 '../'，导致 llm-presets.json 找不到，API 启动崩溃 → 已由 compile_artifact_check 配置块检测路径解析
4. **PowerShell 5.1 语法限制**：不支持 &&/||，需用 ; 分隔 → 已由 powershell_compatibility 配置块检测
5. **bat 脚本 pause 阻塞**：自动化调用时 pause 等待用户按键 → 已由 bat_script.bypass_pause 配置解决
6. **日志重定向 cmd 进程残留**：taskkill 主进程后，日志重定向 cmd 仍持有句柄 → 已由 process_cleanup 配置块的 Get-CimInstance Win32_Process 命令行匹配清理
7. **Vite dev server 优先加载 .js 编译产物**：src 下同时存在 .ts 和 .js 时，Vite 直接读 .js 导致旧版代码被加载 → 已由 compile_artifact_check 配置块检测

### 可抽象的固定流程

#### 六阶段测试流程

```
阶段 1：预检查（环境/端口/配置/PowerShell）→ 并行执行
    ↓（全过才继续）
阶段 2：服务启动（非阻塞+端口轮询）
    ↓
阶段 3：动态验证（API+UI+SSE） ← 并行 → 静态验证（路由注册+类型同步）
    ↓（API+UI 通过才继续）
阶段 4：专项验证（编码+危险操作+滚动+SPA+检查更新）
    ↓
阶段 5：清理（停止服务+清理临时文件）
```

#### 故障分类与诊断决策树

```
服务未启动 → 检查端口占用+旧进程残留（process_cleanup）
SSE 中断 → 检查 Vite proxy 配置（vite_proxy_check：简写形式 vs 对象形式）
API 崩溃 → 检查路径解析（compile_artifact_check：import.meta.url vs process.cwd）
类型不同步 → 检查前后端 types.ts interface 字段（type_sync_check）
```

### 适用场景

- Vue 3 + Vite + Fastify 全栈项目
- SPA 手动路由（无 vue-router）项目
- SSE 长连接项目
- 多主题切换项目
- Windows PowerShell 环境项目

### 不适用场景

- 纯后端项目（无前端 UI 元素验证）
- 使用 vue-router 的 SPA（路由注册验证逻辑不同）
- Linux/macOS 环境（PowerShell 约束不适用，需改为 bash 兼容）
- 无 SSE 的项目（SSE 事件流验证不适用）
- 容器化部署项目（服务生命周期由容器编排管理，不需手动启停）

### 阶段间 DAG 依赖关系

测试阶段间存在有向无环图（DAG）依赖关系：

| 阶段 | 依赖前置阶段 | 故障传播规则 |
|------|-------------|-------------|
| 预检查 | 无（并行执行） | critical 故障中断后续所有阶段 |
| 服务启动 | 预检查全过 | critical 故障中断后续所有阶段 |
| API 端点测试 | 服务启动 | critical 故障中断 UI/SSE/专项验证 |
| 路由注册验证 + 类型同步验证 | 无（与服务启动并行，静态检查） | warning/suggestion 不中断 |
| UI 元素验证 + SSE 事件流验证 | 服务启动 + API 端点测试通过 | critical 故障中断专项验证 |
| 编码乱码检测 + 危险操作测试 + 滚动容器测试 + SPA 跳转测试 + 检查更新测试 | UI 元素验证通过 | warning/suggestion 不中断 |
| 测试后清理 | 最后执行（无论前序成败） | 必须执行 |

关键规则：
- **critical 故障**从任意阶段向上传播，中断后续依赖阶段
- **warning/suggestion**不中断后续阶段
- **测试后清理**必须执行（即使前序阶段失败）

### 新增配置块说明

#### vite_proxy_check（Vite Proxy 配置检查）

检测 Vite proxy 配置是否为对象形式（含 changeOrigin/timeout/proxyTimeout），避免 SSE 长连接中断。

#### port_conflict_resolution（端口冲突自动迁移）

配置端口被占用时的自动迁移策略（检测实际可用端口并更新 config）。

#### compile_artifact_check（编译产物污染检测）

检测 src 下是否同时存在 .ts 和 .js 文件，避免 Vite 加载旧编译产物；检测路径解析是否采用 import.meta.url 三级策略。

#### process_cleanup 增强（进程残留清理增强）

在 service_lifecycle 基础上增强：日志重定向 cmd 残留清理策略（Get-CimInstance Win32_Process 命令行匹配）。

## Tauri 2.x 桌面应用测试（复盘提炼）

> 本节基于 Tauri 2.x 桌面应用集成测试过程复盘提炼，覆盖从环境预检到错误诊断的完整测试流程。
> 所有参数从 `config.tauri` / `config.spa` / `config.health_check` / `config.invoke` / `config.disk_space` / `config.console_log` 读取，不在代码中硬编码。
> 详见 [tauri-desktop-testing.md](references/tauri-desktop-testing.md)。

### 适用场景

- Tauri 2.x 桌面应用（含 SPA 前端 + Rust 后端）
- 通过 `@tauri-apps/api` 的 `invoke` 调用 Rust 命令的 IPC 场景
- 需要验证 SPA 产物与源码同步的场景
- 需要验证 capabilities.json 权限声明完整性的场景
- Windows / macOS / Linux 跨平台构建验证

### 不适用场景

- 纯 Web 项目（用 SKILL.md 主流程的标准 6 阶段测试）
- Tauri 1.x 项目（配置结构不同，需另行适配）
- 无 invoke 调用的简单 Tauri 项目（invoke 权限验证不适用）

### 测试流程（6 阶段）

仅在 `tauri.enabled: true` 时执行。与 SKILL.md 主流程的标准 6 阶段测试并行或串行。

#### 阶段 1：测试前预检

| 子阶段 | 验证内容 | 通过条件 |
|--------|----------|----------|
| 1.1 环境验证 | cargo / LLD / windres / 磁盘空间 | 全部工具可用且磁盘空间 ≥ 阈值 |
| 1.2 SPA 产物时间戳验证 | 源码 mtime vs 产物 mtime | 产物 mtime ≥ 源码 mtime |
| 1.3 SPA 产物特征验证（可选） | JS chunk 中含关键字符串 | 全部关键字符串命中（`spa.require_all_keys: true`） |
| 1.4 端口占用检查 | required_ports 是否被占用 | 全部端口空闲（或已停止占用进程） |

#### 阶段 2：构建与启动

| 子阶段 | 验证内容 | 通过条件 |
|--------|----------|----------|
| 2.1 SPA 构建 | 执行构建脚本 + 验证 index.html | 构建退出码 0 且产物非空 |
| 2.2 Rust 编译 | cargo build + 验证 exe 存在 | 编译退出码 0 且 exe 文件存在 |
| 2.3 Tauri 应用启动 | 非阻塞启动 + 进程存活检查 | 进程在 startup_timeout_ms 内未退出 |
| 2.4 后端健康检查 | 轮询 health_check.endpoint | HTTP 响应状态码 == expected_status |

#### 阶段 3：功能验证

| 子阶段 | 验证内容 | 通过条件 |
|--------|----------|----------|
| 3.1 窗口创建验证 | Get-Process + MainWindowTitle | 进程存活且窗口标题匹配 |
| 3.2 invoke 权限验证 | 三层权限检查（插件依赖/权限声明/URL 白名单） | 三层验证全部通过 |
| 3.3 交互功能验证（可选） | DevTools Protocol 连接 + 元素断言 | 全部用例断言通过 |

#### 阶段 4：错误诊断

| 子阶段 | 验证内容 | 通过条件 |
|--------|----------|----------|
| 4.1 Tauri stderr 日志采集 | 按 error_keywords 扫描 stderr 日志 | 不含任何错误关键词 |
| 4.2 DevTools Console 日志采集 | 静态分析前端 invoke 调用与 Rust 命令注册 | 全部 invoke 命令已注册 |
| 4.3 invoke 错误分类 | 按 failure_classification.rules 匹配错误消息 | 无规则匹配（即无错误） |

> 阶段 4 在阶段 3 失败时仍需执行，用于诊断根因。

#### 阶段 5：结果汇总

输出 PASS/FAIL/SKIP 报告，每条失败项包含：
- 失败的断言名称
- 实际值 vs 期望值
- 匹配的失败分类规则
- 对应的修复建议

#### 阶段 6：测试后清理

- 停止 Tauri 进程（terminate → kill → Stop-Process 兜底）
- 清理临时日志文件（_tauri_stdout.log / _tauri_stderr.log）

### 阶段间 DAG 依赖关系

| 阶段 | 依赖前置阶段 | 故障传播规则 |
|------|-------------|-------------|
| 阶段 1 预检 | 无（并行执行） | critical 故障中断后续所有阶段 |
| 阶段 2 构建与启动 | 阶段 1 全过 | critical 故障仍执行阶段 4 诊断后中断 |
| 阶段 3 功能验证 | 阶段 2 通过 | critical 故障仍执行阶段 4 诊断 |
| 阶段 4 错误诊断 | 阶段 3 失败或 console_log.enabled | 必须执行（用于诊断根因） |
| 阶段 5 结果汇总 | 阶段 1-4 完成 | 必须执行 |
| 阶段 6 测试后清理 | 最后执行（无论前序成败） | 必须执行 |

### invoke 权限三层验证

> Tauri 2.x 的 invoke 权限模型与 1.x 不同，必须在 `capabilities/*.json` 中显式声明。详见 [invoke-permission-verification.md](references/invoke-permission-verification.md)。

| 层级 | 验证内容 | 失败类型 | 修复建议 |
|------|----------|----------|----------|
| 第 1 层 | Cargo.toml 含 `tauri-plugin-{name}` 依赖 | `invoke_layer_1` | 添加插件依赖并重新编译 |
| 第 2 层 | capabilities.json 的 permissions 数组含 `allow-xxx` | `invoke_layer_2` | 在 permissions 数组中添加 `allow-xxx` |
| 第 3 层 | capabilities.json 的 remote.urls 匹配测试 URL | `invoke_layer_3` | 在 remote.urls 中添加 URL 模式 |

错误关键词映射（运行时错误诊断）：

| 错误消息关键词 | 失败层级 | 修复建议 |
|----------------|----------|----------|
| `Plugin not found` | 第 1 层 | 在 Cargo.toml 添加插件依赖 |
| `not allowed` | 第 2 层 | 在 capabilities.json 添加 allow-xxx |
| `URL: local` | 第 3 层 | 在 remote.urls 添加 URL 模式 |
| `command not found` | 命令注册 | 在 lib.rs 的 invoke_handler 注册命令 |
| `serialization error` | 类型不匹配 | 检查 Rust 命令参数与前端 invoke 参数类型 |

### SPA 产物验证

> 防止源码已修改但产物未重建导致 Tauri 加载旧版前端。详见 [spa-artifact-verification.md](references/spa-artifact-verification.md)。

| 验证法 | 原理 | 适用场景 |
|--------|------|----------|
| 时间戳对比法 | 源码 mtime vs 产物 mtime | 主方法，日常构建验证 |
| JS chunk 特征验证法 | 在产物 JS 中搜索关键字符串 | 辅助方法，CI 环境 mtime 重置时 |

### 新增配置块说明

#### tauri（Tauri 桌面应用配置）

Tauri 2.x 桌面应用构建/启动/窗口验证参数。包含 exe_name、src_tauri_dir、build_script_path、expected_window_title、startup_timeout_ms、compile_timeout_sec。

#### spa（SPA 产物验证配置）

防止源码已修改但产物未重建。包含 source_dirs、output_dir、source_extensions、key_strings、force_rebuild。

#### health_check（后端健康检查配置）

Tauri 启动后轮询后端服务健康检查端点。包含 endpoint、retry_count、timeout、expected_status。

#### invoke（invoke 权限验证配置）

Tauri 2.x invoke 调用的三层权限验证。包含 commands、permissions、url_patterns、capabilities_glob、cargo_toml_path。

#### disk_space（磁盘空间检查配置）

Rust 编译产物与 node_modules 占用大，必须预检磁盘空间。包含 debug_min_gb、release_min_gb、cleanup_threshold_gb。

#### console_log（Console 日志采集配置）

Tauri stderr 与 DevTools Console 日志的关键词过滤与错误分类。包含 prefixes、error_keywords。

### 测试编排示例

在 `config.yaml` 的 `test_plan.phases` 中编排 Tauri 桌面测试步骤：

```yaml
test_plan:
  enabled_phases:
    - "build"
    - "startup"
    - "basic"
    - "interactions"
    - "supplementary"
    - "summary"
    - "tauri_desktop"  # 新增 Tauri 桌面测试阶段

tauri:
  enabled: true
  exe_name: "karpathy-wiki"
  src_tauri_dir: "karpathy-wiki/src-tauri"
  build_script_path: "karpathy-wiki/scripts/前端构建.bat"
```

### 故障排查速查表

| 现象 | 可能原因 | 验证阶段 | 修复步骤 |
|------|----------|----------|----------|
| Tauri 启动后立即退出 | Rust 编译错误或窗口配置错误 | 阶段 2 / 阶段 4 | 查看 stderr 日志中的 `panicked at` |
| 窗口创建但白屏 | SPA 产物未构建或路径错误 | 阶段 1.2 / 阶段 4 | 重新构建 SPA，检查 `frontendDist` 配置 |
| invoke 调用报 `Plugin not found` | Cargo.toml 缺少插件依赖 | 阶段 3.2 / 阶段 4 | 添加 `tauri-plugin-xxx` 依赖并重新编译 |
| invoke 调用报 `not allowed` | capabilities.json 缺少权限声明 | 阶段 3.2 / 阶段 4 | 在 `permissions` 数组中添加 `allow-xxx` |
| invoke 调用报 `URL: local` | remote.urls 未匹配测试 URL | 阶段 3.2 / 阶段 4 | 在 `remote.urls` 中添加 URL 模式 |
| 后端健康检查超时 | 后端服务未在 Tauri 启动时初始化 | 阶段 2.4 | 增加 `health_check.retry_count` |
| 编译报 `linker 'lld-link' not found` | 缺少 LLD 链接器 | 阶段 1.1 / 阶段 2.2 | 安装 LLVM 或改用 `msvc-link` |
