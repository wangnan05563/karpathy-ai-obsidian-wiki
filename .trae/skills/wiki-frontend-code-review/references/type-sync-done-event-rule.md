# Rule Catalog — Type Sync: SSE `done` Event Field Addition

前后端类型同步（SSE `done` 事件字段新增）审查规则：后端在 API 响应 / SSE 事件中新增字段时，前端对应 `types.ts` interface 必须在同一变更中更新。本规则扩展 type-sync-frontend-rule.md（TS-1）。

> 复盘来源：后端 `done` 事件新增 `governor` + `threadId` 两个字段后，前端 `types.ts` 的 `DoneEvent` interface 未及时同步，导致前端消费 `event.data` 时这两个字段为 `undefined`（或触发类型不一致）。新增字段须"同 PR 同步 + 加法可选"，避免破坏既有前端逻辑。

## Scope
- Covers: 后端在 API 响应 / SSE 事件（如 `done` 事件）新增字段时，前端 `types.ts` 对应 interface 的同步更新。
- Does NOT cover: 前端独立的类型设计（type-safety-rule.md）；GraphQL / tRPC 自动生成类型的同步。

## Rules

### FR-062-1: 后端事件/响应新增字段，前端 types.ts interface 须同一变更同步

IsUrgent: True
Category: Type Sync (Event)

#### Description

后端在任一 API 响应或 SSE 事件（含 `done` / `result` / `progress` 等）新增字段时，前端 `types.ts` 中对应的 `export interface`（如 `DoneEvent` / `QueryResult`）必须在**同一 PR / 同一变更**中更新字段名与类型。前端消费 `JSON.parse(event.data)` 后直接按 interface 访问新字段；未同步会导致字段为 `undefined` 或 TS 报错。

#### Suggested Fix

```ts
// 后端 SSE done 事件新增 governor + threadId
// ✅ 同一 PR 中前端 types.ts 同步
export interface DoneEvent {
  type: 'done'
  // ...既有字段
  governor?: string      // 新增：后端 Governor 标识
  threadId?: string      // 新增：线程 ID
}
```

> **示例代码**: 见 type-sync-frontend-rule.md（TS-1）示例。

### FR-062-2: 新增字段须加法且可选（Additive + Optional）

IsUrgent: True
Category: Type Sync (Event)

#### Description

SSE / API 契约演进须向后兼容：新增字段必须是**加法（additive）**且**可选（`?`）**。既不允许删除 / 重命名字段（破坏旧前端），也不允许把既有字段改为必填（迫使旧前端报错）。评审时确认：新增字段带 `?`，且未改动既有字段的必填性。

#### Suggested Fix

```ts
// ❌ 错误：把既有字段改必填 + 删除字段，破坏旧前端
export interface DoneEvent {
  type: 'done'
  governor: string   // 旧前端无此数据 → 运行时 undefined；且删了旧字段
}

// ✅ 正确：加法 + 可选
export interface DoneEvent {
  type: 'done'
  governor?: string  // 新增，可选
  threadId?: string  // 新增，可选
}
```

> **示例代码**: 见 type-sync-frontend-rule.md（TS-1）"ignore_optional_marker" 段。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `type_sync_done_event_frontend.enabled` | `true` | 启用本组规则（FR-062，扩展 TS-1） |
| `type_sync_done_event_frontend.severity_br062_1` | `critical` | FR-062-1 未同 PR 同步 interface 违规级别 |
| `type_sync_done_event_frontend.severity_br062_2` | `critical` | FR-062-2 非加法/非可选违规级别 |
| `type_sync_done_event_frontend.backend_types_path` | `api/src/types.ts` | 后端 types 路径 |
| `type_sync_done_event_frontend.frontend_types_path` | `frontend/src/types.ts` | 前端 types 路径 |
| `type_sync_done_event_frontend.watch_event_types` | `done,result,progress,error` | 重点关注的 SSE 事件类型 |
| `type_sync_done_event_frontend.ignore_optional_marker` | `true` | 忽略 `?` 可选标记差异 |
