# 测试选择器优先级与等待策略（FR-044）

> 复盘来源：Skill 导入模块 E2E 测试中，`input[placeholder*='用户']` 因国际化/文案调整导致匹配失败或误匹配多个元素；`button:has-text('登录')` 在含多个登录入口的页面误命中次要按钮。同时 `page.goto(wait_until="networkidle")` 因登录页背景图 `url(${bgImage})` 持续加载永远不触发 networkidle 而超时。修复方式：测试改用 `#login-username` / `#login-password` / `.login-btn` 稳定 ID 选择器，等待策略改用 `domcontentloaded` + 显式 `wait_for_selector("#element-id", state="visible")`。
> 所有可变参数从 config/review-config.md 的 `test_selector_priority` 字段读取，禁止在规则文件中硬编码选择器优先级顺序、等待策略或资源模式。

## 规则

### FR-044-1：测试选择器必须按优先级顺序使用

测试代码（Playwright / Cypress / Vitest / Selenium / Puppeteer 等）中定位 DOM 元素的选择器必须按 `test_selector_priority.selector_priority_order`（从高到低）顺序优先选用：

1. **`#id`**（最高优先级）—— 全文档唯一，文案变更不影响定位
2. **`[data-testid]`** —— 显式测试钩子，与视觉/语义解耦
3. **`[aria-label]`** —— 语义属性，国际化时通常一并更新
4. **`.class`** —— 样式类，重构时易变但比文本稳定
5. **`[placeholder]` / `:has-text()`**（最低优先级）—— 文本可变，禁止在可避免场景下使用

**判定标准**：若测试文件中存在 `[placeholder]` / `:has-text()` 选择器，且对应 DOM 元素可添加 `id` / `data-testid`（即被测组件源码可控），即视为违规。仅当元素为第三方组件库内部 DOM（无法添加属性）且无更高优先级选择器可用时，方可降级使用文本匹配。

### FR-044-2：被测 Vue 组件必须为关键交互元素提供稳定属性

被测的 `.vue` / `.tsx` 组件中以下"关键交互元素"必须提供 `test_selector_priority.required_stable_attributes` 列出的稳定属性（默认 `id` 或 `data-testid`）：

- 表单输入项（`<input>` / `<textarea>` / `<el-input>` / `<select>`）
- 触发业务逻辑的按钮（提交 / 登录 / 保存 / 删除 / 启动 / 停止等，对应 `destructive_button_patterns` 的范围）
- 异步加载区域容器（用于 `wait_for_selector` 的等待目标）
- 断言目标元素（被 `expect(locator).toHaveText(...)` 引用的元素）

**判定标准**：若组件仅以 `placeholder` / `class` 作为可识别属性，且同 PR 中存在引用该元素的测试代码，即视为违规——文案调整会直接导致测试失效。修复方式：在组件 `<template>` 中补充 `id="login-username"` 或 `data-testid="login-submit"`。

### FR-044-3：持续加载资源页面禁用 networkidle 等待策略

测试代码中 `page.goto(wait_until=...)` / `cy.visit(...)` / `page.waitForLoadState(...)` 的等待策略不得使用 `test_selector_priority.forbidden_wait_strategy`（默认 `networkidle`），当目标页面包含 `test_selector_priority.persistent_resource_patterns` 列出的持续加载资源模式时：

- `background-image`（CSS 背景图，长连接或懒加载）
- `event-stream`（SSE 流式接口，持续保持连接）
- `video` / `audio`（媒体流持续加载）
- `polling`（前端轮询定时器，永久触发网络活动）

**必须改用**：`test_selector_priority.recommended_wait_strategy`（默认 `domcontentloaded`）+ 显式 `wait_for_selector("#element-id", state="visible")` 等待关键交互元素就绪。该组合既能避免 networkidle 永不触发的超时，又能保证业务断言的元素已渲染。

### FR-044-4：DOM 结构变更必须同步测试选择器（与 FR-031 联动）

测试代码变更影响 DOM 结构（`class` / `id` / `data-testid` / 层级 / `v-if` / `v-show`）时，必须同步更新引用旧选择器的测试用例，且在同一 commit/PR 内完成（参见 `test_case_sync_frontend.same_commit_required`）。本条与 [FR-031](test-case-sync-frontend-rule.md) 形成"双向联动"：

- **FR-031** 关注 DOM 变更触发测试同步的"流程合规"（同 commit、try/catch 非静默、选择器集中化模块）
- **FR-044** 关注测试选择器的"质量合规"（优先级、稳定属性、等待策略）

两者命中其一即标记违规；同时命中触发 Urgent 级别。

## 适用场景

- 项目使用 Playwright / Cypress / Selenium / Puppeteer 运行 E2E 测试。
- 被测前端为 Vue 3 / React 项目，组件源码可控（可添加 `id` / `data-testid`）。
- 测试目标页面含持续加载资源（背景图 / SSE / 视频 / 轮询）。
- 单元测试 / 组件测试（Vitest / Jest）中通过 jsdom 查询 DOM 的场景同样适用选择器优先级规则（FR-044-1 / FR-044-2）。

## 不适用场景

- 纯第三方组件库内部 DOM 测试（无法添加 `id` / `data-testid`，只能用 placeholder/class 降级）。
- 视觉回归测试（Visual Regression Testing，仅截图比对，不涉及选择器）。
- 静态 HTML 文档测试（无持续加载资源，networkidle 可正常触发，FR-044-3 不适用）。
- 仅依赖 Playwright `role` / `label` 等"语义优先"定位策略的项目（已在 `selector_priority_order` 中通过 `[aria-label]` 覆盖）。

## 检查流程

```
[开始] 扫描测试代码与被测组件
  │
  ▼
[1] 选择器优先级扫描（FR-044-1）
  │  └─ 测试文件中存在 [placeholder] / :has-text() → 检查对应 DOM 是否可加 id/data-testid
  │       └─ 可加而未加 → 标记违规（建议改用 #id 或 [data-testid]）
  │       └─ 第三方组件内部 DOM 不可改 → 跳过（例外）
  │
  ▼
[2] 关键交互元素稳定属性检查（FR-044-2）
  │  └─ 扫描 .vue / .tsx 中 input/button/异步容器/断言目标
  │       └─ 仅含 placeholder/class → 同 PR 中存在引用该元素的测试 → 标记违规
  │
  ▼
[3] 等待策略扫描（FR-044-3）
  │  └─ 检索 page.goto(wait_until=...) / cy.visit() / waitForLoadState
  │       └─ 等待策略 == forbidden_wait_strategy（networkidle）
  │            └─ 目标页面含 persistent_resource_patterns → 标记违规
  │            └─ 改用 recommended_wait_strategy + wait_for_selector
  │
  ▼
[4] DOM 变更与测试同步（FR-044-4，与 FR-031 联动）
  │  └─ git diff 中 .vue/.tsx 变更含 class/id/data-testid/层级
  │       └─ 同 PR 测试文件未同步更新 → 标记违规（与 FR-031 双重命中 → Urgent）
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `test_selector_priority.enabled` | `true` | 是否启用测试选择器优先级审查 |
| `test_selector_priority.severity` | `suggestion` | 违规严重级别（suggestion = 非阻断性建议） |
| `test_selector_priority.selector_priority_order` | `#id,[data-testid],[aria-label],.class,[placeholder],:has-text()` | 选择器优先级顺序（从高到低，逗号分隔） |
| `test_selector_priority.forbidden_wait_strategy` | `networkidle` | 禁用的等待策略（有持续加载资源时） |
| `test_selector_priority.recommended_wait_strategy` | `domcontentloaded` | 推荐的等待策略 |
| `test_selector_priority.persistent_resource_patterns` | `background-image,event-stream,video,polling` | 持续加载资源模式（触发禁用 networkidle） |
| `test_selector_priority.required_stable_attributes` | `id,data-testid` | 关键交互元素必须提供的稳定属性 |

## 检查方式

1. **Grep 扫描测试文件**：在 `e2e/**/*.spec.ts` / `e2e/**/*.test.ts` / `tests/**/*.spec.ts` / `playwright.config.ts` 中检索 `[placeholder` / `:has-text(` / `has_text=` 关键字，命中即提取对应选择器。
2. **核对被测组件**：对每个低优先级选择器命中，定位被测 `.vue` / `.tsx` 文件中对应元素，检查是否已提供 `required_stable_attributes` 中的属性。
3. **等待策略扫描**：检索 `wait_until=` / `waitForLoadState` / `cy.visit(` 调用，对照 `forbidden_wait_strategy` 判定。
4. **持续资源识别**：对等待策略命中的页面，扫描其 `.vue` / `.css` 文件中是否含 `persistent_resource_patterns` 中的资源模式（`background-image: url(...)` / `EventSource` / `<video` / `setInterval`）。
5. **DOM 变更同步检查**：对 git diff 中 `.vue` / `.tsx` 变更行，识别 `class=` / `id=` / `data-testid` 改动，对照同 PR 测试文件是否同步更新引用。
6. **跨规则联动**：FR-044-4 命中时同步触发 FR-031 检查，双重命中升为 Urgent。

## 正确示例

```ts
// ✅ playwright.config.ts — 等待策略与选择器均合规
import { defineConfig } from '@playwright/test'

export default defineConfig({
  use: {
    // ✅ 等待策略从 config 读取（recommended_wait_strategy，禁止 networkidle）
    // 原因：登录页含 background-image 持续加载，networkidle 永不触发
    waitUntilState: 'domcontentloaded',  // 实际取自 config.test_selector_priority.recommended_wait_strategy
  },
})
```

```ts
// ✅ 登录测试 — 使用 ID 选择器 + 显式 wait_for_selector
import { test, expect } from '@playwright/test'

test('user can login', async ({ page }) => {
  // ✅ 等待策略：domcontentloaded（避免 networkidle 因背景图超时）
  await page.goto('/login', { waitUntil: 'domcontentloaded' })

  // ✅ 显式等待关键交互元素 visible，替代隐式 networkidle
  await page.waitForSelector('#login-username', { state: 'visible' })

  // ✅ 选择器优先级：#id（最高优先级，文案变更不影响）
  await page.fill('#login-username', 'testuser')
  await page.fill('#login-password', 'pass1234')

  // ✅ .login-btn 为 class 选择器（次优，但比 :has-text('登录') 稳定）
  await page.click('.login-btn')

  await expect(page).toHaveURL('/dashboard')
})
```

```vue
<!-- ✅ Login.vue — 关键交互元素提供稳定 id -->
<template>
  <div class="login-page" :style="{ backgroundImage: `url(${bgImage})` }">
    <!-- ✅ input 必须提供 id（required_stable_attributes，从 config 读取） -->
    <input
      id="login-username"
      v-model="form.username"
      placeholder="用户名"
      type="text"
    />
    <input
      id="login-password"
      v-model="form.password"
      placeholder="密码"
      type="password"
    />
    <!-- ✅ button 提供 class，作为选择器锚点 -->
    <button class="login-btn" @click="handleLogin">登录</button>
  </div>
</template>
```

## 错误示例

```ts
// ❌ 使用 placeholder 选择器 + networkidle 等待策略
import { test, expect } from '@playwright/test'

test('user can login', async ({ page }) => {
  // ❌ networkidle 在含 background-image 的页面永不触发 → 超时
  await page.goto('/login', { waitUntil: 'networkidle' })

  // ❌ placeholder 选择器：文案调整（如国际化）会导致匹配失败
  // ❌ 多个 input 可能匹配同一 placeholder 模式，定位不稳定
  await page.fill("input[placeholder*='用户']", 'testuser')
  await page.fill("input[placeholder*='密码']", 'pass1234')

  // ❌ :has-text('登录') 可能匹配多个按钮（如"忘记登录密码"链接）
  await page.click("button:has-text('登录')")

  await expect(page).toHaveURL('/dashboard')
})
```

```ts
// ❌ 测试代码用 data-testid，但组件未提供（FR-044-2 违规）
// 测试文件：
await page.click('[data-testid="login-submit"]')

// 对应组件 Login.vue：
// <button class="primary-btn" @click="handleLogin">登录</button>
// ❌ button 既无 id 也无 data-testid，测试 data-testid 选择器会失败
// 修复：在组件中补充 data-testid="login-submit"
```

```ts
// ❌ DOM 变更未同步测试选择器（FR-044-4 与 FR-031 联动违规）
// PR commit 1：Login.vue 中 <button id="login-btn"> 改为 <button class="login-btn">
// PR commit 2：测试仍引用 #login-btn
await page.click('#login-btn')  // ❌ 元素已无 id，定位失败
// 修复：同 PR 内同步测试选择器为 .login-btn（或更优，恢复 id）
```

## 与其他规则的关系

- **FR-031（测试用例与代码结构同步）**：FR-044-4 与 FR-031 形成"流程合规 + 质量合规"双向联动。FR-031 关注 DOM 变更触发测试同步的流程；FR-044 关注测试选择器本身的质量（优先级、稳定属性、等待策略）。两者同时命中触发 Urgent。
- **FR-030（E2E 测试前置服务检查）**：FR-030 关注"服务未起"导致的连接失败；FR-044 关注"服务已起但选择器/等待策略不当"导致的测试失败。两者互补覆盖 E2E 测试全链路。
- **DA-8（破坏性按钮防护）**：FR-044-2 中的"触发业务逻辑的按钮"范围与 `destructive_button_patterns` 一致，确保破坏性按钮既有防护又有稳定选择器。
- **ES-7（禁用元素显式属性）**：FR-044-2 强制稳定属性，ES-7 强制 `disabled` 属性，两者共同要求交互元素以"属性"而非"样式"承载语义。

## 适配新项目

- **Cypress**：`forbidden_wait_strategy` 改为 `networkIdle`（驼峰），`recommended_wait_strategy` 改为 `domContentLoaded`；选择器优先级顺序不变。`cy.visit()` 默认 `load` 事件，可显式传 `{ timeout: ... }`。
- **Vitest / Jest（jsdom）**：FR-044-3 不适用（无网络请求）；FR-044-1 / FR-044-2 仍适用，`getByTestId()` 优先于 `querySelector('.class')`。
- **Selenium**：`forbidden_wait_strategy` 改为 `pageLoadStrategy: none`（等价于不等待），`recommended_wait_strategy` 改为 `eager`；显式等待用 `WebDriverWait(driver, By.id('xxx'))`。
- **纯静态页面（无背景图/SSE/视频/轮询）**：`forbidden_wait_strategy` 可设为空字符串跳过 FR-044-3 检查（networkidle 在静态页面可正常触发）。
- **React / Next.js**：组件源码中将 `id="login-username"` 改为 JSX `id="login-username"`（无需 `v-model`）；其余规则不变。
