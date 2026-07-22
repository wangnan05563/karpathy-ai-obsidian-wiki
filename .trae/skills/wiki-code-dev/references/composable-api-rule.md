# Composable API 先读后用规则（CODING-027）

> 复盘来源：使用非自己编写的 composable（如 `useTTS`）时，假设返回对象包含 `setRate` 方法，实际运行时却缺失该方法。根因是直接调用未读源码，基于"应该有这个方法"的假设编码，导致 store setup 时获取旧版对象。
> 所有可变参数从 `config/coding-standards-config.md` 的 `composable_api` 字段读取，禁止在规则文件中硬编码方法名或属性名。

## 规则

**使用非自己编写的 composable / hook / store 前，必须先 Read 源码确认其导出的属性与方法签名**，禁止基于命名约定或文档假设 API 形状。类型检查通过不等于运行时存在（store 重建、Pinia dispose 等场景可能丢失运行时方法）。

## 适用场景

- 调用项目内其他开发者编写的 composable（`useXxx`）
- 引用第三方库提供的 Vue composable / React hook
- 在测试脚本中初始化 Pinia store 后访问其方法
- 跨模块复用 store 实例（store 可能在其他模块被重建）

## 不适用场景

- 自己刚编写的 composable（已清楚 API 形状）
- 标准库 / 框架内置 API（如 `ref` / `computed` / `watch`）
- 通过 IDE 跳转到定义已查看过源码的 composable

## 检查流程

```
要使用 useXxx() / store 的方法
   ↓
判断是否为自己编写
   ↓
是 → 直接使用
   ↓
否 → 必须 Read 源码，确认：
     1. export 的方法名 / 属性名是否存在
     2. 方法签名（参数、返回类型）是否符合预期
     3. 是否需要传入特定参数（如 store id）
     4. 是否有 setup 顺序依赖（如必须先调用 setXxx 再用 yyy）
   ↓
确认无误 → 使用
   ↓
运行时方法缺失 → 检查 store 是否被重建（详见"运行时方法缺失排查"）
```

## 运行时方法缺失排查

当类型检查通过但运行时 `xxx.method is not a function` 时，按以下顺序排查：

1. **Read 源码**：确认源码确实导出该方法
2. **检查 store 重建**：是否有诊断代码调用 `$dispose()` + `pinia._s.delete('xxx')` 后重建 store，导致运行时丢失方法
3. **检查编译产物污染**：`src/**/*.js` 是否存在旧版编译产物（与 CODING-026 联动）
4. **检查 Vite 缓存**：Vite 是否加载了 `.js` 旧产物而非 `.ts` 源码
5. **检查导入路径**：是否从 `./xxx.js` 而非 `./xxx` 导入

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `composable_api.enabled` | `true` | 是否启用 Composable 先读后用守卫 |
| `composable_api.severity` | `error` | 违规严重级别 |
| `composable_api.pattern_prefixes` | `use, store, composable` | 触发"先读后用"检查的命名前缀（逗号分隔） |
| `composable_api.excluded_patterns` | `useRouter, useRoute, useStore, useState` | 豁免列表（标准库 composable） |
| `composable_api.required_confirmation` | `export_shape,method_signature,setup_order` | 必须确认的 API 形状要素（逗号分隔） |
| `composable_api.diagnostic_code_must_not_rebuild` | `true` | 诊断代码禁止调用 `$dispose` / `_s.delete` 重建 store |

## 检查方式

1. **代码审查**：对调用 `useXxx()` 的位置，检查是否有最近的 Read 源码记录（代码注释中标注 `// 已读 useXxx 源码：返回 { a, b, c }`）
2. **类型 vs 运行时对比**：当类型检查通过但运行时报错时，优先怀疑 store 重建而非类型错误
3. **诊断代码审计**：Grep `\$dispose|_s\.delete` 调用，确认是否在测试/诊断脚本中误重建 store

## 正确示例

```typescript
// 步骤 1：要使用 useTTS composable 的 setRate 方法
// 步骤 2：Read composables/useTTS.ts 确认 export { tts, setRate, setVoice }
// 步骤 3：确认 setup 顺序无依赖（setRate 可在 store setup 后任意时机调用）
// 步骤 4：使用
import { useTTS } from '@/composables/useTTS';
const { tts, setRate } = useTTS();
setRate(1.2);  // 类型 + 运行时都正确
```

## 错误示例

```typescript
// 错误：未读源码，假设 useTTS 返回 setRate
import { useTTS } from '@/composables/useTTS';
const tts = useTTS();  // 假设返回单一对象
tts.setRate(1.2);  // 运行时可能 undefined（实际返回解构对象）

// 错误：诊断代码重建 store 导致方法丢失
function diagnose() {
  const pinia = getActivePinia();
  pinia._s.delete('tts');  // 违规：销毁运行时 store
  pinia._s.set('tts', undefined);  // 后续 setup 拿到旧版对象
}

// 错误：从 .js 编译产物导入
import { useTTS } from '@/composables/useTTS.js';  // 加载旧产物，与 CODING-026 联动
```

## 适配新项目

- 适配 React 项目：`pattern_prefixes` 改为 `use, hook`
- 适配 Angular 项目：`pattern_prefixes` 改为 `service, inject`
- 适配无 store 项目：将 `enabled` 设为 `false`

## 与其他规则的关系

- 与 CODING-026（类型检查缓存清理）联动：CODING-026 解决"类型检查器报错但源码正确"，CODING-027 解决"类型检查通过但运行时方法缺失"
- 与 CODING-028（混合类型运行时分流）互补：CODING-027 强调使用前读源码，CODING-028 强调类型升级时的运行时分流
