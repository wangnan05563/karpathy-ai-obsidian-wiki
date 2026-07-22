# 类型检查缓存清理规则（CODING-026）

> 复盘来源：v2 导航栏与图标改造后，vue-tsc 仍报"Object is possibly null"旧错误，但源文件已修改正确。根因是 vue-tsc 增量缓存（`tsconfig.tsbuildinfo` + Vite `.vite` 目录）返回旧版本类型信息。
> 所有可变参数从 `config/coding-standards-config.md` 的 `typecheck_cache` 字段读取，禁止在规则文件或业务代码中硬编码路径或文件名。

## 规则

**当类型检查器（vue-tsc / tsc）报告的错误与源文件当前内容不一致时**，必须先清理类型检查增量缓存，再重新运行类型检查，禁止在源文件中添加无意义的 `as any` / `!` 断言绕过"幽灵错误"。

## 适用场景

- vue-tsc 报告 `Object is possibly null` / `Property 'xxx' does not exist on type 'never'` 等错误，但源文件已正确收窄类型
- TypeScript 增量编译后修改了类型定义，但检查器仍报旧错误
- 引入新 composable / 工具函数后，类型推断结果与源码实际返回类型不符
- Vite dev server 加载了 `src/**/*.js` 旧编译产物而非 `.ts` 源码（Vite 优先解析 .js URL）

## 不适用场景

- 首次运行类型检查（无缓存可清）
- CI/CD 流水线（通常每次都是 fresh checkout，无增量缓存）
- 错误确实存在于源文件中（先修复源文件，再考虑缓存问题）
- 全局安装的 tsc 与项目 tsconfig 不兼容（应升级/降级 tsc 而非清缓存）

## 缓存清理流程

```
vue-tsc / tsc 报告错误
   ↓
Read 源文件对应行号，确认错误是否真实存在
   ↓
错误真实 → 修复源文件 → 重新检查
   ↓
错误不存在（幽灵错误）→ 进入缓存清理流程
   ↓
1. 删除 typecheck_cache.incremental_cache_files 中配置的缓存文件
2. 删除 typecheck_cache.vite_cache_dirs 中的 Vite 缓存目录
3. 删除 src 下 typecheck_cache.stale_artifact_patterns 匹配的旧 .js 编译产物
4. 重新运行 typecheck_command
   ↓
错误消失 → 完成
   ↓
错误仍存在 → 重新审视源文件（可能误判）
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `typecheck_cache.enabled` | `true` | 是否启用缓存清理守卫 |
| `typecheck_cache.severity` | `error` | 违规严重级别 |
| `typecheck_cache.incremental_cache_files` | `tsconfig.tsbuildinfo,tsconfig.app.tsbuildinfo,tsconfig.node.tsbuildinfo` | TypeScript 增量缓存文件名（逗号分隔） |
| `typecheck_cache.vite_cache_dirs` | `.vite,node_modules/.vite` | Vite 缓存目录（逗号分隔） |
| `typecheck_cache.stale_artifact_patterns` | `src/**/*.js` | 旧版 TypeScript 增量编译产物 glob（污染源码目录） |
| `typecheck_cache.typecheck_command` | `npx vue-tsc --noEmit` | 类型检查命令 |
| `typecheck_cache.prevent_bypass_assertions` | `as any, as unknown, ! postfix, // @ts-ignore, // @ts-expect-error` | 禁止用于绕过幽灵错误的断言模式（逗号分隔） |

## 检查方式

1. **幽灵错误识别**：当 vue-tsc 报错但 Read 源文件对应行号显示代码已正确收窄类型时，判定为幽灵错误
2. **断言绕过检测**：Grep `prevent_bypass_assertions` 中的模式，若新增的断言用于绕过幽灵错误而非真实类型收窄需求，即违规
3. **缓存清理验证**：清理缓存后必须重新运行 `typecheck_command`，确认错误消失

## 正确示例

```typescript
// 步骤 1：发现 vue-tsc 报"Object is possibly null"于第 42 行
// 步骤 2：Read 源文件第 42 行，发现已用局部变量收窄
const result: AiTestResult = await res.json();
aiTestResult.value = result;
if (result.ok) { ... }  // 局部变量已收窄，源码正确

// 步骤 3：判定为幽灵错误，清理缓存
// PowerShell: Remove-Item tsconfig.tsbuildinfo, .vite -Recurse -Force -ErrorAction SilentlyContinue

// 步骤 4：重新运行 npx vue-tsc --noEmit → 错误消失
```

## 错误示例

```typescript
// 错误：用 as any 绕过幽灵错误
const result = (await res.json()) as any;  // 违规：掩盖真实类型
if (result.ok) { ... }

// 错误：用 ! 后缀断言绕过
aiTestResult.value!.ok  // 违规：掩盖 possibly null

// 错误：用 @ts-ignore 注释压制
// @ts-ignore
aiTestResult.value.ok  // 违规：错误被压制而非修复
```

## 适配新项目

- 适配纯 React 项目：`typecheck_command` 改为 `npx tsc --noEmit`，删除 `stale_artifact_patterns`（React 项目无 .vue 编译产物）
- 适配 Webpack 项目：`vite_cache_dirs` 改为 `node_modules/.cache`
- 适配 monorepo：`incremental_cache_files` 列出各子项目的 tsbuildinfo 路径
- 适配 CI 环境：将 `enabled` 设为 `false`（CI 每次 fresh checkout 无缓存问题）

## 与其他规则的关系

- 与 CODING-027（Composable API 先读后用）互补：CODING-026 解决"类型检查器报告的错误"，CODING-027 解决"开发者对返回类型的错误假设"
- 与 CODING-028（混合类型运行时分流）互补：CODING-026 解决"幽灵错误"，CODING-028 解决"真实存在的混合类型分流需求"
