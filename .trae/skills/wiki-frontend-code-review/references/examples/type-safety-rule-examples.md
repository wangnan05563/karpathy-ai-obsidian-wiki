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

## reactive 对象属性访问必须在类型定义范围内

### Wrong

```ts
import { reactive } from 'vue'

// 表单 reactive 只声明了 before / keepDays
const form = reactive({
  before: '',
  keepDays: 7
})

// ❌ Wrong：showDays 是卡片元数据字段，不在 form 上，TS 报错
//   Property 'showDays' does not exist on type '{ before: string; keepDays: number }'
const maxDays = form.showDays
```

### Right

```ts
import { reactive, ref } from 'vue'

// 表单字段用 interface 显式声明
interface CleanForm {
  before: string
  keepDays: number
}
const form = reactive<CleanForm>({ before: '', keepDays: 7 })

// 卡片元数据独立存储，不混入表单
interface CardMeta { key: string; showDays: number; label: string }
const cardMeta = ref<CardMeta[]>([
  { key: 'expired', showDays: 30, label: '过期会话' }
])

// ✅ Right：从元数据用 find 查找，而非挂到 form 上
const meta = cardMeta.value.find(c => c.key === 'expired')
const maxDays = meta?.showDays ?? 7
```

---

## unused imports 必须删除（strict 模式下报错）

### Wrong

```ts
// ❌ Wrong：重构后遗留未使用 import，tsconfig noUnusedLocals 下 TS6133 报错
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCleanupStore } from '@/stores/cleanup'
import type { CleanResult } from '@/types/cleanup'

// 实际只用 ref，其他 import 全部未使用
const loading = ref(false)
// pnpm build 直接失败：error TS6133: 'reactive' is declared but its value is never read.
```

### Right

```ts
// ✅ Right：仅保留实际使用的 import
import { ref } from 'vue'

const loading = ref(false)
```

```ts
// ✅ Right：必须保留但暂时未用的变量用 _ 前缀，TS 跳过检查
function handleSubmit(_event: Event, key: string) {
  // _event 不会触发 TS6133，key 正常使用
  console.log(key)
}
```

---

## 联合类型窄化失败时用 as 断言或 type guard

### Wrong

```ts
type FormItem = { key: string; before: string } | { key: string; keepDays: number }
const record: Record<string, FormItem> = {
  expired: { key: 'expired', before: '2026-01-01' }
}

// ❌ Wrong：通过索引访问 record[key]，TS 合并所有分支类型，无法窄化
function getBefore(key: string): string {
  const item = record[key]
  // Property 'before' does not exist on type 'FormItem'
  return item.before
}
```

```ts
// ❌ Wrong：用 as any 绕过，丢失类型保护
function getBefore(key: string): string {
  return (record[key] as any).before
}
```

### Right

```ts
// ✅ Right 1：as 断言到具体分支
function getBefore(key: string): string | undefined {
  const item = record[key] as { key: string; before: string }
  return item.before
}

// ✅ Right 2：type guard 函数，更安全
interface ExpiringForm { key: string; before: string }
function isExpiringForm(x: FormItem): x is ExpiringForm {
  return 'before' in x
}
function getBefore(key: string): string | undefined {
  const item = record[key]
  if (isExpiringForm(item)) {
    // 此处 item 已窄化为 ExpiringForm，访问 before 安全
    return item.before
  }
  return undefined
}
```

---

*End of examples*