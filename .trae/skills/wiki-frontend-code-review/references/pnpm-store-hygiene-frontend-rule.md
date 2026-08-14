# Rule Catalog — 包管理器 store 卫生（前端构建依赖）(Frontend, FR-085)

前端「包管理器 store 卫生」审查规则：前端构建（`vite` 经 `node_modules` 解析 pnpm store）依赖**健康且收敛的 pnpm store**。在 WorkBuddy safe-delete 沙箱钩子（fail-closed）等会拦截 rename/探测操作的环境中，pnpm 主目录探测被打断会退化为在当前盘根建 `.pnpm-store`，既污染工作区又让前端 `node_modules` 解析不到统一 store，导致构建在散落缓存上静默运行或失败。规范：全局 `.npmrc` 须**显式 `store-dir` 收敛**，且项目/盘根**不得存在孤儿 `.pnpm-store`**。所有参数从 `config/review-config.md` 读取，禁止硬编码绝对路径。

> 复盘来源：项目根目录曾散落一份 pnpm 缓存（Jul 11 创建、无引用），正是 safe-delete 钩子打断 pnpm 主目录探测后的退化产物。统一方案：全局 `.npmrc` 写 `store-dir=D:\.pnpm-store`，`pnpm store path` 在任意 cwd 均返回该值；孤儿确认无 `node_modules/.modules.yaml` 引用后删除。对应 wiki-code-dev CODING-PNPM-STORE-HYGIENE / 后端 BR-095 / wiki-auto-testing `dependency_store_hygiene_check`。

## Scope

- Covers: 前端构建依赖的 pnpm store 收敛；`.npmrc` 的 `store-dir` 收敛键；项目/盘根孤儿 `.pnpm-store` 检测；CI / 环境初始化对 store 收敛的断言。
- Does NOT cover: 纯 npm/yarn（无严格 content-addressable store 或不受该钩子影响）；已显式收敛且无孤儿目录的环境。

## Rules

### FR-085-1: 全局 `.npmrc` 须显式 store-dir 收敛

IsUrgent: False
Category: Dependency Store Hygiene

#### Description

全局 `.npmrc`（`~/.npmrc`）须显式声明 `store-dir=<统一绝对路径>`，使 pnpm 在任何 cwd 都收敛到同一 store，避免依赖沙箱主目录探测。声明后须 `pnpm store path` 验证返回该路径。`store_dir_key`（默认 `store-dir`）缺失即违规（FR-085-1，建议级；CI 前置可升 Critical）。

```text
# ~/.npmrc
store-dir=D:\.pnpm-store
```

### FR-085-2: 项目/盘根不得存在孤儿 .pnpm-store

IsUrgent: False
Category: Dependency Store Hygiene

#### Description

定期扫描项目根 / 盘根，发现与统一 `store-dir` 不一致的孤儿 `.pnpm-store` 目录须清理。清理前须确认该孤儿**未被任何 `node_modules/.modules.yaml` 的 `storeDir` 引用**（无活引用），再删除（受 safe-delete 钩子约束时走放行路径）。命中 `forbidden_store_dirs`（默认 `.pnpm-store`）且与 `canonical_store_dir` 不一致即违规（FR-085-2，建议级）。

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `pnpm_store_hygiene_frontend.enabled` | `true` | 启用本组规则（FR-085） |
| `pnpm_store_hygiene_frontend.store_dir_key` | `store-dir` | `.npmrc` 中用于收敛 store 的键名 |
| `pnpm_store_hygiene_frontend.forbidden_store_dirs` | `.pnpm-store` | 禁止散落的 store 目录名（命中即孤儿） |
| `pnpm_store_hygiene_frontend.canonical_store_dir` | `D:\.pnpm-store` | 统一 store 绝对路径（与孤儿对比，命中则合法） |
| `pnpm_store_hygiene_frontend.scan_root` | 项目根 | 扫描孤儿 store 的根目录 |
| `pnpm_store_hygiene_frontend.severity` | `warn` | 散落缓存/缺收敛键的违规级别（CI 前置可升 error） |
