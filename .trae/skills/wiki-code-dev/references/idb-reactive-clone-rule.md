# IndexedDB 写入前剥离 Vue/Pinia 响应式代理规则

**代码**：CODING-IDB-REACTIVE-CLONE
**严重级别**：critical

## 问题（Problem）

Vue 3 的 `reactive()` / `ref()` 返回的是 **Proxy 代理对象**，且 Vue 的响应式是**深层的**——嵌套的数组 / 对象也全是代理。`indexedDB` 在 `put`/`add` 时会用内部 `structuredClone` 序列化值。Proxy 无法被 `structuredClone` 克隆，会抛出 `DataError: [object Array] could not be cloned`（或 `[object Object] could not be cloned`）。

最隐蔽的点在于**失败是静默的**：写入发生在 IDB 事务回调里，proxy 克隆失败时事务 abort，但调用方（如 `saveUserConfig`）外层 `try/catch` 只 `console.warn`，UI 又因 reactive state 已更新而"看似保存成功"。结果——设置写入后界面正常，刷新页面数据全丢，且无任何报错可追。

真实踩坑：`userConfig.ts` 的 `saveUserConfig` 直接把 store 持有的 `settings`（reactive ref）传给 `dbPut`，导致四类本地配置（AI / 搜索 / 工具 / 输入框）写入即静默丢失。`toRaw()` 也救不了——它只剥掉**顶层**代理，嵌套的数组/对象仍是代理，克隆照样失败。

## 规则（Rule）

### R-1：凡是写 IndexedDB 的路径，写入前必须深拷贝剥离代理

任何最终走到 `dbPut` / `idbPut` / `store.put` / `transactions.add` 的数据，若其源头是 Pinia store state ref 或 `reactive()` 对象，**写入前必须整树深拷贝为 plain object**。深拷贝须递归（嵌套数组/对象同样为代理，浅拷贝不够）。

```typescript
// services/userConfig.ts — 写入前深拷贝剥离 Vue 代理
import { clone } from '@/utils/clone';

export async function saveUserConfig<T>(kind: string, userId: string, value: T): Promise<void> {
  // value 来自 Pinia store（reactive），必须深拷贝剥离代理后再落盘
  await dbPut(`usercfg::${kind}::${userId}`, clone(value));  // ← 关键：clone 而非直传
}

// utils/clone.ts — 递归深拷贝（JSON 回合对纯数据模型足够；含 undefined 的模型用 structuredClone 前先 toRaw 整树）
export function clone<T>(x: T): T {
  return JSON.parse(JSON.stringify(x));
}
```

### R-2：`toRaw()` 不足以处理嵌套代理，禁止当作深剥离

`toRaw()` 仅对**顶层** reactive 生效，无法递归剥离嵌套代理。`structuredClone` 本身也**无法克隆代理**（鸡生蛋问题），所以不能 `structuredClone(reactiveObj)`。唯一可靠做法是对整棵树做 `JSON.parse(JSON.stringify(x))` 或手写递归 `clone`（对含 `Date`/函数/`undefined` 的模型，改用 `toRaw` + 递归遍历，或 `structuredClone(toRaw(deep))`）。

```typescript
// ❌ 错误：toRaw 只剥顶层，嵌套数组仍是代理 → 仍 [object Array] could not be cloned
await dbPut(key, toRaw(settings));

// ❌ 错误：structuredClone 无法克隆代理
await dbPut(key, structuredClone(settings));

// ✅ 正确：整树深拷贝为 plain object
await dbPut(key, clone(settings));   // clone = JSON.parse(JSON.stringify())
```

### R-3：审查任何 IDB 写入路径都须核对"入参是否已被克隆"

凡出现 `idb_reactive_clone.scan_patterns`（如 `dbPut` / `saveUserConfig` / `idbPut` / `store.put`）的地方，其写入值若来自 store state ref / `reactive()`，必须确认上游已 `clone`（或写入值本身已是 `JSON.parse` 得到的 plain object）。缺 `clone` 即 critical 违规。

```typescript
// 审查要点：dbPut 的实参是否可能为 reactive 代理
dbPut(key, settings);              // ❌ settings 来自 store ref 未 clone
dbPut(key, clone(settings));       // ✅ 已剥离代理
dbPut(key, JSON.parse(rawText));   // ✅ 已是 plain object（反序列化结果）
```

## 适用 / 不适用

- **适用**：Vue 3 + Pinia + IndexedDB 项目，凡将 store state / `reactive()` 对象经 `dbPut`/`put`/`add` 写入 IDB 的路径；任何依赖 `structuredClone` 持久化的场景（跨窗口 `postMessage` 传代理、`BroadcastChannel` 传代理同理）。
- **不适用**：`localStorage`（API 是 `JSON.stringify` 序列化到字符串，不受代理影响，但注意 `JSON.stringify(reactiveObj)` 在序列化时也会因 getter 触发而产出 plain JSON，通常没问题）；纯服务端（无 Vue reactive）；写入值已是 `JSON.parse` 反序列化的 plain object；IndexedDB **读取**（`dbGet` 返回 plain，不需 clone）。

## 检查清单

- [ ] 所有 `idb_reactive_clone.scan_patterns` 命中的写入点（`dbPut` / `saveUserConfig` / `idbPut` / `store.put`），其入参若源自 store state ref / `reactive()`，是否经 `clone` 深拷贝
- [ ] 是否禁止用 `toRaw()` 当深剥离（嵌套代理仍会失败）
- [ ] 是否禁止 `structuredClone(reactiveObj)`（代理无法被克隆）
- [ ] 深拷贝是否递归（嵌套数组/对象同为代理，浅拷贝不够）
- [ ] `saveUserConfig` 等封装函数是否在内部统一 `clone`，而非要求每个调用方自行 clone（防御性）
- [ ] 写入失败时是否真正传播错误（而非仅 `console.warn` 静默吞错，见 CODING-CRITICAL-WRITE-NO-SWALLOW）
