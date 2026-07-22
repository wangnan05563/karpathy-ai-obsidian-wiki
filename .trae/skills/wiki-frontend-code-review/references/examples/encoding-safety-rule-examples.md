# encoding-safety-rule - Code Examples

> This file contains Wrong/Right code examples extracted from [encoding-safety-rule.md](../encoding-safety-rule.md).
> Load on demand when you need to reference examples or generate fix code.

---

## ES-1: 源文件必须为 UTF-8 无 BOM 编码

### Wrong

PowerShell 默认编码可能将含中文的文件转为 GB2312，导致 Vite 读取时产生 U+FFFD 乱码：

```powershell
# Wrong：未指定 -Encoding，含中文时可能写入 GB2312
$content = "会话管理"
Set-Content -Path src/views/Session.vue -Value $content
```

```ts
// 文件实际为 GB2312，Vite 按 UTF-8 读取后变为乱码：
// 会话管理 -> 浣犱細绠＄悊  (U+FFFD 替换字符)
const tabTitle = '会话管理' // 实际为乱码字符串
```

### Right

PowerShell 7+ 显式指定 `utf8NoBOM`：

```powershell
# Right：显式指定 UTF-8 无 BOM
$content = "会话管理"
Set-Content -Path src/views/Session.vue -Value $content -Encoding utf8NoBOM
```

PowerShell 5.1 无 `utf8NoBOM`，需用 .NET API 写入：

```powershell
# PS 5.1 兼容写法：直接调用 .NET，避免 BOM
$content = "会话管理"
[System.IO.File]::WriteAllText(
  (Resolve-Path 'src/views/Session.vue').Path,
  $content,
  (New-Object System.Text.UTF8Encoding($false))
)
```

---

## ES-2: 元配置文件必须为 UTF-8 无 BOM 编码

### Wrong

部分编辑器默认在 JSON 文件首部添加 BOM，导致 `JSON.parse` 解析失败：

```text
.vscode/settings.json 字节序列（前 3 字节为 BOM）：
EF BB BF 7B 0D 0A 20 20 22 65 64 69 74 6F 72 ...  {..."editor...
```

```ts
// JSON.parse 遇到 BOM 报错：Unexpected token \uFEFF in JSON at position 0
const settings = JSON.parse(fs.readFileSync('.vscode/settings.json', 'utf-8'))
```

### Right

写入元配置文件时统一使用 UTF-8 无 BOM：

```powershell
# 写入 settings.json 显式指定 utf8NoBOM
$json = '{"editor.formatOnSave": true}'
[System.IO.File]::WriteAllText(
  (Resolve-Path '.vscode').Path + '\settings.json',
  $json,
  (New-Object System.Text.UTF8Encoding($false))
)
```

读取时若不确定来源，先剥离 BOM 再解析：

```ts
function readJsonSafe(path: string): unknown {
  const raw = fs.readFileSync(path, 'utf-8')
  // 剥离可能的 BOM 再解析
  return JSON.parse(raw.replace(/^\uFEFF/, ''))
}
```

---

## ES-3: 编码检测采用严格 UTF-8 解码，含 FFFD 即判定为非 UTF-8

### Wrong

宽松解码会把非法字节替换为 U+FFFD，无法发现编码问题：

```ts
// Wrong：默认 TextDecoder 用 U+FFFD 替换非法字节，不抛错
function checkEncoding(bytes: Uint8Array): boolean {
  try {
    new TextDecoder('utf-8').decode(bytes) // fatal 默认 false
    return true // GB2312 文件也返回 true，但字符串中已含 U+FFFD
  } catch {
    return false
  }
}
```

```powershell
# Wrong：默认 GetString 用 U+FFFD 替换字符，不抛异常
$enc = New-Object System.Text.UTF8Encoding($false) # 第二参数默认 false
$null = $enc.GetString($bytes) # GB2312 文件不抛错，含 U+FFFD 字符
```

### Right

严格模式：fatal = true 或 throwOnInvalidBytes = true：

```ts
// Right：fatal = true，遇到非法字节抛异常
function isUtf8NoBom(bytes: Uint8Array): boolean {
  if (bytes.length >= 3 && bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) {
    return false // BOM 不允许
  }
  try {
    new TextDecoder('utf-8', { fatal: true }).decode(bytes)
    return true
  } catch {
    return false
  }
}
```

```powershell
# Right：throwOnInvalidBytes = true，非法字节抛 DecoderFallbackException
function Test-Utf8NoBom {
  param([string]$Path)
  $bytes = [System.IO.File]::ReadAllBytes($Path)
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

---

## ES-4: 检测时机必须在 Edit 后与构建前执行

### Wrong

仅在浏览器运行时发现乱码才回头排查：

```json
// package.json：无 prebuild 钩子，乱码文件直接进入产物
{
  "scripts": {
    "build": "vite build"
  }
}
```

```ts
// 用户反馈"tab 标签全是 ????"后才回头定位是哪个文件编码问题
// 此时已发布到生产，影响所有用户
```

### Right

构建前 prebuild 钩子 + Edit 后即时检测：

```json
{
  "scripts": {
    "prebuild": "node scripts/check-encoding.mjs",
    "build": "vite build"
  }
}
```

```ts
// scripts/check-encoding.mjs：扫描所有源文件，遇到非 UTF-8 立即退出
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { extname, join } from 'node:path'

const SCAN_EXT = ['.vue', '.ts', '.tsx', '.json', '.md']
const failed: string[] = []

function scan(dir: string) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    if (name === 'node_modules' || name === 'dist') continue
    const st = statSync(full)
    if (st.isDirectory()) { scan(full); continue }
    if (!SCAN_EXT.includes(extname(full))) continue
    const bytes = new Uint8Array(readFileSync(full))
    if (!isUtf8NoBom(bytes)) failed.push(full)
  }
}

function isUtf8NoBom(bytes: Uint8Array): boolean {
  if (bytes.length >= 3 && bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) return false
  try { new TextDecoder('utf-8', { fatal: true }).decode(bytes); return true }
  catch { return false }
}

scan('frontend')
if (failed.length) {
  console.error('Non-UTF-8 files detected:\n' + failed.join('\n'))
  process.exit(1)
}
```

---

## ES-5: 纯 ASCII 文件免检（白名单）

### Wrong

对所有文件（含纯 ASCII 的第三方 d.ts）都做严格解码，耗时且无意义：

```ts
// Wrong：无 ASCII 短路，大量纯 ASCII 文件也被严格解码
function scanAll(bytes: Uint8Array): boolean {
  try {
    new TextDecoder('utf-8', { fatal: true }).decode(bytes)
    return true
  } catch { return false }
}
// 扫描 node_modules 时性能急剧下降
```

### Right

ASCII 短路放行，仅对含非 ASCII 字节的文件严格解码：

```ts
function isAsciiOnly(bytes: Uint8Array): boolean {
  for (let i = 0; i < bytes.length; i++) {
    if (bytes[i] > 0x7F) return false
  }
  return true
}

function checkEncoding(bytes: Uint8Array, asciiWhitelist: boolean): boolean {
  // 白名单启用 + 纯 ASCII：直接放行
  if (asciiWhitelist && isAsciiOnly(bytes)) return true
  if (bytes.length >= 3 && bytes[0] === 0xEF && bytes[1] === 0xBB && bytes[2] === 0xBF) return false
  try {
    new TextDecoder('utf-8', { fatal: true }).decode(bytes)
    return true
  } catch {
    return false
  }
}
```

---

*End of examples*
