# performance-rule - Code Examples

> This file contains Wrong/Right code examples extracted from [performance-rule.md](../performance-rule.md).
> Load on demand when you need to reference examples or generate fix code.

---

## vis-network 大图分级降级

### Wrong

```ts
const network = new Network(container, data, {
  // 无论节点数都用同一份高开销配置
  edges: { smooth: { enabled: true, type: 'dynamic' } },
  physics: { stabilization: { iterations: 500 } }
})
```

### Right

```ts
import { NODE_THRESHOLD_L2, NODE_THRESHOLD_L3 } from '@/config/wiki-graph'
function buildOptions(nodeCount: number): Options {
  if (nodeCount > NODE_THRESHOLD_L3) {
    return {
      edges: { smooth: false },
      physics: { stabilization: { iterations: 80 } }
    }
  }
  if (nodeCount > NODE_THRESHOLD_L2) {
    return { edges: { smooth: false } }
  }
  return { edges: { smooth: { enabled: true, type: 'dynamic' } } }
}
const network = new Network(container, data, buildOptions(data.nodes.length))
```

---

## vis-network 实例须在 onBeforeUnmount 中 destroy

### Wrong

```ts
let network: Network | null = null
onMounted(() => {
  network = new Network(container, data, options)
})
// 缺少 onBeforeUnmount 销毁
```

### Right

```ts
const networkRef = ref<Network | null>(null)
onMounted(() => {
  networkRef.value = new Network(container, data, options)
})
onBeforeUnmount(() => {
  networkRef.value?.destroy()
  networkRef.value = null
})
```

---

## 窄屏切换列表视图，减少 Canvas 渲染

### Wrong

```ts
// 始终渲染图谱，窄屏下卡顿
const showGraph = ref(true)
```

### Right

```ts
import { BREAKPOINT_MOBILE } from '@/config/breakpoint'
const viewMode = ref<'graph' | 'list'>('graph')
const handleResize = () => {
  viewMode.value = window.innerWidth < BREAKPOINT_MOBILE ? 'list' : 'graph'
}
onMounted(() => {
  handleResize()
  window.addEventListener('resize', debounce(handleResize, 200))
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', debounce(handleResize, 200))
})
```

---

## SSE 消费用 ReadableStream 逐块解析，禁止 await 全量

### Wrong

```ts
const res = await fetch(url)
// 错误：等整个响应结束才处理，丧失流式
const text = await res.text()
text.split('\n\n').forEach(handleEvent)
```

### Right

```ts
const res = await fetch(url)
if (!res.body) throw new Error('No stream')
const reader = res.body.getReader()
const decoder = new TextDecoder()
let buffer = ''
while (true) {
  const { done, value } = await reader.read()
  if (done) break
  buffer += decoder.decode(value, { stream: true })
  const lines = buffer.split('\n\n')
  buffer = lines.pop() ?? ''
  for (const line of lines) {
    if (line.startsWith('data: ')) handleEvent(line.slice(6))
  }
}
```

---

## 事件监听须在 onBeforeUnmount 移除

### Wrong

```ts
onMounted(() => {
  // 内联箭头函数，移除时无法匹配同一引用
  window.addEventListener('resize', () => handleResize())
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', () => handleResize())
})
```

### Right

```ts
const onResize = () => handleResize()
onMounted(() => {
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
})
```

---

## 列表渲染用 :key 绑定唯一 ID，禁止 index 作 key

### Wrong

```ts
<div v-for="(item, index) in list" :key="index">{{ item.name }}</div>
```

### Right

```ts
<div v-for="item in list" :key="item.id">{{ item.name }}</div>
```

---

*End of examples*