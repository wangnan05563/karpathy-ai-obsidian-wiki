# Tauri 构建脚本 SPA 构建步骤规则（CODING-051）

> 复盘来源：Tauri 构建脚本 `tauri-build-debug.ps1` 直接调用 `cargo build`，未先构建前端 SPA，导致 Tauri 加载到旧版前端产物，新功能不生效。又因用 `pnpm run build`（项目根脚本）触发递归构建 tauri，陷入死循环。
> 所有可变参数从 [config/coding-standards-config.md](../config/coding-standards-config.md) 的 `tauri_build_script` 字段读取，禁止在规则文件中硬编码脚本名或路径。

## 触发场景

- 编写或修改 Tauri 构建脚本（`tauri-build-debug.ps1` / `tauri-build-release.ps1`）
- Tauri 构建后加载的前端版本与源码不一致
- 构建脚本调用 `pnpm run build` 触发递归构建
- 构建脚本未清理旧产物，导致新旧产物混杂
- Code Review 构建脚本时

## 不适用场景

- 纯 Rust Tauri 项目（无前端 SPA）
- CI/CD 流水线（通常有独立的 build 阶段编排）
- Electron 的 `electron-builder`（构建流程不同）
- Vite 的 `vite build` 直接调用（无递归风险）

## 规则

### 规则 1：构建脚本必须包含 SPA 构建步骤

`tauri-build-debug.ps1` 与 `tauri-build-release.ps1` 都必须有显式的「构建 SPA」步骤，且在 `cargo build` 之前执行。Tauri 的 `cargo build` 不会自动触发前端构建。

### 规则 2：用 `pnpm --filter` 精确构建目标包

必须用 `pnpm --filter @karpathy-wiki/web build` 精确构建 web 包，禁止用 `pnpm run build`（项目根脚本）。项目根的 `build` 脚本可能调用 `tauri build`，导致递归构建死循环。

### 规则 3：构建前清理旧产物

构建前必须清理 `services/api/public/` 下的旧 SPA 产物（HTML/JS/CSS），避免新旧产物混杂导致加载到过期版本。

### 规则 4：SPA 产物双重验证

构建后必须双重验证：
- **mtime 验证**：对比源码 mtime 与产物 mtime，源码新于产物 → 构建未成功，需重建
- **JS chunk 特征验证**：在产物 JS chunk 中搜索新增的关键字符串（如新组件的 class 名、新函数名），确认新代码已进入构建

### 为什么

- **SPA 构建必要性**：Tauri 的 `cargo build` 仅编译 Rust 代码，前端 SPA 必须由 Vite/webpack 独立构建。漏掉 SPA 构建会让 Tauri 加载到上次的旧产物，新功能"消失"但无报错，极难排查
- **递归构建风险**：项目根 `package.json` 的 `build` 脚本常包含 `tauri build`，直接 `pnpm run build` 会再次触发 Tauri 构建，Tauri 构建又触发 SPA 构建...形成无限递归
- **旧产物污染**：Vite 默认不清空输出目录（除非配置 `emptyOutDir`），删除某文件后旧 chunk 仍残留，可能导致 import 解析到已删除的模块
- **mtime 验证可靠性**：比"构建命令退出码 0"更可靠，能捕获"构建命令成功但产物未更新"的边缘场景（如 Vite 缓存命中但源码已变）

## 判断逻辑

```
Tauri 构建脚本必须包含的步骤:
  STEP 1: [清理旧产物] 删除 services/api/public/ 下的 SPA 产物
  STEP 2: [构建 SPA] pnpm --filter @karpathy-wiki/web build
  STEP 3: [SPA 产物验证]
      3a. mtime 验证：源码 mtime ≤ 产物 mtime
      3b. JS chunk 特征验证：搜索关键字符串存在
  STEP 4: [构建 Tauri] cargo build（debug）或 cargo build --release（release）
  STEP 5: [Tauri 产物验证] 检查 .exe 文件生成

违规诊断:
  IF 脚本无 [构建 SPA] 步骤 → CODING-051 违规
  IF 用 pnpm run build 而非 pnpm --filter → 递归构建风险
  IF 无 [清理旧产物] 步骤 → 新旧混杂风险
  IF 无 [SPA 产物验证] → 构建失败未察觉风险
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_build_script.enabled` | `true` | 是否启用构建脚本守卫 |
| `tauri_build_script.severity` | `error` | 违规严重级别 |
| `tauri_build_script.required_scripts` | `tauri-build-debug.ps1, tauri-build-release.ps1` | 必须包含 SPA 构建步骤的脚本列表（逗号分隔） |
| `tauri_build_script.spa_build_command` | `pnpm --filter @karpathy-wiki/web build` | SPA 构建命令（用 --filter 精确构建） |
| `tauri_build_script.forbidden_build_command` | `pnpm run build` | 禁止的构建命令（递归构建风险） |
| `tauri_build_script.spa_output_dir` | `services/api/public/` | SPA 产物输出目录 |
| `tauri_build_script.spa_source_dir` | `packages/web/src/` | SPA 源码目录（用于 mtime 对比） |
| `tauri_build_script.cargo_build_command_debug` | `cargo build` | debug 构建 cargo 命令 |
| `tauri_build_command_release` | `cargo build --release` | release 构建 cargo 命令 |
| `tauri_build_script.cleanup_patterns` | `*.html, assets/*.js, assets/*.css` | 旧产物清理 glob（逗号分隔） |
| `tauri_build_script.key_strings_check` | `true` | 是否验证 JS chunk 含关键字符串 |
| `tauri_build_script.key_string_examples` | `FloatingChat, RecentLog, TauriMode` | 关键字符串示例（实际由任务动态确定） |
| `tauri_build_script.mtime_check_enabled` | `true` | 是否启用源码 mtime vs 产物 mtime 对比 |
| `tauri_build_script.expected_binary_path` | `target/debug/karpathy-wiki.exe` | Tauri 构建产物二进制路径 |

## 正确示例

### tauri-build-debug.ps1

```powershell
# tauri-build-debug.ps1
# Tauri debug 构建脚本：必须按 清理→SPA构建→验证→Tauri构建 顺序执行
$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot/.."
$spaOutputDir = Join-Path $projectRoot "services/api/public"
$spaSourceDir = Join-Path $projectRoot "packages/web/src"

# STEP 1: [清理旧产物] 避免新旧产物混杂
Write-Host "[1/5] 清理旧 SPA 产物: $spaOutputDir"
if (Test-Path $spaOutputDir) {
    Get-ChildItem $spaOutputDir -Recurse | Where-Object {
        $_.Extension -in '.html', '.js', '.css'
    } | Remove-Item -Force
}

# STEP 2: [构建 SPA] 用 --filter 精确构建，避免 pnpm run build 递归
Write-Host "[2/5] 构建 SPA (pnpm --filter @karpathy-wiki/web build)"
# 注意：禁止用 pnpm run build，项目根 build 脚本会触发 tauri build 递归
$spaResult = Start-Process pnpm -ArgumentList "--filter", "@karpathy-wiki/web", "build" -NoNewWindow -Wait -PassThru
if ($spaResult.ExitCode -ne 0) {
    throw "SPA 构建失败，退出码: $($spaResult.ExitCode)"
}

# STEP 3a: [mtime 验证] 源码 mtime 必须 ≤ 产物 mtime
Write-Host "[3/5] 验证 SPA 产物 mtime"
$sourceLatestMtime = (Get-ChildItem $spaSourceDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
$productLatestMtime = (Get-ChildItem $spaOutputDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
if ($sourceLatestMtime -gt $productLatestMtime) {
    throw "SPA 产物过期：源码最新 mtime ($sourceLatestMtime) > 产物最新 mtime ($productLatestMtime)，需重建"
}

# STEP 3b: [JS chunk 特征验证] 搜索关键字符串确认新代码进入构建
Write-Host "[4/5] 验证 JS chunk 特征字符串"
# 关键字符串由实际任务动态确定，这里以 FloatingChat 为例
$keyStrings = @("FloatingChat", "RecentLog", "TauriMode")
$jsFiles = Get-ChildItem (Join-Path $spaOutputDir "assets") -Filter "*.js" -ErrorAction SilentlyContinue
if (-not $jsFiles) {
    throw "SPA 产物 assets 目录无 JS 文件"
}
$allJsContent = $jsFiles | Get-Content -Raw | Out-String
foreach ($key in $keyStrings) {
    if ($allJsContent -notmatch [regex]::Escape($key)) {
        throw "JS chunk 缺少关键字符串: $key（新代码未进入构建）"
    }
}

# STEP 4: [构建 Tauri] cargo build
Write-Host "[5/5] 构建 Tauri (cargo build)"
$cargoResult = Start-Process cargo -ArgumentList "build" -NoNewWindow -Wait -PassThru -WorkingDirectory $projectRoot
if ($cargoResult.ExitCode -ne 0) {
    throw "Tauri 构建失败，退出码: $($cargoResult.ExitCode)"
}

Write-Host "✅ Tauri debug 构建成功"
```

### tauri-build-release.ps1

```powershell
# tauri-build-release.ps1
# Release 构建：与 debug 脚本结构相同，仅 cargo 命令改为 --release
$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path "$PSScriptRoot/.."
$spaOutputDir = Join-Path $projectRoot "services/api/public"

# STEP 1: [清理旧产物]
if (Test-Path $spaOutputDir) {
    Get-ChildItem $spaOutputDir -Recurse | Where-Object {
        $_.Extension -in '.html', '.js', '.css'
    } | Remove-Item -Force
}

# STEP 2: [构建 SPA]
$spaResult = Start-Process pnpm -ArgumentList "--filter", "@karpathy-wiki/web", "build" -NoNewWindow -Wait -PassThru
if ($spaResult.ExitCode -ne 0) { throw "SPA 构建失败" }

# STEP 3: [验证]（与 debug 脚本相同，省略）

# STEP 4: [构建 Tauri] --release
$cargoResult = Start-Process cargo -ArgumentList "build", "--release" -NoNewWindow -Wait -PassThru -WorkingDirectory $projectRoot
if ($cargoResult.ExitCode -ne 0) { throw "Tauri release 构建失败" }

Write-Host "✅ Tauri release 构建成功"
```

## 错误示例

### 错误 1：无 SPA 构建步骤

```powershell
# ❌ 直接 cargo build，未构建 SPA，Tauri 加载旧产物
cargo build
```

### 错误 2：用 `pnpm run build` 触发递归

```powershell
# ❌ 项目根 package.json 的 build 脚本可能调用 tauri build，形成递归
pnpm run build
cargo build
```

### 错误 3：未清理旧产物

```powershell
# ❌ Vite 不清空输出目录，删除的模块文件仍残留
pnpm --filter @karpathy-wiki/web build
cargo build
# 结果：Tauri 可能加载到已删除模块的旧 chunk
```

### 错误 4：仅依赖退出码，不验证产物

```powershell
# ❌ Vite 缓存命中时退出码 0 但产物未更新
pnpm --filter @karpathy-wiki/web build
if ($LASTEXITCODE -eq 0) {
    cargo build  # 可能加载到旧产物
}
```

## 错误诊断速查表

| 现象 | 根因 | 修复动作 |
|------|------|---------|
| Tauri 加载的前端无新功能 | 脚本无 SPA 构建步骤 | 在 cargo build 前追加 `pnpm --filter <pkg> build` |
| 构建脚本卡死/无限循环 | 用 `pnpm run build` 触发递归 | 改用 `pnpm --filter <pkg> build` 精确构建 |
| 加载到已删除模块的旧 chunk | 未清理旧产物 | 构建前清理 `spa_output_dir` |
| 退出码 0 但前端无新功能 | Vite 缓存命中，产物未更新 | 追加 mtime 验证 + 关键字符串验证 |
| JS chunk 中找不到新组件 | 新代码未进入构建 | 检查 Vite 入口配置，确认新组件被 import |

## 适用场景

- Tauri 2.x 项目构建脚本（debug / release）
- Monorepo 结构的 Tauri 项目（前端在独立 package）
- 需要确保前端产物与源码同步的场景
- CI/CD 流水线的 Tauri 构建阶段

## 适配新项目

- **单包 Tauri 项目**（前端在根目录）：`spa_build_command` 改为 `pnpm run build:web`（独立脚本，避免递归）
- **npm 项目**：`spa_build_command` 改为 `npm run build --workspace <pkg>`
- **yarn workspace 项目**：`spa_build_command` 改为 `yarn workspace <pkg> build`
- **webpack 项目**：`spa_output_dir` 改为 webpack 配置的 `output.path`
- **无前端 Tauri 项目**：将 `enabled` 设为 `false`
- **CI 环境**：构建脚本同样适用，CI 仅替代手动调用
