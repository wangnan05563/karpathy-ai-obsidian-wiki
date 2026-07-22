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

### ES-6: 文件内容若出现 U+FFFD 替换字符即判定为编码损坏

IsUrgent: True
Category: Encoding Safety

### Description

即使文件通过了严格 UTF-8 解码（ES-3），仍可能因为历史编辑过程中曾被以错误编码保存再转回 UTF-8，导致原始中文/非 ASCII 字符已永久丢失为 `U+FFFD` 替换字符（对应配置 `fffd_indicator`）。此类文件在解码层面是合法 UTF-8，但内容已损坏——前端渲染时 tab 标签、菜单文案、注释会显示为 `�` 乱码，功能不可读。

复盘 App.vue 中文标签乱码时发现：文件因编辑器/脚本编码错误导致中文字符全部变为 `U+FFFD`，常规 UTF-8 检测无法识别（因为 `U+FFFD` 本身是合法的 Unicode 字符），需要额外对文件内容进行替换字符扫描。

启用配置 `check_replacement_char`（默认 `true`）时，检测器须额外扫描文件内容是否包含 `U+FFFD`；当出现次数超过 `replacement_char_threshold`（默认 `0`，即不允许出现任何替换字符）时，判定为编码损坏文件，必须阻断提交并建议以历史正确版本或备份恢复。

### Judgment Logic

1. 读取文件内容为字符串（在 ES-3 严格解码通过后执行）。
2. 统计字符串中 `U+FFFD`（`\uFFFD`）字符的出现次数 `count`。
3. 若 `count > replacement_char_threshold`，判定为编码损坏：
   - 输出告警，列出文件路径与 `U+FFFD` 出现次数。
   - 建议操作：从版本控制历史恢复（`git checkout HEAD -- <file>`）、从备份恢复、或人工重写损坏区域。
   - 禁止仅以"重新保存为 UTF-8 无 BOM"作为修复——此时原始字符已丢失，重写编码无法恢复。
4. 若 `count <= replacement_char_threshold`，继续后续检查。

### Applicable Scenarios

- 含中文或其他非 ASCII 字符的源文件（`.vue` / `.ts` / `.tsx` / `.md` 等）。
- 曾在多平台/多编辑器间协作或迁移的文件（编码转换历史复杂）。
- 自动化脚本（特别是 PowerShell 默认编码非 UTF-8 的 Windows 环境）批量修改过的文件。

### Non-Applicable Scenarios

- 纯 ASCII 文件（ES-5 白名单已短路放行）。
- 二进制文件（图片、字体、压缩包等不在 `encoding_scan_scope` 范围内）。
- 已知合法包含 `U+FFFD` 的测试 fixture 文件（应在配置中显式加入豁免清单）。

### Configuration Parameters

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `check_replacement_char` | `true` | 是否在严格 UTF-8 解码后额外扫描 `U+FFFD` 替换字符 |
| `replacement_char_threshold` | `0` | 允许出现的 `U+FFFD` 数量上限；`0` 表示完全禁止 |
| `replacement_char_action` | `block` | 命中时的动作：`block` 阻断提交 / `warn` 仅告警 |

### Suggested Fix

检测脚本模板（PowerShell）：

```powershell
# U+FFFD 替换字符扫描：识别"解码合法但内容已损坏"的文件
function Test-ReplacementChar {
  param([string]$Path, [int]$Threshold = 0)
  $content = Get-Content -Path $Path -Raw -Encoding UTF8
  # 统计 U+FFFD 出现次数
  $count = ($content.ToCharArray() | Where-Object { $_ -eq [char]0xFFFD }).Count
  if ($count -gt $Threshold) {
    Write-Warning "$Path 包含 $count 个 U+FFFD 替换字符，编码已损坏，请从版本控制历史恢复"
    return $false
  }
  return $true
}
```

Node 端等价实现：

```ts
// 扫描 U+FFFD：解码合法但原始字符已丢失
function hasReplacementChar(content: string, threshold = 0): boolean {
  let count = 0
  for (let i = 0; i < content.length; i++) {
    if (content.charCodeAt(i) === 0xFFFD) count++
    if (count > threshold) return true
  }
  return false
}
```

> **示例代码**: 参见 [examples/encoding-safety-rule-examples.md](examples/encoding-safety-rule-examples.md)。

### ES-7: 禁用状态的可交互元素必须显式设置 disabled 属性

IsUrgent: False
Category: Encoding Safety

### Description

涉及禁用状态的可交互元素（button、input、select、option 等）必须设置 `disabled` 属性，而非仅依赖 CSS 类或样式置灰。

仅用 CSS 类（如 `.is-disabled`）置灰时，Playwright/Testing Library 等自动化测试工具认为元素仍可点击，点击操作会无限重试直至超时（默认 30s），浪费测试时间且产生误报。此外，屏幕阅读器等辅助技术依赖 `disabled` 属性向残障用户传达状态。

### Suggested Fix

```vue
<!-- ❌ 仅用 CSS 类置灰，测试工具无法识别 -->
<el-button
  type="primary"
  :class="{ 'is-disabled': !isFormValid }"
  @click="handleSubmit"
>
  提交
</el-button>

<!-- ✅ 显式 disabled 属性，便于测试与可访问性 -->
<el-button
  type="primary"
  :disabled="!isFormValid"
  @click="handleSubmit"
>
  提交
</el-button>
```

### ES-8: UI 文案必须与设计文档一致，变更时同步更新测试用例

IsUrgent: False
Category: Encoding Safety

### Description

UI 文案（标题、按钮、菜单项、表单标签等）必须与设计文档中的定义一致。变更文案时必须同步更新设计文档与测试用例。

测试脚本若用旧文案作为定位器或断言文本，而源码文案已变更，测试会失败但不易定位原因。例如 Config.vue 实际显示"AI 服务"，测试脚本却用"AI 配置"作为断言文本，导致测试无法通过且错误信息具有迷惑性。

### Suggested Fix

1. 从源码提取 UI 文本（Grep `title|label|placeholder|el-menu-item|el-button` 属性值）。
2. 交叉比对设计文档与测试用例中的断言文本。
3. git diff 涉及文案变更时，确认相关测试用例的断言文本同步更新。

### ES-9: 多实例数据（主题列表、预设列表等）必须集中管理，禁止硬编码

IsUrgent: True
Category: Encoding Safety

### Description

主题列表、预设列表、菜单项列表等同类多实例数据必须集中管理（从配置文件或后端 API 读取），禁止在组件中硬编码数量或字面量数组。

硬编码主题数量（如 `const themeCount = 3`）会在新增主题时导致计数失真。硬编码预设列表会导致前后端不一致（前端写死 3 个预设，后端新增第 4 个时前端无法展示）。集中管理后，新增/删除实例只需改配置或后端数据，前端自动适配。

### Suggested Fix

```typescript
// ❌ 硬编码数量与列表
const THEME_COUNT = 3;
const THEMES = [
  { key: 'light', label: '浅色' },
  { key: 'dark', label: '深色' },
  { key: 'auto', label: '跟随系统' },
];

// ✅ 从配置/API 加载，数量由数据源决定
export const themes = ref<Theme[]>([]);
export async function loadThemes() {
  const resp = await fetch('/api/themes');
  themes.value = (await resp.json()).themes;
}
export const themeCount = computed(() => themes.value.length);
```

## Checklist
- [ ] 源文件（`.vue` / `.ts` / `.tsx` 等）为 UTF-8 无 BOM
- [ ] 元配置文件（`.editorconfig` / `.vscode/settings.json` 等）为 UTF-8 无 BOM
- [ ] 编码检测采用严格 UTF-8 解码，含 `U+FFFD` 判定为非 UTF-8
- [ ] 检测时机覆盖 Edit 后与构建前
- [ ] 纯 ASCII 文件按白名单短路放行
- [ ] 文件内容扫描 `U+FFFD` 替换字符，超过阈值即判定为编码损坏
- [ ] 禁用状态的可交互元素显式设置 `disabled` 属性（非仅 CSS 置灰）
- [ ] UI 文案与设计文档一致，变更时同步更新测试用例
- [ ] 多实例数据集中管理，禁止硬编码数量或字面量数组
