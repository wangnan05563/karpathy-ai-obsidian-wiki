# Rule Catalog — Strip Vue/Pinia Reactive Proxy Before IndexedDB Write (Frontend)

前端「IndexedDB 写入前剥离 Vue/Pinia 响应式代理」审查规则：凡将 store state ref / `reactive()` 对象经 `dbPut`/`saveUserConfig`/`idbPut`/`store.put` 写入 IndexedDB 的路径，写入前必须整树深拷贝剥离代理，否则 proxy 无法被 `structuredClone` 克隆 → `DataError: [object Array] could not be cloned` → 静默丢配置。所有参数从 `config/review-config.md` 读取，禁止硬编码。

> 复盘来源：`services/userConfig.ts` 的 `saveUserConfig` 直接把 Pinia store 持有的 `settings`（reactive ref）传给 `dbPut`，导致四类本地配置（AI / 搜索 / 工具 / 输入框）写入即静默丢失。失败之所以静默，是因为写入发生在 IndexedDB 事务回调里，proxy 克隆失败时事务 abort，但外层 `try/catch` 只 `console.warn`，UI 又因 reactive state 已更新而"看似保存成功"——刷新页面数据全丢，且无任何报错可追。`toRaw()` 也救不了：它只剥掉**顶层**代理，嵌套的数组/对象仍是代理。

## Scope
- Covers: `frontend/src/services/**/*UserConfig*.ts`、`frontend/src/stores/**/*store*.ts`（将 store state 写入 IndexedDB 的 `dbPut` / `saveUserConfig` / `idbPut` / `store.put`），以及任何 `reactive()` 对象落盘路径。
- Does NOT cover：localStorage（API 是 `JSON.stringify` 序列化到字符串，不受代理影响）；纯服务端（无 Vue reactive）；写入值已是 `JSON.parse` 反序列化的 plain object；IndexedDB **读取**（`dbGet` 返回 plain，不需 clone）。

## Rules

### FR-081-1: IDB 写入前必须对 reactive 入参整树深拷贝

IsUrgent: True
Category: IDB Reactive Clone

#### Description

任何最终走到 `dbPut` / `idbPut` / `store.put` 的数据，若其源头是 Pinia store state ref 或 `reactive()` 对象，写入前必须整树深拷贝为 plain object。深拷贝须递归（嵌套数组/对象同为代理，浅拷贝不够）。否则 proxy 无法被 `structuredClone` 克隆，写入失败被静默吞掉 → 数据丢失（FR-081-1，Critical）。

```typescript
// ✅ 写入前深拷贝剥离代理
await dbPut(`usercfg::${kind}::${userId}`, clone(value));   // clone = JSON.parse(JSON.stringify(value))
// ❌ 直传 reactive 代理 → [object Array] could not be cloned，事务 abort，配置静默丢失
await dbPut(`usercfg::${kind}::${userId}`, value);
```

### FR-081-2: 禁止用 toRaw() 当深剥离

IsUrgent: True
Category: IDB Reactive Clone

#### Description

`toRaw()` 仅对**顶层** reactive 生效，无法递归剥离嵌套代理。嵌套的数组/对象仍是代理，克隆照样失败（FR-081-2，Critical）。

```typescript
// ❌ toRaw 只剥顶层，嵌套数组仍是代理 → 仍 [object Array] could not be cloned
await dbPut(key, toRaw(settings));
```

### FR-081-3: 禁止 structuredClone(reactiveObj)

IsUrgent: True
Category: IDB Reactive Clone

#### Description

`structuredClone` 本身也无法克隆代理（鸡生蛋问题），所以不能 `structuredClone(reactiveObj)`。唯一可靠做法是对整棵树做 `JSON.parse(JSON.stringify(x))` 或手写递归 `clone`（对含 `Date`/函数/`undefined` 的模型，改用 `toRaw` + 递归遍历）（FR-081-3，Critical）。

```typescript
// ❌ structuredClone 无法克隆代理
await dbPut(key, structuredClone(settings));
```

### FR-081-4: 封装函数内部统一 clone 防御

IsUrgent: False
Category: IDB Reactive Clone

#### Description

建议 `saveUserConfig` 等封装函数在**内部**统一对入参 `clone`，而非要求每个调用方自行 clone，形成防御纵深——即使调用方传入 reactive 对象也不会静默丢数据（FR-081-4，建议级）。同时写入失败须真正传播（而非仅 `console.warn` 静默吞错，见 wiki-code-dev CODING-CRITICAL-WRITE-NO-SWALLOW）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `idb_reactive_clone_frontend.enabled` | `true` | 启用本组规则（FR-081） |
| `idb_reactive_clone_frontend.scan_patterns` | `dbPut,saveUserConfig,idbPut,store.put,transactions.add` | 命中即须核对入参是否已深拷贝的 IndexedDB 写入点（逗号分隔） |
| `idb_reactive_clone_frontend.severity_clone_before_put` | `critical` | FR-081-1 直传 reactive 代理导致静默丢配置违规级别 |
| `idb_reactive_clone_frontend.severity_toraw` | `critical` | FR-081-2 用 toRaw() 当深剥离（嵌套代理仍失败）违规级别 |
| `idb_reactive_clone_frontend.severity_structured_clone` | `critical` | FR-081-3 structuredClone(reactiveObj)（代理无法被克隆）违规级别 |
| `idb_reactive_clone_frontend.severity_wrap_clone` | `suggestion` | FR-081-4 封装函数内部统一 clone 防御缺失违规级别 |
| `idb_reactive_clone_frontend.forbidden_unsafe_patterns` | `toRaw(,structuredClone(` | 命中即判违规的"伪剥离"写法 |
| `idb_reactive_clone_frontend.recommended_clone` | `JSON.parse(JSON.stringify(x))` | 推荐深拷贝范式（纯数据模型）；含 Date/函数/undefined 改用 toRaw+递归 |
