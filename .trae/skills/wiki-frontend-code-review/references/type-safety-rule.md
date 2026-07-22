# Rule Catalog — Type Safety

类型安全审查规则：确保 API 响应类型定义完整、ref 收窄规范、禁止 any 滥用。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

## API 响应须定义 TypeScript interface，禁止 any

IsUrgent: True
Category: Type Safety

### Description

所有 API 响应必须定义 TypeScript `interface` 或 `type` 描述结构，函数返回值与变量类型显式标注，禁止用 `any`。`any` 会关闭类型检查、让错误延迟到运行时、破坏 IDE 重构与跳转。例外：与第三方无类型库交互的边界可用 `unknown` 接收后立即断言。

### Suggested Fix

为每个接口定义响应 interface，请求函数显式标注返回类型；用 `unknown` 替代 `any` 作为受检边界。

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## fetch 须先检查 res.ok，再 json() 解析

IsUrgent: True
Category: Type Safety

### Description

`fetch` 不会把 4xx/5xx 当作异常抛出，必须先检查 `res.ok`（或 `res.status`）并在非 ok 时抛出带状态码与响应文本的错误，再调用 `res.json()`。否则 404/500 会以空对象或解析错误的形式悄悄进入业务逻辑，难以定位。

### Suggested Fix

封装统一的请求包装函数，在内部做 `res.ok` 检查；或在每个 fetch 处显式检查。

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## SSE 事件 data 须 JSON.parse 后用类型守卫

IsUrgent: True
Category: Type Safety

### Description

SSE 事件的 `data` 字段是字符串，必须先 `JSON.parse` 再用类型守卫（如 `parsed.sessionId`、`parsed.type`）确认结构后再使用。直接当作强类型对象访问会在异常数据时抛错中断流；`JSON.parse` 失败也须 try/catch 捕获，跳过该事件而非中断整条流。

### Suggested Fix

封装 `parseSSEEvent(raw: string): SSEEvent | null`，内部 try/catch + 字段校验。

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 联合类型窄化用 as 断言或类型守卫函数

IsUrgent: False
Category: Type Safety

### Description

判别式联合（如多种 issue 类型 `broken_link` | `orphan_page`）须通过类型守卫函数或 `as` 断言窄化到具体分支后再访问分支专属字段。直接在 `if` 中跨分支访问字段会触发 TS 报错；用 `as any` 绕过会丢失类型保护。

### Suggested Fix

为每个分支定义带 `type` 字面量的 interface，用 `evt.type === 'xxx'` 窄化；复杂判断抽 `isXxx(x): x is Xxx` 守卫函数。

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## ref 须指定泛型类型

IsUrgent: True
Category: Type Safety

### Description

`ref()` 须显式指定泛型类型，尤其是初始值为 `null` 的模板引用与异步数据。不指定泛型时 TS 会从初始值推断为 `null` 或具体值类型，后续赋值会报错或丢失字段类型。

### Suggested Fix

为 ref 补充泛型参数：模板引用用 `ref<HTMLElement | null>(null)`，数据用 `ref<ItemType[]>([])`。

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 枚举值用字面量联合类型，禁止 enum

IsUrgent: False
Category: Type Safety

### Description

有限的枚举值用字面量联合类型（如 `'broken_link' | 'orphan_page'`）表达，禁止使用 `enum`。字面量联合在编译后是纯字符串、tree-shaking 友好、与 JSON 数据天然兼容；`enum` 会生成额外运行时对象，且字符串枚举与 JSON 互转需要额外映射。

### Suggested Fix

把 `enum X { A = 'a' }` 改为 `type X = 'a' | 'b'`，常量集合可用 `as const` 对象。

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## reactive 对象属性访问必须在类型定义范围内

IsUrgent: True
Category: Type Safety

### Description

`reactive(obj)` 返回的对象类型由入参 `obj` 推断，访问未在入参中声明的属性会触发 TS 报错（`Property 'xxx' does not exist on type ...`）。复盘 Cleanup.vue 时发现：把卡片元数据字段 `showDays` 误当作 `reactive` 表单对象的属性直接访问（`form.showDays`），TS 编译失败。原因：`showDays` 是卡片元数据（独立来源），不是表单字段，应通过元数据查找获取，而非挂到表单 reactive 上。

更广泛地：把不同来源的字段混入同一 `reactive` 对象会让类型与数据来源模糊，TS 无法推断导致编译失败；运行时虽有值但类型已不可信。

### Suggested Fix

- 严格区分表单字段与卡片元数据：表单字段进 `reactive(form)`，元数据单独存储（如 `const cardMeta = ref<Meta[]>([])`）。
- 从元数据取属性时用 `find` / `filter` 查找，禁止把元数据字段直接挂到表单 reactive 上。
- 表单 reactive 接口显式声明 `interface`，避免隐式推断：

```ts
interface CleanForm {
  before: string
  keepDays: number
}
const form = reactive<CleanForm>({ before: '', keepDays: 7 })
// ❌ form.showDays 报错：showDays 不在 CleanForm 上
// ✅ 从元数据查找
const meta = cardMeta.value.find(c => c.key === 'expired')
const showDays = meta?.showDays ?? 7
```

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。

## unused imports 必须删除（strict 模式下报错）

IsUrgent: True
Category: Type Safety

### Description

`tsconfig` 开启 `"strict": true` + `"noUnusedLocals": true` + `"noUnusedParameters": true` 时，未使用的 import / 局部变量 / 参数都会被 TS 编译器报为错误（`error TS6133: 'X' is declared but its value is never read`），导致 `pnpm build` 直接失败。复盘 Cleanup.vue 时发现：重构后遗留的 `ElMessageBox`、`ElMessage`、`ref` 等未使用 import 让构建中断。

仅删除即可，不要保留"以防后续用得到"的 import——后续需要时 IDE 自动导入更可靠，遗留 import 反而掩盖真实依赖关系。

### Suggested Fix

- 重构完成后立即运行 `pnpm tsc --noEmit` 检查未使用 import。
- IDE 启用"保存时整理 import"（VSCode `editor.codeActionsOnSave.source.organizeImports`）。
- 对必须保留但暂时未用的变量用 `_` 前缀（如 `_unused`），TS 会跳过以下划线开头的标识符。

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。

## 联合类型窄化失败时用 as 断言或 type guard

IsUrgent: False
Category: Type Safety

### Description

判别式联合（discriminated union）通常用 `if (x.type === 'a')` 即可窄化。但部分场景 TS 仍无法窄化：
- 判别字段不是字面量类型，而是 `string` / `number`（被放宽）。
- 同一表达式在闭包内被多次访问，TS 担心值变化而拒绝窄化。
- 通过索引访问 `record[key]` 时，TS 合并所有 value 类型，无法按 key 窄化。

此类场景必须用 `as` 断言或自定义 type guard 函数显式窄化；用 `as any` 绕过会丢失类型保护且违反前述"API 响应须定义 TypeScript interface，禁止 any"规则。

### Suggested Fix

```ts
// 1) as 断言：明确告诉 TS 当前的具体分支
const item = record[key] as CleanFormItem

// 2) type guard 函数：复杂判断抽出谓词函数
function isCleanFormItem(x: unknown): x is CleanFormItem {
  return typeof x === 'object' && x !== null && 'before' in x
}
if (isCleanFormItem(record[key])) {
  // 此处 record[key] 已窄化为 CleanFormItem
  record[key].before
}
```

注意：`as` 断言只是"我担保"，运行时仍可能不符；type guard 更安全，优先选择。

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。

## await 后访问 ref 必须用局部变量收窄

IsUrgent: True
Category: Type Safety

### Description

在 async 函数中给 `ref<T | null>` 赋值后，`await` 之后再访问该 ref，TypeScript 认为它可能已被改为 `null`（vue-tsc 报错"Object is possibly null"）。这是因为 await 是一个同步断点，TS 无法保证 await 之间 ref 未被修改。

必须将赋值结果保存到局部变量，通过局部变量访问，因为局部变量不会被外部修改。

### Suggested Fix

```typescript
// ❌ 错误：await 后直接访问 ref.value 的属性
aiTestResult.value = await res.json();
if (aiTestResult.value.ok) { ... }  // possibly null

// ✅ 正确：局部变量收窄
const result: AiTestResult = await res.json();
aiTestResult.value = result;
if (result.ok) { ElMessage.success('成功'); }
```

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。

## 模板中访问可空 ref 必须用计算属性封装

IsUrgent: True
Category: Type Safety

### Description

模板中直接用三元表达式访问 `ref<T | null>` 的属性，在 vue-tsc strict 模式下会报"Object is possibly null"。必须在 `<script setup>` 中用 `computed` 封装，将 null 检查逻辑收敛到计算属性内部，模板只消费计算属性的结果。

`v-if` 守卫可以配合使用，但不应替代计算属性——模板中的复杂条件表达式可读性差且难以调试。

### Suggested Fix

```typescript
// ❌ 错误：模板中直接访问可空 ref
// <span>{{ aiTestResult.ok ? '成功' : aiTestResult.detail }}</span>

// ✅ 正确：计算属性封装
const testResultText = computed(() => {
  const r = aiTestResult.value;
  return r ? (r.ok ? '成功' : r.detail) : '';
});
```

```vue
<template>
  <span>{{ testResultText }}</span>
</template>
```

> **示例代码**: 参见 [examples/type-safety-rule-examples.md](examples/type-safety-rule-examples.md)。
