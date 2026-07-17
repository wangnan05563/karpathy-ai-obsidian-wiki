# Rule Catalog — 编码安全

## Scope

- Covers: 后端源文件（`.ts`）、配置文件（`.json`）以及规则/文档（`.md`）的字符编码一致性，BOM 与非 UTF-8 字节检测，PowerShell 编辑含中文注释时的编码保持。
- 适用对象：所有 `services/api/` 下的 `.ts` 源文件、`config.json` / `tsconfig.json` 等配置文件、本技能及相邻技能目录下的 `.md` 规则文件；Edit 后、`tsc` 编译前的检测点。
- Does NOT cover: 文件系统路径遍历防护（见 [security-rule.md](security-rule.md)）、跨目录路径计算（见 [filesystem-vault-rule.md](filesystem-vault-rule.md)）、配置项硬编码（见 [config-management-rule.md](config-management-rule.md)）。

> 所有具体编码值、检测方法、扫描扩展名均从 [config/review-config.md](../config/review-config.md) 的"编码安全审查参数"节读取，本规则文件只描述通用模式，不硬编码任何具体值。

## Rules

### ES-1 源文件必须为 UTF-8 无 BOM

- Category: encoding-safety
- Severity: critical
- Description: 后端 TypeScript 源文件（`.ts`）若被工具链或编辑器转为 GB2312 / GBK / UTF-16 或带 BOM 的 UTF-8，会触发 `tsc` 编译失败（"SyntaxError: Invalid character" 或 BOM 字节被当作标识符前缀），运行时还会出现中文注释乱码、字符串字面量被破坏。源文件必须保持 `source_encoding_required` 指定的编码（默认 `utf-8-no-bom`）。
- Suggested fix: 检测到非 UTF-8 或带 BOM 时，以严格 UTF-8 解码读出文本内容，再以 `utf-8` 编码、不带 BOM 回写。CI / Edit 钩子可在写入后立即跑一次检测。
- Example:
  - Bad:
    ```text
    # 文件以 GB2312 保存，tsc 编译报错 "Invalid character"，中文注释变成 ??
    ```
  - Good:
    ```text
    # 文件以 UTF-8 无 BOM 保存，tsc 编译通过，中文注释正常显示
    ```

### ES-2 配置文件必须为 UTF-8 无 BOM

- Category: encoding-safety
- Severity: critical
- Description: `config.json` / `tsconfig.json` 等配置文件若带 BOM 或被转为 GB2312，`JSON.parse` 会因 BOM 前缀抛 `Unexpected token \uFEFF`，`tsc` 解析 `tsconfig.json` 时也会失败。配置文件必须保持 `config_encoding_required` 指定的编码（默认 `utf-8-no-bom`）。
- Suggested fix: 与 ES-1 同样的检测/回写策略；配置文件写入时显式 `fs.writeFile(path, content, 'utf-8')`，禁止 `fs.writeFile(path, buffer)` 让默认编码生效。
- Example:
  - Bad:
    ```typescript
    // 写入时未显式声明编码，BOM 被保留，下次 JSON.parse 抛错
    await fs.writeFile(configPath, Buffer.from(jsonText));
    ```
  - Good:
    ```typescript
    // 显式 utf-8，禁止 BOM
    await fs.writeFile(configPath, jsonText, 'utf-8');
    ```

### ES-3 编码检测须用严格 UTF-8 解码，以 U+FFFD 为乱码指示

- Category: encoding-safety
- Severity: critical
- Description: 简单按字节判断"是否含 0xEF 0xBB 0xBF"只能识别 BOM，识别不了被转为 GB2312 的文件。必须用严格 UTF-8 解码（.NET 的 `new UTF8Encoding(false, true)` 等价语义，或 Node 中以 `Buffer.toString('utf8')` 后检测 `U+FFFD` 是否出现）：解码后内容含 `fffd_indicator` 字符即判定为非 UTF-8。纯 ASCII 文件按 `ascii_whitelist` 免检。
- Suggested fix: 提供统一检测函数 `assertUtf8NoBom(filePath)`，在 Edit 后、`tsc` 编译前调用；检测失败时按 ES-1 / ES-2 的修复策略回写。
- PowerShell 检测模板（参数从 config 读取，本模板仅示意检测语义）：
  ```powershell
  # 严格 UTF-8 解码：throwOnInvalidBytes=true，遇非法字节即抛错
  $utf8Strict = New-Object System.Text.UTF8Encoding($false, $true)
  $bytes = [System.IO.File]::ReadAllBytes($filePath)
  try {
    $text = $utf8Strict.GetString($bytes)
    # 含 U+FFFD 说明解码"成功"但出现替换字符，仍判定为非 UTF-8
    if ($text.Contains([char]0xFFFD)) { throw "非 UTF-8: 含替换字符 U+FFFD" }
    # 检测 BOM
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
      throw "含 UTF-8 BOM"
    }
  } catch {
    throw "编码检测失败: $filePath -> $($_.Exception.Message)"
  }
  ```

### ES-4 PowerShell 编辑含中文注释的文件必须保持原编码

- Category: encoding-safety
- Severity: critical
- Description: Windows PowerShell（5.x）默认编码是 GB2312 / ANSI，`Set-Content` / `Out-File` 不显式声明 `-Encoding utf8` 时会以默认编码回写，把含中文注释的 `.ts` 文件转为 GB2312，导致 `tsc` 编译失败。PowerShell 7+ 默认 UTF-8 但仍须显式 `-Encoding utf8NoBOM` 避免 BOM。Edit 工具或脚本编辑 `.ts` / `.json` / `.md` 文件后必须保持原编码。
- Suggested fix: PowerShell 写入时显式声明编码；读取后先检测编码（见 ES-3），再以同编码回写。Edit 工具底层应统一以 `utf-8` 无 BOM 读写。
- Example:
  - Bad:
    ```powershell
    # 未声明编码，PowerShell 5.x 以 GB2312 回写，中文注释损坏
    Set-Content -Path .\routes\cleanup.ts -Value $newContent
    ```
  - Good:
    ```powershell
    # 显式 UTF-8 无 BOM（PowerShell 7+ 用 utf8NoBOM；5.x 用 [System.IO.File]::WriteAllText）
    [System.IO.File]::WriteAllText(
      (Resolve-Path .\routes\cleanup.ts),
      $newContent,
      (New-Object System.Text.UTF8Encoding($false))
    )
    ```

## 适用 / 不适用场景

### 适用

- 评审 `services/api/` 下 `.ts` / `.json` 文件的字符编码一致性。
- 评审 Edit 钩子、CI 脚本中"写后即检测"的编码守卫。
- 评审 PowerShell 维护脚本对含中文注释文件的处理。
- 评审本技能及相邻技能目录下 `.md` 规则文件的编码（避免规则文件自身乱码）。

### 不适用

- 纯 ASCII 文件（按 `ascii_whitelist` 免检）。
- 二进制文件（图片、压缩包等非 `encoding_scan_scope` 扩展名）。
- 前端 `.tsx` / `.jsx` 文件（前端编码由前端构建链路保证，不在本技能范围）。
- 文件系统路径本身的合法性校验（见 [security-rule.md](security-rule.md)）。
