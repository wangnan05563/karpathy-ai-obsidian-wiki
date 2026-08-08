# 类型安全禁止 `as any` 绕过（BR-078）

> 复盘来源：`index.ts` 把 `request.method as any` 传给需要 `HTTPMethods` 的签名，掩盖了实际的 method 类型来源；应改为 `InjectOptions['method']`（从 Fastify 类型推断）。对应 wiki-code-dev CODING-TYPE-SAFE-NO-ANY（前端 FR-026 / type-safety-rule 的泛化上位规范）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"type_safe_no_any"章节读取，禁止在本规则文件硬编码绕过写法。

## Trigger Keywords
as any, as unknown as, !., 非空断言, InjectOptions, HTTPMethods, request.method, 类型绕过, @migration

## Rules

### BR-078-1: 优先提取真实类型而非 `as any`

- **Severity**: critical
- **Description**: 类型来源不明时，从被消费方的类型推断（如 `type Method = InjectOptions['method']`、`import type { HTTPMethods }`），或写类型守卫 / 判别联合收窄，禁止 `as any` 把值变成无类型黑洞。
- **Suggested fix**:
```typescript
// ❌ 绕过类型
app.inject({ method: request.method as any, url: '/x' })
// ✅ 提取真实类型
import type { InjectOptions } from 'fastify'
const method = request.method as InjectOptions['method']
app.inject({ method, url: '/x' })
```

### BR-078-2: `as any` 仅限迁移期且须标注

- **Severity**: suggestion
- **Description**: 确有第三方无类型边界时，用 `unknown` 接收 + 局部断言；历史迁移代码若必须 `as any`，须加 `// @migration` 注释并限定作用域，禁止在常驻业务路径长期使用。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `type_safe_no_any.enabled` | `true` | 是否启用本规则 |
| `type_safe_no_any.forbidden_patterns` | `as any, as unknown as, as any as` | 禁止的绕过写法 |
| `type_safe_no_any.allowed_in` | `@migration` | 允许放行的标注 |
| `type_safe_no_any.proper_type_ref` | `InjectOptions['method']` | 推荐的类型提取示例 |
| `type_safe_no_any.severity` | `critical` | 常驻业务路径 `as any` 绕过违规级别 |

## 检查方式

1. Grep 检索 `type_safe_no_any.forbidden_patterns` 在 `api/src/**/*.ts` 的命中。
2. 命中但无 `type_safe_no_any.allowed_in` 标注且位于常驻业务路径 → BR-078-1 违规。
3. 命中且标注 `@migration` 但作用域超出单函数 / 长期留存 → BR-078-2 违规。

## 适配新项目

- **不同后端框架**：把 `InjectOptions['method']` 替换为对应框架的请求方法类型（如 Express 的 `Method`）；规则核心"禁止 `as any` 绕过"不变。
- **前端**：见 wiki-frontend-code-review FR-026 / type-safety-rule（已覆盖 `as any` / `!`）。
