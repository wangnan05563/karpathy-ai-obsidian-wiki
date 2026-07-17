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

## 测试流程（6 阶段）

### 阶段 1：构建
读取 uild.script_path → 执行构建 → 验证产物 index.html 存在

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
| esponsive_check | - | 响应式布局检查 |
| console_check | - | 控制台错误检查 |
| persistence_crud_test | resource, test_id, payload | 持久化层 CRUD 全生命周期 + PUT 后立即 GET 对比（验证缓存刷新） |
| path_traversal_test | resource, malicious_ids | 路径穿越防护测试（非法 ID 必须返回 4xx） |
| fallback_degradation_test | api_patterns, expected_behavior, wait_ms | 降级测试（拦截 API 返回 503，验证前端不崩溃） |
| encoding_check | check_pages, scan_selectors, fffd_codepoint | 编码检测：dump DOM 文本码点，检查是否含 U+FFFD 替换字符 |
| dangerous_action_test | test_pages, forms, confirm_component | 危险操作完整测试：dry_run 默认值 → danger 样式 → 二次确认 → 取消 → 执行 |
| multi_form_test | test_pages, form_container_selector, loading_selector, result_selector | 多表单独立状态测试：验证每表单独立 loading/result，互不干扰 |
| service_lifecycle | stop_old_process, start_backend, start_frontend, required_ports | 服务生命周期：停止旧进程 → 启动新服务 → 验证端口监听 |
| temp_cleanup | temp_files_pattern, temp_screenshots_pattern, cleanup_dirs | 临时文件清理：按 pattern 删除测试产生的临时脚本和截图 |

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

## 适用场景

- Vue 3 / React / Angular 等 SPA 应用
- Vite / Webpack 构建的前端项目
- 有独立后端 API 的全栈项目
- Element Plus / Ant Design 等组件库项目
- Windows 环境下的 Playwright 测试
- **有编码风险的 Windows 中文环境**（页面 tab/标签可能乱码，需用 Unicode 码点验证）
- **有危险操作（dry_run/二次确认/danger 样式）的清理类模块**
- **多表单独立状态管理（每表单独立 loading/result）的模块**

## 不适用场景

- 纯静态 HTML 页面
- 移动端 App 测试
- 需要 OAuth/SSO 认证的页面
- SSR 应用（渲染时机不同）
- WebSocket 密集的应用
- **无前端界面的纯 API 测试**（用 `persistence_crud_test` / `path_traversal_test` 替代）

## 故障排查

常见问题及解决方案见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。重点关注：

- **编码乱码（U+FFFD）**：见 TROUBLESHOOTING 第 11 条，用 Unicode 码点匹配替代终端字符串匹配
- **Playwright 中文匹配失败**：见 TROUBLESHOOTING 第 12 条，避免 `has_text` 中文，改用 `get_dom_text_codepoints` 比对码点
- **端口占用**：见 TROUBLESHOOTING 第 13 条，用 `service_lifecycle.stop_old_process: true` 启动前清理
- **bat 脚本 pause 卡住**：见 TROUBLESHOOTING 第 14 条，配置 `powershell_constraints.bypass_bat_pause: true`
- **GPU 崩溃**：见 TROUBLESHOOTING 第 15 条，`browser.launch_args` 必须含 `--disable-gpu`
- **Python 文件编码声明缺失**：见 TROUBLESHOOTING 第 16 条，所有 .py 文件首行加 `# -*- coding: utf-8 -*-`
