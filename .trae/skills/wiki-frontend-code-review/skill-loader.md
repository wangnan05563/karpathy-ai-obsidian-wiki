本文件仅含规则路由表，技能意图和流程见 SKILL.md。

---

## 1. Rule Overview

| # | 类别 | 规则文件 | 示例文件 | 适用文件模式 | Urgent | Total |
|---|------|---------|---------|------------|--------|-------|
| V1-V6 | Vue Composition | [references/vue-composition-rule.md](references/vue-composition-rule.md) | [examples/vue-composition-rule-examples.md](examples/vue-composition-rule-examples.md) | *.vue, *.tsx | 3 | 6 |
| E1-E6 | Element Plus | [references/element-plus-rule.md](references/element-plus-rule.md) | [examples/element-plus-rule-examples.md](examples/element-plus-rule-examples.md) | *.vue | 3 | 6 |
| P1-P7 | Pinia Store | [references/pinia-store-rule.md](references/pinia-store-rule.md) | [examples/pinia-store-rule-examples.md](examples/pinia-store-rule-examples.md) | *store*.ts, *.vue | 5 | 7 |
| PR1-PR7 | Performance | [references/performance-rule.md](references/performance-rule.md) | [examples/performance-rule-examples.md](examples/performance-rule-examples.md) | *.vue, *.ts | 6 | 8 |
| T1-T9 | Type Safety | [references/type-safety-rule.md](references/type-safety-rule.md) | [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md) | *.ts, *.vue | 8 | 11 |
| TH1-TH6 | Theming | [references/theming-rule.md](references/theming-rule.md) | [examples/theming-rule-examples.md](examples/theming-rule-examples.md) | *.vue, *.css | 3 | 6 |
| CI1-CI3 | Config Isolation | [references/config-isolation-rule.md](references/config-isolation-rule.md) | [examples/config-isolation-rule-examples.md](examples/config-isolation-rule-examples.md) | *config*.vue, *.ts (含 preset/硬编码列表) | 4 | 4 |
| CS1-CS4 | Config State | [references/config-state-rule.md](references/config-state-rule.md) | — | *config*.vue, *form*.vue | 2 | 4 |
| DF1-DF7 | Display Field | [references/display-field-rule.md](references/display-field-rule.md) | — | *task*.vue, *display*.vue | 5 | 7 |
| PB1-PB6 | Persistence Boundary | [references/persistence-boundary-rule.md](references/persistence-boundary-rule.md) | — | *store*.ts, *.vue (含 fetch/dbPut/localStorage) | 5 | 6 |
| ES1-ES6 | Encoding Safety | [references/encoding-safety-rule.md](references/encoding-safety-rule.md) | [examples/encoding-safety-rule-examples.md](examples/encoding-safety-rule-examples.md) | *.vue, *.ts, *.tsx, *.json, *.md, .editorconfig, .vscode/*.json | 6 | 9 |
| ES7-ES9 | Encoding Safety (Runtime) | [references/encoding-safety-rule.md](references/encoding-safety-rule.md) | — | *.vue (含 disabled / UI 文案 / 主题/预设列表) | 1 | 3 |
| DA1-DA8 | Dangerous Action | [references/dangerous-action-rule.md](references/dangerous-action-rule.md) | [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md) | *.vue, *.ts (含 dry_run/danger/ElMessageBox.confirm/cleanup/delete/启动/停止/保存) | 7 | 8 |
| RR1 | Route Registration | [references/route-registration-frontend-rule.md](references/route-registration-frontend-rule.md) | — | views/*.vue, App.vue (SPA 手动路由) | 1 | 1 |
| TS1 | Type Sync | [references/type-sync-frontend-rule.md](references/type-sync-frontend-rule.md) | — | types.ts (前后端) | 1 | 1 |
| SF1 | Sensitive Field Display | [references/sensitive-field-display-rule.md](references/sensitive-field-display-rule.md) | — | *.vue (含 el-input/input + key/token/secret/password/authtoken) | 1 | 1 |
| SC1 | Scroll Container | [references/scroll-container-rule.md](references/scroll-container-rule.md) | — | *.vue, *.css (含 overflow-y: auto / flex-direction: column / glass-card) | 1 | 1 |
| SN1 | SPA Navigation | [references/spa-navigation-rule.md](references/spa-navigation-rule.md) | — | *.vue (含 CustomEvent / dispatchEvent / currentView / 跨视图跳转) | 1 | 1 |
| UC1-UC4 | Update Check | [references/update-check-rule.md](references/update-check-rule.md) | — | *.vue (含 checkUpdate / setInterval / updateState / 检查更新) | 3 | 4 |
| AR1-AR4 | Async Reliability | [references/async-reliability-rule.md](references/async-reliability-rule.md) | — | *.vue, *.ts (含 fetch / axios / EventSource / consumeSSEStream / setInterval / setTimeout) | 3 | 4 |
| FR26 | Typecheck Cache | [references/typecheck-cache-frontend-rule.md](references/typecheck-cache-frontend-rule.md) | — | *.vue, *.ts, *.tsx (含 vue-tsc / as any / @ts-ignore / !. 非空断言) | 2 | 2 |
| FR27 | Composable API | [references/composable-api-frontend-rule.md](references/composable-api-frontend-rule.md) | — | *.vue, *.ts (含 useXxx / defineStore / pinia._s.delete / $dispose / $reset) | 2 | 2 |
| FR28 | Mixed Type Dispatch | [references/mixed-type-dispatch-frontend-rule.md](references/mixed-type-dispatch-frontend-rule.md) | — | *.ts, *.vue (含 as any / as unknown as / T \| U / typeof / in operator / isXxx) | 3 | 3 |
| FR29 | SFC Single Script | [references/sfc-single-script-frontend-rule.md](references/sfc-single-script-frontend-rule.md) | — | *.vue (含 `<script>` / `<script setup>` / 双 script 块 / defineOptions) | 2 | 2 |
| FR30 | E2E Precheck | [references/e2e-precheck-frontend-rule.md](references/e2e-precheck-frontend-rule.md) | — | playwright.config.ts, e2e/setup.ts, conftest.py, *.spec.ts (含 playwright / test_*.py / ERR_CONNECTION_REFUSED) | 2 | 2 |
| FR31 | Test Case Sync | [references/test-case-sync-frontend-rule.md](references/test-case-sync-frontend-rule.md) | — | *.vue, *.tsx, *.spec.ts, *.test.ts, test_*.py (含 page.locator / try/except / query-head / selector) | 4 | 4 |
| FR32 | Reading Viewport | [references/reading-viewport-frontend-rule.md](references/reading-viewport-frontend-rule.md) | — | Query.vue, Reader.vue, Help.vue, ChatView.vue (含 input-bar / sticky bottom / 毛玻璃 / overflow-y) | 3 | 3 |
| FR41 | Tauri Invoke | [references/tauri-invoke-rule.md](references/tauri-invoke-rule.md) | — | *.vue, *.ts (含 invoke('xxx') / @tauri-apps/api / tauri.conf.json / build.rs / capabilities / lib.rs) | 3 | 3 |
| FR42 | Tauri Transparent CSS | [references/tauri-transparent-css-rule.md](references/tauri-transparent-css-rule.md) | — | *.vue, *.css (含 transparent / floating-active / :global(html.floating-active *) / backdrop-filter / glass-card) | 3 | 4 |
| FR43 | Tauri Drag Click | [references/tauri-drag-click-rule.md](references/tauri-drag-click-rule.md) | — | *.vue, *.ts (含 data-tauri-drag-region / start_dragging / mousedown / mousemove / mouseup) | 3 | 4 |
| FR44 | Test Selector Priority | [references/test-selector-priority-rule.md](references/test-selector-priority-rule.md) | — | *.spec.ts, *.test.ts, test_*.py, *.vue, *.tsx (含 placeholder / :has-text / networkidle / wait_until / page.locator / [data-testid / waitForSelector) | 1 | 4 |
| FR45 | Control Layering | [references/control-layering-frontend-rule.md](references/control-layering-frontend-rule.md) | — | *.vue (含 button-bar / .folding-panel / el-collapse / el-popover / Transition / aria-expanded / @mousedown.stop) | 2 | 5 |
| FR46 | Third-Party Error Guard | [references/third-party-error-guard-frontend-rule.md](references/third-party-error-guard-frontend-rule.md) | — | *.vue, *.ts (含 mermaid / katex / Prism / mermaid.render / katex.render / Prism.highlight / suppressErrorRendering / throwOnError) | 3 | 5 |
| FR47 | Folding Panel Event | [references/folding-panel-event-frontend-rule.md](references/folding-panel-event-frontend-rule.md) | — | *.vue (含 click outside / useClickOutside / v-click-outside / el-dropdown / hide-on-click / @click.stop / @mousedown.stop / Teleport) | 3 | 5 |
| FR48 | Long Task Architecture | [references/long-task-architecture-frontend-rule.md](references/long-task-architecture-frontend-rule.md) | — | *.vue, *.ts (含 EventSource / consumeSSEStream / fetch /api/media/video / setInterval poll / 400 / 429 / 500 状态码 / 后端服务未运行) | 3 | 4 |
| FR49 | SSE Event Dispatch | [references/sse-event-dispatch-frontend-rule.md](references/sse-event-dispatch-frontend-rule.md) | — | *.ts, *.vue (含 consumeSSEStream / EventSource / if/else if 事件分发 / Record<string, Handler> / outputMode / outputModes / 联合字面量类型) | 3 | 5 |
| FR50 | SSE Stream Error | [references/sse-stream-error-frontend-rule.md](references/sse-stream-error-frontend-rule.md) | — | *.ts, *.vue (含 consumeSSEStream / getReader / reader.cancel / AbortError / AbortController / abortReason / signal?: AbortSignal) | 3 | 5 |
| FR51 | Long Task Polling UI | [references/long-task-polling-ui-frontend-rule.md](references/long-task-polling-ui-frontend-rule.md) | — | *.vue, *.ts (含 setInterval / poll / AbortSignal.timeout / setTimeout abort / videoState / closeDialog / resetState / onBeforeUnmount clearInterval) | 3 | 6 |
| FR52 | Event Delegation | [references/event-delegation-frontend-rule.md](references/event-delegation-frontend-rule.md) | — | *.vue (含 v-html / addEventListener / removeEventListener / closest / target.tagName / globalThis / window / destroy / dispose / mermaid.initialize) | 3 | 5 |
| FR53 | Heavy Library | [references/heavy-library-frontend-rule.md](references/heavy-library-frontend-rule.md) | — | *.vue, *.ts (含 import mermaid / import marpit / dynamic import / mod.default / nextTick / mermaid.render / marpInstance / monaco.editor) | 2 | 6 |
| FR61 | TS/JS Shadowing | [references/ts-js-shadowing-frontend-rule.md](references/ts-js-shadowing-frontend-rule.md) | — | *.ts, *.vue, vite.config.ts (含 src/**/*.js, *.js.map, resolve.extensions, vue-tsc, vite build, 编译产物) | 2 | 3 |
| FR62 | Type Sync Done Event | [references/type-sync-done-event-rule.md](references/type-sync-done-event-rule.md) | — | types.ts, *.ts (含 done event, governor, threadId, export interface, additive, optional, SSE 字段新增) | 2 | 2 |
| FR63 | Runtime Data Privacy | [references/runtime-data-privacy-frontend-rule.md](references/runtime-data-privacy-frontend-rule.md) | — | *.ts, *.vue (含 IndexedDB, localStorage, 新磁盘目录, gitignore, persistSessions, 服务端会话) | 2 | 2 |
| FR64 | Packaging Config | [references/packaging-config-rule.md](references/packaging-config-rule.md) | — | *.vue, *.ts, *.ps1, *.iss (含 机器绝对路径/Program Files/用户数据路径/vaultPath 字面量) | 1 | 3 |
| FR65 | Element Plus Radio Deprecation | [references/element-plus-rule.md](references/element-plus-rule.md) | — | *.vue (含 el-radio / el-radio-button + label= 作 value) | 1 | 2 |
| FR66 | Optional Contract Field | [references/optional-contract-field-rule.md](references/optional-contract-field-rule.md) | — | types.ts, *.ts (含 CompileInput / QueryInput / originalName / optional / 后端内部字段 / 前端不消费 / ?? 兜底) | 1 | 3 |
| FR67 | TTS Neural Fallback | [references/tts-neural-fallback-rule.md](references/tts-neural-fallback-rule.md) | — | *.vue, *.ts (含 speechSynthesis / SpeechSynthesisUtterance / /api/tts/synthesize / new Audio / prosody / express-as / volume|pitch|rate / 朗读) | 1 | 4 |
| FR68 | SPA Deploy Integrity | [references/spa-deploy-integrity-frontend-rule.md](references/spa-deploy-integrity-frontend-rule.md) | — | vite.config.ts, build*.{ps1,sh,mjs}, _deploy_live*.mjs, *.vue, *.ts (含 outDir / emptyOutDir / public_live_ / .deploy-complete / 时间戳目录 / 部署完整性) | 1 | 3 |
| FR69 | Session Isolation | [references/session-isolation-frontend-rule.md](references/session-isolation-frontend-rule.md) | — | *store*.ts, *.vue (含 currentConversationId / scopedOwnerId / resetSession / loadConversations / persistConversation / dbGet / filterByOwner / user?.id / 跨账户 / 登出) | 4 | 4 |
| FR70 | BYOK Per-User Override | [references/byok-per-user-override-frontend-rule.md](references/byok-per-user-override-frontend-rule.md) | — | services/userConfig.ts, views/Config.vue, views/Query.vue, *.ts (含 usercfg:: / loadAiUserConfig / llmConfig / toolsConfig / apiKey / 配置菜单 / isAdmin / v-if="isAdmin" / 命名空间) | 3 | 3 |
| FR71 | Streaming Resume | [references/streaming-resume-frontend-rule.md](references/streaming-resume-frontend-rule.md) | — | stores/query.ts, views/Query.vue, constants/storageKeys.ts, types.ts (含 streamingAnswer / persistConversation / onBeforeUnmount / abortController / LAST_ACTIVE_CONVERSATION / status:'streaming' / resumeLastAnswer / 断点续答) | 3 | 3 |
| FR72 | Test Isolation | [references/indexeddb-test-isolation-rule.md](references/indexeddb-test-isolation-rule.md) | — | *.test.ts, *.spec.ts, test_*.py, *.ts (含 indexedDB / localStorage / deleteDatabase / setTimeout(0) / vi.clearAllMocks / vi.resetModules / 唯一命名空间 / beforeEach) | 3 | 3 |
| FR73 | SSML Prosody Injection | [references/ssml-injection-frontend-rule.md](references/ssml-injection-frontend-rule.md) | — | *.vue, *.ts (含 /api/tts/synthesize / EdgeTtsProvider / prosody / rate|volume|pitch / 语音控件 / 朗读) | 2 | 3 |
| FR74 | Safe DOM Delete | [references/dom-compat-class-frontend-rule.md](references/dom-compat-class-frontend-rule.md) | — | *.vue, *.ts (含 removeChild / classList.remove / 删 DOM / 删 .msg-actions / 引用清零 / 安全删) | 1 | 3 |
| FR75 | Theme Aware Icon | [references/theme-aware-icon-frontend-rule.md](references/theme-aware-icon-frontend-rule.md) | — | *.vue, *.svg, *.ts (含 <svg / currentColor / 24x24 / 线条 / stroke / 图标) | 1 | 2 |
| FR76 | Capability Gating Sync | [references/capability-gating-sync-frontend-rule.md](references/capability-gating-sync-frontend-rule.md) | — | *.vue, *.ts (含 !!sessionId / !!getSession / 门控 / v-if / 能力门控 / 内容可得性) | 1 | 2 |
| FR77 | Edit Resend | [references/edit-resend-frontend-rule.md](references/edit-resend-frontend-rule.md) | — | views/Query.vue, stores/query.ts, components/MessageToolbar.vue (含 removeMessagesFrom / submitQuestion / editingIdx / 编辑重发 / 悬空答案 / isLoading) | 2 | 3 |
| FR78 | Chat Autoscroll | [references/chat-autoscroll-frontend-rule.md](references/chat-autoscroll-frontend-rule.md) | — | composables/useChatAutoScroll.ts, views/Query.vue, components/FloatingChat.vue (含 scrollToBottom / double rAF / stickToBottom / img load / 监听绑定解绑 / 贴底) | 1 | 5 |
| FR79 | Button Style | [references/button-style-frontend-rule.md](references/button-style-frontend-rule.md) | — | *.vue (含 .edit-btn.confirm / .edit-btn.cancel / 确认 / 取消 / type="primary" / 主题变量 / 成对按钮) | 0 | 3 |
| FR80 | Editbox Width | [references/editbox-width-frontend-rule.md](references/editbox-width-frontend-rule.md) | — | views/Query.vue, *.vue (含 .msg-content-wrapper.editing / .msg-edit / flex-end / align-items:stretch / width:100% / 编辑态撑满) | 0 | 3 |
| FR81 | IDB Reactive Clone | [references/idb-reactive-clone-frontend-rule.md](references/idb-reactive-clone-frontend-rule.md) | — | services/*UserConfig*.ts, *store*.ts (含 dbPut / saveUserConfig / idbPut / store.put / reactive / toRaw / structuredClone / [object Array] could not be cloned) | 3 | 4 |
| FR82 | Auth Request Timeout | [references/auth-request-timeout-frontend-rule.md](references/auth-request-timeout-frontend-rule.md) | — | stores/auth.ts, *store*.ts, api/auth.ts, views/Login.vue (含 login / fetch / AbortController / AbortSignal.timeout / 登录中 / 登录超时 / 超时) | 2 | 0 |
| FR83 | Auth Loading Reset | [references/auth-loading-reset-frontend-rule.md](references/auth-loading-reset-frontend-rule.md) | — | views/Login.vue, *store*.ts, *.vue (含 loading=true / submitting=true / try / finally / 登录中 / 灰显) | 2 | 0 |
| FR84 | Auth Request Fetch | [references/auth-request-fetch-frontend-rule.md](references/auth-request-fetch-frontend-rule.md) | — | *.vue, *.ts (含 fetch('/api/config') / fetch('/api/ai/config') / apiFetch / Authorization / Bearer / 受保护端点 / requireAuth / bootstrap) | 3 | 0 |
| FR85 | Pnpm Store Hygiene | [references/pnpm-store-hygiene-frontend-rule.md](references/pnpm-store-hygiene-frontend-rule.md) | — | .npmrc, *.ps1, build*.{ps1,sh,mjs} (含 store-dir / .pnpm-store / pnpm store path / 孤儿 store / 收敛) | 0 | 2 |
| FR86 | Persistent Component Lifecycle | [references/persistent-component-lifecycle-frontend-rule.md](references/persistent-component-lifecycle-frontend-rule.md) | — | *.vue, *.ts (含 v-show / props.visible / watch(visible) / watch(auth.user?.id) / onMounted 仅一次 / 重型 DOM / v-if="visible" / vue-tsc 收窄 / 切回恢复 / 账户切换) | 1 | 4 |
| FR87 | ObjectURL Lifecycle | [references/media-object-url-frontend-rule.md](references/media-object-url-frontend-rule.md) | — | *.vue, *.ts (含 URL.createObjectURL / revokeObjectURL / blob / objectUrl / 常驻组件 / 切换曲目 / 图片预览 / 文件下载) | 0 | 2 |
| FR88 | Audio Playback Reliability | [references/audio-playback-reliability-frontend-rule.md](references/audio-playback-reliability-frontend-rule.md) | — | *.vue, *.ts (含 <audio> / a.play() / 语音合成失败 / 播放被浏览器拦截 / position / duration / 朗读队列 / res.ok / 进度重置) | 1 | 2 |
| FR89 | Backdrop Filter Containing Block | [references/backdrop-filter-containing-block-frontend-rule.md](references/backdrop-filter-containing-block-frontend-rule.md) | — | *.vue, *.css (含 backdrop-filter / -webkit-backdrop-filter / position: fixed / .mobile-content / scroll-fab / sheet-mask / Teleport / --m-blur) | 1 | 2 |
| FR90 | Dual Theme Variable | [references/dual-theme-variable-frontend-rule.md](references/dual-theme-variable-frontend-rule.md) | — | *.vue, *.css, *.ts (含 --m- / theme-light / .mobile-root / useMobileTheme / 主题变量 / 切换主题 / karpathy-mobile-theme) | 0 | 3 |
| FR91 | Download Timeout/Abort | [references/download-timeout-abort-frontend-rule.md](references/download-timeout-abort-frontend-rule.md) | — | *.ts, *.vue (含 fetch(, downloadVaultFile, AbortSignal.timeout, blob, 下载, 超时, 大文件, 挂起) | 0 | 2 |
| FR92 | Download Mobile Silent Guard | [references/download-mobile-silent-guard-frontend-rule.md](references/download-mobile-silent-guard-frontend-rule.md) | — | *.ts, *.vue (含 downloadVaultFile, MobileBrowse, 下载, 错误提示, Toast, 静默, 失败兜底, 点了没反应) | 1 | 2 |
| FR93 | Download Reentry Guard | [references/download-reentry-guard-frontend-rule.md](references/download-reentry-guard-frontend-rule.md) | — | *.ts, *.vue (含 downloadVaultFile, downloading, in-flight, 防重复点击, 重入, 并发下载) | 0 | 2 |
| FR94 | Content-Disposition Filename | [references/content-disposition-filename-frontend-rule.md](references/content-disposition-filename-frontend-rule.md) | — | *.ts, *.vue (含 Content-Disposition, filename*, RFC 5987, 扩展名, 文件名解析, blob, 中文文件名) | 0 | 3 |

## 2. Quick Routing Table

| 文件特征 | 必加载规则 | 条件加载规则 |
|---------|-----------|------------|
| *.vue + <script setup> | vue-composition, encoding-safety | element-plus (if el-*), performance (if is-network), theming (if data-theme), pinia-store (if defineStore), dangerous-action (if dry_run/danger/ElMessageBox.confirm/启动/停止/保存), route-registration (if 文件在 views/ 下或为 App.vue), sensitive-field-display (if el-input 含 key/token/password), async-reliability (if fetch/axios/SSE/setInterval/setTimeout) |
| *store*.ts | pinia-store, type-safety, persistence-boundary, encoding-safety | async-reliability (if fetch/axios/SSE) |
| *.vue + 表单 | element-plus, config-state, encoding-safety | dangerous-action (if dry_run/cleanup/delete/启动/停止/保存), sensitive-field-display (if 含 key/token/secret/password/authtoken 字段), async-reliability (if async submit) |
| *.ts + fetch/JSON.parse | type-safety, encoding-safety | performance (if SSE), type-sync (if 文件为 types.ts 或含 export interface), async-reliability (if fetch/axios/SSE) |
| *.vue + 主题切换 | theming | vue-composition |
| *config*form*.vue | config-isolation, config-state, element-plus, persistence-boundary, encoding-safety | dangerous-action (if type="danger" / 恢复初始 / 保存), sensitive-field-display (if 含敏感字段) |
| *display* / *task* | display-field, type-safety | dangerous-action (if delete/cleanup) |
| *.vue / *.ts + dry_run / danger / cleanup / delete / 启动 / 停止 / 保存 / 删除 / 清除 / 重置 | dangerous-action | — |
| *.json / .editorconfig / .vscode/*.json | encoding-safety | — |
| views/*.vue 或 App.vue | route-registration, encoding-safety | vue-composition (if <script setup>) |
| types.ts (前端或后端) | type-sync, type-safety, encoding-safety | — |
| *.vue + el-input/input 含 key/token/secret/password/authtoken | sensitive-field-display, encoding-safety | config-isolation (if 同时是配置页), element-plus (if el-input) |
| *.vue / *.css + overflow-y: auto / flex-direction: column / glass-card | scroll-container, encoding-safety | theming (if 同时涉及主题色) |
| *.vue + CustomEvent / dispatchEvent / currentView / 跨视图跳转 | spa-navigation, encoding-safety | route-registration (if 文件在 views/ 下或为 App.vue), vue-composition (if <script setup>) |
| *.vue + checkUpdate / setInterval / updateState / 检查更新 | update-check, encoding-safety | dangerous-action (if 含重试按钮 type="danger"), vue-composition (if <script setup>) |
| 任何 *.vue / *.ts / *.tsx 文件 Edit 后或构建前 | encoding-safety | — |
| *.vue / *.ts / *.tsx + vue-tsc 报告与源码不一致 / as any / @ts-ignore / !. 非空断言 | typecheck-cache-frontend (FR26) | type-safety (if 真实类型不匹配) |
| *.vue / *.ts + useXxx / defineStore / pinia._s.delete / $dispose / $reset | composable-api-frontend (FR27) | pinia-store (if defineStore), type-safety (if ref/reactive 误用) |
| *.ts / *.vue + as any / as unknown as / T \| U 联合类型 / typeof / in operator | mixed-type-dispatch-frontend (FR28) | type-safety (if 收窄逻辑), type-sync (if 联合类型来自后端) |
| *.vue + `<script>` / `<script setup>` / 双 script 块 / defineOptions | sfc-single-script-frontend (FR29) | vue-composition (if <script setup>), encoding-safety (if Edit 后) |
| playwright.config.ts / e2e/setup.ts / conftest.py + playwright / test_*.py / ERR_CONNECTION_REFUSED | e2e-precheck-frontend (FR30) | async-reliability (if 健康检查含 fetch) |
| *.vue / *.tsx + DOM 变更（class/id/data-testid/文案/结构/v-if）+ *.spec.ts/test_*.py | test-case-sync-frontend (FR31) | encoding-safety (if Edit 后) |
| Query.vue / Reader.vue / Help.vue / ChatView.vue + input-bar / sticky / 毛玻璃 / overflow-y | reading-viewport-frontend (FR32) | scroll-container (if overflow-y: auto), theming (if 毛玻璃) |
| *.vue / *.ts + invoke('xxx') / @tauri-apps/api / tauri.conf.json / src-tauri/ | tauri-invoke-rule (FR41) | tauri-drag-click-rule (if 含 start_dragging / data-tauri-drag-region) |
| *.vue / *.css + transparent: true / floating-active / :global(html.floating-active *) / glass-card | tauri-transparent-css-rule (FR42) | theming (if 毛玻璃), scroll-container (if overflow-y) |
| *.vue / *.ts + data-tauri-drag-region / start_dragging / @mousedown + @click 同元素 | tauri-drag-click-rule (FR43) | tauri-invoke-rule (if invoke 调用), vue-composition (if <script setup>) |
| *.spec.ts / *.test.ts / test_*.py + placeholder / :has-text / networkidle / wait_until / page.locator / [data-testid | test-selector-priority-rule (FR44) | test-case-sync-frontend (if DOM 变更同步), e2e-precheck-frontend (if playwright.config.ts) |
| *.vue + button-bar / .folding-panel / el-collapse / el-popover / 控件数 > 5 / Transition / aria-expanded | control-layering-frontend-rule (FR45) | folding-panel-event-frontend-rule (if 含 click outside / el-dropdown), vue-composition (if <script setup>), theming (if 含主题色) |
| *.vue / *.ts + mermaid / katex / Prism / mermaid.render / katex.render / Prism.highlight / suppressErrorRendering / throwOnError | third-party-error-guard-frontend-rule (FR46) | async-reliability (if 库渲染为异步), encoding-safety (if Edit 后) |
| *.vue + click outside / useClickOutside / v-click-outside / el-dropdown / hide-on-click / @click.stop / @mousedown.stop / Teleport to body | folding-panel-event-frontend-rule (FR47) | control-layering-frontend-rule (if 含折叠面板分层), element-plus (if el-dropdown) |
| *.vue / *.ts + EventSource / consumeSSEStream / fetch /api/media/video / setInterval poll / 400 / 429 / 500 状态码 / 后端服务未运行 | long-task-architecture-frontend-rule (FR48) | async-reliability (if fetch/axios), long-task-polling-ui-frontend-rule (if setInterval poll) |
| *.ts / *.vue + consumeSSEStream / EventSource / if/else if 事件分发 / outputMode / outputModes / Record<string, Handler> | sse-event-dispatch-frontend-rule (FR49) | sse-stream-error-frontend-rule (if catch AbortError), async-reliability (if SSE) |
| *.ts / *.vue + consumeSSEStream / getReader / reader.cancel / AbortError / AbortController / abortReason / signal?: AbortSignal | sse-stream-error-frontend-rule (FR50) | sse-event-dispatch-frontend-rule (if 事件分发), async-reliability (if fetch stream) |
| *.vue / *.ts + setInterval / poll / AbortSignal.timeout / setTimeout abort / videoState / closeDialog / resetState / onBeforeUnmount clearInterval | long-task-polling-ui-frontend-rule (FR51) | long-task-architecture-frontend-rule (if 任务架构选择), async-reliability (if 定时器), event-delegation-frontend-rule (if addEventListener) |
| *.vue + v-html / addEventListener / removeEventListener / closest / target.tagName / globalThis / window / destroy / dispose | event-delegation-frontend-rule (FR52) | heavy-library-frontend-rule (if 含 mermaid/marp/monaco 库), third-party-error-guard-frontend-rule (if 库渲染), encoding-safety (if Edit 后) |
| *.vue / *.ts + import mermaid / import marpit / dynamic import / mod.default / nextTick / mermaid.render / marpInstance / monaco.editor | heavy-library-frontend-rule (FR53) | third-party-error-guard-frontend-rule (if 库渲染错误防护), event-delegation-frontend-rule (if 库实例需销毁), encoding-safety (if Edit 后) |
| *.ts / *.vue + src/**/*.js / *.js.map / resolve.extensions / vue-tsc / vite build | ts-js-shadowing-frontend-rule (FR61) | typecheck-cache-frontend-rule (FR26, if 幽灵错误), encoding-safety (if Edit 后) |
| types.ts + done event / governor / threadId / export interface / SSE 字段新增 | type-sync-done-event-rule (FR62) | type-sync-frontend-rule (TS-1), type-safety (if 类型不匹配) |
| *.ts / *.vue + IndexedDB / localStorage / 新磁盘目录 / gitignore / persistSessions | runtime-data-privacy-frontend-rule (FR63) | persistence-boundary-rule (PB1-PB6), sensitive-field-display-rule (SF1) |
| *.vue + el-radio / el-radio-button + label= 作 value / ElementPlusError label act as value | element-plus-rule (FR65) | encoding-safety (if Edit 后) |
| types.ts / *.ts + CompileInput / QueryInput / originalName / 后端内部可选字段 / 前端不消费 / ?? 兜底 / 同 PR 同步可选 | optional-contract-field-rule (FR66) | type-sync-frontend-rule (TS-1), type-sync-done-event-rule (FR62, if SSE 字段), type-safety (if 类型不匹配) |
| *.vue / *.ts + speechSynthesis / SpeechSynthesisUtterance / /api/tts/synthesize / prosody / express-as / new Audio / 朗读 | tts-neural-fallback-rule (FR67) | async-reliability (if fetch/axios 合成请求) |
| vite.config.ts / build*.{ps1,sh,mjs} / _deploy_live*.mjs + outDir / emptyOutDir / public_live_ / .deploy-complete / 时间戳目录 / 部署完整性 | spa-deploy-integrity-frontend-rule (FR68) | ts-js-shadowing-frontend-rule (FR61, if 构建产物残留), build-artifact (if 产物验证) |
| *store*.ts / *.vue + currentConversationId / scopedOwnerId / resetSession / loadConversations / persistConversation / dbGet / filterByOwner / user?.id / 跨账户 / 登出 | session-isolation-frontend-rule (FR69) | runtime-data-privacy-frontend-rule (FR63, if 客户端按 ownerId 隔离), config-isolation-rule (if 多账户配置命名空间) |
| services/userConfig.ts / views/Config.vue / views/Query.vue + usercfg:: / loadAiUserConfig / llmConfig / toolsConfig / apiKey / 配置菜单 / isAdmin / v-if="isAdmin" / 命名空间 / BYOK | byok-per-user-override-frontend-rule (FR70) | runtime-data-privacy-frontend-rule (FR63, if 密钥/IndexedDB), config-isolation-rule (if 多账户配置隔离) |
| stores/query.ts / views/Query.vue + streamingAnswer / persistConversation / onBeforeUnmount / abortController / LAST_ACTIVE_CONVERSATION / status:'streaming' / resumeLastAnswer / 断点续答 | streaming-resume-frontend-rule (FR71) | sse-event-dispatch-frontend-rule (if SSE 事件分发), persistence-boundary-frontend-rule (if 客户端持久化) |
| *.test.ts / *.spec.ts / test_*.py + indexedDB / localStorage / deleteDatabase / setTimeout(0) flush / vi.clearAllMocks / vi.resetModules / 唯一命名空间 / 唯一 userId | indexeddb-test-isolation-rule (FR72) | runtime-data-privacy-frontend-rule (FR63, if IndexedDB 持久化), config-isolation-rule (if 多账户配置命名空间) |
| *.vue / *.ts + /api/tts/synthesize / EdgeTtsProvider / prosody / rate|volume|pitch / 语音控件 / 朗读 | ssml-injection-frontend-rule (FR73) | tts-neural-fallback-rule (FR67, if 后端合成 + 降级), async-reliability (if fetch 合成请求) |
| *.vue / *.ts + 删除 DOM 节点 / removeChild / classList.remove / 删 .msg-actions / 引用清零 / 安全删 | safe-dom-delete-rule (FR74) | test-case-sync-frontend-rule (if 引用同步), encoding-safety (if Edit 后) |
| *.vue / *.svg + <svg / fill= / stroke= / currentColor / 24x24 / 线条图标 / 图标主题 | theme-aware-icon-frontend-rule (FR75) | theming (if 主题色), icon-and-navigation-rule (if 图标导航) |
| *.vue / *.ts + !!sessionId / !!getSession / v-if 门控 / can-archive / 内容可得性 | capability-gating-sync-frontend-rule (FR76) | backend-review-static-check (if 后端契约同步) |
| *.vue / *.ts + removeMessagesFrom / submitQuestion / editingIdx / 编辑重发 / 悬空答案 / isLoading / 编辑态发送 | edit-resend-frontend-rule (FR77) | streaming-resume-frontend-rule (FR71, if 影响断点续答状态), backend-review-static-check (if 后端 /messages 端点契约) |
| composables/*.ts / *.vue + scrollToBottom / double rAF / stickToBottom / 监听绑定解绑 / img load 补滚 / 贴底 / 用户滚动暂停 | chat-autoscroll-frontend-rule (FR78) | streaming-resume-frontend-rule (FR71, if 流式中滚动) |
| *.vue + .edit-btn.confirm / .edit-btn.cancel / 确认 / 取消 / type="primary" / 成对按钮 / 主题变量 | button-style-frontend-rule (FR79) | theming (if 主题色), icon-and-navigation-rule (if 图标按钮) |
| *.vue + .msg-content-wrapper.editing / .msg-edit / flex-end / align-items:stretch / width:100% / 编辑态撑满 / 输入框宽度 | editbox-width-frontend-rule (FR80) | responsive-layout (if 响应式) |
| services/*UserConfig*.ts / *store*.ts + dbPut / saveUserConfig / idbPut / store.put / reactive( / toRaw( / structuredClone( / [object Array] could not be cloned / 深拷贝 / clone( | idb-reactive-clone-frontend-rule (FR81) | persistence-boundary-rule (if 客户端持久化), runtime-data-privacy-frontend-rule (FR63, if IndexedDB 命名空间) |
| stores/auth.ts / *store*.ts / api/auth.ts + login / fetch / AbortController / AbortSignal.timeout / 登录中 / 登录超时 | auth-request-timeout-frontend-rule (FR82) | async-reliability-frontend-rule (AR-1~AR-4, if SSE/定时器) |
| views/Login.vue / *.vue + loading=true / submitting=true / try / finally / 登录中 / 灰显 | auth-loading-reset-frontend-rule (FR83) | — |
| *.vue / *.ts + fetch('/api/config') / fetch('/api/ai/config') / apiFetch / Authorization / Bearer / 受保护端点 / bootstrap / 401 | auth-request-fetch-frontend-rule (FR84) | backend-review-static-check (if 后端 requireAuth 契约), async-reliability-frontend-rule (if fetch/axios) |
| ~/.npmrc / .npmrc + store-dir / pnpm store path / .pnpm-store / 孤儿 store / 收敛 | pnpm-store-hygiene-frontend-rule (FR85) | dependency-store-hygiene-check (if 后端 BR-095 同查) |
| *.vue / *.ts + v-show 常驻 / props.visible / watch(visible) / watch(auth.user?.id) / onMounted 仅一次 / 重型 DOM / v-if="visible" / vue-tsc 收窄 | persistent-component-lifecycle-frontend-rule (FR86) | session-isolation-frontend-rule (if 账户切换 resetSession), media-object-url-frontend-rule (if 含 createObjectURL) |
| *.vue / *.ts + URL.createObjectURL / revokeObjectURL / blob / objectUrl / 常驻组件 / 切换曲目 | media-object-url-frontend-rule (FR87) | persistent-component-lifecycle-frontend-rule (if v-show 常驻), audio-playback-reliability-frontend-rule (if <audio> 播放) |
| *.vue / *.ts + <audio> / a.play() / 语音合成失败 / 播放被浏览器拦截 / position / duration / 朗读队列 / res.ok | audio-playback-reliability-frontend-rule (FR88) | media-object-url-frontend-rule (if createObjectURL), tts-neural-fallback-rule (FR67, if 后端合成 + 降级) |
| *.vue / *.css + backdrop-filter / -webkit-backdrop-filter / .mobile-content / scroll-fab / position: fixed / Teleport / --m-blur / 毛玻璃滚动容器 | backdrop-filter-containing-block-frontend-rule (FR89) | dual-theme-variable-frontend-rule (if 主题变量 --m-), theming (if 毛玻璃主题色) |
| *.vue / *.css / *.ts + --m- / theme-light / .mobile-root / useMobileTheme / 主题变量 / 切换主题 / karpathy-mobile-theme / data-theme | dual-theme-variable-frontend-rule (FR90) | backdrop-filter-containing-block-frontend-rule (if 含 backdrop-filter 容器), theming (if 主题色), config-isolation-rule (if 多主题配置命名空间) |
| *.ts / *.vue + fetch( / downloadVaultFile / AbortSignal.timeout / blob / URL.createObjectURL / 下载 / 超时 / 大文件 | download-timeout-abort-frontend-rule (FR91) | download-reentry-guard-frontend-rule (FR93, if 防重复点击), download-mobile-silent-guard-frontend-rule (FR92, if 移动端), content-disposition-filename-frontend-rule (FR94, if 文件名解析), async-reliability-frontend-rule (if fetch/axios) |
| *.ts / *.vue + downloadVaultFile / MobileBrowse / 下载 / 错误提示 / Toast / 静默 / 失败兜底 / 点了没反应 | download-mobile-silent-guard-frontend-rule (FR92) | download-timeout-abort-frontend-rule (FR91, if 超时), download-reentry-guard-frontend-rule (FR93, if 重入) |
| *.ts / *.vue + downloadVaultFile / downloading / in-flight / 防重复点击 / 重入 / 并发下载 | download-reentry-guard-frontend-rule (FR93) | download-timeout-abort-frontend-rule (FR91, if 超时), download-mobile-silent-guard-frontend-rule (FR92, if 移动端) |
| *.ts / *.vue + Content-Disposition / filename* / RFC 5987 / 扩展名 / 文件名解析 / blob / 中文文件名 | content-disposition-filename-frontend-rule (FR94) | download-timeout-abort-frontend-rule (FR91, if fetch 下载), media-object-url-frontend-rule (FR87, if createObjectURL) |

## 3. Keyword Scanning Guide

Scan the first 50 lines of a target file for these keywords to determine rule categories:

| Category | Keywords to Search |
|----------|-------------------|
| vue-composition | <script setup, 
ef(, 
eactive(, computed(, watch(, onMounted, onBeforeUnmount |
| element-plus | el-, ElMessage, ElDialog, ElForm, ElButton, ElIcon, 
-loading |
| pinia-store | defineStore, pinia, useXxxStore, state:, ctions: |
| performance | 
is-network, Network, 
esize, 
-for, onMessage, ReadableStream |
| type-safety | interface , ype , Promise<, etch(, JSON.parse, s const, reactive<, noUnusedLocals |
| theming | data-theme, getComputedStyle, gba(, ar(--, ill=, stroke= |
| config-isolation | localStorage, piKey, ****, preset, ccountConfig |
| config-state | config, orm, save, oggle, eature |
| display-field | display, rand, egion, seller, ield_map, 
ormalize |
| encoding-safety | UTF-8, BOM, GB2312, U+FFFD, TextDecoder, UTF8Encoding, .editorconfig, settings.json, \uFFFD |
| dangerous-action | dry_run, dryRun, type="danger", .danger, ElMessageBox.confirm, 不可撤销, cleanup, delete, 审计日志, 启动, 停止, 保存, 清除, 重置 |
| route-registration | views/, App.vue, ViewName, v-else-if, currentView, tabs |
| type-sync | export interface, types.ts, backend, frontend |
| sensitive-field-display | apiKey, authtoken, password, secret, token, type="password", show-password, placeholder, 留空不修改 |
| scroll-container | overflow-y, overflow: auto, flex-direction, flex-shrink, glass-card, min-content, scroll-behavior |
| spa-navigation | CustomEvent, dispatchEvent, addEventListener, removeEventListener, currentView, karpathy:navigate, onMounted, onBeforeUnmount |
| update-check | checkUpdate, updateState, setInterval, clearInterval, has_update, cache_ttl, poll_interval, offline_mode, 检查更新 |
| icon-and-navigation | <svg, icon, nav, tooltip, Transition, menuItems, navCollapsed |
| async-reliability | fetch(, axios, EventSource, consumeSSEStream, AbortController, setInterval, setTimeout, .abort(), clearTimeout, clearInterval |
| typecheck-cache-frontend | vue-tsc, tsc, Object is possibly null, Object is possibly undefined, as any, as unknown as, @ts-ignore, @ts-expect-error, !., tsbuildinfo, noEmit |
| composable-api-frontend | useXxx, defineStore, pinia._s.delete, $dispose, $reset, useStore, useRoute, useRouter, useI18n, useHead, onScopeDispose, $subscribe |
| mixed-type-dispatch-frontend | as any, as unknown as, T \| U, typeof, in operator, isXxx, x is U, type guard, discriminated union, never, _exhaustive |
| sfc-script-block-frontend | `<script>`, `<script setup>`, `<script setup lang="ts">`, 双 script 块, defineProps, defineEmits, defineExpose, defineOptions, defineSlots, export default, name: |
| e2e-precheck-frontend | playwright, test_*.py, conftest.py, ERR_CONNECTION_REFUSED, ECONNREFUSED, webServer, port, /health, netstat, lsof, Get-NetTCPConnection, preflight, reuseExistingServer |
| test-case-sync-frontend | page.locator, query-head, selector, try/except, try/catch, except Exception, pass, data-testid, aria-label, toHaveText, expect, test.skip, pytest.fail |
| reading-viewport-frontend | Query.vue, Reader.vue, Help.vue, ChatView.vue, input-bar, sticky bottom, position: sticky, backdrop-filter, blur, 毛玻璃, z-index, header, content, flex: 1 |
| tauri-invoke-rule | invoke(, @tauri-apps/api, tauri.conf.json, src-tauri, build.rs, capabilities, default.json, lib.rs, generate_handler!, AppManifest, Plugin not found, not allowed, command not found |
| tauri-transparent-css-rule | transparent, floating-active, :global(html.floating-active *), backdrop-filter, glass-card, opacity: 0, visibility: hidden, background-color: transparent |
| tauri-drag-click-rule | data-tauri-drag-region, start_dragging, mousedown, mousemove, mouseup, dragStarted, isDragging, move_threshold |
| test-selector-priority-rule | placeholder=, :has-text(, has_text=, networkidle, wait_until, waitUntil, page.locator, cy.get, waitForSelector, domcontentloaded, background-image: url, EventSource, [data-testid, page.goto |
| control-layering-frontend-rule | button-bar, .folding-panel, .input-area, el-collapse, el-popover, Transition, panel-, aria-expanded, is-active, @mousedown.stop, v-if, v-show, el-button, el-dropdown, el-input, el-switch |
| third-party-error-guard-frontend-rule | mermaid, katex, Prism, mermaid.render, katex.render, Prism.highlight, mermaid.initialize, suppressErrorRendering, throwOnError, logErrors, innerHTML, replaceChildren, parseMermaid, parseKatex, parsePrism, .mermaid-error, .katex-error, .prism-error |
| folding-panel-event-frontend-rule | click outside, useClickOutside, v-click-outside, onClickOutside, el-dropdown, hide-on-click, el-dropdown-menu, el-dropdown-item, @click.stop, @mousedown.stop, Teleport, teleport-to-body, .el-dropdown-menu, .el-popover, .el-select-dropdown, .el-picker-panel |
| long-task-architecture-frontend-rule | EventSource, consumeSSEStream, fetch, /api/media/video, setInterval, poll, pollTimer, videoTaskId, 400, 429, 500, status_code, 后端服务未运行, config_redirect, external_retry, rate_limit, Retry-After, POST, GET |
| sse-event-dispatch-frontend-rule | consumeSSEStream, EventSource, onmessage, if (event.type, else if, switch (event.type, Record<string, Handler>, handlers, outputMode, outputModes, defaultHandler, 联合字面量, type OutputMode, S3776, 认知复杂度 |
| sse-stream-error-frontend-rule | consumeSSEStream, getReader, reader.read, reader.cancel, AbortError, err.name, AbortController, abort(), abortReason, signal?:, signal?., finally, isLoading, isStreaming, partial_data |
| long-task-polling-ui-frontend-rule | setInterval, poll, pollTimer, AbortSignal.timeout, setTimeout, abortReason, videoState, queued, processing, completed, failed, closeDialog, resetState, onBeforeUnmount, clearInterval, clearTimeout, handleKeydown |
| event-delegation-frontend-rule | v-html, addEventListener, removeEventListener, closest, target.tagName, event.target, globalThis, window, document, destroy, dispose, cleanup, mermaid.initialize, mermaidModule, onBeforeUnmount, handleKeydown |
| heavy-library-frontend-rule | import mermaid, import marpit, import monaco, dynamic import, mod.default, mod.mermaid, mod.Marp, xxxLoaded, mermaidModule, marpInstance, nextTick, await import, render, innerHTML, fallback, pre, 200KB, bundle |
| ts-js-shadowing-frontend-rule | src/**/*.js, *.js.map, resolve.extensions, vue-tsc, vite build, 编译产物, .ts 不生效, noEmit |
| type-sync-done-event-rule | done event, governor, threadId, export interface, types.ts, additive, optional, SSE 字段新增, 同 PR 同步 |
| runtime-data-privacy-frontend-rule | IndexedDB, localStorage, 新磁盘目录, gitignore, persistSessions, 服务端会话, 敏感字段明文, 运行期产物 |
| element-plus-radio-deprecation | el-radio, el-radio-button, label act as value, ElementPlusError, label=, value=, 3.0.0 deprecated |
| optional-contract-field-rule | CompileInput, QueryInput, originalName, 后端内部字段, 前端不消费, optional, ?? 兜底, 同 PR 同步, field!, as T, 分支依赖, 加法可选 |
| tts-neural-fallback-rule | speechSynthesis, SpeechSynthesisUtterance, /api/tts/synthesize, prosody, express-as, new Audio, zh-CN-XiaoxiaoNeural, volume, pitch, rate, 朗读, 语音合成 |
| spa-deploy-integrity-frontend-rule | vite.config.ts, outDir, emptyOutDir, public_live_, .deploy-complete, 时间戳目录, deploy, 部署完整性, 全新目录, 覆盖, safe-delete |
| session-isolation-frontend-rule | currentConversationId, scopedOwnerId, resetSession, loadConversations, persistConversation, dbGet, filterByOwner, migrateOwnerless, user?.id, 跨账户, 登出, ownerId, 会话隔离, 复用 id |
| byok-per-user-override-frontend-rule | usercfg::, loadAiUserConfig, saveAiUserConfig, llmConfig, searchConfig, toolsConfig, apiKey, BYOK, 配置菜单, isAdmin, v-if="isAdmin", 命名空间, 自带密钥 |
| streaming-resume-frontend-rule | streamingAnswer, persistConversation, schedulePersistInProgress, onBeforeUnmount, abortController, LAST_ACTIVE_CONVERSATION, status:'streaming', resumeLastAnswer, maybeResumeOnLoad, 断点续答, 增量持久化 |
| test-isolation-frontend-rule | indexedDB, localStorage, deleteDatabase, indexeddb.deleteDatabase, setTimeout(0), flush, vi.clearAllMocks, vi.resetModules, 命名空间, 唯一 userId, beforeEach, fake-indexeddb, onblocked, 异步落盘 |
| ssml-injection-frontend-rule | /api/tts/synthesize, EdgeTtsProvider, prosody, express-as, rate, volume, pitch, 朗读, 语音合成, 1007 |
| safe-dom-delete-rule | removeChild, classList.remove, 删除, remove, querySelector, getElementsByClass, 引用, 清零, .msg-actions, grep, stale |
| theme-aware-icon-frontend-rule | <svg, currentColor, fill=, stroke=, 24x24, viewBox, 线条, icon, rgba(255,255,255, stroke-width |
| capability-gating-sync-frontend-rule | !!sessionId, !!getSession, v-if, can-archive, 门控, 能力, 内容可得性, content availability, 放宽 |
| edit-resend-frontend-rule | removeMessagesFrom, submitQuestion, editingIdx, 编辑重发, 编辑并重新发送, 悬空答案, isLoading, 编辑态发送, 重新插入用户消息 |
| chat-autoscroll-frontend-rule | scrollToBottom, double rAF, requestAnimationFrame, stickToBottom, 贴底, 用户滚动, 监听解绑, img load, 补滚, onMounted, onUnmounted |
| button-style-frontend-rule | .edit-btn.confirm, .edit-btn.cancel, 确认, 取消, type="primary", 成对按钮, 主题变量, el-button |
| editbox-width-frontend-rule | .msg-content-wrapper.editing, .msg-edit, flex-end, align-items:stretch, width:100%, 编辑态撑满, 输入框宽度, 编辑框 |
| idb-reactive-clone-frontend-rule | dbPut, saveUserConfig, idbPut, store.put, reactive(, toRaw(, structuredClone(, [object Array] could not be cloned, JSON.parse(JSON.stringify, 深拷贝, clone(, 静默丢配置 |
| auth-request-timeout-frontend-rule | login, fetch, AbortController, AbortSignal.timeout, 登录中, 登录超时, 超时, 重试, await fetch |
| auth-loading-reset-frontend-rule | loading, submitting, try, finally, 登录中, 灰显, 复位, resetLoading |
| auth-request-fetch-frontend-rule | fetch, /api/config, /api/ai/config, apiFetch, Authorization, Bearer, 受保护端点, requireAuth, bootstrap, 401 |
| backdrop-filter-containing-block-frontend-rule | backdrop-filter, -webkit-backdrop-filter, --m-blur, position: fixed, Teleport, .mobile-content, scroll-fab, sheet-mask, containing block, 毛玻璃滚动容器 |
| dual-theme-variable-frontend-rule | --m-, theme-light, .mobile-root, useMobileTheme, 主题变量, 切换主题, karpathy-mobile-theme, data-theme, 双主题 |
| pnpm-store-hygiene-frontend-rule | store-dir, .npmrc, pnpm store path, .pnpm-store, 孤儿 store, 收敛, content-addressable |
| persistent-component-lifecycle-frontend-rule | v-show, props.visible, watch(, onMounted, onBeforeUnmount, 重型 DOM, v-if="visible", vue-tsc, activeTab, 切回, 账户切换, 常驻, 后台播放 |
| media-object-url-frontend-rule | URL.createObjectURL, revokeObjectURL, blob, objectUrl, new Audio, 图片预览, 文件下载, 常驻组件, 切换曲目 |
| audio-playback-reliability-frontend-rule | <audio, a.play(), .play(), 语音合成失败, 播放被浏览器拦截, position, duration, 朗读队列, res.ok, NotAllowedError, 进度重置 |
| download-timeout-abort-frontend-rule | fetch, downloadVaultFile, AbortSignal.timeout, blob, 下载, 超时, 大文件, 挂起, signal |
| download-mobile-silent-guard-frontend-rule | downloadVaultFile, MobileBrowse, 下载, 错误提示, Toast, 静默, 失败兜底, 点了没反应, showError |
| download-reentry-guard-frontend-rule | downloadVaultFile, downloading, in-flight, 防重复点击, 重入, 并发下载, finally |
| content-disposition-filename-frontend-rule | Content-Disposition, filename*, RFC 5987, 扩展名, 文件名解析, blob, 中文文件名, decodeURIComponent |
