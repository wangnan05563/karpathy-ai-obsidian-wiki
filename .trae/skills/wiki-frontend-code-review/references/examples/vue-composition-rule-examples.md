# vue-composition-rule - Code Examples

> This file contains Wrong/Right code examples extracted from [vue-composition-rule.md](../vue-composition-rule.md).
> Load on demand when you need to reference examples or generate fix code.

---

## 强制使用 script setup + TypeScript

### Wrong

```ts
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

### Right

```ts
<script setup lang="ts">
import { ref } from 'vue'
const count = ref(0)
const increment = () => count.value++
</script>
```

---

## 响应式数据用 ref/reactive，computed 用于派生状态

### Wrong

```ts
const list = reactive([])
// 直接替换 reactive 引用会丢失响应性
list = fetchResult
```

### Right

```ts
const list = ref<RepoItem[]>([])
list.value = fetchResult
```

---

## 生命周期成对使用：onMounted 初始化 / onBeforeUnmount 清理

### Wrong

```ts
onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 缺少移除逻辑
})
```

### Right

```ts
onMounted(() => {
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
```

---

## watch 须避免无限递归，深层 watch 显式声明

### Wrong

```ts
watch(count, (v) => {
  // 回调内写回被监听源，递归触发
  count.value = clamp(v, 0, 100)
})
```

### Right

```ts
watch(count, (v) => {
  if (v < 0) count.value = 0
  else if (v > 100) count.value = 100
})

watch(config, (newVal) => {
  // 显式声明深层监听
}, { deep: true })
```

---

## 事件处理函数命名用 handle*

### Wrong

```ts
<el-button @click="submit">提交</el-button>
<script setup lang="ts">
const submit = () => { /* ... */ }
</script>
```

### Right

```ts
<el-button @click="handleSubmit">提交</el-button>
<script setup lang="ts">
const handleSubmit = () => { /* ... */ }
</script>
```

---

## ref 模板引用须在 DOM 渲染后使用

### Wrong

```ts
<template>
  <div ref="containerRef" v-if="visible"></div>
</template>
<script setup lang="ts">
const containerRef = ref<HTMLDivElement | null>(null)
// setup 顶层访问，此时 v-if=false 时 ref 为 null
const network = new Network(containerRef.value!, …)
</script>
```

### Right

```ts
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

---

*End of examples*