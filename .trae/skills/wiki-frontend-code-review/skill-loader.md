# Wiki Frontend Code Review - Skill Loader & Checklist Index

> Combined reference for efficient rule loading during code review.
> Read this file once at the start of each review session.

---

## 1. Loading Sequence

### Always Load (Baseline)
1. [SKILL.md](SKILL.md) — skill intent, output templates
2. [config/review-config.md](config/review-config.md) — thresholds, tech stack, conventions

### Smart Rule Routing
Use the routing table below to select only applicable rule files.

### On-Demand Examples
Only load eferences/examples/{category}-examples.md when:
- Generating specific fix code
- Rule description needs Wrong/Right comparison

## 2. Rule Overview

| # | 类别 | 规则文件 | 示例文件 | 适用文件模式 | Urgent | Total |
|---|------|---------|---------|------------|--------|-------|
| V1-V6 | Vue Composition | [references/vue-composition-rule.md](references/vue-composition-rule.md) | [examples/vue-composition-rule-examples.md](examples/vue-composition-rule-examples.md) | *.vue, *.tsx | 3 | 6 |
| E1-E6 | Element Plus | [references/element-plus-rule.md](references/element-plus-rule.md) | [examples/element-plus-rule-examples.md](examples/element-plus-rule-examples.md) | *.vue | 3 | 6 |
| P1-P7 | Pinia Store | [references/pinia-store-rule.md](references/pinia-store-rule.md) | [examples/pinia-store-rule-examples.md](examples/pinia-store-rule-examples.md) | *store*.ts, *.vue | 5 | 7 |
| PR1-PR7 | Performance | [references/performance-rule.md](references/performance-rule.md) | [examples/performance-rule-examples.md](examples/performance-rule-examples.md) | *.vue, *.ts | 5 | 7 |
| T1-T9 | Type Safety | [references/type-safety-rule.md](references/type-safety-rule.md) | [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md) | *.ts, *.vue | 6 | 9 |
| TH1-TH6 | Theming | [references/theming-rule.md](references/theming-rule.md) | [examples/theming-rule-examples.md](examples/theming-rule-examples.md) | *.vue, *.css | 3 | 6 |
| CI1-CI3 | Config Isolation | [references/config-isolation-rule.md](references/config-isolation-rule.md) | [examples/config-isolation-rule-examples.md](examples/config-isolation-rule-examples.md) | *config*.vue | 3 | 3 |
| CS1-CS4 | Config State | [references/config-state-rule.md](references/config-state-rule.md) | — | *config*.vue, *form*.vue | 2 | 4 |
| DF1-DF7 | Display Field | [references/display-field-rule.md](references/display-field-rule.md) | — | *task*.vue, *display*.vue | 5 | 7 |
| PB1-PB6 | Persistence Boundary | [references/persistence-boundary-rule.md](references/persistence-boundary-rule.md) | — | *store*.ts, *.vue (含 fetch/dbPut/localStorage) | 5 | 6 |
| ES1-ES6 | Encoding Safety | [references/encoding-safety-rule.md](references/encoding-safety-rule.md) | [examples/encoding-safety-rule-examples.md](examples/encoding-safety-rule-examples.md) | *.vue, *.ts, *.tsx, *.json, *.md, .editorconfig, .vscode/*.json | 5 | 6 |
| DA1-DA8 | Dangerous Action | [references/dangerous-action-rule.md](references/dangerous-action-rule.md) | [examples/dangerous-action-rule-examples.md](examples/dangerous-action-rule-examples.md) | *.vue, *.ts (含 dry_run/danger/ElMessageBox.confirm/cleanup/delete/启动/停止/保存) | 7 | 8 |
| RR1 | Route Registration | [references/route-registration-frontend-rule.md](references/route-registration-frontend-rule.md) | — | views/*.vue, App.vue (SPA 手动路由) | 1 | 1 |
| TS1 | Type Sync | [references/type-sync-frontend-rule.md](references/type-sync-frontend-rule.md) | — | types.ts (前后端) | 1 | 1 |
| SF1 | Sensitive Field Display | [references/sensitive-field-display-rule.md](references/sensitive-field-display-rule.md) | — | *.vue (含 el-input/input + key/token/secret/password/authtoken) | 1 | 1 |
| SC1 | Scroll Container | [references/scroll-container-rule.md](references/scroll-container-rule.md) | — | *.vue, *.css (含 overflow-y: auto / flex-direction: column / glass-card) | 1 | 1 |
| SN1 | SPA Navigation | [references/spa-navigation-rule.md](references/spa-navigation-rule.md) | — | *.vue (含 CustomEvent / dispatchEvent / currentView / 跨视图跳转) | 1 | 1 |
| UC1-UC4 | Update Check | [references/update-check-rule.md](references/update-check-rule.md) | — | *.vue (含 checkUpdate / setInterval / updateState / 检查更新) | 3 | 4 |

## 3. Quick Routing Table

| 文件特征 | 必加载规则 | 条件加载规则 |
|---------|-----------|------------|
| *.vue + <script setup> | vue-composition, encoding-safety | element-plus (if el-*), performance (if is-network), theming (if data-theme), pinia-store (if defineStore), dangerous-action (if dry_run/danger/ElMessageBox.confirm/启动/停止/保存), route-registration (if 文件在 views/ 下或为 App.vue), sensitive-field-display (if el-input 含 key/token/password) |
| *store*.ts | pinia-store, type-safety, persistence-boundary, encoding-safety | — |
| *.vue + 表单 | element-plus, config-state, encoding-safety | dangerous-action (if dry_run/cleanup/delete/启动/停止/保存), sensitive-field-display (if 含 key/token/secret/password/authtoken 字段) |
| *.ts + etch/JSON.parse | type-safety, encoding-safety | performance (if SSE), type-sync (if 文件为 types.ts 或含 export interface) |
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

## 4. Keyword Scanning Guide

Scan the first 50 lines of a target file for these keywords to determine rule categories:

| Category | Keywords to Search |
|----------|-------------------|
| vue-composition | <script setup, ef(, eactive(, computed(, watch(, onMounted, onBeforeUnmount |
| element-plus | el-, ElMessage, ElDialog, ElForm, ElButton, ElIcon, -loading |
| pinia-store | defineStore, pinia, useXxxStore, state:, ctions: |
| performance | is-network, Network, esize, -for, onMessage, ReadableStream |
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

## 5. Token Budget

| Phase | Files | Est. Tokens |
|-------|-------|-------------|
| Baseline | SKILL.md + review-config.md | ~3,500 |
| Single rule | 1 rule file | ~1,000 |
| Typical review | 2-3 rules | ~3,000 |
| Complex review | 5-9 rules | ~7,500 |
| With examples | +1 example file | ~750 |
| **Total typical** | | **~6,500** (vs old ~13,300) |

## 6. Config Parameters Quick Reference

See [config/review-config.md](config/review-config.md) for full details.

### Tech Stack
Vue 3.4+, Element Plus, Pinia (setup), TypeScript strict, Vite, pnpm

### Performance Thresholds
- vis-network: 3-level degradation (L1/L2/L3 thresholds in config)
- Mobile breakpoint: 768px
- SSE events: answer, refs, done, error, progress, page, fixing, fixed

### Theme System
- 6 themes: macaron, enterprise, creative, product, ecommerce, portfolio
- CSS variables: 3-layer architecture (L1 base, L2 subsystem, L3 scene)
- Alpha naming:  + 2 digits (a03..a70)
- Hardcoded whitelist: gba(255,255,255,X), 	ransparent, inherit, currentColor

### Encoding Safety
- Source files (.vue/.ts/.tsx): UTF-8 no BOM
- Meta files (.editorconfig/.vscode/settings.json): UTF-8 no BOM
- Detection: strict UTF-8 decode (fatal=true), FFFD = non-UTF-8
- Scan scope: .vue, .ts, .tsx, .json, .md
- ASCII whitelist: pure ASCII files skip detection
- Replacement char scan: U+FFFD count > 0 → encoding corrupted (block submit)

### Dangerous Action
- dry_run default: true (preview mode safe-first)
- Danger style: type="danger" or .danger class when dry_run=false
- Confirm: ElMessageBox.confirm with type=warning
- Cancel: no request sent
- Irreversible hint required in confirm message
- Audit log: required after actual execution
- Destructive buttons (启动/停止/保存/删除/清除/重置): require at least one of loading / disabled / confirm guard

### Multi-Form State
- Pattern: Record<key, FormState>
- Independent loading + result per key
- Reset result on submit

### Route Registration
- Applicable: SPA manual routing (v-if / v-else-if chain in App.vue)
- Non-applicable: vue-router / react-router / Next.js / Nuxt.js
- Required hooks: import, type (ViewName), v-for (tabs), v-else-if (branch)

### Type Sync
- Applicable: full-stack TypeScript projects with manual types.ts
- Non-applicable: GraphQL / tRPC / OpenAPI auto-generated types
- Sync rule: backend export interface must have matching frontend interface (field name + type)

### Sensitive Field Display
- Applicable: credential fields fetched from backend and rendered to forms
- Non-applicable: login/register password input (user-entered, not echoed)
- Strategies: masked (display ****xxxx) / masked_placeholder (empty input + "留空不修改" hint)
- Field patterns: key, token, secret, password, authtoken

### Scroll Container
- Applicable: Vue 3 + flex 布局的多卡片长内容页面，外层已设 `overflow-y: auto`
- Non-applicable: CSS Grid 布局、原生块级元素堆叠、桌面端固定高度窗口
- Max overflow layers: 1 (default)
- flex-shrink required in flex column: true
- Glass-card selectors: `.glass-card`
- Outer scroll selectors: `.content, .app-shell`

### SPA Navigation
- Applicable: Vue 3 + `<script setup>` SPA 手动路由项目
- Non-applicable: vue-router / react-router / Next.js / Nuxt.js 自动路由项目
- Event name pattern: `{project}:navigate` (default `karpathy:navigate`)
- Lifecycle pair required: onMounted (addEventListener) + onBeforeUnmount (removeEventListener)
- Allowed views whitelist: [] (empty = no validation)

### Update Check
- Applicable: Vue 3 + `<script setup>` 的检查更新功能（含轮询定时器）
- Non-applicable: PWA Service Worker 更新、Electron autoUpdater、一次性检查
- Required states: idle, loading, latest, newer, error
- Cache TTL: 300000ms (5 min)
- Poll interval: 300000ms (≥ cache_ttl_ms)
- First check delay: 5000ms (avoid competing with first render)
- Latest to idle delay: 3000ms
- Offline mode: true (固定返回 has_update: false)
- Cleanup hook: onBeforeUnmount

### Directory Mapping
views → src/views/, stores → src/stores/, components → src/components/
types → src/types/, utils → src/utils/, api → src/api/

---

*End of skill loader & checklist index. This file replaces separate .rule-index.json, skill-loader.md, and checklist-index.md.*
