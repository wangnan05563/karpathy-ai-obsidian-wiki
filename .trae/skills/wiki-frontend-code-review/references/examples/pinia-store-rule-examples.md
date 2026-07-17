# pinia-store-rule - Code Examples

> This file contains Wrong/Right code examples extracted from [pinia-store-rule.md](../pinia-store-rule.md).
> Load on demand when you need to reference examples or generate fix code.

---

## 使用 setup 语法定义 store

### Wrong

```ts
export const useChatStore = defineStore('chat', {
  state: () => ({ messages: [] as Message[] }),
  actions: {
    append(m: Message) {
      this.messages.push(m)
    }
  }
})
```

### Right

```ts
export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const append = (m: Message) => {
    messages.value.push(m)
  }
  return { messages, append }
})
```

---

## store 内部用 ref 定义状态，function 定义 action

### Wrong

```ts
defineStore('chat', () => {
  const messages = ref<Message[]>([])
  function append(m: Message) {
    // 错误：setup 语法下没有 this
    this.messages.push(m)
  }
  return { messages, append }
})
```

### Right

```ts
defineStore('chat', () => {
  const messages = ref<Message[]>([])
  function append(m: Message) {
    messages.value.push(m)
  }
  return { messages, append }
})
```

---

## 须 return 所有外部需要的状态和方法

### Wrong

```ts
defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const loading = ref(false)
  function append(m: Message) {
    messages.value.push(m)
  }
  // 漏 return loading，组件中使用会拿到 undefined
  return { messages, append }
})
```

### Right

```ts
defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const loading = ref(false)
  function append(m: Message) {
    messages.value.push(m)
  }
  return { messages, loading, append }
})
```

---

## SSE 事件处理拆分为独立函数

### Wrong

```ts
// 组件内
reader.onmessage = (e) => {
  const data = JSON.parse(e.data)
  // 全部内联处理，store 状态被组件直接改写
  if (data.type === 'answer') chatStore.messages.push({ text: data.text })
  else if (data.type === 'refs') chatStore.refs = data.refs
  else if (data.type === 'done') chatStore.loading = false
}
```

### Right

```ts
// store 内
function appendAnswer(text: string) {
  messages.value.push({ text })
}
function setRefs(refs: RefItem[]) {
  refsList.value = refs
}
function finalizeAnswer() {
  loading.value = false
}
return { appendAnswer, setRefs, finalizeAnswer }

// 组件内：仅做派发
reader.onmessage = (e) => {
  const data = JSON.parse(e.data)
  switch (data.type) {
    case 'answer': chatStore.appendAnswer(data.text); break
    case 'refs':   chatStore.setRefs(data.refs); break
    case 'done':   chatStore.finalizeAnswer(); break
  }
}
```

---

## 错误处理须保留部分数据并结束 loading

### Wrong

```ts
async function streamChat(question: string) {
  loading.value = true
  try {
    await consumeSSE(question)
  } catch (e) {
    // 错误时清空已生成内容，且未结束 loading
    messages.value = []
    throw e
  }
}
```

### Right

```ts
const error = ref<string | null>(null)
function markError(err: unknown) {
  // 保留 messages 中已接收的部分数据
  loading.value = false
  error.value = err instanceof Error ? err.message : '未知错误'
}
async function streamChat(question: string) {
  loading.value = true
  error.value = null
  try {
    await consumeSSE(question)
  } catch (e) {
    markError(e)
  }
}
```

---

## store 间不直接引用，通过组件组合

### Wrong

```ts
// stores/chat.ts
import { useAuthStore } from './auth'
export const useChatStore = defineStore('chat', () => {
  const auth = useAuthStore() // store 间直接耦合
  const send = () => api.chat(auth.token, …)
  return { send }
})
```

### Right

```ts
// stores/chat.ts — 不引用 auth store
export const useChatStore = defineStore('chat', () => {
  const send = (token: string) => api.chat(token, …)
  return { send }
})

// 组件内组合两个 store
const auth = useAuthStore()
const chat = useChatStore()
chat.send(auth.token)
```

---

*End of examples*