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
| T1-T6 | Type Safety | [references/type-safety-rule.md](references/type-safety-rule.md) | [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md) | *.ts, *.vue | 4 | 6 |
| TH1-TH6 | Theming | [references/theming-rule.md](references/theming-rule.md) | [examples/theming-rule-examples.md](examples/theming-rule-examples.md) | *.vue, *.css | 3 | 6 |
| CI1-CI3 | Config Isolation | [references/config-isolation-rule.md](references/config-isolation-rule.md) | [examples/config-isolation-rule-examples.md](examples/config-isolation-rule-examples.md) | *config*.vue | 3 | 3 |
| CS1-CS4 | Config State | [references/config-state-rule.md](references/config-state-rule.md) | — | *config*.vue, *form*.vue | 2 | 4 |
| DF1-DF7 | Display Field | [references/display-field-rule.md](references/display-field-rule.md) | — | *task*.vue, *display*.vue | 5 | 7 |
| PB1-PB6 | Persistence Boundary | [references/persistence-boundary-rule.md](references/persistence-boundary-rule.md) | — | *store*.ts, *.vue (含 fetch/dbPut/localStorage) | 5 | 6 |

## 3. Quick Routing Table

| 文件特征 | 必加载规则 | 条件加载规则 |
|---------|-----------|------------|
| *.vue + <script setup> | vue-composition | element-plus (if el-*), performance (if is-network), theming (if data-theme), pinia-store (if defineStore) |
| *store*.ts | pinia-store, type-safety, persistence-boundary | — |
| *.vue + 表单 | element-plus, config-state | — |
| *.ts + etch/JSON.parse | type-safety | performance (if SSE) |
| *.vue + 主题切换 | theming | vue-composition |
| *config*form*.vue | config-isolation, config-state, element-plus, persistence-boundary | — |
| *display* / *task* | display-field | type-safety |

## 4. Keyword Scanning Guide

Scan the first 50 lines of a target file for these keywords to determine rule categories:

| Category | Keywords to Search |
|----------|-------------------|
| vue-composition | <script setup, ef(, eactive(, computed(, watch(, onMounted, onBeforeUnmount |
| element-plus | el-, ElMessage, ElDialog, ElForm, ElButton, ElIcon, -loading |
| pinia-store | defineStore, pinia, useXxxStore, state:, ctions: |
| performance | is-network, Network, esize, -for, onMessage, ReadableStream |
| type-safety | interface , 	ype , Promise<, etch(, JSON.parse, s const |
| theming | data-theme, getComputedStyle, gba(, ar(--, ill=, stroke= |
| config-isolation | localStorage, piKey, ****, preset, ccountConfig |
| config-state | config, orm, save, 	oggle, eature |
| display-field | display, rand, egion, seller, ield_map, 
ormalize |

## 5. Token Budget

| Phase | Files | Est. Tokens |
|-------|-------|-------------|
| Baseline | SKILL.md + review-config.md | ~3,500 |
| Single rule | 1 rule file | ~1,000 |
| Typical review | 2-3 rules | ~3,000 |
| Complex review | 5-7 rules | ~6,000 |
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

### Directory Mapping
views → src/views/, stores → src/stores/, components → src/components/
types → src/types/, utils → src/utils/, api → src/api/

---

*End of skill loader & checklist index. This file replaces separate .rule-index.json, skill-loader.md, and checklist-index.md.*
