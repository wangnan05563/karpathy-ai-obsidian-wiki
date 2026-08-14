# Rule Catalog — 包管理器 store 卫生 (BR-095)

后端审查条目，对应通用编码规范 `CODING-PNPM-STORE-HYGIENE`（wiki-code-dev references/pnpm-store-hygiene-rule.md）。前后端构建均依赖 **pnpm content-addressable store** 的健康与收敛。在 WorkBuddy safe-delete 沙箱钩子（fail-closed）等会拦截 rename / 主目录探测操作的环境中，pnpm 主目录探测被打断会退化为在当前盘根建 `.pnpm-store`，污染工作区且让 `node_modules` 解析不到统一 store，导致构建在散落缓存上静默运行或失败。规范：CI / 环境初始化 / Dockerfile / 构建脚本须**断言 pnpm store 收敛**（全局 `.npmrc` 显式 `store-dir`），且仓库 / 盘根**不得存在孤儿 `.pnpm-store`**。

> 复盘来源：项目根目录曾散落一份 pnpm 缓存（Jul 11 创建、无引用），正是 safe-delete 钩子打断 pnpm 主目录探测后的退化产物。统一方案：全局 `.npmrc` 写 `store-dir=D:\.pnpm-store`，`pnpm store path` 在任意 cwd 均返回该值；孤儿确认无 `node_modules/.modules.yaml` 引用后删除。对应前端 FR-085（包管理器 store 卫生）/ wiki-auto-testing `dependency_store_hygiene_check`。

## Scope

- Covers: CI / 环境初始化 / Dockerfile / 构建脚本对 pnpm store 收敛的断言；全局 `.npmrc` 的 `store-dir` 收敛键；仓库 / 盘根孤儿 `.pnpm-store` 检测与清理约束。
- Does NOT cover: 纯 npm/yarn（无严格 content-addressable store 或不受该钩子影响）；已显式收敛且无孤儿目录的环境；不受 safe-delete 钩子约束的普通本地开发机（非 CI / 沙箱）。

## Rules

### BR-095-1: 构建/CI 前置须断言 pnpm store 收敛

Category: 后端 / 构建依赖 / 依赖卫生
Severity: warn

#### Description

CI / 环境初始化 / Dockerfile / 构建脚本在 `pnpm install` / `pnpm build` 之前，须断言 pnpm store 已收敛：全局 `.npmrc` 显式声明 `store-dir=<统一绝对路径>`，且 `pnpm store path` 返回该值（在不同 cwd 下一致）。缺收敛键会让 pnpm 退化为盘根散落 `.pnpm-store`，污染工作区并使 `node_modules` 解析不到统一 store（BR-095-1，建议级；CI 前置可升 Critical）。阈值 / 路径从配置读取，禁止硬编码绝对路径字面量。

```text
# ~/.npmrc（须显式收敛）
store-dir=D:\.pnpm-store
```

### BR-095-2: 仓库/盘根不得存在孤儿 .pnpm-store

Category: 后端 / 构建依赖 / 依赖卫生
Severity: warn

#### Description

定期扫描项目根 / 盘根，发现与统一 `store-dir` 不一致的孤儿 `.pnpm-store` 目录须清理。清理前须确认该孤儿**未被任何 `node_modules/.modules.yaml` 的 `storeDir` 引用**（无活引用），再删除（受 safe-delete 钩子约束时走放行路径）。命中 `forbidden_store_dirs`（默认 `.pnpm-store`）且与 `canonical_store_dir` 不一致即违规（BR-095-2，建议级）。

## Configuration Parameters

> 全部参数从 [config/review-config.md](../config/review-config.md) 的"包管理器 store 卫生审查参数（BR-095）"节读取，本规则文件不硬编码任何值。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dependency_store_hygiene.enabled` | `true` | 启用包管理器 store 卫生审查 |
| `dependency_store_hygiene.store_dir_key` | `store-dir` | `.npmrc` 中用于收敛 store 的键名 |
| `dependency_store_hygiene.forbidden_store_dirs` | `.pnpm-store` | 禁止散落的 store 目录名（命中即孤儿） |
| `dependency_store_hygiene.canonical_store_dir` | `D:\.pnpm-store` | 统一 store 绝对路径（与孤儿对比，命中则合法） |
| `dependency_store_hygiene.scan_root` | `项目根` | 扫描孤儿 store 的根目录 |
| `dependency_store_hygiene.severity` | `warn` | 散落缓存 / 缺收敛键的违规级别（CI 前置可升 error） |
