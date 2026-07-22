# 混合类型运行时分流（FR-028）

> 复盘来源：将后端返回的 `T` 旧响应升级为 `T | U` 联合类型（如旧版 `{ ok: boolean }` 升级为 `{ ok: true } | { ok: false, error: string }`）时，开发者直接用 `as unknown as U` / `as any` 强转，结果旧响应（T）在运行时缺少 U 的字段，渲染分支访问到 `undefined` 属性，UI 呈现 NaN 与空白卡片。
> 所有可变参数从 config/review-config.md 的 `mixed_type_dispatch_frontend` 字段读取。

## 规则

### FR-028-1：类型升级 T→U 时必须用 `isXxx` 类型守卫 + 运行时分流

当后端接口返回的响应类型从单形态 `T` 升级为联合类型 `T | U`（或 `T | U | V`）时，前端消费代码必须满足以下要求：

1. **类型守卫集中化**：在 `mixed_type_dispatch_frontend.typeguard_module` 指定的模块中导出独立的 `isXxx` 函数（如 `isSuccessResponse`、`isErrorPayload`），使用 `x is U` 谓词签名，禁止把守卫逻辑散落在每个调用点。
2. **运行时分流**：消费联合类型的代码必须用 `typeof` / `in` / `isXxx` 守卫在运行时区分分支，禁止依赖字段在某个分支恰好存在。
3. **分支穷尽性**：联合类型的所有成员必须有对应处理分支（即使 `default` 抛错或 `console.warn`），禁止"默认走 T 分支"——因为升级后旧客户端收到的可能就是新形态 U。

### FR-028-2：禁止 `as any` / `as unknown as U` 跨形态强转

跨形态类型转换（`as unknown as U`、`as any`）会跳过 TypeScript 的结构检查，掩盖运行时缺字段。下列转换属于禁止项：

- `response as any as ErrorResponse`
- `response as unknown as { ok: false; error: string }`
- `data as SuccessResponse`（当 `data` 实际类型为联合时）

合法的转换：

- 联合类型收窄：通过 `isXxx` 守卫后 TypeScript 自动收窄，无需断言。
- 同形态字段扩展：`{ a: 1 } as { a: number; b?: number }`（结构兼容，仅扩展可选字段）。
- 字面量→更宽联合：`'foo' as 'foo' | 'bar'`（值兼容）。

### FR-028-3：联合类型分支必须有测试覆盖

每个联合成员至少一条单元测试用例，验证运行时分流走对分支。`mixed_type_dispatch_frontend.required_test_per_member` 默认 `true`。

## 适用场景

- 后端响应从单形态升级为联合形态（成功/失败分支、旧版/新版 schema 共存）。
- 消息总线事件多态（如 `ChatMessage | SystemMessage | ErrorMessage`）。
- 第三方库返回联合类型（如 `MutationResult` 的 `loading | error | success`）。

## 不适用场景

- 类型守卫**已经存在**且调用方正确使用的代码 —— 不重复审查。
- 后端响应始终为单形态且不会升级（如纯静态枚举）。
- 类型转换属于合法结构兼容场景（见 FR-028-2 末尾）。

## 检查流程

```
[开始] 评审目标文件含 T | U 联合类型消费代码
  │
  ▼
[1] 是否存在跨形态强转？(as any / as unknown as)
  │  └─ 是 → 标记 Urgent（FR-028-2）
  │
  ▼ 否
[2] 联合类型消费点是否用 isXxx / typeof / in 守卫分流？
  │  └─ 否（默认走 T 分支） → 标记 Urgent（FR-028-1）
  │
  ▼ 是
[3] 守卫是否集中到 typeguard_module？
  │  └─ 否（散落在每个调用点） → 标记建议
  │
  ▼ 是
[4] 联合类型每个成员是否都有处理分支？
  │  └─ 否（缺 U 分支） → 标记 Urgent（FR-028-1）
  │
  ▼ 是
[5] 每个成员是否有对应单元测试？
  │  └─ 否 → 标记 Urgent（FR-028-3）
  │
  ▼
[结束]
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `mixed_type_dispatch_frontend.forbidden_casts` | `as any, as unknown as` | 禁止的跨形态强转关键字（逗号分隔） |
| `mixed_type_dispatch_frontend.typeguard_module` | `frontend/src/types/guards.ts` | 集中导出 `isXxx` 类型守卫的模块路径 |
| `mixed_type_dispatch_frontend.required_dispatch_keywords` | `typeof, in, isXxx` | 允许的运行时分流方式（任一即可） |
| `mixed_type_dispatch_frontend.required_test_per_member` | `true` | 联合类型每个成员必须有测试覆盖 |
| `mixed_type_dispatch_frontend.exhaustive_branch_required` | `true` | 消费联合类型的代码必须穷尽所有分支 |
| `mixed_type_dispatch_frontend.allowed_structural_cast` | `extends, optional field extension` | 允许的结构兼容强转场景（不视为违规） |

## 检查方式

1. 用 `mixed_type_dispatch_frontend.forbidden_casts` 扫描 PR diff 中的 `as any` / `as unknown as`。
2. 对每处联合类型消费点（`response: T | U` 的 `.then` / `match` / `switch`），核对是否使用 `required_dispatch_keywords` 中至少一种方式分流。
3. 检查 `typeguard_module` 是否导出对应 `isXxx` 函数；若散落在调用点，标记建议集中化。
4. 用 `exhaustive_branch_required` 检查 switch/if 链是否覆盖联合类型的全部成员（缺失成员即违规）。
5. 在测试目录中按联合成员名检索测试用例，缺失即标记 Urgent。

## 正确示例

```ts
// ✅ 集中导出类型守卫（frontend/src/types/guards.ts）
import type { ChatMessage, SystemMessage, ErrorMessage } from '@/types/messages'

export function isChatMessage(m: { type: string }): m is ChatMessage {
  return m.type === 'chat'
}

export function isSystemMessage(m: { type: string }): m is SystemMessage {
  return m.type === 'system'
}

export function isErrorMessage(m: { type: string }): m is ErrorMessage {
  return m.type === 'error'
}

// ✅ 消费点用守卫运行时分流，分支穷尽
import { isChatMessage, isSystemMessage, isErrorMessage } from '@/types/guards'

function renderMessage(msg: ChatMessage | SystemMessage | ErrorMessage) {
  if (isChatMessage(msg)) {
    // TS 自动收窄为 ChatMessage
    return `<div class="chat">${msg.content}</div>`
  }
  if (isSystemMessage(msg)) {
    return `<div class="system">${msg.notice}</div>`
  }
  if (isErrorMessage(msg)) {
    return `<div class="error">${msg.error}</div>`
  }
  // 穷尽性兜底：未来新增类型时 TS 会在此报错
  const _exhaustive: never = msg
  return ''
}

// ✅ 用 in 操作符做后备分流（无 isXxx 时）
function isOk(r: { ok: boolean } | { ok: false; error: string }): r is { ok: true } {
  return r.ok === true
}
```

## 错误示例

```ts
// ❌ 跨形态强转：跳过结构检查，运行时缺字段
import type { ChatMessage, ErrorMessage } from '@/types/messages'

function getMessage(): ChatMessage | ErrorMessage { /* ... */ }

const msg = getMessage()
// ❌ as any 强转后访问 .content，若实际是 ErrorMessage 则得到 undefined
const content = (msg as any).content

// ❌ as unknown as 跨形态强转
const chatMsg = msg as unknown as ChatMessage
console.log(chatMsg.content.toUpperCase())  // 运行时崩溃：undefined.toUpperCase

// ❌ 默认走 T 分支，未穷尽联合
function renderMessage(msg: ChatMessage | ErrorMessage) {
  // 没有守卫直接访问 .content， ErrorMessage 时为 undefined
  return `<div>${msg.content}</div>`
}

// ❌ 守卫散落在调用点，未集中到 typeguard_module
function isChatMessage(m: any): m is ChatMessage {
  return m?.type === 'chat'
}
// 同样的逻辑在 5 个不同文件各写一遍
```

## 适配新项目

- **React / Next.js**：守卫模块路径可改为 `app/_types/guards.ts`（App Router）或 `src/types/guards.ts`；其余规则不变。
- **Vue 2**：用 `mapGetters` + `mapActions` 时仍建议把 `isXxx` 守卫抽到独立模块，调用方在 `computed` 中分流。
- **纯 JavaScript**：本规则降级为"运行时必须用 typeof/in 分流"，因为无类型守卫概念；`as any` 检查自动失效。
- **Monorepo / 共享类型包**：`typeguard_module` 路径改为 `packages/shared-types/guards.ts`，所有消费方从同一处导入守卫，避免重复实现。
