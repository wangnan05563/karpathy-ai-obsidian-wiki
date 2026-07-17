# Encoding Guard Rule

## 触发关键词

Edit, Write, writeFile, UTF-8, GB2312, U+FFFD, 替换字符, 编码, 中文乱码, check-encoding, bat pause

## 规则

### EG-1：Edit 前必须检测文件编码

**严重级别**：critical

使用 Edit / Write 工具修改文件前，若文件可能含非 ASCII 字符（中文/日文/韩文/Emoji 等），必须先用严格 UTF-8 解码检测原文件编码。检测失败则按回退编码读写，禁止盲目以 UTF-8 写入。

**为什么**：Windows 中文系统下，部分历史文件以 GB2312/GBK 保存。Edit 工具按 UTF-8 读入后写回，会把原编码字节当作 UTF-8 解码产生 U+FFFD 替换字符，Vite/esbuild 按 UTF-8 读取后注入到 bundle，前端出现"???"或乱码，且无法回退（替换字符不可逆）。

**检测模板**（PowerShell，参数取自 `config/coding-standards-config.md` 的 `encoding_detection_method` 与 `encoding_fallback`）：

```powershell
# 严格 UTF-8 解码：UTF8Encoding(false, true) 第二参数 throwOnInvalidBytes=true
function Test-Utf8Strict {
  param([string]$Path)
  $bytes = [System.IO.File]::ReadAllBytes($Path)
  try {
    $enc = New-Object System.Text.UTF8Encoding($false, $true)
    [void]$enc.GetString($bytes)
    return $true
  } catch {
    return $false
  }
}

# 用法
if (Test-Utf8Strict $path) {
  # 原 UTF-8，可安全 Edit
} else {
  # 非 UTF-8，需用 encoding_fallback（默认 gb2312）读写
}
```

### EG-2：PowerShell 编辑含中文文件必须保持原编码

**严重级别**：critical

非 UTF-8 文件必须使用 `encoding_fallback` 指定的编码读取与写回，禁止默认 UTF-8 写入。Edit / Write 工具若不支持指定编码，改用 PowerShell `[System.IO.File]::ReadAllText` / `WriteAllText` 显式传编码。

**为什么**：Edit 工具内部默认 UTF-8 输出。对 GB2312 文件执行 Edit 会把原字节按 GB2312 解码再以 UTF-8 编码写回，看似成功但文件编码已变；若中间任一步按错误编码解码，则产生不可逆替换字符。

**正确模板**（参数取自 config 的 `encoding_fallback`）：

```powershell
$enc = [System.Text.Encoding]::GetEncoding("gb2312")  # 来自 encoding_fallback
$content = [System.IO.File]::ReadAllText($path, $enc)
# 修改 $content
[System.IO.File]::WriteAllText($path, $content, $enc)
```

### EG-3：构建前必须扫描编码

**严重级别**：critical

运行 `npm run build` / `vite build` / `vue-tsc` 前必须执行 `encoding_scan_command`（来自 config）扫描 `encoding_scan_scope` 范围内的文件。扫描发现非 UTF-8 文件时必须先修复（运行 `encoding_fix_command`）再构建，禁止带病构建。

**为什么**：Vite/esbuild 按 UTF-8 读取源文件，遇到 GB2312 字节会产生 U+FFFD 替换字符并注入 bundle，运行时无报错但 UI 显示乱码，定位成本高。

**构建门禁模板**：

```powershell
# 构建前编码门禁（命令取自 config 的 encoding_scan_command）
node scripts/check-encoding.js
if ($LASTEXITCODE -ne 0) {
  Write-Error "编码扫描失败，请运行 encoding_fix_command 修复后再构建"
  exit 1
}
npm run build
```

### EG-4：Edit 工具失败时回退到 PowerShell 直写

**严重级别**：suggestion

当 Edit / Write 工具因编码、锁文件、长路径等原因失败时，回退到 PowerShell `[System.IO.File]::WriteAllText` 显式控制编码与写入。

**为什么**：Edit 工具封装层较多，失败时根因不明。直接用 .NET API 可控性强，且与编码守卫流程统一。

### EG-5：bat 脚本末尾禁止 pause

**严重级别**：suggestion

自动化场景禁止在 .bat 脚本末尾添加 `pause`，否则会阻塞 RunCommand 等自动化调用。需要用户交互的脚本改用 `npm run` 替代（来自 config 的 `bat_alternative`）。

**为什么**：`pause` 等待按键，自动化调用永远拿不到按键事件，命令表现为"挂起"，最终超时失败但无错误输出。

## 检测流程

```
┌───────────────┐
│  Edit / Write │
└───────┬───────┘
        │
        ▼
┌─────────────────────────┐    是    ┌──────────────────┐
│ 文件含非 ASCII 字符？    │ ───────▶ │ EG-1: 严格 UTF-8 │
└───────┬─────────────────┘          │     解码检测      │
        │ 否                          └────────┬─────────┘
        │                                      │
        ▼                                      ▼
   直接 Edit                          ┌──────────────────┐
                                      │ UTF-8 解码成功？  │
                                      └────┬─────────┬───┘
                                      是   │         │  否
                                           ▼         ▼
                                    直接 Edit   EG-2: 用 encoding_fallback
                                              读写后 PowerShell 直写
        │
        ▼
┌─────────────────────────┐
│   构建前 (npm run build) │
└───────┬─────────────────┘
        ▼
┌─────────────────────────┐    失败   ┌──────────────────┐
│ EG-3: encoding_scan     │ ───────▶ │ EG-3: fix_command │
│       _command 扫描      │          │ 修复后重扫         │
└───────┬─────────────────┘          └──────────────────┘
        │ 通过
        ▼
   正式构建
```

## PowerShell 编码操作模板

### 模板 A：检测 + 原编码写回（安全 Edit 替代）

```powershell
function Edit-FileWithEncoding {
  param(
    [string]$Path,
    [scriptblock]$Mutator  # 接收 $content 返回新 $content
  )
  $utf8 = New-Object System.Text.UTF8Encoding($false, $true)
  $bytes = [System.IO.File]::ReadAllBytes($Path)
  $isUtf8 = $true
  try { [void]$utf8.GetString($bytes) } catch { $isUtf8 = $false }

  if ($isUtf8) {
    $content = [System.IO.File]::ReadAllText($Path, $utf8)
    $new = & $Mutator $content
    [System.IO.File]::WriteAllText($Path, $new, $utf8)
  } else {
    # 非 UTF-8：用 encoding_fallback（默认 gb2312）
    $fallback = [System.Text.Encoding]::GetEncoding("gb2312")
    $content = [System.IO.File]::ReadAllText($Path, $fallback)
    $new = & $Mutator $content
    [System.IO.File]::WriteAllText($Path, $new, $fallback)
  }
}

# 用法：在文件首行插入注释
Edit-FileWithEncoding -Path "src/main.ts" -Mutator {
  param($c) "// auto header`n" + $c
}
```

### 模板 B：DELIVERY.md 等文档追加章节

文档同步常需在末尾追加章节。若文档原编码非 UTF-8，必须保持原编码。

```powershell
# 严格 UTF-8 检测
$utf8Strict = New-Object System.Text.UTF8Encoding($false, $true)
$bytes = [System.IO.File]::ReadAllBytes("DELIVERY.md")
$isUtf8 = $true
try { [void]$utf8Strict.GetString($bytes) } catch { $isUtf8 = $false }

if ($isUtf8) {
  $enc = $utf8Strict
} else {
  $enc = [System.Text.Encoding]::GetEncoding("gb2312")  # encoding_fallback
}
$content = [System.IO.File]::ReadAllText("DELIVERY.md", $enc)
$append = "`n`n## 新章节`n`n内容..."
[System.IO.File]::WriteAllText("DELIVERY.md", $content + $append, $enc)
```

### 模板 C：构建前编码门禁

```powershell
# encoding_scan_command + encoding_fix_command
node scripts/check-encoding.js
if ($LASTEXITCODE -ne 0) {
  Write-Host "发现编码问题，尝试自动修复..."
  node scripts/check-encoding.js --fix
  node scripts/check-encoding.js  # 复扫
  if ($LASTEXITCODE -ne 0) {
    Write-Error "编码修复失败，构建终止"
    exit 1
  }
}
npm run build
```

## 适用场景

- Windows 中文环境下的全栈项目（前端 Vite/Vue + 后端 Node.js）
- 含中文注释/中文文案的源文件编辑
- 文档文件（DELIVERY.md / README.md / 设计文档）追加章节
- 自动化构建前的编码门禁
- 跨平台协作（Linux/macOS 默认 UTF-8，Windows 历史文件可能 GB2312）

## 不适用场景

- 纯 ASCII 项目（无中文/无 Emoji），UTF-8 与 GB2312 字节一致
- Linux/macOS 原生环境（默认 UTF-8，无 GB2312 历史包）
- 已通过 CI 强制 UTF-8 校验的项目（CI 兜底，本地可省略）
- 二进制文件（图片/音视频/PDF，编码守卫不适用）

## 检查清单

- [ ] Edit 前是否检测目标文件编码（含非 ASCII 字符时）
- [ ] 非 UTF-8 文件是否用 `encoding_fallback` 读写
- [ ] 构建前是否执行 `encoding_scan_command` 门禁
- [ ] 扫描失败是否先 `encoding_fix_command` 修复再复扫
- [ ] bat 脚本末尾是否避免 `pause`（自动化场景）
- [ ] Edit 工具失败是否回退到 PowerShell `[System.IO.File]` 直写
- [ ] 文档追加章节是否保持原文件编码
