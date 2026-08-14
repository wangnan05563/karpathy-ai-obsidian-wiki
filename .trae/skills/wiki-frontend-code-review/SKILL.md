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
| src/ 残留编译产物 .js/.map 使 Vite 优先解析 .js，.ts 修改静默不生效 + resolve.extensions 顺序 | ts-js-shadowing-frontend-rule.md | FR-061 |
| 后端 SSE done 事件新增 governor/threadId 字段，前端 types.ts interface 未同 PR 同步 + 新字段非加法可选 | type-sync-done-event-rule.md | FR-062 |
| 前端新增浏览器端持久化命名空间未确认隐私边界（敏感字段明文 / 产物入库）+ 会话默认服务端存储 | runtime-data-privacy-frontend-rule.md | FR-063 |
| 前端硬编码机器绝对路径/安装路径/版本号（应来自配置或共享常量）；用户数据路径前端自行拼接 exe 同级/Program Files；安装器/打包脚本覆盖用户数据 | packaging-config-rule.md | FR-064 |
| 前端 `el-radio` / `el-radio-button` 沿用 `label` 作 value（EP 2.6+ 弃用、3.0 移除，控制台告警 + 升级后失效） | element-plus-rule.md | FR-065 |
| 后端新增可选契约字段（如 `CompileInput.originalName?`）前端不消费，前端 types.ts 须同步可选声明且不得因字段缺失/新增而崩溃（`field!`/`as`/分支依赖），后端 `??` 兜底 | optional-contract-field-rule.md | FR-066 |
| 朗读/语音合成未优先 neural TTS、缺浏览器 TTS 优雅降级、SSML 注入/express-as 误用 | tts-neural-fallback-rule.md | FR-067 |
| 前端构建产物部署：outDir 硬编码固定目录原地覆盖（触发 safe-delete 钩子 + 残留旧产物 + 清空在服目录）；部署缺完整性标记导致后端选到半写入目录 | spa-deploy-integrity-frontend-rule.md | FR-068 |
| 多账户会话隔离失效：`currentConversationId` 模块级共享 ref 跨账户未 reset、复用 id 持久化未校验归属、会话按 ownerId 隔离不全导致跨账户泄漏（「历史消失/人人可见」） | session-isolation-frontend-rule.md | FR-069 |
| BYOK 多用户密钥代理失效：每用户配置未本地命名空间隔离（跨用户泄漏）/ 密钥未仅经请求体下发（落服务端/回显/日志）/ 始终下发空 toolsConfig 清空服务端共享能力 / 配置菜单仅 admin 可见致非管理员无法改自身配置 | byok-per-user-override-frontend-rule.md | FR-070 |
| 流式回答中间态丢失：流式分片仅内存持有、仅完成时落盘导致刷新退化为新会话；页面卸载 abort 在途流致切页回答死状态；无上次活跃会话记忆无法续答 | streaming-resume-frontend-rule.md | FR-071 |
| TTS prosody rate/volume/pitch 前端未校验即下发，畸形值触发后端免费端点 SSML invalid（1007）；前端 SSML 构造未转义 `<>&` / 误用 express-as | ssml-injection-frontend-rule.md | FR-073 |
| 隔离测试 flaky：含状态测试用 `beforeEach(indexedDB.deleteDatabase)` 在 fake-indexeddb + 已开连接下 onblocked/泄漏、用例间命名空间冲突、异步落盘断言竞态、后端模块单例跨用例共享 | indexeddb-test-isolation-rule.md | FR-072 |
| 归档按钮迁移：删除功能 DOM 节点（如 `.msg-actions`）前未确认引用清零，导致 CSS 选择器 / 测试断言悬空失效 | dom-compat-class-frontend-rule.md | FR-074 |
| 归档按钮迁移：新增 SVG 图标硬编码 `fill`/`stroke` 固定色、尺寸非 24x24、风格与现有线条图标不一致，主题切换下不可见 | theme-aware-icon-frontend-rule.md | FR-075 |
| 归档门控漂移：前端 `:can-archive` 仍依赖 `!!sessionId` 等过期契约，后端已改为请求体取内容解耦后前端门控未同步放宽，功能卡死 | capability-gating-sync-frontend-rule.md | FR-076 |
| 编辑重发丢失用户消息：`removeMessagesFrom(i)` 丢弃被编辑 user 消息后未 `submitQuestion` 重插，对话只剩悬空 AI 答案；重发前未先终止在途流式回复导致并发写入；文本未变仍重发 | edit-resend-frontend-rule.md | FR-077 |
| 流式聊天自动贴底失效：单次 nextTick 早于图片/代码撑高导致落后高度、用户回看被强制拉回底部、带图消息不补滚、滚动/加载监听泄漏到已销毁面板 | chat-autoscroll-frontend-rule.md | FR-078 |
| 成对操作按钮样式不一致：确认/取消基础样式/配色差异误导主次、硬编码色值不随主题、双 `type="primary"` 操作 | button-style-frontend-rule.md | FR-079 |
| 编辑态编辑框停留已发送气泡窄宽：进入编辑态未撑满问答列宽、文字频繁换行、体验远差于首问输入框 | editbox-width-frontend-rule.md | FR-080 |
| Vue/Pinia `reactive` 代理直传 IndexedDB 致 `[object Array] could not be cloned` 静默丢配置（toRaw 只剥顶层 / structuredClone 无法克隆代理 / 写入失败被 try/catch 仅 warn 掩盖） | idb-reactive-clone-frontend-rule.md | FR-081 |
| 登录卡死：认证/会话校验 fetch 无超时兜底，网络慢/服务端无响应时 await 永久悬挂，登录按钮灰显一直「登录中」无法重试 | auth-request-timeout-frontend-rule.md | FR-082 |
| 登录按钮永久灰显：进入等待态后 handler 无 try/finally 复位 loading，请求抛错/超时后无法重试 | auth-loading-reset-frontend-rule.md | FR-083 |
| 前端受保护接口裸 fetch 调 requireAuth 端点（GET /api/config、GET /api/ai/config）→ 后端返 401，AI 伙伴选项消失 + 控制台「加载配置失败：HTTP 401」静默失效 | auth-request-fetch-frontend-rule.md | FR-084 |
| pnpm store 散落项目/盘根（safe-delete 钩子打断 pnpm 主目录探测致退化）→ 前端 node_modules 解析不到统一 store / 构建在散落缓存上静默运行 | pnpm-store-hygiene-frontend-rule.md | FR-085 |
| 聆听页 v-show 常驻：切 Tab 不恢复播放定位 / 账户切换上一账户音色·队列残留（onMounted 仅一次 + 重型列表常驻卡顿 + 移动端 MobilePlaceholder 类型收窄失败） | persistent-component-lifecycle-frontend-rule.md | FR-086 |
| TTS 音频 ObjectURL 常驻泄漏：切曲目/账户切换不复活 revokeObjectURL，Blob 堆积致内存泄漏 | media-object-url-frontend-rule.md | FR-087 |
| `<audio>.play()` reject 两类失败混报"语音合成失败"误导排查（实为浏览器自动播放拦截）+ 切换曲目进度条沿用旧值错乱 | audio-playback-reliability-frontend-rule.md | FR-088 |
| 毛玻璃 backdrop-filter 包含块陷阱：滚动容器 `.mobile-content` 设 `backdrop-filter: var(--m-blur)`，glass 主题下成为内部 `position: fixed` 滚动 FAB / 全屏 sheet 遮罩的 containing block，随滚动失固定；浅色主题 `--m-blur:none` 正常 → 主题间不一致（命中 FR-040） | backdrop-filter-containing-block-frontend-rule.md | FR-089 |
| 双主题切换未统一 `--m-*` 变量：组件写死主题字面量或 `theme === ? a : b` 分支，浅色主题下出现深色补丁；主题状态散落多 store / 硬编码默认 | dual-theme-variable-frontend-rule.md | FR-090 |
| 下载请求无超时：后端卡死/网络中断时请求永久挂起，用户无反馈 | download-timeout-abort-frontend-rule.md | FR-091 |
| 移动端下载失败静默：MobileBrowse 分支未复用桌面端错误处理，失败被吞、用户「点了没反应」 | download-mobile-silent-guard-frontend-rule.md | FR-092 |
| 下载无重入守卫：快速连点触发并发重复下载，状态竞态/UI 抖动 | download-reentry-guard-frontend-rule.md | FR-093 |
| 下载文件名解析缺陷：未解码 RFC 5987 `filename*`、中文名乱码、扩展名静默丢失、头注入字符未清洗 | content-disposition-filename-frontend-rule.md | FR-094 |
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
   - **TS/JS 遮蔽（FR-061）**：若评审范围涉及 `frontend/src/**` 下 `.ts` 文件修改或 `vite.config.ts` 变更，核对 `src/` 下无 `*.js` / `*.js.map` 残留（否则 Vite 优先解析 .js 使 .ts 修改不生效）；核对 `vite.config.ts` 的 `resolve.extensions` 中 `.ts` / `.tsx` 排在 `.js` / `.jsx` 之前；建议变更后以 `ts_js_shadowing_frontend.typecheck_command` + `ts_js_shadowing_frontend.build_command` 验证 .ts 真实生效。
   - **前后端类型同步（SSE done 事件字段新增）（FR-062）**：若评审范围涉及后端 API 响应 / SSE 事件（如 `done` / `result` / `progress`）新增字段，核对前端 `types.ts` 对应 interface（如 `DoneEvent`）在同一 PR 中同步字段名与类型；核对新增字段为加法且带 `?` 可选（禁止删除/重命名字段、禁止把既有字段改必填）。
   - **运行时数据隐私（FR-063）**：若评审范围涉及前端新增浏览器端持久化（IndexedDB 库 / localStorage 键 / Cache Storage 命名空间），核对敏感字段（`runtime_data_privacy_frontend.forbidden_localstorage_fields`）未明文写入 localStorage；核对运行期产物（如 `test_screenshots/` / `test_*.json`）在 `.gitignore` 中；核对会话保存受 `server_side_sessions_config_field`（persistSessions）开关保护、默认关闭（会话默认留客户端 IndexedDB 降级缓存，对应后端 BR-065）。
   - **打包脚本与安装器配置（FR-064）**：若评审范围涉及前端代码或配套打包/安装器脚本（`.iss` / `*.ps1` / `build*.{ps1,sh}`），核对前端**不**硬编码机器绝对路径/安装路径/版本号（`packaging_config_frontend.forbidden_hardcoded_patterns`），这些值须来自配置或共享常量（package.json / build define / 后端 `/version`）；核对用户数据路径（config.json / vault / data）由后端 API 提供，前端不得自行拼接 exe 同级或 `Program Files` 路径；跨文件核对安装器 `[Files]` 仅含程序文件且用 `ignoreversion`，用户数据绝不打包到 `{app}`（对应后端 BR-068 / CODING-PACKAGING-USERDATA）。
   - **Element Plus 单选组件弃用属性（FR-065）**：若评审范围涉及含 `el-radio` / `el-radio-button` 的 `.vue` 文件，扫描 `element_plus_radio.deprecated_value_attr`（`label`）是否仍被用作选项值（即 `label="x"` 且非纯显示文本、实际承担 `v-model` 绑定值）；命中即标记 Critical，并提示改用 `element_plus_radio.replacement_attr`（`value`）承载选项值、显示文本改由默认插槽提供；建议升级 Element Plus 主版本前按 `element_plus_radio.frontend_glob` 全量 grep 存量 `label=` 用法，避免升级到 `element_plus_radio.removal_version`（3.0.0）后选项值静默失效。
   - **可选契约字段同步（前端不消费）（FR-066）**：若评审范围涉及后端 API 契约（如 `CompileInput` / `QueryInput`，由 `optional_contract_field_frontend.watch_request_bodies` 列出）新增可选字段、或前端 `types.ts` interface 修改，核对 `(1)` 前端 `types.ts` 是否在同一 PR 同步声明该可选字段（`FR-066-1`，建议级）；（`2`）前端代码是否对该不消费的内部字段（由 `optional_contract_field_frontend.ignored_unconsumed_internal_fields` 列出，如 `originalName`）做必填访问（`field!` / `as T`）或以其存在性作为关键分支条件，命中即标记 Critical（`FR-066-2`）；（`3`）后端是否对该字段提供运行时兜底（`?? default`），并跨文件核对前端 `types.ts` 与后端 `api/src/types.ts` 字段名/类型/可选性一致（`FR-066-3`，建议级）。
   - **语音合成神经降级（FR-067）**：若评审范围涉及朗读 / 语音合成功能（含 `speechSynthesis` / `SpeechSynthesisUtterance` / `/api/tts/synthesize` / `new Audio` / `prosody` / `express-as` / 语音控件），核对：优先 neural TTS（后端合成端点 + 优质 neural 音色）而非浏览器 Web Speech API（FR-TTS-1，建议级）；必须保留浏览器 `speechSynthesis` 为优雅降级、合成失败不得静默（FR-TTS-2，Critical）；SSML 须转义 `<>&` 且禁用 `<mstts:express-as>`（免费端点不支持，WebSocket 关闭 1007）（FR-TTS-3，Critical）；播放前校验音频响应 magic bytes（`ff f3` / `ff fb` / `ID3`）并在失败前重试 2–3 次（FR-TTS-4，建议级）。对应 wiki-code-dev CODING-TTS-*，基于「Edge TTS 拟人化朗读改造」复盘。
   - **SPA 部署完整性（FR-068）**：若评审范围涉及 `vite.config.ts` 的 `build.outDir` / `emptyOutDir` 或部署脚本（`_deploy_live*.mjs` / `build*.ps1` / `build*.sh`），核对 `outDir` 可被部署注入为**全新时间戳目录**、不硬编码固定 `../api/public` 原地覆盖（FR-068-1，建议级，规避 safe-delete 钩子 + 残留旧产物 + 清空在服目录，对应后端 BR-071-4）；部署须**最后写入**完整性标记（`.deploy-complete`）供后端 `isDeployComplete` 门禁识别（FR-068-2，Critical）；前端验证链构建后须校验产物完整（index.html + 关键 bundle）而非仅 vue-tsc（FR-068-3，建议级）。对应后端 BR-071 / wiki-code-dev CODING-SPA-LIVE-DEPLOY。
   - **会话跨账户隔离（FR-069）**：若评审范围涉及会话 store（`*store*.ts` 中 `currentConversationId` / `scopedOwnerId`）或问答页 auth watch（`user?.id`），核对：(1) Pinia setup store 的会话状态 ref 是否全部加入 store return 对象（漏加则 `resetSession` 赋值不可观测=死状态，FR-069-1，Critical）；(2) 账户切换/登出是否先 `resetSession()` 再 `loadConversations()`（FR-069-2，Critical）；(3) `persistConversation` 复用 id 前是否以 IndexedDB 实际记录（`dbGet`）校验归属、他人记录绝不覆盖（冲突改用全新 uuid，FR-069-3，Critical）；(4) `loadConversations` 二次防御（owner 不符重置当前会话）+ `filterByOwner` 严格按 `ownerId` 隔离 + `migrateOwnerless` 落盘成功后才内存归属（FR-069-4，建议级）。对应 wiki-code-dev CODING-SESSION-ISOLATION，基于「多账户会话隔离泄漏」复盘。
   - **BYOK 多用户配置代理（FR-070）**：若评审范围涉及 `services/userConfig.ts` / `views/Config.vue` / `views/Query.vue` 中 `usercfg::` / `loadAiUserConfig` / `llmConfig` / `toolsConfig` / `apiKey` / 配置菜单 / `isAdmin` / `v-if="isAdmin"` / 命名空间，核对：(1) 每用户配置是否存前端本地命名空间（键内化 userId，绝不全局 localStorage 跨用户共享，FR-070-1，Critical）；(2) 密钥是否仅经请求体下发（不进 URL/GET/日志）、是否仅当配置存在才下发对应块（始终下发空 toolsConfig 会清空服务端共享能力，FR-070-2，Critical）；(3) 配置菜单访问门控——敏感 admin tab 是否 `v-if="isAdmin"` 二层拦截、个人 BYOK 配置是否对全员（`dashboard` 权限）可见（FR-070-3，建议级）。对应 wiki-code-dev CODING-BYOK，基于「BYOK 多用户密钥代理」复盘。
   - **流式回答增量持久化与续答（FR-071）**：若评审范围涉及 `stores/query.ts`（`streamingAnswer` / `persistConversation`）/ `views/Query.vue`（`onBeforeUnmount` / `abortController` / `LAST_ACTIVE_CONVERSATION` / `resumeLastAnswer`）/ `types.ts`（`status:'streaming'`），核对：(1) 流式分片是否增量（防抖）落盘中间态，而非仅完成时落盘（FR-071-1，Critical）；(2) `onBeforeUnmount` 是否仅卸载监听、绝不 `abortController?.abort()` 杀在途流（FR-071-2，Critical）；(3) 重载恢复是否仅对 `status:'streaming'` 末条续答、`interrupted`/`error` 不自动续，且 SPA 重挂载后台流活跃(isLoading)时跳过（FR-071-3，Critical）。对应 wiki-code-dev CODING-STREAMING-RESUME，基于「断点续答（FR-RM-09）」复盘。
   - **隔离测试纪律（FR-072）**：若评审范围涉及 `*.test.ts` / `*.spec.ts` / `test_*.py` 等含持久化 / 全局状态的测试（IndexedDB / localStorage / 模块级单例），核对：(1) 是否用唯一 userId / 线程 id 命名空间隔离，而非 `beforeEach(indexedDB.deleteDatabase)`（fake-indexeddb + 已开连接会 onblocked / 泄漏，FR-072-1，Critical）；(2) 异步落盘断言是否多轮 `setTimeout(0)` flush（轮数从 `test_isolation_frontend.flush_rounds` 读取，FR-072-2，建议级）；(3) 后端用例是否重置模块态 / mock（`vi.clearAllMocks` / `vi.resetModules`）禁止跨用例共享可变单例（FR-072-3，建议级）。对应 wiki-code-dev CODING-TEST-ISOLATION，基于「隔离测试 flaky」复盘。
   - **SSML / TTS Prosody 参数前端校验（FR-073）**：若评审范围涉及朗读 / 语音合成前端（`EdgeTtsProvider` / 语音控件 / `/api/tts/synthesize` 调用）且下发 `rate` / `volume` / `pitch`，核对：前端是否在发送前用 `ssml_injection_frontend.rate_regex` / `volume_regex` / `pitch_regex` 白名单校验并 clamp 到 `default_value`（防御纵深，避免畸形值触发后端免费端点 `SSML is invalid` / 1007，FR-073-1，Critical）；若前端参与任何 SSML 构造，用户朗读文本拼入前须转义 `ssml_injection_frontend.escape_chars`（`<>&`）且禁用 `forbidden_tags_regex`（`mstts:express-as`）（FR-073-2，Critical，与 FR-067 FR-TTS-3 一致）；前端 rate/volume/pitch 调节控件须在 UI 层限制取值范围（FR-073-3，建议级）。对应后端 BR-074 / wiki-code-dev CODING-SSML-INJECTION。
   - **安全删 DOM 节点（FR-074）**：若评审范围涉及删除功能 DOM 节点（如 `.msg-actions` / 按钮容器）的重构，核对删除前是否对 `dom_compat_class.test_file_patterns` 内的选择器 / 测试断言做 `grep` 零引用校验（命中即先同步更新再删）；禁止仅因"代码不报错"就删除仍被 CSS / 测试引用的 class/id（对应后端 BR-050-2 / dom-compat-class-rule.md `preserve_original_class_first` + `stale_class_threshold=0`）。删除与引用更新须同一 PR 完成（FR-074-1，Critical）。
   - **主题感知图标（FR-075）**：若评审范围涉及新增 / 修改 SVG 图标（按钮、工具栏、导航），核对 `fill`/`stroke` 是否用 `currentColor`（禁止硬编码固定色，否则主题切换下不可见，FR-075-1，Critical）；核对图标尺寸是否为 `theme_aware_icon.size`（默认 24x24）且风格与现有线条图标一致（FR-075-2，建议级）。对应 wiki-code-dev theme-aware-icon-rule.md（TAI）。
   - **能力门控同步（FR-076）**：若评审范围涉及前端功能门控（如 `:can-archive` / 按钮 `:disabled` 依据），核对门控依据是否与后端契约放宽同步——后端改为请求体取内容解耦（不再依赖 `sessionId` / 服务端会话）后，前端门控须移除 `!!sessionId` 等过期依赖、改为依据"内容可得性"（FR-076-1，Critical）；前后端放宽须同一变更完成，禁止两端漂移（FR-076-2，建议级）。对应后端 BR-086 / wiki-code-dev CODING-CAPABILITY-GATING-SYNC（与 persistence-client-content-decoupling 同一变更闭环）。
   - **编辑重发重新插入（FR-077）**：若评审范围涉及「编辑已发送消息并重发」（含 `removeMessagesFrom` / `submitQuestion` / `editingIdx` / MessageToolbar 编辑入口），核对：丢弃尾部（`removeMessagesFrom(i)`）后是否**同一处理函数内**立即 `submitQuestion(编辑后文本)` 重插 user 消息，否则对话只剩悬空 AI 答案（FR-077-1，Critical）；编辑重发前是否先终止在途流式回复、释放 `isLoading` 再丢弃尾部，避免并发写入（FR-077-2，Critical）；编辑后文本未变化是否仅退出编辑态、不重发（FR-077-3，建议级）。对应 wiki-code-dev CODING-EDIT-RESEND，基于「编辑重发悬空答案」复盘。
   - **流式自动贴底滚动（FR-078）**：若评审范围涉及流式聊天自动滚动（`useChatAutoScroll` / `scrollToBottom` / `chatBodyRef`），核对：贴底定位是否 `nextTick` + 双 `requestAnimationFrame` 捕获同步布局变化（FR-078-1，建议级）；是否按 `near_bottom_px` 阈值暂停/恢复自动贴底（FR-078-2，建议级）；是否 `capture` 阶段监听 `img` `load` 补滚（FR-078-3，建议级）；`scroll`/`load` 监听是否随容器挂载/卸载绑定解绑、无泄漏（FR-078-4，Critical）；`force` 是否仅用于新消息到达（FR-078-5，建议级）。对应 wiki-code-dev CODING-STREAMING-AUTOSCROLL，基于「流式贴底失效」复盘。
   - **成对按钮样式一致性（FR-079）**：若评审范围涉及成对操作按钮（确认/取消、`.edit-btn.confirm` / `.edit-btn.cancel`、模态框确认取消），核对同组按钮是否共享一致基础样式、差异仅经 hover 强调（FR-079-1，建议级）；配色是否用主题变量、无硬编码色值（FR-079-2，建议级）；是否避免确认/取消同时 `type="primary"`（FR-079-3，建议级）。对应 wiki-code-dev CODING-BUTTON-STYLE-CONSISTENCY，基于「成对按钮样式漂移」复盘。
   - **编辑态撑满列宽（FR-080）**：若评审范围涉及消息气泡进入编辑态（`.msg-content-wrapper.editing` / `.msg-edit` / textarea），核对编辑容器是否撑满问答列宽而非停留已发送气泡窄宽（FR-080-1，建议级）；是否以 `align-items:stretch` / `width:100%` 覆盖已发送态 `flex-end`（FR-080-2，建议级）；textarea/input 是否 `width:100%` 且内边距与首问输入框一致（FR-080-3，建议级）。对应 wiki-code-dev CODING-EDITBOX-WIDTH，基于「编辑框停留窄宽」复盘。
   - **IndexedDB 写入前剥离响应式代理（FR-081）**：若评审范围涉及任何 IndexedDB 写入路径（`idb_reactive_clone_frontend.scan_patterns` 命中的 `dbPut` / `saveUserConfig` / `idbPut` / `store.put` 等），核对其写入值若源自 Pinia store state ref / `reactive()`，是否在写入前整树深拷贝（FR-081-1，Critical）；禁止用 `toRaw()` 当深剥离（嵌套代理仍失败，FR-081-2，Critical）；禁止 `structuredClone(reactiveObj)`（代理无法被克隆，FR-081-3，Critical）；建议封装函数（如 `saveUserConfig`）内部统一 `clone` 防御（FR-081-4，建议级）。对应 wiki-code-dev CODING-IDB-REACTIVE-CLONE，基于「userConfig 静默丢配置」复盘。
   - **认证/异步请求超时兜底（FR-082）**：若评审范围涉及登录 / 会话校验 / 任何"用户点击后进入等待态"的认证或关键异步请求（`auth` store / `login` / fetch 调用点），核对是否用 `AbortController` / `AbortSignal.timeout(ms)` 包裹且超时阈值来自配置（默认 `auth_request_timeout_frontend.timeout_ms`），禁止裸 `await fetch` 无超时（FR-082-1，Critical）；超时是否给出明确可重试文案（如「登录超时，请检查网络或服务器后重试」）并解除按钮禁用态，禁止超时后永久「登录中」灰显（FR-082-2，建议级）。对应 wiki-code-dev CODING-AUTH-REQUEST-TIMEOUT，基于「初次登录卡死（登录按钮灰显 + 一直登录中）」复盘。
   - **异步操作 loading 复位（FR-083）**：若评审范围涉及设置 `loading=true` / `submitting=true` 后发起异步请求的交互（登录 / 提交 / 保存配置），核对 `loading` 复位是否在 `try/finally`（或 Promise `.finally`）中覆盖成功/失败/超时/abort 全路径，禁止只在 `try` 成功分支复位而 `catch` 遗漏（FR-083-1，Major）；复位不得被提前 `return` / `throw` 跳过（FR-083-2，建议级）。对应 wiki-code-dev CODING-AUTH-LOADING-RESET，基于「登录按钮永久灰显（handler 无 finally 复位 loading）」复盘。
   - **受保护接口带鉴权封装调用（FR-084）**：若评审范围涉及调用后端 `requireAuth` 受保护端点（路径片段命中 `auth_request_fetch_frontend.protected_endpoint_patterns`，如 `/api/config` / `/api/ai/config`）的 `.vue` / `.ts` 文件，核对是否统一经带鉴权封装（默认 `auth_request_fetch_frontend.wrapper_symbol` = `apiFetch`）调用，禁止裸 `fetch` 不带 `Authorization` 头（FR-084-1，Critical）；核对封装读取 token 的来源是否为 `localStorage` 等非 Pinia 源（避免 bootstrap 期 auth store 未就绪取不到 token，FR-084-2，Critical）；若本次变更涉及后端把公开端点收紧为 `requireAuth`，须确认前端所有调用方已迁移且 PR 描述标注"端点鉴权升级 + 调用方审计"（FR-084-3，Major）。对应 wiki-code-dev CODING-AUTH-REQUEST-FETCH / 后端 BR-094。
   - **包管理器 store 卫生（FR-085）**：若评审范围涉及构建配置 / 依赖管理 / 仓库初始化（`.npmrc` / `vite.config.ts` / `package.json` / CI 脚本），核对全局 `.npmrc` 是否显式声明 `pnpm_store_hygiene_frontend.store_dir_key`（默认 `store-dir`）收敛 pnpm store（FR-085-1，建议级）；核对项目/盘根是否存在与统一 store 不一致的孤儿 `.pnpm-store`（命中 `forbidden_store_dirs` 且非 `canonical_store_dir`，FR-085-2，建议级）。对应 wiki-code-dev CODING-PNPM-STORE-HYGIENE / 后端 BR-095 / wiki-auto-testing `dependency_store_hygiene_check`。
   - **常驻组件生命周期隔离（FR-086）**：若评审范围涉及用 `v-show` 常驻保留后台状态（音频播放 / 长连接 / 计时器 / 流式进度）的组件（如移动端聆听页 `MobileListen`），核对：(1) 是否用 `watch(() => props.visible)` 在切回时恢复状态 / 自动定位，不依赖 `onMounted` 仅一次执行（FR-086-1，Major）；(2) 因常驻导致 `onMounted` 仅一次的组件，账户切换 / 登出是否 `watch(() => authStore.user?.id)` 显式重置会话态（暂停音频、`revokeObjectURL`、清空 `queue/currentIndex/isPlaying/position/duration`、重载本账户默认配置），缺失即上一账户残留（FR-086-2，Critical）；(3) 内部非播放必需的重型节点（> `heavy_list_threshold` 项的列表 / 搜索结果 / 目录树）是否用 `v-if="visible"` 懒渲染，仅 Tab 激活时渲染（FR-086-3，Major）；(4) 分支移出 `v-else-if` 链后 `MobilePlaceholder` 是否改为独立 `v-if` 排除全部已知 Tab 让 TS 收窄 `activeTab` 为 never（FR-086-4，建议级）。对应 wiki-code-dev CODING-PERSISTENT-COMPONENT，基于「移动端聆听页 v-show 常驻后台播放」复盘。
   - **ObjectURL 生命周期（FR-087）**：若评审范围涉及 `URL.createObjectURL(blob)` 持有 TTS 音频 / 图片预览 / 文件下载等 Blob 的组件（尤其 `v-show` 常驻或频繁重建），核对每次重新合成（赋新 `a.src`）前是否先 `revokeObjectURL` 旧 URL、状态重置 / 切换曲目 / `onBeforeUnmount` 前是否释放当前句柄（FR-087-1，Major）；ObjectURL 句柄是否收口到单一组件级变量（如 `objectUrl`）集中管理释放时机（FR-087-2，建议级）。对应 wiki-code-dev CODING-MEDIA-OBJECT-URL，基于「聆听页 TTS 音频 ObjectURL 常驻泄漏」复盘。
   - **音频播放可靠性（FR-088）**：若评审范围涉及前端 `<audio>` / Web Audio 播放用户触发的媒体且合成（后端 / TTS）与播放分两步，核对 `synthAndPlay` 是否把合成段（res.ok / blob 解析）与播放段（`a.play()`）分开 catch、各自给出区分文案（"语音合成失败" / "播放被浏览器拦截"），避免把浏览器自动播放拦截误报为合成失败（FR-088-1，Major）；切换曲目 / 重合成前是否清零 `position` / `duration` 避免沿用旧进度（FR-088-2，建议级）。对应 wiki-code-dev CODING-AUDIO-PLAYBACK-RELIABILITY，基于「聆听页两类播放失败混报」复盘。
   - **毛玻璃包含块陷阱（FR-089）**：若评审范围涉及含 `backdrop-filter` 的滚动容器（如 `backdrop_filter_frontend.scroll_container_selectors` 命中的 `.mobile-content`）且其内有 `position: fixed` 后代（滚动回顶 FAB / 定位按钮 / 全屏 sheet 遮罩，见 `fixed_descendant_selectors`），按 `blur_variable_name`（默认 `--m-blur`）确认毛玻璃主题下该容器不会成为 fixed 后代的包含块——修复须移除容器 `backdrop-filter` / `-webkit-backdrop-filter` 两行（毛玻璃保留在同级兄弟节点如 tabbar）或 `<Teleport to=".mobile-root">` 逃逸 fixed 子元素（FR-089-1，Critical）；若组件写 `theme === ? a : b` 主题分支改 `backdrop-filter`，须改 `--m-*` 变量驱动（FR-089-2，Standard，与 FR-090-3 协同）。对应 wiki-code-dev CODING-BACKDROP-FILTER-CB，基于「移动端双主题切换 + 滚动 FAB 主题间失固定」复盘。
   - **双主题变量架构（FR-090）**：若评审范围涉及主题相关样式（背景 / 模糊 / 文字 / 边框 / 阴影），核对是否引用 `var(--m-*)`（前缀 `theme_variable_prefix` 默认 `--m-`）而非字面量、新增样式是否先在 `var_definition_files` 补 `--m-*` 定义再引用（FR-090-1，Standard，与 FR-035 主题色变量映射互补）；主题切换状态是否集中单一 composable、`localStorage` 持久化 key 统一（`persist_key`）、默认主题参数化（`default_theme`）（FR-090-2，Standard）；组件是否无 `theme === ? a : b` / `data-theme` 硬编码分支（FR-090-3，Standard）。对应 wiki-code-dev CODING-DUAL-THEME-VAR，基于「移动端双主题 --m-* 变量架构」复盘。
6. **组装输出**：按下方 Required output 输出。先按 **Urgent** 分组（urgent 在前），再按类别顺序排序（Vue Composition -> Element Plus -> Pinia Store -> Performance -> Type Safety -> Theming -> Theme Color Mapping -> Config Isolation -> Config State -> Display Field -> Persistence Boundary -> Encoding Safety -> Dangerous Action -> Route Registration -> Type Sync -> Sensitive Field Display -> Scroll Container -> SPA Navigation -> Update Check -> Icon & Navigation -> Async Reliability -> Tauri Integration -> Control Layering -> Third-Party Error Guard -> Folding Panel Event -> Long Task Architecture -> SSE Event Dispatch -> SSE Stream Error -> Long Task Polling UI -> Event Delegation -> Heavy Library -> TS/JS Shadowing -> Type Sync Done Event -> Optional Contract Field -> TTS / Neural Fallback -> SSML Prosody Injection -> SPA Deploy Integrity -> Session Isolation -> BYOK / Per-User Override -> Streaming Resume -> Runtime Data Privacy -> Packaging Config -> Test Isolation -> Safe DOM Delete -> Theme Aware Icon -> Capability Gating Sync -> Edit Resend -> Chat Autoscroll -> Button Style -> Editbox Width -> IDB Reactive Clone -> Auth Request Timeout -> Auth Loading Reset -> Auth Request Fetch Wrapping -> Pnpm Store Hygiene -> Persistent Component Lifecycle -> ObjectURL Lifecycle -> Audio Playback Reliability -> Backdrop Filter Containing Block -> Dual Theme Variable）。无任何偏离时使用 Template B。

## Required output
When invoked, the response must exactly follow one of the two templates:

### Template A (any findings)

> **Severity & Scope Legend（与四维度复盘对齐）**
> - **Urgent / Suggestion / Nit** 分别对应"阻断合并 / 建议改进 / 吹毛求疵"三级严重度。
> - **Scope（适用边界）**：每条 finding 须标注**适用场景**与**不适用场景**（对应 wiki-code-dev 复盘维度④），避免把噪声当缺陷；跨项目复用规则时须注明本项目适用边界。
> - **Rule link**：标注命中的 FR- 编号与对应 `*-rule.md`，便于回溯"事故 → 规则"来由（见 references/retrospective-synthesis.md）。

```
# Code review
Found <N> urgent issues need to be fixed:

## 1 <brief description of bug>
FilePath: <path> line <line>
<relevant code snippet or pointer>

**Rule / Scope:** <FR-xxx> · 适用：<场景>；不适用：<场景>

### Suggested fix
<brief description of suggested fix>

---
... (repeat for each urgent issue) ...

Found <M> suggestions for improvement:

## 1 <brief description of suggestion>
FilePath: <path> line <line>
<relevant code snippet or pointer>

**Rule / Scope:** <FR-xxx> · 适用：<场景>；不适用：<场景>

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

## 配置化与泛化审查（CODING-CONFIG-DRIVEN / J-CONFIG-FIRST）

> 本段是「配置驱动 + 泛化」的**统一审查透镜**，作为所有 FR 的前置约束。任何评审都须把以下两类作为独立扫描维度，具体阈值 / 颜色 / 路径 / 数量信号一律来自 `config/review-config.md` 的 `config_driven_frontend` 段（零硬编码）。

| 审查维度 | 扫描信号（来自 config，不内联） | 判定 |
|---------|-------------------------------|------|
| 硬编码颜色值 | `hardcode.color_signals`（rgba()/rgb()/#hex/hsl() 等） | 命中且不匹配 `whitelist_patterns` → 改为 CSS 变量（🟡 Warning） |
| 硬编码路径/数量 | `hardcode.path_signals`（机器绝对路径/Program Files）/ `hardcode.count_signals`（主题/预设/菜单数量字面量） | 命中 → 改配置键 / 后端 API 动态获取（🟡 Warning） |
| 非泛化特判 | `hardcode.special_case_signals`（`if (kind===` / `switch`） | 可 registry 化的 → 建议改为配置组遍历 |
| 配置三层合规 | 默认值 vs 项目覆盖 vs 示例三层清晰；改项目只动覆盖层 | 默认值被项目特有值污染 → 🟡 Warning |

- **适用**：所有含可变参数（颜色/路径/数量/阈值）的改动；需跨项目复用的规则 / 技能；CI / 多业务泛化。
- **不适用**：编译期真常量、协议固定枚举（但若未来可能扩展仍建议配置化）。
- 对应 wiki-code-dev `references/config-driven-generic-rule.md`（CODING-CONFIG-DRIVEN）；参数段见 `review-config.md` 的 `config_driven_frontend` 段（v2.17.0 新增）。

## Version History

| 版本 | 日期 | 变更摘要 |
|------|------|---------|
| v2.1.0 | 2026-07-23 | 新增 FR-044 规则（测试选择器优先级）：FR-044-1 选择器优先级 #id > [data-testid] > [aria-label] > .class > [placeholder]/:has-text()；FR-044-2 关键交互元素必须提供稳定 id 或 data-testid；FR-044-3 networkidle 禁用于含持续加载资源页面；FR-044-4 DOM 变更同步更新测试选择器。新增 references/test-selector-priority-rule.md；更新 review-config.md 追加 test_selector_priority 参数章节；更新 Historical Incident Coverage 表格。基于「Skill 导入模块 E2E 测试」任务复盘（placeholder 选择器误匹配 + 背景图阻塞 networkidle 超时）。 |
| v2.2.0 | 2026-07-31 | 新增 FR-045~FR-047 共 3 条前端编码规范复盘规则：控件分层原则（control-layering-frontend-rule.md，工具栏控件数 > 阈值必须分层 + 折叠面板须在 button-bar 外 input-area 内 + Vue Transition 动画 + 触发按钮激活态 + @mousedown.stop）、第三方库错误防护三层法（third-party-error-guard-frontend-rule.md，Mermaid/KaTeX/Prism 库级配置+预校验+CSS 兜底 + 渲染前清空容器 + 版本升级验证 + LLM 内容预校验）、折叠面板事件冲突防护（folding-panel-event-frontend-rule.md，click outside 排除 teleport 组件 + el-dropdown :hide-on-click=false + @click.stop/@mousedown.stop + teleport_selectors 列表）。SKILL.md Historical Incident Coverage 表追加 3 行，Full-File Mode 第 5 步跨文件一致性检查追加 3 个子项，组装输出类别顺序追加 Control Layering/Third-Party Error Guard/Folding Panel Event。同步更新 config/review-config.md（追加 control_layering_frontend/third_party_error_guard_frontend/folding_panel_event_frontend 三个参数段）、skill-loader.md（Rule Overview/Quick Routing Table/Keyword Scanning Guide 三表追加 FR-045~FR-047 行）。基于工具栏重构/Mermaid 错误防护/MCP 并行加载/折叠面板事件冲突等问题复盘。 |
| v2.3.0 | 2026-07-31 | 新增 FR-048~FR-053 共 6 条 v3 媒体生成工具复盘规则：长短任务架构分离前端视角（long-task-architecture-frontend-rule.md，按耗时分界选 SSE/轮询 + HTTP 状态码分类驱动 UI + 创建用 POST 查询用 GET）、SSE 事件对象映射分发前端视角（sse-event-dispatch-frontend-rule.md，事件类型 ≥3 用 Record<string,Handler> 对象映射表 + outputMode 联合字面量类型 + outputMode/outputModes 正交分离 + 未知事件 default handler）、SSE 流消费错误处理（sse-stream-error-frontend-rule.md，吞掉 AbortError + abortReason 三态 + finally reader.cancel 兜底 + signal 可空 + 中断复位 loading）、长任务轮询 UI（long-task-polling-ui-frontend-rule.md，五状态机 + 单次失败不终止 + 完成/失败显式停止 + 超时用 setTimeout 非 AbortSignal.timeout + 关闭/重置拆分 + onBeforeUnmount 三类资源清理）、事件委托与生命周期清理（event-delegation-frontend-rule.md，v-html 用父容器事件委托 + closest 命中目标 + addEventListener 配对 removeEventListener + 全局事件配对 + 库实例 destroy/dispose）、第三方重库动态加载（heavy-library-frontend-rule.md，动态 import + loaded 标志防重复 + 实例缓存 + CJS mod.X??mod.default?.X 兼容 + watch 中 await nextTick + 渲染失败降级显示原始内容）。SKILL.md Historical Incident Coverage 表追加 6 行，Full-File Mode 第 5 步跨文件一致性检查追加 6 个子项，组装输出类别顺序追加 Long Task Architecture/SSE Event Dispatch/SSE Stream Error/Long Task Polling UI/Event Delegation/Heavy Library。同步更新 config/review-config.md（追加 long_task_architecture_frontend/sse_event_dispatch_frontend/sse_stream_error_frontend/long_task_polling_ui_frontend/event_delegation_frontend/heavy_library_frontend 六个参数段）、skill-loader.md（Rule Overview/Quick Routing Table/Keyword Scanning Guide 三表追加 FR-048~FR-053 行）。基于「v3 媒体生成工具开发」四维度复盘（成功步骤/不确定性/可抽象流程/适用场景），对应 wiki-code-dev 的 CODING-059/063/064/065/066/067 编码规范前端部分。 |
| v2.4.0 | 2026-08-05 | 新增 FR-064 规则（打包脚本与安装器配置）：前端代码不得硬编码机器绝对路径/安装路径/版本号（应来自配置或共享常量）；用户数据路径由后端 API 提供，前端不得自行拼接 exe 同级/Program Files 路径；跨文件核对安装器 `[Files]` 仅含程序文件且用 `ignoreversion`、用户数据绝不打包到 `{app}`。SKILL.md Historical Incident Coverage 表追加 1 行，Full-File Mode 第 5 步跨文件一致性检查追加 1 个子项，组装输出类别顺序追加 Packaging Config。同步更新 config/review-config.md（追加 packaging_config_frontend 参数段）。对应后端 BR-068 / wiki-code-dev CODING-PACKAGING-USERDATA（基于「安装器覆盖配置 / AppData 数据迁移 / SEA 路径解析 / clean-defaults」复盘）。 |
| v2.5.0 | 2026-08-05 | 新增 FR-065 规则（Element Plus 单选组件弃用属性）：`el-radio` / `el-radio-button` 的 `label` 作 value 在 Element Plus 2.6.0+ 已弃用、3.0.0 移除，选项值须改用 `value`、显示文本改由默认插槽提供；升级主版本前须全量 grep 存量 `label=` 用法。SKILL.md Historical Incident Coverage 表追加 1 行，Full-File Mode 第 5 步跨文件一致性检查追加 1 个子项（Element Plus 单选组件弃用属性）。同步更新 references/element-plus-rule.md（新增规则段）、references/examples/element-plus-rule-examples.md（新增 Wrong/Right）、config/review-config.md（追加 element_plus_radio 参数段）、skill-loader.md（Rule Overview / Quick Routing Table / Keyword Scanning Guide 三表追加 FR-064 与 FR-065 行）。基于「开发模式点击知识浏览页 el-radio 弃用警告」复盘。 |
| v2.6.0 | 2026-08-05 | 新增 FR-066 规则（可选契约字段同步 - 前端不消费）：后端在 API 契约（如 CompileInput）新增可选字段（如 originalName?，仅供后端内部兜底）时，前端 types.ts 须同一 PR 同步声明可选（FR-066-1，建议级）；前端若不消费该内部字段，禁止对其做必填访问（`field!`/`as`）或依赖存在性分支（FR-066-2，Critical）；后端须 `??` 兜底且跨文件核对字段一致性（FR-066-3，建议级）。扩展 TS-1 / FR-062 的"加法+可选"原则至"前端不消费字段"子场景。SKILL.md Historical Incident Coverage 表追加 1 行，Full-File Mode 第 5 步跨文件一致性检查追加 1 个子项（可选契约字段同步），组装输出类别顺序追加 Optional Contract Field。同步新增 references/optional-contract-field-rule.md、config/review-config.md（追加 optional_contract_field_frontend 参数段）、skill-loader.md（Rule Overview / Quick Routing Table / Keyword Scanning Guide 三表追加 FR-066 行）。对应后端 BR-069-4 / BR-026，基于「raw 文件名修复 + 走查建议优化」四维度复盘。 |
| v2.7.0 | 2026-08-07 | 新增 FR-067 规则（语音合成神经降级）：朗读/语音合成功能优先 neural TTS（后端合成端点 + 优质 neural 音色）而非浏览器 Web Speech API（FR-TTS-1，建议级）；必须保留浏览器 speechSynthesis 为优雅降级、合成失败不得静默（FR-TTS-2，Critical）；SSML 须转义 <>& 且禁用 <mstts:express-as>（免费端点不支持，WebSocket 关闭 1007）（FR-TTS-3，Critical）；播放前校验音频响应 magic bytes（ff f3 / ff fb / ID3）并在失败前重试 2–3 次（FR-TTS-4，建议级）。SKILL.md Historical Incident Coverage 表追加 1 行，Full-File Mode 第 5 步跨文件一致性检查追加 1 个子项（语音合成神经降级），组装输出类别顺序追加 TTS / Neural Fallback。同步新增 references/tts-neural-fallback-rule.md、config/review-config.md 追加 tts_neural_fallback_frontend 参数段、skill-loader.md 三表追加 FR-067 行。对应 wiki-code-dev CODING-TTS-*，基于「Edge TTS 拟人化朗读改造」复盘。 |
| v2.8.0 | 2026-08-06 | 新增 FR-068 规则（SPA 部署完整性，前端视角）：前端 `vite.config.ts` 的 `build.outDir` 须可被部署注入为全新时间戳目录、不硬编码固定 `../api/public` 原地覆盖（FR-068-1，建议级，规避 safe-delete 钩子 + 残留旧产物 + 清空在服目录，对应后端 BR-071-4）；部署须最后写入完整性标记（`.deploy-complete`）供后端 `isDeployComplete` 门禁识别（FR-068-2，Critical）；前端验证链构建后须校验产物完整（index.html + 关键 bundle）而非仅 vue-tsc（FR-068-3，建议级）。SKILL.md Historical Incident Coverage 表追加 1 行，Full-File Mode 第 5 步跨文件一致性检查追加 1 个子项（SPA 部署完整性），组装输出类别顺序追加 SPA Deploy Integrity。同步新增 references/spa-deploy-integrity-frontend-rule.md、config/review-config.md 追加 spa_live_deploy_frontend 参数段、skill-loader.md 三表追加 FR-068 行。对应后端 BR-071 / wiki-code-dev CODING-SPA-LIVE-DEPLOY，基于「实时部署解析 + /wiki/* 路径穿越加固」复盘。 |
| v2.9.0 | 2026-08-07 | 新增 FR-069 规则（多账户会话隔离，前端视角）：Pinia setup store 会话状态 ref 必须加入 return 对象否则 reset 不可观测（FR-069-1，Critical）；账户切换/登出必须 resetSession 先 reset 再 load（FR-069-2，Critical）；persistConversation 复用 id 前须以 IndexedDB 实际记录校验归属、他人记录绝不覆盖（FR-069-3，Critical）；loadConversations 二次防御 + filterByOwner 严格隔离 + migrateOwnerless 落盘后归属（FR-069-4，建议级）。SKILL.md Historical Incident Coverage 表追加 1 行，Full-File Mode 第 5 步跨文件一致性检查追加 1 个子项（会话跨账户隔离），组装输出类别顺序追加 Session Isolation。同步新增 references/session-isolation-frontend-rule.md、config/review-config.md 追加 session_isolation_frontend 参数段、skill-loader.md 三表追加 FR-069 行。对应 wiki-code-dev CODING-SESSION-ISOLATION，基于「多账户会话隔离泄漏（currentConversationId 模块级共享 ref 跨账户未 reset + scopedOwnerId 漏加 return 死状态 + 复用 id 未校验归属）」复盘。 |
| v2.10.0 | 2026-08-07 | 新增 FR-070（BYOK 多用户密钥代理）与 FR-071（流式回答增量持久化与续答）两组前端规则。FR-070：每用户配置本地命名空间隔离不跨用户共享（FR-070-1，Critical）；密钥仅经请求体下发、仅当配置存在才下发对应块（FR-070-2，Critical）；配置菜单访问门控（敏感 admin tab 二层拦截、个人 BYOK 对全员可见，FR-070-3，建议级）。FR-071：流式分片增量（防抖）落盘而非仅完成时（FR-071-1，Critical）；页面卸载/切页不得 abort 在途流（FR-071-2，Critical）；重载仅对 status:'streaming' 末条续答、interrupted/error 不自动续（FR-071-3，Critical）。SKILL.md Historical Incident Coverage 表追加 2 行，Full-File Mode 第 5 步跨文件一致性检查追加 2 个子项（BYOK / 流式续答），组装输出类别顺序追加 BYOK / Per-User Override 与 Streaming Resume。同步新增 references/byok-per-user-override-frontend-rule.md 与 references/streaming-resume-frontend-rule.md、config/review-config.md 追加 byok_per_user_override_frontend 与 streaming_resume_frontend 两个参数段、skill-loader.md 三表追加 FR-070 与 FR-071 行。对应 wiki-code-dev CODING-BYOK / CODING-STREAMING-RESUME，基于「BYOK 多用户密钥代理」与「断点续答（FR-RM-09）」复盘。 |
| v2.11.0 | 2026-08-08 | 新增 FR-072（隔离测试纪律）：含状态测试须用唯一 userId / 线程 id 命名空间隔离，禁止 `beforeEach(indexedDB.deleteDatabase)`（fake-indexeddb + 已开连接会 onblocked / 泄漏，FR-072-1，Critical）；异步落盘断言须多轮 `setTimeout(0)` flush（轮数从 config 读取，FR-072-2，建议级）；后端用例须重置模块态 / mock 禁止跨用例共享可变单例（FR-072-3，建议级）。SKILL.md Historical Incident Coverage 表追加 1 行，Full-File Mode 第 5 步跨文件一致性检查追加 1 个子项（隔离测试纪律），组装输出类别顺序追加 Test Isolation。同步新增 references/indexeddb-test-isolation-rule.md（wiki-code-dev CODING-TEST-ISOLATION）、config/review-config.md 追加 test_isolation_frontend 参数段、skill-loader.md 三表追加 FR-072 行。对应 wiki-code-dev CODING-TEST-ISOLATION，基于「隔离测试 flaky（fake-indexeddb 删库陷阱）」复盘，与 wiki-auto-testing `indexeddb_test_isolation_check` 参数对齐。 |
| v2.12.0 | 2026-08-07 | 新增 FR-073（SSML / TTS Prosody 参数前端校验，防御纵深）：前端下发 `rate/volume/pitch` 给 TTS 端点前须按 `ssml_injection_frontend.*_regex` 白名单校验并 clamp 到 `default_value`，避免畸形值触发后端免费端点 `SSML is invalid` / 1007（FR-073-1，Critical）；若前端参与 SSML 构造须转义 `<>&` 且禁用 `mstts:express-as`（FR-073-2，Critical，与 FR-067 FR-TTS-3 一致）；前端 prosody 控件须做范围约束（FR-073-3，建议级）。SKILL.md Historical Incident Coverage 表追加 1 行，Full-File Mode 第 5 步跨文件一致性检查追加 1 个子项（SSML / TTS Prosody 参数前端校验），组装输出类别顺序追加 SSML Prosody Injection。同步新增 references/ssml-injection-frontend-rule.md、config/review-config.md 追加 ssml_injection_frontend 参数段、skill-loader.md 三表追加 FR-073 行。对应后端 BR-074 / wiki-code-dev CODING-SSML-INJECTION，基于「TTS 端点 SSML 注入」复盘。 |
| v2.13.0 | 2026-08-08 | 新增 FR-074~FR-076 三组前端规范复盘规则（基于「前端归档按钮迁移」复盘）：FR-074（安全删 DOM 节点）删除功能 DOM（如 `.msg-actions`）前须对测试 / CSS 选择器 `grep` 零引用校验、删除与引用更新同 PR 完成（对应 dom-compat-class-rule.md，与后端 BR-050-2 同一纵深）；FR-075（主题感知图标 TAI）新增 / 修改 SVG 图标须用 `currentColor`（禁硬编码固定色）+ 默认 24x24 + 风格与现有线条图标一致（对应 wiki-code-dev theme-aware-icon-rule.md）；FR-076（能力门控同步）前端功能门控（`:can-archive` 等）须随后端契约放宽同步——后端改为请求体取内容解耦后前端移除 `!!sessionId` 过期依赖、依"内容可得性"放宽，两端放宽同变更完成（对应后端 BR-086 / wiki-code-dev CODING-CAPABILITY-GATING-SYNC）。SKILL.md Historical Incident Coverage 表追加 3 行，Full-File Mode 第 5 步跨文件一致性检查追加 3 个子项（安全删 DOM / 主题感知图标 / 能力门控同步），组装输出类别顺序追加 Safe DOM Delete / Theme Aware Icon / Capability Gating Sync。同步更新 config/review-config.md 追加 safe_dom_delete / theme_aware_icon / capability_gating_sync 三个参数段、skill-loader.md 三表追加 FR-074~FR-076 行。 |
| v2.14.0 | 2026-08-08 | 新增 FR-077~FR-080 四组前端规范复盘规则（基于「问答页交互细节」复盘）：FR-077（编辑重发重新插入）`removeMessagesFrom(i)` 丢弃尾部后必须同函数内 `submitQuestion` 重插 user 消息（否则悬空答案）、先终止在途流式回复再丢弃、文本未变仅退出编辑态（对应 wiki-code-dev CODING-EDIT-RESEND）；FR-078（流式自动贴底滚动）`nextTick`+双 rAF 捕获布局变化、用户上滑超阈值暂停贴底、capture 阶段监听 img load 补滚、监听随容器生命周期绑定解绑（对应 wiki-code-dev CODING-STREAMING-AUTOSCROLL）；FR-079（成对按钮样式一致性）同组确认/取消共享基础样式、差异仅 hover 强调、配色用主题变量、单主操作（对应 wiki-code-dev CODING-BUTTON-STYLE-CONSISTENCY）；FR-080（编辑态撑满列宽）编辑容器 align-items:stretch 撑满整列、textarea width:100% 且内边距与首问一致（对应 wiki-code-dev CODING-EDITBOX-WIDTH）。SKILL.md Historical Incident Coverage 表追加 4 行，Full-File Mode 第 5 步跨文件一致性检查追加 4 个子项，组装输出类别顺序追加 Edit Resend / Chat Autoscroll / Button Style / Editbox Width。同步新增 4 个 references rule 文件、config/review-config.md 追加 edit_resend_frontend / chat_autoscroll_frontend / button_style_frontend / editbox_width_frontend 四个参数段、skill-loader.md 三表追加 FR-077~FR-080 行。 |
| v2.15.0 | 2026-08-08 | 新增 FR-081 规则（IndexedDB 写入前剥离 Vue/Pinia 响应式代理）：凡将 store state ref / `reactive()` 对象经 `dbPut`/`saveUserConfig`/`idbPut`/`store.put` 写入 IndexedDB 的路径，写入前必须整树深拷贝剥离代理，否则 proxy 无法被 `structuredClone` 克隆 → `DataError: [object Array] could not be cloned` → 静默丢配置（FR-081-1，Critical）；禁止 `toRaw()` 当深剥离（嵌套代理仍失败，FR-081-2，Critical）；禁止 `structuredClone(reactiveObj)`（FR-081-3，Critical）；封装函数内部统一 `clone` 防御（FR-081-4，建议级）。SKILL.md Historical Incident Coverage 表追加 1 行，Full-File Mode 第 5 步跨文件一致性检查追加 1 个子项（IndexedDB 写入前剥离响应式代理），组装输出类别顺序追加 IDB Reactive Clone。同步新增 references/idb-reactive-clone-frontend-rule.md、config/review-config.md 追加 idb_reactive_clone_frontend 参数段、skill-loader.md 三表追加 FR-081 行。对应 wiki-code-dev CODING-IDB-REACTIVE-CLONE，基于「userConfig 静默丢配置（proxy 无法被 structuredClone 克隆）」复盘。 |
| v2.16.0 | 2026-08-10 | 新增 FR-082 与 FR-083 两组前端规范复盘规则（基于「初次登录卡死 / 登录按钮永久灰显」四维度复盘，含 Sequential Thinking）：FR-082（认证/异步请求超时兜底）登录/会话校验等关键请求必须 `AbortController` + 可配置超时（默认 `auth_request_timeout_frontend.timeout_ms`），禁止裸 `await fetch` 无超时悬挂；超时须明确可重试文案并解除按钮禁用态（FR-082-1 Critical / FR-082-2 建议）；FR-083（异步操作 loading 复位）进入等待态的交互须在 `try/finally` 复位 `loading`，覆盖成功/失败/超时全路径，禁止遗漏复位致永久「登录中」灰显（FR-083-1 Major / FR-083-2 建议）。SKILL.md Historical Incident Coverage 表追加 2 行，Full-File Mode 第 5 步跨文件一致性检查追加 2 个子项（认证/异步请求超时兜底 / 异步操作 loading 复位），组装输出类别顺序追加 Auth Request Timeout / Auth Loading Reset。同步新增 references/auth-request-timeout-frontend-rule.md 与 references/auth-loading-reset-frontend-rule.md、config/review-config.md 追加 auth_request_timeout_frontend 与 auth_loading_reset_frontend 两个参数段、skill-loader.md 三表追加 FR-082 与 FR-083 行。对应 wiki-code-dev CODING-AUTH-REQUEST-TIMEOUT / CODING-AUTH-LOADING-RESET，并与 wiki-auto-testing `frontend_review_static_check` 的 `auth_request_timeout` / `async_loading_reset` 两组（零硬编码）配置对齐。 |
| v2.17.0 | 2026-08-11 | 新增「配置化与泛化审查」透镜（CODING-CONFIG-DRIVEN / J-CONFIG-FIRST 前端侧）：把「硬编码颜色值 / 硬编码路径·数量 / 非泛化特判 / 配置三层合规」作为所有 FR 的前置独立扫描维度，扫描信号全部来自 `config/review-config.md` 的 `config_driven_frontend` 段（零硬编码）。同步增强 `references/review-output-format.md`：单条 finding 增加可选 `Applicability` 字段、新增「配置化与泛化维度」说明、结尾新增「📐 适用性说明」区块（对齐 wiki-code-dev 复盘维度④）。与 wiki-code-dev CODING-CONFIG-DRIVEN、wiki-backend-code-review 同透镜保持一致。 |
| v2.18.0 | 2026-08-11 | 新增 FR-084（受保护接口必须带鉴权封装调用）与 FR-085（包管理器 store 卫生）两组前端规范复盘规则（基于「401 静默失效 / pnpm store 散落盘根」四维度复盘，含 Sequential Thinking）：FR-084 后端 `requireAuth` 受保护端点（`/api/config`、`/api/ai/config` 等）必须统一经带鉴权封装 `apiFetch` 调用、禁止裸 `fetch` 不带 token（FR-084-1 Critical）；封装须从 `localStorage` 等非 Pinia 源读 token（避免 bootstrap 期取不到，FR-084-2 Critical）；给公开端点加 `requireAuth` 是破坏性变更须审计全部前端调用方（FR-084-3 Major）；FR-085 全局 `.npmrc` 须显式 `store-dir` 收敛 pnpm store、项目/盘根不得存在孤儿 `.pnpm-store`（FR-085-1/2 建议级，CI 前置可升 error）。SKILL.md Historical Incident Coverage 表追加 2 行，Full-File Mode 第 5 步跨文件一致性检查追加 2 个子项（受保护接口带鉴权封装调用 / 包管理器 store 卫生），组装输出类别顺序追加 Auth Request Fetch Wrapping / Pnpm Store Hygiene。同步新增 references/auth-request-fetch-frontend-rule.md 与 references/pnpm-store-hygiene-frontend-rule.md、config/review-config.md 追加 auth_request_fetch_frontend 与 pnpm_store_hygiene_frontend 两个参数段、skill-loader.md 三表追加 FR-084 与 FR-085 行。对应 wiki-code-dev CODING-AUTH-REQUEST-FETCH / CODING-PNPM-STORE-HYGIENE、后端 BR-094 / BR-095，并与 wiki-auto-testing `frontend_review_static_check` 的 `auth_fetch_wrapped` 组（零硬编码）配置对齐。 |
| v2.19.0 | 2026-08-11 | 新增 FR-086~FR-088 三组前端规范复盘规则（基于「移动端聆听页 v-show 常驻后台播放 + TTS 音频 ObjectURL 泄漏 + 两类播放失败混报」四维度复盘，含 Sequential Thinking）：FR-086（常驻组件生命周期隔离）`v-show` 常驻组件须 `watch(visible)` 切回恢复（FR-086-1 Major）、`watch(auth.user?.id)` 显式重置会话态（FR-086-2 Critical，避免账户残留）、重型 DOM 用 `v-if="visible"` 懒渲染（FR-086-3 Major）、vue-tsc 模板收窄（FR-086-4 建议）；FR-087（ObjectURL 生命周期）`createObjectURL`/`revokeObjectURL` 成对（FR-087-1 Major，常驻组件内存泄漏）、句柄收口单一变量（FR-087-2 建议）；FR-088（音频播放可靠性）合成失败与播放拦截文案分离（FR-088-1 Major，避免误报合成失败）、切换曲目重置进度（FR-088-2 建议）。SKILL.md Historical Incident Coverage 表追加 3 行，Full-File Mode 第 5 步跨文件一致性检查追加 3 个子项（常驻组件生命周期隔离 / ObjectURL 生命周期 / 音频播放可靠性），组装输出类别顺序追加 Persistent Component Lifecycle / ObjectURL Lifecycle / Audio Playback Reliability。同步新增 references/persistent-component-lifecycle-frontend-rule.md、references/media-object-url-frontend-rule.md、references/audio-playback-reliability-frontend-rule.md 三个规则文件、config/review-config.md 追加 persistent_component_frontend / media_object_url_frontend / audio_playback_frontend 三个参数段、skill-loader.md 三表追加 FR-086~FR-088 行。对应 wiki-code-dev CODING-PERSISTENT-COMPONENT / CODING-MEDIA-OBJECT-URL / CODING-AUDIO-PLAYBACK-RELIABILITY，并与 wiki-auto-testing `frontend_review_static_check` 的 `persistent_component_visible_watch` / `object_url_revoked` / `audio_autoplay_distinguished` 三个派生组（零硬编码）配置对齐。 |
| v2.20.0 | 2026-08-12 | 新增 FR-089（毛玻璃 backdrop-filter 包含块陷阱）与 FR-090（双主题统一 --m-* 变量架构）两组前端规范复盘规则（基于「移动端双主题切换 + 滚动回顶 FAB 主题间行为不一致 / 双主题变量架构」四维度复盘，含 Sequential Thinking）：FR-089 含 `backdrop-filter` 的滚动容器在毛玻璃主题下成为其内部 `position: fixed` 悬浮元素（滚动 FAB / 全屏 sheet 遮罩）的 containing block、随滚动失固定，浅色主题正常 → 主题间不一致（FR-089-1 Critical，与 FR-040 协同）；组件级主题分支须改 `--m-*` 变量驱动（FR-089-2 Standard）；FR-090 主题相关样式全走 `var(--m-*)`（FR-090-1 Standard）、主题状态集中单一 composable（FR-090-2 Standard）、禁组件级主题分支（FR-090-3 Standard）。SKILL.md Historical Incident Coverage 表追加 2 行，Full-File Mode 第 5 步跨文件一致性检查追加 2 个子项（毛玻璃包含块陷阱 / 双主题变量架构），组装输出类别顺序追加 Backdrop Filter Containing Block / Dual Theme Variable。同步新增 references/backdrop-filter-containing-block-frontend-rule.md、config/review-config.md 追加 backdrop_filter_frontend / dual_theme_var_frontend 两个参数段、skill-loader.md 三表追加 FR-089 / FR-090 行。对应 wiki-code-dev CODING-BACKDROP-FILTER-CB / CODING-DUAL-THEME-VAR，并与 wiki-auto-testing `frontend_review_static_check` 的 `backdrop_filter_fixed_ancestor` 派生组（零硬编码）配置对齐。 |

> 完整版本历史见 [references/changelog.md](references/changelog.md)

## 参考文档

| 文件 | 内容 |
|------|------|
| [references/changelog.md](references/changelog.md) | 版本历史（完整记录） |





