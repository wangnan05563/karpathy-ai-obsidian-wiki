# 测试用例与代码结构同步（FR-031）

> 复盘来源：v2 改造中 Query.vue / Reader.vue 等组件 DOM 结构变更（class 重命名、`data-testid` 删除、`query-head` 容器替换）后未同步更新 E2E 与组件测试中的 `page.locator('.query-head')` 选择器，CI 报"selector timeout"误判为业务 bug；同时 Python E2E 测试用 `try/except Exception: pass` 静默吞掉选择器失效异常，掩盖真实回归。
> 所有可变参数从 config/review-config.md 的 `test_case_sync_frontend` 字段读取。

## 规则

### FR-031-1：代码变更影响 DOM 时必须同步更新测试选择器

当 PR 修改了 `.vue` / `.tsx` 文件中影响 DOM 的下列任一要素时，**同一 commit / PR** 必须同步更新引用该 DOM 的测试文件（Playwright / Cypress / Vitest UI 测试 / Python E2E）：

1. 元素 `class` / `id` 的重命名或删除。
2. `data-testid` / `data-test` / `aria-label` 属性的增删或重命名。
3. 元素层级结构变化（如把 `<button>` 包进 `<div>`、删除包裹层）。
4. 文本内容变化（按钮文案、标题、错误提示）—— 若测试用 `toHaveText` 断言文案。
5. 元素渲染条件变化（`v-if` / `v-show` 改动），导致原选择器在某些状态下不再存在。

**禁止**：把"DOM 已变但测试未更新"推迟到下一个 PR 处理，否则当前 PR 在 CI 上即出现测试失败，阻塞合并。

### FR-031-2：测试禁止 `try/except` / `try/catch` 静默吞错

E2E 与组件测试代码中，禁止以下静默吞错模式：

- Python：`try: locator.click() except Exception: pass`（无 `raise` / `logger.error`）。
- TypeScript：`try { await page.locator(x).click() } catch (e) {}`（空 catch 体）。
- 仅 `console.log` 但不抛错也不标记用例失败。

允许的 `try/catch` 场景：

- **断言前置等待**：`try { await expect(locator).toBeVisible({ timeout: 1000 }) } catch { /* skip */ }` —— 但必须显式 `test.skip()` 标注，禁止静默跳过。
- **降级重试**：`try { ... } catch (e) { await retry() }` —— 重试失败后必须 `throw`。
- **诊断信息收集**：`try { ... } catch (e) { attachScreenshot(e); throw e }` —— 必须 `throw`。

判定标准：catch 块结束前是否有 `throw` / `test.fail()` / `test.skip()` / `pytest.fail()` 之一，否则即违规。

### FR-031-3：选择器优先级

测试用例中的 DOM 选择器必须按以下优先级使用，以降低 DOM 重构对测试的冲击：

1. `data-testid`（首选，与视觉重构解耦）。
2. `aria-label`（语义化）。
3. `role` + 可访问名称。
4. 元素文本（最后选择，文案改写时即失效）。
5. `class` 选择器（不推荐，重构易碎）—— 仅用于纯样式断言。

### FR-031-4：选择器清单集中化

测试用例共享的选择器应集中到 `test_case_sync_frontend.selector_module` 指定的模块（如 `e2e/selectors.ts`），禁止在每个测试文件硬编码字符串字面量。这样 DOM 变更时只需更新一处。

## 适用场景

- Vue 3 / React 项目修改了 `.vue` / `.tsx` 文件中影响 DOM 的代码。
- PR 同时涉及前端组件与对应测试用例。
- Python / TypeScript E2E 测试套件。
- CI 流水线中的测试用例维护。

## 不适用场景

- 仅修改 `<script setup>` 内部纯逻辑（如改 store action 实现、改计算属性内部计算），DOM 结构与文案未变 —— 测试用例无需更新。
- 单元测试中针对纯函数的测试（不依赖 DOM 选择器）。
- 测试基础设施重构（如更换测试运行器）—— 由专门任务处理。

## 检查流程

```
[开始] PR 修改了 .vue / .tsx 文件
  │
  ▼
[1] 提取 diff 中 DOM 影响变更：class/id/testid/层级/文案/渲染条件
  │  └─ 无 DOM 影响 → [通过]
  │
  ▼ 有 DOM 影响
[2] 在同一 PR 中查找引用了变更选择器的测试文件
  │  └─ 测试未更新 → 标记 Urgent（FR-031-1）
  │
  ▼ 测试已更新
[3] 扫描测试文件中的 try/catch / try/except
  │  └─ catch 块无 throw/fail/skip → 标记 Urgent（FR-031-2）
  │
  ▼
[4] 检查选择器优先级：是否使用 data-testid / aria-label 而非 class
  │  └─ 全用 class → 标记建议（FR-031-3）
  │
  ▼
[5] 检查选择器是否集中到 selector_module
  │  └─ 否（散落在各测试文件） → 标记建议（FR-031-4）
  │
  ▼
[结束]
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `test_case_sync_frontend.dom_impact_triggers` | `class rename, id rename, data-testid change, structural change, text change, v-if/v-show change` | 触发测试同步的 DOM 变更类型（逗号分隔） |
| `test_case_sync_frontend.same_commit_required` | `true` | DOM 变更与测试更新必须在同一 commit/PR |
| `test_case_sync_frontend.silence_patterns` | `try/catch with empty body, try/except pass, catch with only console.log` | 禁止的静默吞错模式 |
| `test_case_sync_frontend.allowed_catch_terminators` | `throw, test.fail, test.skip, pytest.fail, expect.assertions` | catch 块必须包含的至少一种终止符 |
| `test_case_sync_frontend.selector_priority` | `data-testid, aria-label, role, text, class` | 选择器优先级（从高到低） |
| `test_case_sync_frontend.class_selector_discouraged` | `true` | 是否禁止 class 选择器（仅用于样式断言时允许） |
| `test_case_sync_frontend.selector_module` | `e2e/selectors.ts` | 集中导出选择器常量的模块路径 |
| `test_case_sync_frontend.selector_lint_files` | `e2e/**/*.spec.ts, e2e/**/*.test.ts, e2e/test_*.py, tests/**/*.spec.ts` | 需扫描选择器同步情况的测试文件 glob |

## 检查方式

1. 从 PR diff 中提取 `.vue` / `.tsx` 文件 DOM 影响变更（class / id / data-testid / 结构 / 文案 / 渲染条件）。
2. 用变更前的选择器字符串在 `selector_lint_files` 范围内 grep，找到引用该选择器的测试文件。
3. 在同一 PR diff 中检查这些测试文件是否有对应更新（选择器替换、断言文案同步等），未更新即 Urgent。
4. 用 `silence_patterns` 正则扫描测试代码，命中且 catch 块不包含 `allowed_catch_terminators` 任一关键字即 Urgent。
5. 用 `selector_priority` 检查测试选择器优先级，统计 class 选择器占比，全部为 class 即标记建议。
6. 检查 `selector_module` 是否存在并被测试文件引用，未集中化即标记建议。

## 正确示例

```ts
// ✅ e2e/selectors.ts — 选择器集中化
export const Selectors = {
  queryHead: '[data-testid="query-head"]',
  submitButton: '[data-testid="submit"]',
  resultCard: '[data-testid="result-card"]',
  errorBanner: '[role="alert"]',
} as const
```

```ts
// ✅ e2e/query.spec.ts — 同步更新测试 + 合法 try/catch
import { test, expect } from '@playwright/test'
import { Selectors } from './selectors'

test('query shows result card', async ({ page }) => {
  await page.goto('/')
  await page.locator(Selectors.queryHead).fill('keyword')
  await page.locator(Selectors.submitButton).click()

  // ✅ 合法 try/catch：降级重试 + 显式 throw
  try {
    await expect(page.locator(Selectors.resultCard)).toBeVisible({ timeout: 5000 })
  } catch (e) {
    await page.screenshot({ path: 'fail-result.png' })
    throw e  // ✅ 必须重新抛出
  }
})

// ✅ 合法 try/catch：显式 test.skip
test('optional feature', async ({ page }) => {
  try {
    await expect(page.locator(Selectors.resultCard)).toBeVisible({ timeout: 1000 })
  } catch {
    test.skip(true, 'optional feature not available in this env')
  }
})
```

```vue
<!-- ✅ .vue 修改 DOM 时同步改 data-testid -->
<!-- 旧版本： -->
<!-- <div class="query-head">...</div> -->
<!-- 新版本： -->
<template>
  <div data-testid="query-head">  <!-- ✅ 用 data-testid 替换 class 选择器 -->
    <!-- ... -->
  </div>
</template>
```

## 错误示例

```ts
// ❌ DOM 已变但测试未同步（PR 拆成两个 commit）
// commit 1: Query.vue 中 .query-head 重命名为 .query-bar
// commit 2: e2e/query.spec.ts 仍引用 .query-head
test('query shows result', async ({ page }) => {
  // ❌ selector timeout，但开发者误以为是业务 bug
  await page.locator('.query-head').fill('keyword')
})
```

```python
# ❌ try/except 静默吞错
def test_query_flow(page):
    try:
        page.locator(".query-head").click()
    except Exception:
        pass  # ❌ 选择器失效被吞，测试假绿
```

```ts
// ❌ catch 块仅 console.log 不抛错
test('result card visible', async ({ page }) => {
  try {
    await expect(page.locator(Selectors.resultCard)).toBeVisible()
  } catch (e) {
    console.log('result not visible', e)  // ❌ 仅日志，未 throw / fail
  }
})
```

```ts
// ❌ 选择器全用 class，未集中到 selector_module
test('submit', async ({ page }) => {
  await page.locator('.query-bar .btn-primary.active').click()  // ❌ class 链易碎
  await page.locator('.result-card-title').waitFor()
})
```

## 适配新项目

- **React / Next.js**：本规则完全适用；选择器模块路径可改为 `__tests__/selectors.ts`。
- **Vue 2**：DOM 影响触发条件相同；测试文件若是 vue-test-utils 写法，选择器优先级与同步要求不变。
- **纯 JavaScript（无框架）**：DOM 影响触发条件相同；`try/catch` 静默吞错检查通过 ESLint 规则 `no-empty-catch` 自动化。
- **Python E2E**：`try/except` 静默吞错检查通过 `flake8-bugbear` 的 `B902` / 自定义 ast 检查实现；`pytest.fail()` / `pytest.skip()` 作为合法终止符。
- **Monorepo**：选择器模块路径可改为 `packages/shared-e2e/selectors.ts`，所有测试套件从同一处导入；DOM 变更触发的测试同步检查需跨 package 引用关系分析。
