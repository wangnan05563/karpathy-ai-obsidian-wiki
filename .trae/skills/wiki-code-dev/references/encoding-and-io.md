# 编码与 I/O 规范

> ⚠️ **项目特定知识库文档**：本文档含硬编码项目路径（如 `karpathy-wiki/`），这些值来源于项目实际排查沉淀，非配置化参数。可配置的编码参数见 `config/coding-standards-config.md`。

本文档记录在编码和 I/O 操作中的常见陷阱与最佳实践。

## 源文件被保存为 GBK（最常见的乱码根因）

### 问题：`.vue` / `.ts` 文件实际是 GBK 编码

Vite 加载源文件时按 UTF-8 解析，若文件实际是 GBK，浏览器会看到乱码：
- `\uFFFD`（U+FFFD 替换字符）
- `锟斤拷`（GBK 字节被 UTF-8 误读后形成 `0xEF 0xBF 0xBD` 替换字符的串叠）
- 连续 `????`（GBK 不可解码时返回 `?`）

### 根因：Trae/VSCode 工作区设置 `files.encoding: "gbk"`

历史教训：2026-07-10 排查时发现 **`<workspace>/.vscode/settings.json` 第 2 行设置 `"files.encoding": "gbk"`**。
所有源文件被 Trae 加载/保存时按 GBK 处理，导致：
1. 前端 `packages/web/src/*.vue` 全部 GBK → Vite 加载时浏览器看到乱码
2. 后端 `services/api/src/*.ts` 同样受影响
3. Volar（vue-tsc 2.x）读源文件时按 GBK 解码，生成 `*.vue.js` / `*.ts.js` 预转换副本（也是 GBK）
4. 任何"修复"如果不改这个元凶，下次 IDE 重新保存文件就复发

### 复发根因（2026-07-10 复盘）：元配置文件本身是 GBK

**症状**：改了 `<workspace>/.vscode/settings.json` 第 2 行为 `"files.encoding": "utf8"`、
加了 `.editorconfig`、加了 `karpathy-wiki/.vscode/settings.json`，
但页面**仍然乱码**或**修了几天后又复发**。

**真实原因**：
- `<workspace>/.vscode/settings.json` 的字节流**本身是 GBK**
- `karpathy-wiki/.editorconfig` 的字节流**本身是 GBK**
- `karpathy-wiki/.vscode/settings.json` 的字节流**本身是 GBK**
- `karpathy-wiki/DELIVERY.md` 的字节流**本身是 GBK**

**这意味着什么**：
- 你"改了"配置文件，但配置文件在磁盘上的字节仍是 GBK
- 你的 IDE 看到的是 GBK 字节流按 GBK 解码后显示的中文
- 你的 IDE **重新保存文件**时按 GBK 写入
- `check-encoding.js` 之前只扫源码（46 个文件），不扫元配置（5 个文件）
- 所以你跑 `check-encoding.js` 一直显示 0 问题，但根元配置文件**默默在乱码**

**复发机制（死循环）**：
```
乱码 -> 改 .editorconfig 加 charset=utf-8
       -> 磁盘上 .editorconfig 字节流仍是 GBK
       -> Trae 重新保存时按 GBK 写入
       -> 改的"UTF-8"配置等于没改
       -> 继续乱码
```

**唯一解决方案**：
- 直接用 PowerShell 强制 GBK -> UTF-8 重写元配置文件
- 让 `check-encoding.js` 同时扫源码 + 元配置，发现问题立即报告
- 让 `fix-encoding-all.ps1` 同时修复源码 + 元配置

**教训**：
- Read 工具读取 GBK 文件时**会按 GBK 解码显示**，所以 cat -n 输出看似正常
- Write 工具写入 GBK 文件时**有时仍按 GBK 写入**（参见 lessons learned）
- **唯一可靠验证方式**是字节流检查（FFFD / 0xEF 0xBB 0xBF 头判断）

### 解决方案：多层防御

1. **改工作区根配置**（元凶）：
   ```json
   // <workspace>/.vscode/settings.json
   { "files.encoding": "utf8" }
   ```
2. **加项目级 .editorconfig**（跨编辑器强制）：
   ```ini
   root = true
   [*]
   charset = utf-8
   end_of_line = lf
   indent_style = space
   indent_size = 2
   ```
3. **加项目级 .vscode/settings.json**（双层保险）：
   ```json
   { "files.encoding": "utf8" }
   ```
4. **加 tsconfig exclude**（避免 Volar 预转换副本参与 TS 编译）：
   ```json
   {
     "include": ["src/**/*", "src/**/*.vue"],
     "exclude": ["node_modules", "src/**/*.js", "src/**/*.vue.js", "src/**/*.ts.js"]
   }
   ```
5. **常驻检测脚本**（CI/手动）：
   ```bash
   # 检测
   node scripts/check-encoding.js
   # 一键修复
   node scripts/check-encoding.js --fix
   # 清理 Volar 副本
   node scripts/clean-volar.js
   ```

### 检测原理

```javascript
// Node 内置：toString('utf8') 对非法 UTF-8 序列返回 \uFFFD
const buf = fs.readFileSync(file);
const text = buf.toString('utf8');
if (text.includes('\uFFFD')) {
  // 文件含非法 UTF-8 字节，几乎可肯定是 GBK（或混合编码）
}
```

### 修复原理

PowerShell 自带 GBK 解码能力（Node 不内置 GBK，需借助 PowerShell）：

```powershell
$gbk = [System.Text.Encoding]::GetEncoding('GBK')
$utf8 = [System.Text.UTF8Encoding]::new($false)
$b = [System.IO.File]::ReadAllBytes($path)
$t = $gbk.GetString($b)
[System.IO.File]::WriteAllBytes($path, $utf8.GetBytes($t))
```

**判定"纯 GBK"的三条件**（缺一不可，避免破坏混合编码文件）：
1. `gbkHasFFFD=False`：GBK 解码无失败
2. `gbkHasGarbled=False`：解码后无"锟斤拷/烫烫烫/屯屯屯"等典型乱码
3. `gbkHasChinese=True`：解码后含中文

### Volar 预转换副本的真相

vue-tsc 2.x 在 IDE 打开 `.vue` / `.ts` 时会实时生成同名 `.js` 副本（用于 IDE 内部类型检查），特征：
- 头部是 `/// <reference types=".../vue-global-types/..." />`
- 路径在源文件同目录（如 `App.vue` -> `App.vue.js`）
- 已被 `.gitignore` 排除（`*.vue.js` / `packages/web/src/**/*.js`）
- 不影响 Vite 实际加载（Vite 通过 `.vue` 扩展名加载），但会污染扫描器

**处理策略**：
- 接受副本生成（IDE 行为，无法完全抑制）
- 工作区改 utf8 后，新副本是 utf8（不会乱码）
- 扫描器显式排除 `*.vue.js` / `*.ts.js`
- 提供 `scripts/clean-volar.js` 一次性清理历史脏副本

## PowerShell here-string 陷阱

### 问题：单引号 here-string 中 `` `n `` 被视为字面量

```powershell
# 错误：`` `n `` 不会被转义为换行符
$content = @'
line1
line2
'@
# $content 包含字面量 "\n" 而非换行符

# 正确：使用双引号 here-string 或 .Replace()
$content = @"
line1
line2
"@

# 或使用 .Replace() 修复
$content = $content.Replace('\n', "`n")
```

### 根因

PowerShell 单引号 here-string（`@'...'@`）不进行任何变量展开或转义解析，所有字符均为字面量。

## Write 工具磁盘写入失败

### 问题

Write 工具报告成功但文件内容为空或只有几个字节。

### 根因排查

1. 检查文件大小：`Get-Item path\to\file | Select-Object Length`
2. 检查文件内容：`Get-Content path\to\file -Raw`
3. 如果文件存在但内容为空，说明写入存在竞态

### 解决方案

改用 PowerShell 原生写入：

```powershell
# UTF-8 无 BOM 写入
[System.IO.File]::WriteAllText(
  "path\to\file.txt",
  $content,
  [System.Text.Encoding]::UTF8
)

# UTF-8 有 BOM 写入（如果需要）
$bom = [System.Text.UTF8Encoding]::new($true)
[System.IO.File]::WriteAllText("path\to\file.txt", $content, $bom)

# UTF-8 无 BOM 写入（推荐）
$noBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText("path\to\file.txt", $content, $noBom)
```

## UTF-8 BOM 问题

### 问题

PowerShell 某些 cmdlet 写入文件时会添加 UTF-8 BOM（EF BB BF），导致 TypeScript/JSON 解析失败。

### 解决方案

始终使用 `[System.IO.File]::WriteAllText` 并指定 `UTF8Encoding(false)`：

```powershell
# 去 BOM 写入
[System.IO.File]::WriteAllText(
  "output.json",
  $jsonContent,
  [System.Text.UTF8Encoding]::new($false)
)
```

## rgba() CSS 语法陷阱

### 问题：rgba(#hex, alpha) 是无效 CSS

批量生成 CSS 变量时，直接把 hex 字符串塞进 `rgba()` 会导致 CSS 解析失败，浏览器忽略该声明。

```css
/* 错误：rgba() 不接受 hex 参数 */
--accent-purple-a05: rgba(#b026ff, 0.05);

/* 正确：必须先转换为 r, g, b 数值 */
--accent-purple-a05: rgba(176, 38, 255, 0.05);
```

### 根因

CSS `rgba()` 函数只接受 `r, g, b` 整数（0-255）或百分比，不接受 `#hex` 字符串。`rgba(#hex, alpha)` 是常见误解。

### 解决方案

在 Node.js 批量生成脚本中加入 hexToRgb 转换：

```javascript
function hexToRgb(hex) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!m) throw new Error('Invalid hex: ' + hex);
  return `${parseInt(m[1], 16)}, ${parseInt(m[2], 16)}, ${parseInt(m[3], 16)}`;
}
function rgba(hex, a) {
  return `rgba(${hexToRgb(hex)}, ${a})`;
}
```

### 验证方式

生成后检查文件中是否含 `rgba(#` 字符串：

```javascript
const hasInvalid = content.includes('rgba(#');
if (hasInvalid) console.error('Found invalid rgba(#hex) syntax');
```

## TypeScript 联合类型窄化

### 问题

TS 无法基于独立 discriminant 窄化联合类型：

```typescript
// 错误：TS 无法窄化
type Param = string | { from: string; to: string };
function processParam(p: Param) {
  if (typeof p === 'string') {
    // 这里 TS 仍然认为 p 是 Param 而非 string
    console.log(p.toUpperCase()); // Error!
  }
}

// 正确：使用 as 断言
if (typeof p === 'string') {
  const s = p as string;
  console.log(s.toUpperCase());
}

// 正确：使用 type guard
function isStringParam(p: Param): p is string {
  return typeof p === 'string';
}
```

## 文件操作优先用 fs/promises

### 推荐

```typescript
import { readFile, writeFile, mkdir } from 'fs/promises';

// 异步 API，自动处理错误
const content = await readFile(path, 'utf-8');
```

### 避免

```typescript
// 避免使用同步 API
const content = fs.readFileSync(path, 'utf-8');

// 避免使用回调 API
fs.readFile(path, 'utf-8', (err, data) => { ... });
```
