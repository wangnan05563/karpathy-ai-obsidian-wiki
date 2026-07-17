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
