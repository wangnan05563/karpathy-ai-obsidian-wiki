---
name:。 wiki-frontend-code-review
description: "Review Vue 3 + Element Plus + Pinia frontend code for the wiki project. Invoke when user asks to review, analyze, or improve frontend files (e.g., .vue, .ts) under frontend/. Covers Vue Composition API, Element Plus, Pinia, performance, and type safety."
---

# Wiki Frontend Code Review

## Intent
Use this skill whenever the user asks to review, analyze, or improve frontend code of the wiki project (especially `.vue` / `.ts` / `.tsx` files under `frontend/`). Support three review modes:

1. **Pending-change review** – inspect staged/working-tree files slated for commit and flag checklist violations before submission.
2. **File-targeted review** – review the specific file(s) the user names and report the relevant checklist findings.
3. **Code snippet review** – review code snippet pasted by the user (no file path context, focus on pattern correctness).

Scope and non-goals (backend code, build scripts, config files) are defined in [config/review-config.md](config/review-config.md) under "适用 / 不适用场景". When in doubt about whether a file is in scope, consult that section first.

### Historical Incident Coverage

本技能规则集已纳入以下历史问题的复盘规则，审查时须重点关注：

| 历史问题 | 对应规则 | 规则编号 |
|---------|---------|---------|
| App.vue 中文标签乱码（编码损坏 U+FFFD） | encoding-safety-rule.md | ES-6 |
| 前后端 types.ts 不同步（TunnelConfig 接口缺失） | type-sync-frontend-rule.md | TS-1 |
| Tab/视图未注册（Tunnel.vue 未在 App.vue 四处注册） | route-registration-frontend-rule.md | RR-1 |
| 破坏性按钮未防护（启动/停止/保存被自动测试触发） | dangerous-action-rule.md | DA-8 |
| 敏感字段明文回显（authtoken 直接绑定到输入框） | sensitive-field-display-rule.md | SF-1 |
| Help.vue 章节卡片仅显示标题（双重滚动裁切） | scroll-container-rule.md | SC-1 |
| About→Help 跨组件跳转缺失 CustomEvent 派发 | spa-navigation-rule.md | SN-1 |
| 检查更新状态机不完整 + 定时器未清理 | update-check-rule.md | UC-1/UC-2 |
| 禁用按钮仅 CSS 置灰（Playwright 点击超时） | encoding-safety-rule.md | ES-7 |
| UI 文案与测试断言不同步（"AI 服务" vs "AI 配置"） | encoding-safety-rule.md | ES-8 |
| 主题/预设数量硬编码 | encoding-safety-rule.md | ES-9 |
| async 请求无超时/无降级/定时器未清理 | async-reliability-rule.md | AR-1~AR-4 |
| vue-tsc 幽灵错误用 as any / ! / @ts-ignore 绕过 | typecheck-cache-frontend-rule.md | FR-026 |
| 未读 useXxx 源码误用 ref/reactive + 诊断用 $dispose / _s.delete 重建 store | composable-api-frontend-rule.md | FR-027 |
| 联合类型 T\|U 升级用 as unknown as 强转，运行时缺字段 | mixed-type-dispatch-frontend-rule.md | FR-028 |
| .vue 双 script 块（为声明 name 引入 Options 写法） | sfc-single-script-frontend-rule.md | FR-029 |
| E2E 测试未做端口+健康检查，首用例 ERR_CONNECTION_REFUSED 失败 | e2e-precheck-frontend-rule.md | FR-030 |
| DOM 结构变更后测试选择器失效（侧栏折叠/展开/标签替换） | dom-compat-class-frontend-rule.md | FR-056 |
| calc(100vh - Xpx) 在布局变更后失效（删除导航/页脚后底部留白） | flex-viewport-adapt-frontend-rule.md | FR-057 |
| 多态状态机未简化（三态折叠需两次点击） | state-machine-simplify-frontend-rule.md | FR-058 |
| 恢复删除功能时破坏性 Write 重写整个文件（编码风险） | rollback-minimal-frontend-rule.md | FR-060 |
| Query/Reader 标题头占比过大 + 输入区未 sticky 毛玻璃 | reading-viewport-frontend-rule.md | FR-032 |
| 前端构建产物（dist/）混入源码目录或 services/api/public/ 未 gitignore；检查 services/api/public/ 是否在 .gitignore 中；构建产物是否 git rm --cached | 目录结构分离 | FR-033 |
| 测试截图/临时产物未 gitignore；检查 test_screenshots/ 和 test_*.json 是否在 .gitignore 中 | .gitignore 完整性 | FR-034 |
| 硬编码 rgba()/#hex 颜色值未替换为 CSS 变量（.recent-log 深色背景在浅色主题下辨识度低） | theme-color-mapping-frontend-rule.md | FR-035 |
| alpha 变体变量名不符合 --accent-{color}-a{NN} 规范（使用未定义的 a07 等值） | theme-color-mapping-frontend-rule.md | FR-036 |
| 语义变量选择错误（场景背景硬编码值映射为卡片背景变量，导致对比度不足） | theme-color-mapping-frontend-rule.md | FR-037 |
| 含中文 .vue 文件被 Write 重写而非 Edit 精准替换（中文注释被破坏为 GBK 字节） | theme-color-mapping-frontend-rule.md | FR-038 |
| 类型变更仅运行前端 vue-tsc，后端 tsc --noEmit 未通过（API 契约不匹配） | theme-color-mapping-frontend-rule.md | FR-039 |
| 多主题切换后部分元素在浅色/深色主题下对比度不足（未切换主题验证） | theme-color-mapping-frontend-rule.md | FR-040 |
| Tauri invoke 命令三层声明缺失（build.rs/capabilities/lib.rs 任一层漏写 → 运行时 'Plugin not found' / 'not allowed'） | tauri-invoke-rule.md | FR-041 |
| 透明窗口 CSS 仅覆盖 body（html/#app/通配符缺失 → 窗口边缘白边 / floating-active 状态背景残留） | tauri-transparent-css-rule.md | FR-042 |
| drag+click 元素误用 data-tauri-drag-region（原生拦截 mousedown → click 永不触发 / 阈值硬编码 / start_dragging 重复调用） | tauri-drag-click-rule.md | FR-043 |
| Playwright 选择器不精确（placeholder 匹配失败/多元素误匹配）+ networkidle 超时（背景图阻塞） | test-selector-priority-rule.md | FR-044 |
| 工具栏控件数 > 5 未分层 + 折叠面板放在 button-bar 内导致布局抖动 | control-layering-frontend-rule.md | FR-045 |
| Mermaid/KaTeX/Prism 渲染非法语法白屏（缺库级配置/预校验/CSS 兜底） | third-party-error-guard-frontend-rule.md | FR-046 |
| click outside 未排除 teleport-to-body 组件导致折叠面板误关闭 | folding-panel-event-frontend-rule.md | FR-047 |
| 视频生成（长任务）误用 SSE 流导致超时断开 + 所有错误统一"后端服务未运行" | long-task-architecture-frontend-rule.md | FR-048 |
| SSE 事件 if/else if 链分发 6 种事件认知复杂度超标 + outputMode/outputModes 混用 | sse-event-dispatch-frontend-rule.md | FR-049 |
| SSE 流消费未吞掉 AbortError 污染 errorMessage + finally 未 reader.cancel 兜底 | sse-stream-error-frontend-rule.md | FR-050 |
| 长任务轮询用 AbortSignal.timeout 无法同步标记 abortReason + 关闭/重置合为一个函数 | long-task-polling-ui-frontend-rule.md | FR-051 |
| v-html 渲染内容绑 @click 失败 + onBeforeUnmount 未移除监听器 + 库实例未销毁 | event-delegation-frontend-rule.md | FR-052 |
| mermaid/marpit 重库顶层静态导入致首屏 bundle 膨胀 + CJS 命名导出位置不确定 | heavy-library-frontend-rule.md | FR-053 |
## Context Loading Strategy

Follow the loading sequence in [skill-loader.md](skill-loader.md) to minimize context tokens.

### 1. Baseline (always load)
- [SKILL.md](SKILL.md) — this file
- [config/review-config.md](config/review-config.md) — project thresholds, tech stack, conventions

### 2. Rule routing (load selectively)
Read [skill-loader.md](skill-loader.md) once (~3KB) to determine which rule files apply:
1. Match target file extension against `file_patterns[].pattern`
2. Scan the first 50 lines for category keywords (see skill-loader.md)
3. Load only matched rule files from `rule_categories[].file`
4. Load corresponding examples files only when generating fix code

### 3. On-demand examples
Only load `references/examples/{category}-examples.md` when:
- Generating specific code fixes
- The rule description needs Wrong/Right comparison

This selective loading typically reduces context from ~13k to ~6-8k tokens per review.



Stick to the checklist below for every applicable file and mode. Do not invent rules outside the catalog.

## Checklist

Use [skill-loader.md](checklist-index.md) for the complete rule overview and quick routing table.

### Loading Procedure
1. Read [skill-loader.md](checklist-index.md) once to understand all rules and their dependencies
2. Match target files against the quick routing table to select applicable rules
3. Load [config/review-config.md](config/review-config.md) for thresholds and conventions
4. Load matched rule files from the checklist
5. Load examples files only when generating specific fix code

All configurable parameters (directory mapping, tech stack, performance thresholds, SSE event types) live in [config/review-config.md](config/review-config.md). Rule files describe general patterns only and reference the config for concrete values — never hardcode thresholds in rule files.

Flag each rule violation with urgency metadata so future reviewers can prioritize fixes.

## Review Process

### Mode Detection
First, determine the review mode from the user request:

- **pending-change review**: User mentions staged/working-tree files, git diff, or commit prep. Use diff-aware mode.
- **file-targeted review**: User names specific files. Use full-file mode.
- **code snippet review**: User pastes code without file path. Use pattern-only mode (check patterns, skip cross-file rules).
- **auto-detect**: If unclear, check `git status` / `git diff --cached` to see if there are pending changes.

### Diff-Aware Mode (for pending changes)

When reviewing staged or working-tree files:

1. **Get diff first**: Run `git diff --cached` (staged) or `git diff` (working tree) to identify changed files and lines.
2. **Extract context**: For each changed file, read only the diff hunks + 5 lines of surrounding context. Do NOT read the entire file.
3. **Route rules**: Use the quick routing table in [skill-loader.md](skill-loader.md) to determine which rule files apply to the changed areas.
4. **Targeted review**: Apply rules only to changed lines and their immediate context. Mark unchanged code as "verified, skip."
5. **Track cumulative issues**: If reviewing the same file across multiple commits, note pre-existing issues separately.

### Full-File Mode (for file-targeted or auto-detect with no diff)

1. **定位文件**：定位待评审的 `.vue` / `.ts` / `.tsx` 文件，按 `config/review-config.md` 的目录映射确认其在 `frontend/` 范围内；不在范围内则跳过并说明原因。
2. **读取配置**：打开 [config/review-config.md](config/review-config.md) 获取当前的技术栈版本、性能阈值、SSE 事件类型约定、组件设计规范、主题色系统配置。
3. **路由规则**：根据文件路径与内容特征，匹配上表中的规则文件；一个文件可能命中多个规则文件，均需逐条核对。
4. **判断偏离**：对每条规则，记录代码偏离的具体位置（文件路径 + 行号）与一段代表性代码片段。需要参考示例时，加载规则文件中链接的 examples 文件。
5. **跨文件一致性检查**：除单文件规则外，须执行以下跨文件审查（参考 config/review-config.md 的对应配置段）：
   - **前端视图注册（RR-1）**：若评审范围涉及 `views/*.vue` 新增或 `App.vue` 修改，按 `views_directory` 列出全部视图，对比 `app_entry` 中的 import / ViewName 类型 / v-for 数组 / v-else-if 分支是否齐全。
   - **前后端类型同步（TS-1）**：若评审范围涉及 `types.ts` 修改或新增后端接口调用，按 `backend_types_path` 与 `frontend_types_path` 对比 export interface 字段名/类型一致性。
   - **敏感字段展示（SF-1）**：若评审范围涉及表单类 `.vue` 文件，扫描 `<el-input>` / `<input>` 是否有匹配 `sensitive_field_patterns` 的字段，检查回显策略是否符合 `display_strategy`。
   - **编码损坏扫描（ES-6）**：对所有评审文件，按 `check_replacement_char` 扫描 `U+FFFD` 替换字符，超过 `replacement_char_threshold` 即告警。
   - **破坏性按钮防护（DA-8）**：对所有评审的 `.vue` 文件 `<template>` 段，扫描匹配 `destructive_button_patterns` 的按钮，检查是否满足 `required_guards` 至少其一。
   - **滚动容器单一职责（SC-1）**：若评审范围涉及含 `overflow-y: auto` 的 `.vue` / `.css` 文件，按 `scroll_container.outer_scroll_selectors` 识别外层滚动容器，统计容器链路上 `overflow-y: auto` 嵌套层数是否超过 `scroll_container.max_overflow_layers`；检查 `flex-direction: column + flex: 1` 容器内的自然高度子项是否设 `flex-shrink: 0`。
   - **SPA 内部跳转（SN-1）**：若评审范围涉及含跨组件视图跳转的 `.vue` 文件（如 About → Help），检查是否通过 `CustomEvent` 派发 `spa_navigation.event_name_pattern` 事件；入口组件 `spa_navigation.app_entry` 是否在 `onMounted` / `onBeforeUnmount` 配对管理监听器。
   - **检查更新状态机（UC-1/UC-2/UC-3）**：若评审范围涉及检查更新功能（含 `setInterval` / `checkUpdate` / `updateState`），验证状态机覆盖 `check_update.required_states` 全部状态、定时器在 `check_update.cleanup_hook` 中清理、轮询间隔 ≥ `check_update.cache_ttl_ms`。
   - **图标与导航栏（IN-1/IN-3）**：若评审范围涉及 `App.vue` 或导航栏组件，统计菜单项数量；若 > `icon_navigation.nav_threshold`（默认 7）检查是否实现折叠/展开双模式；扫描 SVG 图标的 `stroke`/`fill` 是否为 `currentColor`；验证折叠模式 tooltip 是否用纯 CSS hover；验证切换是否用 `<Transition mode="out-in">`；验证 `menuItems` 是否为单一数据源。
	   - **禁用元素显式属性（ES-7）**：对所有评审的 `.vue` 文件 `<template>` 段，扫描条件置灰的按钮/输入框，检查是否有 `:disabled` 绑定而非仅 CSS 类置灰。
	   - **UI 文案一致性（ES-8）**：若评审范围涉及文案变更，确认相关测试用例的断言文本同步更新。
	   - **多实例数据集中管理（ES-9）**：对所有评审文件，扫描硬编码的主题/预设/菜单数量或字面量数组，确认从配置/API 动态获取。
	   - **预设列表外置**：若评审范围涉及预设/配置模板的 `.vue` / `.ts` 文件，检查预设列表是否从后端 API 获取，禁止前端硬编码（参见 config-isolation-rule.md"预设列表必须从后端 API 获取"规则）。
	   - **Async 可靠性（AR-1~AR-4）**：对所有评审的 `.vue` / `.ts` 文件，执行以下检查：async 网络请求是否设超时（AR-1）；SSE 消费是否有心跳与重连（AR-2）；看门狗/轮询定时器是否在 onBeforeUnmount 清理（AR-3）；async 失败是否有降级 UI 反馈（AR-4）。
   - **类型检查缓存清理（FR-026）**：对所有评审的 `.vue` / `.ts` / `.tsx` 文件，扫描 `typecheck_cache_frontend.bypass_keywords` 关键字（as any / as unknown as / @ts-ignore / !. 非空断言）的新增行；若 vue-tsc 报告与源码收窄逻辑不一致（幽灵错误），按 `typecheck_cache_frontend.cache_cleanup_targets` 清缓存后重跑 `typecheck_command` 验证，禁止用断言绕过。
   - **Composable API 先读后用（FR-027）**：对所有评审的 `.vue` / `.ts` 文件中新增的 `useXxx` 调用，要求 PR 描述中贴出 composable 源码签名并核对返回值形状（ref/reactive/computed）；扫描 `composable_api_frontend.store_lifecycle_forbidden` 关键字（pinia._s.delete / $dispose / $reset），命中且不在 `diagnostic_allowlist_in_tests` 文件中即标记 Urgent。
   - **混合类型运行时分流（FR-028）**：对所有评审的 `.ts` / `.vue` 文件中含联合类型 `T | U` 消费的代码，核对是否用 `mixed_type_dispatch_frontend.required_dispatch_keywords`（typeof / in / isXxx）运行时分流且分支穷尽；扫描 `forbidden_casts`（as any / as unknown as）跨形态强转即标记 Urgent；联合类型每个成员须有对应单元测试。
   - **Vue SFC 单 script 块（FR-029）**：对所有评审的 `.vue` 文件，统计 `<script>` 块数量；超过 `sfc_script_block_frontend.allowed_script_count`（默认 1）时，检查额外块首行是否含 `exception_marker`（`// 例外：`）且理由在 `allowed_exceptions` 清单内；编译宏禁止在非 setup 块中调用；组件 name 须通过 `defineOptions({ name })` 声明。
   - **E2E 测试前置服务检查（FR-030）**：若评审范围涉及 `playwright.config.ts` / `e2e/setup.ts` / `conftest.py` / `test_*.py`，核对是否对 `e2e_precheck_frontend.required_ports` 列出的端口做 LISTEN 检查、对 `health_endpoints` 做 HTTP 2xx 健康检查、失败重试 `retry_count` 次后中止测试套件；测试报告须含独立 preflight 段，区分"服务未就绪"与"用例失败"。
   - **测试用例与代码结构同步（FR-031）**：若评审范围涉及 `.vue` / `.tsx` 文件 DOM 影响变更（class/id/data-testid/结构/文案/v-if），核对同 PR 中引用旧选择器的测试文件是否同步更新；扫描测试代码 `try/catch` / `try/except` 静默吞错模式，catch 块须含 `allowed_catch_terminators`（throw / test.fail / test.skip / pytest.fail）至少其一；选择器优先用 `data-testid` / `aria-label`，集中到 `selector_module`。
   - **阅读视野优化与输入区固定（FR-032）**：若评审范围涉及 `reading_viewport_frontend.target_views`（Query.vue / Reader.vue / Help.vue / ChatView.vue 等），核对标题头占比 ≤ `header_max_ratio`（0.15）、内容区 ≥ `content_min_ratio`（0.75）；输入区须 `position: sticky; bottom: 0;` + `backdrop-filter: blur()` + 半透明背景 + `z-index ≥ input_bar_min_zindex`（2），且必须在滚动容器外（同级兄弟元素而非子节点）。
   - **前端构建产物目录结构分离（FR-033）**：若评审范围涉及前端构建配置（`vite.config.ts` / `webpack.config.js`）或 `services/api/public/` 目录变更，检查 `services/api/public/`（或对应构建产物输出目录）是否在 `.gitignore` 中登记；若该目录下文件已被 git 跟踪，须先 `git rm --cached` 移除索引，仅添加 .gitignore 对已跟踪文件无效。
   - **测试截图与临时产物 .gitignore 完整性（FR-034）**：若评审范围涉及 E2E 测试或截图功能（`playwright.config.ts` / `test_*.py` / 截图相关代码），检查 `test_screenshots/` 和 `test_*.json` 是否在 `.gitignore` 中登记；运行时生成的测试产物不得入库。
   - **主题色变量映射合规性（FR-035）**：对所有评审的 `.vue` / `.css` / `.scss` 文件，扫描 `theme_color_mapping_frontend.forbidden_color_formats`（rgba()/rgb()/#hex/hsl()/hsla()）硬编码颜色值；命中后检查是否匹配 `whitelist_patterns`（rgba(255,255,255,*)/transparent/inherit/currentColor），未匹配的必须替换为 CSS 变量。
   - **alpha 变体命名合规性（FR-036）**：对所有评审的 `.vue` / `.css` / `.scss` 文件中新增的 `--accent-{color}-a{NN}` 变量引用，核对 `{NN}` 是否 ∈ `theme_color_mapping_frontend.allowed_alpha_values` 列表；变量名格式必须匹配 `alpha_variable_pattern` 模板；`{color}` 必须 ∈ `color_identifiers` 列表。
   - **语义变量选择正确性（FR-037）**：对所有评审的 `.vue` / `.css` / `.scss` 文件中新增的 CSS 变量引用，按 `theme_color_mapping_frontend.semantic_priority` 顺序验证语义用途：页面背景须用 `--bg-scene`、卡片/面板背景须用 `--bg-card-solid`、文字须用 `--text-base`/`--text-muted`、边框须用 `--accent-{color}-a15`、阴影/光晕须用 `--glow-{color}`、滚动条须用 `--accent-{color}-a20`/`a40`；禁止跨语义层选择变量。
   - **编辑工具使用合规性（FR-038）**：若评审范围为 pending-change 模式，检查 `git diff` 中单个 `.vue` / `.ts` 文件的修改行数占比；若修改行数 > 文件总行数 × `edit_threshold_ratio`（默认 0.5）且文件含非 ASCII 字符，标记为「疑似使用 Write 重写」，建议改用 Edit 分块精准替换；含中文文件被 Write 重写可能导致 GBK 字节留存。
   - **类型检查通过性（FR-039）**：若评审范围涉及 `.ts` / `.vue` 文件类型变更，要求 PR 中包含 `theme_color_mapping_frontend.backend_typecheck_command`（tsc --noEmit）与 `frontend_typecheck_command`（vue-tsc --noEmit）的双重通过截图或 CI 日志；`require_both_pass` 为 true 时缺失任一即标记 Urgent。
   - **多主题视觉一致性（FR-040）**：若评审范围涉及 CSS 变量引用或主题色适配，要求 PR 描述中包含 `theme_color_mapping_frontend.test_themes` 列出的所有主题切换截图（macaron/enterprise/portfolio 浅色 + creative/product 深色）；缺失任一主题截图标记为 Suggestion；截图须能证明元素在对应主题下对比度可读。
   - **Tauri invoke 三层声明（FR-041）**：若评审范围涉及 Tauri 桌面应用前端代码（含 `invoke('xxx')` 调用），按 `tauri_invoke_frontend.build_manifest_path` / `capabilities_path` / `runtime_handler_path` 三层文件对照检查命令名是否齐全；命中 `plugin_command_allowlist` 中的插件命令（如 `start_dragging`）跳过；缺失任一层即标记 Urgent，并输出对应 `error_keyword_layer1/2/3` 错误关键词以便运行时排查。
   - **Tauri 透明窗口 CSS 覆盖（FR-042）**：若评审范围涉及 Tauri 桌面应用且 `tauri_transparent_css_frontend.tauri_conf_path` 中 `app.windows[].transparent = true`，扫描全局 CSS 与 `.vue` `<style>` 块，按 `required_transparent_layers`（html/body/#app/*）逐层核对 `background-color: transparent`；检查 `:global(html.{floating_active_class} *)` 通配符规则是否带 `!important`；扫描 `forbidden_transparent_properties`（opacity:0/visibility:hidden）误用；毛玻璃卡片（`glass_card_selectors`）须有显式背景且 alpha ≥ `glass_card_min_alpha`。
   - **Tauri drag+click 冲突处理（FR-043）**：若评审范围涉及 Tauri 桌面应用前端代码中含 `data-tauri-drag-region` 属性或 `invoke('start_dragging')` 调用的元素，扫描该元素是否同时绑定 `@click` / `@dblclick` —— 若有则标记 Urgent（须改用三阶段 mousedown/mousemove/mouseup 处理）；核对 `move_threshold_px` 是否从 config 读取而非硬编码；核对 `start_dragging_command` 命令名一致性；核对 `prevent_duplicate_invoke` 是否用 `dragStarted` 标志防重复调用。
   - **控件分层原则（FR-045）**：若评审范围涉及含工具栏（button-bar）+ 折叠面板的 .vue 文件，按 control_layering_frontend.button_bar_selector 定位工具栏容器，统计直接子级控件数是否超过 	hreshold（默认 5）；按 panel_root_selectors 定位折叠面板根元素，核对 DOM 父级链是否在 utton_bar_selector 内（须移出）且在 input_area_selector 内（须挂入）；检查折叠面板的 -if/-show 是否被 <Transition> 包裹且 
ame 以 	ransition_name_prefix 为前缀；检查触发按钮是否有 ria-expanded + 激活态 class；检查面板根元素及内部控件是否绑定 @mousedown.stop。
   - **第三方库错误防护（FR-046）**：若评审范围涉及 Mermaid/KaTeX/Prism 等第三方库渲染调用（	hird_party_error_guard_frontend.libraries 列出），核对库级配置层（suppress_config_keys 是否设置）、预校验层（parse_method_names 是否在渲染前调用）、CSS 兜底层（error_css_classes 是否在全局样式中定义）三层防护是否齐全；核对渲染前是否清空容器（equire_container_clear）；若库版本变更（ersion_change_files 中文件）要求 PR 描述含验证段；核对 LLM 流式输出（llm_source_patterns）是否经预校验后进入库渲染。
   - **折叠面板事件冲突（FR-047）**：若评审范围涉及含 click outside 实现的 .vue 文件（click_outside_patterns 命中），核对回调是否对 event.target 调用 closest(click_outside_exclude_selectors + teleport_selectors) 排除面板内控件与 teleport 组件；若折叠面板内含 <el-dropdown>，核对是否设 :hide-on-click="false"（equired_dropdown_props）；核对 <el-dropdown-menu> 是否绑定 @click.stop + @mousedown.stop（equired_event_modifiers）；核对面板根元素是否绑定 @mousedown.stop；核对 	eleport_selectors 列表是否覆盖项目实际使用的 teleport 组件。
   - **长短任务架构分离（FR-048）**：若评审范围涉及调用后端任务端点的 `.vue` / `.ts` 文件，核对任务名是否 ∈ `long_task_architecture_frontend.long_task_names` 却用 `EventSource` / `consumeSSEStream` 消费（须改 POST 创建 + GET 轮询）；核对 fetch/axios 的 response 处理是否按 `status_code_strategy` 分类（400=配置缺失引导 / 500=外部失败重试 / 429=限流 / 5xx=服务异常），禁止统一"后端服务未运行"；核对 SSE 流任务 finally 块是否有 `reader.cancel()` + 轮询任务是否暴露 `cancel()` 方法；核对创建任务用 POST、查询用 GET。
   - **SSE 事件对象映射分发（FR-049）**：若评审范围涉及 SSE 事件处理的 `.vue` / `.ts` 文件，核对事件类型数 ≥ `sse_event_dispatch_frontend.object_dispatch_threshold`（默认 3）时是否用 `Record<string, Handler>` 对象映射表替代 if/else if 链；核对 outputMode 类型是否为联合字面量类型（`'normal' | 'mindmap' | ...`）而非 string/enum；核对 outputMode（结构模式）与 outputModes（事件可见性）是否正交分离；核对未知事件是否有 default handler（`handlers[type] ?? defaultHandler`）；核对 handler 是否为独立具名函数引用。
   - **SSE 流消费错误处理（FR-050）**：若评审范围涉及 `consumeSSEStream` / `fetch stream` 的 `.ts` / `.vue` 文件，核对 catch 块是否吞掉 AbortError（`err.name === 'AbortError'` 直接 return）；核对调用方是否用 `abortReason` 三态（`'user' | 'timeout' | null`）管理停止原因，禁止用 errorMessage 兼任；核对 finally 块是否 `reader.cancel().catch(() => {})` 兜底释放；核对 `signal?: AbortSignal` 参数是否可选且内部用 `signal?.` 可选链；核对中断时 isLoading/isStreaming 是否复位。
   - **长任务轮询 UI（FR-051）**：若评审范围涉及长任务轮询的 `.vue` / `.ts` 文件（含 `setInterval` + `long_task_polling_ui_frontend.long_task_names` 任务名），核对是否用五状态机（`idle/queued/processing/completed/failed`）驱动 UI 而非单一 isLoading；核对轮询单次失败是否仅更新 error 文案不终止（catch 中无 clearInterval）；核对 completed/failed 分支是否显式停止定时器；核对超时是否用 `setTimeout` + 手动 abort + `abortReason='timeout'`（禁止 `AbortSignal.timeout`）；核对"关闭对话框"与"重置状态"是否拆为两个独立函数；核对 onBeforeUnmount 是否清理 abortController + 监听器 + 定时器三类资源。
   - **事件委托与生命周期清理（FR-052）**：若评审范围涉及 `v-html` 渲染的 `.vue` 文件，核对事件绑定是否用父容器 `addEventListener` 事件委托（禁止在 v-html DOM 上绑 @click）；核对 handler 是否用 `target.closest(selector)` / `target.tagName` 命中目标（禁止直接操作 event.target）；核对所有 `addEventListener` 是否在 `onBeforeUnmount` 用同一函数引用 `removeEventListener` 移除（禁止匿名函数注册）；核对 `globalThis/window/document.addEventListener` 全局事件是否配对 removeEventListener；核对第三方库实例（mermaid/marp/monaco 等）是否在 onBeforeUnmount 调用 destroy/dispose 或清空容器。
   - **第三方重库动态加载（FR-053）**：若评审范围涉及第三方库导入的 `.vue` / `.ts` 文件，核对 `heavy_library_frontend.heavy_libraries` 列表中的库是否用动态 `import()` 加载（禁止顶层 `import xxx from 'xxx'` 静态导入）；核对动态 import 是否有模块级缓存变量/loaded 标志防重复加载；核对库实例是否缓存复用（禁止每次渲染都 new）；核对 CJS 模块属性访问是否用 `mod.X ?? mod.default?.X` 兼容模式；核对动态 import + watch 回调中是否 `await nextTick()` 等 DOM 更新；核对渲染失败是否降级显示原始内容（`<pre>{{ raw }}</pre>`）。
6. **组装输出**：按下方 Required output 输出。先按 **Urgent** 分组（urgent 在前），再按类别顺序排序（Vue Composition -> Element Plus -> Pinia Store -> Performance -> Type Safety -> Theming -> Theme Color Mapping -> Config Isolation -> Config State -> Display Field -> Persistence Boundary -> Encoding Safety -> Dangerous Action -> Route Registration -> Type Sync -> Sensitive Field Display -> Scroll Container -> SPA Navigation -> Update Check -> Icon & Navigation -> Async Reliability -> Tauri Integration -> Control Layering -> Third-Party Error Guard -> Folding Panel Event -> Long Task Architecture -> SSE Event Dispatch -> SSE Stream Error -> Long Task Polling UI -> Event Delegation -> Heavy Library）。无任何偏离时使用 Template B。

## Required output
When invoked, the response must exactly follow one of the two templates:

### Template A (any findings)
```
# Code review
Found <N> urgent issues need to be fixed:

## 1 <brief description of bug>
FilePath: <path> line <line>
<relevant code snippet or pointer>


### Suggested fix
<brief description of suggested fix>

---
... (repeat for each urgent issue) ...

Found <M> suggestions for improvement:

## 1 <brief description of suggestion>
FilePath: <path> line <line>
<relevant code snippet or pointer>


### Suggested fix
<brief description of suggested fix>

---

... (repeat for each suggestion) ...
```

If there are no urgent issues, omit that section. If there are no suggestions, omit that section.

If the issue number is more than 10, summarize as "10+ urgent issues" or "10+ suggestions" and just output the first 10 issues.

Don't compress the blank lines between sections; keep them as-is for readability.

If you use Template A (i.e., there are issues to fix) and at least one issue requires code changes, append a brief follow-up question after the structured output asking whether the user wants you to apply the suggested fix(es). For example: "Would you like me to use the Suggested fix section to address these issues?"

### Template B。 (no issues)
```
## Code review
No issues found.
```

## Version History

| 版本 | 日期 | 变更摘要 |
|------|------|---------|
| v2.1.0 | 2026-07-23 | 新增 FR-044 规则（测试选择器优先级）：FR-044-1 选择器优先级 #id > [data-testid] > [aria-label] > .class > [placeholder]/:has-text()；FR-044-2 关键交互元素必须提供稳定 id 或 data-testid；FR-044-3 networkidle 禁用于含持续加载资源页面；FR-044-4 DOM 变更同步更新测试选择器。新增 references/test-selector-priority-rule.md；更新 review-config.md 追加 test_selector_priority 参数章节；更新 Historical Incident Coverage 表格。基于「Skill 导入模块 E2E 测试」任务复盘（placeholder 选择器误匹配 + 背景图阻塞 networkidle 超时）。 |
| v2.2.0 | 2026-07-31 | 新增 FR-045~FR-047 共 3 条前端编码规范复盘规则：控件分层原则（control-layering-frontend-rule.md，工具栏控件数 > 阈值必须分层 + 折叠面板须在 button-bar 外 input-area 内 + Vue Transition 动画 + 触发按钮激活态 + @mousedown.stop）、第三方库错误防护三层法（third-party-error-guard-frontend-rule.md，Mermaid/KaTeX/Prism 库级配置+预校验+CSS 兜底 + 渲染前清空容器 + 版本升级验证 + LLM 内容预校验）、折叠面板事件冲突防护（folding-panel-event-frontend-rule.md，click outside 排除 teleport 组件 + el-dropdown :hide-on-click=false + @click.stop/@mousedown.stop + teleport_selectors 列表）。SKILL.md Historical Incident Coverage 表追加 3 行，Full-File Mode 第 5 步跨文件一致性检查追加 3 个子项，组装输出类别顺序追加 Control Layering/Third-Party Error Guard/Folding Panel Event。同步更新 config/review-config.md（追加 control_layering_frontend/third_party_error_guard_frontend/folding_panel_event_frontend 三个参数段）、skill-loader.md（Rule Overview/Quick Routing Table/Keyword Scanning Guide 三表追加 FR-045~FR-047 行）。基于工具栏重构/Mermaid 错误防护/MCP 并行加载/折叠面板事件冲突等问题复盘。 |
| v2.3.0 | 2026-07-31 | 新增 FR-048~FR-053 共 6 条 v3 媒体生成工具复盘规则：长短任务架构分离前端视角（long-task-architecture-frontend-rule.md，按耗时分界选 SSE/轮询 + HTTP 状态码分类驱动 UI + 创建用 POST 查询用 GET）、SSE 事件对象映射分发前端视角（sse-event-dispatch-frontend-rule.md，事件类型 ≥3 用 Record<string,Handler> 对象映射表 + outputMode 联合字面量类型 + outputMode/outputModes 正交分离 + 未知事件 default handler）、SSE 流消费错误处理（sse-stream-error-frontend-rule.md，吞掉 AbortError + abortReason 三态 + finally reader.cancel 兜底 + signal 可空 + 中断复位 loading）、长任务轮询 UI（long-task-polling-ui-frontend-rule.md，五状态机 + 单次失败不终止 + 完成/失败显式停止 + 超时用 setTimeout 非 AbortSignal.timeout + 关闭/重置拆分 + onBeforeUnmount 三类资源清理）、事件委托与生命周期清理（event-delegation-frontend-rule.md，v-html 用父容器事件委托 + closest 命中目标 + addEventListener 配对 removeEventListener + 全局事件配对 + 库实例 destroy/dispose）、第三方重库动态加载（heavy-library-frontend-rule.md，动态 import + loaded 标志防重复 + 实例缓存 + CJS mod.X??mod.default?.X 兼容 + watch 中 await nextTick + 渲染失败降级显示原始内容）。SKILL.md Historical Incident Coverage 表追加 6 行，Full-File Mode 第 5 步跨文件一致性检查追加 6 个子项，组装输出类别顺序追加 Long Task Architecture/SSE Event Dispatch/SSE Stream Error/Long Task Polling UI/Event Delegation/Heavy Library。同步更新 config/review-config.md（追加 long_task_architecture_frontend/sse_event_dispatch_frontend/sse_stream_error_frontend/long_task_polling_ui_frontend/event_delegation_frontend/heavy_library_frontend 六个参数段）、skill-loader.md（Rule Overview/Quick Routing Table/Keyword Scanning Guide 三表追加 FR-048~FR-053 行）。基于「v3 媒体生成工具开发」四维度复盘（成功步骤/不确定性/可抽象流程/适用场景），对应 wiki-code-dev 的 CODING-059/063/064/065/066/067 编码规范前端部分。 |

> 完整版本历史见 [references/changelog.md](references/changelog.md)

## 参考文档

| 文件 | 内容 |
|------|------|
| [references/changelog.md](references/changelog.md) | 版本历史（完整记录） |





