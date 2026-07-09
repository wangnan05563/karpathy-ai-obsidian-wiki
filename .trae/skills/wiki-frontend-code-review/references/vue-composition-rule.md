# Rule Catalog — Vue 3 Composition API

> 通用规则文件，具体路径、阈值、技术栈版本以 `config/review-config.md` 为准。

## 强制使用 script setup + TypeScript

IsUrgent: True
Category: Vue Composition

### Description

所有单文件组件必须使用 `<script setup lang="ts">` 语法编写，禁止使用 Options API（`export default { data, methods, computed }`）或无 `lang="ts"` 的 `<script setup>`。Composition API 配合 TypeScript 可提供更好的类型推断与逻辑复用，是项目统一约定。

### Suggested Fix

将 Options API 改写为 `setup` 写法，并把 `data`/`methods`/`computed` 迁移为 `ref`/`reactive`/`computed`/普通函数。

Wrong:

```vue
<script>
export default {
  data() {
    return { count: 0 }
  },
  methods: {
    increment() {
      this.count++
    }
  }
}
</script>
```

Right:

```vue
<script setup lang="ts">
import { ref } from 'vue'
const count = ref(0)
const increment = () => count.value++
</script>
```

## 响应式数据用 ref/reactive，computed 用于派生状态

IsUrgent: True
Category: Vue Composition

### Description

原始值与单一对象用 `ref`，复杂对象可用 `reactive`；派生状态必须用 `computed` 包裹，禁止在模板中调用方法做计算或在 `watch` 中手动同步派生值。直接修改 `reactive` 的根引用会丢失响应性，需整体替换时改用 `ref`。

### Suggested Fix

把"读取依赖 → 返回结果"的逻辑改为 `computed`；避免对 `reactive` 对象做整体赋值。

Wrong:

```ts
const list = reactive([])
// 直接替换 reactive 引用会丢失响应性
list = fetchResult
```

Right:

```ts
const list = ref<RepoItem[]>([])
list.value = fetchResult
```

## 生命周期成对使用：onMounted 初始化 / onBeforeUnmount 清理

IsUrgent: True
Category: Vue Composition

### Description

在 `onMounted` 中执行依赖 DOM 的初始化（如实例化 vis-network、加载数据、注册 window 事件）；在 `onBeforeUnmount` 中执行对等清理（销毁 Network 实例、移除事件监听、关闭 SSE 流）。两者必须成对出现，避免内存泄漏与僵尸监听。

### Suggested Fix

逐项检查 `onMounted` 中创建的资源，为每项在 `onBeforeUnmount` 中编写对应的释放逻辑。

Wrong:

```ts
onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 缺少移除逻辑
})
```

Right:

```ts
onMounted(() => {
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
```

## watch 须避免无限递归，深层 watch 显式声明

IsUrgent: False
Category: Vue Composition

### Description

`watch` 监听自身会修改的响应式源会造成无限递归，需通过 `flush: 'post'`、改用 `watchEffect` 或拆分数据源规避。监听嵌套对象属性变化须显式传入 `{ deep: true }`，否则深层变更不触发回调。

### Suggested Fix

检查回调内是否会写回被监听的对象；需要监听嵌套结构时补上 `{ deep: true }`。

Wrong:

```ts
watch(count, (v) => {
  // 回调内写回被监听源，递归触发
  count.value = clamp(v, 0, 100)
})
```

Right:

```ts
watch(count, (v) => {
  if (v < 0) count.value = 0
  else if (v > 100) count.value = 100
})

watch(config, (newVal) => {
  // 显式声明深层监听
}, { deep: true })
```

## 事件处理函数命名用 handle*

IsUrgent: False
Category: Vue Composition

### Description

组件内事件处理函数统一以 `handle` 开头（如 `handleSubmit`、`handleResize`、`handleNodeClick`）；对外 emit 的事件名用 `on*` 或 kebab-case 事件名。命名一致可降低跨文件阅读成本。

### Suggested Fix

把 `submit`/`onClick`/`resizeFn` 等不一致命名统一改为 `handle*`。

Wrong:

```vue
<el-button @click="submit">提交</el-button>
<script setup lang="ts">
const submit = () => { /* ... */ }
</script>
```

Right:

```vue
<el-button @click="handleSubmit">提交</el-button>
<script setup lang="ts">
const handleSubmit = () => { /* ... */ }
</script>
```

## ref 模板引用须在 DOM 渲染后使用

IsUrgent: True
Category: Vue Composition

### Description

模板引用（`ref="containerRef"`）在 `v-if` 切换为 false 时为 `null`，在 `setup` 顶层直接访问会得到 `null`。需要容器存在的初始化逻辑应放在 `onMounted`，或用 `v-show` 替代 `v-if` 保证 ref 始终存在；访问前必须判空。

### Suggested Fix

把依赖 ref 的逻辑移入 `onMounted` 或 `nextTick`；对可能为空的 ref 使用 `v-show` 保活，并在使用前判空。

Wrong:

```vue
<template>
  <div ref="containerRef" v-if="visible"></div>
</template>
<script setup lang="ts">
const containerRef = ref<HTMLDivElement | null>(null)
// setup 顶层访问，此时 v-if=false 时 ref 为 null
const network = new Network(containerRef.value!, …)
</script>
```

Right:

```vue
<template>
  <div ref="containerRef" v-show="visible"></div>
</template>
<script setup lang="ts">
const containerRef = ref<HTMLDivElement | null>(null)
onMounted(() => {
  if (!containerRef.value) return
  const network = new Network(containerRef.value, …)
})
</script>
```
