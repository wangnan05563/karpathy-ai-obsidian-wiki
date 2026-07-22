# Tauri 构建脚本审查规则（BR-038~040）

> 复盘来源：Tauri 2.x 桌面应用集成中，构建脚本 `tauri-build-debug.ps1` / `tauri-build-release.ps1` 漏写 SPA 构建步骤、用错 pnpm 子包构建命令（递归触发 tauri 构建）、未清理后端 public 旧产物、未做磁盘空间预检查导致构建中途失败且产物残缺。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"Tauri 构建脚本审查参数（tauri_build_script）"章节读取，禁止在本规则文件硬编码具体包名、路径或阈值。

## Trigger Keywords

tauri-build-debug.ps1, tauri-build-release.ps1, tauri build, pnpm --filter, services/api/public/, index.html, SPA 构建步骤, 磁盘空间预检查, emptyOutDir, cargo tauri, tauri build --debug, tauri build --release

## Rules

### BR-038: Tauri 构建脚本必须包含 SPA 构建步骤且使用 `pnpm --filter` 子包构建

- **Severity**: critical
- **Description**: Tauri 桌面应用打包前必须先构建前端 SPA，否则 Tauri 加载 WebView 时会拿到空目录或残留旧产物导致白屏。构建 SPA 时必须用 `pnpm --filter <spa_package_name> build`（通过 `--filter` 指定子包），**禁止**用 `pnpm run build`（在 monorepo 根目录会触发根 package.json 的 `build` 脚本，进而递归调用 `tauri build`，形成循环依赖并最终打包到错误的产物路径）。评审时确认每个 `tauri-build-*.ps1` 脚本中存在 SPA 构建步骤，且命令形式为 `pnpm --filter <spa_package_name> build`。
- **Suggested fix**:

```powershell
# 错误 1：完全缺失 SPA 构建步骤
# tauri-build-debug.ps1 直接执行 cargo tauri build --debug
cargo tauri build --debug   # ❌ WebView 加载空 public/

# 错误 2：用 pnpm run build 触发根脚本（递归）
pnpm run build              # ❌ 根 package.json 的 build 会调用 tauri build，形成循环
cargo tauri build --debug

# 正确：用 --filter 指定 SPA 子包构建
pnpm --filter @karpathy-wiki/web build   # ✅ 仅构建前端 SPA，不触发 tauri
cargo tauri build --debug
```

### BR-039: Tauri 构建脚本构建前必须清理后端 public 旧产物并验证 SPA 产物

- **Severity**: critical
- **Description**: Tauri 构建脚本在执行 SPA 构建前必须清理后端 `spa_artifact_path`（如 `services/api/public/`）下的旧产物，避免 hash 文件名变更后旧 `index-oldHash.js` 残留、WebView 加载到过期 bundle。SPA 构建完成后必须验证 `index.html` 存在性（`Test-Path`），缺失则中断构建并报错——否则后续 `cargo tauri build` 会把空目录打包进二进制，运行时白屏但构建不报错，问题难以定位。评审时确认脚本中存在"清理 → 构建 → 验证"三步骤。
- **Suggested fix**:

```powershell
# 错误：未清理旧产物、未验证 SPA 产物
pnpm --filter @karpathy-wiki/web build
cargo tauri build --debug   # ❌ 旧 hash 文件残留，或 public 为空导致白屏

# 正确：清理 → 构建 → 验证
$ErrorActionPreference = 'Stop'

# 1. 清理后端 public 旧产物（避免旧 hash 文件残留）
$publicDir = "services/api/public"
if (Test-Path $publicDir) {
    Remove-Item -Path "$publicDir/*" -Recurse -Force
    Write-Host "已清理 $publicDir 旧产物"
}

# 2. 构建 SPA（用 --filter 指定子包，避免递归触发 tauri）
pnpm --filter @karpathy-wiki/web build

# 3. 验证 SPA 产物（index.html 存在性）
$indexHtml = Join-Path $publicDir "index.html"
if (-not (Test-Path $indexHtml)) {
    throw "SPA 构建失败：$indexHtml 不存在，请检查前端构建配置"
}
Write-Host "SPA 产物验证通过：$indexHtml 存在"

# 4. 构建 Tauri 桌面应用
cargo tauri build --debug
```

### BR-040: Tauri 构建脚本必须做磁盘空间预检查

- **Severity**: suggestion
- **Description**: Tauri 桌面应用构建（debug + release）会产生大量中间产物（Rust 编译缓存、SPA bundle、Tauri 打包的安装包等），磁盘空间不足会导致构建中途失败、产物残缺、Cargo 锁文件损坏等不可恢复问题。构建脚本必须在前置检查阶段调用磁盘空间预检查：debug 模式至少需要 `debug_min_gb` GB，release 模式至少需要 `release_min_gb` GB（阈值从 config 读取）。空间不足时应中断构建并给出明确的清理建议（如 `cargo cache -a` / 清理 `target/` 旧产物），不能让构建在中途因空间不足失败。
- **Suggested fix**:

```powershell
# 错误：未做磁盘空间预检查，构建中途因磁盘满失败
pnpm --filter @karpathy-wiki/web build
cargo tauri build --release   # ❌ 编译到 80% 时磁盘满，产物残缺

# 正确：构建前预检查磁盘空间
$ErrorActionPreference = 'Stop'

# 从 config 读取阈值（示例值：debug=3GB, release=5GB）
$requiredGb = if ($BuildMode -eq 'release') { 5 } else { 3 }
$drive = (Get-Item $PSScriptRoot).PSDrive
$freeGb = [math]::Round($drive.Free / 1GB, 2)
if ($freeGb -lt $requiredGb) {
    throw "磁盘空间不足：当前 $freeGb GB，至少需要 $requiredGb GB。请执行 cargo cache -a 或清理 target/ 目录"
}
Write-Host "磁盘空间检查通过：$freeGb GB（要求 >= $requiredGb GB）"

pnpm --filter @karpathy-wiki/web build
cargo tauri build --release
```

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `tauri_build_script.enabled` | `true` | 是否启用本组规则（BR-038~040） |
| `tauri_build_script.severity_br038` | `critical` | BR-038 SPA 构建步骤缺失违规严重级别 |
| `tauri_build_script.severity_br039` | `critical` | BR-039 旧产物清理 + SPA 产物验证缺失违规严重级别 |
| `tauri_build_script.severity_br040` | `suggestion` | BR-040 磁盘空间预检查缺失违规严重级别 |
| `tauri_build_script.build_scripts` | `tauri-build-debug.ps1,tauri-build-release.ps1` | Tauri 构建脚本文件名列表（逗号分隔，相对项目根） |
| `tauri_build_script.spa_package_name` | `@karpathy-wiki/web` | SPA 子包名（`pnpm --filter` 参数） |
| `tauri_build_script.spa_artifact_path` | `services/api/public/` | SPA 构建产物输出目录（相对项目根） |
| `tauri_build_script.spa_entry_file` | `index.html` | SPA 入口文件名（用于存在性验证） |
| `tauri_build_script.forbidden_build_command` | `pnpm run build` | 禁用的根目录构建命令（会递归触发 tauri 构建） |
| `tauri_build_script.required_build_command_pattern` | `pnpm --filter <pkg> build` | 必需的 SPA 构建命令模式（`<pkg>` 占位符运行时替换为 `spa_package_name`） |
| `tauri_build_script.debug_min_gb` | `3` | debug 模式磁盘空间下限（GB） |
| `tauri_build_script.release_min_gb` | `5` | release 模式磁盘空间下限（GB） |
| `tauri_build_script.disk_space_cleanup_hint` | `cargo cache -a; 清理 target/ 目录` | 空间不足时的清理建议命令（分号分隔多条） |
| `tauri_build_script.tauri_build_commands` | `cargo tauri build --debug,cargo tauri build --release` | Tauri 打包命令列表（逗号分隔，用于识别 tauri 构建步骤） |

## 检查方式

1. 用 Glob 检索 `tauri_build_script.build_scripts` 列表中的脚本文件是否存在。
2. 对每个存在的脚本，用 Read 读取完整内容。
3. **BR-038 检查**：
   - 用 Grep 在脚本内容中检索 `pnpm --filter` 或 `tauri_build_script.required_build_command_pattern`：
     - 命中 → 继续
     - 未命中 → BR-038 违规（缺失 SPA 构建步骤）
   - 用 Grep 检索 `tauri_build_script.forbidden_build_command`（如 `pnpm run build`）：
     - 命中 → BR-038 违规（使用了递归触发 tauri 的根命令）
4. **BR-039 检查**：
   - 用 Grep 检索 `Remove-Item.*<spa_artifact_path>` 或 `Clear-Content.*<spa_artifact_path>`：
     - 命中 → 旧产物清理步骤存在
     - 未命中 → BR-039 违规（未清理后端 public 旧产物）
   - 用 Grep 检索 `Test-Path.*index.html` 或 `Test-Path.*<spa_entry_file>`：
     - 命中 → SPA 产物验证步骤存在
     - 未命中 → BR-039 违规（未验证 SPA 产物）
5. **BR-040 检查**：
   - 用 Grep 检索 `PSDrive` / `Get-PSDrive` / `$drive.Free` / `disk space` / `磁盘空间`：
     - 命中 → 磁盘空间预检查存在
     - 未命中 → BR-040 违规（未做磁盘空间预检查）
   - 若命中，进一步检查阈值是否从 config 读取（避免硬编码 `3` 或 `5` 字面量）：
     - 命中字面量 `3` / `5` 且未引用 config → suggestion 级别 warning（建议参数化）

## 正确示例

```powershell
# tauri-build-debug.ps1 —— 完整合规脚本
$ErrorActionPreference = 'Stop'

# 1. 磁盘空间预检查
$requiredGb = 3   # debug 模式下限（建议从 config 读取）
$drive = (Get-Item $PSScriptRoot).PSDrive
$freeGb = [math]::Round($drive.Free / 1GB, 2)
if ($freeGb -lt $requiredGb) {
    throw "磁盘空间不足：当前 $freeGb GB，至少需要 $requiredGb GB。请执行 cargo cache -a 或清理 target/ 目录"
}

# 2. 清理后端 public 旧产物
$publicDir = "services/api/public"
if (Test-Path $publicDir) {
    Remove-Item -Path "$publicDir/*" -Recurse -Force
}

# 3. 构建 SPA（用 --filter 指定子包）
pnpm --filter @karpathy-wiki/web build

# 4. 验证 SPA 产物
$indexHtml = Join-Path $publicDir "index.html"
if (-not (Test-Path $indexHtml)) {
    throw "SPA 构建失败：$indexHtml 不存在"
}

# 5. 构建 Tauri 桌面应用
cargo tauri build --debug
```

## 错误示例

```powershell
# 错误 1：缺失 SPA 构建步骤（BR-038 违规）
# tauri-build-debug.ps1 直接执行
cargo tauri build --debug
# ❌ WebView 加载空 services/api/public/ → 白屏

# 错误 2：用 pnpm run build 递归触发 tauri（BR-038 违规）
pnpm run build
cargo tauri build --debug
# ❌ 根 package.json 的 build 脚本调用 tauri build，形成循环

# 错误 3：未清理旧产物（BR-039 违规）
pnpm --filter @karpathy-wiki/web build
cargo tauri build --debug
# ❌ 旧 index-oldHash.js 残留，WebView 可能加载过期 bundle

# 错误 4：未验证 SPA 产物（BR-039 违规）
Remove-Item -Path "services/api/public/*" -Recurse -Force
pnpm --filter @karpathy-wiki/web build
cargo tauri build --debug
# ❌ SPA 构建失败但未中断，cargo tauri 把空目录打包进二进制 → 运行时白屏但构建不报错

# 错误 5：未做磁盘空间预检查（BR-040 违规）
pnpm --filter @karpathy-wiki/web build
cargo tauri build --release
# ❌ release 编译到 80% 时磁盘满，产物残缺且 Cargo 锁文件损坏
```

## 适配新项目

- **不同包管理器项目**：若用 npm / yarn，`required_build_command_pattern` 调整为 `npm run build --workspace <pkg>` / `yarn workspace <pkg> build`，`forbidden_build_command` 调整为对应的根目录命令（如 `npm run build` 在根目录会触发所有 workspace 的 build）。
- **不同 SPA 框架项目**：`spa_entry_file` 调整为实际入口文件名（如 Next.js 用 `.next/`，但 Tauri 集成 Next.js 较少，多数用 Vite + React/Vue）。
- **不同 Tauri 版本项目**：Tauri 1.x 用 `tauri build` 命令，Tauri 2.x 用 `cargo tauri build`，`tauri_build_commands` 参数按实际版本调整。
- **CI/CD 集成项目**：CI 脚本（如 GitHub Actions / GitLab CI）同样适用本规则，将 `build_scripts` 调整为 CI 配置文件路径（如 `.github/workflows/build.yml`），其余检查项不变。
- **多 SPA 子包项目**：若 Tauri 应用加载多个 SPA 子包，`spa_package_name` 用逗号分隔多个包名，每个包名都须用 `--filter` 单独构建并验证产物。
