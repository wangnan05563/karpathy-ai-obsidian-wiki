# Rule Catalog - Type Sync (Frontend-Backend)

## Scope
- Covers: 全栈 TypeScript 项目中后端 `types.ts` 新增 `interface` 时在前端 `types.ts` 的同步守卫、字段名/字段类型一致性校验。
- Does NOT cover: 前端独立的类型设计（type-safety-rule.md）、运行时数据结构校验（type-safety-rule.md SSE 类型守卫段）、GraphQL / tRPC / OpenAPI 自动生成类型的同步（由代码生成工具保证）。

> 所有可配置参数（后端 types 路径、前端 types 路径、需同步的接口名清单等）集中定义在 [config/review-config.md](../config/review-config.md) 的"前后端类型同步审查参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### TS-1: 后端 types.ts 新增 interface 必须在前端 types.ts 同步对应类型

IsUrgent: True
Category: Type Sync

### Description

全栈 TypeScript 项目中，后端 `types.ts` 与前端 `types.ts` 通常通过手动维护的双向约定保持一致。后端新增 `interface`（如 `TunnelConfig`、`AccountConfig` 等配置接口）时，必须在前端 `types.ts` 同步定义同名的 `interface`，且字段名、字段类型必须逐一对应。

复盘 TunnelConfig 时发现：后端 `api/src/types.ts` 新增了 `TunnelConfig` 接口，前端 `src/types.ts` 未同步，导致：
- 前端调用 `/api/tunnel/config` 的请求函数返回 `any` 或 `unknown`，丢失类型提示。
- 前端表单 reactive 对象的字段类型与后端响应不匹配，运行时静默丢字段。
- IDE 跳转失败，重构后端字段时前端无类型错误提示，遗漏修改。

### Judgment Logic

1. 读取配置 `backend_types_path` 指定的后端 types 文件，提取所有 `export interface Foo { ... }` 定义，得到接口集合 `I_backend = { name, fields[] }`。
2. 读取配置 `frontend_types_path` 指定的前端 types 文件，提取所有 `export interface` 定义，得到 `I_frontend`。
3. 按以下规则比对：
   - 若配置 `sync_interfaces` 非空，则仅检查清单中的接口；否则检查全部接口。
   - 对每个需同步的接口 `I`：
     - 前端不存在同名接口 → 告警"前端缺失接口定义"。
     - 前端存在但字段名不一致（缺失/多余/拼写差异）→ 告警"字段不一致"，列出差异字段。
     - 前端存在但字段类型不一致（如后端 `string` 前端 `number`、后端 `string | null` 前端 `string`）→ 告警"字段类型不一致"，列出差异。
4. 命中以上任一差异即输出告警，给出后端定义作为同步基准。

### Applicable Scenarios

- 全栈 TypeScript 项目（后端 Node.js / Deno / Bun + 前端 Vue / React / Svelte）。
- 前后端通过手动维护的 `types.ts` 文件约定共享类型。
- REST API + JSON 数据交换，前端 fetch 后直接断言为某 interface。

### Non-Applicable Scenarios

- 后端独立运行无前端（如纯 API 服务、CLI 工具）。
- GraphQL / tRPC / OpenAPI Generator / json-schema-to-typescript 等自动生成前端类型的方案（由代码生成工具保证一致性，重复维护反而产生冲突）。
- 后端使用非 TypeScript 语言（如 Python / Go / Java），前端类型由 schema 文件生成。

### Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `backend_types_path` | `../api/src/types.ts` | 后端 types 文件路径（相对前端项目根） |
| `frontend_types_path` | `src/types.ts` | 前端 types 文件路径 |
| `sync_interfaces` | `[]` | 需同步的接口名清单；留空表示全部 interface 都需同步 |
| `ignore_optional_marker` | `true` | 是否忽略 `?` 可选标记差异（后端必填前端可选视为兼容） |

### Example

```ts
// 后端 api/src/types.ts
export interface TunnelConfig {
  authtoken: string
  region: string
  enabled: boolean
  subdomain?: string
}
```

```ts
// ❌ 前端 src/types.ts 未同步
// 调用 api.getTunnelConfig() 返回 unknown，表单 reactive 无类型保护
const form = reactive({
  authtoken: '',
  region: '',
  enabled: false
})
```

```ts
// ✅ 前端 src/types.ts 同步定义
export interface TunnelConfig {
  authtoken: string
  region: string
  enabled: boolean
  subdomain?: string
}

// 请求函数显式标注返回类型
export async function getTunnelConfig(): Promise<TunnelConfig> {
  const res = await fetch('/api/tunnel/config')
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<TunnelConfig>
}
```

### Checklist

- [ ] 后端 `types.ts` 中所有 `export interface` 在前端 `types.ts` 都有同名定义
- [ ] 同步接口的字段名逐一对应（无缺失、无多余、无拼写差异）
- [ ] 同步接口的字段类型逐一对应（`string`/`number`/`boolean`/联合类型一致）
- [ ] 前端调用相关 API 的请求函数显式标注返回类型为对应 interface
