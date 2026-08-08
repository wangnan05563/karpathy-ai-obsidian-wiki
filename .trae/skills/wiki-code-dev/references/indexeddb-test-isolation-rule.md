# 隔离测试纪律规则（前端 IndexedDB / 后端模块态隔离）

**代码**：CODING-TEST-ISOLATION
**严重级别**：important（测试正确性，非生产运行时）

## 问题（Problem）

测试套件中多个用例共享同一持久化命名空间（如前端 IndexedDB `preferences` store 的 `usercfg::ai::guest`、后端模块级单例），会导致：

1. **用例间状态泄漏**：前一个用例写入的记录被后一个用例读到，断言偶发失败，表现为"本地单独跑过、CI 合入后 flaky"。
2. **`beforeEach(() => indexedDB.deleteDatabase(...))` 陷阱**：fake-indexeddb 持有 open connection（且 `chatDb` 模块级缓存连接）时，`deleteDatabase` 触发 `onblocked` 或静默超时，跨用例记录无法真正清掉，反而制造更隐蔽的泄漏。
3. **异步落盘断言竞态**：fake-indexeddb 的写是异步的，断言紧跟 `await dbPut(...)` 后立刻 `dbGet` 可能因事件循环未 flush 而读到旧值，产生假阴性。

真实事故：本项目的 `userConfig-isolation.test.ts` 初版用 `beforeEach(deleteDatabase)` + 默认 `guest` 用户，2 个用例偶发失败；改用**每用例唯一 userId 命名空间**后稳定通过（详见 [wiki-auto-testing testing-process-review.md Round 10](../../wiki-auto-testing/references/testing-process-review.md)）。

## 规则（Rule）

### R-1：隔离测试用唯一命名空间，绝不依赖 `deleteDatabase` 清理

前端隔离测试为每个用例生成**唯一 userId / 线程 id 命名空间**（如 `user-${Date.now()}-${rand}`），写不同 key，使记录天然不冲突。禁止在 `beforeEach` 调用 `indexeddb.deleteDatabase`（fake-indexeddb + 已开连接会 onblocked/泄漏）。

```typescript
// 反例：deleteDatabase 在 fake-indexeddb 下不可靠
beforeEach(() => { indexedDB.deleteDatabase('karpathy-wiki-chat'); });

// 正例：唯一命名空间隔离，不依赖删除
const uid = `user-${Date.now()}-${Math.random().toString(36).slice(2)}`;
await saveAiUserConfig(uid, {...});
const got = await loadAiUserConfig(uid);
expect(got.apiKey).toBe('...'); // 其他用例永远读不到本 uid 的数据
```

### R-2：异步落盘断言须多轮 flush

fake-indexeddb 写后读需让微任务/宏任务 flush。断言前循环若干轮 `await new Promise(r => setTimeout(r, 0))`（轮数从配置读取），避免读到未落盘的旧值。

```typescript
for (let i = 0; i < FLUSH_ROUNDS; i++) await new Promise(r => setTimeout(r, 0));
const got = await dbGet('preferences', key);
```

### R-3：后端测试隔离模块态，禁止跨用例共享可变单例

vitest 下模块级单例（Map/缓存/连接）默认跨用例复用。用例若改写共享单例须在每个用例 `beforeEach` 中重置（重建实例 / `vi.clearAllMocks()` / 重置模块注册表 `vi.resetModules()`），禁止依赖"上一条用例留下的状态"。

```typescript
beforeEach(() => { vi.clearAllMocks(); /* 必要时 resetModules() 重新 import */ });
```

## 适用 / 不适用

- **适用**：所有含持久化 / 全局状态的测试——前端 IndexedDB（fake-indexeddb）、localStorage、后端文件态 `FileStateStore`、模块级缓存、任何"先写后读"的断言。
- **不适用**：纯函数单测（无副作用、无共享状态）；只读不写的快照测试。

## 检查清单

- [ ] 隔离测试是否用唯一命名空间（userId / 线程 id），而非 `beforeEach(deleteDatabase)`（`test_isolation.frontend.namespaces_prefixes` 列出的前缀须唯一化）
- [ ] 是否出现 `forbidden_patterns` 中的 `indexedDB.deleteDatabase` / `deleteDatabase` 在 `beforeEach`（`test_isolation.frontend.forbidden_patterns`）
- [ ] 异步落盘断言是否多轮 `setTimeout(0)` flush（`test_isolation.frontend.flush_rounds`）
- [ ] 后端用例是否重置模块态 / mock，禁止跨用例共享可变单例（`test_isolation.backend.isolate_module_state`）

> 自动校验见 wiki-auto-testing `indexeddb_test_isolation_check`（参数 `namespace_prefixes` / `forbidden_patterns` / `flush_rounds` 与上式对齐）。
