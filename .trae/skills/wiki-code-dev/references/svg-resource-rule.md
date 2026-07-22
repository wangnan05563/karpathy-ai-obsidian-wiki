# SVG 资源创建规则

## 触发场景

- 创建 `.svg` 矢量图标文件（favicon、菜单图标、IP 形象）
- 修改 HTML 中引用 SVG 资源的 `<link>` / `<img>` 标签
- 使用 Write 工具创建含中文的 SVG 文件

## 规则

### SR-1：SVG 文件编码必须为 UTF-8 无 BOM

含中文的 SVG 文件若以 GBK 保存，浏览器用 UTF-8 解析 XML 时会因无效字节序列而渲染失败，表现为 favicon 不显示或 SVG 图标空白。

- 纯 ASCII SVG：可直接用 Write 工具创建
- 含中文 SVG：必须用 PowerShell `[System.IO.File]::WriteAllText(path, content, [System.Text.UTF8Encoding]::new($false))` 写入

### SR-2：HTML 引用 SVG 时必须加版本参数

浏览器会缓存 SVG 资源，修改后不刷新仍显示旧版本。必须在 HTML 引用中加 `?v={version}` 参数，每次修改 SVG 内容时递增版本号。

```html
<link rel="icon" href="/favicon.svg?v=2" type="image/svg+xml" />
```

### SR-3：Write 工具创建含中文 SVG 不可靠时用 PowerShell 回退

Windows 环境下 Write 工具可能以系统默认编码（GBK）保存含中文字符的文件，导致 SVG XML 解析失败。回退方案：

```powershell
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText("path/to/file.svg", $content, $utf8NoBom)
```

## 检测方法

1. 扫描 `.svg` 文件，若含非 ASCII 字符则用 `node scripts/check-encoding.js` 验证编码
2. 扫描 HTML 文件中 `href="*.svg"` 引用，验证是否含 `?v=` 版本参数
3. 若 SVG 文件被修改但 HTML 引用的版本号未递增，告警

## 配置参数

所有参数见 [config/coding-standards-config.md](../config/coding-standards-config.md) 的"SVG 资源创建参数"段。

## 适配说明

- 纯 ASCII SVG：无需 PowerShell 回退，直接 Write 即可
- Linux/Mac 环境：Write 工具默认 UTF-8，无需回退
- CI/CD 环境：用 `git diff` 检测 SVG 变更，自动递增 HTML 版本号
