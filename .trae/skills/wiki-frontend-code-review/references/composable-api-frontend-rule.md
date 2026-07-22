# Composable API 先读后用（FR-027）

> 复盘来源：诊断 Pinia store 状态异常时，开发者凭函数名推断 useXxx 的返回形状（"既然叫 useFooStore，应该返回 ref 而不是 reactive"），导致错误调用 ref.value 解构；又在排查阶段调用 `pinia._s.delete(id)` 与 `$dispose()` 重建 store 以"刷新状态"，结果污染了同一 store 在其他组件中的订阅、丢失已注册的副作用。
> 所有可变参数从 config/review-config.md 的 `composable_api_frontend` 字段读取。

## 规则

### FR-027-1：调用 `useXxx` 前必须读源码确认 API 形状

在新增对任意 `useXxx` / `defineStore` 返回值的使用前（包括 `useStore()`、`useRoute()`、`useRouter()`、自定义 composable），必须先打开其源码确认以下信息：

1. 返回值是 `ref` / `reactive` / `computed` / 普通对象。
2. 暴露的字段名与类型（state 字段是 `Ref<string>` 还是 `string`）。
3. action 是普通函数还是返回 Promise，是否有副作用（如发请求、写 localStorage）。
4. 是否需要在调用方传入参数（id、初始化选项）。
5. 是否需要在 `onBeforeUnmount` 中显式清理（订阅、watch、定时器）。

未读源码直接按"常见模式"调用属于违规，因为 composable 的返回形状因实现而异——`useStore()` 在 setup store 中返回带 `ref` 字段的对象，在 option store 中返回 reactive proxy，模板自动解包规则也不同。

### FR-027-2：诊断代码禁止 `$dispose` / `pinia._s.delete` 重建 store

排查 store 状态异常时，禁止用以下手段"强制重置"：

- `pinia._s.delete(id)`：删除 store 注册表条目，下次 `useStore()` 创建全新实例，丢失所有已注册的 watcher、订阅、持久化副作用。
- `store.$dispose()`：释放 store 与其响应式依赖，导致其他仍在使用该 store 的组件访问到已销毁的 reactive proxy。
- `store.$reset()`（option store 才有）：仅适用于"用户主动重置"的语义场景，不应用于诊断"为什么状态不对"——它只是把症状盖掉，根因（错误的 action 调用、订阅泄漏）依然存在。

诊断阶段应该：

1. 在 store 内部添加 `console.log` 或用 Vue DevTools 检查状态快照。
2. 用 `store.$subscribe` 临时监听变化定位写入来源。
3. 在调用方检查 `useStore()` 是否被重复调用（setup 中只能调一次）。

`$dispose` / `_s.delete` 只允许出现在**测试代码**中（见 `composable_api_frontend.diagnostic_allowlist_in_tests`），且必须配合 `setActivePinia(createPinia())` 重新创建实例。

## 适用场景

- Vue 3 Composition API 项目中调用任意 `useXxx`（自定义 composable / `useStore` / `useRoute` / `useRouter` / `useI18n` / `useHead` 等）。
- Pinia store 的状态诊断与排查。
- 新增组件引入新 store / composable 的 PR 评审。

## 不适用场景

- 框架内置 Hooks（React `useEffect` / `useMemo` 等）—— 走 React 专属规则。
- 仅引用类型（`import type { Foo }`），未实际调用 composable 的代码。
- 单元测试中创建隔离 store 实例（允许 `$dispose` / `_s.delete`）。

## 检查流程

```
[开始] PR 引入新 useXxx 调用 / store 诊断代码
  │
  ▼
[1] 读取被调用的 useXxx 源码
  │  └─ 未读源码 → 标记 Urgent（FR-027-1）
  │
  ▼ 已读源码
[2] 核对调用方代码与源码 API 形状
  │  └─ ref/reactive 误用 / 字段名错配 → 标记 Urgent
  │
  ▼ API 匹配
[3] 扫描诊断/重置相关代码
  │  ├─ pinia._s.delete / $dispose / $reset 用于"诊断重置" → 标记 Urgent（FR-027-2）
  │  └─ 仅在测试文件中且配 setActivePinia → 通过
  │
  ▼
[4] 检查 onBeforeUnmount 清理
  │  └─ composable 显式要求清理但调用方未清理 → 标记 Urgent
  │
  ▼
[结束]
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `composable_api_frontend.use_xxx_pattern` | `use[A-Z]\w*` | 标识 composable 调用的正则 |
| `composable_api_frontend.store_lifecycle_forbidden` | `pinia._s.delete, $dispose, $reset` | 诊断代码禁止的 store 生命周期 API（逗号分隔） |
| `composable_api_frontend.diagnostic_allowlist_in_tests` | `*.spec.ts, *.test.ts` | 允许使用上述 API 的测试文件 glob |
| `composable_api_frontend.must_read_source_before_use` | `true` | 调用 useXxx 前必须读源码 |
| `composable_api_frontend.required_source_read_evidence` | `false` | 是否要求 PR 描述中显式贴出源码片段（推荐开启） |
| `composable_api_frontend.cleanup_hooks_to_check` | `onBeforeUnmount, onScopeDispose` | 检查 composable 副作用清理的生命周期钩子 |

## 检查方式

1. 用 `composable_api_frontend.use_xxx_pattern` 扫描 PR diff 中的 `useXxx` 调用。
2. 对每个调用，要求 PR 作者在描述或评论中粘贴被调用 composable 的源码签名（`export function useXxx(): { ... }`）。
3. 核对调用方对返回字段的使用是否与签名一致（`ref.value` vs `reactive.field`）。
4. 用 `composable_api_frontend.store_lifecycle_forbidden` 关键字扫描 diff，命中且不在 `diagnostic_allowlist_in_tests` 文件中即标记 Urgent。
5. 检查 composable 文档中标注"需清理"的副作用，调用方是否在 `cleanup_hooks_to_check` 中配对清理。

## 正确示例

```ts
// ✅ 步骤 1：先读 useThemeStore 源码确认 API 形状
// frontend/src/stores/useThemeStore.ts
// export const useThemeStore = defineStore('theme', () => {
//   const current = ref<ThemeKey>('macaron')   // 注意：返回 Ref，调用方需 .value
//   const themes = reactive<ThemeKey[]>([])     // 注意：返回 reactive，调用方直接 .themes
//   function applyTheme(key: ThemeKey): Promise<void> { ... }
//   return { current, themes, applyTheme }
// })

// ✅ 步骤 2：调用方按源码签名正确使用
import { useThemeStore } from '@/stores/useThemeStore'
import { onBeforeUnmount } from 'vue'

const themeStore = useThemeStore()

// current 是 Ref，模板自动解包但脚本中需 .value
console.log('current theme:', themeStore.current.value)

// applyTheme 是 async，需 await
await themeStore.applyTheme('enterprise')

// ✅ 诊断状态异常时用 $subscribe 而非 $dispose
themeStore.$subscribe((mutation, state) => {
  console.log('theme changed:', mutation.type, state.current)
})

onBeforeUnmount(() => {
  // ✅ 显式取消订阅（如有 watch / $subscribe）
})
```

## 错误示例

```ts
// ❌ 未读源码，把 ref 当 reactive 用
import { useThemeStore } from '@/stores/useThemeStore'

const themeStore = useThemeStore()
// ❌ current 是 Ref，在脚本中直接访问得到 Ref 对象，比较永远不等
if (themeStore.current === 'macaron') { ... }

// ❌ 诊断阶段用 _s.delete "重置" store
import { pinia } from '@/main'
function debugReset() {
  pinia._s.delete('theme')          // 丢失所有订阅与持久化副作用
  const fresh = useThemeStore()      // 创建全新实例，其他组件仍在用旧引用
  console.log(fresh.current)         // 看似"重置成功"，实则根因未查
}

// ❌ 用 $dispose 释放后继续访问
function debugDispose() {
  themeStore.$dispose()
  console.log(themeStore.current)    // 访问已销毁的 reactive proxy，行为未定义
}
```

## 适配新项目

- **React / Next.js**：`useXxx` 同样要求先读源码（Hooks 返回值形状更易混淆，因 `useState` 返回 `[value, setter]` 元组）；诊断阶段禁止在 `useEffect` 中调用 `reactDom.unmountComponentAtNode` 强制卸载来"重置状态"。
- **Vue 2**：用 `mapState` / `mapActions` 时本规则降级为"调用前先读 Vuex store 字段定义"；`$dispose` / `_s.delete` 不存在，规则自动满足。
- **纯 JavaScript（无 Pinia）**：仅保留 FR-027-1（先读源码），FR-027-2 自动失效。
- **Monorepo**：跨 package 引用 composable 时，PR 描述必须同时贴出 composable 源码片段与 package 版本号，避免"版本漂移导致 API 形状变更"。
