# 事件委托 + 生命周期清理（FR-052）

> 复盘来源：v3 媒体生成工具的 MultimodalOutputCard.vue 用 `v-html` 渲染 LLM 返回的 Markdown（含 Mermaid 图表），初期尝试在 v-html 内容上绑定 `@click` 事件失败——Vue 无法对 v-html 渲染的 DOM 绑定事件；后改为父容器 `addEventListener` 事件委托，按 `target.tagName` / `target.closest(selector)` 命中目标。同时 onBeforeUnmount 初期未移除监听器，导致组件卸载后回调飞溅；后补齐 `removeEventListener` 并保存函数引用。第三方库实例（mermaid/marp）初期未在卸载时销毁，导致内存泄漏。
> 所有可变参数从 config/review-config.md 的 `event_delegation_frontend` 字段读取，禁止在规则文件中硬编码选择器或库名。

## 规则

### FR-052-1：v-html 渲染内容的事件绑定必须用父容器事件委托，禁止在 v-html DOM 上绑事件

- **Severity**: critical
- **Description**：Vue 中 `v-html` 渲染的 DOM 节点无法绑定 Vue 事件（`@click` 等指令对 v-html 内容无效），必须用父容器 `addEventListener` 事件委托：在父容器上监听事件，通过 `event.target.tagName` / `event.target.closest(selector)` 命中目标元素后执行对应逻辑。原因：v-html 内容是运行时动态注入的 raw HTML，Vue 编译器无法对其绑定事件；强行绑定会导致事件不触发，用户点击无响应。
- **判定标准**：检索 `v-html` 指令使用点，若同元素或其子元素尝试用 `@click` / `@mousedown` 等 Vue 事件指令绑定，即视为违规。修复方式：改为父容器 `addEventListener('click', handler)` 事件委托，handler 内用 `target.closest(selector)` 命中目标。

### FR-052-2：事件委托 handler 必须按 target.tagName / target.closest(selector) 命中目标

- **Severity**: critical
- **Description**：事件委托 handler 必须通过 `event.target.tagName` / `event.target.closest(event_delegation_frontend.target_selectors)`（默认 `a, button, img, code`）命中目标元素，禁止直接操作 `event.target`——`event.target` 可能是目标元素的子节点（如 `<a>` 内的 `<span>`），直接操作会漏处理。`closest(selector)` 会向上查找最近匹配的祖先元素，确保命中目标。
- **判定标准**：检索事件委托 handler，若直接操作 `event.target`（无 `closest` / `tagName` 判定），即视为违规。修复方式：`const target = (event.target as HTMLElement).closest('a'); if (!target) return;`。

### FR-052-3：onBeforeUnmount 必须移除所有 addEventListener 注册的监听器，函数引用须保存

- **Severity**: critical
- **Description**：组件中所有 `addEventListener` 注册的监听器必须在 `onBeforeUnmount` 中用 `removeEventListener` 移除，且必须用**同一函数引用**（匿名箭头函数无法移除）。原因：若不移除，组件卸载后监听器仍挂在 DOM 上，回调引用已销毁的组件状态导致飞溅报错；匿名函数无法匹配 removeEventListener 的参数，移除失败。
- **判定标准**：检索组件中的 `addEventListener` 调用，若对应的 `removeEventListener` 缺失，或用匿名函数注册（无具名函数引用保存），即视为违规。修复方式：`const handler = () => {...}; container.addEventListener('click', handler); onBeforeUnmount(() => container.removeEventListener('click', handler))`。

### FR-052-4：全局事件（globalThis.addEventListener）必须配对 removeEventListener

- **Severity**: critical
- **Description**：注册到 `globalThis` / `window` / `document` 的全局事件监听器（如 `keydown` / `resize` / `scroll` / `popstate`）必须在 `onBeforeUnmount` 中配对 `removeEventListener` 移除。全局事件不会随组件卸载自动清理，是最常见的内存泄漏源。
- **判定标准**：检索 `globalThis.addEventListener` / `window.addEventListener` / `document.addEventListener` 调用，若 `onBeforeUnmount` 中无对应 `removeEventListener`，即视为违规。修复方式：保存函数引用，在 `onBeforeUnmount` 中移除。

### FR-052-5：第三方库实例（mermaid/marp/monaco 等）必须在 onBeforeUnmount 调用 destroy/dispose

- **Severity**: warning
- **Description**：组件中创建的第三方库实例（如 `mermaid` / `marp` / `monaco editor` / `codemirror`）若提供 `destroy()` / `dispose()` / `cleanup()` 方法，必须在 `onBeforeUnmount` 中调用。原因：这些库通常持有 DOM 引用、事件监听器、定时器等资源，不销毁会内存泄漏；即使库未显式提供 destroy 方法，也应清空容器（`container.innerHTML = ''`）释放 DOM 引用。
- **判定标准**：检索组件中第三方库实例创建代码（`new Editor()` / `mermaid.initialize()` / `marpInstance` 等），若 `onBeforeUnmount` 中无对应 `destroy()` / `dispose()` 调用（且库提供该方法），即视为违规。修复方式：在 `onBeforeUnmount` 中调用销毁方法，或清空容器。

## 适用场景

- Vue 3 / React 项目中用 `v-html` 渲染 LLM 返回的 Markdown / HTML 内容。
- 富文本编辑器、文档预览、知识库等含动态 HTML 内容的页面。
- 使用 mermaid / marp / monaco / codemirror 等第三方库创建实例的组件。
- 注册全局事件（快捷键、窗口尺寸、滚动等）的组件。

## 不适用场景

- 纯模板渲染（`{{ }}` / `v-if` / `v-for` 生成的 DOM，Vue 自动管理事件）。
- 静态 HTML（编译期确定，无运行时注入风险）。
- 单元测试中的 mock 事件（测试本身验证事件逻辑）。
- SSR 场景（服务端无 DOM 事件，仅客户端 hydration 后适用）。

## 检查流程

```
[开始] 扫描 .vue / .ts 文件中的 v-html 与 addEventListener
  │
  ▼
[1] v-html 事件委托检查（FR-052-1）
  │  └─ 检索 v-html 指令使用点
  │       └─ 同元素或子元素有 @click / @mousedown 等 → 标记违规
  │       └─ 父容器有 addEventListener 事件委托 → 合规
  │
  ▼
[2] 命中目标方式检查（FR-052-2）
  │  └─ 检索事件委托 handler
  │       └─ 直接操作 event.target（无 closest/tagName）→ 标记违规
  │       └─ 用 target.closest(selector) 命中 → 合规
  │
  ▼
[3] 监听器移除检查（FR-052-3）
  │  └─ 检索 addEventListener 调用
  │       └─ onBeforeUnmount 无对应 removeEventListener → 标记违规
  │       └─ 用匿名函数注册（无具名引用）→ 标记违规（无法移除）
  │
  ▼
[4] 全局事件配对检查（FR-052-4）
  │  └─ 检索 globalThis/window/document.addEventListener
  │       └─ onBeforeUnmount 无对应 removeEventListener → 标记违规
  │
  ▼
[5] 第三方库实例销毁检查（FR-052-5）
  │  └─ 检索第三方库实例创建（new Editor / mermaid.initialize / marpInstance）
  │       └─ onBeforeUnmount 无 destroy/dispose → 标记违规
  │       └─ 库无 destroy 方法但未清空容器 → 标记违规
  │
  ▼
[结束] 输出审查报告
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `event_delegation_frontend.enabled` | `true` | 是否启用事件委托审查 |
| `event_delegation_frontend.target_selectors` | `a, button, img, code, .copy-btn, .mermaid` | 事件委托命中目标的选择器列表（逗号分隔） |
| `event_delegation_frontend.tag_names_to_handle` | `A, BUTTON, IMG, CODE` | 事件委托按 tagName 命中的标签名列表（大写，逗号分隔） |
| `event_delegation_frontend.cleanup_hook` | `onBeforeUnmount` | 监听器清理的生命周期钩子名 |
| `event_delegation_frontend.global_event_targets` | `globalThis, window, document` | 全局事件注册目标（逗号分隔，必须配对 removeEventListener） |
| `event_delegation_frontend.library_instances` | `mermaid, marp, monaco, codemirror, chartjs, d3` | 需在卸载时销毁的第三方库实例清单（逗号分隔） |
| `event_delegation_frontend.destroy_method_names` | `destroy, dispose, cleanup, terminate` | 第三方库销毁方法名候选（逗号分隔，按库选择） |
| `event_delegation_frontend.require_named_function_ref` | `true` | 是否强制用具名函数引用注册监听器（禁止匿名函数） |
| `event_delegation_frontend.vhtml_directive` | `v-html` | Vue v-html 指令名（用于识别需事件委托的场景） |

## 检查方式

1. **v-html 扫描**：在 `.vue` 文件中检索 `v-html` 指令，定位动态 HTML 渲染点。
2. **事件绑定核对**：对每个 v-html 使用点，检查同元素及子元素是否有 `@click` / `@mousedown` 等 Vue 事件指令。
3. **事件委托检查**：检索父容器的 `addEventListener` 调用，验证是否有对应 v-html 内容的事件委托。
4. **命中目标分析**：检索事件委托 handler，验证是否用 `target.closest(selector)` / `target.tagName` 命中目标。
5. **监听器移除核对**：检索所有 `addEventListener` 调用，对照 `onBeforeUnmount` 验证是否有对应 `removeEventListener`；检查是否用具名函数引用。
6. **全局事件检查**：检索 `globalThis.addEventListener` / `window.addEventListener` / `document.addEventListener`，验证配对移除。
7. **第三方库实例检查**：检索 `library_instances` 中的库实例创建代码，验证 `onBeforeUnmount` 中是否有 `destroy` / `dispose` 调用或容器清空。

## 正确示例

```vue
<!-- ✅ v-html 事件委托 + 监听器清理 + 库实例销毁（FR-052-1/2/3/5） -->
<template>
  <!-- ✅ 父容器用 ref 拿到 DOM 引用，v-html 内容不绑 Vue 事件（FR-052-1） -->
  <div ref="contentRef" class="markdown-content" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import mermaid from 'mermaid'

const contentRef = ref<HTMLElement>()
const renderedHtml = ref('')

// ✅ 保存具名函数引用以便 removeEventListener（FR-052-3）
const handleClick = (event: MouseEvent) => {
  // ✅ 用 target.closest(selector) 命中目标（FR-052-2）
  const link = (event.target as HTMLElement).closest('a')
  if (!link) return

  // 处理链接点击
  console.log('Link clicked:', link.href)
}

const handleCopy = (event: MouseEvent) => {
  // ✅ 用 target.closest(selector) 命中复制按钮（FR-052-2）
  const copyBtn = (event.target as HTMLElement).closest('.copy-btn')
  if (!copyBtn) return

  const code = copyBtn.previousElementSibling?.textContent || ''
  navigator.clipboard.writeText(code)
}

// ✅ 全局事件用具名函数引用（FR-052-4）
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    console.log('Escape pressed')
  }
}

let mermaidInitialized = false

onMounted(() => {
  // ✅ 父容器事件委托替代 v-html 上绑事件（FR-052-1）
  contentRef.value?.addEventListener('click', handleClick)
  contentRef.value?.addEventListener('click', handleCopy)

  // ✅ 全局事件注册（FR-052-4）
  window.addEventListener('keydown', handleKeydown)

  // ✅ 第三方库实例初始化（FR-052-5）
  if (!mermaidInitialized) {
    mermaid.initialize({ startOnLoad: false, suppressErrorRendering: true })
    mermaidInitialized = true
  }
})

// ✅ watch v-html 内容变化后重新渲染 mermaid
watch(renderedHtml, async () => {
  await nextTick()
  const mermaidElements = contentRef.value?.querySelectorAll('.mermaid')
  mermaidElements?.forEach((el) => {
    mermaid.render(`m-${Date.now()}`, (el as HTMLElement).textContent || '').then(({ svg }) => {
      el.innerHTML = svg
    })
  })
})

// ✅ onBeforeUnmount 移除所有监听器（FR-052-3/4）
onBeforeUnmount(() => {
  // ✅ 移除父容器事件委托监听器（用保存的函数引用）（FR-052-3）
  contentRef.value?.removeEventListener('click', handleClick)
  contentRef.value?.removeEventListener('click', handleCopy)

  // ✅ 移除全局事件监听器（FR-052-4）
  window.removeEventListener('keydown', handleKeydown)

  // ✅ 清空容器释放 DOM 引用（mermaid 无 destroy 方法，用清空替代）（FR-052-5）
  if (contentRef.value) {
    contentRef.value.innerHTML = ''
  }
})
</script>
```

## 错误示例

```vue
<!-- ❌ v-html 上绑 Vue 事件（FR-052-1 违规） -->
<template>
  <!-- ❌ @click 对 v-html 渲染的 <a> 标签无效，Vue 编译器无法绑定 -->
  <div v-html="renderedHtml" @click="handleClick"></div>
</template>

<script setup lang="ts">
const handleClick = (e: MouseEvent) => {
  // ❌ 此 handler 永远不会触发，用户点击链接无响应
  console.log('clicked')
}
</script>
```

```ts
// ❌ 直接操作 event.target（FR-052-2 违规）
const handleClick = (event: MouseEvent) => {
  // ❌ event.target 可能是 <a> 内的 <span>，直接操作会漏处理
  const href = (event.target as HTMLElement).getAttribute('href')
  // 若点击 <a><span>text</span></a> 的 span，target 是 span 无 href
  console.log(href)  // ❌ null
}

// ✅ 正确：用 closest 向上查找
const handleClickFixed = (event: MouseEvent) => {
  const link = (event.target as HTMLElement).closest('a')
  if (!link) return
  console.log(link.href)  // ✅ 总能命中 <a>
}
```

```ts
// ❌ 监听器未移除 + 匿名函数无法移除（FR-052-3 违规）
onMounted(() => {
  // ❌ 匿名函数注册，removeEventListener 无法匹配
  contentRef.value?.addEventListener('click', (event: MouseEvent) => {
    console.log('clicked')
  })
})

onBeforeUnmount(() => {
  // ❌ 无法移除匿名函数，监听器残留
  contentRef.value?.removeEventListener('click', ???)  // ❌ 无函数引用可传
})
```

```ts
// ❌ 全局事件未配对移除（FR-052-4 违规）
onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

// ❌ 无 onBeforeUnmount 或 onBeforeUnmount 中无 removeEventListener
// ❌ 组件卸载后 handleKeydown 仍挂在 window 上，引用已销毁的组件状态
```

```ts
// ❌ 第三方库实例未销毁（FR-052-5 违规）
import Editor from '@monaco/editor'

let editor: Editor

onMounted(() => {
  editor = new Editor(container.value)
})

// ❌ onBeforeUnmount 未调用 editor.dispose()
// ❌ Monaco 持有 DOM 引用 + 事件监听器 + 定时器，内存泄漏
onBeforeUnmount(() => {
  // 应补齐：editor?.dispose()
})
```

## 与其他规则的关系

- **FR-046（第三方库错误防护）**：FR-052-5 约束库实例的销毁，FR-046 约束库渲染的错误防护。两者互补：FR-046 防止库渲染崩溃，FR-052-5 防止库实例泄漏。
- **FR-053（第三方重库动态加载）**：FR-053 约束库的加载方式（动态 import + 标志防重复），FR-052-5 约束库实例的销毁。两者共同覆盖第三方库的生命周期管理。
- **FR-051（长任务轮询 UI）**：FR-051-6 的 onBeforeUnmount 清理与 FR-052-3/4 的监听器清理互补——FR-051-6 关注轮询资源，FR-052 关注事件监听器。
- **AR-3（定时器清理）**：AR-3 通用约束定时器清理，FR-052-3/4 细化为事件监听器清理，两者同属 onBeforeUnmount 资源清理职责。
- **vue.cleanup_required**：Vue 通用规则要求事件监听器必须清理，FR-052 细化 v-html 场景的事件委托与全局事件配对移除。

## 适配新项目

- **React / Next.js**：`v-html` 改为 `dangerouslySetInnerHTML`；`addEventListener` 在 `useEffect` 中注册；`onBeforeUnmount` 改为 `useEffect` cleanup；`ref` 改为 `useRef`；事件委托逻辑不变。
- **Vue 2**：`onMounted` / `onBeforeUnmount` 改为 `mounted` / `beforeDestroy`；`ref` 改为 `this.$refs`；事件委托逻辑不变。
- **纯 JavaScript**：去掉框架生命周期，用自定义 `destroy()` 函数封装清理逻辑；事件委托逻辑不变。
- **Angular**：`v-html` 改为 `[innerHTML]`；`addEventListener` 在 `ngOnInit` / `ngAfterViewInit` 注册；`onBeforeUnmount` 改为 `ngOnDestroy`；事件委托用 `Renderer2.listen` 自动清理。
- **Svelte**：`v-html` 改为 `{@html}`；`addEventListener` 在 `onMount` 注册；`onBeforeUnmount` 改为 `onDestroy`；事件委托逻辑不变。
