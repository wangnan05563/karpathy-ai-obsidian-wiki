# SPA 产物验证法

> 本文档提供 Tauri 桌面应用构建前的 SPA 产物验证方法，防止源码与产物不同步导致 Tauri 加载旧版前端。
> 所有参数从 `config.yaml` 的 `spa` 节读取，不在代码中硬编码路径或特征字符串。

## 1. 验证目标

确保 Tauri 加载的 SPA 产物与当前源码一致，避免以下场景：
- 源码已修改但未重新构建 → Tauri 加载旧版前端，新功能不生效
- 构建产物被意外删除 → Tauri 启动后白屏
- 构建产物被旧版覆盖（如 CI 缓存） → 版本回退难以察觉

## 2. 验证方法

### 2.1 时间戳对比法（主方法）

**原理**：通过比较源码文件的最后修改时间（mtime）与产物文件的 mtime，判断是否需要重新构建。

**验证流程**：
1. 遍历 `spa.source_dirs` 中配置的源码目录
2. 对每个目录递归扫描 `spa.source_extensions`（默认 `[".ts", ".tsx", ".vue", ".js", ".jsx"]`）的文件
3. 取所有源码文件 mtime 的最大值 `source_max_mtime`
4. 取 `spa.output_dir/index.html` 的 mtime 作为 `artifact_mtime`
5. 若 `source_max_mtime > artifact_mtime` → 判定需重建

**配置示例**：
```yaml
spa:
  package_name: "karpathy-wiki-frontend"
  output_dir: "karpathy-wiki/api/public"
  source_dirs:
    - "karpathy-wiki/frontend/src"
  source_extensions:
    - ".ts"
    - ".tsx"
    - ".vue"
    - ".js"
    - ".jsx"
  force_rebuild: false
  # 产物验证的关键文件（用于 mtime 比较，默认 index.html）
  artifact_marker_file: "index.html"
```

**通过条件**：
- `artifact_mtime` ≥ `source_max_mtime`，或
- `spa.force_rebuild: true` 时已触发重建并重新验证

**失败修复建议**：
- 执行 `tauri.build_script_path` 重新构建 SPA
- 检查 `spa.output_dir` 是否被 `.gitignore` 排除导致构建跳过
- 检查构建脚本的 `outDir` 是否与 `spa.output_dir` 一致

**输出格式**：
```
[SPA-Artifact] source_max_mtime: 2026-07-22 14:30:00 (karpathy-wiki/frontend/src/App.vue)
[SPA-Artifact] artifact_mtime:   2026-07-22 13:00:00 (karpathy-wiki/api/public/index.html)
[SPA-Artifact] VERDICT: REBUILD_NEEDED (source is newer than artifact)
[SPA-Artifact] SUGGESTION: Run "karpathy-wiki/scripts/前端构建.bat" to rebuild SPA
```

### 2.2 JS chunk 特征验证法（辅助方法）

**原理**：在 SPA 产物的 JS chunk 文件中搜索关键字符串，验证新功能已正确编译到产物中。

**适用场景**：
- 时间戳对比通过，但运行时仍出现"功能不生效"问题
- CI 环境中文件 mtime 可能被重置（如 `git checkout` 后 mtime 不反映实际修改）
- 怀疑产物被旧版覆盖

**验证流程**：
1. 列出 `spa.output_dir` 下所有 `*.js` 文件（含子目录）
2. 对 `spa.key_strings` 中的每个关键字符串：
   - 在所有 JS 文件中搜索该字符串
   - 记录命中的文件路径与出现次数
3. 若任一关键字符串未命中 → 判定产物不完整

**配置示例**：
```yaml
spa:
  # 关键字符串列表：新增组件/功能时追加
  # 这些字符串应能唯一标识新功能已编译到产物中
  key_strings:
    - "nav-collapsed"           # 导航栏折叠模式
    - "icon-tooltip"            # 图标 tooltip
    - "useTheme"                # 主题切换 composable
    - "invoke"                  # Tauri IPC 调用
    - "__TAURI_INTERNALS__"     # Tauri 内部对象
  # 关键字符串必须全部命中（false 时允许部分命中）
  require_all_keys: true
```

**通过条件**：
- `spa.require_all_keys: true` → 全部 `key_strings` 都至少在一个 JS 文件中命中
- `spa.require_all_keys: false` → 至少一个 `key_strings` 命中

**失败修复建议**：
- 关键字符串未命中 → 检查源码中是否确实使用了该字符串（如组件类名是否正确）
- 全部字符串都未命中 → 产物可能被旧版覆盖，执行强制重建（`spa.force_rebuild: true`）

**输出格式**：
```
[SPA-Keys] Searching for 5 key strings in 12 JS files...
[SPA-Keys]   "nav-collapsed" → HIT (assets/index-abc123.js, 3 occurrences)
[SPA-Keys]   "icon-tooltip" → HIT (assets/index-abc123.js, 1 occurrence)
[SPA-Keys]   "useTheme" → HIT (assets/vendor-def456.js, 2 occurrences)
[SPA-Keys]   "invoke" → HIT (assets/index-abc123.js, 8 occurrences)
[SPA-Keys]   "__TAURI_INTERNALS__" → MISS
[SPA-Keys] VERDICT: FAIL (1 key string not found)
[SPA-Keys] SUGGESTION: "__TAURI_INTERNALS__" not found, check if @tauri-apps/api is imported in source
```

## 3. 配置驱动原则

所有参数从 `config.yaml` 的 `spa` 节读取，不在代码中硬编码：

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `spa.package_name` | `""` | 前端 package.json 的 name 字段（用于验证构建脚本对应的包） |
| `spa.output_dir` | `""` | SPA 产物输出目录（如 `dist` / `api/public`） |
| `spa.source_dirs` | `[]` | 需监控的源码目录列表 |
| `spa.source_extensions` | `[".ts", ".tsx", ".vue", ".js", ".jsx"]` | 源码文件扩展名过滤 |
| `spa.artifact_marker_file` | `"index.html"` | 产物标记文件（用于 mtime 比较） |
| `spa.key_strings` | `[]` | JS chunk 中需验证的关键字符串列表 |
| `spa.require_all_keys` | `true` | 是否要求全部关键字符串都命中 |
| `spa.force_rebuild` | `false` | 是否强制重建（跳过时间戳验证） |

## 4. 与 Tauri 测试流程的集成

本验证法在 Tauri 桌面测试流程中的位置：

```
阶段 1：测试前预检
  ├── 1.1 环境验证
  ├── 1.2 SPA 产物时间戳验证  ← 本文档主方法（2.1）
  ├── 1.3 SPA 产物特征验证    ← 本文档辅助方法（2.2）（可选）
  └── 1.4 端口占用检查
```

- 时间戳对比法（2.1）作为阶段 1.2 的**必需验证**
- JS chunk 特征验证法（2.2）作为阶段 1.3 的**可选验证**，仅在 `spa.key_strings` 非空时执行
- 两项验证任一失败即判定阶段 1 失败，中断后续阶段

## 5. PowerShell 实现示例

以下脚本展示时间戳对比法的核心逻辑，实际实现见 `templates/phase_tauri_desktop.py`：

```powershell
# 参数从 config.yaml 读取，此处仅为示例
$sourceDirs = @("karpathy-wiki/frontend/src")
$outputDir = "karpathy-wiki/api/public"
$artifactFile = Join-Path $outputDir "index.html"

# 取源码 mtime 最大值
$sourceMaxMtime = [DateTime]::MinValue
$latestSourceFile = ""
foreach ($dir in $sourceDirs) {
    Get-ChildItem -Path $dir -Recurse -File |
        Where-Object { $_.Extension -in @(".ts", ".tsx", ".vue", ".js", ".jsx") } |
        ForEach-Object {
            if ($_.LastWriteTime -gt $sourceMaxMtime) {
                $sourceMaxMtime = $_.LastWriteTime
                $latestSourceFile = $_.FullName
            }
        }
}

# 取产物 mtime
if (Test-Path $artifactFile) {
    $artifactMtime = (Get-Item $artifactFile).LastWriteTime
} else {
    Write-Output "FAIL: Artifact file not found: $artifactFile"
    exit 1
}

# 判定
if ($sourceMaxMtime -gt $artifactMtime) {
    Write-Output "FAIL: Source ($latestSourceFile) is newer than artifact"
    Write-Output "SUGGESTION: Rebuild SPA before running Tauri tests"
    exit 1
} else {
    Write-Output "PASS: Artifact is up-to-date"
    exit 0
}
```

## 6. 常见误判与规避

| 误判场景 | 现象 | 规避方法 |
|----------|------|----------|
| CI 环境 mtime 重置 | `git checkout` 后所有文件 mtime 相同，时间戳对比失效 | 启用 JS chunk 特征验证法（2.2）作为辅助 |
| 编辑器临时文件被扫描 | `.ts.bak` / `.vue.swp` 等文件被误扫 | 严格按 `spa.source_extensions` 过滤，不扫描无扩展名文件 |
| node_modules 被误扫 | source_dirs 包含 node_modules 导致 mtime 永远新于产物 | `source_dirs` 只配置业务源码目录，不包含 `node_modules` |
| 构建产物分多个 chunk | index.html mtime 早于 chunk 文件 | 取 `spa.output_dir` 下所有文件的 mtime 最大值作为 artifact_mtime |
| 强制重建后未重新验证 | `force_rebuild: true` 触发重建但跳过验证 | 重建后必须重新执行时间戳对比，确认产物 mtime 已更新 |

## 7. 适用场景

- ✅ Tauri 桌面应用构建前的 SPA 产物验证
- ✅ CI/CD 流水线中的构建产物完整性检查
- ✅ 怀疑产物被旧版覆盖时的特征验证
- ❌ 纯 SSR 应用（无独立 SPA 产物）
- ❌ 动态加载的微前端应用（chunk 文件分散且动态生成）
