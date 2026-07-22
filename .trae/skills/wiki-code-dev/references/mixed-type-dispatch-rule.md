# 混合类型运行时分流规则（CODING-028）

> 复盘来源：InputToolbar 组件的 tools 数组元素类型从 `string` 升级为 `{ key: string, ... }` 对象时，未做运行时类型分流，导致 v-for 渲染时旧字符串元素调用 `.key` 失败。
> 所有可变参数从 `config/coding-standards-config.md` 的 `mixed_type_dispatch` 字段读取，禁止在规则文件中硬编码类型名或字段名。

## 规则

**当类型从 T 升级为 U（如 `string` → `{ key: string, ... }`）且代码需同时处理新旧版本时，必须用 helper 函数做 `typeof` / `in` 运算符运行时分流**，禁止用 `as any` / `as unknown as U` 强制类型断言绕过分流。

## 适用场景

- 数组元素类型从原始类型升级为对象类型（如 `string[]` → `Array<{ key: string, ... }>`）
- API 响应字段从单值升级为复合对象（如 `value: string` → `value: { text: string, label?: string }`）
- 跨版本兼容代码（旧数据为 T，新数据为 U，需同时处理）
- 渐进式重构场景（部分代码已升级为 U，部分仍为 T）

## 不适用场景

- 类型升级后已全量迁移完毕（无旧数据残留，直接用 U 即可）
- 同一对象在不同分支有不同字段（用 type guard 而非 typeof 分流）
- 泛型约束已确保类型一致（编译器保证）

## 分流流程

```
类型从 T 升级为 U
   ↓
判断是否需同时处理新旧版本
   ↓
否 → 直接用 U，旧数据迁移后删除兼容代码
   ↓
是 → 必须用 helper 函数运行时分流
   ↓
1. 定义 type guard 函数 isU(x: T | U): x is U
2. 用 typeof / in 运算符判断
3. v-for / map 中调用 type guard 分流
   ↓
禁止用 as any / as unknown as U
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `mixed_type_dispatch.enabled` | `true` | 是否启用混合类型分流守卫 |
| `mixed_type_dispatch.severity` | `error` | 违规严重级别 |
| `mixed_type_dispatch.forbidden_assertions` | `as any, as unknown as, as T` | 禁止的强制类型断言模式（逗号分隔） |
| `mixed_type_dispatch.required_type_guards` | `typeof, in, instanceof` | 必须使用的运行时分流运算符（任一即可） |
| `mixed_type_dispatch.helper_function_required` | `true` | 是否必须封装为独立 helper 函数（而非内联 typeof） |
| `mixed_type_dispatch.helper_naming_pattern` | `is<TypeName>` | helper 函数命名约定（如 `isObjectTool` / `isRangeValue`） |

## 检查方式

1. **断言检测**：Grep `forbidden_assertions` 中的模式，在涉及类型升级的代码段中命中即违规
2. **type guard 存在性**：当数组元素 / 函数参数类型为 `T | U` 联合类型时，必须有对应 `isU` helper 函数
3. **运行时分流验证**：v-for / map 中访问 U 类型独有字段前，必须先调用 type guard 分流

## 正确示例

```typescript
// 类型从 string 升级为 { key: string, icon?: string, label?: string }
type ToolItem = string | { key: string; icon?: string; label?: string };

// 正确：定义 type guard helper
function isObjectTool(tool: ToolItem): tool is { key: string; icon?: string; label?: string } {
  return typeof tool === 'object' && tool !== null && 'key' in tool;
}

// 正确：v-for 中分流
<template>
  <div v-for="tool in tools" :key="isObjectTool(tool) ? tool.key : tool">
    <svg v-if="isObjectTool(tool) && tool.icon">{{ tool.icon }}</svg>
    <span>{{ isObjectTool(tool) ? tool.label : tool }}</span>
  </div>
</template>

// 正确：map 中分流
const keys = tools.map(t => isObjectTool(t) ? t.key : t);
```

## 错误示例

```typescript
// 错误：用 as any 绕过分流
tools.map(t => (t as any).key);  // 运行时 t 是 string 时报错

// 错误：用 as unknown as 强制断言
const obj = tool as unknown as { key: string };  // 运行时可能不是对象

// 错误：内联 typeof 但未封装 helper（违反 helper_function_required）
if (typeof tool === 'object') {
  // 多处重复的 typeof 判断，难以维护
}

// 错误：假设所有元素都是新类型
tools.forEach(t => t.key);  // 旧数据 string 没有 .key
```

## 适配新项目

- 适配 JavaScript 项目（无类型）：仍需用 `typeof` / `in` 运行时分流，但无需 type guard
- 适配严格类型项目：可将 `helper_function_required` 降级为 `suggestion`（内联 typeof 也可）
- 适配无类型升级场景：将 `enabled` 设为 `false`

## 与其他规则的关系

- 与 CODING-026（类型检查缓存清理）联动：CODING-026 解决"类型检查器误报"，CODING-028 解决"类型检查器不报但运行时失败"
- 与 CODING-029（SFC 单 script 块）独立：CODING-029 是文件结构约束，CODING-028 是类型分流约束
