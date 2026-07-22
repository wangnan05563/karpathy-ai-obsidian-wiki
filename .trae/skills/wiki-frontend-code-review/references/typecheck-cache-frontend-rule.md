# 类型检查缓存清理（FR-026）

> 复盘来源：vue-tsc 在源码已正确收窄（如 `if (store.foo) return store.foo.bar`）后仍持续报 `Object is possibly null` / `Object is possibly 'undefined'`，开发者用 `as any` / 非空断言 `!` / `@ts-ignore` 绕过告警，结果掩盖真实类型缺陷，并使后续 PR 的类型检查结果与源码不一致。
> 所有可变参数从 config/review-config.md 的 `typecheck_cache_frontend` 字段读取。

## 规则

### FR-026-1：vue-tsc 报告与源码不一致时必须清缓存而非绕过

当 `vue-tsc` / `tsc` 报告的错误在源码中已经通过显式收窄（`if (x != null)`、`Array.isArray(x)`、`typeof x === 'string'` 等）消除，但工具仍持续报错时，判定为**幽灵错误**（stale typecheck artifact）。处理方式必须按以下顺序：

1. 先复核源码：确认收窄逻辑无误（包括跨函数调用、跨 await 边界的类型守卫是否被丢失）。
2. 源码确认无误后，按 `typecheck_cache_frontend.cache_cleanup_targets` 列出的清理目标一次性删除缓存产物（如 `*.tsbuildinfo`、Vite 依赖缓存、TS 编译产物目录）。
3. 重新执行 `typecheck_cache_frontend.typecheck_command` 验证错误是否消失。
4. 若清缓存后错误仍存在，回到第 1 步重新审源码——禁止跳过到第 5 步。
5. 仅在确认是工具已知限制（如 vue-tsc 对复杂泛型的误报，已在 issue tracker 记录）时，才允许使用 `@ts-expect-error`（非 `@ts-ignore`）并在同行注明 issue 链接。

**禁止**用以下方式"绕过"幽灵错误，因为它们会同时掩盖真实类型缺陷：

- `as any` / `as unknown as T`
- 非空断言 `value!.foo`
- `// @ts-ignore`
- `// eslint-disable-next-line @typescript-eslint/no-non-null-assertion`

### FR-026-2：禁止把 `as any` / `!` / `@ts-ignore` 作为常规类型修复手段

不属于幽灵错误场景的常规类型不匹配，必须修复类型本身（修正接口定义、收紧联合类型、补充类型守卫），禁止用断言或抑制指令掩盖。

## 适用场景

- Vue 3 + `<script setup lang="ts">` 项目使用 `vue-tsc` 做类型检查时报告与源码逻辑不一致的错误。
- 升级 Vue / TypeScript / Volar 后出现的批量类型告警。
- PR diff 中出现 `as any` / `!` / `@ts-ignore` 的新增行。

## 不适用场景

- 真实的类型不匹配（源码确有缺陷）—— 此时必须修复源码，不属于本规则范围。
- 第三方库 `d.ts` 不完整导致的告警 —— 走 `declare module` 或 `// @ts-expect-error` 加 issue 引用的例外路径，但需在 PR 描述中说明。
- 单元测试 / mock 文件中的 `as any` —— 测试夹具允许放宽类型（见 config 的 `typecheck_cache_frontend.test_file_allowlist`）。

## 检查流程

```
[开始] vue-tsc 报告 Object is possibly null/undefined
  │
  ▼
[1] 复核源码收窄逻辑
  │  └─ 收窄无效 / 缺失 → 修复源码（非本规则）
  │
  ▼ 收窄有效
[2] 按 cache_cleanup_targets 删除缓存产物
  │
  ▼
[3] 重新执行 typecheck_command 验证
  │  └─ 错误消失 → [结束：幽灵错误已解决]
  │
  ▼ 错误仍存在
[4] 回到 [1] 重新审源码（禁止直接跳到 [5]）
  │  └─ 仍确认源码无误
  │
  ▼
[5] 确认为工具已知限制 → 用 @ts-expect-error + issue 链接
  │
  ▼
[结束]
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `typecheck_cache_frontend.typecheck_command` | `vue-tsc --noEmit` | 类型检查命令 |
| `typecheck_cache_frontend.cache_cleanup_targets` | `*.tsbuildinfo, node_modules/.vite, src/**/*.js` | 幽灵错误时清理的缓存产物 glob 列表（逗号分隔） |
| `typecheck_cache_frontend.bypass_keywords` | `as any, as unknown as, @ts-ignore, !.` | 禁止用作常规修复手段的绕过关键字 |
| `typecheck_cache_frontend.allow_ts_expect_error` | `true` | 是否允许 `@ts-expect-error`（须配 issue 链接） |
| `typecheck_cache_frontend.test_file_allowlist` | `*.spec.ts, *.test.ts, **/__mocks__/**` | 允许放宽类型的测试文件 glob |
| `typecheck_cache_frontend.recheck_after_clean` | `true` | 清缓存后必须重新验证 |

## 检查方式

1. 在 PR diff 中扫描 `typecheck_cache_frontend.bypass_keywords` 关键字新增行。
2. 对每个新增行追溯其上下文：定位 vue-tsc 报告的对应告警，复核源码收窄逻辑。
3. 若源码已正确收窄但告警仍存在，按 `cache_cleanup_targets` 清缓存后重跑 `typecheck_command`。
4. 仍存在则要求 PR 作者在评论中说明 issue 链接并改用 `@ts-expect-error`。
5. 任何 `as any` / `!` / `@ts-ignore` 在非测试文件中的新增都标记为 Urgent。

## 正确示例

```vue
<!-- ✅ 源码已正确收窄，先清缓存而非绕过 -->
<script setup lang="ts">
import { ref, computed } from 'vue'

interface Foo { bar?: { baz: string } }
const foo = ref<Foo | null>(null)

const baz = computed<string>(() => {
  // 显式收窄：if 分支内 TS 已识别为非空
  if (foo.value?.bar?.baz) {
    return foo.value.bar.baz
  }
  return ''
})
</script>
```

```bash
# vue-tsc 仍报 Object is possibly null → 清缓存而非加 !
pnpm exec vue-tsc --noEmit            # 复现
rm -f frontend/*.tsbuildinfo
rm -rf frontend/node_modules/.vite
rm -f frontend/src/**/*.js            # 清理陈旧编译产物
pnpm exec vue-tsc --noEmit            # 验证告警消失
```

## 错误示例

```vue
<!-- ❌ 用 as any / ! / @ts-ignore 绕过幽灵错误 -->
<script setup lang="ts">
import { ref, computed } from 'vue'

interface Foo { bar?: { baz: string } }
const foo = ref<Foo | null>(null)

const baz = computed<string>(() => {
  // ❌ 非空断言绕过：一旦 foo.value 为 null 直接运行时崩溃
  return foo.value!.bar!.baz
})

// ❌ as any 绕过：丢失全部类型保护
const unsafe = computed(() => (foo.value as any).bar.baz)

// ❌ @ts-ignore 绕过：且未附 issue 链接
// @ts-ignore
const ignored = foo.value.bar.baz
</script>
```

## 适配新项目

- **React / Next.js**：将 `vue-tsc` 替换为 `tsc --noEmit`，清理目标改为 `next build` 缓存（`.next/`）与 `*.tsbuildinfo`；其余流程不变。
- **Vue 2**：使用 `vetur` / `vls` 时同样清 `*.tsbuildinfo` 与 `node_modules/.cache`，绕过关键字集合保持一致。
- **纯 JavaScript**：本规则不适用（无静态类型检查），但 ESLint 规则 `no-undef` 类似的"幽灵告警"可参考本流程清 `.eslintcache`。
- **Monorepo**：`cache_cleanup_targets` 改为各 package 的 `dist/` 与 `*.tsbuildinfo`，并按 turbo / nx 的缓存根配置调整。
