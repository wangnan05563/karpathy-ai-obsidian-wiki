# type-safety-rule - Code Examples

> This file contains Wrong/Right code examples extracted from [type-safety-rule.md](../type-safety-rule.md).
> Load on demand when you need to reference examples or generate fix code.

---

## API 响应须定义 TypeScript interface，禁止 any

### Wrong

```ts
async function fetchWiki(id: string): Promise<any> {
  const res = await fetch(`/api/wiki/${id}`)
  return res.json()
}
```

### Right

```ts
interface WikiPage {
  id: string
  title: string
  content: string
  updatedAt: string
}
async function fetchWiki(id: string): Promise<WikiPage> {
  const res = await fetch(`/api/wiki/${id}`)
  return res.json() as Promise<WikiPage>
}
```

---

## fetch 须先检查 res.ok，再 json() 解析

### Wrong

```ts
async function loadPage(id: string) {
  const res = await fetch(`/api/wiki/${id}`)
  // 404 时不抛错，data 为错误页 HTML，json() 会抛 SyntaxError
  return res.json()
}
```

### Right

```ts
async function loadPage(id: string): Promise<WikiPage> {
  const res = await fetch(`/api/wiki/${id}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  return res.json()
}
```

---

## SSE 事件 data 须 JSON.parse 后用类型守卫

### Wrong

```ts
reader.onmessage = (e) => {
  // 未 try/catch，未做结构校验
  const data = JSON.parse(e.data) as AnswerEvent
  store.appendAnswer(data.text)
}
```

### Right

```ts
type SSEEvent =
  | { type: 'answer'; text: string }
  | { type: 'refs'; refs: RefItem[] }
  | { type: 'done' }

function parseSSEEvent(raw: string): SSEEvent | null {
  try {
    const parsed = JSON.parse(raw)
    // 用判别字段做类型守卫
    if (parsed.type === 'answer' && typeof parsed.text === 'string') return parsed
    if (parsed.type === 'refs' && Array.isArray(parsed.refs)) return parsed
    if (parsed.type === 'done') return parsed
    return null
  } catch {
    return null
  }
}
reader.onmessage = (e) => {
  const evt = parseSSEEvent(e.data)
  if (!evt) return
  // 此处 evt 已被窄化为具体类型
  switch (evt.type) {
    case 'answer': store.appendAnswer(evt.text); break
    case 'refs':   store.setRefs(evt.refs); break
    case 'done':   store.finalizeAnswer(); break
  }
}
```

---

## 联合类型窄化用 as 断言或类型守卫函数

### Wrong

```ts
type Issue = { type: 'broken_link'; url: string } | { type: 'orphan_page'; path: string }
function describe(i: Issue) {
  // 直接访问，TS 报错且运行时可能 undefined
  return i.url ?? i.path
}
```

### Right

```ts
type Issue = { type: 'broken_link'; url: string } | { type: 'orphan_page'; path: string }
function describe(i: Issue): string {
  if (i.type === 'broken_link') return i.url
  return i.path
}
// 或类型守卫函数
function isBrokenLink(i: Issue): i is Extract<Issue, { type: 'broken_link' }> {
  return i.type === 'broken_link'
}
```

---

## ref 须指定泛型类型

### Wrong

```ts
const container = ref(null)        // 推断为 Ref<null>
const list = ref([])               // 推断为 never[]
const network = ref(null)          // 推断为 Ref<null>
```

### Right

```ts
const container = ref<HTMLDivElement | null>(null)
const list = ref<WikiPage[]>([])
const network = ref<Network | null>(null)
```

---

## 枚举值用字面量联合类型，禁止 enum

### Wrong

```ts
enum IssueType {
  BrokenLink = 'broken_link',
  OrphanPage = 'orphan_page'
}
function handle(type: IssueType) { /* ... */ }
```

### Right

```ts
type IssueType = 'broken_link' | 'orphan_page'
function handle(type: IssueType) { /* ... */ }

// 需要值集合时
const ISSUE_TYPES = ['broken_link', 'orphan_page'] as const
type IssueType = typeof ISSUE_TYPES[number]
```

---

*End of examples*