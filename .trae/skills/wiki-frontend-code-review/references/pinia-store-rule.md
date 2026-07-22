# Rule Catalog — Pinia Store

Pinia Store 审查规则：确保 store 定义规范、状态管理模式一致。所有参数从 `config/review-config.md` 读取，禁止在规则文件中硬编码。

## 使用 setup 语法定义 store

IsUrgent: True
Category: Pinia Store

### Description

`defineStore` 必须使用 setup 语法：`defineStore('name', () => { ... })`，禁止 options 语法（`{ state, getters, actions }`）。setup 语法与 Composition API 一致、可自由组合 `ref`/`computed`/函数，便于在组件与 store 间复用逻辑。

### Suggested Fix

把 options 语法的 state/getters/actions 迁移为 setup 内的 `ref`/`computed`/函数，并在末尾 `return` 外部需要的成员。

> **示例代码**: 参见 [examples/pinia-store-rule-examples.md](examples/pinia-store-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## store 内部用 ref 定义状态，function 定义 action

IsUrgent: False
Category: Pinia Store

### Description

状态用 `ref` 声明（访问处加 `.value`），派生状态用 `computed`，变更逻辑用普通 `function` 声明——不区分 mutations 与 actions。setup 语法下没有 mutations 概念，混用 options 心智模型会引入 `this` 歧义。

### Suggested Fix

把 `this.xxx = ...` 改为 `xxx.value = ...`，把 `actions` 中的方法改为顶层 `function`。

> **示例代码**: 参见 [examples/pinia-store-rule-examples.md](examples/pinia-store-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 须 return 所有外部需要的状态和方法

IsUrgent: True
Category: Pinia Store

### Description

setup 语法下，store 只暴露在 `return` 语句中列出的成员。遗漏 return 会导致组件中使用 `storeXxx is undefined`，且无类型报错提示（仅在运行时暴露）。提交前须核对组件实际使用的成员是否都已 return。

### Suggested Fix

对照组件使用清单，逐项核对 store 末尾 `return` 对象；建议按状态/计算/动作分组排列。

> **示例代码**: 参见 [examples/pinia-store-rule-examples.md](examples/pinia-store-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## SSE 事件处理拆分为独立函数

IsUrgent: True
Category: Pinia Store

### Description

SSE 流式事件的处理逻辑必须按事件类型拆分为独立的具名函数（如 `appendAnswer`/`setRefs`/`finalizeAnswer`），由消费 SSE 的组件按事件类型分发调用。禁止把所有事件处理内联到组件的 `onMessage` 回调里——这会让 store 逻辑泄漏到组件，且无法被测试与复用。

### Suggested Fix

在 store 内为每种事件类型定义独立 action，组件侧只做"事件类型 → action"的派发。

> **示例代码**: 参见 [examples/pinia-store-rule-examples.md](examples/pinia-store-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## 错误处理须保留部分数据并结束 loading

IsUrgent: True
Category: Pinia Store

### Description

SSE 流或异步请求失败时，错误处理 action 必须：(1) 保留已接收的部分数据（不重置已 push 的消息）；(2) 将 `loading` 标记为 `false`；(3) 设置错误状态字段供 UI 展示。直接 throw 或重置状态会导致用户丢失已生成内容、界面卡在 loading。

### Suggested Fix

抽出 `markError(err)` action，只更新 loading 与 error 字段，不动 messages。

> **示例代码**: 参见 [examples/pinia-store-rule-examples.md](examples/pinia-store-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。

## store 间不直接引用，通过组件组合

IsUrgent: False
Category: Pinia Store

### Description

store 之间禁止互相 `useXxxStore()` 直接调用以避免循环依赖与初始化顺序问题。需要跨 store 的数据流时，由组件同时引入两个 store 并在组件内组合；确有共享逻辑时，抽到独立的 composable（`useXxx`）中。

### Suggested Fix

删除 store A 内 `useBStore()` 的调用，把跨 store 协调移到组件层；共享逻辑抽 composable。

> **示例代码**: 参见 [examples/pinia-store-rule-examples.md](examples/pinia-store-rule-examples.md)。加载示例文件以参考 Wrong/Right 对照或生成修复代码。
