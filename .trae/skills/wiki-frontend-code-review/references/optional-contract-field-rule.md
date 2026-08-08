# Rule Catalog — Optional Contract Field Sync (Frontend Non-Consumption)

可选契约字段同步审查规则：后端在 API 契约（如 `CompileInput`）新增可选字段（如 `originalName?`，仅供后端内部兜底使用）时，前端 `types.ts` 对应 interface 须在同一变更中声明该字段为可选；且前端若不消费该内部字段，不得对其做必填访问或依赖其存在而分支，确保契约演进（字段缺失 / 新增）均不破坏前端逻辑。本规则扩展 type-sync-frontend-rule.md（TS-1）与 type-sync-done-event-rule.md（FR-062）的"加法 + 可选"原则，聚焦"前端不消费的可选字段"这一特殊子场景。

> 复盘来源：后端 `CompileInput` 新增 `originalName?` 可选字段用于落盘文件名兜底（`?? basename`），前端 `types.ts` interface 未消费该内部字段。评审关注点：前端须在 `types.ts` 同步声明可选字段以维持契约清晰、且不得因该字段存在/缺失而崩溃（禁止 `field!` / `as` 强转 / 分支依赖）；后端用 `??` 兜底确保字段恒有值（对应后端 BR-069-4 / BR-026）。

## Scope
- Covers: 后端在 API 契约（如编译/查询请求体 `CompileInput` / `QueryInput`）新增可选字段、且前端不消费该内部字段时，前端 `types.ts` 的同步声明与无破坏校验。
- Does NOT cover: 前端独立新增类型（type-safety-rule.md）；后端必填字段缺失导致的前端崩溃（属 FR-062 非加法范畴）；GraphQL / tRPC 自动生成类型。

## Rules

### FR-066-1: 后端新增可选契约字段，前端 types.ts interface 须同一变更声明可选

IsUrgent: False（建议级）
Category: Type Sync (Optional Contract)

#### Description

后端在任一 API 契约（如编译请求的 `CompileInput`）新增可选字段（`field?: T`，仅后端内部使用）时，前端 `types.ts` 中对应的 `export interface` 必须在**同一 PR / 同一变更**中同步声明该字段为可选。即使前端不消费该字段，同步声明可维持契约清晰、避免未来字段演进时前后端类型漂移。未声明不会导致运行时崩溃（结构化类型对多余属性宽松），但会造成契约文档缺失、后续开发者误判字段可用性。

#### Suggested Fix

```ts
// 后端 CompileInput 新增 originalName?（仅供后端文件名兜底）
// ✅ 同一 PR 中前端 types.ts 同步声明可选
export interface CompileInput {
  source: string
  // ...既有字段
  originalName?: string   // 新增：后端内部文件名兜底，前端不消费
}
```

> **示例代码**: 见 type-sync-frontend-rule.md（TS-1）与 type-sync-done-event-rule.md（FR-062）示例。

### FR-066-2: 前端不消费的可选字段，禁止必填访问或依赖存在而分支

IsUrgent: True
Category: Type Sync (Optional Contract)

#### Description

若前端确实不消费该后端内部可选字段（如 `originalName`），前端代码中**禁止**对该字段做必填访问或依赖其存在而分支：`field!` 非空断言、`as T` 强转、或直接以 `if (data.field)` 作为关键分支条件导致字段缺失时逻辑错位。字段由后端保证（运行时 `??` 兜底），前端无需感知其存在与否；正确做法是前端按自身契约独立访问它实际消费的字段，绝不在前端引入对该内部字段的强依赖。

#### Suggested Fix

```ts
// ❌ 错误：前端对不消费的内部字段做必填访问 / 分支依赖
const name = input.originalName!          // 缺失即崩溃
if (input.originalName) { /* 关键分支 */ } // 字段存在性不该驱动前端逻辑

// ✅ 正确：前端只访问自身契约字段，内部字段可有可无
const source = input.source
// originalName 由后端兜底，前端不引用
```

> **示例代码**: 见 type-safety-rule.md（`as` / `!` 强转审查）。

### FR-066-3: 后端可选字段须运行时兜底；跨文件核对字段名/类型/可选性一致

IsUrgent: False（建议级）
Category: Type Sync (Optional Contract)

#### Description

后端对该可选字段须在落盘/使用前提供运行时兜底默认值（如 `input.originalName ?? basename(input.source)`），确保字段恒有值、不因 `undefined` 产生脏数据。跨文件评审时，须核对前端 `types.ts` 字段名 / 类型 / 可选性与后端 `api/src/types.ts` 完全一致（字段名拼写、是否为 `?` 可选、类型是否匹配）；不一致时归入 FR-062 排查路径。

#### Suggested Fix

```ts
// 后端（ts）：运行时兜底，前端无需感知
const displayName = input.originalName ?? path.basename(input.source)
```

> **示例代码**: 见 type-sync-frontend-rule.md（TS-1）"前后端类型一致"段。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `optional_contract_field_frontend.enabled` | `true` | 启用本组规则（FR-066，扩展 TS-1 / FR-062） |
| `optional_contract_field_frontend.severity_br066_1` | `suggestion` | FR-066-1 未同步声明可选字段违规级别（契约清晰性，非运行时阻断） |
| `optional_contract_field_frontend.severity_br066_2` | `critical` | FR-066-2 对不消费字段做必填访问/分支依赖违规级别 |
| `optional_contract_field_frontend.severity_br066_3` | `suggestion` | FR-066-3 后端缺运行时兜底 / 跨文件字段不一致违规级别 |
| `optional_contract_field_frontend.backend_types_path` | `api/src/types.ts` | 后端 types 路径 |
| `optional_contract_field_frontend.frontend_types_path` | `frontend/src/types.ts` | 前端 types 路径 |
| `optional_contract_field_frontend.ignored_unconsumed_internal_fields` | `originalName` | 后端专属、前端不消费的可选字段清单（逗号分隔）；这些字段在前端 types.ts 须可选且前端禁止强依赖 |
| `optional_contract_field_frontend.watch_request_bodies` | `CompileInput,QueryInput` | 重点关注的 API 请求体 interface 名 |
