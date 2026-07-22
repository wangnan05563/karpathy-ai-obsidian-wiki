# 常见问题

> ⚠️ **项目特定知识库文档**：本文档含硬编码项目路径和命令（如 `karpathy-wiki/`、`cd karpathy-wiki`），这些值来源于项目实际排查沉淀，非配置化参数。可配置的参数见 `config/coding-standards-config.md` 和 `config/tech-stack.json`。

## Q: 页面又出现中文乱码（U+FFFD / 锟斤拷），刚修过怎么又复发？

**症状**：浏览器看到 `?` / 锟斤拷 / 空方块等乱码。Vite 控制台无报错。

**根因（双层）**：
1. **表层根因**：源文件被保存为 GBK 编码，Vite 按 UTF-8 加载产生乱码
2. **深层根因**（2026-07-10 复盘发现）：**元配置文件本身是 GBK**——`.gitignore` / `.editorconfig` / `.vscode/settings.json` / 根 `.md` 文档的字节流是 GBK，Trae 重新保存时按 GBK 写入，形成"修了又复发"的死循环

**复盘机制（典型死循环）**：
```
页面乱码
  -> 改 .vscode/settings.json 加 "files.encoding": "utf8"
  -> 但 .vscode/settings.json 字节流本身是 GBK
  -> Trae 看到 GBK 字节流，保存时按 GBK 写入
  -> 配置文件"改完了"但字节流仍是 GBK
  -> 几天后页面又乱码
```

**关键排查**：
```powershell
cd karpathy-wiki
node scripts/check-encoding.js
# 输出：扫描 51 个文件（源码 46 + 元配置 5），未发现 GBK 乱码
# exit 0 = 干净；exit 1 = 有问题文件
# 注意：v1.1 起同时扫描 .gitignore / .editorconfig / .vscode/*.json / 根 *.md
```

**一键修复**：
```powershell
node scripts/check-encoding.js --fix
# v1.1 起同时修复源码 + 元配置 + 根 .md
```

**根治 Checklist**（按顺序全部完成才能根治）：
1. 跑 `check-encoding.js --fix` 把所有 GBK 文件转 UTF-8
2. 确认 `<workspace>/.vscode/settings.json` 字节流是 UTF-8（不是 GBK！）
3. 确认 `karpathy-wiki/.editorconfig` 存在且字节流是 UTF-8
4. 确认 `karpathy-wiki/.vscode/settings.json` 项目级覆盖存在
5. 重启 Trae 让新设置生效
6. 浏览器强制刷新（Ctrl+Shift+R）清 Vite 缓存

**如何区分"src"还是"meta"问题**：
- 输出 `[SRC]` = 源码是 GBK → 跑 `--fix` 后浏览器强刷
- 输出 `[META]` = 元配置/根 .md 是 GBK → 跑 `--fix` 后重启 IDE

详见 [encoding-and-io.md](encoding-and-io.md#复发根因2026-07-10-复盘元配置文件本身是-gbk) 和 [project-rules.md](project-rules.md#7-文件编码必须是-utf-8-无-bom)。

## Q: 扫描器报告 *.vue.js / *.ts.js 文件乱码

**症状**：`check-encoding.js` 报告一堆 `.vue.js` / `.ts.js` 文件 U+FFFD / 锟斤拷。

**根因**：vue-tsc 2.x 在 IDE 打开 `.vue` / `.ts` 时实时生成同名 `.js` 副本（Volar 预转换产物）。这些副本**不影响 Vite 实际加载**（Vite 通过 `.vue` 扩展名加载），但会污染编码扫描器。

**处理**：
1. 一次性清理：`node scripts/clean-volar.js`
2. 扫描器已默认排除 `*.vue.js` / `*.ts.js` / `*.js`
3. 工作区改 utf8 后，新副本按 utf8 生成，不会再乱码
4. 副本已被 `.gitignore` 排除，不会入库

**不要尝试**：
- 在 .vue 源文件里 import `.vue.js`（Volar 不支持，Vite 也不会加载）
- 把 .vue.js 文件改回 .vue（这只是 Vite 误读时显示的乱码，源文件本身可能正常）

## Q: fix-encoding-all.ps1 转码后文件还是乱码（甚至更乱）

**症状**：运行 `node scripts/check-encoding.js --fix` 后某些文件依然有 U+FFFD 或出现"锟斤拷"乱码。

**根因**：文件是**混合编码**（部分 GBK 注释 + 部分 UTF-8 代码段），整体按 GBK 解码会破坏 UTF-8 段。

**判定**：脚本里 `SKIP  reason=mixed-encoding-detected` 就是这种情况。

**处理**：
1. **不要再次运行 --fix**（不会变好）
2. 检查是否有 `.gbk.bak` 备份（脚本转码前会自动备份）—— `ls services/api/src/*.gbk.bak`
3. 如果转码已发生且更乱，从 `.gbk.bak` 恢复：
   ```powershell
   # 单文件恢复
   Copy-Item -LiteralPath 'path\to\file.gbk.bak' -Destination 'path\to\file' -Force
   ```
4. 混合编码文件需要**人工处理**：逐段判断 GBK / UTF-8 边界
5. 通常是历史遗留的"部分文件被 GBK 编辑器重新保存"造成的，**只能整文件重写**

**预防**：
- 工作区根 `.vscode/settings.json` 必须 `files.encoding: "utf8"`
- 新文件创建时确认编码（Trae 右下角状态栏会显示当前文件编码）

## Q: 写了 .gitattributes 但 Git 仍把 .vue.js 纳入 diff

**症状**：`git status` 列出 `App.vue.js` 等 Volar 预转换副本。

**根因**：`.gitattributes` 不控制"是否纳入版本控制"，只控制"已纳入文件的属性"（如 eol）。
**真正控制入库的是** `.gitignore`。

**处理**：
- 确认 `karpathy-wiki/.gitignore` 含：
  ```
  *.vue.js
  packages/web/src/**/*.js
  ```
- 如果已忽略但仍出现：可能是 `git add -f` 强加过，用 `git rm --cached App.vue.js` 移出索引
- 新生成的副本在工作区改 utf8 后是 utf8，但仍会被 .gitignore 拦截

## Q: Write 工具报告成功但文件为空

**症状**：Write 工具返回成功，但文件内容为空或只有几个字节。

**根因**：Write 工具在某些情况下存在异步写入竞态。

**解决方案**：改用 PowerShell `[System.IO.File]::WriteAllText` 直写。

```powershell
[System.IO.File]::WriteAllText(
  "path\to\file.txt",
  $content,
  [System.Text.UTF8Encoding]::new($false)
)
```

## Q: PowerShell 端口占用

**症状**：启动服务时报错 `EADDRINUSE: address already in use :::3000`。

**根因**：旧 server 进程未释放端口。

**解决方案**：

```powershell
# 查找占用进程
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object OwningProcess

# 终止进程（替换 <PID> 为实际进程 ID）
Stop-Process -Id <PID> -Force
```

## Q: TypeScript 联合类型窄化失败

**症状**：`typeof p === 'string'` 后 TS 仍认为 p 是联合类型。

**根因**：TS 无法基于独立 discriminant 窄化 `string | {from, to}`。

**解决方案**：

```typescript
// 方案 A：as 断言
const s = p as string;

// 方案 B：type guard 函数
function isStringParam(p: Param): p is string {
  return typeof p === 'string';
}
```

## Q: SSE 路由返回 404

**症状**：新增路由后访问返回 404。

**根因**：路由未在 `routes/index.ts` 中注册。

**解决方案**：在 `routes/index.ts` 中添加路由注册：

```typescript
import { registerWikiRoute } from './api/wiki';
app.register(registerWikiRoute);
```

## Q: PowerShell $pid 只读变量

**症状**：`$pid = 1234` 报错 Cannot assign to read-only property。

**根因**：`$pid` 是 PowerShell 内置只读变量（当前进程 ID）。

**解决方案**：使用 `$procId` 或其他变量名替代。

```powershell
# 错误
$pid = 1234

# 正确
$procId = 1234
```

## Q: here-string 中 `` `n `` 未转义

**症状**：单引号 here-string 中 `` `n `` 变为字面量 `\n`。

**根因**：PowerShell 单引号 here-string 不进行转义解析。

**解决方案**：使用 `.Replace()` 修复。

```powershell
$content = $content.Replace('\n', "`n")
```

## Q: curl 测试 SSE 路由超时

**症状**：`curl http://localhost:3000/api/wiki/compile` 一直等待不返回。

**根因**：curl 默认等待完整响应，SSE 是长连接。

**解决方案**：

```powershell
# 使用 -N 参数（不缓冲）
curl -N http://localhost:3000/api/wiki/compile?vaultId=xxx

# 或使用 PowerShell Invoke-RestMethod
Invoke-WebRequest -Uri "http://localhost:3000/api/wiki/compile?vaultId=xxx" -UseBasicParsing
```
