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
| DOM 变更未同步测试选择器 + try/except 静默吞错 | test-case-sync-frontend-rule.md | FR-031 |
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
6. **组装输出**：按下方 Required output 输出。先按 **Urgent** 分组（urgent 在前），再按类别顺序排序（Vue Composition -> Element Plus -> Pinia Store -> Performance -> Type Safety -> Theming -> Theme Color Mapping -> Config Isolation -> Config State -> Display Field -> Persistence Boundary -> Encoding Safety -> Dangerous Action -> Route Registration -> Type Sync -> Sensitive Field Display -> Scroll Container -> SPA Navigation -> Update Check -> Icon & Navigation -> Async Reliability -> Tauri Integration）。无任何偏离时使用 Template B。

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
| v1.7.0 | 2026-07-22 | 新增 FR-026~FR-032 共 7 条 v2 改造复盘规则：类型检查缓存清理（typecheck-cache-frontend-rule.md）、Composable API 先读后用（composable-api-frontend-rule.md）、混合类型运行时分流（mixed-type-dispatch-frontend-rule.md）、Vue SFC 单 script 块（sfc-single-script-frontend-rule.md）、E2E 测试前置服务检查（e2e-precheck-frontend-rule.md）、测试用例与代码结构同步（test-case-sync-frontend-rule.md）、阅读视野优化与输入区固定（reading-viewport-frontend-rule.md）。同步更新 config/review-config.md（追加 7 个新参数段）、skill-loader.md（Rule Overview / Quick Routing Table / Keyword Scanning Guide 三表追加 FR26-FR32 行）、SKILL.md Historical Incident Coverage 表与 Full-File Mode 第 5 步跨文件一致性检查追加 7 个子项。 |
| v1.8.0 | 2026-07-22 | 新增 FR-033~FR-034 共 2 条目录结构复盘规则：前端构建产物目录结构分离（services/api/public/ 未 gitignore + 已跟踪文件未 git rm --cached）、测试截图与临时产物 .gitignore 完整性（test_screenshots/ 和 test_*.json 未登记）。SKILL.md Historical Incident Coverage 表追加 2 行（FR-033 / FR-034），Full-File Mode 第 5 步跨文件一致性检查追加 2 个子项。 |
| v1.9.0 | 2026-07-22 | 新增 FR-035~FR-040 共 6 条主题色变量映射复盘规则：主题色变量映射合规性（硬编码 rgba()/#hex 未替换为 CSS 变量）、alpha 变体命名合规性（使用未定义的 a07 等值）、语义变量选择正确性（场景背景硬编码值映射为卡片背景变量）、编辑工具使用合规性（含中文 .vue 文件被 Write 重写而非 Edit 精准替换）、类型检查通过性（双重门禁 tsc+vue-tsc）、多主题视觉一致性（未切换主题验证对比度）。SKILL.md Historical Incident Coverage 表追加 6 行，Full-File Mode 第 5 步跨文件一致性检查追加 6 个子项，组装输出类别顺序追加 Theme Color Mapping。基于「仪表盘 .recent-log 与 FloatingChat 主题色适配」任务四维度复盘。 |
| v2.0.0 | 2026-07-22 | 新增 FR-041~FR-043 共 3 条 Tauri 2.x 桌面应用集成复盘规则：Tauri invoke 命令三层声明审查（tauri-invoke-rule.md，build.rs/capabilities/lib.rs 三层缺失导致运行时 'Plugin not found'/'not allowed'/'command not found'）、透明窗口 CSS 覆盖审查（tauri-transparent-css-rule.md，仅覆盖 body 不够，须 html/body/#app/* 四层 + floating-active 通配符 + !important）、drag+click 冲突处理审查（tauri-drag-click-rule.md，data-tauri-drag-region 拦截 mousedown 致 click 永不触发，须 JS 三阶段处理 + 阈值从 config 读取 + start_dragging 防重复调用）。SKILL.md Historical Incident Coverage 表追加 3 行，Full-File Mode 第 5 步跨文件一致性检查追加 3 个子项，组装输出类别顺序追加 Tauri Integration。同步更新 config/review-config.md（追加 tauri_invoke_frontend / tauri_transparent_css_frontend / tauri_drag_click_frontend 三个参数段）、skill-loader.md（Rule Overview / Quick Routing Table / Keyword Scanning Guide 三表追加 FR-041~FR-043 行）。基于 Tauri 2.x 桌面应用集成历史问题复盘。 |





