# Rule Catalog — 包管理器 store 卫生（显式 store-dir 收敛）(CODING-PNPM-STORE-HYGIENE)

通用工程/依赖管理规范：在 **WorkBuddy safe-delete 沙箱钩子（fail-closed）** 等会拦截文件系统 rename/探测操作的环境中，pnpm 的"主目录探测"（`storePathRelativeToHome` 里的 `rename` 临时操作）会被拦截并抛 `EPERM`，导致 pnpm **退化为在当前盘根创建 `.pnpm-store`**。这会使缓存散落在多个项目的根目录，既污染工作区又让 `node_modules` 解析不到统一 store。规范：**显式在全局 `.npmrc` 写 `store-dir` 收敛到统一路径**，并定期检测/清理散落的孤儿 `.pnpm-store`。本规则是前端审查 `wiki-frontend-code-review` FR-085 与后端审查 `wiki-backend-code-review` BR-095 的上位规范，亦对应 wiki-auto-testing `dependency_store_hygiene_check` 配置化步骤。

> 复盘来源：项目根目录（`D:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\.pnpm-store`）曾散落一份 pnpm 缓存（Jul 11 创建、无引用），正是 safe-delete 钩子打断 pnpm 主目录探测后的退化产物。根因：pnpm 探测 home 目录可写性时用的 `rename` 临时操作被沙箱 `genie-safe-delete.cjs` 以 fail-closed 拦截 → `EPERM` → pnpm 无法确认 home store 路径 → 退化为"当前盘根建 `.pnpm-store`"。统一方案：全局 `.npmrc` 写 `store-dir=D:\.pnpm-store`，`pnpm store path` 在任意 cwd 均返回该值，散落缓存可安全删除。

## Scope

- Covers: pnpm（及类似依赖严格 store 管理的包管理器）在**受限文件系统环境**下的 store 收敛；孤儿 store 检测与清理；CI / 开发环境初始化对 `store-dir` 的断言。
- Does NOT cover: 纯 npm/yarn（无严格 content-addressable store 或不受该钩子影响）；已在 `.npmrc` 显式收敛且确认无孤儿目录的环境。

## Rules

### CODING-PNPM-STORE-HYGIENE-1: 显式 store-dir 收敛到统一路径

IsUrgent: False（建议级，CI 前置）
Category: 依赖管理 / 环境一致性

#### Description

在全局 `.npmrc`（`~/.npmrc`）显式声明 `store-dir=<统一绝对路径>`，使 pnpm 在任何 cwd 都收敛到同一 store，避免依赖沙箱主目录探测。声明后须用 `pnpm store path` 验证返回值为该路径（exit 0）。**不要依赖 pnpm 自动探测 home**——受限环境下探测会被拦截。

#### Suggested Fix

```text
# ~/.npmrc
store-dir=D:\.pnpm-store
```
```bash
# 验证：任意 cwd 均返回 D:\.pnpm-store\v11
pnpm store path
```

### CODING-PNPM-STORE-HYGIENE-2: 检测并清理孤儿 .pnpm-store

IsUrgent: False（建议级）
Category: 工作区卫生

#### Description

定期扫描项目根 / 盘根，发现与统一 `store-dir` 不一致的孤儿 `.pnpm-store` 目录须清理。清理前须确认：该孤儿**未被任何 `node_modules/.modules.yaml` 的 `storeDir` 引用**（即无活引用），再删除。删除受沙箱 safe-delete 钩子约束时，须用钩子放行的方式（写全新目录/移动到新路径，或参考 wiki-code-dev 的 windows-file-operation-rule 与 PowerShell 约束）。

#### Suggested Fix

```text
# 1. 确认孤儿无引用（storeDir 指向统一 store，而非孤儿）
grep "storeDir" node_modules/.modules.yaml   # 期望 D:\.pnpm-store\v11

# 2. 删除孤儿（受 safe-delete 钩子时走钩子放行路径，如 robocopy 清空 + Delete 空壳）
#    详见 wiki-code-dev references/windows-file-operation-rule.md
```

### CODING-PNPM-STORE-HYGIENE-3: CI / 环境初始化须断言 store-dir 收敛

IsUrgent: False（建议级）
Category: CI 前置检查

#### Description

CI 与开发环境初始化步骤须包含"store-dir 收敛断言"：检查全局/项目 `.npmrc` 存在 `store-dir` 键，且**不存在**与统一 store 不一致的孤儿 `.pnpm-store`。未收敛则提前失败，避免构建在散落缓存上静默运行、或在受限环境退化。本规则对应 wiki-auto-testing `dependency_store_hygiene_check`（配置化：扫描根、禁止目录名、要求 npmrc 键，零硬编码）。

#### Suggested Fix

```text
# CI 前置（伪代码，参数全部来自配置）
assert_npmrc_has("store-dir")            # 缺收敛键 → 失败
assert_no_orphan_store(".pnpm-store")    # 项目/盘根存在孤儿 → 失败
```

## Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `pnpm_store_hygiene.enabled` | `true` | 启用 store 卫生审查 |
| `pnpm_store_hygiene.store_dir_key` | `store-dir` | `.npmrc` 中用于收敛 store 的键名 |
| `pnpm_store_hygiene.forbidden_store_dirs` | `.pnpm-store` | 禁止散落的 store 目录名（命中即孤儿） |
| `pnpm_store_hygiene.canonical_store_dir` | `D:\.pnpm-store` | 统一 store 绝对路径（与孤儿对比，命中则合法） |
| `pnpm_store_hygiene.scan_root` | 项目根 | 扫描孤儿 store 的根目录 |
| `pnpm_store_hygiene.severity` | `warn` | 散落缓存/缺收敛键的违规级别（CI 前置可升 error） |
