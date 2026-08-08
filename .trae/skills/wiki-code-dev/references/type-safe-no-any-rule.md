# Rule Catalog — 类型安全：禁止 `as any` 绕过 (CODING-TYPE-SAFE-NO-ANY)

通用编码规范：禁止用 `as any`（以及 `as unknown as`、非断言性的 `!`）绕过 TypeScript 类型检查来"消红"。类型不匹配时须用正确类型——优先从源码提取类型（如 Fastify 的 `InjectOptions['method']`、后端 `HTTPMethods`）、用类型守卫 / 类型断言收窄、或修源类型。仅在迁移期代码（明确标注 `@migration`）可临时放行。本规则是后端审查条目 `wiki-backend-code-review` BR-078 与前端 `wiki-frontend-code-review` FR-026 / type-safety-rule 的泛化上位规范。

> 复盘来源：`index.ts` 把 `request.method as any` 传给需要 `HTTPMethods` 的签名，掩盖了实际的 method 类型来源；应改为 `InjectOptions['method']`（从 Fastify 类型推断）。`as any` 会关掉类型检查，让 method 拼接到未收窄的联合类型，重构时无法被编译器捕获。

## Scope

- Covers: 任何 TypeScript 中"为消类型错误而强转"的写法（`as any` / `as unknown as` / `value!` 非空断言绕过）。
- Does NOT cover: 与无类型第三方库边界用 `unknown` 接收后立刻断言（允许，但须局部收窄）；迁移期代码（须 `@migration` 标注）。

## Rules

### CODING-TYPE-SAFE-NO-ANY-1: 优先提取真实类型而非 `as any`

IsUrgent: True（严重）
Category: 类型安全

#### Description

类型来源不明时，从被消费方的类型推断（如 `type Method = InjectOptions['method']`、`import type { HTTPMethods }`），或写类型守卫 / 判别联合收窄，禁止 `as any` 把值变成无类型黑洞。

#### Suggested Fix

```ts
// ❌ 绕过类型
app.inject({ method: request.method as any, url: '/x' })
// ✅ 提取真实类型
import type { InjectOptions } from 'fastify'
const method = request.method as InjectOptions['method']
app.inject({ method, url: '/x' })
```

### CODING-TYPE-SAFE-NO-ANY-2: `as any` 仅限迁移期且须标注

IsUrgent: False（建议级）
Category: 类型安全

#### Description

确有第三方无类型边界时，用 `unknown` 接收 + 局部断言；历史迁移代码若必须 `as any`，须加 `// @migration` 注释并限定作用域，禁止在常驻业务路径长期使用。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `type_safe_no_any.enabled` | `true` | 启用本组规则（CODING-TYPE-SAFE-NO-ANY） |
| `type_safe_no_any.forbidden_patterns` | `as any, as unknown as, as any as` | 禁止的绕过写法 |
| `type_safe_no_any.allowed_in` | `@migration` | 允许放行的标注（须注释标记） |
| `type_safe_no_any.proper_type_ref` | `InjectOptions['method']` | 推荐的类型提取示例（Fastify method） |
| `type_safe_no_any.severity` | `critical` | 常驻业务路径 `as any` 绕过违规级别 |
