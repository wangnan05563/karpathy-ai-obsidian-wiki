# Rule Catalog - SPA Internal Navigation (Frontend Cross-Component)

## Scope
- Covers: SPA 项目中跨组件视图切换（如 About → Help）的 CustomEvent 派发与监听审查，含生命周期配对、参数校验、事件命名规范。
- Does NOT cover: vue-router / react-router 项目（直接用 router.push）、SSR 跳转（属于框架层职责）、父子组件 props/emit 通信（属于组件内通信）。

> 所有可配置参数（事件名模式、项目名、允许视图名列表等）集中定义在 [config/review-config.md](../config/review-config.md) 的"SPA 内部跳转审查参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### SN-1: 跨组件视图切换必须通过 CustomEvent 派发

IsUrgent: True
Category: SPA Navigation

### Description

SPA 项目（无 vue-router）中，跨组件视图切换（如 About 视图内部点击"查看帮助文档"按钮跳转到 Help 视图）必须通过 `CustomEvent` 派发，由入口组件（如 `App.vue`）监听后切换 `currentView` ref。

禁止以下写法：
- 直接操作入口组件的 ref（违反组件隔离原则）
- 通过全局变量共享状态（难以追踪变更源）
- 通过 localStorage 间接传递跳转意图（异步且不可靠）

事件命名必须遵循 `spa_navigation.event_name_pattern`（默认 `{project}:navigate`），如 `karpathy:navigate`。

### Judgment Logic

1. 在目标 `.vue` 文件 `<template>` 段扫描跳转触发点（`@click` / `@keydown.enter`）。
2. 检查对应处理函数是否调用 `globalThis.dispatchEvent(new CustomEvent('xxx:navigate', { detail: 'viewName' }))`。
3. 验证事件名匹配 `spa_navigation.event_name_pattern`（`{project}:navigate`）。
4. 在入口组件（如 `App.vue`）中检查是否在 `onMounted` 中 `addEventListener` 同名事件，且在 `onBeforeUnmount` 中 `removeEventListener` 同名函数。

### Applicable Scenarios

- Vue 3 + `<script setup>` SPA 手动路由项目。
- 无 vue-router / react-router 的单视图切换应用。
- 入口组件通过 `currentView` ref + `v-if` / `v-else-if` 链路切换视图。

### Non-Applicable Scenarios

- vue-router / react-router 项目（直接用 `router.push('/path')`）。
- Next.js / Nuxt.js 文件系统路由。
- 父子组件通信（用 `props` / `emit` 即可）。
- 跨标签页通信（用 `BroadcastChannel` 或 `storage` 事件）。

### Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `spa_navigation.event_name_pattern` | `{project}:navigate` | 事件名模式，`{project}` 占位符运行时替换 |
| `spa_navigation.project_name` | `karpathy` | 项目名，替换事件名中的 `{project}` 占位符 |
| `spa_navigation.app_entry` | `frontend/src/App.vue` | 监听事件的入口组件路径 |
| `spa_navigation.allowed_views` | `[]` | 允许跳转的视图名白名单；留空表示不校验 |
| `spa_navigation.require_lifecycle_pair` | `true` | 监听器必须在 `onMounted` / `onBeforeUnmount` 配对管理 |

### Example

```vue
<!-- ❌ Wrong: 直接操作入口 ref / 全局变量 / localStorage -->
<script setup lang="ts">
function goToHelp() {
  // ❌ 直接修改外部 ref（违反组件隔离）
  window.appRef.currentView = 'help'
  // ❌ localStorage 异步且不可靠
  localStorage.setItem('navigate', 'help')
}
</script>

<!-- ✅ Right: CustomEvent 派发 + 入口组件监听 -->
<!-- About.vue -->
<script setup lang="ts">
const NAV_EVENT = 'karpathy:navigate'  // 与 config.spa_navigation.event_name_pattern 一致

function goToHelp() {
  globalThis.dispatchEvent(
    new CustomEvent(NAV_EVENT, { detail: 'help' })
  )
}
</script>

<template>
  <el-button @click="goToHelp">查看帮助文档</el-button>
</template>

<!-- App.vue -->
<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const currentView = ref<ViewName>('dashboard')

// ✅ 具名函数，便于 removeEventListener 配对
function handleNavigate(e: Event) {
  const detail = (e as CustomEvent<string>).detail
  // ✅ 白名单校验，防止恶意派发跳到不存在视图
  if (typeof detail === 'string' && allowedViews.includes(detail)) {
    currentView.value = detail as ViewName
  }
}

onMounted(() => {
  globalThis.addEventListener('karpathy:navigate', handleNavigate)
})

// ✅ 必须在 onBeforeUnmount 配对移除，防止内存泄漏
onBeforeUnmount(() => {
  globalThis.removeEventListener('karpathy:navigate', handleNavigate)
})
</script>
```

### Checklist

- [ ] 跨组件视图跳转通过 `CustomEvent` 派发，未直接操作外部 ref 或 localStorage
- [ ] 事件名匹配 `spa_navigation.event_name_pattern`（默认 `{project}:navigate`）
- [ ] 入口组件在 `onMounted` 中 `addEventListener`，在 `onBeforeUnmount` 中 `removeEventListener`
- [ ] 监听器使用具名函数（非匿名箭头函数），确保 add 与 remove 引用同一函数
- [ ] `detail` 字段在 `allowed_views` 白名单内校验后才切换视图
