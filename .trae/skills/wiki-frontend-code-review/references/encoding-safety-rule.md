# Rule Catalog - Encoding Safety

## Scope
- Covers: 源文件与元配置文件的字符编码合规性、UTF-8 严格解码检测、白名单策略、检测时机。
- Does NOT cover: 代码逻辑正确性（type-safety-rule.md）、构建产物编码（属构建工具职责）、第三方依赖文件编码。

> 所有可配置参数（要求编码、检测方法、扫描范围、白名单等）集中定义在 [config/review-config.md](../config/review-config.md) 的"编码安全审查参数"段。本文件只描述通用模式，不硬编码具体值。

## Rules

### ES-1: 源文件必须为 UTF-8 无 BOM 编码

IsUrgent: True
Category: Encoding Safety

### Description

源代码文件（`.vue` / `.ts` / `.tsx` 等，具体扩展名以配置 `encoding_scan_scope` 为准）必须以 UTF-8 无 BOM 编码保存。Windows 环境下，PowerShell 默认编码可能是 GB2312 / GBK，编辑含中文的源文件时若未显式指定 `-Encoding utf8NoBOM`，文件会被转为本地 ANSI 编码。Vite / esbuild 按 UTF-8 读取此类文件时，无法识别的字节序列会被替换为 `U+FFFD`（即配置 `fffd_indicator`），导致页面 tab 标签、菜单文案、注释全部显示为乱码，功能不可用。

### Suggested Fix

PowerShell 写文件时显式指定 `-Encoding utf8NoBOM`（PowerShell 7+）或 `Set-Content -Encoding UTF8`（PS 5.1，注意会带 BOM 需手动去除）。检测模板见 ES-3。

> **示例代码**: 参见 [examples/encoding-safety-rule-examples.md](examples/encoding-safety-rule-examples.md)。

### ES-2: 元配置文件必须为 UTF-8 无 BOM 编码

IsUrgent: True
Category: Encoding Safety

### Description

元配置文件（`.editorconfig` / `.vscode/settings.json` / `tsconfig.json` 等，具体以配置 `meta_encoding_required` 为准）同样必须为 UTF-8 无 BOM。元配置文件通常较小但被工具链频繁读取，BOM 字符（`EF BB BF`）会被部分工具当作正文解析，导致 `tsconfig` 首字段解析失败、`settings.json` JSON 解析报错。

### Suggested Fix

提交前对元配置文件运行编码检测；若需新建/修改，统一使用 UTF-8 无 BOM 写入。

> **示例代码**: 参见 [examples/encoding-safety-rule-examples.md](examples/encoding-safety-rule-examples.md)。

### ES-3: 编码检测采用严格 UTF-8 解码，含 FFFD 即判定为非 UTF-8

IsUrgent: True
Category: Encoding Safety

### Description

编码检测必须采用严格 UTF-8 解码（对应配置 `encoding_detection = utf8-strict-decode`）：使用 `new UTF8Encoding(false, true)`（第二参数 `throwOnInvalidBytes = true`），任何非法字节序列都应抛出 `DecoderFallbackException`；或采用 `decoder.fatal = true`（Node/Web Decoder API）模式。若以宽松模式解码（默认 `U+FFFD` 替换），无法区分"原文合法包含 U+FFFD"与"非 UTF-8 文件被强制转换"，会产生误判。

检测到结果字符串中包含配置 `fffd_indicator` 指示字符时，判定为非 UTF-8 编码文件，必须阻断提交。

### Suggested Fix

检测脚本模板（PowerShell）：

```powershell
# 严格 UTF-8 解码检测：任何非法字节都抛异常
function Test-Utf8NoBom {
  param([string]$Path)
  $bytes = [System.IO.File]::ReadAllBytes($Path)
  # BOM 检测：EF BB BF
  if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
    return $false
  }
  $enc = New-Object System.Text.UTF8Encoding($false, $true)
  try {
    $null = $enc.GetString($bytes)
    return $true
  } catch [System.Text.DecoderFallbackException] {
    return $false
  }
}
```

Node / Web 端等价实现：

```ts
// decoder.fatal = true：遇到非法字节抛异常
function isUtf8NoBom(bytes: Uint8Array): boolean {
  if (bytes.length >= 3 && bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) {
    return false
  }
  try {
    new TextDecoder('utf-8', { fatal: true }).decode(bytes)
    return true
  } catch {
    return false
  }
}
```

> **示例代码**: 参见 [examples/encoding-safety-rule-examples.md](examples/encoding-safety-rule-examples.md)。

### ES-4: 检测时机必须在 Edit 后与构建前执行

IsUrgent: True
Category: Encoding Safety

### Description

编码检测的执行时机决定问题发现早晚，越晚发现修复成本越高。最低限度必须在两个时机执行：

1. **Edit 后**：自动化代理或人工完成文件编辑后立即检测，可在问题扩散前定位到具体文件。
2. **构建前**：`pnpm build` / `vite build` 之前作为 prebuild 钩子运行，阻断带乱码文件进入产物。

仅依赖运行时浏览器发现乱码会导致 tab 标签全屏乱码后才能察觉，用户体验受损且难定位根因。

### Suggested Fix

- 在 `package.json` 添加 `"prebuild": "node scripts/check-encoding.mjs"` 钩子。
- 在编辑工作流末尾追加检测步骤；CI 流水线在 lint 阶段同步执行。

### ES-5: 纯 ASCII 文件免检（白名单）

IsUrgent: False
Category: Encoding Safety

### Description

仅含 ASCII 字符（字节范围 0x00–0x7F）的文件在 UTF-8 / GB2312 / GBK / Latin-1 等多种编码下字节序列完全一致，按任何编码解码都得不到 `U+FFFD`，无需检测。当配置 `ascii_whitelist = true` 时，检测器应先扫描字节是否全部 `<= 0x7F`，若是则直接放行，避免对大量纯 ASCII 第三方依赖文件、配置文件做无意义的严格解码，降低检测耗时。

### Suggested Fix

检测器入口增加 ASCII 短路：

```ts
function isAsciiOnly(bytes: Uint8Array): boolean {
  for (let i = 0; i < bytes.length; i++) {
    if (bytes[i] > 0x7F) return false
  }
  return true
}
// 主流程：ascii_whitelist 启用时优先短路
if (config.ascii_whitelist && isAsciiOnly(bytes)) return true
```

## Checklist
- [ ] 源文件（`.vue` / `.ts` / `.tsx` 等）为 UTF-8 无 BOM
- [ ] 元配置文件（`.editorconfig` / `.vscode/settings.json` 等）为 UTF-8 无 BOM
- [ ] 编码检测采用严格 UTF-8 解码，含 `U+FFFD` 判定为非 UTF-8
- [ ] 检测时机覆盖 Edit 后与构建前
- [ ] 纯 ASCII 文件按白名单短路放行
