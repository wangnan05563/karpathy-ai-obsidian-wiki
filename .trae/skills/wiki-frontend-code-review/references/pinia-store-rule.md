# Rule Catalog — Pinia Store

> 通用规则文件，具体 SSE 事件类型与 action 命名以 `config/review-config.md` 为准。

## 使用 setup 语法定义 store

IsUrgent: True
Category: Pinia Store

### Description

`defineStore` 必须使用 setup 语法：`defineStore('name', () => { ... })`，禁止 options 语法（`{ state, getters, actions }`）。setup 语法与 Composition API 一致、可自由组合 `ref`/`computed`/函数，便于在组件与 store 间复用逻辑。

### Suggested Fix

把 options 语法的 state/getters/actions 迁移为 setup 内的 `ref`/`computed`/函数，并在末尾 `return` 外部需要的成员。

Wrong:

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

Right:

```ts
export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const append = (m: Message) => {
    messages.value.push(m)
  }
  return { messages, append }
})
```

## store 内部用 ref 定义状态，function 定义 action

IsUrgent: False
Category: Pinia Store

### Description

状态用 `ref` 声明（访问处加 `.value`），派生状态用 `computed`，变更逻辑用普通 `function` 声明——不区分 mutations 与 actions。setup 语法下没有 mutations 概念，混用 options 心智模型会引入 `this` 歧义。

### Suggested Fix

把 `this.xxx = ...` 改为 `xxx.value = ...`，把 `actions` 中的方法改为顶层 `function`。

Wrong:

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

Right:

```ts
defineStore('chat', () => {
  const messages = ref<Message[]>([])
  function append(m: Message) {
    messages.value.push(m)
  }
  return { messages, append }
})
```

## 须 return 所有外部需要的状态和方法

IsUrgent: True
Category: Pinia Store

### Description

setup 语法下，store 只暴露在 `return` 语句中列出的成员。遗漏 return 会导致组件中使用 `storeXxx is undefined`，且无类型报错提示（仅在运行时暴露）。提交前须核对组件实际使用的成员是否都已 return。

### Suggested Fix

对照组件使用清单，逐项核对 store 末尾 `return` 对象；建议按状态/计算/动作分组排列。

Wrong:

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

Right:

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

## SSE 事件处理拆分为独立函数

IsUrgent: True
Category: Pinia Store

### Description

SSE 流式事件的处理逻辑必须按事件类型拆分为独立的具名函数（如 `appendAnswer`/`setRefs`/`finalizeAnswer`），由消费 SSE 的组件按事件类型分发调用。禁止把所有事件处理内联到组件的 `onMessage` 回调里——这会让 store 逻辑泄漏到组件，且无法被测试与复用。

### Suggested Fix

在 store 内为每种事件类型定义独立 action，组件侧只做"事件类型 → action"的派发。

Wrong:

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

Right:

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

## 错误处理须保留部分数据并结束 loading

IsUrgent: True
Category: Pinia Store

### Description

SSE 流或异步请求失败时，错误处理 action 必须：(1) 保留已接收的部分数据（不重置已 push 的消息）；(2) 将 `loading` 标记为 `false`；(3) 设置错误状态字段供 UI 展示。直接 throw 或重置状态会导致用户丢失已生成内容、界面卡在 loading。

### Suggested Fix

抽出 `markError(err)` action，只更新 loading 与 error 字段，不动 messages。

Wrong:

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

Right:

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

## store 间不直接引用，通过组件组合

IsUrgent: False
Category: Pinia Store

### Description

store 之间禁止互相 `useXxxStore()` 直接调用以避免循环依赖与初始化顺序问题。需要跨 store 的数据流时，由组件同时引入两个 store 并在组件内组合；确有共享逻辑时，抽到独立的 composable（`useXxx`）中。

### Suggested Fix

删除 store A 内 `useBStore()` 的调用，把跨 store 协调移到组件层；共享逻辑抽 composable。

Wrong:

```ts
// stores/chat.ts
import { useAuthStore } from './auth'
export const useChatStore = defineStore('chat', () => {
  const auth = useAuthStore() // store 间直接耦合
  const send = () => api.chat(auth.token, …)
  return { send }
})
```

Right:

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
