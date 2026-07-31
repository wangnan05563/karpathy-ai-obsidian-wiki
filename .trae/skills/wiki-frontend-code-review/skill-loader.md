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
